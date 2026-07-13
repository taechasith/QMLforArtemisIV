"""Frozen development-only reporting and Gate 5 trigger evaluation."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import subprocess
from collections import defaultdict
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

import numpy as np
import yaml

from .gate4 import read_csv, sha256_file
from .gate5 import _clean_source_commit, validate_development_output_path
from .phase1_analysis import (
    holm_adjust,
    paired_bootstrap_mean_interval,
    paired_sign_permutation_pvalue,
)


CLASSICAL_IDS = ("C01", "C02", "C03", "C04", "C05", "C06")
QML_IDS = ("Q01", "Q02", "Q03")
SEED_COUNT = 20
RELATIVE_GAP_LIMIT = 0.05
FOLD_IDS = {"CV01", "CV02", "CV03", "CV04", "CV05"}
FROZEN_QML_RETAIN_AT_128 = 15
TERMINAL_NONADVANCEMENT_ERROR = (
    "Too few eligible trials to satisfy the frozen retention count"
)
D007_IMPLEMENTATION_PATHS = (
    "src/openqfuel/gate5_reporting.py",
    "scripts/report_gate5_results.py",
    "scripts/make_gate5_result_figures.py",
)
D006_IMMUTABLE_EVIDENCE_PATHS = (
    "experiments/gate5_campaign_audit.json",
    "experiments/phase1_rung_rankings.csv",
    "experiments/phase1_seed_fold_metrics.csv",
    "experiments/phase1_seed_regime_metrics.csv",
    "experiments/phase1_seed_results.csv",
    "experiments/phase1_tuning_fold_metrics.csv",
    "experiments/phase1_tuning_regime_metrics.csv",
    "experiments/phase1_tuning_results.csv",
)
REPORTING_PACKAGE_ARTIFACTS = {
    "algorithm_trigger_report": ("experiment", "algorithm_trigger_report.md"),
    "claim_boundary_diagnostics": (
        "experiment",
        "gate5_claim_boundary_diagnostics.json",
    ),
    "model_registry": ("experiment", "phase1_model_registry.yaml"),
    "model_summary": ("reporting", "gate5_model_summary.csv"),
    "regime_trigger": ("reporting", "gate5_regime_trigger.csv"),
    "trigger_summary": ("experiment", "gate5_trigger_summary.json"),
}


def _assert_d007_candidate_snapshot(root: Path, candidate_commit: str) -> None:
    """Anchor implementation and immutable D006 evidence to accepted Git bytes."""
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", candidate_commit, "HEAD"],
        cwd=root,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if ancestor.returncode != 0:
        raise RuntimeError(
            "Accepted D007 candidate commit does not exist in current Git history"
        )
    mismatches: list[str] = []
    for relative in (*D007_IMPLEMENTATION_PATHS, *D006_IMMUTABLE_EVIDENCE_PATHS):
        try:
            accepted = subprocess.check_output(
                ["git", "show", f"{candidate_commit}:{relative}"],
                cwd=root,
                stderr=subprocess.DEVNULL,
            )
        except subprocess.CalledProcessError:
            mismatches.append(f"{relative} (absent from accepted candidate)")
            continue
        path = root / relative
        if not path.is_file() or path.read_bytes() != accepted:
            mismatches.append(relative)
    if mismatches:
        raise RuntimeError(
            "Current reporting implementation or immutable D006 evidence differs "
            "from the accepted D007 candidate: " + ", ".join(mismatches)
        )


def assert_gate5_report_regeneration_authorized(root: Path) -> dict[str, Any]:
    """Fail closed until the post-outcome D007 reporting rule is accepted."""
    config_path = root / "configs/phase1_benchmark.yaml"
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    freeze = config.get("gate5_runner_freeze", {})
    refinement = freeze.get("post_fit_reporting_refinement")
    authorized = freeze.get("report_regeneration_authorized")
    candidate_commit = str(freeze.get("d007_accepted_candidate_commit", ""))
    if (
        refinement != "d007_accepted"
        or authorized is not True
        or re.fullmatch(r"[0-9a-f]{40}", candidate_commit) is None
    ):
        raise RuntimeError(
            "Gate 5 report regeneration is not authorized: explicit D007 "
            "acceptance, its 40-character candidate commit, and "
            "report_regeneration_authorized=true are required"
        )
    _assert_d007_candidate_snapshot(root, candidate_commit)
    return freeze


def _bool(value: Any) -> bool:
    return str(value).lower() == "true"


def _float(value: Any) -> float:
    return float(str(value))


def _seed_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _stable_seed(*values: str) -> int:
    digest = hashlib.sha256("|".join(values).encode()).hexdigest()
    return int(digest[:8], 16)


def _write_csv(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    if not rows:
        rows = [{"status": "no_eligible_rows"}]
    leading = list(rows[0])
    trailing = sorted({key for row in rows for key in row if key not in leading})
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[*leading, *trailing],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def _reporting_package_paths(
    experiment_dir: Path,
    reporting_dir: Path,
) -> dict[str, Path]:
    bases = {"experiment": experiment_dir, "reporting": reporting_dir}
    return {
        label: bases[location] / filename
        for label, (location, filename) in REPORTING_PACKAGE_ARTIFACTS.items()
    }


def validate_gate5_reporting_package(
    root: Path,
    experiment_dir: Path,
    reporting_dir: Path,
    governance: Mapping[str, Any],
) -> dict[str, Any]:
    """Verify a complete official report package before rendering figures."""
    errors: list[str] = []
    package_path = experiment_dir / "gate5_reporting_package.json"
    if not package_path.is_file():
        raise RuntimeError("Gate 5 reporting package manifest is missing")
    package = json.loads(package_path.read_text(encoding="utf-8"))
    provenance = package.get("reporting_provenance", {})
    candidate_commit = governance.get("d007_accepted_candidate_commit")
    if package.get("status") != "complete":
        errors.append("reporting package is not complete")
    if not isinstance(provenance, Mapping):
        errors.append("reporting package provenance is missing")
        provenance = {}
    if (
        provenance.get("mode") != "official"
        or provenance.get("accepted_d007_candidate_commit") != candidate_commit
    ):
        errors.append("reporting package is not bound to accepted D007")
    head = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True
    ).strip()
    reporting_source = _text(provenance.get("reporting_source_commit"))
    if not reporting_source or subprocess.run(
        ["git", "merge-base", "--is-ancestor", reporting_source, head],
        cwd=root,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    ).returncode != 0:
        errors.append("reporting source commit is not in current Git history")
    actual_code_hashes = {
        "reporting_module_sha256": sha256_file(Path(__file__).resolve()),
        "reporting_script_sha256": sha256_file(
            root / "scripts/report_gate5_results.py"
        ),
        "figure_generator_sha256": sha256_file(
            root / "scripts/make_gate5_result_figures.py"
        ),
    }
    for field, actual in actual_code_hashes.items():
        if provenance.get(field) != actual:
            errors.append(f"reporting package {field} mismatch")

    artifact_paths = _reporting_package_paths(experiment_dir, reporting_dir)
    expected_hashes = package.get("artifact_sha256", {})
    if not isinstance(expected_hashes, Mapping) or set(expected_hashes) != set(
        artifact_paths
    ):
        errors.append("reporting package artifact map is incomplete")
    else:
        for label, path in artifact_paths.items():
            if not path.is_file() or sha256_file(path) != expected_hashes.get(label):
                errors.append(f"reporting package artifact mismatch: {label}")

    structured_provenance: list[tuple[str, Any]] = []
    trigger_path = artifact_paths["trigger_summary"]
    diagnostics_path = artifact_paths["claim_boundary_diagnostics"]
    registry_path = artifact_paths["model_registry"]
    if trigger_path.is_file():
        structured_provenance.append(
            (
                "trigger summary",
                json.loads(trigger_path.read_text(encoding="utf-8")).get(
                    "reporting_provenance"
                ),
            )
        )
    if diagnostics_path.is_file():
        structured_provenance.append(
            (
                "claim-boundary diagnostics",
                json.loads(diagnostics_path.read_text(encoding="utf-8")).get(
                    "reporting_provenance"
                ),
            )
        )
    if registry_path.is_file():
        structured_provenance.append(
            (
                "model registry",
                yaml.safe_load(registry_path.read_text(encoding="utf-8")).get(
                    "reporting_provenance"
                ),
            )
        )
    for label, embedded in structured_provenance:
        if embedded != provenance:
            errors.append(f"{label} provenance differs from reporting package")

    csv_provenance_fields = (
        "campaign_source_commit",
        "reporting_source_commit",
        "accepted_d007_candidate_commit",
        "reporting_module_sha256",
        "reporting_script_sha256",
        "figure_generator_sha256",
    )
    for label in ("model_summary", "regime_trigger"):
        path = artifact_paths[label]
        rows = _seed_rows(path) if path.is_file() else []
        if not rows or any(
            row.get(field, "") != _text(provenance.get(field))
            for row in rows
            for field in csv_provenance_fields
        ):
            errors.append(f"{label} provenance differs from reporting package")
    if not _zero_read_count(package.get("calibration_rows_read")) or not _zero_read_count(
        package.get("final_test_rows_read")
    ):
        errors.append("reporting package does not preserve locked-split reads")
    if errors:
        raise RuntimeError("Invalid Gate 5 reporting package: " + "; ".join(errors))
    return package


def _text(value: Any) -> str:
    return "" if value is None else str(value)


def _zero_read_count(value: Any) -> bool:
    try:
        return int(value) == 0
    except (TypeError, ValueError):
        return False


def _task_identity(row: Mapping[str, Any]) -> tuple[str, str, str, str, str]:
    return (
        _text(row.get("family_id")),
        _text(row.get("trial_id")),
        _text(row.get("view")),
        _text(row.get("rung_samples")),
        _text(row.get("matched_qubits")),
    )


def _scientific_elimination_evidence(
    root: Path,
    experiment_dir: Path,
    audit: Mapping[str, Any],
) -> tuple[dict[str, dict[str, Any]], list[str]]:
    """Verify D007's narrow, source-bound terminal-nonadvancement case.

    This does not reinterpret a failed or interrupted campaign. It recognizes
    only the exact D006 outcome where Q02/Q03 completed every authorized
    128-row task and fold, but too few tasks satisfied the frozen optimizer
    eligibility rule to fill the preregistered retain count of 15.
    """

    selection = audit.get("selection_manifest", {})
    if not isinstance(selection, Mapping) or selection.get("status") == "complete":
        return {}, []
    errors: list[str] = []
    if selection.get("status") != "incomplete_with_terminal_failures":
        return {}, ["selection status is not a recognized D006 disposition"]
    source_commit = _text(audit.get("source_commit"))
    if not source_commit:
        errors.append("campaign audit has no source commit")
    if not _zero_read_count(audit.get("calibration_rows_read")) or not _zero_read_count(
        audit.get("final_test_rows_read")
    ):
        errors.append("campaign audit does not preserve locked-split reads")
    task_states = audit.get("task_states", {})
    if not isinstance(task_states, Mapping) or not _zero_read_count(
        task_states.get("failed")
    ):
        errors.append("campaign has terminal task failures")

    missing = set(selection.get("missing_candidate_families", []))
    if missing != {"Q02", "Q03"}:
        errors.append("missing finalists are not exactly Q02 and Q03")
    if selection.get("missing_tuned_controls") not in ([], ()):  # type: ignore[comparison-overlap]
        errors.append("selection has missing tuned controls")
    finalist_families = [
        _text(row.get("family_id")) for row in selection.get("finalists", [])
    ]
    expected_families = set((*CLASSICAL_IDS, *QML_IDS))
    if (
        len(finalist_families) != len(set(finalist_families))
        or set(finalist_families) | missing != expected_families
        or set(finalist_families) & missing
        or selection.get("candidate_family_count") != len(expected_families)
        or selection.get("selected_family_count") != len(finalist_families)
    ):
        errors.append("selection family counts or identities are inconsistent")

    required_files = (
        "phase1_tuning_results.csv",
        "phase1_tuning_fold_metrics.csv",
        "phase1_rung_rankings.csv",
    )
    evidence_hashes = audit.get("evidence_sha256", {})
    for filename in required_files:
        path = experiment_dir / filename
        expected = evidence_hashes.get(filename) if isinstance(evidence_hashes, Mapping) else None
        if not path.is_file() or not expected:
            errors.append(f"missing source-bound elimination file: {filename}")
        elif sha256_file(path) != expected:
            errors.append(f"elimination evidence digest mismatch: {filename}")
    if errors:
        return {}, sorted(set(errors))

    tuning = _seed_rows(experiment_dir / "phase1_tuning_results.csv")
    folds = _seed_rows(experiment_dir / "phase1_tuning_fold_metrics.csv")
    rankings = _seed_rows(experiment_dir / "phase1_rung_rankings.csv")
    if audit.get("authorized_tuning_tasks") != len(tuning):
        errors.append("tuning-result count differs from campaign authorization")
    if isinstance(task_states, Mapping) and task_states.get("complete") != (
        int(audit.get("authorized_tuning_tasks", -1))
        + int(audit.get("authorized_seed_tasks", -1))
    ):
        errors.append("complete task count differs from all authorizations")

    frozen_manifest = read_csv(
        root / "data/processed/simulator/tuning_manifest.csv"
    )
    dispositions: dict[str, dict[str, Any]] = {}
    optimizer_fields = (
        "cost_optimization_success",
        "cost_optimization_message",
        "cost_loss_improvement",
        "cost_gradient_norm_proxy",
        "cost_parameter_count",
        "cost_logical_circuit_depth",
        "cost_two_qubit_gate_count",
        "feasibility_optimization_success",
        "feasibility_optimization_message",
        "feasibility_loss_improvement",
        "feasibility_gradient_norm_proxy",
        "feasibility_parameter_count",
        "training_wall_time_s",
        "inference_wall_time_s",
    )
    for family_id in sorted(missing):
        frozen_ids = {
            row["trial_id"] for row in frozen_manifest if row["family_id"] == family_id
        }
        family_results = [
            row
            for row in tuning
            if row.get("family_id") == family_id
            and row.get("candidate_role") == "primary_candidate"
        ]
        result_ids = {row.get("trial_id", "") for row in family_results}
        if len(family_results) != 30 or result_ids != frozen_ids:
            errors.append(f"{family_id} does not contain all 30 frozen tuning tasks")
            continue
        if any(
            row.get("stage") != "tuning"
            or row.get("status") != "complete"
            or row.get("source_commit") != source_commit
            or row.get("source_split") != "development"
            or row.get("rung_samples") != "128"
            or row.get("fold_count") != "5"
            or not row.get("task_signature")
            or not _zero_read_count(row.get("calibration_rows_read"))
            or not _zero_read_count(row.get("final_test_rows_read"))
            for row in family_results
        ):
            errors.append(f"{family_id} tuning tasks are not signed complete 128-row evidence")
            continue

        family_rankings = [
            row
            for row in rankings
            if row.get("family_id") == family_id
            and row.get("completed_rung") == "128"
            and row.get("next_rung") == "256"
        ]
        if (
            len(family_rankings) != 30
            or {row.get("trial_id", "") for row in family_rankings} != frozen_ids
            or any(
                row.get("task_status") != "nonadvancing"
                or row.get("advancement_error") != TERMINAL_NONADVANCEMENT_ERROR
                or _bool(row.get("selected_for_next_rung"))
                for row in family_rankings
            )
        ):
            errors.append(f"{family_id} ranking is not frozen terminal nonadvancement")
            continue

        results_by_key = {row["task_key"]: row for row in family_results}
        family_folds = [
            row
            for row in folds
            if row.get("family_id") == family_id
            and row.get("candidate_role") == "primary_candidate"
        ]
        folds_by_key: dict[str, list[Mapping[str, str]]] = defaultdict(list)
        for row in family_folds:
            folds_by_key[row.get("task_key", "")].append(row)
        if len(family_folds) != 150 or set(folds_by_key) != set(results_by_key):
            errors.append(f"{family_id} does not contain 150 matched tuning folds")
            continue

        recomputed_eligible: dict[str, bool] = {}
        fold_error = False
        for task_key, result in results_by_key.items():
            task_folds = folds_by_key[task_key]
            if (
                {row.get("fold_id", "") for row in task_folds} != FOLD_IDS
                or len(task_folds) != 5
                or any(
                    row.get("task_signature") != result.get("task_signature")
                    or row.get("source_commit") != source_commit
                    or row.get("source_split") != "development"
                    or row.get("family_id") != family_id
                    or row.get("trial_id") != result.get("trial_id")
                    or row.get("rung_samples") != "128"
                    or not _zero_read_count(row.get("calibration_rows_read"))
                    or not _zero_read_count(row.get("final_test_rows_read"))
                    or any(row.get(field, "") == "" for field in optimizer_fields)
                    for row in task_folds
                )
            ):
                fold_error = True
                break
            eligible = all(
                _bool(row["cost_optimization_success"])
                and _bool(row["feasibility_optimization_success"])
                and _bool(row["eligible_to_advance"])
                for row in task_folds
            )
            recomputed_eligible[task_key] = eligible
            if eligible != _bool(result.get("eligible_to_advance")):
                fold_error = True
                break
        if fold_error:
            errors.append(f"{family_id} fold diagnostics do not reproduce task eligibility")
            continue
        eligible_count = sum(recomputed_eligible.values())
        if eligible_count >= FROZEN_QML_RETAIN_AT_128:
            errors.append(f"{family_id} had enough eligible trials to advance")
            continue
        dispositions[family_id] = {
            "status": "verified_terminal_nonadvancing",
            "last_authorized_rung": 128,
            "blocked_next_rung": 256,
            "authorized_tasks": 30,
            "completed_folds": 150,
            "eligible_tasks": eligible_count,
            "required_retained_tasks": FROZEN_QML_RETAIN_AT_128,
            "reason": TERMINAL_NONADVANCEMENT_ERROR,
            "seed_rerun_status": "not_reached_under_frozen_eligibility",
        }
    if set(dispositions) != missing:
        errors.append("not every missing family is verified terminal nonadvancing")
    return dispositions, sorted(set(errors))


def validate_campaign_evidence(
    root: Path,
    experiment_dir: Path,
    audit: Mapping[str, Any],
    seed_rows: Sequence[Mapping[str, str]],
    regime_rows: Sequence[Mapping[str, str]],
) -> list[str]:
    """Return fail-closed provenance/completeness errors for Gate 5 reporting."""

    errors: list[str] = []
    source_commit = _text(audit.get("source_commit"))
    if not source_commit:
        errors.append("campaign audit has no source commit")
    if audit.get("status") != "complete":
        errors.append("campaign audit is not complete without terminal failures")
    if not _zero_read_count(audit.get("calibration_rows_read")):
        errors.append("campaign audit does not verify zero calibration reads")
    if not _zero_read_count(audit.get("final_test_rows_read")):
        errors.append("campaign audit does not verify zero final-test reads")

    contract = audit.get("campaign_contract", {})
    benchmark = audit.get("benchmark_audit", {})
    selection = audit.get("selection_manifest", {})
    for name, embedded in (
        ("campaign contract", contract),
        ("benchmark audit", benchmark),
        ("selection manifest", selection),
    ):
        if not isinstance(embedded, Mapping):
            errors.append(f"{name} is missing from the campaign audit")
            continue
        if _text(embedded.get("source_commit")) != source_commit:
            errors.append(f"{name} source commit does not match the campaign audit")
        if not _zero_read_count(embedded.get("calibration_rows_read")):
            errors.append(f"{name} does not verify zero calibration reads")
        if not _zero_read_count(embedded.get("final_test_rows_read")):
            errors.append(f"{name} does not verify zero final-test reads")
    if isinstance(benchmark, Mapping) and (
        benchmark.get("status") != "pass"
        or benchmark.get("scale_up_authorized") is not True
    ):
        errors.append("bounded benchmark did not authorize scale-up")
    elimination_dispositions, elimination_errors = _scientific_elimination_evidence(
        root, experiment_dir, audit
    )
    if isinstance(selection, Mapping) and selection.get("status") != "complete":
        missing = set(selection.get("missing_candidate_families", []))
        if elimination_errors or set(elimination_dispositions) != missing:
            errors.append("selection manifest is incomplete")
            errors.extend(
                f"selection elimination evidence: {error}"
                for error in elimination_errors
            )

    evidence_hashes = audit.get("evidence_sha256", {})
    if not isinstance(evidence_hashes, Mapping):
        errors.append("campaign audit has no evidence digest map")
    else:
        for filename in (
            "phase1_seed_results.csv",
            "phase1_seed_regime_metrics.csv",
            "phase1_seed_fold_metrics.csv",
            "phase1_tuning_results.csv",
            "phase1_tuning_fold_metrics.csv",
            "phase1_tuning_regime_metrics.csv",
            "phase1_rung_rankings.csv",
        ):
            path = experiment_dir / filename
            expected = evidence_hashes.get(filename)
            if not path.is_file() or not expected:
                errors.append(f"missing source-bound evidence file: {filename}")
            elif sha256_file(path) != expected:
                errors.append(f"evidence digest mismatch: {filename}")

    if audit.get("authorized_seed_tasks") != len(seed_rows):
        errors.append("seed-result row count differs from campaign authorization")
    task_states = audit.get("task_states", {})
    if not isinstance(task_states, Mapping) or not _zero_read_count(
        task_states.get("failed")
    ):
        errors.append("campaign contains terminal task failures")

    manifest = {
        row["trial_id"]: row
        for row in read_csv(root / "data/processed/simulator/tuning_manifest.csv")
    }
    seen_keys: set[str] = set()
    complete_by_signature: dict[str, Mapping[str, str]] = {}
    for row in seed_rows:
        task_key = row.get("task_key", "")
        if not task_key or task_key in seen_keys:
            errors.append("seed results contain a missing or duplicate task key")
        seen_keys.add(task_key)
        if row.get("stage") != "seed_rerun" or row.get("source_split") != "development":
            errors.append(
                f"seed task is outside the development rerun stage: {task_key}"
            )
        if row.get("source_commit") != source_commit:
            errors.append(f"seed task source commit mismatch: {task_key}")
        if not _zero_read_count(
            row.get("calibration_rows_read")
        ) or not _zero_read_count(row.get("final_test_rows_read")):
            errors.append(f"seed task does not verify locked split reads: {task_key}")
        frozen = manifest.get(row.get("trial_id", ""))
        if frozen is None or any(
            (
                row.get("family_id") != frozen.get("family_id"),
                row.get("model_family") != frozen.get("model_family"),
                row.get("trial_order") != frozen.get("trial_order"),
            )
        ):
            errors.append(
                f"seed task differs from the frozen tuning manifest: {task_key}"
            )
        signature = row.get("task_signature", "")
        if row.get("status") != "complete" or not signature:
            errors.append(f"seed task is not a signed completion: {task_key}")
        elif signature in complete_by_signature:
            errors.append("seed results contain a duplicate task signature")
        else:
            complete_by_signature[signature] = row

    if isinstance(selection, Mapping):
        finalist_ids = {_task_identity(row) for row in selection.get("finalists", [])}
        tuned_control_map = {
            _task_identity(row): set(
                filter(None, _text(row.get("control_for")).split(";"))
            )
            for row in selection.get("tuned_control_finalists", [])
        }
        qml_finalists = [
            row
            for row in selection.get("finalists", [])
            if row.get("family_id") in QML_IDS
        ]
        for row in seed_rows:
            identity = _task_identity(row)
            role = row.get("candidate_role")
            basis = row.get("advancement_basis", "")
            task_key = row.get("task_key", "")
            if role == "primary_candidate":
                if identity not in finalist_ids:
                    errors.append(
                        f"candidate seed task is not a frozen finalist: {task_key}"
                    )
                continue
            valid_control = False
            if "control_ranked" in basis:
                valid_control = identity in tuned_control_map and (
                    set(filter(None, row.get("control_for", "").split(";")))
                    == tuned_control_map.get(identity, set())
                )
            elif "qml_matched" in basis:
                controls_for = set(filter(None, row.get("control_for", "").split(";")))
                control_view_valid = (
                    row.get("family_id") == "A01" and row.get("view") == "primary"
                ) or (
                    row.get("family_id") == "C05"
                    and row.get("view") == "compressed_c05"
                )
                valid_control = control_view_valid and any(
                    _text(qml.get("trial_order")) == row.get("trial_order")
                    and _text(qml.get("matched_qubits")) == row.get("matched_qubits")
                    and qml.get("family_id") in controls_for
                    for qml in qml_finalists
                )
            if not valid_control:
                errors.append(
                    f"control seed task is not bound to frozen selection: {task_key}"
                )

    for row in regime_rows:
        signature = row.get("task_signature", "")
        seed_row = complete_by_signature.get(signature)
        if seed_row is None:
            errors.append("regime row is not bound to a signed seed task")
            continue
        comparisons = {
            "source_commit": "source_commit",
            "source_split": "source_split",
            "stage": "stage",
            "family_id": "family_id",
            "model_family": "model_family",
            "trial_id": "trial_id",
            "trial_order": "trial_order",
            "view": "view",
            "rung_samples": "rung_samples",
            "matched_qubits": "matched_qubits",
            "candidate_role": "candidate_role",
            "control_for": "control_for",
            "advancement_basis": "advancement_basis",
            "seed_index": "resolved_seed_index",
        }
        if any(
            row.get(left, "") != seed_row.get(right, "")
            for left, right in comparisons.items()
        ):
            errors.append(f"regime metadata differs from seed task: {signature}")
        if not _zero_read_count(
            row.get("calibration_rows_read")
        ) or not _zero_read_count(row.get("final_test_rows_read")):
            errors.append(f"regime row does not verify locked split reads: {signature}")
    return sorted(set(errors))


def evaluate_claim_boundary_diagnostics(
    root: Path,
    experiment_dir: Path,
) -> dict[str, Any]:
    """Summarize the mandatory D004 diagnostics without adding outcome thresholds."""

    paths = {
        "tuning": experiment_dir / "phase1_tuning_results.csv",
        "folds": experiment_dir / "phase1_tuning_fold_metrics.csv",
        "tuning_regimes": experiment_dir / "phase1_tuning_regime_metrics.csv",
        "seeds": experiment_dir / "phase1_seed_results.csv",
        "seed_folds": experiment_dir / "phase1_seed_fold_metrics.csv",
        "regimes": experiment_dir / "phase1_seed_regime_metrics.csv",
        "rankings": experiment_dir / "phase1_rung_rankings.csv",
    }
    rows = {
        name: _seed_rows(path) if path.is_file() else [] for name, path in paths.items()
    }
    audit_path = experiment_dir / "gate5_campaign_audit.json"
    audit = (
        json.loads(audit_path.read_text(encoding="utf-8"))
        if audit_path.is_file()
        else {}
    )
    eliminated, elimination_errors = _scientific_elimination_evidence(
        root, experiment_dir, audit
    )
    manifest = {
        row["trial_id"]: json.loads(row["parameters_json"])
        for row in read_csv(root / "data/processed/simulator/tuning_manifest.csv")
    }
    complete_tuning = [row for row in rows["tuning"] if row.get("status") == "complete"]
    expected_rungs = {128, 256, 512, 1024}
    rung_sets: dict[str, set[int]] = {}
    for label, selector in {
        "Q01": lambda row: row.get("family_id") == "Q01",
        "Q02": lambda row: row.get("family_id") == "Q02",
        "Q03": lambda row: row.get("family_id") == "Q03",
        "A01": lambda row: row.get("family_id") == "A01",
        "compressed_C05": lambda row: (
            row.get("family_id") == "C05" and row.get("view") == "compressed_c05"
        ),
    }.items():
        rung_sets[label] = {
            int(row["rung_samples"])
            for row in complete_tuning
            if selector(row) and row.get("rung_samples")
        }

    sensitivity: dict[tuple[str, int, float, bool, int], list[float]] = defaultdict(
        list
    )
    feature_scales: dict[str, set[float]] = defaultdict(set)
    entanglement_states: dict[str, set[bool]] = defaultdict(set)
    for row in complete_tuning:
        family_id = row.get("family_id", "")
        if family_id not in QML_IDS or not row.get("rung_samples"):
            continue
        parameters = manifest[row["trial_id"]]
        feature_scale = float(parameters["feature_scale"])
        entangle = bool(parameters["entangle"])
        qubits = int(parameters["qubits"])
        feature_scales[family_id].add(feature_scale)
        entanglement_states[family_id].add(entangle)
        if row.get("pooled_oof_nrmse"):
            sensitivity[
                (family_id, int(row["rung_samples"]), feature_scale, entangle, qubits)
            ].append(_float(row["pooled_oof_nrmse"]))

    q01_folds = [row for row in rows["folds"] if row.get("family_id") == "Q01"]
    q01_seed_folds = [
        row
        for row in rows["seed_folds"]
        if row.get("family_id") == "Q01"
        and row.get("candidate_role") == "primary_candidate"
    ]
    kernel_fields = (
        "centered_kernel_target_alignment",
        "off_diagonal_mean",
        "off_diagonal_std",
        "effective_rank",
        "regularized_condition_number",
        "kernel_rows",
        "nystrom_landmarks",
    )
    variational_seed_folds = [
        row
        for row in rows["seed_folds"]
        if row.get("family_id") in {"Q02", "Q03"}
        and row.get("candidate_role") == "primary_candidate"
    ]
    variational_tuning_folds = [
        row
        for row in rows["folds"]
        if row.get("family_id") in {"Q02", "Q03"}
        and row.get("candidate_role") == "primary_candidate"
    ]
    variational_fields = (
        "cost_optimization_success",
        "cost_optimization_message",
        "cost_loss_improvement",
        "cost_parameter_count",
        "cost_logical_circuit_depth",
        "cost_two_qubit_gate_count",
        "feasibility_optimization_success",
        "feasibility_optimization_message",
        "feasibility_loss_improvement",
        "feasibility_parameter_count",
        "training_wall_time_s",
        "inference_wall_time_s",
    )
    no_reference_rows = [
        row
        for row in rows["regimes"]
        if row.get("dimension") == "reference_feasible_status"
        and row.get("value") == "no_reference_feasible"
    ]
    controls = [
        row for row in rows["seeds"] if row.get("candidate_role") != "primary_candidate"
    ]
    a01_parameter_counts = sorted(
        {
            int(row["cost_fitted_trainable_parameter_count"])
            for row in rows["folds"]
            if row.get("family_id") == "A01"
            and row.get("cost_fitted_trainable_parameter_count", "") != ""
        }
    )
    compressed_c05_parameter_counts = sorted(
        {
            int(row["cost_fitted_trainable_parameter_count"])
            for row in rows["folds"]
            if row.get("family_id") == "C05"
            and row.get("view") == "compressed_c05"
            and row.get("cost_fitted_trainable_parameter_count", "") != ""
        }
    )

    def exact_control_coverage(
        candidate_rows: Sequence[Mapping[str, str]],
        all_rows: Sequence[Mapping[str, str]],
    ) -> bool:
        qml_rows = [
            row
            for row in candidate_rows
            if row.get("family_id") in QML_IDS
            and row.get("candidate_role") == "primary_candidate"
        ]
        if not qml_rows:
            return False
        for qml in qml_rows:
            for family_id, view in (
                ("A01", "primary"),
                ("C05", "compressed_c05"),
            ):
                if not any(
                    control.get("family_id") == family_id
                    and control.get("view") == view
                    and "qml_matched" in control.get("advancement_basis", "")
                    and qml["family_id"] in control.get("control_for", "").split(";")
                    and control.get("trial_order") == qml.get("trial_order")
                    and control.get("rung_samples") == qml.get("rung_samples")
                    and control.get("matched_qubits") == qml.get("matched_qubits")
                    and control.get("resolved_seed_index")
                    == qml.get("resolved_seed_index")
                    for control in all_rows
                ):
                    return False
        return True

    required_regime_dimensions = {
        "fidelity",
        "uncertainty_family",
        "base_trajectory_family",
        "boundary_or_tail",
        "reference_feasible_status",
    }

    def fixed_regime_coverage(
        result_rows: Sequence[Mapping[str, str]],
        metric_rows: Sequence[Mapping[str, str]],
    ) -> bool:
        coverage: dict[str, tuple[set[str], set[str]]] = {}
        for row in metric_rows:
            task_key = row.get("task_key", "")
            dimensions, folds = coverage.setdefault(task_key, (set(), set()))
            dimensions.add(row.get("dimension", ""))
            folds.add(row.get("fold_id", ""))
        task_keys = {
            row.get("task_key", "")
            for row in result_rows
            if row.get("status") == "complete" and row.get("task_key")
        }
        return bool(task_keys) and all(
            task_key in coverage
            and coverage[task_key][0] == required_regime_dimensions
            and coverage[task_key][1] == FOLD_IDS
            for task_key in task_keys
        )

    fixed_tuning_regime_coverage = fixed_regime_coverage(
        complete_tuning, rows["tuning_regimes"]
    )
    fixed_seed_regime_coverage = fixed_regime_coverage(rows["seeds"], rows["regimes"])

    def five_fold_task_coverage(selected: Sequence[Mapping[str, str]]) -> bool:
        by_task: dict[str, set[str]] = defaultdict(set)
        for row in selected:
            by_task[row.get("task_key", "")].add(row.get("fold_id", ""))
        return bool(by_task) and all(folds == FOLD_IDS for folds in by_task.values())

    q01_required_fields = (
        "feature_scale",
        "rung_samples",
        "training_rows",
        *kernel_fields,
    )
    variational_seed_rows = [
        row
        for row in rows["seeds"]
        if row.get("family_id") in {"Q02", "Q03"}
        and row.get("candidate_role") == "primary_candidate"
    ]
    expected_rung_order = (128, 256, 512, 1024)

    def authorized_rungs_complete(label: str, rungs: set[int]) -> bool:
        if rungs == expected_rungs:
            return True
        if label not in eliminated or not rungs:
            return False
        last_rung = int(eliminated[label]["last_authorized_rung"])
        expected_prefix = set(
            expected_rung_order[: expected_rung_order.index(last_rung) + 1]
        )
        return rungs == expected_prefix

    def variational_family_diagnostics_complete(family_id: str) -> bool:
        seed_rows = [
            row for row in variational_seed_rows if row["family_id"] == family_id
        ]
        seed_folds = [
            row for row in variational_seed_folds if row["family_id"] == family_id
        ]
        if seed_rows:
            selected = seed_folds
            seed_coverage = len(seed_rows) == SEED_COUNT
        elif family_id in eliminated and not elimination_errors:
            selected = [
                row
                for row in variational_tuning_folds
                if row["family_id"] == family_id
            ]
            seed_coverage = True
        else:
            return False
        return (
            bool(selected)
            and seed_coverage
            and five_fold_task_coverage(selected)
            and all(
                all(row.get(field, "") != "" for field in variational_fields)
                and "cost_gradient_norm_proxy" in row
                and "feasibility_gradient_norm_proxy" in row
                for row in selected
            )
        )

    checks = {
        "learning_curve_rungs_complete": all(
            authorized_rungs_complete(label, rungs)
            for label, rungs in rung_sets.items()
        ),
        "feature_scale_comparison_present": all(
            len(feature_scales[family_id]) >= 2 for family_id in QML_IDS
        ),
        "entanglement_removal_comparison_present": all(
            entanglement_states[family_id] == {False, True} for family_id in QML_IDS
        ),
        "q01_bandwidth_kernel_diagnostics_complete": bool(q01_folds)
        and five_fold_task_coverage(q01_folds)
        and len({row.get("task_key") for row in q01_seed_folds}) == 20
        and five_fold_task_coverage(q01_seed_folds)
        and all(
            all(row.get(field, "") != "" for field in q01_required_fields)
            for row in [*q01_folds, *q01_seed_folds]
        ),
        "variational_parameter_trainability_diagnostics_complete": all(
            variational_family_diagnostics_complete(family_id)
            for family_id in ("Q02", "Q03")
        ),
        "random_feature_controls_present": any(
            row.get("family_id") == "A01" for row in controls
        ),
        "compressed_parameter_controls_present": any(
            row.get("family_id") == "C05" and row.get("view") == "compressed_c05"
            for row in controls
        ),
        "control_parameter_counts_reported": bool(a01_parameter_counts)
        and bool(compressed_c05_parameter_counts),
        "same_index_tuning_controls_complete": exact_control_coverage(
            complete_tuning, complete_tuning
        ),
        "same_index_seed_controls_complete": exact_control_coverage(
            rows["seeds"], rows["seeds"]
        ),
        "all_fixed_tuning_regime_dimensions_and_folds_reported": fixed_tuning_regime_coverage,
        "all_fixed_seed_regime_dimensions_and_folds_reported": fixed_seed_regime_coverage,
        "no_reference_concentration_report_present": bool(no_reference_rows),
    }
    variational_summary = []
    for family_id in ("Q02", "Q03"):
        selected_seed_folds = [
            row for row in variational_seed_folds if row["family_id"] == family_id
        ]
        selected_tuning_folds = [
            row for row in variational_tuning_folds if row["family_id"] == family_id
        ]
        selected_seeds = [
            row for row in variational_seed_rows if row["family_id"] == family_id
        ]
        selected_tuning_tasks = [
            row
            for row in complete_tuning
            if row.get("family_id") == family_id
            and row.get("candidate_role") == "primary_candidate"
        ]
        if selected_seed_folds:
            selected = selected_seed_folds
            diagnostic_stage = "selected_configuration_seed_reruns"
            seed_rerun_status = "complete"
        else:
            selected = selected_tuning_folds
            diagnostic_stage = "tuning_elimination_rung"
            seed_rerun_status = (
                "not_reached_under_frozen_eligibility"
                if family_id in eliminated
                else "missing"
            )
        variational_summary.append(
            {
                "family_id": family_id,
                "diagnostic_stage": diagnostic_stage,
                "fold_rows": len(selected),
                "seed_rows": len(selected_seeds),
                "seed_rerun_status": seed_rerun_status,
                "seed_ineligibility_rate": (
                    float(
                        np.mean(
                            [
                                not _bool(row["eligible_to_advance"])
                                for row in selected_seeds
                            ]
                        )
                    )
                    if selected_seeds
                    else None
                ),
                "tuning_task_ineligibility_rate": (
                    float(
                        np.mean(
                            [
                                not _bool(row["eligible_to_advance"])
                                for row in selected_tuning_tasks
                            ]
                        )
                    )
                    if selected_tuning_tasks
                    and all(
                        row.get("eligible_to_advance", "") != ""
                        for row in selected_tuning_tasks
                    )
                    else None
                ),
                "cost_optimizer_failure_rate": (
                    float(
                        np.mean(
                            [
                                not _bool(row["cost_optimization_success"])
                                for row in selected
                            ]
                        )
                    )
                    if selected
                    else None
                ),
                "feasibility_optimizer_failure_rate": (
                    float(
                        np.mean(
                            [
                                not _bool(row["feasibility_optimization_success"])
                                for row in selected
                            ]
                        )
                    )
                    if selected
                    else None
                ),
                "parameter_counts": sorted(
                    {int(row["cost_parameter_count"]) for row in selected}
                ),
                "logical_circuit_depths": sorted(
                    {int(row["cost_logical_circuit_depth"]) for row in selected}
                ),
                "two_qubit_gate_counts": sorted(
                    {int(row["cost_two_qubit_gate_count"]) for row in selected}
                ),
                "mean_cost_loss_improvement": (
                    float(
                        np.mean(
                            [_float(row["cost_loss_improvement"]) for row in selected]
                        )
                    )
                    if selected
                    else None
                ),
                "gradient_norm_proxy_available_rows": sum(
                    row.get("cost_gradient_norm_proxy", "") != "" for row in selected
                ),
            }
        )
    kernel_summary = {}
    for field in kernel_fields:
        values = [
            _float(row[field])
            for row in [*q01_folds, *q01_seed_folds]
            if row.get(field, "") != "" and math.isfinite(_float(row[field]))
        ]
        kernel_summary[field] = {
            "minimum": min(values) if values else None,
            "maximum": max(values) if values else None,
        }
    no_reference_summary = []
    for family_id in (*CLASSICAL_IDS, *QML_IDS, "A01"):
        values = [
            _float(row["nrmse"])
            for row in no_reference_rows
            if row.get("family_id") == family_id and row.get("nrmse", "") != ""
        ]
        if values:
            no_reference_summary.append(
                {
                    "family_id": family_id,
                    "fold_seed_rows": len(values),
                    "mean_reported_nrmse": float(np.mean(values)),
                }
            )
    return {
        "status": "complete" if all(checks.values()) else "incomplete",
        "handling": "mandatory_report_only_pending_human_interpretation",
        "checks": checks,
        "learning_curve_rungs": {
            label: sorted(values) for label, values in rung_sets.items()
        },
        "learning_curve_dispositions": {
            label: (
                "full_four_rung_curve"
                if values == expected_rungs
                else eliminated.get(label, {}).get("status", "incomplete")
            )
            for label, values in rung_sets.items()
        },
        "verified_terminal_nonadvancing_families": eliminated,
        "terminal_nonadvancement_errors": elimination_errors,
        "feature_scales": {
            family_id: sorted(feature_scales[family_id]) for family_id in QML_IDS
        },
        "entanglement_states": {
            family_id: sorted(entanglement_states[family_id]) for family_id in QML_IDS
        },
        "qml_sensitivity_summary": [
            {
                "family_id": key[0],
                "rung_samples": key[1],
                "feature_scale": key[2],
                "entangle": key[3],
                "qubits": key[4],
                "trial_count": len(values),
                "mean_pooled_oof_nrmse": float(np.mean(values)),
            }
            for key, values in sorted(sensitivity.items())
        ],
        "q01_kernel_tuning_fold_rows": len(q01_folds),
        "q01_kernel_seed_fold_rows": len(q01_seed_folds),
        "q01_kernel_diagnostic_ranges": kernel_summary,
        "variational_trainability": variational_summary,
        "no_reference_regime_rows": len(no_reference_rows),
        "no_reference_concentration_summary": no_reference_summary,
        "matched_control_seed_rows": len(controls),
        "a01_fitted_trainable_parameter_counts": a01_parameter_counts,
        "compressed_c05_fitted_trainable_parameter_counts": compressed_c05_parameter_counts,
        "calibration_rows_read": 0,
        "final_test_rows_read": 0,
    }


def summarize_candidate_seeds(
    seed_rows: Sequence[Mapping[str, str]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for family_id in (*CLASSICAL_IDS, *QML_IDS):
        selected = [
            row
            for row in seed_rows
            if row["family_id"] == family_id
            and row["candidate_role"] == "primary_candidate"
        ]
        complete = [
            row
            for row in selected
            if row["status"] == "complete" and _bool(row["eligible_to_advance"])
        ]
        seed_indices = {int(row["resolved_seed_index"]) for row in selected}
        eligible = (
            len(selected) == SEED_COUNT
            and len(complete) == SEED_COUNT
            and seed_indices == set(range(1, SEED_COUNT + 1))
            and all(int(row["fold_count"]) == 5 for row in complete)
        )
        rows.append(
            {
                "family_id": family_id,
                "model_family": selected[0]["model_family"] if selected else "",
                "trial_id": selected[0]["trial_id"] if selected else "",
                "effective_qubits": (
                    selected[0]["effective_qubits"] if selected else ""
                ),
                "authorized_seed_rows": len(selected),
                "eligible_seed_rows": len(complete),
                "all_twenty_seeds_eligible": eligible,
                "mean_pooled_oof_nrmse": (
                    float(
                        np.mean([_float(row["pooled_oof_nrmse"]) for row in complete])
                    )
                    if complete
                    else None
                ),
                "mean_regret_m_s": (
                    float(np.mean([_float(row["mean_regret_m_s"]) for row in complete]))
                    if complete
                    else None
                ),
                "calibration_rows_read": 0,
                "final_test_rows_read": 0,
            }
        )
    return rows


def _eligible_best(
    summaries: Sequence[Mapping[str, Any]], family_ids: Sequence[str]
) -> Mapping[str, Any] | None:
    eligible = [
        row
        for row in summaries
        if row["family_id"] in family_ids
        and row["all_twenty_seeds_eligible"]
        and row["mean_pooled_oof_nrmse"] is not None
    ]
    return (
        min(
            eligible,
            key=lambda row: (
                float(row["mean_pooled_oof_nrmse"]),
                str(row["family_id"]),
            ),
        )
        if eligible
        else None
    )


def _candidate_by_seed(
    seed_rows: Sequence[Mapping[str, str]], family_id: str
) -> dict[int, Mapping[str, str]]:
    return {
        int(row["resolved_seed_index"]): row
        for row in seed_rows
        if row["family_id"] == family_id
        and row["candidate_role"] == "primary_candidate"
        and row["status"] == "complete"
        and _bool(row["eligible_to_advance"])
    }


def _regime_selector(
    family_id: str,
    qml_id: str,
    control: bool = False,
) -> Callable[[Mapping[str, str]], bool]:
    def selected(row: Mapping[str, str]) -> bool:
        if row["family_id"] != family_id:
            return False
        if not control:
            return row["candidate_role"] == "primary_candidate"
        return (
            row["candidate_role"] != "primary_candidate"
            and "control_ranked" in row["advancement_basis"]
            and qml_id in row["control_for"].split(";")
        )

    return selected


def _pooled_regimes(
    rows: Sequence[Mapping[str, str]],
    selector: Callable[[Mapping[str, str]], bool],
) -> tuple[
    dict[tuple[str, str, int], float],
    dict[tuple[str, str, str, int], float],
    dict[tuple[str, str, int], set[str]],
]:
    by_seed: dict[tuple[str, str, int], list[tuple[int, float]]] = defaultdict(list)
    by_fold: dict[tuple[str, str, str, int], float] = {}
    folds: dict[tuple[str, str, int], set[str]] = defaultdict(set)
    for row in rows:
        if not selector(row):
            continue
        seed = int(row["seed_index"])
        cell = (row["dimension"], row["value"], seed)
        fold_id = row["fold_id"]
        count = int(row["rows"])
        nrmse = _float(row["nrmse"])
        by_seed[cell].append((count, nrmse))
        by_fold[(row["dimension"], row["value"], fold_id, seed)] = nrmse
        folds[cell].add(fold_id)
    pooled = {
        cell: math.sqrt(
            sum(count * nrmse * nrmse for count, nrmse in values)
            / sum(count for count, _ in values)
        )
        for cell, values in by_seed.items()
    }
    return pooled, by_fold, folds


def evaluate_regime_trigger(
    regime_rows: Sequence[Mapping[str, str]],
    qml_id: str,
    classical_id: str,
    bootstrap_replicates: int = 10000,
    permutation_replicates: int = 10000,
) -> list[dict[str, Any]]:
    comparators = {
        "qml": _pooled_regimes(regime_rows, _regime_selector(qml_id, qml_id)),
        "classical": _pooled_regimes(
            regime_rows, _regime_selector(classical_id, qml_id)
        ),
        "a01": _pooled_regimes(
            regime_rows, _regime_selector("A01", qml_id, control=True)
        ),
        "compressed_c05": _pooled_regimes(
            regime_rows, _regime_selector("C05", qml_id, control=True)
        ),
    }
    cells = sorted(
        {(dimension, value) for dimension, value, _ in comparators["qml"][0]}
    )
    results: list[dict[str, Any]] = []
    pvalues: list[float] = []
    eligible_result_indices: list[int] = []
    for dimension, value in cells:
        keys = [(dimension, value, seed) for seed in range(1, SEED_COUNT + 1)]
        complete = all(
            key in comparators[name][0] and comparators[name][2].get(key) == FOLD_IDS
            for name in comparators
            for key in keys
        )
        row: dict[str, Any] = {
            "dimension": dimension,
            "value": value,
            "all_twenty_seeds": complete,
            "all_five_folds": complete,
            "qml_family_id": qml_id,
            "classical_family_id": classical_id,
            "qualified_residual_regime": False,
        }
        if not complete:
            results.append(row)
            continue
        arrays = {
            name: np.asarray([mapping[0][key] for key in keys], dtype=float)
            for name, mapping in comparators.items()
        }
        differences = {
            name: arrays["qml"] - arrays[name]
            for name in ("classical", "a01", "compressed_c05")
        }
        intervals = {
            name: paired_bootstrap_mean_interval(
                values,
                replicates=bootstrap_replicates,
                seed=_stable_seed(qml_id, classical_id, dimension, value, name),
            )
            for name, values in differences.items()
        }
        fold_consistent = True
        for fold_id in sorted(FOLD_IDS):
            qml_fold = np.asarray(
                [
                    comparators["qml"][1][(dimension, value, fold_id, seed)]
                    for seed in range(1, SEED_COUNT + 1)
                ]
            )
            classical_fold = np.asarray(
                [
                    comparators["classical"][1][(dimension, value, fold_id, seed)]
                    for seed in range(1, SEED_COUNT + 1)
                ]
            )
            fold_consistent &= float(np.mean(qml_fold - classical_fold)) < 0.0
        pvalue = paired_sign_permutation_pvalue(
            differences["classical"],
            replicates=permutation_replicates,
            seed=_stable_seed(qml_id, classical_id, dimension, value, "perm"),
        )
        row.update(
            {
                "qml_mean_nrmse": float(np.mean(arrays["qml"])),
                "classical_mean_nrmse": float(np.mean(arrays["classical"])),
                "a01_mean_nrmse": float(np.mean(arrays["a01"])),
                "compressed_c05_mean_nrmse": float(np.mean(arrays["compressed_c05"])),
                "qml_minus_classical_ci_upper": intervals["classical"].upper,
                "qml_minus_a01_ci_upper": intervals["a01"].upper,
                "qml_minus_compressed_c05_ci_upper": intervals["compressed_c05"].upper,
                "classical_sign_permutation_pvalue": pvalue,
                "classical_holm_adjusted_pvalue": None,
                "every_fold_mean_difference_below_zero": fold_consistent,
            }
        )
        eligible_result_indices.append(len(results))
        pvalues.append(pvalue)
        results.append(row)
    if pvalues:
        adjusted = holm_adjust(pvalues)
        for index, adjusted_value in zip(eligible_result_indices, adjusted):
            row = results[index]
            row["classical_holm_adjusted_pvalue"] = float(adjusted_value)
            row["qualified_residual_regime"] = bool(
                row["qml_minus_classical_ci_upper"] < 0.0
                and row["qml_minus_a01_ci_upper"] < 0.0
                and row["qml_minus_compressed_c05_ci_upper"] < 0.0
                and row["every_fold_mean_difference_below_zero"]
                and adjusted_value < 0.05
            )
    return results


def evaluate_gate5_trigger(
    seed_rows: Sequence[Mapping[str, str]],
    regime_rows: Sequence[Mapping[str, str]],
    bootstrap_replicates: int = 10000,
    permutation_replicates: int = 10000,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    summaries = summarize_candidate_seeds(seed_rows)
    classical = _eligible_best(summaries, CLASSICAL_IDS)
    qml = _eligible_best(summaries, QML_IDS)
    if classical is None or qml is None:
        result = {
            "trigger_passed": False,
            "condition_1_within_five_percent": False,
            "condition_2_reproducible_controlled_regime": False,
            "condition_3_twenty_seed_grouped_stability": False,
            "strongest_classical_family_id": (
                classical["family_id"] if classical else None
            ),
            "best_qml_family_id": qml["family_id"] if qml else None,
            "reason": "No eligible 20-seed classical or QML finalist",
            "recommendation": "reject_new_algorithm_development_and_report_negative_result",
            "calibration_rows_read": 0,
            "final_test_rows_read": 0,
        }
        return result, summaries, []

    classical_by_seed = _candidate_by_seed(seed_rows, str(classical["family_id"]))
    qml_by_seed = _candidate_by_seed(seed_rows, str(qml["family_id"]))
    paired = sorted(set(classical_by_seed) & set(qml_by_seed))
    relative = np.asarray(
        [
            (
                _float(qml_by_seed[seed]["pooled_oof_nrmse"])
                - _float(classical_by_seed[seed]["pooled_oof_nrmse"])
            )
            / _float(classical_by_seed[seed]["pooled_oof_nrmse"])
            for seed in paired
        ]
    )
    relative_interval = (
        paired_bootstrap_mean_interval(
            relative,
            replicates=bootstrap_replicates,
            seed=_stable_seed(
                str(qml["family_id"]), str(classical["family_id"]), "relative"
            ),
        )
        if len(paired) == SEED_COUNT
        else None
    )
    mean_relative_gap = (
        float(qml["mean_pooled_oof_nrmse"]) / float(classical["mean_pooled_oof_nrmse"])
        - 1.0
    )
    condition_1 = mean_relative_gap <= RELATIVE_GAP_LIMIT
    condition_3 = bool(
        len(paired) == SEED_COUNT
        and qml["all_twenty_seeds_eligible"]
        and relative_interval is not None
        and relative_interval.upper <= RELATIVE_GAP_LIMIT
    )
    regimes = evaluate_regime_trigger(
        regime_rows,
        str(qml["family_id"]),
        str(classical["family_id"]),
        bootstrap_replicates,
        permutation_replicates,
    )
    condition_2 = any(row["qualified_residual_regime"] for row in regimes)
    trigger = bool(condition_1 and condition_2 and condition_3)
    result = {
        "trigger_passed": trigger,
        "condition_1_within_five_percent": condition_1,
        "condition_2_reproducible_controlled_regime": condition_2,
        "condition_3_twenty_seed_grouped_stability": condition_3,
        "strongest_classical_family_id": classical["family_id"],
        "strongest_classical_mean_nrmse": classical["mean_pooled_oof_nrmse"],
        "best_qml_family_id": qml["family_id"],
        "best_qml_mean_nrmse": qml["mean_pooled_oof_nrmse"],
        "mean_relative_nrmse_gap": mean_relative_gap,
        "relative_gap_bootstrap_lower": (
            relative_interval.lower if relative_interval else None
        ),
        "relative_gap_bootstrap_upper": (
            relative_interval.upper if relative_interval else None
        ),
        "paired_seed_count": len(paired),
        "qualified_regime_count": sum(
            bool(row["qualified_residual_regime"]) for row in regimes
        ),
        "recommendation": (
            "authorize_one_registered_physics_constrained_quantum_residual_variant"
            if trigger
            else "reject_new_algorithm_development_and_report_negative_result"
        ),
        "calibration_rows_read": 0,
        "final_test_rows_read": 0,
    }
    return result, summaries, regimes


def _model_registry(
    root: Path,
    seed_rows: Sequence[Mapping[str, str]],
    source_commit: str,
    reporting_provenance: Mapping[str, Any],
) -> dict[str, Any]:
    tuning = {
        row["trial_id"]: row
        for row in read_csv(root / "data/processed/simulator/tuning_manifest.csv")
    }
    selected: dict[tuple[str, str, str, str], Mapping[str, str]] = {}
    for row in seed_rows:
        if (
            int(row["resolved_seed_index"]) != 1
            or row["status"] != "complete"
            or not _bool(row["eligible_to_advance"])
        ):
            continue
        key = (
            row["family_id"],
            row["view"],
            row["trial_id"],
            row["effective_qubits"],
        )
        selected[key] = row
    entries = []
    for row in selected.values():
        frozen = tuning[row["trial_id"]]
        entries.append(
            {
                "family_id": row["family_id"],
                "model_family": row["model_family"],
                "trial_id": row["trial_id"],
                "view": row["view"],
                "rung_samples": row["rung_samples"] or None,
                "effective_qubits": row["effective_qubits"] or None,
                "candidate_role": row["candidate_role"],
                "control_for": row["control_for"],
                "advancement_basis": row["advancement_basis"],
                "parameters": json.loads(frozen["parameters_json"]),
                "development_seed_indices": list(range(1, SEED_COUNT + 1)),
            }
        )
    return {
        "schema_version": "0.1.0",
        "status": "gate5_development_configurations_frozen_pending_human_decision",
        "selection_scope": "development_only",
        "source_commit": source_commit,
        "reporting_provenance": dict(reporting_provenance),
        "models": sorted(
            entries,
            key=lambda row: (
                row["candidate_role"] != "primary_candidate",
                row["family_id"],
                row["view"],
                row["trial_id"],
            ),
        ),
        "calibration_rows_read": 0,
        "final_test_rows_read": 0,
    }


def write_gate5_report(
    root: Path,
    experiment_dir: Path,
    reporting_dir: Path,
    *,
    unpublished: bool = False,
) -> dict[str, Any]:
    if unpublished:
        official_paths = {
            (root / "experiments").resolve(),
            (root / "data/processed/reporting").resolve(),
        }
        requested_paths = {experiment_dir.resolve(), reporting_dir.resolve()}
        if official_paths & requested_paths:
            raise RuntimeError(
                "Unpublished Gate 5 evaluation cannot write an official output path"
            )
        governance = yaml.safe_load(
            (root / "configs/phase1_benchmark.yaml").read_text(encoding="utf-8")
        ).get("gate5_runner_freeze", {})
        reporting_source_commit = "unpublished_working_tree"
    else:
        governance = assert_gate5_report_regeneration_authorized(root)
        reporting_source_commit = _clean_source_commit(root)
    validate_development_output_path(root, experiment_dir)
    validate_development_output_path(root, reporting_dir)
    package_path = experiment_dir / "gate5_reporting_package.json"
    package_path.unlink(missing_ok=True)
    seed_rows = _seed_rows(experiment_dir / "phase1_seed_results.csv")
    regime_rows = _seed_rows(experiment_dir / "phase1_seed_regime_metrics.csv")
    audit = json.loads(
        (experiment_dir / "gate5_campaign_audit.json").read_text(encoding="utf-8")
    )
    reporting_provenance = {
        "mode": "unpublished_evaluation" if unpublished else "official",
        "campaign_source_commit": audit.get("source_commit"),
        "reporting_source_commit": reporting_source_commit,
        "accepted_d007_candidate_commit": governance.get(
            "d007_accepted_candidate_commit"
        ),
        "reporting_module_sha256": sha256_file(Path(__file__).resolve()),
        "reporting_script_sha256": sha256_file(
            root / "scripts/report_gate5_results.py"
        ),
        "figure_generator_sha256": sha256_file(
            root / "scripts/make_gate5_result_figures.py"
        ),
    }
    eliminated_families, elimination_errors = _scientific_elimination_evidence(
        root, experiment_dir, audit
    )
    evidence_errors = validate_campaign_evidence(
        root, experiment_dir, audit, seed_rows, regime_rows
    )
    try:
        trigger, summaries, regimes = evaluate_gate5_trigger(seed_rows, regime_rows)
    except (KeyError, TypeError, ValueError, ZeroDivisionError) as error:
        evidence_errors.append(f"trigger evidence schema error: {error}")
        evidence_errors = sorted(set(evidence_errors))
        trigger, summaries, regimes = evaluate_gate5_trigger([], [])
    if evidence_errors:
        claim_boundary = {
            "status": "incomplete",
            "handling": "mandatory_report_only_pending_human_interpretation",
            "checks": {},
            "reason": "source-bound campaign evidence is invalid",
            "calibration_rows_read": audit.get("calibration_rows_read"),
            "final_test_rows_read": audit.get("final_test_rows_read"),
        }
    else:
        try:
            claim_boundary = evaluate_claim_boundary_diagnostics(root, experiment_dir)
        except (KeyError, TypeError, ValueError, ZeroDivisionError) as error:
            claim_boundary = {
                "status": "incomplete",
                "handling": "mandatory_report_only_pending_human_interpretation",
                "checks": {},
                "reason": f"claim-boundary evidence schema error: {error}",
                "calibration_rows_read": audit.get("calibration_rows_read"),
                "final_test_rows_read": audit.get("final_test_rows_read"),
            }
    claim_boundary_complete = claim_boundary["status"] == "complete"
    statistical_trigger_passed = bool(trigger["trigger_passed"])
    decision_available = not evidence_errors and claim_boundary_complete
    trigger["trigger_passed"] = bool(decision_available and statistical_trigger_passed)
    if not decision_available:
        trigger_status = "UNAVAILABLE"
        recommendation = "repair_or_complete_evidence_before_gate5_decision"
        decision_status = "repair_required_before_human_gate5_decision"
    elif trigger["trigger_passed"]:
        trigger_status = "PASS"
        recommendation = "technical_trigger_passed_human_claim_boundary_review_required"
        decision_status = "pending_human_accept_reject_or_revise"
    else:
        trigger_status = "FAIL"
        recommendation = "reject_new_algorithm_development_and_report_negative_result"
        decision_status = "pending_human_accept_reject_or_revise"
    trigger["recommendation"] = recommendation
    trigger.update(
        {
            "source_commit": audit.get("source_commit"),
            "technical_trigger_status": trigger_status,
            "decision_available": decision_available,
            "decision_status": decision_status,
            "evidence_contract_valid": not evidence_errors,
            "evidence_contract_errors": evidence_errors,
            "statistical_trigger_passed_before_audit_gates": statistical_trigger_passed,
            "claim_boundary_diagnostics_complete": claim_boundary_complete,
            "claim_boundary_handling": claim_boundary["handling"],
            "selection_evidence_status": (
                "complete_with_scientific_eliminations"
                if eliminated_families and not elimination_errors
                else (
                    "complete"
                    if audit.get("selection_manifest", {}).get("status") == "complete"
                    else "incomplete"
                )
            ),
            "scientifically_eliminated_families": eliminated_families,
            "calibration_rows_read": audit.get("calibration_rows_read"),
            "final_test_rows_read": audit.get("final_test_rows_read"),
            "reporting_provenance": reporting_provenance,
        }
    )
    claim_boundary["reporting_provenance"] = reporting_provenance
    _write_json(experiment_dir / "gate5_trigger_summary.json", trigger)
    _write_json(
        experiment_dir / "gate5_claim_boundary_diagnostics.json", claim_boundary
    )
    csv_provenance = {
        "campaign_source_commit": reporting_provenance["campaign_source_commit"],
        "reporting_source_commit": reporting_provenance["reporting_source_commit"],
        "accepted_d007_candidate_commit": reporting_provenance[
            "accepted_d007_candidate_commit"
        ],
        "reporting_module_sha256": reporting_provenance[
            "reporting_module_sha256"
        ],
        "reporting_script_sha256": reporting_provenance[
            "reporting_script_sha256"
        ],
        "figure_generator_sha256": reporting_provenance[
            "figure_generator_sha256"
        ],
    }
    summary_rows = [{**row, **csv_provenance} for row in summaries]
    regime_output_rows = [{**row, **csv_provenance} for row in regimes]
    _write_csv(reporting_dir / "gate5_model_summary.csv", summary_rows)
    _write_csv(reporting_dir / "gate5_regime_trigger.csv", regime_output_rows)

    registry = _model_registry(
        root,
        seed_rows if not evidence_errors else [],
        str(audit.get("source_commit")),
        reporting_provenance,
    )
    registry_path = experiment_dir / "phase1_model_registry.yaml"
    registry_path.write_text(
        yaml.safe_dump(registry, sort_keys=False), encoding="utf-8"
    )
    verdict = trigger["technical_trigger_status"]
    report = f"""# Gate 5 Preregistered Algorithm Trigger Report

