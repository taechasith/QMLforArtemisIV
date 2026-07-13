"""Run D016-C1 synthetic compute admission for the missing A02 exact RBF control."""

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
from typing import Any, Callable

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")

import numpy as np  # noqa: E402
import yaml  # noqa: E402
from sklearn.kernel_ridge import KernelRidge  # noqa: E402
from sklearn.preprocessing import StandardScaler  # noqa: E402

from openqfuel.post_gate5 import (  # noqa: E402
    process_memory_observation,
    total_physical_memory_bytes,
)
from openqfuel.post_gate5_classical import (  # noqa: E402
    residual_cost_metrics,
    residual_target,
    safety_metrics,
)


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/post_gate5_d016_c1_a02_compute_preflight.yaml"


def _git(*args: str, binary: bool = False) -> str | bytes:
    completed = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=not binary,
    )
    return completed.stdout


def _clean_source() -> tuple[str, str]:
    dirty = str(_git("status", "--porcelain")).strip()
    if dirty:
        raise RuntimeError("D016-C1 requires a clean Git worktree")
    branch = str(_git("branch", "--show-current")).strip()
    if branch != "main":
        raise RuntimeError("D016-C1 is accepted only on main")
    return str(_git("rev-parse", "HEAD")).strip(), branch


def _git_blob_sha256(commit: str, relative_path: str) -> str:
    blob = _git("show", f"{commit}:{relative_path}", binary=True)
    if not isinstance(blob, bytes):
        raise TypeError("Git blob reader returned text unexpectedly")
    return hashlib.sha256(blob).hexdigest()


