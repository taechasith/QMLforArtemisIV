from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import numpy as np
import pytest

import openqfuel.gate5 as gate5_module
from openqfuel.gate4 import read_yaml
from openqfuel.gate5 import (
    RUNNER_ACCEPTED_STATUS,
    TargetStandardizer,
    deterministic_group_folds,
    execute_trial,
    fitted_trainable_parameter_count,
    fit_fold_features,
    gate5_preflight,
    initial_execution_plan,
    load_fold_checkpoint,
    load_trial,
    matched_qubits_for_trial,
    nested_training_indices,
    rank_rung_summaries,
    trial_seed,
    write_fold_checkpoint,
)
from openqfuel.models import PhysicsResidualRegressor, build_classical_regressor
from openqfuel.qml import HybridQuantumResidualRegressor, VariationalQuantumRegressor


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/phase1_benchmark.yaml"


def test_group_folds_are_deterministic_complete_and_label_agnostic() -> None:
    groups = [f"G{index:02d}" for index in range(1, 13)]
    strata = {
        group: (f"U{(index - 1) % 5}", "T" if index > 8 else "C")
        for index, group in enumerate(groups, start=1)
    }
    first = deterministic_group_folds(groups, 20260710, 5, strata)
    second = deterministic_group_folds(list(reversed(groups)), 20260710, 5, strata)
    assert first == second
    assert set(first) == set(groups)
    assert sorted(Counter(first.values()).values()) == [2, 2, 2, 3, 3]
    for uncertainty in {value[0] for value in strata.values()}:
        assigned = [
            first[group] for group in groups if strata[group][0] == uncertainty
        ]
        assert len(assigned) == len(set(assigned))


def test_learning_rows_are_nested_and_ignore_outcomes() -> None:
    records = [
        {"scenario_id": f"F1-G01-{index:06d}", "outcomes": {"target": index}}
        for index in range(1, 40)
    ]
    eligible = np.arange(len(records))
    small = nested_training_indices(records, eligible, 8, 7)
    large = nested_training_indices(records, eligible, 16, 7)
    assert set(small).issubset(set(large))
    for record in records:
        record["outcomes"]["target"] *= -1000
    np.testing.assert_array_equal(
        small, nested_training_indices(records, eligible, 8, 7)
    )


def test_initial_plan_preserves_trials_and_exactly_matches_qml_dimensions() -> None:
    rows = initial_execution_plan(ROOT)
    assert len(rows) == 450
    assert len({row["task_id"] for row in rows}) == len(rows)
    qml = [row for row in rows if row["family_id"] in {"Q01", "Q02", "Q03"}]
    matched = [
        row
        for row in rows
        if row["family_id"] == "A01" or row["view"] == "compressed_c05"
    ]
    assert len(qml) == 90
    assert len(matched) == 180
    assert Counter(row["effective_qubits"] for row in matched) == {
        4: 60,
        6: 60,
        8: 60,
    }
    control_keys = {
        (row["family_id"], row["trial_order"], row["effective_qubits"])
        for row in matched
    }
    for row in qml:
        key = (row["trial_order"], row["effective_qubits"])
        assert ("A01", *key) in control_keys
        assert ("C05", *key) in control_keys
    assert [matched_qubits_for_trial(index) for index in (1, 2, 3, 4)] == [
        4,
        6,
        8,
        4,
    ]


def test_initial_plan_status_follows_runner_acceptance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = {
        "gate5_runner_freeze": {
            "status": "d005_candidate_pending_human_acceptance"
        }
    }
    monkeypatch.setattr(gate5_module, "read_yaml", lambda _: config)
    assert {row["execution_status"] for row in initial_execution_plan(ROOT)} == {
        "blocked_pending_d005_acceptance"
    }

    config["gate5_runner_freeze"]["status"] = RUNNER_ACCEPTED_STATUS
    assert {row["execution_status"] for row in initial_execution_plan(ROOT)} == {
        "blocked_pending_d006_acceptance"
    }
    config["gate5_runner_freeze"]["research_fit_authorized"] = True
    assert {row["execution_status"] for row in initial_execution_plan(ROOT)} == {
        "ready"
    }


def test_trial_seed_defaults_to_trial_order_and_supports_frozen_reruns() -> None:
    trial = load_trial(ROOT, "C01-T01")
    assert trial_seed(ROOT, trial) == 2215023969
    assert trial_seed(ROOT, trial, seed_index=20) == 621220452
    with pytest.raises(ValueError, match=r"C01 seed_index=31"):
        trial_seed(ROOT, trial, seed_index=31)


def test_fitted_parameter_count_covers_linear_and_mlp_arrays() -> None:
    linear = type("Linear", (), {})()
    linear.coef_ = np.zeros((2, 3))
    linear.intercept_ = np.zeros(2)
    assert fitted_trainable_parameter_count(linear) == 8

    mlp = type("MLP", (), {})()
    mlp.coefs_ = [np.zeros((3, 4)), np.zeros((4, 1))]
    mlp.intercepts_ = [np.zeros(4), np.zeros(1)]
    assert fitted_trainable_parameter_count(mlp) == 21


