from __future__ import annotations

import csv
import json
import shutil
import subprocess
from pathlib import Path

import pytest

from openqfuel.gate4 import read_csv, sha256_file
from openqfuel.gate5_reporting import (
    D006_IMMUTABLE_EVIDENCE_PATHS,
    D007_IMPLEMENTATION_PATHS,
    REPORTING_PACKAGE_ARTIFACTS,
    _assert_d007_candidate_snapshot,
    _scientific_elimination_evidence,
    evaluate_claim_boundary_diagnostics,
    evaluate_gate5_trigger,
    validate_campaign_evidence,
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


def test_no_eligible_finalist_writes_unavailable_repair_report(
    tmp_path: Path,
) -> None:
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

    trigger = write_gate5_report(
        ROOT, experiment_dir, reporting_dir, unpublished=True
    )

    assert not trigger["trigger_passed"]
    assert not trigger["evidence_contract_valid"]
    assert trigger["evidence_contract_errors"]
    assert trigger["technical_trigger_status"] == "UNAVAILABLE"
    assert trigger["recommendation"] == (
        "repair_or_complete_evidence_before_gate5_decision"
    )
    assert trigger["calibration_rows_read"] == 0
    assert trigger["final_test_rows_read"] == 0
    assert trigger["reporting_provenance"]["mode"] == "unpublished_evaluation"
    assert len(trigger["reporting_provenance"]["reporting_module_sha256"]) == 64
    assert (experiment_dir / "algorithm_trigger_report.md").is_file()
    package = json.loads(
        (experiment_dir / "gate5_reporting_package.json").read_text(
            encoding="utf-8"
        )
    )
    assert package["status"] == "complete"
    assert set(package["artifact_sha256"]) == set(REPORTING_PACKAGE_ARTIFACTS)
    bases = {"experiment": experiment_dir, "reporting": reporting_dir}
    for label, (location, filename) in REPORTING_PACKAGE_ARTIFACTS.items():
        assert package["artifact_sha256"][label] == sha256_file(
            bases[location] / filename
        )


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


def test_real_terminal_nonadvancement_is_complete_negative_evidence(
    tmp_path: Path,
) -> None:
    source = ROOT / "experiments"
    experiment_dir = tmp_path / "experiments"
    reporting_dir = tmp_path / "reporting"
    shutil.copytree(source, experiment_dir)
    reporting_dir.mkdir()
    audit = json.loads(
        (experiment_dir / "gate5_campaign_audit.json").read_text(encoding="utf-8")
    )
    dispositions, errors = _scientific_elimination_evidence(
        ROOT, experiment_dir, audit
    )
    assert not errors
    assert dispositions["Q02"]["eligible_tasks"] == 8
    assert dispositions["Q03"]["eligible_tasks"] == 4
    assert all(
        value["status"] == "verified_terminal_nonadvancing"
        for value in dispositions.values()
    )

    seed_rows = read_csv(experiment_dir / "phase1_seed_results.csv")
    regime_rows = read_csv(experiment_dir / "phase1_seed_regime_metrics.csv")
    assert not validate_campaign_evidence(
        ROOT, experiment_dir, audit, seed_rows, regime_rows
    )
    diagnostics = evaluate_claim_boundary_diagnostics(ROOT, experiment_dir)
    assert diagnostics["status"] == "complete"
    assert all(diagnostics["checks"].values())
    by_family = {
        row["family_id"]: row for row in diagnostics["variational_trainability"]
    }
    assert by_family["Q02"]["diagnostic_stage"] == "tuning_elimination_rung"
    assert by_family["Q02"]["fold_rows"] == 150
    assert by_family["Q03"]["fold_rows"] == 150
    assert by_family["Q02"]["seed_rerun_status"] == (
        "not_reached_under_frozen_eligibility"
    )

    trigger = write_gate5_report(
        ROOT, experiment_dir, reporting_dir, unpublished=True
    )
    assert trigger["decision_available"]
    assert trigger["evidence_contract_valid"]
    assert trigger["claim_boundary_diagnostics_complete"]
    assert trigger["technical_trigger_status"] == "FAIL"
    assert not trigger["trigger_passed"]
    assert trigger["selection_evidence_status"] == (
        "complete_with_scientific_eliminations"
    )
    assert trigger["calibration_rows_read"] == 0
    assert trigger["final_test_rows_read"] == 0
    assert trigger["reporting_provenance"]["mode"] == "unpublished_evaluation"


def test_gate5_report_publication_requires_explicit_d007_acceptance(
    tmp_path: Path,
) -> None:
    experiment_dir = tmp_path / "experiments"
    reporting_dir = tmp_path / "reporting"

    with pytest.raises(RuntimeError, match="explicit D007 acceptance"):
        write_gate5_report(ROOT, experiment_dir, reporting_dir)

    assert not experiment_dir.exists()
    assert not reporting_dir.exists()


def test_unpublished_gate5_report_cannot_target_official_outputs() -> None:
    with pytest.raises(RuntimeError, match="cannot write an official output path"):
        write_gate5_report(
            ROOT,
            ROOT / "experiments",
            ROOT / "data/processed/reporting",
            unpublished=True,
        )


def test_accepted_candidate_snapshot_anchors_code_and_raw_evidence(
    tmp_path: Path,
) -> None:
    for relative in (*D007_IMPLEMENTATION_PATHS, *D006_IMMUTABLE_EVIDENCE_PATHS):
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"frozen:{relative}\n", encoding="utf-8")
    subprocess.check_call(["git", "init", "-q"], cwd=tmp_path)
    subprocess.check_call(
        ["git", "config", "user.email", "gate5-test@example.invalid"], cwd=tmp_path
    )
    subprocess.check_call(
        ["git", "config", "user.name", "Gate 5 Test"], cwd=tmp_path
    )
    subprocess.check_call(["git", "add", "."], cwd=tmp_path)
    subprocess.check_call(["git", "commit", "-qm", "freeze candidate"], cwd=tmp_path)
    candidate = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=tmp_path, text=True
    ).strip()

    _assert_d007_candidate_snapshot(tmp_path, candidate)
    mutated = tmp_path / D006_IMMUTABLE_EVIDENCE_PATHS[0]
    mutated.write_text("mutated audit and digest map\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="immutable D006 evidence differs"):
        _assert_d007_candidate_snapshot(tmp_path, candidate)


def test_terminal_nonadvancement_semantics_fail_closed_on_selected_ranking(
    tmp_path: Path,
) -> None:
    experiment_dir = tmp_path / "experiments"
    experiment_dir.mkdir()
    for filename in (
        "phase1_tuning_results.csv",
        "phase1_tuning_fold_metrics.csv",
        "phase1_rung_rankings.csv",
    ):
        shutil.copy2(ROOT / "experiments" / filename, experiment_dir / filename)
    audit = json.loads(
        (ROOT / "experiments/gate5_campaign_audit.json").read_text(encoding="utf-8")
    )
    rankings = read_csv(experiment_dir / "phase1_rung_rankings.csv")
    q02 = next(row for row in rankings if row["family_id"] == "Q02")
    q02["selected_for_next_rung"] = "True"
    _write_rows(experiment_dir / "phase1_rung_rankings.csv", rankings)
    audit["evidence_sha256"]["phase1_rung_rankings.csv"] = sha256_file(
        experiment_dir / "phase1_rung_rankings.csv"
    )

    dispositions, errors = _scientific_elimination_evidence(
        ROOT, experiment_dir, audit
    )
    assert "Q02" not in dispositions
    assert any("Q02 ranking" in error for error in errors)
