"""D017-C development-only CRES/CSAFE classical-first campaign."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import subprocess
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import yaml
from sklearn.ensemble import RandomForestClassifier
from sklearn.kernel_approximation import RBFSampler
from sklearn.kernel_ridge import KernelRidge
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .gate5 import (
    audit_development_records,
    load_development_records,
    validate_development_output_path,
)
from .post_gate5 import process_memory_observation
from .post_gate5_campaign import build_fold_context
from .post_gate5_classical import (
    residual_cost_metrics,
    residual_target,
    safety_metrics,
    select_safety_threshold,
)


FOLD_IDS = ("CV01", "CV02", "CV03", "CV04", "CV05")
SEED_INDICES = tuple(range(1, 21))


def _git(root: Path, *args: str, binary: bool = False) -> str | bytes:
    completed = subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        capture_output=True,
        text=not binary,
    )
    return completed.stdout


def _clean_source(root: Path) -> tuple[str, str]:
    status = str(_git(root, "status", "--porcelain")).strip()
    if status:
        raise PermissionError("D017-C execution requires a clean Git worktree")
    branch = str(_git(root, "branch", "--show-current")).strip()
    if branch != "main":
        raise PermissionError("D017-C execution is accepted only on main")
    return str(_git(root, "rev-parse", "HEAD")).strip(), branch


def _git_blob_sha256(root: Path, commit: str, relative_path: str) -> str:
    blob = _git(root, "show", f"{commit}:{relative_path}", binary=True)
    if not isinstance(blob, bytes):
        raise TypeError("Git blob reader returned text unexpectedly")
    return hashlib.sha256(blob).hexdigest()


def _committed_yaml(root: Path, commit: str, relative_path: str) -> dict[str, Any]:
    blob = _git(root, "show", f"{commit}:{relative_path}", binary=True)
    if not isinstance(blob, bytes):
        raise TypeError("Git blob reader returned text unexpectedly")
    payload = yaml.safe_load(blob.decode("utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"Committed YAML must contain a mapping: {relative_path}")
    return payload


def _committed_json(root: Path, commit: str, relative_path: str) -> dict[str, Any]:
    blob = _git(root, "show", f"{commit}:{relative_path}", binary=True)
    if not isinstance(blob, bytes):
        raise TypeError("Git blob reader returned text unexpectedly")
    payload = json.loads(blob.decode("utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"Committed JSON must contain an object: {relative_path}")
    return payload


def _seed(master_seed: int, *parts: object) -> int:
    material = "|".join([str(master_seed), *[str(part) for part in parts]]).encode()
    return int(hashlib.sha256(material).hexdigest()[:8], 16)


def _low_cost(records: Sequence[Mapping[str, Any]], indices: np.ndarray) -> np.ndarray:
    return np.asarray(
        [float(records[index]["inputs"]["low_fidelity_cost_m_s"]) for index in indices],
        dtype=float,
    )


def _target(records: Sequence[Mapping[str, Any]], indices: np.ndarray, name: str) -> np.ndarray:
    return np.asarray(
        [float(records[index]["outcomes"][name]) for index in indices],
        dtype=float,
    )


def _exact_rbf_gamma(x_train: np.ndarray) -> float:
    distances = (
        np.sum(x_train * x_train, axis=1)[:, None]
        + np.sum(x_train * x_train, axis=1)[None, :]
        - 2.0 * (x_train @ x_train.T)
    )
    positive = np.maximum(distances, 0.0)
    values = positive[positive > 0.0]
    if values.size == 0:
        raise ValueError("A02 exact RBF median distance is zero")
    return 1.0 / float(np.median(values))


def _write_csv(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0]) if rows else ["empty"]
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _probability(model: Any, values: np.ndarray) -> np.ndarray:
    if hasattr(model, "predict_proba"):
        return np.asarray(model.predict_proba(values)[:, 1], dtype=float)
    return np.clip(np.asarray(model.predict(values), dtype=float), 0.0, 1.0)


def _append_cres(
    rows: list[dict[str, Any]],
    *,
    model_id: str,
    fold_id: str,
    seed_index: int,
    truth_residual: np.ndarray,
    prediction: np.ndarray,
) -> None:
    metrics = residual_cost_metrics(truth_residual, prediction)
    rows.append(
        {
            "model_id": model_id,
            "fold_id": fold_id,
            "seed_index": seed_index,
            "validation_rows": int(truth_residual.size),
            "rmse": metrics.rmse,
            "nrmse": metrics.nrmse,
            "mae": metrics.mae,
            "tail_abs_error_q90": metrics.tail_abs_error_q90,
            "tail_abs_error_q95": metrics.tail_abs_error_q95,
        }
    )


def _append_csafe(
    rows: list[dict[str, Any]],
    *,
    model_id: str,
    fold_id: str,
    seed_index: int,
    labels: np.ndarray,
    probabilities: np.ndarray,
    threshold: float,
    bins: int,
) -> None:
    metrics = safety_metrics(labels, probabilities, threshold=threshold, calibration_bins=bins)
    rows.append(
        {
            "model_id": model_id,
            "fold_id": fold_id,
            "seed_index": seed_index,
            "validation_rows": int(labels.size),
            "threshold": threshold,
            "brier": metrics.brier,
            "auroc": metrics.auroc,
            "recall": metrics.recall,
            "precision": metrics.precision,
            "false_negative_rate": metrics.false_negative_rate,
            "false_positive_rate": metrics.false_positive_rate,
            "expected_calibration_error": metrics.expected_calibration_error,
            "intervention_rate": metrics.intervention_rate,
        }
    )


def _summarize(rows: Sequence[Mapping[str, Any]], metric_names: Sequence[str]) -> list[dict[str, Any]]:
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["model_id"])].append(row)
    summary = []
    for model_id in sorted(grouped):
        model_rows = grouped[model_id]
        item: dict[str, Any] = {
            "model_id": model_id,
            "fold_seed_rows": len(model_rows),
            "validation_rows_per_seed_sum": int(sum(int(row["validation_rows"]) for row in model_rows)),
        }
        for metric in metric_names:
            values = np.asarray([float(row[metric]) for row in model_rows], dtype=float)
            item[f"mean_{metric}"] = float(np.mean(values))
            item[f"median_{metric}"] = float(np.median(values))
            item[f"best_{metric}"] = float(np.min(values))
            item[f"worst_{metric}"] = float(np.max(values))
        summary.append(item)
    return summary


def _verify_authority(root: Path, source_commit: str) -> dict[str, Any]:
    config = _committed_yaml(
        root, source_commit, "configs/post_gate5_d017_classical_first_development.yaml"
    )
    if (
        config.get("decision_id") != "D017-C"
        or config.get("status") != "accepted_development_only_classical_first_campaign_pending"
    ):
        raise PermissionError("D017-C authority is not active")
    authority = config["authority"]
    if (
        authority.get("campaign_execution_authorized") is not True
        or authority.get("development_data_fitting_authorized") is not True
        or authority.get("calibration_access_authorized") is not False
        or authority.get("final_test_access_authorized") is not False
        or authority.get("gate6_authorized") is not False
    ):
        raise PermissionError("D017-C authority boundary is invalid")
    d016 = _committed_json(root, source_commit, str(config["source_binding"]["d016_result"]))
    d016_c1 = _committed_json(root, source_commit, str(config["source_binding"]["d016_c1_result"]))
    if d016.get("decision_id") != "D016-C" or d016.get("status") != "PASS":
        raise PermissionError("D017-C requires D016-C PASS")
    if d016_c1.get("decision_id") != "D016-C1" or d016_c1.get("status") != "PASS":
        raise PermissionError("D017-C requires D016-C1 PASS")
    return config


def run_d017_campaign(root: Path) -> dict[str, Any]:
    """Run the one authorized D017-C development-only campaign."""

    source_commit, branch = _clean_source(root)
    config = _verify_authority(root, source_commit)
    output_root = validate_development_output_path(
        root, root / str(config["campaign"]["output_root"])
    )
    complete_path = output_root / "campaign_summary.json"
    failure_path = output_root / "campaign_failure.json"
    if complete_path.is_file():
        existing = json.loads(complete_path.read_text(encoding="utf-8"))
        if existing.get("source_commit") != source_commit:
            raise PermissionError("D017 completed campaign source mismatch")
        return existing
    if failure_path.is_file():
        raise PermissionError("D017 has a recorded failure; new authority is required")

    phase_config = _committed_yaml(root, source_commit, str(config["source_binding"]["phase1_config"]))
    source_hashes = {
        key: _git_blob_sha256(root, source_commit, str(path))
        for key, path in config["source_binding"].items()
    }
    wall_started = time.perf_counter()
    cpu_started = time.process_time()
    development_rows_read = 0
    try:
        records, manifest = load_development_records(root, phase_config)
        development_rows_read = len(records)
        audit = audit_development_records(records, manifest, phase_config)
        target_name = str(phase_config["targets"]["primary_regression"])
        cres_rows: list[dict[str, Any]] = []
        csafe_rows: list[dict[str, Any]] = []
        for fold_id in FOLD_IDS:
            context = build_fold_context(
                records,
                manifest,
                phase_config,
                fold_id=fold_id,
                rung_samples=int(config["campaign"]["training_rows_per_fold"]),
                qubit_dimensions=[int(config["campaign"]["compressed_pca_dimensions"])],
            )
            train_low = _low_cost(records, context.train_indices)
            valid_low = _low_cost(records, context.validation_indices)
            train_high = _target(records, context.train_indices, target_name)
            valid_high = context.y_validation
            train_residual = residual_target(train_high, train_low)
            valid_residual = residual_target(valid_high, valid_low)
            x_train = context.x_train_full
            x_valid = context.x_validation_full
            z_train = context.compressed_train[int(config["campaign"]["compressed_pca_dimensions"])]
            z_valid = context.compressed_validation[int(config["campaign"]["compressed_pca_dimensions"])]
            gamma = _exact_rbf_gamma(z_train)
            for seed_index in SEED_INDICES:
                seed = _seed(int(phase_config["scenario_design"]["master_seed"]), "D017", fold_id, seed_index)
                ridge = make_pipeline(StandardScaler(), Ridge(alpha=1.0))
                ridge.fit(x_train, train_residual.residual)
                _append_cres(
                    cres_rows,
                    model_id="ridge_residual",
                    fold_id=fold_id,
                    seed_index=seed_index,
                    truth_residual=valid_residual.residual,
                    prediction=ridge.predict(x_valid),
                )
                rbf = make_pipeline(
                    StandardScaler(),
                    RBFSampler(
                        gamma=1.0 / z_train.shape[1],
                        n_components=512,
                        random_state=seed,
                    ),
                    Ridge(alpha=1.0),
                )
                rbf.fit(z_train, train_residual.residual)
                _append_cres(
                    cres_rows,
                    model_id="random_feature_rbf_residual",
                    fold_id=fold_id,
                    seed_index=seed_index,
                    truth_residual=valid_residual.residual,
                    prediction=rbf.predict(z_valid),
                )
                mlp = make_pipeline(
                    StandardScaler(),
                    MLPRegressor(
                        hidden_layer_sizes=(64,),
                        activation="relu",
                        solver="adam",
                        alpha=0.001,
                        max_iter=50,
                        random_state=seed,
                    ),
                )
                mlp.fit(z_train, train_residual.residual)
                _append_cres(
                    cres_rows,
                    model_id="compressed_mlp_residual",
                    fold_id=fold_id,
                    seed_index=seed_index,
                    truth_residual=valid_residual.residual,
                    prediction=mlp.predict(z_valid),
                )
                a02_cost = KernelRidge(alpha=0.01, kernel="rbf", gamma=gamma)
                a02_cost.fit(z_train, train_residual.residual)
                _append_cres(
                    cres_rows,
                    model_id="a02_exact_rbf_residual",
                    fold_id=fold_id,
                    seed_index=seed_index,
                    truth_residual=valid_residual.residual,
                    prediction=a02_cost.predict(z_valid),
                )

                logistic = make_pipeline(
                    StandardScaler(),
                    LogisticRegression(
                        class_weight="balanced",
                        max_iter=500,
                        random_state=seed,
                    ),
                )
                logistic.fit(x_train, context.feasible_train)
                train_prob = _probability(logistic, x_train)
                valid_prob = _probability(logistic, x_valid)
                threshold = select_safety_threshold(
                    context.feasible_train,
                    train_prob,
                    minimum_recall=float(config["campaign"]["threshold_minimum_recall"]),
                    maximum_intervention_rate=float(config["campaign"]["threshold_maximum_intervention_rate"]),
                )
                _append_csafe(
                    csafe_rows,
                    model_id="calibrated_logistic",
                    fold_id=fold_id,
                    seed_index=seed_index,
                    labels=context.feasible_validation,
                    probabilities=valid_prob,
                    threshold=threshold,
                    bins=int(config["campaign"]["calibration_bins"]),
                )

                tree = RandomForestClassifier(
                    n_estimators=64,
                    max_depth=8,
                    class_weight="balanced",
                    random_state=seed,
                    n_jobs=1,
                )
                tree.fit(x_train, context.feasible_train)
                train_prob = _probability(tree, x_train)
                valid_prob = _probability(tree, x_valid)
                threshold = select_safety_threshold(
                    context.feasible_train,
                    train_prob,
                    minimum_recall=float(config["campaign"]["threshold_minimum_recall"]),
                    maximum_intervention_rate=float(config["campaign"]["threshold_maximum_intervention_rate"]),
                )
                _append_csafe(
                    csafe_rows,
                    model_id="class_weighted_tree",
                    fold_id=fold_id,
                    seed_index=seed_index,
                    labels=context.feasible_validation,
                    probabilities=valid_prob,
                    threshold=threshold,
                    bins=int(config["campaign"]["calibration_bins"]),
                )

                a02_safe = KernelRidge(alpha=0.01, kernel="rbf", gamma=gamma)
                a02_safe.fit(z_train, context.feasible_train)
                train_prob = np.clip(a02_safe.predict(z_train), 0.0, 1.0)
                valid_prob = np.clip(a02_safe.predict(z_valid), 0.0, 1.0)
                threshold = select_safety_threshold(
                    context.feasible_train,
                    train_prob,
                    minimum_recall=float(config["campaign"]["threshold_minimum_recall"]),
                    maximum_intervention_rate=float(config["campaign"]["threshold_maximum_intervention_rate"]),
                )
                _append_csafe(
                    csafe_rows,
                    model_id="a02_exact_rbf_feasibility",
                    fold_id=fold_id,
                    seed_index=seed_index,
                    labels=context.feasible_validation,
                    probabilities=valid_prob,
                    threshold=threshold,
                    bins=int(config["campaign"]["calibration_bins"]),
                )

        cres_summary = _summarize(
            cres_rows,
            ("rmse", "nrmse", "mae", "tail_abs_error_q90", "tail_abs_error_q95"),
        )
        csafe_summary = _summarize(
            csafe_rows,
            (
                "brier",
                "auroc",
                "recall",
                "false_negative_rate",
                "expected_calibration_error",
                "intervention_rate",
            ),
        )
        output_root.mkdir(parents=True, exist_ok=True)
        _write_csv(output_root / "cres_fold_metrics.csv", cres_rows)
        _write_csv(output_root / "cres_summary.csv", cres_summary)
        _write_csv(output_root / "csafe_fold_metrics.csv", csafe_rows)
        _write_csv(output_root / "csafe_summary.csv", csafe_summary)
        files = {
            name: {
                "sha256": _sha256(output_root / name),
                "bytes": (output_root / name).stat().st_size,
            }
            for name in (
                "cres_fold_metrics.csv",
                "cres_summary.csv",
                "csafe_fold_metrics.csv",
                "csafe_summary.csv",
            )
        }
        evidence = {
            "schema_version": "0.1.0",
            "decision_id": "D017-C",
            "source_commit": source_commit,
            "files": files,
        }
        _write_json(output_root / "evidence_manifest.json", evidence)
        summary = {
            "schema_version": "0.1.0",
            "decision_id": "D017-C",
            "protocol_id": "P001",
            "status": "complete",
            "source_commit": source_commit,
            "branch": branch,
            "source_hash_scope": "committed Git blob bytes",
            "source_hashes": source_hashes,
            "development_audit": audit,
            "development_rows_read": development_rows_read,
            "calibration_rows_read": 0,
            "final_test_rows_read": 0,
            "hardware_jobs_submitted": 0,
            "gpu_hours": 0.0,
            "gate6_runs": 0,
            "folds": len(FOLD_IDS),
            "seed_count": len(SEED_INDICES),
            "cres_best_mean_nrmse_model": min(cres_summary, key=lambda row: float(row["mean_nrmse"]))["model_id"],
            "csafe_best_mean_brier_model": min(csafe_summary, key=lambda row: float(row["mean_brier"]))["model_id"],
            "wall_seconds": time.perf_counter() - wall_started,
            "cpu_seconds": time.process_time() - cpu_started,
            "peak_working_set_gib": process_memory_observation().peak_bytes / float(1024**3),
            "logical_processors": os.cpu_count(),
            "evidence_manifest": "evidence_manifest.json",
            "claim_boundary": config["reporting"]["claim_boundary"],
        }
        _write_json(output_root / "campaign_summary.json", summary)
        return summary
    except Exception as error:
        failure = {
            "schema_version": "0.1.0",
            "decision_id": "D017-C",
            "status": "technical_failure",
            "source_commit": source_commit,
            "exception_type": type(error).__name__,
            "exception_message": str(error),
            "development_rows_read": development_rows_read,
            "calibration_rows_read": 0,
            "final_test_rows_read": 0,
            "hardware_jobs_submitted": 0,
            "gpu_hours": 0.0,
            "gate6_runs": 0,
            "retry_authorized": False,
        }
        _write_json(failure_path, failure)
        raise
