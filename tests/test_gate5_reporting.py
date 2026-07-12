from __future__ import annotations

import csv
import json
from pathlib import Path

from openqfuel.gate4 import read_csv
from openqfuel.gate5_reporting import (
    evaluate_claim_boundary_diagnostics,
    evaluate_gate5_trigger,
    write_gate5_report,
)


ROOT = Path(__file__).resolve().parents[1]


def _write_rows(path: Path, rows: list[dict[str, object]]) -> None:
    fields = list(rows[0])
    fields.extend(sorted({key for row in rows for key in row if key not in fields}))
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _seed_row(family_id: str, seed: int, nrmse: float) -> dict[str, str]:
    return {
        "family_id": family_id,
        "model_family": "test_family",
        "trial_id": f"{family_id}-T01",
        "view": "primary",
        "candidate_role": "primary_candidate",
        "control_for": "",
        "advancement_basis": "candidate",
        "effective_qubits": "4" if family_id.startswith("Q") else "",
        "resolved_seed_index": str(seed),
        "status": "complete",
        "eligible_to_advance": "True",
        "fold_count": "5",
        "pooled_oof_nrmse": str(nrmse),
        "mean_regret_m_s": "1.0",
    }


def _regime_row(
    family_id: str,
    seed: int,
    fold: int,
    nrmse: float,
    control_for: str = "",
    advancement_basis: str = "candidate",
) -> dict[str, str]:
    return {
        "family_id": family_id,
        "candidate_role": (
            "primary_candidate"
            if not control_for
            else "interpretation_control_not_eligible_to_win"
        ),
        "control_for": control_for,
        "advancement_basis": advancement_basis,
        "seed_index": str(seed),
        "dimension": "fidelity",
        "value": "F1",
        "fold_id": f"CV{fold:02d}",
        "rows": "100",
        "nrmse": str(nrmse),
    }


def _passing_inputs():
    seeds = []
    regimes = []
    for seed in range(1, 21):
        seeds.extend(
            [
                _seed_row("C01", seed, 0.5),
                _seed_row("Q01", seed, 0.51),
            ]
        )
        for fold in range(1, 6):
            regimes.extend(
                [
                    _regime_row("C01", seed, fold, 0.7),
                    _regime_row("Q01", seed, fold, 0.4),
                    _regime_row(
                        "A01",
                        seed,
                        fold,
                        0.65,
                        control_for="Q01",
                        advancement_basis="control_ranked",
                    ),
                    _regime_row(
                        "C05",
                        seed,
                        fold,
                        0.6,
                        control_for="Q01",
                        advancement_basis="control_ranked",
                    ),
                ]
            )
    return seeds, regimes


def test_gate5_trigger_requires_all_three_frozen_conditions() -> None:
    seeds, regimes = _passing_inputs()
    trigger, _, regime_results = evaluate_gate5_trigger(
        seeds,
        regimes,
        bootstrap_replicates=500,
        permutation_replicates=2000,
    )
    assert trigger["trigger_passed"]
    assert trigger["condition_1_within_five_percent"]
    assert trigger["condition_2_reproducible_controlled_regime"]
    assert trigger["condition_3_twenty_seed_grouped_stability"]
    assert regime_results[0]["qualified_residual_regime"]


def test_gate5_trigger_fails_when_qml_exceeds_five_percent() -> None:
    seeds, regimes = _passing_inputs()
    for row in seeds:
        if row["family_id"] == "Q01":
            row["pooled_oof_nrmse"] = "0.6"
    trigger, _, _ = evaluate_gate5_trigger(
        seeds,
        regimes,
        bootstrap_replicates=200,
        permutation_replicates=500,
    )
    assert not trigger["trigger_passed"]
    assert not trigger["condition_1_within_five_percent"]


