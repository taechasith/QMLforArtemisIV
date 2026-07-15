"""Run the D047 orthogonalized multi-scale fidelity stack campaign."""

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
from openqfuel.gate5 import audit_development_records, deterministic_group_folds, fold_manifest_rows, load_development_records  # noqa: E402
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
except ModuleNotFoundError as error:
    if error.name != "scripts":
        raise
    from run_post_gate5_d036_tapqk import _atomic_json, _score, _source_commit, _write_csv  # type: ignore[no-redef] # noqa: E402
    from run_post_gate5_d038_gfrk import _fit_fidelity, _predict_fidelity  # type: ignore[no-redef] # noqa: E402
    from run_post_gate5_d039_ecgfrk import _inner_cross_fitted_c06  # type: ignore[no-redef] # noqa: E402
    from run_post_gate5_d041_hefrk import _fit_rbf_pair, _predict_rbf_pair  # type: ignore[no-redef] # noqa: E402
    from run_post_gate5_d043_sfrk import _inner_channel_predictions  # type: ignore[no-redef] # noqa: E402
    from run_post_gate5_d046_orfrk import _orthogonalized_target  # type: ignore[no-redef] # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs/post_gate5_d047_omfrk.yaml"
PHASE_CONFIG_PATH = ROOT / "configs/phase1_benchmark.yaml"


def _fit_linear_stack(features: np.ndarray, target: np.ndarray, alpha: float) -> np.ndarray:
    values = np.asarray(features, dtype=float)
    labels = np.asarray(target, dtype=float)
    if values.ndim != 2 or values.shape[1] != 4 or values.shape[0] != labels.size:
        raise ValueError("D047 stack feature shape is invalid")
    if not np.all(np.isfinite(values)) or not np.all(np.isfinite(labels)):
        raise ValueError("D047 stack values are not finite")
    regularizer = np.diag([0.0, alpha, alpha, alpha])
    coefficients = np.linalg.solve(values.T @ values + regularizer, values.T @ labels)
    if not np.all(np.isfinite(coefficients)):
        raise RuntimeError("D047 stack coefficients are not finite")
    return coefficients


