"""Run the D035 cross-fitted C06-stacked quantum residual campaign."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import shutil
import subprocess
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
    deterministic_group_folds,
    fold_manifest_rows,
    load_development_records,
)
from openqfuel.models import build_classical_classifier, build_classical_regressor  # noqa: E402
from openqfuel.phase1_analysis import (  # noqa: E402
    development_target_scale,
    feasibility_constrained_regret,
    feasibility_metrics,
    paired_bootstrap_mean_interval,
    regression_metrics,
)
from openqfuel.post_gate5 import process_memory_observation  # noqa: E402
from openqfuel.post_gate5_campaign import build_fold_context  # noqa: E402
from openqfuel.qml import (  # noqa: E402
    PhysicsAnchoredProjectedQuantumKernelRegressor,
    deterministic_landmark_indices,
    projected_quantum_features,
    symmetrize_and_clip_psd,
)


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs/post_gate5_d035_cfqsr.yaml"
PHASE_CONFIG_PATH = ROOT / "configs/phase1_benchmark.yaml"


def _write_csv(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"Cannot write empty CSV: {path}")
    fields: list[str] = []
    for row in rows:
        for field in row:
            if field not in fields:
                fields.append(field)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(row for row in rows)
    temporary.replace(path)


def _atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout.strip()


def _source_commit() -> str:
    if _git("status", "--porcelain"):
        raise RuntimeError("D035 requires a clean source worktree")
    if _git("branch", "--show-current") != "main":
        raise RuntimeError("D035 requires the main branch")
    return _git("rev-parse", "HEAD")


def _squared_distances(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    return np.maximum(
        np.sum(left * left, axis=1)[:, None]
        + np.sum(right * right, axis=1)[None, :]
        - 2.0 * (left @ right.T),
        0.0,
    )


def _fit_rbf(
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
        raise RuntimeError("D035 A02-STACK median distance is zero")
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
    coefficients = np.linalg.solve(
        embedded.T @ embedded + float(alpha) * np.eye(embedded.shape[1]),
        embedded.T @ target,
    )
    return {
        "landmarks": landmark_values,
        "inverse_root": inverse_root,
        "coefficients": coefficients,
        "gamma": gamma,
    }


def _predict_rbf(model: Mapping[str, Any], values: np.ndarray) -> np.ndarray:
    kernel = np.exp(
        -float(model["gamma"])
        * _squared_distances(values, np.asarray(model["landmarks"], dtype=float))
    )
    return kernel @ np.asarray(model["inverse_root"]) @ np.asarray(model["coefficients"])


def _score(
    decision_ids: Sequence[str],
    observed: np.ndarray,
    feasible: np.ndarray,
    predicted: np.ndarray,
    probability: np.ndarray,
    scale: float,
) -> dict[str, float | int]:
    probability = np.clip(np.asarray(probability, dtype=float), 0.0, 1.0)
    regression = regression_metrics(observed, predicted, scale)
    regret = feasibility_constrained_regret(
        decision_ids,
        predicted,
        probability,
        observed,
        feasible,
        feasibility_threshold=0.5,
        infeasible_penalty_m_s=20.0,
    )
    safety = feasibility_metrics(feasible, probability, threshold=0.5, calibration_bins=10)
    return {
        "validation_rows": int(observed.size),
        "nrmse": regression.nrmse,
        "mae": regression.mae,
        "mean_regret_m_s": regret.mean_regret_m_s,
        "infeasible_selection_rate": regret.independently_infeasible_selection_rate,
        "brier": safety.brier,
        "auroc": safety.auroc,
        "recall": safety.recall,
        "precision": safety.precision,
        "ece": safety.expected_calibration_error,
    }


def _inner_cross_fitted_c06(
    records: Sequence[Mapping[str, Any]],
    context: Any,
    outer_fold: str,
    seed: int,
    c06_parameters: Mapping[str, Any],
    inner_folds: int,
) -> tuple[np.ndarray, list[dict[str, Any]]]:
    groups = [str(records[index]["group_id"]) for index in context.train_indices]
    unique_groups = sorted(set(groups))
    assignments = deterministic_group_folds(
        unique_groups,
        master_seed=35035,
        fold_count=inner_folds,
        strata={group: ("all", "all") for group in unique_groups},
    )
    oof = np.empty(context.train_indices.size, dtype=float)
    audit_rows: list[dict[str, Any]] = []
    for inner_fold in range(1, inner_folds + 1):
        hold_positions = np.asarray(
            [position for position, group in enumerate(groups) if assignments[group] == inner_fold],
            dtype=int,
        )
        fit_positions = np.asarray(
            [position for position, group in enumerate(groups) if assignments[group] != inner_fold],
            dtype=int,
        )
        if not hold_positions.size or not fit_positions.size:
            raise RuntimeError("D035 inner grouped fold is empty")
        fit_groups = sorted({groups[position] for position in fit_positions})
        hold_groups = sorted({groups[position] for position in hold_positions})
        if set(fit_groups) & set(hold_groups):
            raise RuntimeError("D035 inner C06 fit/holdout groups overlap")
        model_seed = int.from_bytes(
            hashlib.sha256(f"P003|D035|{outer_fold}|{inner_fold}|{seed}".encode()).digest()[-4:],
            "big",
        )
        model = build_classical_regressor(
            "physics_residual", c06_parameters, model_seed, low_fidelity_column=-1
        )
        fit_x = np.column_stack(
            (context.x_train_full[fit_positions], context.baseline_train_standardized[fit_positions])
        )
        hold_x = np.column_stack(
            (context.x_train_full[hold_positions], context.baseline_train_standardized[hold_positions])
        )
        model.fit(fit_x, context.y_train_standardized[fit_positions])
        oof[hold_positions] = model.predict(hold_x)
        audit_rows.append(
            {
                "outer_fold": outer_fold,
                "seed_index": seed,
                "inner_fold": inner_fold,
                "fit_groups": ";".join(fit_groups),
                "holdout_groups": ";".join(hold_groups),
                "group_intersection_count": 0,
                "fit_rows": int(fit_positions.size),
                "holdout_rows": int(hold_positions.size),
            }
        )
    if not np.all(np.isfinite(oof)):
        raise RuntimeError("D035 inner cross-fitted C06 residual is incomplete")
    return oof, audit_rows


def run() -> dict[str, Any]:
    source_commit = _source_commit()
    config = read_yaml(CONFIG_PATH)
    phase_config = read_yaml(PHASE_CONFIG_PATH)
    if config.get("decision_id") != "D035" or config.get("protocol_id") != "P003":
        raise RuntimeError("D035 config identity is invalid")
    if not bool(config["authority"]["research_data_fitting_authorized"]):
        raise RuntimeError("D035 fitting is not authorized")
    output_root = ROOT / str(config["reporting"]["result_root"])
    result_path = output_root / "campaign_result.json"
    if result_path.is_file():
        result = json.loads(result_path.read_text(encoding="utf-8"))
        if result.get("source_commit") != source_commit:
            raise RuntimeError("D035 result belongs to another source commit")
        return result

    records, manifest = load_development_records(ROOT, phase_config)
    audit = audit_development_records(records, manifest, phase_config)
    if audit["rows"] != 39000 or audit["unique_scenarios"] != 39000:
        raise RuntimeError("D035 development grain does not match the frozen audit")
    fold_ids = sorted({str(row["fold_id"]) for row in fold_manifest_rows(phase_config, manifest)})
    if fold_ids != ["CV01", "CV02", "CV03", "CV04", "CV05"]:
        raise RuntimeError("D035 outer fold manifest is invalid")
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
    started = time.perf_counter()
    cpu_started = time.process_time()
    fold_metrics: list[dict[str, Any]] = []
    inner_audit: list[dict[str, Any]] = []
    prediction_store: dict[tuple[str, int], dict[str, list[np.ndarray] | list[str]]] = {}

    for outer_fold in fold_ids:
        context = build_fold_context(
            records,
            manifest,
            phase_config,
            fold_id=outer_fold,
            rung_samples=1024,
            qubit_dimensions=[4, 6, 8],
        )
        observed = np.asarray(context.y_validation, dtype=float)
        feasible = np.asarray(context.feasible_validation, dtype=int)
        decision_ids = context.decision_set_ids
        base_train = context.baseline_train_standardized
        base_validation = context.baseline_validation_standardized
        c06_validation_x = np.column_stack((context.x_validation_full, base_validation))
        for seed in seeds:
            c06_cost = build_classical_regressor(
                "physics_residual", c06_parameters, seed, low_fidelity_column=-1
            )
            c06_cost.fit(
                np.column_stack((context.x_train_full, base_train)),
                context.y_train_standardized,
            )
            c06_standardized_validation = c06_cost.predict(c06_validation_x)
            c06_prediction = context.target_standardizer.inverse(c06_standardized_validation)
            c06_safety = build_classical_classifier("physics_residual", c06_parameters, seed)
            c06_safety.fit(context.x_train_full, context.feasible_train)
            probability = c06_safety.predict_proba(context.x_validation_full)[:, 1]
            crossfit_baseline, crossfit_rows = _inner_cross_fitted_c06(
                records,
                context,
                outer_fold,
                seed,
                c06_parameters,
                int(config["locks"]["inner_grouped_folds"]),
            )
            inner_audit.extend(crossfit_rows)
            for model_id, cost in (("C06", c06_prediction),):
                key = (model_id, seed)
                prediction_store.setdefault(key, {"cost": [], "probability": [], "labels": [], "observed": [], "decision_ids": []})
                prediction_store[key]["cost"].append(cost)
                prediction_store[key]["probability"].append(probability)
                prediction_store[key]["labels"].append(feasible)
                prediction_store[key]["observed"].append(observed)
                prediction_store[key]["decision_ids"].extend(decision_ids)
                fold_metrics.append({"model_id": model_id, "config_id": model_id, "outer_fold": outer_fold, "seed_index": seed, **_score(decision_ids, observed, feasible, cost, probability, scale)})

            for spec in specs:
                config_id = str(spec["id"])
                q = int(spec["qubits"])
                projected_train = projected_quantum_features(
                    context.compressed_train[q], q, int(spec["layers"]),
                    feature_scale=float(spec["feature_scale"]), entangle=bool(spec["entangle"])
                )
                projected_validation = projected_quantum_features(
                    context.compressed_validation[q], q, int(spec["layers"]),
                    feature_scale=float(spec["feature_scale"]), entangle=bool(spec["entangle"])
                )
                parameters = {
                    "n_qubits": q,
                    "layers": int(spec["layers"]),
                    "alpha": float(spec["alpha"]),
                    "landmarks": int(spec["landmarks"]),
                    "gamma_multiplier": float(spec["gamma_multiplier"]),
                    "projection_id": config_id,
                    "fold_id": outer_fold,
                    "seed_index": seed,
                    "feature_scale": float(spec["feature_scale"]),
                    "entangle": bool(spec["entangle"]),
                }
                quantum = PhysicsAnchoredProjectedQuantumKernelRegressor(**parameters)
                quantum.fit_projected(
                    projected_train,
                    crossfit_baseline,
                    context.y_train_standardized,
                    row_ids=context.row_ids,
                )
                quantum_prediction = context.target_standardizer.inverse(
                    quantum.predict_projected(projected_validation, c06_standardized_validation)
                )
                key = (config_id, seed)
                prediction_store.setdefault(key, {"cost": [], "probability": [], "labels": [], "observed": [], "decision_ids": []})
                prediction_store[key]["cost"].append(quantum_prediction)
                prediction_store[key]["probability"].append(probability)
                prediction_store[key]["labels"].append(feasible)
                prediction_store[key]["observed"].append(observed)
                prediction_store[key]["decision_ids"].extend(decision_ids)
                fold_metrics.append({"model_id": config_id, "config_id": config_id, "outer_fold": outer_fold, "seed_index": seed, **_score(decision_ids, observed, feasible, quantum_prediction, probability, scale)})

                rbf = _fit_rbf(
                    context.compressed_train[q],
                    context.y_train_standardized - crossfit_baseline,
                    context.row_ids,
                    config_id,
                    outer_fold,
                    seed,
                    float(spec["gamma_multiplier"]),
                    float(spec["alpha"]),
                    int(spec["landmarks"]),
                )
                rbf_prediction = context.target_standardizer.inverse(
                    c06_standardized_validation + _predict_rbf(rbf, context.compressed_validation[q])
                )
                rbf_id = f"A02-STACK-q{q}"
                key = (rbf_id, seed)
                prediction_store.setdefault(key, {"cost": [], "probability": [], "labels": [], "observed": [], "decision_ids": []})
                prediction_store[key]["cost"].append(rbf_prediction)
                prediction_store[key]["probability"].append(probability)
                prediction_store[key]["labels"].append(feasible)
                prediction_store[key]["observed"].append(observed)
                prediction_store[key]["decision_ids"].extend(decision_ids)
                fold_metrics.append({"model_id": rbf_id, "config_id": rbf_id, "outer_fold": outer_fold, "seed_index": seed, **_score(decision_ids, observed, feasible, rbf_prediction, probability, scale)})

    per_seed: list[dict[str, Any]] = []
    for (model_id, seed), values in sorted(prediction_store.items()):
        cost = np.concatenate(values["cost"])
        observed = np.concatenate(values["observed"])
        feasible = np.concatenate(values["labels"])
        probability = np.concatenate(values["probability"])
        metrics = _score(values["decision_ids"], observed, feasible, cost, probability, scale)
        per_seed.append({"model_id": model_id, "seed_index": seed, **metrics})

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

    primary = "CFQSR-08-N"
    c06_nrmse = metric("C06", "nrmse")
    primary_nrmse = metric(primary, "nrmse")
    rbf_nrmse = metric("A02-STACK-q8", "nrmse")
    if c06_nrmse.size != 20 or primary_nrmse.size != 20 or rbf_nrmse.size != 20:
        raise RuntimeError("D035 paired seed endpoint is incomplete")
    interval = paired_bootstrap_mean_interval(
        primary_nrmse - c06_nrmse, confidence_level=0.95, replicates=10000, seed=35035
    )
    primary_summary = next(row for row in summary if row["model_id"] == primary)
    c06_summary = next(row for row in summary if row["model_id"] == "C06")
    rbf_summary = next(row for row in summary if row["model_id"] == "A02-STACK-q8")
    checks = {
        "five_percent_nrmse_improvement": primary_summary["mean_nrmse"] <= 0.95 * c06_summary["mean_nrmse"],
        "paired_upper_bound_below_zero": interval.upper < 0.0,
        "regret_not_worse": primary_summary["mean_mean_regret_m_s"] <= c06_summary["mean_mean_regret_m_s"],
        "infeasible_selection_not_worse": primary_summary["mean_infeasible_selection_rate"] <= c06_summary["mean_infeasible_selection_rate"],
        "beats_classical_stack_by_five_percent": primary_summary["mean_nrmse"] <= 0.95 * rbf_summary["mean_nrmse"],
    }
    result = {
        "schema_version": "0.1.0",
        "decision_id": "D035",
        "protocol_id": "P003",
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
        "a02_stack_q8_summary": rbf_summary,
        "decision_checks": checks,
        "paired_nrmse_interval": {
            "estimate": interval.estimate,
            "lower": interval.lower,
            "upper": interval.upper,
            "confidence_level": interval.confidence_level,
        },
        "runtime": {
            "wall_clock_seconds": time.perf_counter() - started,
            "cpu_seconds": time.process_time() - cpu_started,
            "peak_working_set_gib": process_memory_observation().peak_bytes / 1024**3,
            "free_disk_gib": shutil.disk_usage(ROOT).free / 1024**3,
        },
        "claim_boundary": config["reporting"]["claim_boundary"],
        "result_files": ["inner_fold_audit.csv", "fold_seed_metrics.csv", "per_seed_metrics.csv", "summary.csv", "paired_comparison.csv"],
    }
    _write_csv(output_root / "inner_fold_audit.csv", inner_audit)
    _write_csv(output_root / "fold_seed_metrics.csv", fold_metrics)
    _write_csv(output_root / "per_seed_metrics.csv", per_seed)
    _write_csv(output_root / "summary.csv", summary)
    _write_csv(output_root / "paired_comparison.csv", [{"comparison": "CFQSR-08-N_minus_C06_nrmse", "seed_count": 20, "mean_difference": interval.estimate, "lower_95": interval.lower, "upper_95": interval.upper}])
    _atomic_json(result_path, result)
    _atomic_json(output_root / "campaign_summary.json", result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return result


if __name__ == "__main__":
    run()
