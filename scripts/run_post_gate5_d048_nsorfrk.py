"""Run the D048 nested-shrinkage q8 orthogonalized campaign."""

from __future__ import annotations

import json
import os
import shutil
import time
from pathlib import Path
from typing import Any

import numpy as np

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")

from openqfuel.gate4 import read_yaml  # noqa: E402
from openqfuel.gate5 import audit_development_records, fold_manifest_rows, load_development_records  # noqa: E402
from openqfuel.models import build_classical_classifier, build_classical_regressor  # noqa: E402
from openqfuel.phase1_analysis import development_target_scale, paired_bootstrap_mean_interval  # noqa: E402
from openqfuel.post_gate5 import process_memory_observation  # noqa: E402
from openqfuel.post_gate5_campaign import build_fold_context  # noqa: E402
from openqfuel.qml import TaskAlignedProjection  # noqa: E402

try:
    from scripts.run_post_gate5_d036_tapqk import _atomic_json, _score, _source_commit, _write_csv  # noqa: E402
    from scripts.run_post_gate5_d038_gfrk import _fit_fidelity, _predict_fidelity  # noqa: E402
    from scripts.run_post_gate5_d039_ecgfrk import _inner_cross_fitted_c06  # noqa: E402
    from scripts.run_post_gate5_d041_hefrk import _fit_rbf_pair, _predict_rbf_pair  # noqa: E402
    from scripts.run_post_gate5_d043_sfrk import _inner_channel_predictions  # noqa: E402
    from scripts.run_post_gate5_d046_orfrk import _orthogonalized_target  # noqa: E402
    from scripts.run_post_gate5_d047_omfrk import _inner_second_stage_channels  # noqa: E402
except ModuleNotFoundError as error:
    if error.name != "scripts":
        raise
    from run_post_gate5_d036_tapqk import _atomic_json, _score, _source_commit, _write_csv  # type: ignore[no-redef] # noqa: E402
    from run_post_gate5_d038_gfrk import _fit_fidelity, _predict_fidelity  # type: ignore[no-redef] # noqa: E402
    from run_post_gate5_d039_ecgfrk import _inner_cross_fitted_c06  # type: ignore[no-redef] # noqa: E402
    from run_post_gate5_d041_hefrk import _fit_rbf_pair, _predict_rbf_pair  # type: ignore[no-redef] # noqa: E402
    from run_post_gate5_d043_sfrk import _inner_channel_predictions  # type: ignore[no-redef] # noqa: E402
    from run_post_gate5_d046_orfrk import _orthogonalized_target  # type: ignore[no-redef] # noqa: E402
    from run_post_gate5_d047_omfrk import _inner_second_stage_channels  # type: ignore[no-redef] # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs/post_gate5_d048_nsorfrk.yaml"
PHASE_CONFIG_PATH = ROOT / "configs/phase1_benchmark.yaml"


def _select_shrinkage(residual: np.ndarray, first: np.ndarray, second: np.ndarray, grid: tuple[float, ...]) -> tuple[float, list[float]]:
    labels = np.asarray(residual, dtype=float)
    first_values = np.asarray(first, dtype=float)
    second_values = np.asarray(second, dtype=float)
    if labels.shape != first_values.shape or labels.shape != second_values.shape:
        raise ValueError("D048 shrinkage arrays do not have matching shapes")
    if not np.all(np.isfinite(labels)) or not np.all(np.isfinite(first_values)) or not np.all(np.isfinite(second_values)):
        raise ValueError("D048 shrinkage arrays are not finite")
    losses = [float(np.mean((labels - value * (first_values + second_values)) ** 2)) for value in grid]
    if not np.all(np.isfinite(losses)):
        raise ValueError("D048 shrinkage losses are not finite")
    return float(grid[int(np.argmin(np.asarray(losses)))]), losses


def _append_prediction(
    store: dict[tuple[str, int], dict[str, list[np.ndarray] | list[str]]],
    model_id: str,
    seed: int,
    prediction: np.ndarray,
    probability: np.ndarray,
    feasible: np.ndarray,
    observed: np.ndarray,
    decision_ids: list[str],
) -> None:
    key = (model_id, seed)
    store.setdefault(key, {"cost": [], "probability": [], "labels": [], "observed": [], "decision_ids": []})
    store[key]["cost"].append(prediction)
    store[key]["probability"].append(probability)
    store[key]["labels"].append(feasible)
    store[key]["observed"].append(observed)
    store[key]["decision_ids"].extend(decision_ids)