def test_execute_trial_records_resolved_seed_in_signature_and_outputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = {
        "gate5_runner_freeze": {
            "status": RUNNER_ACCEPTED_STATUS,
            "research_fit_authorized": True,
        },
        "governance": {"final_payload_root": "locked/final"},
        "targets": {"primary_regression": "cost", "feasibility": "feasible"},
        "tuning": {"grouped_cv_folds": 1},
        "scenario_design": {"master_seed": 7},
        "analysis": {
            "feasibility_threshold": 0.5,
            "infeasible_regret_penalty_m_s": 20.0,
        },
    }
    records = [
        {
            "group_id": group_id,
            "decision_set_id": decision_set_id,
            "outcomes": {"cost": cost, "feasible": feasible},
        }
        for group_id, decision_set_id, cost, feasible in (
            ("GTRAIN", "TRAIN-1", 1.0, 0),
            ("GTRAIN", "TRAIN-2", 2.0, 1),
            ("GTRAIN", "TRAIN-3", 3.0, 1),
            ("GVALID", "VALID-1", 4.0, 1),
            ("GVALID", "VALID-1", 5.0, 0),
            ("GVALID", "VALID-2", 6.0, 1),
            ("GVALID", "VALID-2", 7.0, 0),
        )
    ]
    trial = load_trial(ROOT, "C01-T01")
    training_seeds = {1: 101, 20: 202}

    class DummyRegressor:
        def fit(self, x: np.ndarray, y: np.ndarray) -> "DummyRegressor":
            return self

        def predict(self, x: np.ndarray) -> np.ndarray:
            return np.zeros(x.shape[0])

    class DummyClassifier:
        def fit(self, x: np.ndarray, y: np.ndarray) -> "DummyClassifier":
            return self

        def predict_proba(self, x: np.ndarray) -> np.ndarray:
            probability = np.linspace(0.25, 0.75, x.shape[0])
            return np.column_stack((1.0 - probability, probability))

    monkeypatch.setattr(gate5_module, "read_yaml", lambda _: config)
    monkeypatch.setattr(gate5_module, "_clean_source_commit", lambda _: "abc123")
    monkeypatch.setattr(
        gate5_module, "load_development_records", lambda root, raw: (records, [])
    )
    monkeypatch.setattr(
        gate5_module, "audit_development_records", lambda records, manifest, raw: {}
    )
    monkeypatch.setattr(gate5_module, "load_trial", lambda root, trial_id: trial)
    monkeypatch.setattr(
        gate5_module,
        "trial_seed",
        lambda root, raw, seed_index=None: training_seeds[int(seed_index)],
    )
    monkeypatch.setattr(
        gate5_module,
        "fold_manifest_rows",
        lambda raw, manifest: [
            {"group_id": "GVALID", "fold_id": "CV01"},
            {"group_id": "GTRAIN", "fold_id": "CV02"},
        ],
    )
    monkeypatch.setattr(
        gate5_module,
        "fit_fold_features",
        lambda train, validation, raw, projected_qubits=None: (
            np.zeros((len(train), 2)),
            np.zeros((len(validation), 2)),
        ),
    )
    monkeypatch.setattr(
        gate5_module,
        "_build_models",
        lambda raw, seed, view: (DummyRegressor(), DummyClassifier()),
    )
    monkeypatch.setattr(
        gate5_module,
        "_regime_diagnostics",
        lambda *args: [{"fold_id": args[-1], "dimension": "test"}],
    )

    default = execute_trial(ROOT, trial.trial_id, tmp_path / "default")
    rerun = execute_trial(
        ROOT, trial.trial_id, tmp_path / "rerun", seed_index=20
    )
    assert (default["seed_index"], default["training_seed"]) == (1, 101)
    assert (rerun["seed_index"], rerun["training_seed"]) == (20, 202)
    assert default["task_signature"] != rerun["task_signature"]
    assert rerun["end_to_end_wall_time_s"] > 0.0

    checkpoint = json.loads(
        (tmp_path / "rerun/fold_CV01.json").read_text(encoding="utf-8")
    )
    assert (checkpoint["seed_index"], checkpoint["training_seed"]) == (20, 202)
    assert (
        checkpoint["fold_metrics"]["seed_index"],
        checkpoint["fold_metrics"]["training_seed"],
    ) == (20, 202)
    assert checkpoint["fold_metrics"]["fold_end_to_end_wall_time_s"] > 0.0

    training_seeds[20] = 303
    changed_training_seed = execute_trial(
        ROOT, trial.trial_id, tmp_path / "changed", seed_index=20
    )
    assert changed_training_seed["task_signature"] != rerun["task_signature"]


