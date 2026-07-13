"""Run the D011 largest-fold synthetic compute-admission benchmark."""

from __future__ import annotations

import csv
import importlib.metadata
import json
import os
import platform
import shutil
import time
from pathlib import Path
from typing import Any

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")

import numpy as np  # noqa: E402

from openqfuel.post_gate5 import (  # noqa: E402
    process_memory_observation,
    total_physical_memory_bytes,
    validate_future_research_discussion_row,
)
from openqfuel.post_gate5_campaign import (  # noqa: E402
    evaluate_fold_shape_admission,
    git_blob_sha256,
    project_fold_shape_resources,
    verify_d011_preflight_correction,
    verify_d011_authority,
)
from openqfuel.post_gate5_preflight_runner import (  # noqa: E402
    control_predictions,
    fit_two_heads,
    nystrom_features,
    registry_models,
    timed,
)
from openqfuel.qml import projected_quantum_features  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]


def _record_resource_stop(
    config: dict[str, Any], correction: dict[str, Any], payload: dict[str, Any]
) -> None:
    path = ROOT / str(config["failure_policy"]["future_discussion_register"])
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    decision_id = str(correction["decision_id"])
    step_id = f"{decision_id.replace('-', '_')}_fold_shape_preflight"
    if any(row["step_id"] == step_id for row in rows):
        raise PermissionError(f"{decision_id} fold-shape STOP was already recorded")
    fields = list(rows[0])
    identifiers = [
        int(row["record_id"].split("FR")[-1])
        for row in rows
        if row["record_id"].startswith("P001-FR")
        and row["record_id"].split("FR")[-1].isdigit()
    ]
    failed = [
        name
        for name, check in payload["admission"]["checks"].items()
        if not bool(check["passed"])
    ]
    row = {
        "record_id": f"P001-FR{max(identifiers, default=0) + 1:03d}",
        "recorded_date": "2026-07-14",
        "track_id": "shared",
        "step_id": step_id,
        "terminal_status": "resource_stop",
        "evidence_paths": str(correction["source_binding"]["output"]),
        "observed_finding": (
            "The source-bound D011 largest-fold synthetic workload exceeded "
            "one or more unchanged admission boundaries: " + ", ".join(failed) + "."
        ),
        "bounded_interpretation": (
            "This is a laptop resource-admission STOP. It is not Q01b/FQK "
            "performance evidence, and no development, calibration, or final-test "
            "payload was opened."
        ),
        "future_research_improvement": (
            "A later prospective protocol should evaluate algorithm-preserving "
            "streaming/checkpoint storage or separately governed external CPU "
            "capacity using the same largest-fold workload before requesting a new "
            "execution decision; it must not reduce or retry P001 post outcome."
        ),
        "new_protocol_required": "true",
        "active_pipeline_change_authorized": "false",
        "post_outcome_retry_authorized": "false",
        "reporting_commit": "pending_result_commit",
    }
    validate_future_research_discussion_row(
        row, [field for field in fields if field != "reporting_commit"]
    )
    rows.append(row)
    temporary = path.with_suffix(".csv.tmp")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


def _benchmark_contract(config: dict[str, Any]) -> dict[str, Any]:
    correction = config["fold_shape_correction"]
    return {
        "seed": 20260713,
        "training_rows": int(correction["benchmark_training_rows"]),
        "validation_rows": int(correction["benchmark_validation_rows"]),
        "primary_control_feature_count": int(
            correction["benchmark_primary_control_feature_count"]
        ),
        "compressed_feature_count": int(
            correction["benchmark_compressed_feature_count"]
        ),
        "qubits": int(correction["benchmark_qubits"]),
        "data_reupload_layers": int(correction["benchmark_layers"]),
        "feature_scale": 2.0,
        "entangle": True,
        "gamma_multiplier": 1.0,
        "regularization_alpha": 0.01,
        "nystrom_landmarks": 256,
        "projection_id": "D011-Q8-L2-LARGEST-FOLD",
        "fold_id": "D011-SYNTHETIC-CV02",
        "seed_index": 1,
        "statevector_concurrency": 1,
    }


