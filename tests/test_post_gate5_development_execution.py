from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
import yaml

from openqfuel.gate5 import TargetStandardizer
from openqfuel.post_gate5_campaign import (
    FoldContext,
    ProjectionSpec,
    endpoint_rank_key,
    evaluate_fold_shape_admission,
    execute_control_fold,
    execute_projection_fold,
    project_fold_shape_resources,
    sample_projected_expectations,
    select_with_advancement_floor,
    stable_seed,
)
from openqfuel.post_gate5_reporting import evaluate_exploratory_signal


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/post_gate5_development_execution.yaml"


def _config() -> dict:
    return yaml.safe_load(CONFIG.read_text(encoding="utf-8"))


def _context(*, constant_compressed: bool = False) -> FoldContext:
    rng = np.random.default_rng(12)
    train_rows = 32
    validation_rows = 20
    x_train = rng.normal(size=(train_rows, 7))
    x_validation = rng.normal(size=(validation_rows, 7))
    compressed_train = rng.normal(size=(train_rows, 4))
    compressed_validation = rng.normal(size=(validation_rows, 4))
    if constant_compressed:
        compressed_train.fill(0.0)
        compressed_validation.fill(0.0)
    raw_target = 5.0 + 0.3 * x_train[:, 0] - 0.2 * x_train[:, 1]
    standardizer = TargetStandardizer.fit(raw_target)
    validation_target = 5.0 + 0.3 * x_validation[:, 0] - 0.2 * x_validation[:, 1]
    feasible_train = np.tile([0, 1], train_rows // 2)
    feasible_validation = np.tile([0, 1], validation_rows // 2)
    return FoldContext(
        fold_id="CV01",
        rung_samples=128,
        train_indices=np.arange(train_rows),
        validation_indices=np.arange(validation_rows),
        row_ids=[f"synthetic-{index:03d}" for index in range(train_rows)],
        x_train_full=x_train,
        x_validation_full=x_validation,
        compressed_train={4: compressed_train},
        compressed_validation={4: compressed_validation},
        y_train_standardized=standardizer.transform(raw_target),
        y_validation=validation_target,
        feasible_train=feasible_train,
        feasible_validation=feasible_validation,
        decision_set_ids=[f"D{index // 5:02d}" for index in range(validation_rows)],
        baseline_train_standardized=standardizer.transform(raw_target - 0.05),
        baseline_validation_standardized=standardizer.transform(
            validation_target - 0.05
        ),
        target_standardizer=standardizer,
        development_scale=float(np.std(np.r_[raw_target, validation_target], ddof=1)),
    )


def _spec() -> ProjectionSpec:
    return ProjectionSpec(
        projection_id="PX-TEST",
        qubits=4,
        layers=1,
        feature_scale=1.0,
        entangle=True,
        gamma_multiplier=1.0,
        alpha=0.01,
        landmarks=16,
    )


def test_d011_contract_keeps_locked_scope_and_fold_shape() -> None:
    config = _config()
    assert config["decision_id"] == "D011"
    assert config["outcome"]["current_status"] == (
        "terminal_prelaunch_technical_stop"
    )
    assert config["locks"]["allowed_data_scope"] == "development"
    assert config["locks"]["calibration_rows_read"] == 0
    assert config["locks"]["final_test_rows_read"] == 0
    assert config["locks"]["hardware_execution_authorized"] is False
    assert config["locks"]["gate6_authorized"] is False
    assert config["fold_shape_correction"]["benchmark_validation_rows"] == 9750
    assert config["fold_shape_correction"]["total_worst_fold_bundle_units"] == 1220
    assert config["campaign"]["validation_rows_per_complete_task"] == 39000
    assert set(config["endpoints"]["q01b_regime_analysis"]["dimensions"]) == {
        "fidelity",
        "uncertainty_family",
        "base_trajectory_family",
        "boundary_or_tail",
        "reference_feasible_status",
    }
    for path in config["source_binding"].values():
        if isinstance(path, str):
            assert (ROOT / path).is_file()


def test_d011_prelaunch_stop_has_no_scientific_or_admission_result() -> None:
    evidence = json.loads(
        (
            ROOT
            / "data/processed/reporting/post_gate5_d011_fold_shape_preflight.json"
        ).read_text(encoding="utf-8")
    )
    assert evidence["status"] == "STOP"
    assert evidence["terminal_status"] == "technical_failure"
    assert evidence["failed_stage"] == (
        "launcher_import_before_authority_verification"
    )
    assert evidence["admission_status"] == "NOT_REACHED"
    assert evidence["retry_authorized"] is False
    assert evidence["workload_progress"] == {
        "launcher_imports_completed": False,
        "authority_verification_reached": False,
        "source_hash_verification_reached": False,
        "synthetic_arrays_created": False,
        "synthetic_workload_started": False,
        "resource_admission_evaluated": False,
        "development_campaign_started": False,
    }
    assert all(value == 0 for value in evidence["integrity"].values())

    with (
        ROOT / "data/processed/reporting/post_gate5_future_research_discussion.csv"
    ).open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    future = next(row for row in rows if row["record_id"] == "P001-FR002")
    assert future["step_id"] == "D011_fold_shape_preflight_launcher"
    assert future["new_protocol_required"] == "true"
    assert future["active_pipeline_change_authorized"] == "false"
    assert future["post_outcome_retry_authorized"] == "false"
    assert future["reporting_commit"] == evidence["reporting_commit"]


def test_fold_shape_projection_and_admission_are_conservative() -> None:
    config = _config()
    projected = project_fold_shape_resources(
        config,
        benchmark_cpu_seconds=100.0,
        benchmark_wall_seconds=50.0,
        peak_rss_gib=2.0,
        free_disk_gib=60.0,
    )
    assert projected["worst_fold_bundle_units"] == 1220.0
    assert np.isclose(projected["projected_cpu_core_hours"], 100 * 1220 * 1.25 / 3600)
    assert evaluate_fold_shape_admission(config, projected)["status"] == "PASS"
    projected["observed_peak_rss_gib"] = 25.0
    assert evaluate_fold_shape_admission(config, projected)["status"] == "STOP"


def test_endpoint_order_and_advancement_floor_are_frozen() -> None:
    rows = []
    for index, (qubits, entangle) in enumerate(
        ((4, False), (4, True), (6, False), (6, True), (8, False), (8, True))
    ):
        rows.append(
            {
                "projection_id": f"PX-{index:02d}",
                "eligible": True,
                "pooled_oof_nrmse": 0.1 + index * 0.01,
                "mean_regret_m_s": 1.0,
                "regularized_condition_number": 2.0,
                "qubits": qubits,
                "layers": 1,
                "entangle": entangle,
            }
        )
    selected = select_with_advancement_floor(rows, track_id="Q01b", retain=4)
    assert {row["qubits"] for row in selected} == {4, 6, 8}
    assert {row["entangle"] for row in selected} == {False, True}
    assert endpoint_rank_key(rows[0], "Q01b") < endpoint_rank_key(rows[1], "Q01b")


def test_sampling_and_seed_derivation_are_deterministic() -> None:
    values = np.linspace(-0.9, 0.9, 24).reshape(2, 12)
    seed = stable_seed("P001", "D011", "test")
    first = sample_projected_expectations(values, shots=1024, seed=seed)
    second = sample_projected_expectations(values, shots=1024, seed=seed)
    assert np.array_equal(first, second)
    assert np.all((-1.0 <= first) & (first <= 1.0))


def test_projection_checkpoint_separates_governed_ineligibility(tmp_path: Path) -> None:
    context = _context()
    result = execute_projection_fold(
        tmp_path / "eligible",
        context,
        _spec(),
        _config(),
        source_commit="synthetic-source",
        stage="tuning",
        seed_index=0,
        active_tracks=["Q01b", "FQK"],
    )
    assert result["status"] == "complete"
    assert result["track_eligibility"]["Q01b"]["eligible"] is True
    assert result["track_eligibility"]["FQK"]["eligible"] is True
    assert (tmp_path / "eligible/PX-TEST.npz").is_file()

    ineligible = execute_projection_fold(
        tmp_path / "ineligible",
        _context(constant_compressed=True),
        _spec(),
        _config(),
        source_commit="synthetic-source",
        stage="tuning",
        seed_index=0,
        active_tracks=["Q01b", "FQK"],
    )
    assert ineligible["status"] == "complete_governed_ineligible"
    assert ineligible["track_eligibility"]["Q01b"]["reason_code"] == (
        "projected_kernel_geometry_undefined"
    )


def test_control_checkpoint_respects_active_endpoint(tmp_path: Path) -> None:
    result = execute_control_fold(
        ROOT,
        tmp_path,
        _context(),
        source_commit="synthetic-source",
        stage="tuning",
        seed_index=0,
        qubit_dimensions=[4],
        active_tracks=["Q01b"],
    )
    assert result["status"] == "complete"
    assert all(not key.endswith("_FQK") for key in result["metrics"])
    assert "C06-T17_Q01b" in result["metrics"]
    arrays = np.load(tmp_path / "controls.npz", allow_pickle=False)
    try:
        assert "cost__C06-T17" in arrays
        assert "probability__C01-T18" not in arrays
    finally:
        arrays.close()


def _selected_row(track: str, seed: int, **metrics: float) -> dict:
    return {
        "track_id": track,
        "seed_index": seed,
        "projection_id": f"PX-{track}",
        "eligible": True,
        "fold_count": 5,
        **metrics,
    }


def _control_row(track: str, control: str, seed: int, **metrics: float) -> dict:
    return {
        "track_id": track,
        "control_id": control,
        "seed_index": seed,
        "eligible": True,
        "fold_count": 5,
        **metrics,
    }


def test_exploratory_signal_requires_every_frozen_condition() -> None:
    projected = []
    controls = []
    a02 = []
    fqk_control_ids = (
        "C01-T18",
        "C02-T02",
        "C03-T13",
        "C04-T28",
        "C05-T12",
        "C06-T17",
        "A01-T04-q4",
        "C05-T17-q4",
    )
    for seed in range(1, 21):
        projected.append(
            _selected_row("Q01b", seed, pooled_oof_nrmse=0.98, pooled_oof_rmse=0.98)
        )
        controls.append(
            _control_row(
                "Q01b",
                "C06-T17",
                seed,
                pooled_oof_nrmse=1.0,
                pooled_oof_rmse=1.0,
            )
        )
        projected.append(
            _selected_row(
                "FQK",
                seed,
                pooled_oof_brier=0.10,
                auroc=0.91,
                recall_at_0_5=0.88,
                precision_at_0_5=0.84,
                false_negative_rate=0.12,
                false_positive_rate=0.08,
            )
        )
        for control in fqk_control_ids:
            controls.append(
                _control_row(
                    "FQK",
                    control,
                    seed,
                    pooled_oof_brier=0.11,
                    auroc=0.90,
                    recall_at_0_5=0.87,
                    precision_at_0_5=0.82,
                    false_negative_rate=0.13,
                    false_positive_rate=0.09,
                )
            )
        a02.append(
            _selected_row(
                "FQK",
                seed,
                pooled_oof_brier=0.12,
                auroc=0.89,
                recall_at_0_5=0.86,
                precision_at_0_5=0.81,
                false_negative_rate=0.14,
                false_positive_rate=0.10,
            )
        )
    selected = {
        "summaries": projected,
        "control_summaries": controls,
        "a02_summaries": a02,
    }
    regimes = [{"qualified_dequantization_regime": True}]
    result = evaluate_exploratory_signal(selected, regimes)
    assert result["tracks"]["Q01b"]["status"] == "promising_for_new_protocol"
    assert result["tracks"]["FQK"]["status"] == "promising_for_new_protocol"

    selected["summaries"] = [
        {**row, "pooled_oof_brier": 0.20} if row["track_id"] == "FQK" else row
        for row in selected["summaries"]
    ]
    negative = evaluate_exploratory_signal(selected, regimes)
    assert negative["tracks"]["FQK"]["status"] == "valid_exploratory_negative"


def test_no_reporting_source_mentions_locked_payloads_as_inputs() -> None:
    source = (ROOT / "src/openqfuel/post_gate5_reporting.py").read_text(
        encoding="utf-8"
    )
    assert "load_development_records" in source
    assert 'calibration_rows_read": 0' in source
    assert 'final_test_rows_read": 0' in source
    assert "data/locked" not in source
    json.dumps(_config())
