"""Run the D040 centered error-conditioned global-fidelity campaign."""

from __future__ import annotations

import json
import os
import shutil
import time
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")

from openqfuel.gate4 import read_yaml  # noqa: E402
from openqfuel.gate5 import (  # noqa: E402
    audit_development_records,
    fold_manifest_rows,
    load_development_records,
)
from openqfuel.models import build_classical_classifier, build_classical_regressor  # noqa: E402
from openqfuel.phase1_analysis import development_target_scale, paired_bootstrap_mean_interval  # noqa: E402
from openqfuel.post_gate5 import process_memory_observation  # noqa: E402
from openqfuel.post_gate5_campaign import build_fold_context  # noqa: E402
from openqfuel.qml import (  # noqa: E402
    deterministic_landmark_indices,
    quantum_kernel_matrix,
    symmetrize_and_clip_psd,
    TaskAlignedProjection,
)

try:
    from scripts.run_post_gate5_d039_ecgfrk import (  # noqa: E402
        _atomic_json,
        _inner_cross_fitted_c06,
        _projection_hash,
        _score,
        _source_commit,
        _write_csv,
    )
except ModuleNotFoundError as error:
    if error.name != "scripts":
        raise
    from run_post_gate5_d039_ecgfrk import (  # type: ignore[no-redef] # noqa: E402
        _atomic_json,
        _inner_cross_fitted_c06,
        _projection_hash,
        _score,
        _source_commit,
        _write_csv,
    )


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs/post_gate5_d040_cegfrk.yaml"
PHASE_CONFIG_PATH = ROOT / "configs/phase1_benchmark.yaml"


