"""Run the D016-C clean-source synthetic CRES/CSAFE compute preflight."""

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
from sklearn.ensemble import RandomForestClassifier  # noqa: E402
from sklearn.kernel_approximation import RBFSampler  # noqa: E402
from sklearn.linear_model import LogisticRegression, Ridge  # noqa: E402
from sklearn.neural_network import MLPRegressor  # noqa: E402
from sklearn.pipeline import make_pipeline  # noqa: E402
from sklearn.preprocessing import StandardScaler  # noqa: E402

from openqfuel.post_gate5 import (  # noqa: E402
    process_memory_observation,
    total_physical_memory_bytes,
)
from openqfuel.post_gate5_classical import (  # noqa: E402
    assert_d015_scope,
    residual_cost_metrics,
    residual_target,
    safety_metrics,
    select_safety_threshold,
)


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/post_gate5_d016_classical_compute_preflight.yaml"


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
        raise RuntimeError("D016-C requires a clean Git worktree")
    branch = _git("branch", "--show-current")
    if branch != "main":
        raise RuntimeError("D016-C is accepted only on main")
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


def _synthetic_payload(benchmark: dict[str, Any]) -> dict[str, np.ndarray]:
    rng = np.random.default_rng(int(benchmark["seed"]))
    training_rows = int(benchmark["training_rows"])
    validation_rows = int(benchmark["validation_rows"])
    primary_width = int(benchmark["primary_feature_count"])
    compressed_width = int(benchmark["compressed_feature_count"])
    x_train = rng.normal(size=(training_rows, primary_width))
    x_valid = rng.normal(size=(validation_rows, primary_width))
    z_train = x_train[:, :compressed_width] + 0.05 * rng.normal(
        size=(training_rows, compressed_width)
    )
    z_valid = x_valid[:, :compressed_width] + 0.05 * rng.normal(
        size=(validation_rows, compressed_width)
    )
    low_train = (
        0.70 * x_train[:, 0]
        - 0.35 * x_train[:, 1]
        + 0.15 * np.sin(x_train[:, 2])
    )
    low_valid = (
        0.70 * x_valid[:, 0]
        - 0.35 * x_valid[:, 1]
        + 0.15 * np.sin(x_valid[:, 2])
    )
    high_train = low_train + (
        0.20 * np.sin(x_train[:, 3])
        - 0.10 * x_train[:, 4] * x_train[:, 5]
        + 0.03 * rng.normal(size=training_rows)
    )
    high_valid = low_valid + (
        0.20 * np.sin(x_valid[:, 3])
        - 0.10 * x_valid[:, 4] * x_valid[:, 5]
        + 0.03 * rng.normal(size=validation_rows)
    )
    score_train = (
        0.9 * x_train[:, 0]
        - 0.6 * x_train[:, 1]
        + 0.35 * np.sin(x_train[:, 6])
        - 0.2 * x_train[:, 7] * x_train[:, 8]
    )
    score_valid = (
        0.9 * x_valid[:, 0]
        - 0.6 * x_valid[:, 1]
        + 0.35 * np.sin(x_valid[:, 6])
        - 0.2 * x_valid[:, 7] * x_valid[:, 8]
    )
    threshold = float(np.quantile(score_train, 0.40))
    y_train = (score_train >= threshold).astype(int)
    y_valid = (score_valid >= threshold).astype(int)
    if set(np.unique(y_train)) != {0, 1} or set(np.unique(y_valid)) != {0, 1}:
        raise ValueError("D016 synthetic safety labels require both classes")
    return {
        "x_train": x_train,
        "x_valid": x_valid,
        "z_train": z_train,
        "z_valid": z_valid,
        "low_train": low_train,
        "low_valid": low_valid,
        "high_train": high_train,
        "high_valid": high_valid,
        "y_train": y_train,
        "y_valid": y_valid,
    }


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
    if config["decision_id"] != "D016-C":
        raise ValueError("D016-C preflight requires the D016-C config")
    if config["authority"]["preflight_execution_authorized"] is not True:
        raise PermissionError("D016-C preflight is not authorized")
    if config["authority"]["development_data_fitting_authorized"] is not False:
        raise PermissionError("D016-C must not authorize development fitting")

    d015 = _load_committed_yaml(
        source_commit, str(config["source_binding"]["d015_config"])
    )
    assert_d015_scope(d015, action="synthetic_validation", data_scope="synthetic")

    benchmark = config["benchmark"]
    records: list[dict[str, Any]] = []
    wall_started = time.perf_counter()
    cpu_started = time.process_time()
    data = _timed(records, "synthetic_largest_fold_payload", lambda: _synthetic_payload(benchmark))
    train_residual = residual_target(data["high_train"], data["low_train"])
    valid_residual = residual_target(data["high_valid"], data["low_valid"])

    ridge_prediction = _timed(
        records,
        "CRES_ridge_residual_fit_predict",
        lambda: make_pipeline(StandardScaler(), Ridge(alpha=1.0)).fit(
            data["x_train"], train_residual.residual
        ).predict(data["x_valid"]),
    )
    rbf_prediction = _timed(
        records,
        "CRES_random_feature_rbf_residual_fit_predict",
        lambda: make_pipeline(
            StandardScaler(),
            RBFSampler(
                gamma=1.0 / float(benchmark["compressed_feature_count"]),
                n_components=int(benchmark["random_feature_count"]),
                random_state=int(benchmark["seed"]),
            ),
            Ridge(alpha=1.0),
        ).fit(data["z_train"], train_residual.residual).predict(data["z_valid"]),
    )
    mlp_prediction = _timed(
        records,
        "CRES_compressed_mlp_residual_fit_predict",
        lambda: make_pipeline(
            StandardScaler(),
            MLPRegressor(
                hidden_layer_sizes=(int(benchmark["mlp_hidden_units"]),),
                activation="relu",
                solver="adam",
                alpha=0.001,
                max_iter=int(benchmark["mlp_max_iter"]),
                random_state=int(benchmark["seed"]),
            ),
        ).fit(data["z_train"], train_residual.residual).predict(data["z_valid"]),
    )
    residual_metrics = {
        "ridge": residual_cost_metrics(valid_residual.residual, ridge_prediction).__dict__,
        "random_feature_rbf": residual_cost_metrics(
            valid_residual.residual, rbf_prediction
        ).__dict__,
        "compressed_mlp": residual_cost_metrics(
            valid_residual.residual, mlp_prediction
        ).__dict__,
    }

    logistic_prob = _timed(
        records,
        "CSAFE_calibrated_logistic_fit_predict",
        lambda: make_pipeline(
            StandardScaler(),
            LogisticRegression(
                class_weight="balanced",
                max_iter=500,
                random_state=int(benchmark["seed"]),
            ),
        ).fit(data["x_train"], data["y_train"]).predict_proba(data["x_valid"])[:, 1],
    )
    tree_prob = _timed(
        records,
        "CSAFE_class_weighted_tree_fit_predict",
        lambda: RandomForestClassifier(
            n_estimators=int(benchmark["tree_count"]),
            max_depth=int(benchmark["tree_max_depth"]),
            class_weight="balanced",
            random_state=int(benchmark["seed"]),
            n_jobs=1,
        ).fit(data["x_train"], data["y_train"]).predict_proba(data["x_valid"])[:, 1],
    )
    threshold = select_safety_threshold(
        data["y_train"],
        np.clip(data["y_train"] * 0.75 + 0.125, 0.0, 1.0),
        minimum_recall=float(benchmark["safety_minimum_recall"]),
        maximum_intervention_rate=float(benchmark["safety_maximum_intervention_rate"]),
    )
    safety = {
        "threshold": threshold,
        "logistic": safety_metrics(
            data["y_valid"],
            logistic_prob,
            threshold=threshold,
            calibration_bins=int(benchmark["calibration_bins"]),
        ).__dict__,
        "class_weighted_tree": safety_metrics(
            data["y_valid"],
            tree_prob,
            threshold=threshold,
            calibration_bins=int(benchmark["calibration_bins"]),
        ).__dict__,
    }

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
        "decision_id": "D016-C",
        "protocol_id": "P001",
        "status": admission["status"],
        "evidence_scope": "clean-source synthetic classical-first compute admission only",
        "source_commit": source_commit,
        "branch": branch,
        "source_hash_scope": "committed Git blob bytes",
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
            "residual_cost": residual_metrics,
            "safety_filter": safety,
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
            else "Record governed resource STOP; do not open development data"
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