Status: **Technical trigger {verdict}**
Scope: development-only grouped CV; 20 frozen seed indices
Campaign source commit: `{audit.get("source_commit")}`
Reporting source commit: `{reporting_provenance["reporting_source_commit"]}`
Accepted D007 candidate commit: `{reporting_provenance["accepted_d007_candidate_commit"]}`
Reporting module SHA-256: `{reporting_provenance["reporting_module_sha256"]}`
Reporting script SHA-256: `{reporting_provenance["reporting_script_sha256"]}`
Figure generator SHA-256: `{reporting_provenance["figure_generator_sha256"]}`

## Decision result

| Condition | Result |
|---|---|
| Best QML within 5% of strongest classical mean NRMSE | {trigger["condition_1_within_five_percent"]} |
| Reproducible regime survives strongest classical and tuned A01/C05 controls | {trigger["condition_2_reproducible_controlled_regime"]} |
| Five-fold, 20-seed stability including the upper confidence bound | {trigger["condition_3_twenty_seed_grouped_stability"]} |
| Source-bound complete campaign evidence | {trigger["evidence_contract_valid"]} |
| Mandatory D004 claim-boundary diagnostics complete | {trigger["claim_boundary_diagnostics_complete"]} |

Strongest classical: `{trigger.get("strongest_classical_family_id")}`.
Best QML: `{trigger.get("best_qml_family_id")}`.
Mean relative NRMSE gap: `{trigger.get("mean_relative_nrmse_gap")}`.
Qualified preregistered regimes: `{trigger.get("qualified_regime_count", 0)}`.