def _squared_distances(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    return np.maximum(
        np.sum(left * left, axis=1)[:, None]
        + np.sum(right * right, axis=1)[None, :]
        - 2.0 * (left @ right.T),
        0.0,
    )


def _fit_centered_fidelity(
    training: np.ndarray,
    target: np.ndarray,
    row_ids: Sequence[str],
    config_id: str,
    fold_id: str,
    seed: int,
    n_qubits: int,
    layers: int,
    feature_scale: float,
    entangle: bool,
    alpha: float,
    landmarks: int,
) -> dict[str, Any]:
    if alpha <= 0.0 or landmarks <= 0:
        raise ValueError("D040 fidelity ridge settings must be positive")
    indices = deterministic_landmark_indices(
        row_ids, config_id, fold_id, seed, min(landmarks, training.shape[0])
    )
    landmark_values = training[indices]
    landmark_kernel = quantum_kernel_matrix(
        landmark_values,
        landmark_values,
        n_qubits,
        layers,
        feature_scale=feature_scale,
        entangle=entangle,
    )
    clipped, info = symmetrize_and_clip_psd(landmark_kernel)
    eigenvalues, eigenvectors = np.linalg.eigh(clipped)
    inverse_root = (eigenvectors * (1.0 / np.sqrt(eigenvalues))) @ eigenvectors.T
    cross_kernel = quantum_kernel_matrix(
        training,
        landmark_values,
        n_qubits,
        layers,
        feature_scale=feature_scale,
        entangle=entangle,
    )
    embedded = cross_kernel @ inverse_root
    feature_mean = np.mean(embedded, axis=0)
    centered = embedded - feature_mean
    coefficients = np.linalg.solve(
        centered.T @ centered + alpha * np.eye(centered.shape[1]),
        centered.T @ target,
    )
    return {
        "landmarks": landmark_values,
        "inverse_root": inverse_root,
        "feature_mean": feature_mean,
        "coefficients": coefficients,
        "n_qubits": n_qubits,
        "layers": layers,
        "feature_scale": feature_scale,
        "entangle": entangle,
        "psd_info": info,
        "train_mean_abs_after_centering": float(np.max(np.abs(np.mean(centered, axis=0)))),
    }


def _predict_centered_fidelity(model: Mapping[str, Any], values: np.ndarray) -> np.ndarray:
    kernel = quantum_kernel_matrix(
        values,
        np.asarray(model["landmarks"], dtype=float),
        int(model["n_qubits"]),
        int(model["layers"]),
        feature_scale=float(model["feature_scale"]),
        entangle=bool(model["entangle"]),
    )
    embedded = kernel @ np.asarray(model["inverse_root"])
    return (embedded - np.asarray(model["feature_mean"])) @ np.asarray(model["coefficients"])


def _fit_centered_rbf(
    training: np.ndarray,
    target: np.ndarray,
    row_ids: Sequence[str],
    config_id: str,
    fold_id: str,
    seed: int,
    gamma_multiplier: float,
    alpha: float,
    landmarks: int,
) -> dict[str, Any]:
    distances = _squared_distances(training, training)
    positive = distances[distances > 0.0]
    if positive.size == 0:
        raise RuntimeError("D040 centered RBF median distance is zero")
    gamma = float(gamma_multiplier) / float(np.median(positive))
    indices = deterministic_landmark_indices(
        row_ids, config_id, fold_id, seed, min(landmarks, training.shape[0])
    )
    landmark_values = training[indices]

    def kernel(left: np.ndarray, right: np.ndarray) -> np.ndarray:
        return np.exp(-gamma * _squared_distances(left, right))

    landmark_kernel = kernel(landmark_values, landmark_values)
    clipped, _ = symmetrize_and_clip_psd(landmark_kernel)
    eigenvalues, eigenvectors = np.linalg.eigh(clipped)
    inverse_root = (eigenvectors * (1.0 / np.sqrt(eigenvalues))) @ eigenvectors.T
    embedded = kernel(training, landmark_values) @ inverse_root
    feature_mean = np.mean(embedded, axis=0)
    centered = embedded - feature_mean
    coefficients = np.linalg.solve(
        centered.T @ centered + float(alpha) * np.eye(centered.shape[1]),
        centered.T @ target,
    )
    return {
        "landmarks": landmark_values,
        "inverse_root": inverse_root,
        "feature_mean": feature_mean,
        "coefficients": coefficients,
        "gamma": gamma,
        "train_mean_abs_after_centering": float(np.max(np.abs(np.mean(centered, axis=0)))),
    }


def _predict_centered_rbf(model: Mapping[str, Any], values: np.ndarray) -> np.ndarray:
    embedded = np.exp(
        -float(model["gamma"])
        * _squared_distances(values, np.asarray(model["landmarks"], dtype=float))
    ) @ np.asarray(model["inverse_root"])
    return (embedded - np.asarray(model["feature_mean"])) @ np.asarray(model["coefficients"])


def run() -> dict[str, Any]:
    source_commit = _source_commit()
    config = read_yaml(CONFIG_PATH)
    phase_config = read_yaml(PHASE_CONFIG_PATH)
    if config.get("decision_id") != "D040" or config.get("protocol_id") != "P008":
        raise RuntimeError("D040 config identity is invalid")
    if not bool(config["authority"]["research_data_fitting_authorized"]):
        raise RuntimeError("D040 fitting is not authorized")
    d039_result = json.loads(
        (ROOT / "data/processed/reporting/post_gate5_d039_ecgfrk/campaign_result.json").read_text(encoding="utf-8")
    )
    if d039_result.get("status") != "complete_valid_negative":
        raise RuntimeError("D040 requires an integrity-valid D039 negative")
    free_disk = shutil.disk_usage(ROOT).free / 1024**3
    floor = float(config["resources"]["free_disk_floor_gib"])
    if free_disk < floor:
        raise RuntimeError(f"D040 free disk preflight is below {floor:.1f} GiB: {free_disk:.3f} GiB")
    output_root = ROOT / str(config["reporting"]["result_root"])
    result_path = output_root / "campaign_result.json"
    if result_path.is_file():
        result = json.loads(result_path.read_text(encoding="utf-8"))
        if result.get("source_commit") != source_commit:
            raise RuntimeError("D040 result belongs to another source commit")
        return result

    records, manifest = load_development_records(ROOT, phase_config)
    audit = audit_development_records(records, manifest, phase_config)
    if audit["rows"] != 39000 or audit["unique_scenarios"] != 39000:
        raise RuntimeError("D040 development grain does not match the frozen audit")
    fold_ids = sorted({str(row["fold_id"]) for row in fold_manifest_rows(phase_config, manifest)})
    if fold_ids != ["CV01", "CV02", "CV03", "CV04", "CV05"]:
        raise RuntimeError("D040 outer fold manifest is invalid")
    registry_payload = read_yaml(ROOT / "experiments/phase1_model_registry.yaml")
    registry = {str(row["trial_id"]): row for row in registry_payload["models"]}
    c06_parameters = registry["C06-T17"]["parameters"]
    targets = np.asarray(
        [float(row["outcomes"][phase_config["targets"]["primary_regression"]]) for row in records],
        dtype=float,
    )
    scale = development_target_scale(targets)
    seeds = [int(value) for value in config["locks"]["seed_indices"]]
    specs = [dict(value) for value in config["candidate"]["configurations"]]
    lambda_value = float(config["candidate"]["shrinkage"])
    started = time.perf_counter()
    cpu_started = time.process_time()
    fold_metrics: list[dict[str, Any]] = []
    inner_audit: list[dict[str, Any]] = []
    projection_audit: list[dict[str, Any]] = []
    fidelity_audit: list[dict[str, Any]] = []
    centering_audit: list[dict[str, Any]] = []
    prediction_store: dict[tuple[str, int], dict[str, list[np.ndarray] | list[str]]] = {}

    for outer_fold in fold_ids:
        context = build_fold_context(
            records, manifest, phase_config, fold_id=outer_fold,
            rung_samples=1024, qubit_dimensions=[4, 6, 8]
        )
        observed = np.asarray(context.y_validation, dtype=float)
        feasible = np.asarray(context.feasible_validation, dtype=int)
        decision_ids = context.decision_set_ids
        base_train = context.baseline_train_standardized
        base_validation = context.baseline_validation_standardized
        c06_validation_x = np.column_stack((context.x_validation_full, base_validation))
        for seed in seeds:
            c06_cost = build_classical_regressor("physics_residual", c06_parameters, seed, low_fidelity_column=-1)
            c06_cost.fit(np.column_stack((context.x_train_full, base_train)), context.y_train_standardized)
            c06_standardized_validation = c06_cost.predict(c06_validation_x)
            c06_prediction = context.target_standardizer.inverse(c06_standardized_validation)
            c06_safety = build_classical_classifier("physics_residual", c06_parameters, seed)
            c06_safety.fit(context.x_train_full, context.feasible_train)
            probability = c06_safety.predict_proba(context.x_validation_full)[:, 1]
            crossfit_baseline, crossfit_rows = _inner_cross_fitted_c06(
                records, context, outer_fold, seed, c06_parameters,
                int(config["locks"]["inner_grouped_folds"]),
            )
            inner_audit.extend(crossfit_rows)

            key = ("C06", seed)
            prediction_store.setdefault(key, {"cost": [], "probability": [], "labels": [], "observed": [], "decision_ids": []})
            prediction_store[key]["cost"].append(c06_prediction)
            prediction_store[key]["probability"].append(probability)
            prediction_store[key]["labels"].append(feasible)
            prediction_store[key]["observed"].append(observed)
            prediction_store[key]["decision_ids"].extend(decision_ids)
            fold_metrics.append({"model_id": "C06", "config_id": "C06", "outer_fold": outer_fold, "seed_index": seed, **_score(decision_ids, observed, feasible, c06_prediction, probability, scale)})

            for spec in specs:
                q = int(spec["qubits"])
                raw_train = np.asarray(context.compressed_train[q], dtype=float)
                raw_validation = np.asarray(context.compressed_validation[q], dtype=float)
                residual = context.y_train_standardized - crossfit_baseline
                train_input = np.column_stack((raw_train, crossfit_baseline))
                validation_input = np.column_stack((raw_validation, c06_standardized_validation))
                if train_input.shape != (raw_train.shape[0], q + 1) or validation_input.shape != (raw_validation.shape[0], q + 1):
                    raise RuntimeError("D040 conditioning feature shape is invalid")
                if not np.all(np.isfinite(train_input)) or not np.all(np.isfinite(validation_input)):
                    raise RuntimeError("D040 conditioning features are not finite")
                config_id = str(spec["id"])
                projection = TaskAlignedProjection(n_components=q).fit(train_input, residual)
                aligned_train = projection.transform(train_input)
                aligned_validation = projection.transform(validation_input)
                projection_audit.append(
                    {
                        "outer_fold": outer_fold,
                        "seed_index": seed,
                        "config_id": config_id,
                        "fit_rows": int(raw_train.shape[0]),
                        "fit_features": int(train_input.shape[1]),
                        "validation_rows": int(raw_validation.shape[0]),
                        "projection_components": q,
                        "projection_hash": _projection_hash(projection),
                        "conditioning_feature": "cross_fitted_c06_train_outer_c06_validation",
                        "validation_outcomes_used": 0,
                    }
                )
                fidelity = _fit_centered_fidelity(
                    aligned_train, residual, context.row_ids, config_id, outer_fold, seed,
                    q, int(spec["layers"]), float(spec["feature_scale"]), bool(spec["entangle"]),
                    float(spec["alpha"]), int(spec["landmarks"]),
                )
                quantum_delta = _predict_centered_fidelity(fidelity, aligned_validation)
                rbf = _fit_centered_rbf(
                    aligned_train, residual, context.row_ids, config_id, outer_fold, seed,
                    0.25, float(spec["alpha"]), int(spec["landmarks"]),
                )
                rbf_delta = _predict_centered_rbf(rbf, aligned_validation)
                fidelity_audit.append(
                    {
                        "outer_fold": outer_fold,
                        "seed_index": seed,
                        "config_id": config_id,
                        "q": q,
                        "layers": int(spec["layers"]),
                        "entangle": bool(spec["entangle"]),
                        "state_dimension": 2**q,
                        "landmarks": min(int(spec["landmarks"]), aligned_train.shape[0]),
                        "lambda": lambda_value,
                        "psd_clipped_eigenvalues": fidelity["psd_info"].clipped_eigenvalues,
                        "min_eigenvalue_before_clip": fidelity["psd_info"].min_eigenvalue_before_clip,
                        "conditioning_feature": "cross_fitted_c06_train_outer_c06_validation",
                        "validation_outcomes_used": 0,
                    }
                )
                centering_audit.append(
                    {
                        "outer_fold": outer_fold,
                        "seed_index": seed,
                        "config_id": config_id,
                        "q": q,
                        "train_feature_width": int(aligned_train.shape[1]),
                        "quantum_train_center_mean_abs": fidelity["train_mean_abs_after_centering"],
                        "classical_train_center_mean_abs": rbf["train_mean_abs_after_centering"],
                        "centering_source": "outer_training_rows_only",
                        "validation_outcomes_used": 0,
                    }
                )
                quantum_id = config_id
                rbf_id = f"EC-TAP-RBF-C-SHR-q{q}-L010"
                quantum_prediction = context.target_standardizer.inverse(c06_standardized_validation + lambda_value * quantum_delta)
                rbf_prediction = context.target_standardizer.inverse(c06_standardized_validation + lambda_value * rbf_delta)
                for model_id, prediction in ((quantum_id, quantum_prediction), (rbf_id, rbf_prediction)):
                    key = (model_id, seed)
                    prediction_store.setdefault(key, {"cost": [], "probability": [], "labels": [], "observed": [], "decision_ids": []})
                    prediction_store[key]["cost"].append(prediction)
                    prediction_store[key]["probability"].append(probability)
                    prediction_store[key]["labels"].append(feasible)
                    prediction_store[key]["observed"].append(observed)
                    prediction_store[key]["decision_ids"].extend(decision_ids)
                    fold_metrics.append({"model_id": model_id, "config_id": model_id, "outer_fold": outer_fold, "seed_index": seed, **_score(decision_ids, observed, feasible, prediction, probability, scale)})

    per_seed: list[dict[str, Any]] = []
    for (model_id, seed), values in sorted(prediction_store.items()):
        per_seed.append({
            "model_id": model_id,
            "seed_index": seed,
            **_score(
                values["decision_ids"], np.concatenate(values["observed"]),
                np.concatenate(values["labels"]), np.concatenate(values["cost"]),
                np.concatenate(values["probability"]), scale,
            ),
        })

    summary: list[dict[str, Any]] = []
    for model_id in sorted({str(row["model_id"]) for row in per_seed}):
        rows = [row for row in per_seed if row["model_id"] == model_id]
        record: dict[str, Any] = {"model_id": model_id, "seed_count": len(rows)}
        for metric in ("nrmse", "mae", "mean_regret_m_s", "infeasible_selection_rate", "brier", "auroc", "recall"):
            values = np.asarray([float(row[metric]) for row in rows], dtype=float)
            record[f"mean_{metric}"] = float(np.mean(values))
            record[f"std_{metric}"] = float(np.std(values, ddof=1)) if values.size > 1 else 0.0
        summary.append(record)

    def metric(model_id: str, name: str) -> np.ndarray:
        return np.asarray([float(row[name]) for row in per_seed if row["model_id"] == model_id])

    primary = "CE-GFRK-08-L010"
    control = "EC-TAP-RBF-C-SHR-q8-L010"
    c06_nrmse = metric("C06", "nrmse")
    primary_nrmse = metric(primary, "nrmse")
    control_nrmse = metric(control, "nrmse")
    if c06_nrmse.size != 20 or primary_nrmse.size != 20 or control_nrmse.size != 20:
        raise RuntimeError("D040 paired seed endpoint is incomplete")
    interval = paired_bootstrap_mean_interval(primary_nrmse - c06_nrmse, confidence_level=0.95, replicates=10000, seed=40040)
    primary_summary = next(row for row in summary if row["model_id"] == primary)
    c06_summary = next(row for row in summary if row["model_id"] == "C06")
    control_summary = next(row for row in summary if row["model_id"] == control)
    checks = {
        "five_percent_nrmse_improvement": primary_summary["mean_nrmse"] <= 0.95 * c06_summary["mean_nrmse"],
        "paired_upper_bound_below_zero": interval.upper < 0.0,
        "regret_not_worse": primary_summary["mean_mean_regret_m_s"] <= c06_summary["mean_mean_regret_m_s"],
        "infeasible_selection_not_worse": primary_summary["mean_infeasible_selection_rate"] <= c06_summary["mean_infeasible_selection_rate"],
        "beats_classical_shrunk_rbf_by_five_percent": primary_summary["mean_nrmse"] <= 0.95 * control_summary["mean_nrmse"],
    }
    result = {
        "schema_version": "0.1.0",
        "decision_id": "D040",
        "protocol_id": "P008",
        "status": "complete_scientifically_superior" if all(checks.values()) else "complete_valid_negative",
        "source_commit": source_commit,
        "development_audit": audit,
        "development_rows_read": len(records),
        "calibration_rows_read": 0,
        "final_test_rows_read": 0,
        "hardware_jobs_submitted": 0,
        "gate6_runs": 0,
        "primary_model": primary,
        "primary_summary": primary_summary,
        "c06_summary": c06_summary,
        "classical_shrunk_rbf_summary": control_summary,
        "decision_checks": checks,
        "paired_nrmse_interval": {"estimate": interval.estimate, "lower": interval.lower, "upper": interval.upper, "confidence_level": interval.confidence_level},
        "inner_audit_rows": len(inner_audit),
        "projection_audit_rows": len(projection_audit),
        "fidelity_audit_rows": len(fidelity_audit),
        "centering_audit_rows": len(centering_audit),
        "conditioning_feature": "cross_fitted_c06_train_outer_c06_validation",
        "centering_source": "outer_training_rows_only",
        "runtime": {
            "wall_clock_seconds": time.perf_counter() - started,
            "cpu_seconds": time.process_time() - cpu_started,
            "peak_working_set_gib": process_memory_observation().peak_bytes / 1024**3,
            "free_disk_gib": shutil.disk_usage(ROOT).free / 1024**3,
            "free_disk_preflight_gib": free_disk,
        },
        "claim_boundary": config["reporting"]["claim_boundary"],
        "result_files": ["inner_fold_audit.csv", "projection_audit.csv", "fidelity_audit.csv", "centering_audit.csv", "fold_seed_metrics.csv", "per_seed_metrics.csv", "summary.csv", "paired_comparison.csv"],
    }
    _write_csv(output_root / "inner_fold_audit.csv", inner_audit)
    _write_csv(output_root / "projection_audit.csv", projection_audit)
    _write_csv(output_root / "fidelity_audit.csv", fidelity_audit)
    _write_csv(output_root / "centering_audit.csv", centering_audit)
    _write_csv(output_root / "fold_seed_metrics.csv", fold_metrics)
    _write_csv(output_root / "per_seed_metrics.csv", per_seed)
    _write_csv(output_root / "summary.csv", summary)
    _write_csv(output_root / "paired_comparison.csv", [{"comparison": "CE-GFRK-08-L010_minus_C06_nrmse", "seed_count": 20, "mean_difference": interval.estimate, "lower_95": interval.lower, "upper_95": interval.upper}])
    _atomic_json(result_path, result)
    _atomic_json(output_root / "campaign_summary.json", result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return result


if __name__ == "__main__":
    run()