def main() -> None:
    config, source_commit, branch = verify_d011_authority(
        ROOT,
        action="fold_shape_preflight",
        require_fold_shape_pass=False,
    )
    correction = verify_d011_preflight_correction(ROOT, source_commit)
    benchmark = _benchmark_contract(config)
    runner_config = {"benchmark": benchmark}
    rng = np.random.default_rng(int(benchmark["seed"]))
    training_rows = int(benchmark["training_rows"])
    validation_rows = int(benchmark["validation_rows"])
    primary_width = int(benchmark["primary_control_feature_count"])
    compressed_width = int(benchmark["compressed_feature_count"])

    raw_train = rng.normal(size=(training_rows, primary_width))
    raw_validation = rng.normal(size=(validation_rows, primary_width))
    compressed_train = np.clip(
        rng.normal(size=(training_rows, compressed_width)), -3.0, 3.0
    ) * (np.pi / 3.0)
    compressed_validation = np.clip(
        rng.normal(size=(validation_rows, compressed_width)), -3.0, 3.0
    ) * (np.pi / 3.0)
    cost_target = (
        raw_train[:, -1]
        + 0.2 * np.sin(raw_train[:, 0])
        - 0.1 * raw_train[:, 1]
        + 0.02 * rng.normal(size=training_rows)
    )
    feasibility_score = raw_train[:, 0] - 0.4 * raw_train[:, 1] + 0.2 * raw_train[:, 2]
    feasibility_target = (feasibility_score >= np.median(feasibility_score)).astype(int)
    if set(np.unique(feasibility_target)) != {0, 1}:
        raise ValueError("D011 synthetic feasibility labels require both classes")
    row_ids = [f"d011-synthetic-{index:04d}" for index in range(training_rows)]

    records: list[dict[str, Any]] = []
    wall_started = time.perf_counter()
    cpu_started = time.process_time()
    projected_train = timed(
        records,
        "Q01b_FQK_shared_training_projection",
        lambda: projected_quantum_features(
            compressed_train,
            int(benchmark["qubits"]),
            int(benchmark["data_reupload_layers"]),
            feature_scale=float(benchmark["feature_scale"]),
            entangle=bool(benchmark["entangle"]),
        ),
    )
    projected_validation = timed(
        records,
        "Q01b_FQK_largest_fold_validation_projection",
        lambda: projected_quantum_features(
            compressed_validation,
            int(benchmark["qubits"]),
            int(benchmark["data_reupload_layers"]),
            feature_scale=float(benchmark["feature_scale"]),
            entangle=bool(benchmark["entangle"]),
        ),
    )
    q_train, q_validation, q_diagnostics = timed(
        records,
        "Q01b_FQK_projected_kernel_geometry",
        lambda: nystrom_features(
            projected_train,
            projected_validation,
            row_ids,
            runner_config,
            projected_quantum=True,
        ),
    )
    timed(
        records,
        "Q01b_FQK_two_head_fit_and_inference",
        lambda: fit_two_heads(
            q_train,
            q_validation,
            cost_target,
            feasibility_target,
            float(benchmark["regularization_alpha"]),
        ),
    )

    a02_train, a02_validation, a02_diagnostics = timed(
        records,
        "A02_classical_RBF_geometry",
        lambda: nystrom_features(
            compressed_train,
            compressed_validation,
            row_ids,
            runner_config,
            projected_quantum=False,
        ),
    )
    timed(
        records,
        "A02_classical_RBF_two_head_fit_and_inference",
        lambda: fit_two_heads(
            a02_train,
            a02_validation,
            cost_target,
            feasibility_target,
            float(benchmark["regularization_alpha"]),
        ),
    )

    models = registry_models()
    seed = int(benchmark["seed"])
    regression_controls = {
        "C06-T17_cost": (models["C06-T17"], raw_train, raw_validation),
        "A01-T04_cost": (
            models["A01-T04"],
            compressed_train,
            compressed_validation,
        ),
        "C05-T17_compressed_cost": (
            models["C05-T17"],
            compressed_train,
            compressed_validation,
        ),
    }
    for name, (trial, train, validation) in regression_controls.items():
        timed(
            records,
            name,
            lambda trial=trial, train=train, validation=validation: (
                control_predictions(
                    trial,
                    train,
                    validation,
                    cost_target,
                    classifier=False,
                    seed=seed,
                )
            ),
        )

    classifier_specs = [
        ("C01-T18", raw_train, raw_validation),
        ("C02-T02", raw_train, raw_validation),
        ("C03-T13", raw_train, raw_validation),
        ("C04-T28", raw_train, raw_validation),
        ("C05-T12", raw_train, raw_validation),
        ("C06-T17", raw_train, raw_validation),
        ("A01-T04", compressed_train, compressed_validation),
        ("C05-T17", compressed_train, compressed_validation),
    ]
    for trial_id, train, validation in classifier_specs:
        trial = models[trial_id]
        timed(
            records,
            f"{trial_id}_feasibility",
            lambda trial=trial, train=train, validation=validation: (
                control_predictions(
                    trial,
                    train,
                    validation,
                    feasibility_target,
                    classifier=True,
                    seed=seed,
                )
            ),
        )

    benchmark_wall_seconds = time.perf_counter() - wall_started
    benchmark_cpu_seconds = time.process_time() - cpu_started
    peak_rss_gib = process_memory_observation().peak_bytes / float(1024**3)
    free_disk_gib = shutil.disk_usage(ROOT).free / float(1024**3)
    projected = project_fold_shape_resources(
        config,
        benchmark_cpu_seconds=benchmark_cpu_seconds,
        benchmark_wall_seconds=benchmark_wall_seconds,
        peak_rss_gib=peak_rss_gib,
        free_disk_gib=free_disk_gib,
    )
    admission = evaluate_fold_shape_admission(config, projected)

    source_paths = {
        **dict(config["source_binding"]),
        **dict(correction["source_binding"]["additional_sources"]),
    }
    source_hashes = {
        key: git_blob_sha256(ROOT, source_commit, str(path))
        for key, path in source_paths.items()
    }
    payload = {
        "schema_version": "0.1.0",
        "decision_id": str(correction["decision_id"]),
        "corrects_decision_id": str(correction["authority"]["corrected_decision"]),
        "unchanged_preflight_contract": "D011 largest-fold synthetic compute admission",
        "attempt": 1,
        "protocol_id": "P001",
        "status": admission["status"],
        "evidence_scope": "largest-fold synthetic compute admission only",
        "source_commit": source_commit,
        "branch": branch,
        "source_hash_scope": "committed Git blob bytes",
        "source_paths": source_paths,
        "source_hashes": source_hashes,
        "benchmark": {
            **benchmark,
            "wall_seconds": benchmark_wall_seconds,
            "cpu_seconds": benchmark_cpu_seconds,
            "steps": records,
            "projected_kernel_diagnostics": q_diagnostics,
            "classical_rbf_diagnostics": a02_diagnostics,
            "gpu_hours": 0.0,
        },
        "accounting_correction": {
            "d010_validation_rows": 256,
            "d011_validation_rows": validation_rows,
            "validation_row_ratio": validation_rows / 256.0,
            "complete_task_validation_rows": 39000,
            "worst_fold_bundle_units": int(
                config["fold_shape_correction"]["total_worst_fold_bundle_units"]
            ),
            "no_cache_or_smaller_shape_credit": True,
        },
        "campaign_projection": projected,
        "admission": admission,
        "machine": {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "numpy": importlib.metadata.version("numpy"),
            "scikit_learn": importlib.metadata.version("scikit-learn"),
            "logical_processors": os.cpu_count(),
            "physical_memory_gib": total_physical_memory_bytes() / float(1024**3),
            "declared_reference_cpu": "Intel Core i9-13900HX",
            "declared_reference_gpu": ("NVIDIA GeForce RTX 4060 Laptop GPU; unused"),
        },
        "development_rows_read": 0,
        "calibration_rows_read": 0,
        "final_test_rows_read": 0,
        "hardware_jobs_submitted": 0,
        "gate6_runs": 0,
        "claim_boundary": (
            "Synthetic fold-shape compute evidence only; no model-performance, "
            "development-outcome, calibration, final-test, hardware, Gate 5, "
            "or Gate 6 claim."
        ),
        "next_step": (
            "Request human decision on whether to resume the D011 development-only campaign"
            if admission["status"] == "PASS"
            else "Record governed resource STOP; do not open development data"
        ),
    }
    output = ROOT / str(correction["source_binding"]["output"])
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({"status": admission["status"], **projected}, indent=2))
    if admission["status"] != "PASS":
        _record_resource_stop(config, correction, payload)
        raise SystemExit(2)


if __name__ == "__main__":
    main()