def _load_committed_yaml(commit: str, relative_path: str) -> dict[str, Any]:
    blob = _git("show", f"{commit}:{relative_path}", binary=True)
    if not isinstance(blob, bytes):
        raise TypeError("Git blob reader returned text unexpectedly")
    payload = yaml.safe_load(blob.decode("utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"Committed YAML must contain a mapping: {relative_path}")
    return payload


def _load_committed_json(commit: str, relative_path: str) -> dict[str, Any]:
    blob = _git("show", f"{commit}:{relative_path}", binary=True)
    if not isinstance(blob, bytes):
        raise TypeError("Git blob reader returned text unexpectedly")
    payload = json.loads(blob.decode("utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"Committed JSON must contain an object: {relative_path}")
    return payload


def _timed(
    records: list[dict[str, Any]], name: str, operation: Callable[[], Any]
) -> Any:
    wall_started = time.perf_counter()
    cpu_started = time.process_time()
    result = operation()
    records.append(
        {
            "step": name,
            "wall_seconds": time.perf_counter() - wall_started,
            "cpu_seconds": time.process_time() - cpu_started,
            "peak_working_set_gib": process_memory_observation().peak_bytes
            / float(1024**3),
        }
    )
    return result


def _squared_distances(values: np.ndarray) -> np.ndarray:
    distances = (
        np.sum(values * values, axis=1)[:, None]
        + np.sum(values * values, axis=1)[None, :]
        - 2.0 * (values @ values.T)
    )
    return np.maximum(distances, 0.0)


def _synthetic_payload(benchmark: dict[str, Any]) -> dict[str, np.ndarray]:
    rng = np.random.default_rng(int(benchmark["seed"]))
    training_rows = int(benchmark["training_rows"])
    validation_rows = int(benchmark["validation_rows"])
    width = int(benchmark["compressed_feature_count"])
    x_train = rng.normal(size=(training_rows, width))
    x_valid = rng.normal(size=(validation_rows, width))
    low_train = 0.55 * x_train[:, 0] - 0.20 * x_train[:, 1]
    low_valid = 0.55 * x_valid[:, 0] - 0.20 * x_valid[:, 1]
    high_train = low_train + 0.18 * np.sin(x_train[:, 2]) - 0.08 * x_train[:, 3] ** 2
    high_valid = low_valid + 0.18 * np.sin(x_valid[:, 2]) - 0.08 * x_valid[:, 3] ** 2
    safety_train = x_train[:, 0] - 0.5 * x_train[:, 1] + 0.25 * np.sin(x_train[:, 4])
    safety_valid = x_valid[:, 0] - 0.5 * x_valid[:, 1] + 0.25 * np.sin(x_valid[:, 4])
    threshold = float(np.quantile(safety_train, 0.40))
    y_train = (safety_train >= threshold).astype(int)
    y_valid = (safety_valid >= threshold).astype(int)
    if set(np.unique(y_train)) != {0, 1} or set(np.unique(y_valid)) != {0, 1}:
        raise ValueError("D016-C1 synthetic labels require both classes")
    scaler = StandardScaler().fit(x_train)
    return {
        "x_train": scaler.transform(x_train),
        "x_valid": scaler.transform(x_valid),
        "low_train": low_train,
        "low_valid": low_valid,
        "high_train": high_train,
        "high_valid": high_valid,
        "y_train": y_train,
        "y_valid": y_valid,
    }


def _gamma(x_train: np.ndarray, multiplier: float) -> float:
    distances = _squared_distances(x_train)
    positive = distances[distances > 0.0]
    if positive.size == 0:
        raise ValueError("A02 synthetic median distance is zero")
    return float(multiplier) / float(np.median(positive))


def _admission(config: dict[str, Any], projection: dict[str, float]) -> dict[str, Any]:
    ceilings = config["ceilings"]
    checks = {
        "cpu_core_hours": (projection["projected_cpu_core_hours"], float(ceilings["branch_cpu_core_hours"]), "le"),
        "wall_clock_days": (projection["projected_wall_clock_days"], float(ceilings["branch_wall_clock_days"]), "le"),
        "new_artifacts_gib": (projection["projected_new_artifacts_gib"], float(ceilings["branch_new_artifacts_gib"]), "le"),
        "peak_working_set_gib": (projection["observed_peak_rss_gib"], float(ceilings["max_total_project_working_set_gib"]), "le"),
        "free_disk_after_artifacts_gib": (projection["projected_free_disk_after_artifacts_gib"], float(ceilings["minimum_free_disk_gib"]), "ge"),
        "gpu_hours": (0.0, float(ceilings["max_gpu_hours"]), "le"),
    }
    payload = {}
    for name, (observed, limit, comparison) in checks.items():
        passed = observed <= limit if comparison == "le" else observed >= limit
        if comparison == "le":
            utilization = observed / limit if limit else 0.0
        else:
            utilization = limit / observed if observed > 0.0 else float("inf")
        payload[name] = {
            "observed": observed,
            "limit": limit,
            "comparison": "less_than_or_equal" if comparison == "le" else "greater_than_or_equal",
            "passed": passed,
            "utilization_fraction": utilization,
        }
    return {
        "status": "PASS" if all(row["passed"] for row in payload.values()) else "STOP",
        "checks": payload,
    }


def main() -> None:
    source_commit, branch = _clean_source()
    config_path = CONFIG.relative_to(ROOT).as_posix()
    config = _load_committed_yaml(source_commit, config_path)
    if config["decision_id"] != "D016-C1":
        raise ValueError("D016-C1 preflight requires the D016-C1 config")
    d016 = _load_committed_json(source_commit, str(config["source_binding"]["d016_result"]))
    if d016.get("decision_id") != "D016-C" or d016.get("status") != "PASS":
        raise PermissionError("D016-C1 requires the completed D016-C PASS evidence")
    if config["authority"]["development_data_fitting_authorized"] is not False:
        raise PermissionError("D016-C1 must not authorize development fitting")

    benchmark = config["benchmark"]
    records: list[dict[str, Any]] = []
    wall_started = time.perf_counter()
    cpu_started = time.process_time()
    data = _timed(records, "synthetic_a02_payload", lambda: _synthetic_payload(benchmark))
    gamma = _gamma(data["x_train"], float(benchmark["gamma_multiplier"]))
    train_residual = residual_target(data["high_train"], data["low_train"])
    valid_residual = residual_target(data["high_valid"], data["low_valid"])

    residual_prediction = _timed(
        records,
        "A02_exact_rbf_residual_fit_predict",
        lambda: KernelRidge(
            alpha=float(benchmark["regularization_alpha"]),
            kernel="rbf",
            gamma=gamma,
        ).fit(data["x_train"], train_residual.residual).predict(data["x_valid"]),
    )
    feasibility_score = _timed(
        records,
        "A02_exact_rbf_feasibility_fit_predict",
        lambda: KernelRidge(
            alpha=float(benchmark["regularization_alpha"]),
            kernel="rbf",
            gamma=gamma,
        ).fit(data["x_train"], data["y_train"]).predict(data["x_valid"]),
    )
    probabilities = np.clip(feasibility_score, 0.0, 1.0)
    wall_seconds = time.perf_counter() - wall_started
    cpu_seconds = time.process_time() - cpu_started
    peak_rss_gib = process_memory_observation().peak_bytes / float(1024**3)
    free_disk_gib = shutil.disk_usage(ROOT).free / float(1024**3)
    workload = config["candidate_workload"]
    units = int(workload["projected_fold_count"]) * int(workload["projected_seed_count"])
    margin = float(workload["projection_margin"])
    artifact_gib = (
        units * margin * int(workload["artifact_bytes_per_fold_seed"]) / float(1024**3)
    )
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
    payload = {
        "schema_version": "0.1.0",
        "decision_id": "D016-C1",
        "corrects_decision_id": "D016-C",
        "protocol_id": "P001",
        "status": admission["status"],
        "evidence_scope": "clean-source synthetic A02 exact-RBF compute admission only",
        "source_commit": source_commit,
        "branch": branch,
        "source_hash_scope": "committed Git blob bytes",
        "source_paths": source_paths,
        "source_hashes": source_hashes,
        "benchmark": {
            **benchmark,
            "gamma": gamma,
            "wall_seconds": wall_seconds,
            "cpu_seconds": cpu_seconds,
            "steps": records,
            "gpu_hours": 0.0,
        },
        "synthetic_metrics": {
            "residual_cost": residual_cost_metrics(
                valid_residual.residual, residual_prediction
            ).__dict__,
            "safety_filter": safety_metrics(
                data["y_valid"],
                probabilities,
                threshold=0.5,
                calibration_bins=10,
            ).__dict__,
        },
        "campaign_projection": projection,
        "admission": admission,
        "machine": {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "numpy": importlib.metadata.version("numpy"),
            "scikit_learn": importlib.metadata.version("scikit-learn"),
            "logical_processors": os.cpu_count(),
            "physical_memory_gib": total_physical_memory_bytes() / float(1024**3),
            "declared_reference_cpu": config["ceilings"]["reference_cpu"],
            "declared_reference_gpu": config["ceilings"]["reference_gpu"],
        },
        "integrity": {
            "clean_source_verified_before_execution": True,
            "synthetic_rows_used": int(benchmark["training_rows"])
            + int(benchmark["validation_rows"]),
            "development_rows_read": 0,
            "calibration_rows_read": 0,
            "final_test_rows_read": 0,
            "hardware_jobs_submitted": 0,
            "gpu_hours": 0.0,
            "gate6_runs": 0,
        },
        "claim_boundary": config["reporting"]["claim_boundary"],
        "next_step": (
            "Prepare D017 development-data-fitting decision"
            if admission["status"] == "PASS"
            else "Record governed A02 compute STOP; do not open development data"
        ),
    }
    output = ROOT / str(source_paths["output"])
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({"status": payload["status"], **projection}, indent=2))
    if payload["status"] != "PASS":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
