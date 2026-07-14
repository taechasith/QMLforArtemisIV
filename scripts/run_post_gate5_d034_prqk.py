"""Run the D034 physics-anchored projected-kernel campaign."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")

from openqfuel.gate5 import (  # noqa: E402
    audit_development_records,
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
from openqfuel.gate4 import read_yaml  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs/post_gate5_d034_prqk.yaml"
PHASE_CONFIG_PATH = ROOT / "configs/phase1_benchmark.yaml"


def _atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    temporary.replace(path)


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
        writer.writerows(rows)
    temporary.replace(path)


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _assert_clean_source() -> str:
    if _git("status", "--porcelain"):
        raise RuntimeError("D034 requires a clean source worktree")
    if _git("branch", "--show-current") != "main":
        raise RuntimeError("D034 requires the main branch")
    return _git("rev-parse", "HEAD")


def _squared_distances(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    values = (
        np.sum(left * left, axis=1)[:, None]
        + np.sum(right * right, axis=1)[None, :]
        - 2.0 * (left @ right.T)
    )
    return np.maximum(values, 0.0)


def _fit_rbf(
    training: np.ndarray,
    targets: np.ndarray,
    row_ids: Sequence[str],
    projection_id: str,
    fold_id: str,
    seed_index: int,
    gamma_multiplier: float,
    alpha: float,
    landmark_count: int,
) -> dict[str, Any]:
    distances = _squared_distances(training, training)
    positive = distances[distances > 0.0]
    if positive.size == 0:
        raise RuntimeError("A02-R training-fold median distance is zero")
    gamma = float(gamma_multiplier) / float(np.median(positive))
    indices = deterministic_landmark_indices(
        row_ids,
        projection_id,
        fold_id,
        seed_index,
        min(landmark_count, training.shape[0]),
    )
    landmarks = training[indices]

    def kernel(left: np.ndarray, right: np.ndarray) -> np.ndarray:
        return np.exp(-gamma * _squared_distances(left, right))

    landmark_kernel = kernel(landmarks, landmarks)
    clipped, _ = symmetrize_and_clip_psd(landmark_kernel)
    eigenvalues, eigenvectors = np.linalg.eigh(clipped)
    inverse_root = (eigenvectors * (1.0 / np.sqrt(eigenvalues))) @ eigenvectors.T
    embedding = kernel(training, landmarks) @ inverse_root
    coefficients = np.linalg.solve(
        embedding.T @ embedding + float(alpha) * np.eye(embedding.shape[1]),
        embedding.T @ targets,
    )
    return {
        "landmarks": landmarks,
        "inverse_root": inverse_root,
        "coefficients": coefficients,
        "gamma": gamma,
    }


def _predict_rbf(model: Mapping[str, Any], values: np.ndarray) -> np.ndarray:
    kernel = np.exp(
        -float(model["gamma"])
        * _squared_distances(values, np.asarray(model["landmarks"], dtype=float))
    )
    return kernel @ np.asarray(model["inverse_root"]) @ np.asarray(
        model["coefficients"]
    )


def _score(
    decision_set_ids: Sequence[str],
    observed_cost: np.ndarray,
    observed_feasible: np.ndarray,
    predicted_cost: np.ndarray | None,
    probability: np.ndarray,
    scale: float,
) -> dict[str, float | int]:
    probability = np.clip(np.asarray(probability, dtype=float), 0.0, 1.0)
    result: dict[str, float | int] = {
        "validation_rows": int(probability.size),
        "brier": float(
            np.mean((probability - np.asarray(observed_feasible, dtype=float)) ** 2)
        ),
    }
    safety = feasibility_metrics(
        observed_feasible, probability, threshold=0.5, calibration_bins=10
    )
    result.update(
        {
            "auroc": safety.auroc,
            "recall": safety.recall,
            "precision": safety.precision,
            "ece": safety.expected_calibration_error,
        }
    )
    if predicted_cost is None:
        return result
    cost = np.asarray(predicted_cost, dtype=float)
    regression = regression_metrics(observed_cost, cost, scale)
    regret = feasibility_constrained_regret(
        decision_set_ids,
        cost,
        probability,
        observed_cost,
        observed_feasible,
        feasibility_threshold=0.5,
        infeasible_penalty_m_s=20.0,
    )
    result.update(
        {
            "rmse": regression.rmse,
            "nrmse": regression.nrmse,
            "mae": regression.mae,
            "mean_regret_m_s": regret.mean_regret_m_s,
            "infeasible_selection_rate": regret.independently_infeasible_selection_rate,
            "no_predicted_feasible_rate": regret.no_predicted_feasible_rate,
        }
    )
    return result


def _config_hash(config: Mapping[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(config, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def run() -> dict[str, Any]:
    source_commit = _assert_clean_source()
    config = read_yaml(CONFIG_PATH)
    phase_config = read_yaml(PHASE_CONFIG_PATH)
    if config.get("decision_id") != "D034" or config.get("protocol_id") != "P002":
        raise RuntimeError("D034 config identity is invalid")
    if not config["authority"]["research_data_fitting_authorized"]:
        raise RuntimeError("D034 development fitting is not authorized")
    if config["locks"]["calibration_rows_read"] != 0 or config["locks"]["final_test_rows_read"] != 0:
        raise RuntimeError("D034 locked-data counters are invalid")

    output_root = ROOT / str(config["reporting"]["result_root"])
    checkpoint_root = ROOT / str(config["reporting"]["checkpoint_root"])
    complete_path = output_root / "campaign_result.json"
    if complete_path.is_file():
        existing = json.loads(complete_path.read_text(encoding="utf-8"))
        if existing.get("source_commit") != source_commit:
            raise RuntimeError("D034 result exists for a different source commit")
        return existing

    records, manifest = load_development_records(ROOT, phase_config)
    audit = audit_development_records(records, manifest, phase_config)
    if audit["rows"] != 39000 or audit["unique_scenarios"] != 39000:
        raise RuntimeError("D034 development data audit did not match the frozen grain")
    fold_rows = fold_manifest_rows(phase_config, manifest)
    fold_ids = sorted({str(row["fold_id"]) for row in fold_rows})
    if fold_ids != ["CV01", "CV02", "CV03", "CV04", "CV05"]:
        raise RuntimeError("D034 grouped fold manifest is invalid")

    specs = [dict(spec) for spec in config["candidate"]["configurations"]]
    seed_indices = [int(value) for value in config["locks"]["seed_indices"]]
    started = time.perf_counter()
    cpu_started = time.process_time()
    fold_metrics: list[dict[str, Any]] = []
    prediction_store: dict[tuple[str, int], dict[str, list[np.ndarray]]] = {}
    machine_rows: list[dict[str, Any]] = []
    registry = {
        str(row["trial_id"]): row
        for row in phase_config.get("models", [])
    }
    registry_payload = read_yaml(ROOT / "experiments/phase1_model_registry.yaml")
    registry = {str(row["trial_id"]): row for row in registry_payload["models"]}
    c06_params = registry["C06-T17"]["parameters"]
    c02_params = registry["C02-T02"]["parameters"]
    all_targets = np.asarray(
        [float(row["outcomes"][phase_config["targets"]["primary_regression"]]) for row in records]
    )
    scale = development_target_scale(all_targets)

    for fold_id in fold_ids:
        context = build_fold_context(
            records,
            manifest,
            phase_config,
            fold_id=fold_id,
            rung_samples=1024,
            qubit_dimensions=[4, 6, 8],
        )
        observed_cost = np.asarray(context.y_validation, dtype=float)
        observed_feasible = np.asarray(context.feasible_validation, dtype=int)
        decision_ids = context.decision_set_ids
        base_train = context.baseline_train_standardized
        base_validation = context.baseline_validation_standardized
        c06_train = np.column_stack((context.x_train_full, base_train))
        c06_validation = np.column_stack((context.x_validation_full, base_validation))

        for seed_index in seed_indices:
            c06_cost_model = build_classical_regressor(
                "physics_residual", c06_params, seed_index, low_fidelity_column=-1
            )
            c06_cost_model.fit(c06_train, context.y_train_standardized)
            c06_cost = context.target_standardizer.inverse(
                c06_cost_model.predict(c06_validation)
            )
            c06_classifier = build_classical_classifier(
                "physics_residual", c06_params, seed_index
            )
            c06_classifier.fit(context.x_train_full, context.feasible_train)
            c06_probability = c06_classifier.predict_proba(
                context.x_validation_full
            )[:, 1]
            for model_id, cost, probability in (
                ("C06", c06_cost, c06_probability),
                (
                    "BASELINE",
                    context.target_standardizer.inverse(base_validation),
                    c06_probability,
                ),
            ):
                key = (model_id, seed_index)
                prediction_store.setdefault(key, {"cost": [], "probability": [], "labels": [], "observed": [], "decision_ids": []})
                prediction_store[key]["cost"].append(np.asarray(cost))
                prediction_store[key]["probability"].append(np.asarray(probability))
                prediction_store[key]["labels"].append(observed_feasible)
                prediction_store[key]["observed"].append(observed_cost)
                prediction_store[key]["decision_ids"].extend(decision_ids)
                metrics = _score(decision_ids, observed_cost, observed_feasible, cost, probability, scale)
                fold_metrics.append({"model_id": model_id, "config_id": model_id, "fold_id": fold_id, "seed_index": seed_index, **metrics})

            c02_classifier = build_classical_classifier("extra_trees", c02_params, seed_index)
            c02_classifier.fit(context.x_train_full, context.feasible_train)
            c02_probability = c02_classifier.predict_proba(context.x_validation_full)[:, 1]
            key = ("C02", seed_index)
            prediction_store.setdefault(key, {"cost": [], "probability": [], "labels": [], "observed": [], "decision_ids": []})
            prediction_store[key]["probability"].append(np.asarray(c02_probability))
            prediction_store[key]["labels"].append(observed_feasible)
            prediction_store[key]["observed"].append(observed_cost)
            prediction_store[key]["decision_ids"].extend(decision_ids)
            fold_metrics.append({"model_id": "C02", "config_id": "C02", "fold_id": fold_id, "seed_index": seed_index, **_score(decision_ids, observed_cost, observed_feasible, None, c02_probability, scale)})

        for spec in specs:
            model_id = str(spec["id"])
            q = int(spec["qubits"])
            projected_train = projected_quantum_features(
                context.compressed_train[q],
                q,
                int(spec["layers"]),
                feature_scale=float(spec["feature_scale"]),
                entangle=bool(spec["entangle"]),
            )
            projected_validation = projected_quantum_features(
                context.compressed_validation[q],
                q,
                int(spec["layers"]),
                feature_scale=float(spec["feature_scale"]),
                entangle=bool(spec["entangle"]),
            )
            for seed_index in seed_indices:
                parameters = {
                    "n_qubits": q,
                    "layers": int(spec["layers"]),
                    "alpha": float(spec["alpha"]),
                    "landmarks": int(spec["landmarks"]),
                    "gamma_multiplier": float(spec["gamma_multiplier"]),
                    "projection_id": model_id,
                    "fold_id": fold_id,
                    "seed_index": seed_index,
                    "feature_scale": float(spec["feature_scale"]),
                    "entangle": bool(spec["entangle"]),
                }
                cost_model = PhysicsAnchoredProjectedQuantumKernelRegressor(**parameters)
                cost_model.fit_projected(
                    projected_train,
                    base_train,
                    context.y_train_standardized,
                    row_ids=context.row_ids,
                )
                cost = context.target_standardizer.inverse(
                    cost_model.predict_projected(projected_validation, base_validation)
                )
                safety_model = PhysicsAnchoredProjectedQuantumKernelRegressor(**parameters)
                safety_model.fit_projected(
                    projected_train,
                    np.zeros_like(base_train),
                    context.feasible_train.astype(float),
                    row_ids=context.row_ids,
                )
                probability = np.clip(
                    safety_model.predict_projected(
                        projected_validation, np.zeros_like(base_validation)
                    ),
                    0.0,
                    1.0,
                )
                key = (model_id, seed_index)
                prediction_store.setdefault(key, {"cost": [], "probability": [], "labels": [], "observed": [], "decision_ids": []})
                prediction_store[key]["cost"].append(np.asarray(cost))
                prediction_store[key]["probability"].append(np.asarray(probability))
                prediction_store[key]["labels"].append(observed_feasible)
                prediction_store[key]["observed"].append(observed_cost)
                prediction_store[key]["decision_ids"].extend(decision_ids)
                fold_metrics.append({"model_id": model_id, "config_id": model_id, "fold_id": fold_id, "seed_index": seed_index, **_score(decision_ids, observed_cost, observed_feasible, cost, probability, scale)})

                a02_model = _fit_rbf(
                    context.compressed_train[q],
                    context.y_train_standardized - base_train,
                    context.row_ids,
                    model_id,
                    fold_id,
                    seed_index,
                    float(spec["gamma_multiplier"]),
                    float(spec["alpha"]),
                    int(spec["landmarks"]),
                )
                a02_cost = context.target_standardizer.inverse(
                    base_validation + _predict_rbf(a02_model, context.compressed_validation[q])
                )
                a02_safety_model = _fit_rbf(
                    context.compressed_train[q],
                    context.feasible_train.astype(float),
                    context.row_ids,
                    model_id,
                    fold_id,
                    seed_index,
                    float(spec["gamma_multiplier"]),
                    float(spec["alpha"]),
                    int(spec["landmarks"]),
                )
                a02_probability = np.clip(
                    _predict_rbf(a02_safety_model, context.compressed_validation[q]),
                    0.0,
                    1.0,
                )
                a02_id = f"A02-R-q{q}"
                key = (a02_id, seed_index)
                prediction_store.setdefault(key, {"cost": [], "probability": [], "labels": [], "observed": [], "decision_ids": []})
                prediction_store[key]["cost"].append(np.asarray(a02_cost))
                prediction_store[key]["probability"].append(np.asarray(a02_probability))
                prediction_store[key]["labels"].append(observed_feasible)
                prediction_store[key]["observed"].append(observed_cost)
                prediction_store[key]["decision_ids"].extend(decision_ids)
                fold_metrics.append({"model_id": a02_id, "config_id": a02_id, "fold_id": fold_id, "seed_index": seed_index, **_score(decision_ids, observed_cost, observed_feasible, a02_cost, a02_probability, scale)})

        machine_rows.append(
            {
                "fold_id": fold_id,
                "training_rows": int(context.train_indices.size),
                "validation_rows": int(context.validation_indices.size),
                "decision_sets": len(set(decision_ids)),
                "qubits": "4;6;8",
            }
        )

    per_seed: list[dict[str, Any]] = []
    for (model_id, seed_index), values in sorted(prediction_store.items()):
        cost = (
            np.concatenate(values["cost"]) if values["cost"] else None
        )
        probability = np.concatenate(values["probability"])
        labels = np.concatenate(values["labels"])
        observed = np.concatenate(values["observed"])
        metrics = _score(
            values["decision_ids"], observed, labels, cost, probability, scale
        )
        per_seed.append(
            {
                "model_id": model_id,
                "seed_index": seed_index,
                **metrics,
            }
        )

    summary: list[dict[str, Any]] = []
    for model_id in sorted({str(row["model_id"]) for row in per_seed}):
        rows = [row for row in per_seed if row["model_id"] == model_id]
        record: dict[str, Any] = {
            "model_id": model_id,
            "seed_count": len(rows),
        }
        for metric in ("nrmse", "mae", "mean_regret_m_s", "infeasible_selection_rate", "brier", "auroc", "recall", "precision", "ece"):
            values = np.asarray([float(row[metric]) for row in rows if metric in row], dtype=float)
            if values.size:
                record[f"mean_{metric}"] = float(np.mean(values))
                record[f"std_{metric}"] = float(np.std(values, ddof=1)) if values.size > 1 else 0.0
        summary.append(record)

    def seed_values(model_id: str, metric: str) -> np.ndarray:
        return np.asarray([
            float(row[metric]) for row in per_seed
            if row["model_id"] == model_id and metric in row
        ])

    primary = "PRQK-08-N"
    c06_nrmse = seed_values("C06", "nrmse")
    primary_nrmse = seed_values(primary, "nrmse")
    if c06_nrmse.size != primary_nrmse.size or c06_nrmse.size != len(seed_indices):
        raise RuntimeError("D034 primary/C06 paired seed counts are incomplete")
    differences = primary_nrmse - c06_nrmse
    interval = paired_bootstrap_mean_interval(
        differences, confidence_level=0.95, replicates=10000, seed=34001
    )
    primary_summary = next(row for row in summary if row["model_id"] == primary)
    c06_summary = next(row for row in summary if row["model_id"] == "C06")
    c02_summary = next(row for row in summary if row["model_id"] == "C02")
    regret_pass = primary_summary["mean_mean_regret_m_s"] <= c06_summary["mean_mean_regret_m_s"]
    infeasible_pass = primary_summary["mean_infeasible_selection_rate"] <= c06_summary["mean_infeasible_selection_rate"]
    safety_pass = (
        primary_summary["mean_brier"] <= 1.05 * c02_summary["mean_brier"]
        and primary_summary["mean_auroc"] >= c02_summary["mean_auroc"] - 0.01
        and primary_summary["mean_recall"] >= c02_summary["mean_recall"] - 0.02
    )
    scientific_superiority = bool(
        primary_summary["mean_nrmse"] <= 0.95 * c06_summary["mean_nrmse"]
        and interval.upper < 0.0
        and regret_pass
        and infeasible_pass
        and safety_pass
    )
    elapsed = time.perf_counter() - started
    cpu_seconds = time.process_time() - cpu_started
    memory = process_memory_observation()
    free_disk_gib = float(__import__("shutil").disk_usage(ROOT).free / 1024**3)
    checkpoint_root.mkdir(parents=True, exist_ok=True)
    _write_csv(output_root / "fold_seed_metrics.csv", fold_metrics)
    _write_csv(output_root / "per_seed_metrics.csv", per_seed)
    _write_csv(output_root / "summary.csv", summary)
    _write_csv(
        output_root / "paired_comparison.csv",
        [
            {
                "comparison": "PRQK-08-N_minus_C06_nrmse",
                "seed_count": int(differences.size),
                "mean_difference": float(interval.estimate),
                "lower_95": float(interval.lower),
                "upper_95": float(interval.upper),
                "superiority_threshold": "upper_95 < 0 and mean <= -0.05*C06",
            }
        ],
    )
    result = {
        "schema_version": "0.1.0",
        "decision_id": "D034",
        "protocol_id": "P002",
        "status": "complete_scientifically_superior" if scientific_superiority else "complete_valid_negative",
        "source_commit": source_commit,
        "config_sha256": _config_hash(config),
        "development_audit": audit,
        "folds": machine_rows,
        "development_rows_read": len(records),
        "calibration_rows_read": 0,
        "final_test_rows_read": 0,
        "hardware_jobs_submitted": 0,
        "gate6_runs": 0,
        "primary_model": primary,
        "primary_summary": primary_summary,
        "c06_summary": c06_summary,
        "c02_summary": c02_summary,
        "paired_nrmse_interval": {
            "estimate": interval.estimate,
            "lower": interval.lower,
            "upper": interval.upper,
            "confidence_level": interval.confidence_level,
        },
        "decision_checks": {
            "five_percent_nrmse_improvement": bool(primary_summary["mean_nrmse"] <= 0.95 * c06_summary["mean_nrmse"]),
            "paired_upper_bound_below_zero": bool(interval.upper < 0.0),
            "regret_not_worse": bool(regret_pass),
            "infeasible_selection_not_worse": bool(infeasible_pass),
            "safety_comparator_rule": bool(safety_pass),
        },
        "runtime": {
            "wall_clock_seconds": elapsed,
            "cpu_seconds": cpu_seconds,
            "peak_working_set_gib": memory.peak_bytes / 1024**3,
            "memory_backend": memory.backend,
            "free_disk_gib": free_disk_gib,
        },
        "claim_boundary": config["reporting"]["claim_boundary"],
        "result_files": [
            "fold_seed_metrics.csv",
            "per_seed_metrics.csv",
            "summary.csv",
            "paired_comparison.csv",
        ],
    }
    _atomic_json(complete_path, result)
    _atomic_json(output_root / "campaign_summary.json", result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return result


if __name__ == "__main__":
    run()