Recommendation: `{trigger["recommendation"]}`.

Evidence-contract findings: `{trigger["evidence_contract_errors"]}`.

Selection evidence: `{trigger["selection_evidence_status"]}`. Scientifically
eliminated families: `{trigger["scientifically_eliminated_families"]}`. A
terminally nonadvancing family remains excluded from seed comparisons and the
trigger; no missing seed evidence is imputed.

D004 claim-boundary handling: `{trigger["claim_boundary_handling"]}`. The
feature-scale, entanglement-removal, random-feature, parameter-count,
sample/rung, and no-reference summaries are frozen in
`gate5_claim_boundary_diagnostics.json` and require human interpretation.

## Governance boundary

This report makes no final-test, mission-performance, hardware-speedup, quantum
advantage, or flight-suitability claim. Calibration rows read:
**{trigger["calibration_rows_read"]}**. Final-test rows read:
**{trigger["final_test_rows_read"]}**. An `UNAVAILABLE` report must be repaired
before a Gate 5 decision. Once evidence is available, the human research lead
must separately accept, reject, or revise the trigger result before Gate 6 or
any new algorithm work.
"""
    (experiment_dir / "algorithm_trigger_report.md").write_text(
        report, encoding="utf-8"
    )
    artifact_paths = _reporting_package_paths(experiment_dir, reporting_dir)
    _write_json(
        package_path,
        {
            "schema_version": "0.1.0",
            "status": "complete",
            "reporting_provenance": reporting_provenance,
            "artifact_sha256": {
                label: sha256_file(path) for label, path in artifact_paths.items()
            },
            "calibration_rows_read": audit.get("calibration_rows_read"),
            "final_test_rows_read": audit.get("final_test_rows_read"),
        },
    )
    return trigger