def test_ranking_preserves_required_qubits_and_frozen_ties() -> None:
    summaries = []
    for order, qubits in enumerate((4, 4, 6, 6, 8, 8), start=1):
        summaries.append(
            {
                "eligible_to_advance": True,
                "pooled_oof_nrmse": 0.1 + order * 0.01,
                "mean_regret_m_s": 1.0,
                "trial": {
                    "trial_id": f"Q02-T{order:02d}",
                    "model_family": "variational_quantum_regressor",
                    "parameters": {
                        "qubits": qubits,
                        "data_reupload_layers": 1,
                        "entangle": False,
                    },
                },
            }
        )
    ranking = rank_rung_summaries(summaries, retain=4, preserve_required_qubits=True)
    selected = [row for row in ranking if row["selected_for_next_rung"]]
    assert len(selected) == 4
    assert {row["effective_qubits"] for row in selected} == {4, 6, 8}


def test_target_standardization_is_training_only_and_invertible() -> None:
    scaler = TargetStandardizer.fit([2.0, 4.0, 6.0])
    values = np.array([-1.0, 0.0, 8.0])
    np.testing.assert_allclose(
        scaler.inverse(scaler.transform(values)), values, atol=1e-12
    )
    with pytest.raises(ValueError):
        TargetStandardizer.fit([1.0, 1.0])


def test_fold_checkpoints_are_atomic_and_signature_guarded(tmp_path: Path) -> None:
    path = tmp_path / "fold_CV01.json"
    checkpoint = {"task_signature": "abc", "fold_metrics": {"nrmse": 0.1}}
    write_fold_checkpoint(path, checkpoint)
    assert load_fold_checkpoint(path, "abc") == checkpoint
    assert not path.with_suffix(".json.tmp").exists()
    with pytest.raises(PermissionError, match="signature mismatch"):
        load_fold_checkpoint(path, "different")


def test_fold_transforms_do_not_fit_on_validation_outlier() -> None:
    config = read_yaml(CONFIG)

    def record(value: float) -> dict[str, object]:
        inputs = {name: value for name in config["features"]["numeric"]}
        inputs.update({name: value for name in config["features"]["physics_derived"]})
        inputs.update({name: "A" for name in config["features"]["categorical"]})
        return {"inputs": inputs}

    train = [record(float(index)) for index in range(1, 10)]
    first_train, _ = fit_fold_features(train, [record(10.0)], config)
    second_train, _ = fit_fold_features(train, [record(1e12)], config)
    np.testing.assert_allclose(first_train, second_train)


def test_residual_factories_use_explicit_physical_baseline_column() -> None:
    model = build_classical_regressor(
        "physics_residual",
        {
            "residual_estimator": "ridge",
            "alpha": 0.1,
            "max_leaf_nodes": 15,
            "learning_rate": 0.03,
        },
        seed=3,
        low_fidelity_column=0,
    )
    assert isinstance(model, PhysicsResidualRegressor)
    assert model.low_fidelity_column == 0


def test_hybrid_residual_does_not_encode_the_appended_baseline() -> None:
    circuit = np.array(
        [[value, -value, value / 2, 0.25] for value in np.linspace(-0.5, 0.5, 6)]
    )
    baseline = np.linspace(-0.2, 0.2, 6)
    x = np.column_stack((circuit, baseline))
    y = baseline + 0.1 * circuit[:, 0]
    model = HybridQuantumResidualRegressor(
        low_fidelity_column=-1,
        n_qubits=4,
        layers=1,
        maximum_optimizer_iterations=2,
        seed=4,
    ).fit(x, y)
    shifted = x.copy()
    shifted[:, -1] += 2.0
    np.testing.assert_allclose(model.predict(shifted) - model.predict(x), 2.0)


def test_variational_fit_exposes_d004_optimizer_diagnostics() -> None:
    x = np.array(
        [[value, -value, value / 2, 0.25] for value in np.linspace(-0.5, 0.5, 5)]
    )
    model = VariationalQuantumRegressor(
        n_qubits=4,
        layers=1,
        maximum_optimizer_iterations=2,
        seed=12,
    ).fit(x, 0.2 + 0.3 * x[:, 0])
    assert np.isfinite(model.initial_loss_)
    assert np.isfinite(model.training_loss_)
    assert model.loss_improvement_ == pytest.approx(
        model.initial_loss_ - model.training_loss_
    )
    assert model.objective_evaluations_ > 0


def test_real_preflight_reads_development_only_and_keeps_final_blind() -> None:
    audit, folds = gate5_preflight(ROOT)
    assert audit["rows"] == 39000
    assert audit["decision_sets"] == 7800
    assert audit["calibration_rows_read"] == 0
    assert audit["final_test_rows_read"] == 0
    assert len(folds) == 12


def test_research_execution_is_blocked_without_d005_acceptance(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        gate5_module,
        "read_yaml",
        lambda _: {
            "gate5_runner_freeze": {
                "status": "d005_candidate_pending_human_acceptance"
            }
        },
    )
    with pytest.raises(PermissionError, match="accepts the active runner contract"):
        execute_trial(ROOT, "C01-T01", tmp_path)


def test_real_d006_candidate_blocks_research_fitting(tmp_path: Path) -> None:
    with pytest.raises(PermissionError, match="active runner contract"):
        execute_trial(ROOT, "C01-T01", tmp_path)