def test_no_eligible_finalist_still_writes_a_negative_report(tmp_path: Path) -> None:
    experiment_dir = tmp_path / "experiments"
    reporting_dir = tmp_path / "reporting"
    experiment_dir.mkdir()
    (experiment_dir / "phase1_seed_results.csv").write_text("\n", encoding="utf-8")
    (experiment_dir / "phase1_seed_regime_metrics.csv").write_text(
        "\n", encoding="utf-8"
    )
    (experiment_dir / "gate5_campaign_audit.json").write_text(
        json.dumps(
            {
                "source_commit": "test-source",
                "calibration_rows_read": 0,
                "final_test_rows_read": 0,
            }
        ),
        encoding="utf-8",
    )

    trigger = write_gate5_report(ROOT, experiment_dir, reporting_dir)

    assert not trigger["trigger_passed"]
    assert not trigger["evidence_contract_valid"]
    assert trigger["evidence_contract_errors"]
    assert trigger["technical_trigger_status"] == "UNAVAILABLE"
    assert trigger["recommendation"] == (
        "repair_or_complete_evidence_before_gate5_decision"
    )
    assert trigger["calibration_rows_read"] == 0
    assert trigger["final_test_rows_read"] == 0
    assert (experiment_dir / "algorithm_trigger_report.md").is_file()