def _inner_second_stage_channels(
    records: Sequence[Mapping[str, Any]],
    context: Any,
    outer_fold: str,
    seed: int,
    q: int,
    residual: np.ndarray,
    common_target: np.ndarray,
    crossfit_baseline: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, list[dict[str, Any]]]:
    """Generate q-specific second-stage OOF channels on one common target."""

    groups = [str(records[index]["group_id"]) for index in context.train_indices]
    unique_groups = sorted(set(groups))
    assignments = deterministic_group_folds(unique_groups, master_seed=47047, fold_count=4, strata={group: ("all", "all") for group in unique_groups})
    raw = np.asarray(context.compressed_train[q], dtype=float)
    fidelity_oof = np.empty(raw.shape[0], dtype=float)
    rbf50_oof = np.empty(raw.shape[0], dtype=float)
    audit_rows: list[dict[str, Any]] = []
    for inner_fold in range(1, 5):
        hold_positions = np.asarray([position for position, group in enumerate(groups) if assignments[group] == inner_fold], dtype=int)
        fit_positions = np.asarray([position for position, group in enumerate(groups) if assignments[group] != inner_fold], dtype=int)
        if not hold_positions.size or not fit_positions.size:
            raise RuntimeError("D047 inner grouped fold is empty")
        fit_groups = sorted({groups[position] for position in fit_positions})
        hold_groups = sorted({groups[position] for position in hold_positions})
        if set(fit_groups) & set(hold_groups):
            raise RuntimeError("D047 inner channel fit/holdout groups overlap")
        fit_input = np.column_stack((raw[fit_positions], crossfit_baseline[fit_positions]))
        hold_input = np.column_stack((raw[hold_positions], crossfit_baseline[hold_positions]))
        projection = TaskAlignedProjection(n_components=q).fit(fit_input, residual[fit_positions])
        aligned_fit = projection.transform(fit_input)
        aligned_hold = projection.transform(hold_input)
        row_ids = [str(context.row_ids[position]) for position in fit_positions]
        channel_id = f"D047-q{q:02d}-I{inner_fold:02d}"
        fidelity = _fit_fidelity(aligned_fit, common_target[fit_positions], row_ids, channel_id, outer_fold, seed, q, 1, 1.0, True, 1.0, 256)
        fidelity_oof[hold_positions] = _predict_fidelity(fidelity, aligned_hold)
        rbf_pair = _fit_rbf_pair(aligned_fit, common_target[fit_positions], row_ids, channel_id, outer_fold, seed, 1.0, 256)
        rbf50_oof[hold_positions] = _predict_rbf_pair(rbf_pair, aligned_hold)[0.50]
        audit_rows.append({"outer_fold": outer_fold, "seed_index": seed, "q": q, "inner_fold": inner_fold, "fit_rows": int(fit_positions.size), "holdout_rows": int(hold_positions.size), "fit_groups": ";".join(fit_groups), "holdout_groups": ";".join(hold_groups), "group_intersection_count": 0, "channel_source": "common_q8_rbf25_oof_orthogonalized_target", "validation_outcomes_used": 0})
    if not np.all(np.isfinite(fidelity_oof)) or not np.all(np.isfinite(rbf50_oof)):
        raise RuntimeError("D047 inner second-stage OOF predictions are incomplete")
    return fidelity_oof, rbf50_oof, audit_rows


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
    if config.get("decision_id") != "D047" or config.get("protocol_id") != "P015":
        raise RuntimeError("D047 config identity is invalid")
    if not bool(config["authority"]["research_data_fitting_authorized"]):
        raise RuntimeError("D047 fitting is not authorized")
    d046_result = json.loads((ROOT / "data/processed/reporting/post_gate5_d046_orfrk/campaign_result.json").read_text(encoding="utf-8"))
    if d046_result.get("status") != "complete_valid_negative":
        raise RuntimeError("D047 requires an integrity-valid D046 negative")
    free_disk = shutil.disk_usage(ROOT).free / 1024**3
    floor = float(config["resources"]["free_disk_floor_gib"])
    if free_disk < floor:
        raise RuntimeError(f"D047 free disk preflight is below {floor:.1f} GiB: {free_disk:.3f} GiB")
    output_root = ROOT / str(config["reporting"]["result_root"])
    result_path = output_root / "campaign_result.json"
    if result_path.is_file():
        result = json.loads(result_path.read_text(encoding="utf-8"))
        if result.get("source_commit") != source_commit:
            raise RuntimeError("D047 result belongs to another source commit")
        return result

    records, manifest = load_development_records(ROOT, phase_config)
    audit = audit_development_records(records, manifest, phase_config)
    if audit["rows"] != 39000 or audit["unique_scenarios"] != 39000:
        raise RuntimeError("D047 development grain does not match the frozen audit")
    fold_ids = sorted({str(row["fold_id"]) for row in fold_manifest_rows(phase_config, manifest)})
    if fold_ids != ["CV01", "CV02", "CV03", "CV04", "CV05"]:
        raise RuntimeError("D047 outer fold manifest is invalid")
    registry_payload = read_yaml(ROOT / "experiments/phase1_model_registry.yaml")
    registry = {str(row["trial_id"]): row for row in registry_payload["models"]}
    c06_parameters = registry["C06-T17"]["parameters"]
    targets = np.asarray([float(row["outcomes"][phase_config["targets"]["primary_regression"]]) for row in records], dtype=float)
    scale = development_target_scale(targets)
    seeds = [int(value) for value in config["locks"]["seed_indices"]]
    q_values = [4, 6, 8]
    started = time.perf_counter()
    cpu_started = time.process_time()
    fold_metrics: list[dict[str, Any]] = []
    inner_audit: list[dict[str, Any]] = []
    shared_stage_audit: list[dict[str, Any]] = []
    orthogonal_audit: list[dict[str, Any]] = []
    channel_audit: list[dict[str, Any]] = []
    stack_audit: list[dict[str, Any]] = []
    prediction_store: dict[tuple[str, int], dict[str, list[np.ndarray] | list[str]]] = {}

    for outer_fold in fold_ids:
        context = build_fold_context(records, manifest, phase_config, fold_id=outer_fold, rung_samples=1024, qubit_dimensions=q_values)
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
            raw_train_8 = np.asarray(context.compressed_train[8], dtype=float)
            raw_validation_8 = np.asarray(context.compressed_validation[8], dtype=float)
            shared_train_input = np.column_stack((raw_train_8, crossfit_baseline))
            shared_validation_input = np.column_stack((raw_validation_8, c06_standardized_validation))
            shared_projection = TaskAlignedProjection(n_components=8).fit(shared_train_input, residual)
            shared_aligned_train = shared_projection.transform(shared_train_input)
            shared_aligned_validation = shared_projection.transform(shared_validation_input)
            shared_pair = _fit_rbf_pair(shared_aligned_train, residual, context.row_ids, "D047-shared-q08", outer_fold, seed, 1.0, 256)
            shared_rbf25_validation = _predict_rbf_pair(shared_pair, shared_aligned_validation)[0.25]

            second_oof: dict[int, tuple[np.ndarray, np.ndarray]] = {}
            second_validation: dict[int, tuple[np.ndarray, np.ndarray]] = {}
            for q in q_values:
                fidelity_oof, rbf50_oof, inner_rows = _inner_second_stage_channels(records, context, outer_fold, seed, q, residual, common_target, crossfit_baseline)
                second_oof[q] = (fidelity_oof, rbf50_oof)
                orthogonal_audit.extend(inner_rows)
                raw_train = np.asarray(context.compressed_train[q], dtype=float)
                raw_validation = np.asarray(context.compressed_validation[q], dtype=float)
                train_input = np.column_stack((raw_train, crossfit_baseline))
                validation_input = np.column_stack((raw_validation, c06_standardized_validation))
                projection = TaskAlignedProjection(n_components=q).fit(train_input, residual)
                aligned_train = projection.transform(train_input)
                aligned_validation = projection.transform(validation_input)
                channel_id = f"D047-q{q:02d}"
                fidelity = _fit_fidelity(aligned_train, common_target, context.row_ids, channel_id, outer_fold, seed, q, 1, 1.0, True, 1.0, 256)
                fidelity_validation = _predict_fidelity(fidelity, aligned_validation)
                rbf_pair = _fit_rbf_pair(aligned_train, common_target, context.row_ids, channel_id, outer_fold, seed, 1.0, 256)
                rbf50_validation = _predict_rbf_pair(rbf_pair, aligned_validation)[0.50]
                second_validation[q] = (fidelity_validation, rbf50_validation)
                channel_audit.append({"outer_fold": outer_fold, "seed_index": seed, "q": q, "common_target_l2": float(np.linalg.norm(common_target)), "second_stage_fidelity_l2": float(np.linalg.norm(fidelity_validation)), "second_stage_rbf50_l2": float(np.linalg.norm(rbf50_validation)), "validation_outcomes_used": 0, "stage_order": "shared_q8_rbf25_then_common_e2_q_stack", "channel_source": "common_q8_rbf25_oof_orthogonalized_target"})

            candidate_train = np.column_stack((np.ones(common_target.size), second_oof[4][0], second_oof[6][0], second_oof[8][0]))
            control_train = np.column_stack((np.ones(common_target.size), second_oof[4][1], second_oof[6][1], second_oof[8][1]))
            candidate_coefficients = _fit_linear_stack(candidate_train, common_target, 0.001)
            control_coefficients = _fit_linear_stack(control_train, common_target, 0.001)
            candidate_validation = np.column_stack((np.ones(shared_rbf25_validation.size), second_validation[4][0], second_validation[6][0], second_validation[8][0]))
            control_validation = np.column_stack((np.ones(shared_rbf25_validation.size), second_validation[4][1], second_validation[6][1], second_validation[8][1]))
            stack_audit.append({"outer_fold": outer_fold, "seed_index": seed, "fit_rows": int(common_target.size), "candidate_feature_columns": 4, "control_feature_columns": 4, "stack_ridge": 0.001, "candidate_coefficients": ";".join(f"{value:.16g}" for value in candidate_coefficients), "control_coefficients": ";".join(f"{value:.16g}" for value in control_coefficients), "feature_order": "[1,F4(e2),F6(e2),F8(e2)] versus [1,R50_4(e2),R50_6(e2),R50_8(e2)]", "common_target_l2": float(np.linalg.norm(common_target)), "validation_outcomes_used": 0})
            candidate_delta = shared_rbf25_validation + candidate_validation @ candidate_coefficients
            control_delta = shared_rbf25_validation + control_validation @ control_coefficients
            candidate_prediction = context.target_standardizer.inverse(c06_standardized_validation + 0.10 * candidate_delta)
            control_prediction = context.target_standardizer.inverse(c06_standardized_validation + 0.10 * control_delta)
            for model_id, prediction in (("OMFRK-ALL", candidate_prediction), ("OM-TWO-RBF", control_prediction)):
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

    c06_nrmse = metric("C06", "nrmse")
    primary_nrmse = metric("OMFRK-ALL", "nrmse")
    control_nrmse = metric("OM-TWO-RBF", "nrmse")
    if c06_nrmse.size != 20 or primary_nrmse.size != 20 or control_nrmse.size != 20:
        raise RuntimeError("D047 paired seed endpoint is incomplete")
    interval = paired_bootstrap_mean_interval(primary_nrmse - c06_nrmse, confidence_level=0.95, replicates=10000, seed=47047)
    primary_summary = next(row for row in summary if row["model_id"] == "OMFRK-ALL")
    c06_summary = next(row for row in summary if row["model_id"] == "C06")
    control_summary = next(row for row in summary if row["model_id"] == "OM-TWO-RBF")
    checks = {"five_percent_nrmse_improvement": primary_summary["mean_nrmse"] <= 0.95 * c06_summary["mean_nrmse"], "paired_upper_bound_below_zero": interval.upper < 0.0, "regret_not_worse": primary_summary["mean_mean_regret_m_s"] <= c06_summary["mean_mean_regret_m_s"], "infeasible_selection_not_worse": primary_summary["mean_infeasible_selection_rate"] <= c06_summary["mean_infeasible_selection_rate"], "beats_classical_orthogonalized_stack_by_five_percent": primary_summary["mean_nrmse"] <= 0.95 * control_summary["mean_nrmse"]}
    result = {"schema_version": "0.1.0", "decision_id": "D047", "protocol_id": "P015", "status": "complete_scientifically_superior" if all(checks.values()) else "complete_valid_negative", "source_commit": source_commit, "development_audit": audit, "development_rows_read": len(records), "calibration_rows_read": 0, "final_test_rows_read": 0, "hardware_jobs_submitted": 0, "gate6_runs": 0, "primary_model": "OMFRK-ALL", "primary_summary": primary_summary, "c06_summary": c06_summary, "classical_orthogonalized_summary": control_summary, "decision_checks": checks, "paired_nrmse_interval": {"estimate": interval.estimate, "lower": interval.lower, "upper": interval.upper, "confidence_level": interval.confidence_level}, "inner_audit_rows": len(inner_audit), "shared_stage_audit_rows": len(shared_stage_audit), "orthogonal_audit_rows": len(orthogonal_audit), "channel_audit_rows": len(channel_audit), "stack_audit_rows": len(stack_audit), "q_values": q_values, "shared_first_stage_q": 8, "stage_order": "shared q8 RBF-0.25 fitted to e; common e2=e-r25_q8_OOF; q4/q6/q8 second-stage stack", "runtime": {"wall_clock_seconds": time.perf_counter() - started, "cpu_seconds": time.process_time() - cpu_started, "peak_working_set_gib": process_memory_observation().peak_bytes / 1024**3, "free_disk_gib": shutil.disk_usage(ROOT).free / 1024**3, "free_disk_preflight_gib": free_disk}, "claim_boundary": config["reporting"]["claim_boundary"], "result_files": ["inner_fold_audit.csv", "shared_stage_audit.csv", "orthogonal_audit.csv", "channel_audit.csv", "stack_audit.csv", "fold_seed_metrics.csv", "per_seed_metrics.csv", "summary.csv", "paired_comparison.csv"]}
    _write_csv(output_root / "inner_fold_audit.csv", inner_audit)
    _write_csv(output_root / "shared_stage_audit.csv", shared_stage_audit)
    _write_csv(output_root / "orthogonal_audit.csv", orthogonal_audit)
    _write_csv(output_root / "channel_audit.csv", channel_audit)
    _write_csv(output_root / "stack_audit.csv", stack_audit)
    _write_csv(output_root / "fold_seed_metrics.csv", fold_metrics)
    _write_csv(output_root / "per_seed_metrics.csv", per_seed)
    _write_csv(output_root / "summary.csv", summary)
    _write_csv(output_root / "paired_comparison.csv", [{"comparison": "OMFRK-ALL_minus_C06_nrmse", "seed_count": 20, "mean_difference": interval.estimate, "lower_95": interval.lower, "upper_95": interval.upper}, {"comparison": "OMFRK-ALL_minus_OM-TWO-RBF_mean_nrmse", "seed_count": 20, "mean_difference": primary_summary["mean_nrmse"] - control_summary["mean_nrmse"]}])
    _atomic_json(result_path, result)
    _atomic_json(output_root / "campaign_summary.json", result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return result


if __name__ == "__main__":
    run()