def run() -> dict[str, Any]:
    source_commit = _source_commit()
    config = read_yaml(CONFIG_PATH)
    phase_config = read_yaml(PHASE_CONFIG_PATH)
    if config.get("decision_id") != "D048" or config.get("protocol_id") != "P016":
        raise RuntimeError("D048 config identity is invalid")
    if not bool(config["authority"]["research_data_fitting_authorized"]):
        raise RuntimeError("D048 fitting is not authorized")
    d047_result = json.loads((ROOT / "data/processed/reporting/post_gate5_d047_omfrk/campaign_result.json").read_text(encoding="utf-8"))
    if d047_result.get("status") != "complete_valid_negative":
        raise RuntimeError("D048 requires an integrity-valid D047 negative")
    free_disk = shutil.disk_usage(ROOT).free / 1024**3
    floor = float(config["resources"]["free_disk_floor_gib"])
    if free_disk < floor:
        raise RuntimeError(f"D048 free disk preflight is below {floor:.1f} GiB: {free_disk:.3f} GiB")
    output_root = ROOT / str(config["reporting"]["result_root"])
    result_path = output_root / "campaign_result.json"
    if result_path.is_file():
        result = json.loads(result_path.read_text(encoding="utf-8"))
        if result.get("source_commit") != source_commit:
            raise RuntimeError("D048 result belongs to another source commit")
        return result

    records, manifest = load_development_records(ROOT, phase_config)
    audit = audit_development_records(records, manifest, phase_config)
    if audit["rows"] != 39000 or audit["unique_scenarios"] != 39000:
        raise RuntimeError("D048 development grain does not match the frozen audit")
    fold_ids = sorted({str(row["fold_id"]) for row in fold_manifest_rows(phase_config, manifest)})
    if fold_ids != ["CV01", "CV02", "CV03", "CV04", "CV05"]:
        raise RuntimeError("D048 outer fold manifest is invalid")
    registry_payload = read_yaml(ROOT / "experiments/phase1_model_registry.yaml")
    registry = {str(row["trial_id"]): row for row in registry_payload["models"]}
    c06_parameters = registry["C06-T17"]["parameters"]
    targets = np.asarray([float(row["outcomes"][phase_config["targets"]["primary_regression"]]) for row in records], dtype=float)
    scale = development_target_scale(targets)
    seeds = [int(value) for value in config["locks"]["seed_indices"]]
    grid = tuple(float(value) for value in config["mathematical_contract"]["shrinkage_grid"])
    if grid != (0.05, 0.10, 0.15):
        raise RuntimeError("D048 shrinkage grid is not the frozen grid")
    started = time.perf_counter()
    cpu_started = time.process_time()
    fold_metrics: list[dict[str, Any]] = []
    inner_audit: list[dict[str, Any]] = []
    shared_stage_audit: list[dict[str, Any]] = []
    orthogonal_audit: list[dict[str, Any]] = []
    channel_audit: list[dict[str, Any]] = []
    selection_audit: list[dict[str, Any]] = []
    prediction_store: dict[tuple[str, int], dict[str, list[np.ndarray] | list[str]]] = {}

    for outer_fold in fold_ids:
        context = build_fold_context(records, manifest, phase_config, fold_id=outer_fold, rung_samples=1024, qubit_dimensions=[8])
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
            crossfit_baseline, crossfit_rows = _inner_cross_fitted_c06(records, context, outer_fold, seed, c06_parameters, int(config["locks"]["inner_grouped_folds"]))
            inner_audit.extend(crossfit_rows)
            _append_prediction(prediction_store, "C06", seed, c06_prediction, probability, feasible, observed, decision_ids)
            fold_metrics.append({"model_id": "C06", "config_id": "C06", "outer_fold": outer_fold, "seed_index": seed, **_score(decision_ids, observed, feasible, c06_prediction, probability, scale)})

            residual = context.y_train_standardized - crossfit_baseline
            _, shared_rbf25_oof, _, shared_rows = _inner_channel_predictions(records, context, outer_fold, seed, 8, residual, crossfit_baseline)
            common_target = _orthogonalized_target(residual, shared_rbf25_oof)
            shared_stage_audit.extend([dict(row, stage="shared_q8_rbf25") for row in shared_rows])
            fidelity_oof, rbf50_oof, second_rows = _inner_second_stage_channels(records, context, outer_fold, seed, 8, residual, common_target, crossfit_baseline)
            orthogonal_audit.extend(second_rows)
            candidate_lambda, candidate_losses = _select_shrinkage(residual, shared_rbf25_oof, fidelity_oof, grid)
            control_lambda, control_losses = _select_shrinkage(residual, shared_rbf25_oof, rbf50_oof, grid)
            selection_audit.append({"outer_fold": outer_fold, "seed_index": seed, "grid": ";".join(f"{value:.2f}" for value in grid), "candidate_losses": ";".join(f"{value:.16g}" for value in candidate_losses), "control_losses": ";".join(f"{value:.16g}" for value in control_losses), "candidate_lambda": candidate_lambda, "control_lambda": control_lambda, "selection_source": "outer_training_inner_oof_only", "validation_outcomes_used": 0})

            raw_train = np.asarray(context.compressed_train[8], dtype=float)
            raw_validation = np.asarray(context.compressed_validation[8], dtype=float)
            train_input = np.column_stack((raw_train, crossfit_baseline))
            validation_input = np.column_stack((raw_validation, c06_standardized_validation))
            projection = TaskAlignedProjection(n_components=8).fit(train_input, residual)
            aligned_train = projection.transform(train_input)
            aligned_validation = projection.transform(validation_input)
            first_stage = _fit_rbf_pair(aligned_train, residual, context.row_ids, "D048-q08-first", outer_fold, seed, 1.0, 256)
            first_validation = _predict_rbf_pair(first_stage, aligned_validation)[0.25]
            second_fidelity = _fit_fidelity(aligned_train, common_target, context.row_ids, "D048-q08-second", outer_fold, seed, 8, 1, 1.0, True, 1.0, 256)
            fidelity_validation = _predict_fidelity(second_fidelity, aligned_validation)
            second_rbf = _fit_rbf_pair(aligned_train, common_target, context.row_ids, "D048-q08-second", outer_fold, seed, 1.0, 256)
            rbf50_validation = _predict_rbf_pair(second_rbf, aligned_validation)[0.50]
            candidate_prediction = context.target_standardizer.inverse(c06_standardized_validation + candidate_lambda * (first_validation + fidelity_validation))
            control_prediction = context.target_standardizer.inverse(c06_standardized_validation + control_lambda * (first_validation + rbf50_validation))
            channel_audit.append({"outer_fold": outer_fold, "seed_index": seed, "q": 8, "common_target_l2": float(np.linalg.norm(common_target)), "first_stage_rbf25_l2": float(np.linalg.norm(first_validation)), "second_stage_fidelity_l2": float(np.linalg.norm(fidelity_validation)), "second_stage_rbf50_l2": float(np.linalg.norm(rbf50_validation)), "candidate_lambda": candidate_lambda, "control_lambda": control_lambda, "validation_outcomes_used": 0, "stage_order": "shared_q8_rbf25_then_nested_shrinkage_e2", "channel_source": "inner_oof_selection_then_outer_refit"})
            for model_id, prediction in (("NSORFRK-08", candidate_prediction), ("NSO-TWO-RBF-08", control_prediction)):
                _append_prediction(prediction_store, model_id, seed, prediction, probability, feasible, observed, decision_ids)
                fold_metrics.append({"model_id": model_id, "config_id": model_id, "outer_fold": outer_fold, "seed_index": seed, **_score(decision_ids, observed, feasible, prediction, probability, scale)})

    per_seed: list[dict[str, Any]] = []
    for (model_id, seed), values in sorted(prediction_store.items()):
        per_seed.append({"model_id": model_id, "seed_index": seed, **_score(values["decision_ids"], np.concatenate(values["observed"]), np.concatenate(values["labels"]), np.concatenate(values["cost"]), np.concatenate(values["probability"]), scale)})
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

    primary_id = "NSORFRK-08"
    control_id = "NSO-TWO-RBF-08"
    c06_nrmse = metric("C06", "nrmse")
    primary_nrmse = metric(primary_id, "nrmse")
    control_nrmse = metric(control_id, "nrmse")
    if c06_nrmse.size != 20 or primary_nrmse.size != 20 or control_nrmse.size != 20:
        raise RuntimeError("D048 paired seed endpoint is incomplete")
    interval = paired_bootstrap_mean_interval(primary_nrmse - c06_nrmse, confidence_level=0.95, replicates=10000, seed=48048)
    primary_summary = next(row for row in summary if row["model_id"] == primary_id)
    c06_summary = next(row for row in summary if row["model_id"] == "C06")
    control_summary = next(row for row in summary if row["model_id"] == control_id)
    checks = {"five_percent_nrmse_improvement": primary_summary["mean_nrmse"] <= 0.95 * c06_summary["mean_nrmse"], "paired_upper_bound_below_zero": interval.upper < 0.0, "regret_not_worse": primary_summary["mean_mean_regret_m_s"] <= c06_summary["mean_mean_regret_m_s"], "infeasible_selection_not_worse": primary_summary["mean_infeasible_selection_rate"] <= c06_summary["mean_infeasible_selection_rate"], "beats_classical_orthogonalized_control_by_five_percent": primary_summary["mean_nrmse"] <= 0.95 * control_summary["mean_nrmse"]}
    result = {"schema_version": "0.1.0", "decision_id": "D048", "protocol_id": "P016", "status": "complete_scientifically_superior" if all(checks.values()) else "complete_valid_negative", "source_commit": source_commit, "development_audit": audit, "development_rows_read": len(records), "calibration_rows_read": 0, "final_test_rows_read": 0, "hardware_jobs_submitted": 0, "gate6_runs": 0, "primary_model": primary_id, "primary_summary": primary_summary, "c06_summary": c06_summary, "classical_orthogonalized_summary": control_summary, "decision_checks": checks, "paired_nrmse_interval": {"estimate": interval.estimate, "lower": interval.lower, "upper": interval.upper, "confidence_level": interval.confidence_level}, "inner_audit_rows": len(inner_audit), "shared_stage_audit_rows": len(shared_stage_audit), "orthogonal_audit_rows": len(orthogonal_audit), "channel_audit_rows": len(channel_audit), "selection_audit_rows": len(selection_audit), "q": 8, "shrinkage_grid": list(grid), "tie_rule": "smallest grid value", "stage_order": "shared q8 RBF-0.25 fitted to e; common e2=e-r25_q8_OOF; q8 second-stage channel; nested lambda selection", "runtime": {"wall_clock_seconds": time.perf_counter() - started, "cpu_seconds": time.process_time() - cpu_started, "peak_working_set_gib": process_memory_observation().peak_bytes / 1024**3, "free_disk_gib": shutil.disk_usage(ROOT).free / 1024**3, "free_disk_preflight_gib": free_disk}, "claim_boundary": config["reporting"]["claim_boundary"], "result_files": ["inner_fold_audit.csv", "shared_stage_audit.csv", "orthogonal_audit.csv", "channel_audit.csv", "selection_audit.csv", "fold_seed_metrics.csv", "per_seed_metrics.csv", "summary.csv", "paired_comparison.csv"]}
    _write_csv(output_root / "inner_fold_audit.csv", inner_audit)
    _write_csv(output_root / "shared_stage_audit.csv", shared_stage_audit)
    _write_csv(output_root / "orthogonal_audit.csv", orthogonal_audit)
    _write_csv(output_root / "channel_audit.csv", channel_audit)
    _write_csv(output_root / "selection_audit.csv", selection_audit)
    _write_csv(output_root / "fold_seed_metrics.csv", fold_metrics)
    _write_csv(output_root / "per_seed_metrics.csv", per_seed)
    _write_csv(output_root / "summary.csv", summary)
    _write_csv(output_root / "paired_comparison.csv", [{"comparison": f"{primary_id}_minus_C06_nrmse", "seed_count": 20, "mean_difference": interval.estimate, "lower_95": interval.lower, "upper_95": interval.upper}, {"comparison": f"{primary_id}_minus_{control_id}_mean_nrmse", "seed_count": 20, "mean_difference": primary_summary["mean_nrmse"] - control_summary["mean_nrmse"]}])
    _atomic_json(result_path, result)
    _atomic_json(output_root / "campaign_summary.json", result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return result


if __name__ == "__main__":
    run()