def test_claim_boundary_diagnostics_cover_all_frozen_checks(tmp_path: Path) -> None:
    manifest = read_csv(ROOT / "data/processed/simulator/tuning_manifest.csv")
    qml_trials = [row for row in manifest if row["family_id"] in {"Q01", "Q02", "Q03"}]
    tuning_rows = []
    for row in qml_trials:
        parameters = json.loads(row["parameters_json"])
        for rung in (128, 256, 512, 1024):
            qml = {
                "task_key": f"{row['trial_id']}-r{rung}",
                "family_id": row["family_id"],
                "trial_id": row["trial_id"],
                "trial_order": row["trial_order"],
                "view": "primary",
                "rung_samples": str(rung),
                "matched_qubits": str(parameters["qubits"]),
                "resolved_seed_index": row["trial_order"],
                "candidate_role": "primary_candidate",
                "control_for": "",
                "advancement_basis": "candidate",
                "status": "complete",
                "pooled_oof_nrmse": "0.5",
            }
            tuning_rows.append(qml)
            for family_id, view in (
                ("A01", "primary"),
                ("C05", "compressed_c05"),
            ):
                tuning_rows.append(
                    {
                        **qml,
                        "task_key": (
                            f"{family_id}-{row['family_id']}-{row['trial_order']}-"
                            f"q{parameters['qubits']}-r{rung}"
                        ),
                        "family_id": family_id,
                        "trial_id": f"{family_id}-T{int(row['trial_order']):02d}",
                        "view": view,
                        "candidate_role": "interpretation_control_not_eligible_to_win",
                        "control_for": row["family_id"],
                        "advancement_basis": "qml_matched",
                        "pooled_oof_nrmse": "0.6",
                    }
                )
    _write_rows(tmp_path / "phase1_tuning_results.csv", tuning_rows)

    regime_values = {
        "fidelity": "F1",
        "uncertainty_family": "U0",
        "base_trajectory_family": "N",
        "boundary_or_tail": "false",
        "reference_feasible_status": "no_reference_feasible",
    }
    tuning_regime_rows = []
    for row in tuning_rows:
        for fold in range(1, 6):
            for dimension, value in regime_values.items():
                tuning_regime_rows.append(
                    {
                        "task_key": row["task_key"],
                        "fold_id": f"CV{fold:02d}",
                        "dimension": dimension,
                        "value": value,
                        "nrmse": "0.4",
                    }
                )
    _write_rows(tmp_path / "phase1_tuning_regime_metrics.csv", tuning_regime_rows)

    kernel_fields = {
        "feature_scale": "1.0",
        "rung_samples": "128",
        "training_rows": "128",
        "centered_kernel_target_alignment": "0.2",
        "off_diagonal_mean": "0.1",
        "off_diagonal_std": "0.01",
        "effective_rank": "4.0",
        "regularized_condition_number": "10.0",
        "kernel_rows": "128",
        "nystrom_landmarks": "64",
    }
    fold_rows = [
        {
            "task_key": "Q01-tuning",
            "family_id": "Q01",
            "fold_id": f"CV{fold:02d}",
            **kernel_fields,
        }
        for fold in range(1, 6)
    ]
    fold_rows.extend(
        {
            "family_id": family_id,
            "view": view,
            "cost_fitted_trainable_parameter_count": count,
        }
        for family_id, view, count in (
            ("A01", "primary", "65"),
            ("C05", "compressed_c05", "129"),
        )
    )
    _write_rows(tmp_path / "phase1_tuning_fold_metrics.csv", fold_rows)

    selected_trials = {
        family_id: next(row for row in qml_trials if row["family_id"] == family_id)
        for family_id in ("Q01", "Q02", "Q03")
    }
    seed_rows = []
    for family_id, trial in selected_trials.items():
        parameters = json.loads(trial["parameters_json"])
        for seed in range(1, 21):
            qml = {
                "task_key": f"{family_id}-seed-{seed}",
                "task_signature": f"sig-{family_id}-{seed}",
                "family_id": family_id,
                "trial_id": trial["trial_id"],
                "trial_order": trial["trial_order"],
                "view": "primary",
                "rung_samples": "1024",
                "matched_qubits": str(parameters["qubits"]),
                "resolved_seed_index": str(seed),
                "candidate_role": "primary_candidate",
                "control_for": "",
                "advancement_basis": "candidate",
                "status": "complete",
                "eligible_to_advance": "True",
            }
            seed_rows.append(qml)
            for control_id, view in (
                ("A01", "primary"),
                ("C05", "compressed_c05"),
            ):
                seed_rows.append(
                    {
                        **qml,
                        "task_key": f"{control_id}-{family_id}-seed-{seed}",
                        "task_signature": f"sig-{control_id}-{family_id}-{seed}",
                        "family_id": control_id,
                        "trial_id": f"{control_id}-T{int(trial['trial_order']):02d}",
                        "view": view,
                        "candidate_role": "interpretation_control_not_eligible_to_win",
                        "control_for": family_id,
                        "advancement_basis": "qml_matched",
                    }
                )
    _write_rows(tmp_path / "phase1_seed_results.csv", seed_rows)

    seed_fold_rows = []
    for row in seed_rows:
        if row["family_id"] not in {"Q01", "Q02", "Q03"}:
            continue
        for fold in range(1, 6):
            base = {
                "task_key": row["task_key"],
                "task_signature": row["task_signature"],
                "family_id": row["family_id"],
                "candidate_role": "primary_candidate",
                "fold_id": f"CV{fold:02d}",
                "feature_scale": "1.0",
                "rung_samples": "1024",
                "training_rows": "1024",
            }
            if row["family_id"] == "Q01":
                seed_fold_rows.append({**base, **kernel_fields})
            else:
                seed_fold_rows.append(
                    {
                        **base,
                        "cost_optimization_success": "True",
                        "cost_optimization_message": "converged",
                        "cost_loss_improvement": "0.1",
                        "cost_gradient_norm_proxy": "0.01",
                        "cost_parameter_count": "33",
                        "cost_logical_circuit_depth": "12",
                        "cost_two_qubit_gate_count": "8",
                        "feasibility_optimization_success": "True",
                        "feasibility_optimization_message": "converged",
                        "feasibility_loss_improvement": "0.1",
                        "feasibility_gradient_norm_proxy": "0.01",
                        "feasibility_parameter_count": "33",
                        "training_wall_time_s": "1.0",
                        "inference_wall_time_s": "0.1",
                    }
                )
    _write_rows(tmp_path / "phase1_seed_fold_metrics.csv", seed_fold_rows)

    regime_rows = []
    for row in seed_rows:
        for fold in range(1, 6):
            for dimension, value in regime_values.items():
                regime_rows.append(
                    {
                        "task_key": row["task_key"],
                        "task_signature": row["task_signature"],
                        "family_id": row["family_id"],
                        "fold_id": f"CV{fold:02d}",
                        "dimension": dimension,
                        "value": value,
                        "nrmse": "0.4",
                    }
                )
    _write_rows(tmp_path / "phase1_seed_regime_metrics.csv", regime_rows)

    diagnostics = evaluate_claim_boundary_diagnostics(ROOT, tmp_path)

    assert diagnostics["status"] == "complete"
    assert all(diagnostics["checks"].values())
