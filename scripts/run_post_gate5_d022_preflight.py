"""Run D022-C clean-source synthetic CSAFE-RF compute preflight."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import platform
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")

import numpy as np  # noqa: E402
import yaml  # noqa: E402

from openqfuel.post_gate5 import (  # noqa: E402
    process_memory_observation,
    total_physical_memory_bytes,
)
from openqfuel.post_gate5_classical import (  # noqa: E402
    assert_d021_scope,
    recall_first_safety_score,
    select_recall_first_candidate,
    select_safety_threshold,
)


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/post_gate5_d022_recall_first_preflight.yaml"


def _git(*args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _clean_source() -> tuple[str, str]:
    dirty = _git("status", "--porcelain")
    if dirty:
        raise RuntimeError("D022-C requires a clean Git worktree")
    branch = _git("branch", "--show-current")
    if branch != "main":
        raise RuntimeError("D022-C is accepted only on main")
    return _git("rev-parse", "HEAD"), branch


def _git_blob_sha256(commit: str, relative_path: str) -> str:
    completed = subprocess.run(
        ["git", "show", f"{commit}:{relative_path}"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    return hashlib.sha256(completed.stdout).hexdigest()


def _load_committed_yaml(commit: str, relative_path: str) -> dict[str, Any]:
    completed = subprocess.run(
        ["git", "show", f"{commit}:{relative_path}"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    payload = yaml.safe_load(completed.stdout)
    if not isinstance(payload, dict):
        raise TypeError(f"Committed YAML must contain a mapping: {relative_path}")
    return payload


def _synthetic_candidates(benchmark: dict[str, Any]) -> list[dict[str, Any]]:
    rng = np.random.default_rng(int(benchmark["seed"]))
    train_n = int(benchmark["training_rows"])
    valid_n = int(benchmark["validation_rows"])
    latent_train = rng.normal(size=train_n)
    latent_valid = rng.normal(size=valid_n)
    train_labels = (latent_train >= np.quantile(latent_train, 0.60)).astype(int)
    valid_labels = (latent_valid >= np.quantile(latent_train, 0.60)).astype(int)
    noise_train = rng.normal(scale=0.05, size=train_n)
    noise_valid = rng.normal(scale=0.05, size=valid_n)
    recall_train_prob = np.clip(0.5 + 0.28 * latent_train + noise_train, 0.0, 1.0)
    recall_valid_prob = np.clip(0.5 + 0.28 * latent_valid + noise_valid, 0.0, 1.0)
    brier_train_prob = np.where(train_labels == 1, 0.82, 0.08)
    brier_valid_prob = np.where(valid_labels == 1, 0.78, 0.06)
    # Force a low-recall operating point for the Brier-style fixture.
    brier_train_prob[: max(1, train_n // 12)] = 0.98
    brier_valid_prob[: max(1, valid_n // 12)] = 0.98
    return [
        {
            "model_id": "synthetic_recall_first_logistic",
            "model_complexity": 1,
            "train_labels": train_labels,
            "valid_labels": valid_labels,
            "train_prob": recall_train_prob,
            "valid_prob": recall_valid_prob,
        },
        {
            "model_id": "synthetic_brier_first_tree",
            "model_complexity": 2,
            "train_labels": train_labels,
            "valid_labels": valid_labels,
            "train_prob": brier_train_prob,
            "valid_prob": brier_valid_prob,
        },
    ]


def _admission(config: dict[str, Any], projection: dict[str, float]) -> dict[str, Any]:
    ceilings = config["ceilings"]
    checks = {
        "cpu_core_hours": {
            "observed": projection["projected_cpu_core_hours"],
            "limit": float(ceilings["branch_cpu_core_hours"]),
            "comparison": "less_than_or_equal",
        },
        "wall_clock_days": {
            "observed": projection["projected_wall_clock_days"],
            "limit": float(ceilings["branch_wall_clock_days"]),
            "comparison": "less_than_or_equal",
        },
        "new_artifacts_gib": {
            "observed": projection["projected_new_artifacts_gib"],
            "limit": float(ceilings["branch_new_artifacts_gib"]),
            "comparison": "less_than_or_equal",
        },
        "peak_working_set_gib": {
            "observed": projection["observed_peak_rss_gib"],
            "limit": float(ceilings["max_total_project_working_set_gib"]),
            "comparison": "less_than_or_equal",
        },
        "free_disk_after_artifacts_gib": {
            "observed": projection["projected_free_disk_after_artifacts_gib"],
            "limit": float(ceilings["minimum_free_disk_gib"]),
            "comparison": "greater_than_or_equal",
        },
        "gpu_hours": {
            "observed": 0.0,
            "limit": float(ceilings["max_gpu_hours"]),
            "comparison": "less_than_or_equal",
        },
    }
    for check in checks.values():
        if check["comparison"] == "less_than_or_equal":
            check["passed"] = check["observed"] <= check["limit"]
            check["utilization_fraction"] = (
                check["observed"] / check["limit"] if check["limit"] else 0.0
            )
        else:
            check["passed"] = check["observed"] >= check["limit"]
            check["utilization_fraction"] = check["limit"] / check["observed"]
    return {
        "status": "PASS" if all(check["passed"] for check in checks.values()) else "STOP",
        "checks": checks,
    }


def main() -> None:
    source_commit, branch = _clean_source()
    config_path = CONFIG.relative_to(ROOT).as_posix()
    config = _load_committed_yaml(source_commit, config_path)
    if config["decision_id"] != "D022-C":
        raise ValueError("D022-C preflight requires the D022-C config")
    if config["authority"]["preflight_execution_authorized"] is not True:
        raise PermissionError("D022-C preflight is not authorized")
    d021 = _load_committed_yaml(source_commit, str(config["source_binding"]["d021_config"]))
    assert_d021_scope(d021, action="synthetic_validation", data_scope="synthetic")

    benchmark = config["benchmark"]
    records: list[dict[str, Any]] = []
    wall_started = time.perf_counter()
    cpu_started = time.process_time()
    candidates = _synthetic_candidates(benchmark)
    scores = []
    for candidate in candidates:
        step_started = time.perf_counter()
        cpu_step_started = time.process_time()
        threshold = select_safety_threshold(
            candidate["train_labels"],
            candidate["train_prob"],
            minimum_recall=float(benchmark["safety_minimum_recall"]),
            maximum_intervention_rate=float(benchmark["safety_maximum_intervention_rate"]),
        )
        score = recall_first_safety_score(
            model_id=str(candidate["model_id"]),
            model_complexity=int(candidate["model_complexity"]),
            labels=candidate["valid_labels"],
            probabilities=candidate["valid_prob"],
            threshold=threshold,
            calibration_bins=int(benchmark["calibration_bins"]),
        )
        scores.append(score)
        records.append(
            {
                "step": f"CSAFE_RF_{candidate['model_id']}",
                "wall_seconds": time.perf_counter() - step_started,
                "cpu_seconds": time.process_time() - cpu_step_started,
                "peak_working_set_gib": process_memory_observation().peak_bytes / float(1024**3),
            }
        )
    selected = select_recall_first_candidate(scores)
    wall_seconds = time.perf_counter() - wall_started
    cpu_seconds = time.process_time() - cpu_started
    peak_rss_gib = process_memory_observation().peak_bytes / float(1024**3)
    free_disk_gib = shutil.disk_usage(ROOT).free / float(1024**3)
    workload = config["candidate_workload"]
    units = int(workload["projected_fold_count"]) * int(workload["projected_seed_count"])
    margin = float(workload["projection_margin"])
    artifact_gib = units * margin * int(workload["artifact_bytes_per_fold_seed"]) / float(1024**3)
    projection = {
        "largest_fold_seed_units": float(units),
        "projection_margin": margin,
        "projected_cpu_core_hours": cpu_seconds * units * margin / 3600.0,
        "projected_wall_clock_days": wall_seconds * units * margin / 86400.0,
        "projected_new_artifacts_gib": artifact_gib,
        "observed_peak_rss_gib": peak_rss_gib,
        "observed_free_disk_gib": free_disk_gib,
        "projected_free_disk_after_artifacts_gib": free_disk_gib - artifact_gib,
    }
    admission = _admission(config, projection)
    source_paths = config["source_binding"]
    source_hashes = {
        key: _git_blob_sha256(source_commit, str(path))
        for key, path in source_paths.items()
        if key != "output"
    }
    output = ROOT / str(source_paths["output"])
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "0.1.0",
        "decision_id": "D022-C",
        "protocol_id": "P001",
        "status": admission["status"],
        "evidence_scope": "clean-source synthetic CSAFE-RF compute admission only",
        "source_commit": source_commit,
        "branch": branch,
        "source_paths": source_paths,
        "source_hashes": source_hashes,
        "benchmark": {
            **benchmark,
            "wall_seconds": wall_seconds,
            "cpu_seconds": cpu_seconds,
            "steps": records,
            "gpu_hours": 0.0,
        },
        "synthetic_metrics": {
            "selected_model_id": selected.model_id,
            "selected_recall": selected.metrics.recall,
            "selected_false_negative_rate": selected.metrics.false_negative_rate,
            "selected_brier": selected.metrics.brier,
            "candidate_scores": [score.as_row() for score in scores],
        },
        "campaign_projection": projection,
        "admission": admission,
        "machine": {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "numpy": importlib.metadata.version("numpy"),
            "logical_processors": os.cpu_count(),
            "physical_memory_gib": total_physical_memory_bytes() / float(1024**3),
            "declared_reference_cpu": config["ceilings"]["reference_cpu"],
            "declared_reference_gpu": config["ceilings"]["reference_gpu"],
        },
        "integrity": {
            "clean_source_verified_before_execution": True,
            "synthetic_rows_used": int(benchmark["training_rows"]) + int(benchmark["validation_rows"]),
            "development_rows_read": 0,
            "calibration_rows_read": 0,
            "final_test_rows_read": 0,
            "hardware_jobs_submitted": 0,
            "gpu_hours": 0.0,
            "gate6_runs": 0,
        },
        "claim_boundary": config["reporting"]["claim_boundary"],
        "next_step": (
            "Prepare D023 development-data decision"
            if admission["status"] == "PASS"
            else "Record governed resource STOP; do not open development data"
        ),
    }
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": payload["status"], **projection}, indent=2))
    if payload["status"] != "PASS":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
