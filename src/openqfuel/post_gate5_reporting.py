"""Source-bound reporting for the D011 development-only P001 campaign."""

from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

from .gate4 import sha256_file
from .gate5 import (
    audit_development_records,
    load_development_records,
    validate_development_output_path,
)
from .phase1_analysis import paired_bootstrap_mean_interval
from .post_gate5 import validate_future_research_discussion_row
from .post_gate5_campaign import (
    TRACK_IDS,
    committed_yaml,
    stable_seed,
    verify_d011_authority,
)


REGIME_DIMENSIONS = (
    "fidelity",
    "uncertainty_family",
    "base_trajectory_family",
    "boundary_or_tail",
    "reference_feasible_status",
)


def _atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def _write_csv(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"D011 reporting table cannot be empty: {path.name}")
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


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"D011 JSON output must be an object: {path}")
    return payload


def _validate_zero_locks(payload: Mapping[str, Any], label: str) -> None:
    for field in ("calibration_rows_read", "final_test_rows_read"):
        if int(payload.get(field, -1)) != 0:
            raise PermissionError(f"D011 {label} violates {field}")


def _flatten_tuning(
    checkpoint_root: Path, config: Mapping[str, Any], source_commit: str
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for rung in config["campaign"]["tuning_rungs"]:
        samples = int(rung["development_samples"])
        rung_root = checkpoint_root / "tuning" / f"rung_{samples:04d}"
        for track in TRACK_IDS:
            path = rung_root / f"{track}_summaries.json"
            if not path.is_file():
                continue
            payload = _read_json(path)
            if payload.get("source_commit") != source_commit:
                raise PermissionError("D011 tuning summary source mismatch")
            for category, key in (
                ("projected", "summaries"),
                ("A02", "a02_summaries"),
                ("control", "control_summaries"),
            ):
                for row in payload.get(key, []):
                    rows.append(
                        {
                            "rung_samples": samples,
                            "track_id": track,
                            "category": category,
                            **row,
                        }
                    )
    return rows


def _with_category(
    rows: Sequence[Mapping[str, Any]], category: str
) -> list[dict[str, Any]]:
    return [{"category": category, **row} for row in rows]


def _selected_rows(selected: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [
        *_with_category(selected.get("summaries", []), "projected"),
        *_with_category(selected.get("a02_summaries", []), "A02"),
    ]


def _diagnostic_rows(selected: Mapping[str, Any]) -> list[dict[str, Any]]:
    fields = (
        "gamma",
        "clipped_eigenvalues",
        "minimum_eigenvalue_before_clip",
        "maximum_negative_eigenvalue",
        "off_diagonal_mean",
        "off_diagonal_std",
        "off_diagonal_q05",
        "off_diagonal_q95",
        "effective_rank",
        "regularized_condition_number",
        "kernel_target_alignment_q01b",
        "kernel_target_alignment_fqk",
    )
    rows: list[dict[str, Any]] = []
    for row in _selected_rows(selected):
        rows.append(
            {
                "track_id": row["track_id"],
                "category": row["category"],
                "projection_id": row["projection_id"],
                "seed_index": row["seed_index"],
                "qubits": row["qubits"],
                "layers": row["layers"],
                "entangle": row["entangle"],
                "eligible": row["eligible"],
                **{field: row.get(field) for field in fields},
            }
        )
    return rows


def _regime_labels(
    records: Sequence[Mapping[str, Any]], indices: np.ndarray
) -> dict[str, np.ndarray]:
    decision_ids = np.asarray(
        [str(records[index]["decision_set_id"]) for index in indices],
        dtype=object,
    )
    feasibility = np.asarray(
        [
            int(records[index]["outcomes"]["independently_propagated_feasible"])
            for index in indices
        ],
        dtype=int,
    )
    reference_feasible = {
        decision_id: bool(np.any(feasibility[decision_ids == decision_id]))
        for decision_id in set(decision_ids.tolist())
    }
    return {
        "fidelity": np.asarray(
            [str(records[index]["fidelity"]) for index in indices], dtype=object
        ),
        "uncertainty_family": np.asarray(
            [str(records[index]["inputs"]["uncertainty_family"]) for index in indices],
            dtype=object,
        ),
        "base_trajectory_family": np.asarray(
            [str(records[index]["base_trajectory"])[0] for index in indices],
            dtype=object,
        ),
        "boundary_or_tail": np.asarray(
            [
                str(bool(records[index]["boundary_or_tail"])).lower()
                for index in indices
            ],
            dtype=object,
        ),
        "reference_feasible_status": np.asarray(
            [
                "reference_feasible"
                if reference_feasible[str(records[index]["decision_set_id"])]
                else "no_reference_feasible"
                for index in indices
            ],
            dtype=object,
        ),
    }


def _regime_error_components(
    records: Sequence[Mapping[str, Any]],
    indices: np.ndarray,
    predictions: np.ndarray,
    scale: float,
    fold_id: str,
) -> list[dict[str, Any]]:
    truth = np.asarray(
        [
            float(records[index]["outcomes"]["robust_total_correction_delta_v_m_s"])
            for index in indices
        ],
        dtype=float,
    )
    estimate = np.asarray(predictions, dtype=float)
    if estimate.shape != truth.shape or not np.all(np.isfinite(estimate)):
        raise ValueError("D011 regime predictions are invalid")
    squared = (estimate - truth) ** 2
    rows: list[dict[str, Any]] = []
    for dimension, values in _regime_labels(records, indices).items():
        for value in sorted(set(values.tolist())):
            selected = values == value
            count = int(np.sum(selected))
            error_sum = float(np.sum(squared[selected]))
            rows.append(
                {
                    "fold_id": fold_id,
                    "dimension": dimension,
                    "value": value,
                    "rows": count,
                    "squared_error_sum": error_sum,
                    "nrmse": math.sqrt(error_sum / count) / scale,
                }
            )
    return rows


def _selected_regime_components(
    checkpoint_root: Path,
    selected: Mapping[str, Any],
    records: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    projection_id = selected.get("selected_projection_ids", {}).get("Q01b")
    if projection_id is None:
        return []
    q_rows = {
        int(row["seed_index"]): row
        for row in selected.get("summaries", [])
        if row["track_id"] == "Q01b" and bool(row["eligible"])
    }
    if not q_rows:
        return []
    qubits = int(next(iter(q_rows.values()))["qubits"])
    a02_seeds = {
        int(row["seed_index"])
        for row in selected.get("a02_summaries", [])
        if row["track_id"] == "Q01b" and bool(row["eligible"])
    }
    required_control_ids = {
        f"A01-T04-q{qubits}",
        f"C05-T17-q{qubits}",
    }
    control_seeds = {
        control_id: {
            int(row["seed_index"])
            for row in selected.get("control_summaries", [])
            if row["track_id"] == "Q01b"
            and row["control_id"] == control_id
            and bool(row["eligible"])
        }
        for control_id in required_control_ids
    }
    expected_seeds = set(range(1, 21))
    if (
        set(q_rows) != expected_seeds
        or a02_seeds != expected_seeds
        or any(seeds != expected_seeds for seeds in control_seeds.values())
    ):
        return []
    labels = {
        "Q01b": ("projection", "q_cost"),
        "A02": ("projection", "a02_cost"),
        "A01": ("control", f"cost__A01-T04-q{qubits}"),
        "compressed_C05": ("control", f"cost__C05-T17-q{qubits}"),
    }
    rows: list[dict[str, Any]] = []
    for seed_index, q_summary in sorted(q_rows.items()):
        scale = float(q_summary["pooled_oof_rmse"]) / float(
            q_summary["pooled_oof_nrmse"]
        )
        for fold_id in ("CV01", "CV02", "CV03", "CV04", "CV05"):
            fold_root = (
                checkpoint_root / "selected" / f"seed_{seed_index:02d}" / fold_id
            )
            projection_path = fold_root / f"{projection_id}.npz"
            control_path = fold_root / "controls.npz"
            with np.load(projection_path, allow_pickle=False) as projection:
                indices = np.asarray(projection["validation_indices"], dtype=int)
                projection_arrays = {
                    key: np.asarray(projection[key], dtype=float)
                    for key in ("q_cost", "a02_cost")
                }
            with np.load(control_path, allow_pickle=False) as controls:
                control_indices = np.asarray(controls["validation_indices"], dtype=int)
                if not np.array_equal(indices, control_indices):
                    raise PermissionError(
                        "D011 regime control rows differ from projected rows"
                    )
                control_arrays = {
                    key: np.asarray(controls[key], dtype=float)
                    for _, (kind, key) in labels.items()
                    if kind == "control"
                }
            for model_id, (kind, key) in labels.items():
                values = (
                    projection_arrays[key]
                    if kind == "projection"
                    else control_arrays[key]
                )
                for row in _regime_error_components(
                    records, indices, values, scale, fold_id
                ):
                    rows.append(
                        {
                            "seed_index": seed_index,
                            "model_id": model_id,
                            **row,
                        }
                    )
    return rows


def evaluate_q01b_regimes(
    components: Sequence[Mapping[str, Any]],
    *,
    bootstrap_replicates: int,
    confidence_level: float,
) -> list[dict[str, Any]]:
    by_cell: dict[tuple[str, str, int, str], list[Mapping[str, Any]]] = defaultdict(
        list
    )
    for row in components:
        by_cell[
            (
                str(row["dimension"]),
                str(row["value"]),
                int(row["seed_index"]),
                str(row["model_id"]),
            )
        ].append(row)
    pooled: dict[tuple[str, str, int, str], float] = {}
    complete: dict[tuple[str, str, int, str], bool] = {}
    for key, rows in by_cell.items():
        folds = {str(row["fold_id"]) for row in rows}
        complete[key] = folds == {"CV01", "CV02", "CV03", "CV04", "CV05"}
        total_rows = sum(int(row["rows"]) for row in rows)
        scale_numerators = [
            math.sqrt(float(row["squared_error_sum"]) / int(row["rows"]))
            / float(row["nrmse"])
            for row in rows
            if float(row["nrmse"]) > 0.0
        ]
        if not scale_numerators:
            raise ValueError("D011 regime scale cannot be reconstructed")
        scale = float(np.mean(scale_numerators))
        pooled[key] = (
            math.sqrt(sum(float(row["squared_error_sum"]) for row in rows) / total_rows)
            / scale
        )

    cells = sorted({(key[0], key[1]) for key in pooled})
    results: list[dict[str, Any]] = []
    for dimension, value in cells:
        seeds = range(1, 21)
        models = ("Q01b", "A01", "A02", "compressed_C05")
        all_complete = all(
            complete.get((dimension, value, seed, model), False)
            for seed in seeds
            for model in models
        )
        row: dict[str, Any] = {
            "dimension": dimension,
            "value": value,
            "all_five_folds_and_twenty_seeds": all_complete,
            "qualified_dequantization_regime": False,
        }
        if not all_complete:
            results.append(row)
            continue
        arrays = {
            model: np.asarray(
                [pooled[(dimension, value, seed, model)] for seed in seeds],
                dtype=float,
            )
            for model in models
        }
        row["q01b_mean_nrmse"] = float(np.mean(arrays["Q01b"]))
        qualified = True
        for comparator in ("A01", "A02", "compressed_C05"):
            interval = paired_bootstrap_mean_interval(
                arrays["Q01b"] - arrays[comparator],
                confidence_level=confidence_level,
                replicates=bootstrap_replicates,
                seed=stable_seed(
                    "P001", "D011", "regime", dimension, value, comparator
                ),
            )
            prefix = comparator.lower()
            row[f"{prefix}_mean_nrmse"] = float(np.mean(arrays[comparator]))
            row[f"q01b_minus_{prefix}_ci_lower"] = interval.lower
            row[f"q01b_minus_{prefix}_ci_upper"] = interval.upper
            qualified &= interval.upper < 0.0
        row["qualified_dequantization_regime"] = bool(qualified)
        results.append(row)
    return results


def _eligible_seed_rows(
    rows: Sequence[Mapping[str, Any]], track_id: str
) -> list[Mapping[str, Any]]:
    selected = [
        row
        for row in rows
        if row["track_id"] == track_id and bool(row.get("eligible", False))
    ]
    return sorted(selected, key=lambda row: int(row["seed_index"]))


def _mean(row_set: Sequence[Mapping[str, Any]], field: str) -> float:
    return float(np.mean([float(row[field]) for row in row_set]))


def evaluate_exploratory_signal(
    selected: Mapping[str, Any],
    regimes: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    decisions: dict[str, Any] = {}
    projected = selected.get("summaries", [])
    controls = selected.get("control_summaries", [])
    a02 = selected.get("a02_summaries", [])

    q01 = _eligible_seed_rows(projected, "Q01b")
    c06 = [
        row
        for row in _eligible_seed_rows(controls, "Q01b")
        if row["control_id"] == "C06-T17"
    ]
    q01_complete = (
        len(q01) == 20
        and len(c06) == 20
        and {int(row["seed_index"]) for row in q01} == set(range(1, 21))
        and {int(row["seed_index"]) for row in c06} == set(range(1, 21))
        and all(int(row["fold_count"]) == 5 for row in [*q01, *c06])
    )
    if q01_complete:
        q_by_seed = {int(row["seed_index"]): row for row in q01}
        c_by_seed = {int(row["seed_index"]): row for row in c06}
        relative = np.asarray(
            [
                (
                    float(q_by_seed[seed]["pooled_oof_nrmse"])
                    - float(c_by_seed[seed]["pooled_oof_nrmse"])
                )
                / float(c_by_seed[seed]["pooled_oof_nrmse"])
                for seed in range(1, 21)
            ]
        )
        mean_relative_gap = float(np.mean(relative))
        qualified_regimes = sum(
            bool(row["qualified_dequantization_regime"]) for row in regimes
        )
        q01_promising = mean_relative_gap <= 0.05 and qualified_regimes > 0
        decisions["Q01b"] = {
            "status": (
                "promising_for_new_protocol"
                if q01_promising
                else "valid_exploratory_negative"
            ),
            "promising": q01_promising,
            "all_five_folds_and_twenty_seeds": True,
            "selected_projection_id": q01[0]["projection_id"],
            "mean_pooled_oof_nrmse": _mean(q01, "pooled_oof_nrmse"),
            "c06_mean_pooled_oof_nrmse": _mean(c06, "pooled_oof_nrmse"),
            "mean_relative_nrmse_gap_vs_c06": mean_relative_gap,
            "within_five_percent_of_c06": mean_relative_gap <= 0.05,
            "qualified_dequantization_regimes": qualified_regimes,
        }
    else:
        decisions["Q01b"] = {
            "status": "not_reached_under_frozen_eligibility",
            "promising": False,
            "all_five_folds_and_twenty_seeds": False,
        }

    fqk = _eligible_seed_rows(projected, "FQK")
    fqk_controls = _eligible_seed_rows(controls, "FQK")
    fqk_a02 = _eligible_seed_rows(a02, "FQK")
    by_control: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in fqk_controls:
        by_control[str(row["control_id"])].append(row)
    if fqk_a02:
        by_control["A02"].extend(fqk_a02)
    complete_controls = {
        name: rows
        for name, rows in by_control.items()
        if len(rows) == 20
        and {int(row["seed_index"]) for row in rows} == set(range(1, 21))
        and all(int(row["fold_count"]) == 5 for row in rows)
    }
    fqk_complete = (
        len(fqk) == 20
        and {int(row["seed_index"]) for row in fqk} == set(range(1, 21))
        and all(int(row["fold_count"]) == 5 for row in fqk)
        and len(complete_controls) == 9
    )
    if fqk_complete:
        strongest_name, strongest = min(
            complete_controls.items(),
            key=lambda item: (
                _mean(item[1], "pooled_oof_brier"),
                -_mean(item[1], "recall_at_0_5"),
                -_mean(item[1], "auroc"),
                str(item[0]),
            ),
        )
        q_brier = _mean(fqk, "pooled_oof_brier")
        c_brier = _mean(strongest, "pooled_oof_brier")
        brier_condition = (
            q_brier == 0.0 if c_brier == 0.0 else q_brier <= 1.05 * c_brier
        )
        auroc_condition = _mean(fqk, "auroc") >= _mean(strongest, "auroc") - 0.01
        recall_condition = (
            _mean(fqk, "recall_at_0_5") >= _mean(strongest, "recall_at_0_5") - 0.02
        )
        fqk_promising = brier_condition and auroc_condition and recall_condition
        decisions["FQK"] = {
            "status": (
                "promising_for_new_protocol"
                if fqk_promising
                else "valid_exploratory_negative"
            ),
            "promising": fqk_promising,
            "all_five_folds_and_twenty_seeds": True,
            "selected_projection_id": fqk[0]["projection_id"],
            "mean_pooled_oof_brier": q_brier,
            "mean_auroc": _mean(fqk, "auroc"),
            "mean_recall_at_0_5": _mean(fqk, "recall_at_0_5"),
            "mean_precision_at_0_5": _mean(fqk, "precision_at_0_5"),
            "mean_false_negative_rate": _mean(fqk, "false_negative_rate"),
            "mean_false_positive_rate": _mean(fqk, "false_positive_rate"),
            "strongest_comparator_id": strongest_name,
            "strongest_comparator_mean_brier": c_brier,
            "strongest_comparator_mean_auroc": _mean(strongest, "auroc"),
            "strongest_comparator_mean_recall_at_0_5": _mean(
                strongest, "recall_at_0_5"
            ),
            "brier_condition": brier_condition,
            "auroc_condition": auroc_condition,
            "recall_condition": recall_condition,
        }
    else:
        decisions["FQK"] = {
            "status": "not_reached_under_frozen_eligibility",
            "promising": False,
            "all_five_folds_and_twenty_seeds": False,
            "complete_comparator_count": len(complete_controls),
        }

    return {
        "schema_version": "0.1.0",
        "decision_id": "D011",
        "protocol_id": "P001",
        "status": "complete",
        "tracks": decisions,
        "gate5_result_unchanged": True,
        "gate6_authorized": False,
        "calibration_rows_read": 0,
        "final_test_rows_read": 0,
        "claim_boundary": (
            "Development-only exploratory signal. A promising label can support "
            "a later protocol decision only and is not quantum advantage, mission "
            "performance, Gate 5 revision, or Gate 6 authority."
        ),
    }


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _append_future_discussion(
    path: Path,
    decisions: Mapping[str, Any],
    tuning: Mapping[str, Any],
) -> list[str]:
    rows = _read_csv(path)
    fields = list(rows[0])
    existing_steps = {row["step_id"] for row in rows}
    numeric_ids = [
        int(row["record_id"].split("FR")[-1])
        for row in rows
        if row["record_id"].startswith("P001-FR")
        and row["record_id"].split("FR")[-1].isdigit()
    ]
    next_id = max(numeric_ids, default=0) + 1
    added: list[str] = []
    required = [field for field in fields if field != "reporting_commit"]
    for track in TRACK_IDS:
        decision = decisions["tracks"][track]
        if decision["status"] == "promising_for_new_protocol":
            continue
        terminal = tuning.get("terminal_nonadvancement", {}).get(track)
        step_id = (
            f"D011_{track}_terminal_nonadvancement"
            if terminal is not None
            else f"D011_{track}_exploratory_result"
        )
        if step_id in existing_steps:
            continue
        if terminal is not None:
            terminal_status = "terminal_nonadvancement"
            observed = (
                f"{track} had {terminal['eligible']} eligible projections at the "
                f"{terminal['rung_samples']}-row rung, below the frozen requirement "
                f"of {terminal['required']}."
            )
            bounded = (
                "The track did not reach selected-configuration testing under the "
                "frozen eligibility rule; this is not a task-execution failure or a "
                "claim that all related QML methods fail."
            )
            improvement = (
                "A future protocol should prospectively test a broader observable "
                "set and diagnose projection degeneracy before freezing its trial "
                "budget, while retaining grouped folds and matched classical controls."
            )
        elif decision["status"] == "not_reached_under_frozen_eligibility":
            terminal_status = "metric_undefined"
            observed = (
                f"{track} reached selection but did not produce a complete eligible "
                "five-fold, 20-seed comparison under the frozen metric rules."
            )
            bounded = (
                "The preregistered exploratory signal is unavailable for this track; "
                "missing evidence is not treated as zero or as a completed model failure."
            )
            improvement = (
                "A future protocol should prospectively audit class coverage and kernel "
                "geometry at each planned fold and seed before fixing its inferential "
                "budget, without reusing P001 outcomes or changing this result."
            )
        else:
            terminal_status = "scientific_negative"
            if track == "Q01b":
                observed = (
                    "Q01b completed the frozen selected-seed campaign but did not "
                    f"meet the promising rule: mean relative NRMSE gap versus C06 = "
                    f"{decision.get('mean_relative_nrmse_gap_vs_c06')!r}, qualified "
                    f"dequantization regimes = {decision.get('qualified_dequantization_regimes')!r}."
                )
                improvement = (
                    "A future protocol should prospectively compare richer local "
                    "observable projections or task-informed encodings selected without "
                    "outcome reuse, while preserving A02, random-feature, compressed-MLP, "
                    "and physics-residual controls."
                )
            else:
                observed = (
                    "FQK completed the frozen selected-seed campaign but did not meet "
                    f"all promising conditions: Brier={decision.get('brier_condition')!r}, "
                    f"AUROC={decision.get('auroc_condition')!r}, "
                    f"recall={decision.get('recall_condition')!r}."
                )
                improvement = (
                    "A future protocol should prospectively test class-sensitive kernel "
                    "training and a separately calibrated safety threshold, with the "
                    "same grouped split, Brier/AUROC/recall endpoints, and matched controls."
                )
            bounded = (
                "This is a valid development-only negative for the exact P001 feature "
                "map and frozen benchmark, not evidence that every projected quantum "
                "kernel or feasibility-learning approach fails."
            )
        row = {
            "record_id": f"P001-FR{next_id:03d}",
            "recorded_date": "2026-07-13",
            "track_id": track,
            "step_id": step_id,
            "terminal_status": terminal_status,
            "evidence_paths": (
                "data/processed/reporting/post_gate5_p001/"
                "exploratory_decision.json;data/processed/reporting/"
                "post_gate5_p001/selected_summary.csv"
            ),
            "observed_finding": observed,
            "bounded_interpretation": bounded,
            "future_research_improvement": improvement,
            "new_protocol_required": "true",
            "active_pipeline_change_authorized": "false",
            "post_outcome_retry_authorized": "false",
            "reporting_commit": "pending_result_commit",
        }
        validate_future_research_discussion_row(row, required)
        rows.append(row)
        added.append(row["record_id"])
        existing_steps.add(step_id)
        next_id += 1
    temporary = path.with_suffix(".csv.tmp")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)
    return added


def write_d011_report(root: Path) -> dict[str, Any]:
    """Validate checkpoints and write compact paper/report evidence."""

    config, source_commit, _ = verify_d011_authority(
        root, action="reporting", require_fold_shape_pass=True
    )
    checkpoint_root = validate_development_output_path(
        root, root / str(config["campaign"]["checkpoint_root"])
    )
    output_root = validate_development_output_path(
        root, root / str(config["campaign"]["output_root"])
    )
    campaign = _read_json(checkpoint_root / "campaign_index.json")
    if (
        campaign.get("status") != "complete"
        or campaign.get("source_commit") != source_commit
    ):
        raise PermissionError("D011 campaign index is not source-valid")
    _validate_zero_locks(campaign, "campaign")
    if int(campaign.get("development_rows_read", -1)) != 39000:
        raise PermissionError(
            "D011 campaign did not read exactly 39,000 development rows"
        )

    phase_config = committed_yaml(
        root, source_commit, str(config["source_binding"]["phase1_config"])
    )
    records, manifest = load_development_records(root, phase_config)
    audit = audit_development_records(records, manifest, phase_config)
    if audit != campaign["development_audit"]:
        raise PermissionError("D011 reporting data audit differs from campaign")

    tuning = campaign["tuning"]
    selected = campaign["selected"]
    sensitivity = campaign["sensitivity"]
    for label, payload in (
        ("tuning", tuning),
        ("selected", selected),
        ("sensitivity", sensitivity),
    ):
        _validate_zero_locks(payload, label)
        if payload.get("source_commit") != source_commit:
            raise PermissionError(f"D011 {label} source mismatch")

    output_root.mkdir(parents=True, exist_ok=True)
    tuning_rows = _flatten_tuning(checkpoint_root, config, source_commit)
    selected_rows = _selected_rows(selected)
    control_rows = _with_category(selected.get("control_summaries", []), "control")
    sensitivity_rows = list(sensitivity.get("summaries", []))
    diagnostic_rows = _diagnostic_rows(selected)
    _write_csv(output_root / "tuning_summary.csv", tuning_rows)
    if selected_rows:
        _write_csv(output_root / "selected_summary.csv", selected_rows)
    if control_rows:
        _write_csv(output_root / "control_summary.csv", control_rows)
    if sensitivity_rows:
        _write_csv(output_root / "sensitivity_summary.csv", sensitivity_rows)
    if diagnostic_rows:
        _write_csv(output_root / "kernel_diagnostics.csv", diagnostic_rows)

    components = _selected_regime_components(checkpoint_root, selected, records)
    regimes = (
        evaluate_q01b_regimes(
            components,
            bootstrap_replicates=int(config["endpoints"]["bootstrap_replicates"]),
            confidence_level=float(config["endpoints"]["confidence_level"]),
        )
        if components
        else []
    )
    if regimes:
        _write_csv(output_root / "q01b_regime_comparisons.csv", regimes)
    decision = evaluate_exploratory_signal(selected, regimes)
    decision["source_commit"] = source_commit
    _atomic_json(output_root / "exploratory_decision.json", decision)

    summary = {
        "schema_version": "0.1.0",
        "decision_id": "D011",
        "protocol_id": "P001",
        "status": "complete",
        "source_commit": source_commit,
        "development_audit": audit,
        "selected_projection_ids": tuning["selected_projection_ids"],
        "terminal_nonadvancement": tuning["terminal_nonadvancement"],
        "track_decisions": decision["tracks"],
        "calibration_rows_read": 0,
        "final_test_rows_read": 0,
        "hardware_jobs_submitted": 0,
        "gate6_runs": 0,
        "claim_boundary": decision["claim_boundary"],
    }
    _atomic_json(output_root / "campaign_summary.json", summary)
    added_records = _append_future_discussion(
        root / str(config["failure_policy"]["future_discussion_register"]),
        decision,
        tuning,
    )
    summary["future_discussion_records_added"] = added_records
    _atomic_json(output_root / "campaign_summary.json", summary)

    evidence_files = sorted(
        path
        for path in output_root.iterdir()
        if path.is_file() and path.name != "evidence_manifest.json"
    )
    manifest_payload = {
        "schema_version": "0.1.0",
        "decision_id": "D011",
        "protocol_id": "P001",
        "status": "complete",
        "source_commit": source_commit,
        "files": {
            path.name: {
                "sha256": sha256_file(path),
                "bytes": path.stat().st_size,
            }
            for path in evidence_files
        },
        "campaign_index_sha256": sha256_file(checkpoint_root / "campaign_index.json"),
        "future_discussion_register_sha256": sha256_file(
            root / str(config["failure_policy"]["future_discussion_register"])
        ),
        "calibration_rows_read": 0,
        "final_test_rows_read": 0,
    }
    _atomic_json(output_root / "evidence_manifest.json", manifest_payload)
    return summary
