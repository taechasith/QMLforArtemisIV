"""Fail-closed development workflow for the frozen Phase 1 benchmark."""

from __future__ import annotations

import csv
import functools
import hashlib
import json
import math
import subprocess
import time
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

from .gate4 import assert_no_final_payloads, read_csv, read_yaml, sha256_file
from .models import (
    build_classical_classifier,
    build_classical_regressor,
    build_qml_control_classifier,
    build_qml_control_regressor,
    build_quantum_classifier,
    build_quantum_regressor,
)
from .phase1_analysis import (
    development_target_scale,
    feasibility_constrained_regret,
    feasibility_metrics,
    regression_metrics,
)
from .preprocessing import FrozenFeaturePreprocessor, QuantumFeatureProjector
from .qml import quantum_kernel_matrix


DEVELOPMENT_SPLIT = "development"
RUNNER_ACCEPTED_STATUS = "d005_gate5_runner_accepted"
QML_FAMILIES = {
    "quantum_kernel",
    "variational_quantum_regressor",
    "hybrid_quantum_residual",
}
RESIDUAL_FAMILIES = {"physics_residual", "hybrid_quantum_residual"}
MATCHED_QUBITS = (4, 6, 8)


@dataclass(frozen=True)
class TrialSpec:
    family_id: str
    model_family: str
    trial_id: str
    trial_order: int
    parameters: dict[str, Any]


@dataclass(frozen=True)
class TargetStandardizer:
    mean: float
    scale: float

    @classmethod
    def fit(cls, values: Sequence[float]) -> "TargetStandardizer":
        array = np.asarray(values, dtype=float)
        if array.ndim != 1 or array.size < 2 or not np.all(np.isfinite(array)):
            raise ValueError("Training targets must be finite and one-dimensional")
        scale = float(np.std(array, ddof=0))
        if not math.isfinite(scale) or scale <= 0.0:
            raise ValueError("Training target scale must be positive")
        return cls(float(np.mean(array)), scale)

    def transform(self, values: Sequence[float]) -> np.ndarray:
        return (np.asarray(values, dtype=float) - self.mean) / self.scale

    def inverse(self, values: Sequence[float]) -> np.ndarray:
        return np.asarray(values, dtype=float) * self.scale + self.mean


def stable_digest(master_seed: int, namespace: str, value: str) -> str:
    material = f"{master_seed}|{namespace}|{value}".encode()
    return hashlib.sha256(material).hexdigest()


def deterministic_group_folds(
    group_ids: Sequence[str],
    master_seed: int,
    fold_count: int,
    strata: Mapping[str, tuple[str, str]] | None = None,
) -> dict[str, int]:
    """Assign whole groups using frozen design strata and no outcome labels."""

    unique = sorted(set(group_ids))
    if fold_count < 2 or len(unique) < fold_count:
        raise ValueError("Grouped CV requires at least one group per fold")
    design = strata or {group: ("all", "all") for group in unique}
    if set(design) != set(unique):
        raise ValueError("Every grouped-CV group requires one frozen design stratum")
    uncertainty_frequency = Counter(value[0] for value in design.values())
    ranked = sorted(
        unique,
        key=lambda group: (
            -uncertainty_frequency[design[group][0]],
            stable_digest(master_seed, "gate5_cv_group_stratified_v1", group),
        ),
    )
    assignments: dict[str, int] = {}
    fold_size: Counter[int] = Counter()
    fold_uncertainty: Counter[tuple[int, str]] = Counter()
    fold_trajectory_family: Counter[tuple[int, str]] = Counter()
    for group in ranked:
        uncertainty, trajectory_family = design[group]
        selected_fold = min(
            range(1, fold_count + 1),
            key=lambda fold: (
                fold_uncertainty[(fold, uncertainty)],
                fold_size[fold],
                fold_trajectory_family[(fold, trajectory_family)],
                stable_digest(
                    master_seed,
                    "gate5_cv_fold_tie_v1",
                    f"{group}|{fold}",
                ),
            ),
        )
        assignments[group] = selected_fold
        fold_size[selected_fold] += 1
        fold_uncertainty[(selected_fold, uncertainty)] += 1
        fold_trajectory_family[(selected_fold, trajectory_family)] += 1
    return assignments


def nested_training_indices(
    records: Sequence[Mapping[str, Any]],
    eligible_indices: Sequence[int],
    sample_count: int,
    master_seed: int,
) -> np.ndarray:
    """Select a nested, label-agnostic sample shared by QML and controls."""

    indices = np.asarray(eligible_indices, dtype=int)
    if sample_count <= 0 or sample_count > indices.size:
        raise ValueError("Requested sample count is outside the training fold")
    ranked = sorted(
        indices.tolist(),
        key=lambda index: stable_digest(
            master_seed,
            "gate5_learning_row_v1",
            str(records[index]["scenario_id"]),
        ),
    )
    return np.asarray(ranked[:sample_count], dtype=int)


def _scenario_path(root: Path, fidelity: str, group_id: str) -> Path:
    return (
        root
        / "data"
        / "processed"
        / "simulator"
        / "scenarios"
        / fidelity
        / DEVELOPMENT_SPLIT
        / f"{group_id}.jsonl"
    )


def load_development_records(
    root: Path, config: Mapping[str, Any]
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    """Load only paths committed to the development split manifest."""

    assert_no_final_payloads(root / config["governance"]["final_payload_root"])
    manifest = read_csv(root / "data/processed/simulator/scenario_manifest.csv")
    development = [row for row in manifest if row["split"] == DEVELOPMENT_SPLIT]
    records: list[dict[str, Any]] = []
    for row in development:
        path = _scenario_path(root, row["fidelity"], row["group_id"])
        if not path.is_file():
            raise FileNotFoundError(f"Missing development payload: {path}")
        with path.open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                record = json.loads(line)
                if record.get("split") != DEVELOPMENT_SPLIT:
                    raise ValueError(
                        f"Non-development row in {path}:{line_number}"
                    )
                if record.get("fidelity") != row["fidelity"]:
                    raise ValueError(f"Fidelity mismatch in {path}:{line_number}")
                if record.get("group_id") != row["group_id"]:
                    raise ValueError(f"Group mismatch in {path}:{line_number}")
                records.append(record)
    return records, development


def audit_development_records(
    records: Sequence[Mapping[str, Any]],
    manifest: Sequence[Mapping[str, str]],
    config: Mapping[str, Any],
) -> dict[str, Any]:
    """Check grain, completeness, identifiers, decision sets, and feature safety."""

    expected_rows = sum(int(row["case_count"]) for row in manifest)
    if len(records) != expected_rows:
        raise ValueError(f"Expected {expected_rows} development rows, found {len(records)}")

    ids = [str(record["scenario_id"]) for record in records]
    if len(ids) != len(set(ids)):
        raise ValueError("Development scenario_id values are not unique")

    expected_features = set(config["features"]["numeric"])
    expected_features.update(config["features"]["physics_derived"])
    expected_features.update(config["features"]["categorical"])
    prohibited = set(config["features"]["prohibited"])
    target = str(config["targets"]["primary_regression"])
    feasibility = str(config["targets"]["feasibility"])
    decision_sets: dict[str, list[int]] = defaultdict(list)
    by_fidelity: Counter[str] = Counter()
    by_group: Counter[str] = Counter()
    feasible_count = 0

    for record in records:
        inputs = record.get("inputs")
        outcomes = record.get("outcomes")
        if not isinstance(inputs, Mapping) or set(inputs) != expected_features:
            raise ValueError(f"Feature contract mismatch for {record['scenario_id']}")
        if prohibited.intersection(inputs):
            raise ValueError(f"Prohibited model input in {record['scenario_id']}")
        if not isinstance(outcomes, Mapping) or target not in outcomes:
            raise ValueError(f"Missing primary outcome for {record['scenario_id']}")
        if feasibility not in outcomes:
            raise ValueError(f"Missing feasibility for {record['scenario_id']}")
        if not math.isfinite(float(outcomes[target])):
            raise ValueError(f"Non-finite target for {record['scenario_id']}")
        if not isinstance(outcomes[feasibility], bool):
            raise ValueError(f"Non-boolean feasibility for {record['scenario_id']}")
        feasible_count += int(outcomes[feasibility])
        decision_sets[str(record["decision_set_id"])].append(
            int(record["candidate_index"])
        )
        by_fidelity[str(record["fidelity"])] += 1
        by_group[str(record["group_id"])] += 1

    expected_candidates = int(
        config["scenario_design"]["decision_sets"]["candidates_per_set"]
    )
    expected_candidate_ids = list(range(1, expected_candidates + 1))
    malformed = [
        set_id
        for set_id, candidates in decision_sets.items()
        if sorted(candidates) != expected_candidate_ids
    ]
    if malformed:
        raise ValueError(f"Malformed decision sets: {malformed[:5]}")

    expected_by_key = {
        (row["fidelity"], row["group_id"]): int(row["case_count"])
        for row in manifest
    }
    actual_by_key = Counter(
        (str(record["fidelity"]), str(record["group_id"])) for record in records
    )
    if dict(actual_by_key) != expected_by_key:
        raise ValueError("Development fidelity/group counts do not match the manifest")

    return {
        "status": "pass",
        "split": DEVELOPMENT_SPLIT,
        "rows": len(records),
        "columns_in_model_contract": len(expected_features),
        "unique_scenarios": len(ids),
        "decision_sets": len(decision_sets),
        "candidates_per_decision_set": expected_candidates,
        "feasible_rows": feasible_count,
        "feasible_rate": feasible_count / len(records),
        "rows_by_fidelity": dict(sorted(by_fidelity.items())),
        "rows_by_group": dict(sorted(by_group.items())),
    }


def fold_manifest_rows(
    config: Mapping[str, Any], manifest: Sequence[Mapping[str, str]]
) -> list[dict[str, Any]]:
    development = [row for row in manifest if row["split"] == DEVELOPMENT_SPLIT]
    registry = {
        item["id"]: item
        for item in config["scenario_design"]["group_registry"]
        if item["split"] == DEVELOPMENT_SPLIT
    }
    folds = deterministic_group_folds(
        list(registry),
        int(config["scenario_design"]["master_seed"]),
        int(config["tuning"]["grouped_cv_folds"]),
        {
            group_id: (
                str(item["uncertainty_family"]),
                str(item["base_trajectory"])[0],
            )
            for group_id, item in registry.items()
        },
    )
    counts: dict[str, Counter[str]] = defaultdict(Counter)
    for row in development:
        counts[row["group_id"]][row["fidelity"]] += int(row["case_count"])
    rows = []
    for group_id in sorted(registry):
        item = registry[group_id]
        fidelity_counts = counts[group_id]
        rows.append(
            {
                "fold_id": f"CV{folds[group_id]:02d}",
                "group_id": group_id,
                "base_trajectory": item["base_trajectory"],
                "uncertainty_family": item["uncertainty_family"],
                "f0_rows": fidelity_counts["F0"],
                "f1_rows": fidelity_counts["F1"],
                "f2_rows": fidelity_counts["F2"],
                "total_rows": sum(fidelity_counts.values()),
                "assignment_inputs": "master_seed_group_id_uncertainty_and_trajectory_family",
                "outcome_labels_used": False,
                "hash_namespace": "gate5_cv_group_stratified_v1",
            }
        )
    return sorted(rows, key=lambda row: (row["fold_id"], row["group_id"]))


def gate5_preflight(root: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Run the complete read-only audit required before Gate 5 fitting."""

    config = read_yaml(root / "configs/phase1_benchmark.yaml")
    records, manifest = load_development_records(root, config)
    audit = audit_development_records(records, manifest, config)
    tuning = read_csv(root / "data/processed/simulator/tuning_manifest.csv")
    seeds = read_csv(root / "data/processed/simulator/seed_manifest.csv")
    final_manifest = read_csv(
        root / "data/processed/simulator/final_test_manifest.csv"
    )
    checksums = read_csv(
        root / "data/processed/simulator/gate4_freeze_checksums.csv"
    )
    for row in checksums:
        artifact = root / "data/processed/simulator" / row["artifact"]
        if not artifact.is_file() or sha256_file(artifact) != row["sha256"]:
            raise ValueError(f"Gate 4 freeze checksum mismatch: {artifact}")
    family_trials = Counter(row["family_id"] for row in tuning)
    family_seeds = Counter(row["family_id"] for row in seeds)
    if len(tuning) != 300 or set(family_trials.values()) != {30}:
        raise ValueError("Tuning manifest must contain 30 trials for 10 families")
    if len(seeds) != 300 or set(family_seeds.values()) != {30}:
        raise ValueError("Seed manifest must contain 30 seeds for 10 families")
    if len({row["training_seed"] for row in seeds}) != len(seeds):
        raise ValueError("Training seeds must be unique in the frozen manifest")
    if any(
        row["feature_payload"] != "LOCKED_NOT_GENERATED"
        or row["label_payload"] != "LOCKED_NOT_GENERATED"
        for row in final_manifest
    ):
        raise ValueError("Final-test manifest no longer records a blind payload")

    folds = fold_manifest_rows(config, manifest)
    fold_ids = sorted({str(row["fold_id"]) for row in folds})
    if len(fold_ids) != int(config["tuning"]["grouped_cv_folds"]):
        raise ValueError("Fold manifest does not contain five validation folds")
    if len({str(row["group_id"]) for row in folds}) != 12:
        raise ValueError("Each development group must appear in exactly one fold")

    fold_by_group = {str(row["group_id"]): str(row["fold_id"]) for row in folds}
    feasibility_name = str(config["targets"]["feasibility"])
    fold_quality = []
    for fold_id in fold_ids:
        indices = [
            index
            for index, record in enumerate(records)
            if fold_by_group[str(record["group_id"])] == fold_id
        ]
        labels = [int(records[index]["outcomes"][feasibility_name]) for index in indices]
        if len(set(labels)) != 2:
            raise ValueError(f"{fold_id} lacks both feasibility classes")
        fold_quality.append(
            {
                "fold_id": fold_id,
                "validation_rows": len(indices),
                "validation_groups": len(
                    {str(records[index]["group_id"]) for index in indices}
                ),
                "feasible_rows": sum(labels),
                "feasible_rate": sum(labels) / len(labels),
            }
        )

    audit.update(
        {
            "runner_status": config.get("gate5_runner_freeze", {}).get("status"),
            "research_fit_authorized": config.get("gate5_runner_freeze", {}).get(
                "research_fit_authorized", False
            ),
            "campaign_refinement": config.get("gate5_runner_freeze", {}).get(
                "pre_fit_campaign_refinement"
            ),
            "tuning_trials": len(tuning),
            "seed_rows": len(seeds),
            "gate4_checksums_verified": len(checksums),
            "folds": fold_quality,
            "calibration_rows_read": 0,
            "final_test_rows_read": 0,
            "final_payload_root_absent_or_empty": True,
        }
    )
    return audit, folds


def write_csv_rows(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    if not rows:
        raise ValueError("Cannot write an empty CSV")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=list(rows[0]), lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


def load_fold_checkpoint(
    path: Path, task_signature: str
) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    checkpoint = json.loads(path.read_text(encoding="utf-8"))
    if checkpoint.get("task_signature") != task_signature:
        raise PermissionError(f"Checkpoint signature mismatch: {path}")
    return checkpoint


def write_fold_checkpoint(path: Path, checkpoint: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(checkpoint, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def load_trial(root: Path, trial_id: str) -> TrialSpec:
    rows = read_csv(root / "data/processed/simulator/tuning_manifest.csv")
    matches = [row for row in rows if row["trial_id"] == trial_id]
    if len(matches) != 1:
        raise ValueError(f"Expected one tuning row for {trial_id}")
    row = matches[0]
    return TrialSpec(
        row["family_id"],
        row["model_family"],
        row["trial_id"],
        int(row["trial_order"]),
        json.loads(row["parameters_json"]),
    )


def matched_qubits_for_trial(trial_order: int) -> int:
    if trial_order <= 0:
        raise ValueError("Trial order must be positive")
    return MATCHED_QUBITS[(trial_order - 1) % len(MATCHED_QUBITS)]


def initial_execution_plan(root: Path) -> list[dict[str, Any]]:
    """Return the complete first stage without reading scenario outcomes.

    A01 and compressed C05 are execution views rather than extra tuning trials.
    Every frozen control trial is repeated at 4/6/8 dimensions. This both gives
    each QML result an exactly matched control and permits strong controls to be
    advanced independently within each required dimension.
    """

    config = read_yaml(root / "configs/phase1_benchmark.yaml")
    runner_status = config.get("gate5_runner_freeze", {}).get("status")
    research_fit_authorized = config.get("gate5_runner_freeze", {}).get(
        "research_fit_authorized", False
    )
    if runner_status == RUNNER_ACCEPTED_STATUS and research_fit_authorized is True:
        execution_status = "ready"
    elif runner_status == RUNNER_ACCEPTED_STATUS:
        execution_status = "blocked_pending_d006_acceptance"
    else:
        execution_status = "blocked_pending_d005_acceptance"
    tuning = read_csv(root / "data/processed/simulator/tuning_manifest.csv")
    rows: list[dict[str, Any]] = []
    trial_by_family_order = {
        (raw["family_id"], int(raw["trial_order"])): raw for raw in tuning
    }
    qml_pairs: dict[tuple[int, int], set[str]] = defaultdict(set)
    for raw in tuning:
        trial_order = int(raw["trial_order"])
        family_id = raw["family_id"]
        family = raw["model_family"]
        parameters = json.loads(raw["parameters_json"])
        if family_id == "A01":
            continue
        if family in QML_FAMILIES:
            view = "primary"
            rung = 128
            qubits = int(parameters["qubits"])
            qml_pairs[(trial_order, qubits)].add(family_id)
        else:
            view = "primary"
            rung = None
            qubits = None
        rows.append(
            {
                "task_id": f"{raw['trial_id']}__{view}__{rung or 'full'}",
                "family_id": family_id,
                "model_family": family,
                "trial_id": raw["trial_id"],
                "trial_order": trial_order,
                "view": view,
                "rung_samples": rung,
                "matched_qubits": None,
                "effective_qubits": qubits,
                "candidate_role": raw["candidate_role"],
                "control_for": "",
                "advancement_basis": "candidate",
                "execution_status": execution_status,
            }
        )

    for trial_order in range(1, 31):
        for qubits in MATCHED_QUBITS:
            qml_ids = qml_pairs.get((trial_order, qubits), set())
            for family_id, view in (("A01", "primary"), ("C05", "compressed_c05")):
                raw = trial_by_family_order[(family_id, trial_order)]
                rows.append(
                    {
                        "task_id": f"{raw['trial_id']}__{view}__128__q{qubits}",
                        "family_id": raw["family_id"],
                        "model_family": raw["model_family"],
                        "trial_id": raw["trial_id"],
                        "trial_order": trial_order,
                        "view": view,
                        "rung_samples": 128,
                        "matched_qubits": qubits,
                        "effective_qubits": qubits,
                        "candidate_role": "interpretation_control_not_eligible_to_win",
                        "control_for": ";".join(sorted(qml_ids)),
                        "advancement_basis": (
                            "control_ranked_and_qml_matched"
                            if qml_ids
                            else "control_ranked"
                        ),
                        "execution_status": execution_status,
                    }
                )
    return rows


def _complexity_key(summary: Mapping[str, Any]) -> tuple[Any, ...]:
    trial = summary["trial"]
    family = str(trial["model_family"])
    parameters = trial["parameters"]
    if family == "ridge_elastic_net":
        return (0 if parameters["estimator"] == "ridge" else 1,)
    if family == "extra_trees":
        depth = parameters["max_depth"]
        return (int(parameters["n_estimators"]), math.inf if depth is None else int(depth))
    if family == "histogram_gradient_boosting":
        return (int(parameters["max_iter"]) * int(parameters["max_leaf_nodes"]),)
    if family == "sparse_gaussian_process":
        return (int(parameters["training_samples"]),)
    if family == "multilayer_perceptron":
        return (sum(int(value) for value in parameters["hidden_layers"]),)
    if family == "physics_residual":
        return (
            0 if parameters["residual_estimator"] == "ridge" else 1,
            int(parameters["max_leaf_nodes"]),
        )
    if family == "quantum_kernel":
        return (
            int(parameters["landmarks"]),
            int(parameters["data_reupload_layers"]) * int(parameters["qubits"]),
            int(bool(parameters["entangle"])),
        )
    if family in {"variational_quantum_regressor", "hybrid_quantum_residual"}:
        qubits = int(parameters["qubits"])
        layers = int(parameters["data_reupload_layers"])
        return (layers * qubits * 2 + qubits + 1, int(bool(parameters["entangle"])))
    if family == "random_fourier_ridge":
        return (int(parameters["n_components"]),)
    raise ValueError(f"No frozen complexity proxy for {family}")


def rank_rung_summaries(
    summaries: Sequence[Mapping[str, Any]],
    retain: int,
    preserve_required_qubits: bool = False,
) -> list[dict[str, Any]]:
    """Rank completed tasks with the frozen objective and deterministic ties."""

    if retain <= 0:
        raise ValueError("Retained trial count must be positive")

    def compare(left: Mapping[str, Any], right: Mapping[str, Any]) -> int:
        left_eligible = bool(left.get("eligible_to_advance", False))
        right_eligible = bool(right.get("eligible_to_advance", False))
        if left_eligible != right_eligible:
            return -1 if left_eligible else 1
        left_objective = float(left["pooled_oof_nrmse"])
        right_objective = float(right["pooled_oof_nrmse"])
        if abs(left_objective - right_objective) > 1e-12:
            return -1 if left_objective < right_objective else 1
        left_regret = float(left["mean_regret_m_s"])
        right_regret = float(right["mean_regret_m_s"])
        if abs(left_regret - right_regret) > 1e-12:
            return -1 if left_regret < right_regret else 1
        left_complexity = _complexity_key(left)
        right_complexity = _complexity_key(right)
        if left_complexity != right_complexity:
            return -1 if left_complexity < right_complexity else 1
        left_id = str(left["trial"]["trial_id"])
        right_id = str(right["trial"]["trial_id"])
        return (left_id > right_id) - (left_id < right_id)

    ranked = sorted(summaries, key=functools.cmp_to_key(compare))
    eligible = [row for row in ranked if bool(row.get("eligible_to_advance", False))]
    if len(eligible) < retain:
        raise ValueError("Too few eligible trials to satisfy the frozen retention count")
    selected: list[Mapping[str, Any]] = []
    if preserve_required_qubits:
        for qubits in MATCHED_QUBITS:
            match = next(
                (
                    row
                    for row in eligible
                    if int(
                        row["trial"]["parameters"].get(
                            "qubits", row.get("matched_qubits") or 0
                        )
                    )
                    == qubits
                ),
                None,
            )
            if match is None:
                raise ValueError(f"No eligible {qubits}-qubit task remains")
            selected.append(match)
    for row in eligible:
        if len(selected) >= retain:
            break
        if row not in selected:
            selected.append(row)
    return [
        {
            "rank": index,
            "trial_id": row["trial"]["trial_id"],
            "model_family": row["trial"]["model_family"],
            "pooled_oof_nrmse": row["pooled_oof_nrmse"],
            "mean_regret_m_s": row["mean_regret_m_s"],
            "complexity_proxy": json.dumps(_complexity_key(row)),
            "effective_qubits": row["trial"]["parameters"].get(
                "qubits", row.get("matched_qubits")
            ),
            "selected_for_next_rung": row in selected,
        }
        for index, row in enumerate(ranked, start=1)
    ]


def trial_seed(
    root: Path, trial: TrialSpec, seed_index: int | None = None
) -> int:
    resolved_seed_index = trial.trial_order if seed_index is None else seed_index
    rows = read_csv(root / "data/processed/simulator/seed_manifest.csv")
    matches = [
        row
        for row in rows
        if row["family_id"] == trial.family_id
        and int(row["seed_index"]) == resolved_seed_index
    ]
    if len(matches) != 1:
        raise ValueError(
            "Missing frozen training seed for "
            f"{trial.family_id} seed_index={resolved_seed_index}"
        )
    return int(matches[0]["training_seed"])


def _record_targets(
    records: Sequence[Mapping[str, Any]], indices: np.ndarray, name: str
) -> np.ndarray:
    return np.asarray(
        [float(records[index]["outcomes"][name]) for index in indices],
        dtype=float,
    )


def _record_feasibility(
    records: Sequence[Mapping[str, Any]], indices: np.ndarray, name: str
) -> np.ndarray:
    return np.asarray(
        [int(records[index]["outcomes"][name]) for index in indices],
        dtype=int,
    )


def _low_fidelity_cost(
    records: Sequence[Mapping[str, Any]], indices: np.ndarray
) -> np.ndarray:
    return np.asarray(
        [float(records[index]["inputs"]["low_fidelity_cost_m_s"]) for index in indices]
    )


def fit_fold_features(
    train_records: Sequence[Mapping[str, Any]],
    validation_records: Sequence[Mapping[str, Any]],
    config: Mapping[str, Any],
    projected_qubits: int | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Fit every learned transform on one CV training fold only."""

    numeric_features = [
        *config["features"]["numeric"],
        *config["features"]["physics_derived"],
    ]
    categorical_features = config["features"]["categorical"]
    preprocessor = FrozenFeaturePreprocessor(numeric_features, categorical_features)
    x_train = preprocessor.fit_transform(train_records, DEVELOPMENT_SPLIT)
    x_validation = preprocessor.transform(validation_records, DEVELOPMENT_SPLIT)
    if projected_qubits is not None:
        projector = QuantumFeatureProjector(projected_qubits)
        x_train = projector.fit_transform(x_train, DEVELOPMENT_SPLIT)
        x_validation = projector.transform(x_validation, DEVELOPMENT_SPLIT)
    return x_train, x_validation


def _kernel_diagnostics(
    x: np.ndarray, y: np.ndarray, trial: TrialSpec
) -> dict[str, Any]:
    parameters = trial.parameters
    kernel = quantum_kernel_matrix(
        x,
        x,
        int(parameters["qubits"]),
        int(parameters["data_reupload_layers"]),
        feature_scale=float(parameters["feature_scale"]),
        entangle=bool(parameters["entangle"]),
    )
    count = kernel.shape[0]
    centering = np.eye(count) - np.ones((count, count)) / count
    centered = centering @ kernel @ centering
    centered_target = y - np.mean(y)
    target_kernel = np.outer(centered_target, centered_target)
    denominator = np.linalg.norm(centered) * np.linalg.norm(target_kernel)
    alignment = float(np.sum(centered * target_kernel) / denominator)
    eigenvalues = np.clip(np.linalg.eigvalsh(centered), 0.0, None)
    total = float(np.sum(eigenvalues))
    probabilities = eigenvalues[eigenvalues > 0.0] / total
    effective_rank = float(np.exp(-np.sum(probabilities * np.log(probabilities))))
    alpha = float(parameters["alpha"])
    regularized = np.linalg.eigvalsh(kernel + alpha * np.eye(count))
    off_diagonal = kernel[~np.eye(count, dtype=bool)]
    return {
        "centered_kernel_target_alignment": alignment,
        "off_diagonal_mean": float(np.mean(off_diagonal)),
        "off_diagonal_std": float(np.std(off_diagonal, ddof=0)),
        "off_diagonal_q05": float(np.quantile(off_diagonal, 0.05)),
        "off_diagonal_q95": float(np.quantile(off_diagonal, 0.95)),
        "effective_rank": effective_rank,
        "regularized_condition_number": float(regularized[-1] / regularized[0]),
        "kernel_rows": count,
        "nystrom_landmarks": int(parameters["landmarks"]),
    }


def variational_diagnostics(model: Any, qubits: int, layers: int, entangle: bool) -> dict[str, Any]:
    residual_model = getattr(model, "residual_model_", model)
    parameter_count = layers * qubits * 2 + qubits + 1
    return {
        "optimization_success": bool(residual_model.optimization_success_),
        "optimization_message": residual_model.optimization_message_,
        "initial_loss": float(residual_model.initial_loss_),
        "training_loss": float(residual_model.training_loss_),
        "loss_improvement": float(residual_model.loss_improvement_),
        "gradient_norm_proxy": residual_model.gradient_norm_proxy_,
        "optimizer_iterations": int(residual_model.optimizer_iterations_),
        "objective_evaluations": int(residual_model.objective_evaluations_),
        "parameter_count": parameter_count,
        "logical_circuit_depth": layers * (6 if entangle else 4),
        "two_qubit_gate_count": layers * qubits if entangle else 0,
        "resource_count_scope": "logical_pretranspilation_per_circuit_evaluation",
    }


def fitted_trainable_parameter_count(model: Any) -> int | None:
    """Count fitted linear/MLP trainable arrays for capacity diagnostics."""

    fitted = getattr(model, "estimator_", model)
    if hasattr(fitted, "steps"):
        fitted = fitted.steps[-1][1]
    arrays: list[np.ndarray] = []
    if hasattr(fitted, "coefs_"):
        arrays.extend(np.asarray(value) for value in fitted.coefs_)
        arrays.extend(np.asarray(value) for value in fitted.intercepts_)
    elif hasattr(fitted, "coef_"):
        arrays.append(np.asarray(fitted.coef_))
        if hasattr(fitted, "intercept_"):
            arrays.append(np.asarray(fitted.intercept_))
    return sum(value.size for value in arrays) if arrays else None


def _regime_diagnostics(
    records: Sequence[Mapping[str, Any]],
    indices: np.ndarray,
    observed_cost: np.ndarray,
    predicted_cost: np.ndarray,
    observed_feasible: np.ndarray,
    predicted_probability: np.ndarray,
    development_scale: float,
    config: Mapping[str, Any],
    fold_id: str,
) -> list[dict[str, Any]]:
    decision_ids = np.asarray(
        [str(records[index]["decision_set_id"]) for index in indices], dtype=object
    )
    reference_feasible = {
        decision_id: bool(np.any(observed_feasible[decision_ids == decision_id]))
        for decision_id in set(decision_ids.tolist())
    }
    dimensions = {
        "fidelity": [str(records[index]["fidelity"]) for index in indices],
        "uncertainty_family": [
            str(records[index]["inputs"]["uncertainty_family"]) for index in indices
        ],
        "base_trajectory_family": [
            str(records[index]["base_trajectory"])[0] for index in indices
        ],
        "boundary_or_tail": [
            str(bool(records[index]["boundary_or_tail"])).lower() for index in indices
        ],
        "reference_feasible_status": [
            "reference_feasible"
            if reference_feasible[str(records[index]["decision_set_id"])]
            else "no_reference_feasible"
            for index in indices
        ],
    }
    expected_candidates = int(
        config["scenario_design"]["decision_sets"]["candidates_per_set"]
    )
    rows: list[dict[str, Any]] = []
    for dimension, raw_values in dimensions.items():
        values = np.asarray(raw_values, dtype=object)
        for value in sorted(set(raw_values)):
            selected = values == value
            regression = regression_metrics(
                observed_cost[selected], predicted_cost[selected], development_scale
            )
            try:
                feasibility = feasibility_metrics(
                    observed_feasible[selected], predicted_probability[selected]
                )
                auroc = feasibility.auroc
                brier = feasibility.brier
                feasibility_error = None
            except ValueError as error:
                auroc = None
                brier = None
                feasibility_error = str(error)
            selected_ids = decision_ids[selected]
            counts = Counter(selected_ids.tolist())
            complete_ids = {
                decision_id
                for decision_id, count in counts.items()
                if count == expected_candidates
            }
            complete = selected & np.isin(decision_ids, list(complete_ids))
            if complete_ids:
                regret = feasibility_constrained_regret(
                    decision_ids[complete],
                    predicted_cost[complete],
                    predicted_probability[complete],
                    observed_cost[complete],
                    observed_feasible[complete],
                    feasibility_threshold=float(
                        config["analysis"]["feasibility_threshold"]
                    ),
                    infeasible_penalty_m_s=float(
                        config["analysis"]["infeasible_regret_penalty_m_s"]
                    ),
                )
                mean_regret = regret.mean_regret_m_s
                no_reference_rate = regret.no_reference_feasible_rate
            else:
                mean_regret = None
                no_reference_rate = None
            rows.append(
                {
                    "fold_id": fold_id,
                    "dimension": dimension,
                    "value": value,
                    "rows": int(np.sum(selected)),
                    "complete_decision_sets": len(complete_ids),
                    "rmse": regression.rmse,
                    "nrmse": regression.nrmse,
                    "mae": regression.mae,
                    "feasibility_auroc": auroc,
                    "feasibility_brier": brier,
                    "feasibility_metric_error": feasibility_error,
                    "mean_regret_m_s": mean_regret,
                    "no_reference_feasible_rate": no_reference_rate,
                }
            )
    return rows


def _clean_source_commit(root: Path) -> str:
    commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True
    ).strip()
    tracked_status = subprocess.check_output(
        ["git", "status", "--porcelain", "--untracked-files=no"],
        cwd=root,
        text=True,
    ).strip()
    if tracked_status:
        raise PermissionError("Gate 5 execution requires a clean tracked worktree")
    return commit


def validate_development_output_path(
    root: Path,
    output_path: Path,
    config: Mapping[str, Any] | None = None,
) -> Path:
    """Reject any development artifact path inside the locked final payload."""

    active_config = (
        read_yaml(root / "configs/phase1_benchmark.yaml")
        if config is None
        else config
    )
    locked_root = (root / active_config["governance"]["final_payload_root"]).resolve()
    resolved_output = output_path.resolve()
    if resolved_output == locked_root or locked_root in resolved_output.parents:
        raise PermissionError(
            "Gate 5 development artifacts cannot be written under the final payload root"
        )
    return resolved_output


def _build_models(
    trial: TrialSpec,
    seed: int,
    view: str,
) -> tuple[Any, Any]:
    family = trial.model_family
    if view == "compressed_c05":
        if family != "multilayer_perceptron":
            raise ValueError("compressed_c05 requires a C05 trial")
        return (
            build_classical_regressor(family, trial.parameters, seed),
            build_classical_classifier(family, trial.parameters, seed),
        )
    if family in QML_FAMILIES:
        return (
            build_quantum_regressor(
                family,
                trial.parameters,
                seed,
                low_fidelity_column=-1,
            ),
            build_quantum_classifier(family, trial.parameters, seed),
        )
    if family == "random_fourier_ridge":
        return (
            build_qml_control_regressor(family, trial.parameters, seed),
            build_qml_control_classifier(family, trial.parameters, seed),
        )
    return (
        build_classical_regressor(
            family,
            trial.parameters,
            seed,
            low_fidelity_column=-1,
        ),
        build_classical_classifier(family, trial.parameters, seed),
    )


def execute_trial(
    root: Path,
    trial_id: str,
    output_dir: Path,
    rung_samples: int | None = None,
    matched_qubits: int | None = None,
    view: str = "primary",
    seed_index: int | None = None,
) -> dict[str, Any]:
    """Execute one resumable development-CV task under the active authorization."""

    config = read_yaml(root / "configs/phase1_benchmark.yaml")
    status = config.get("gate5_runner_freeze", {}).get("status")
    research_fit_authorized = config.get("gate5_runner_freeze", {}).get(
        "research_fit_authorized", False
    )
    if status != RUNNER_ACCEPTED_STATUS or research_fit_authorized is not True:
        raise PermissionError(
            "Research fitting is blocked until the human lead accepts the active runner contract"
        )
    source_commit = _clean_source_commit(root)
    validate_development_output_path(root, output_dir, config)
    task_started = time.perf_counter()
    records, manifest = load_development_records(root, config)
    audit_development_records(records, manifest, config)
    trial = load_trial(root, trial_id)
    resolved_seed_index = trial.trial_order if seed_index is None else seed_index
    seed = trial_seed(root, trial, resolved_seed_index)

    projected = trial.model_family in QML_FAMILIES or trial.model_family == "random_fourier_ridge" or view == "compressed_c05"
    qubits = (
        int(trial.parameters["qubits"])
        if trial.model_family in QML_FAMILIES
        else matched_qubits
    )
    if (
        trial.model_family in QML_FAMILIES
        and matched_qubits is not None
        and matched_qubits != qubits
    ):
        raise ValueError("QML matched_qubits must equal the frozen trial dimension")
    if projected and qubits not in {4, 6, 8}:
        raise ValueError("Matched projected views require 4, 6, or 8 qubits")
    if projected and rung_samples not in {128, 256, 512, 1024}:
        raise ValueError("Projected views require a frozen learning-curve rung")
    if not projected and rung_samples is not None:
        raise ValueError("Unrestricted classical trials do not accept a rung")

    task_signature = hashlib.sha256(
        json.dumps(
            {
                "source_commit": source_commit,
                "trial": asdict(trial),
                "view": view,
                "rung_samples": rung_samples,
                "matched_qubits": matched_qubits,
                "seed_index": resolved_seed_index,
                "training_seed": seed,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()
    output_dir.mkdir(parents=True, exist_ok=True)

    fold_rows = fold_manifest_rows(config, manifest)
    fold_by_group = {
        row["group_id"]: int(str(row["fold_id"])[2:]) for row in fold_rows
    }
    primary_target = str(config["targets"]["primary_regression"])
    feasibility_target = str(config["targets"]["feasibility"])
    all_targets = _record_targets(
        records, np.arange(len(records), dtype=int), primary_target
    )
    development_scale = development_target_scale(all_targets)
    master_seed = int(config["scenario_design"]["master_seed"])
    fold_results: list[dict[str, Any]] = []
    regime_results: list[dict[str, Any]] = []
    total_squared_error = 0.0
    total_prediction_rows = 0
    all_regret_weighted = 0.0
    all_decision_sets = 0
    setup_wall_time = time.perf_counter() - task_started

    for fold_id in range(1, int(config["tuning"]["grouped_cv_folds"]) + 1):
        checkpoint_path = output_dir / f"fold_CV{fold_id:02d}.json"
        checkpoint = load_fold_checkpoint(checkpoint_path, task_signature)
        if checkpoint is not None:
            fold_results.append(checkpoint["fold_metrics"])
            regime_results.extend(checkpoint["regime_metrics"])
            total_squared_error += float(checkpoint["squared_error_sum"])
            total_prediction_rows += int(checkpoint["validation_rows"])
            all_regret_weighted += float(checkpoint["regret_sum_m_s"])
            all_decision_sets += int(checkpoint["decision_sets"])
            continue
        fold_started = time.perf_counter()
        validation_indices = np.asarray(
            [
                index
                for index, record in enumerate(records)
                if fold_by_group[str(record["group_id"])] == fold_id
            ],
            dtype=int,
        )
        eligible_train = np.asarray(
            [
                index
                for index, record in enumerate(records)
                if fold_by_group[str(record["group_id"])] != fold_id
            ],
            dtype=int,
        )
        train_indices = eligible_train
        if projected:
            train_indices = nested_training_indices(
                records, eligible_train, int(rung_samples), master_seed
            )
        elif trial.model_family == "sparse_gaussian_process":
            train_indices = nested_training_indices(
                records,
                eligible_train,
                min(int(trial.parameters["training_samples"]), eligible_train.size),
                master_seed,
            )

        train_records = [records[index] for index in train_indices]
        validation_records = [records[index] for index in validation_indices]
        x_train, x_validation = fit_fold_features(
            train_records,
            validation_records,
            config,
            projected_qubits=int(qubits) if projected else None,
        )

        y_train_raw = _record_targets(records, train_indices, primary_target)
        y_validation = _record_targets(records, validation_indices, primary_target)
        standardizer = TargetStandardizer.fit(y_train_raw)
        y_train = standardizer.transform(y_train_raw)
        x_feasibility_train = x_train
        x_feasibility_validation = x_validation
        if trial.model_family in RESIDUAL_FAMILIES:
            baseline_train = standardizer.transform(
                _low_fidelity_cost(records, train_indices)
            )
            baseline_validation = standardizer.transform(
                _low_fidelity_cost(records, validation_indices)
            )
            x_train = np.column_stack((x_train, baseline_train))
            x_validation = np.column_stack((x_validation, baseline_validation))

        feasible_train = _record_feasibility(
            records, train_indices, feasibility_target
        )
        feasible_validation = _record_feasibility(
            records, validation_indices, feasibility_target
        )
        cost_model, feasibility_model = _build_models(trial, seed, view)
        started = time.perf_counter()
        cost_model.fit(x_train, y_train)
        feasibility_model.fit(x_feasibility_train, feasible_train)
        training_wall = time.perf_counter() - started
        started = time.perf_counter()
        predicted_cost = standardizer.inverse(cost_model.predict(x_validation))
        predicted_probability = feasibility_model.predict_proba(
            x_feasibility_validation
        )[:, 1]
        inference_wall = time.perf_counter() - started

        regression = regression_metrics(
            y_validation, predicted_cost, development_scale
        )
        try:
            feasibility = asdict(
                feasibility_metrics(feasible_validation, predicted_probability)
            )
            feasibility_error = None
        except ValueError as error:
            feasibility = {}
            feasibility_error = str(error)
        decision_ids = [
            str(records[index]["decision_set_id"]) for index in validation_indices
        ]
        regret = feasibility_constrained_regret(
            decision_ids,
            predicted_cost,
            predicted_probability,
            y_validation,
            feasible_validation,
            feasibility_threshold=float(config["analysis"]["feasibility_threshold"]),
            infeasible_penalty_m_s=float(
                config["analysis"]["infeasible_regret_penalty_m_s"]
            ),
        )
        errors = predicted_cost - y_validation
        squared_error_sum = float(np.sum(errors * errors))
        regret_sum = regret.mean_regret_m_s * regret.decision_sets
        total_squared_error += squared_error_sum
        total_prediction_rows += errors.size
        all_regret_weighted += regret_sum
        all_decision_sets += regret.decision_sets
        row: dict[str, Any] = {
            "fold_id": f"CV{fold_id:02d}",
            "trial_id": trial.trial_id,
            "family_id": trial.family_id,
            "model_family": trial.model_family,
            "view": view,
            "seed_index": resolved_seed_index,
            "training_seed": seed,
            "rung_samples": rung_samples,
            "qubits": qubits,
            "data_reupload_layers": trial.parameters.get("data_reupload_layers"),
            "feature_scale": trial.parameters.get("feature_scale"),
            "entangle": trial.parameters.get("entangle"),
            "shots": "exact_statevector" if trial.model_family in QML_FAMILIES else None,
            "noise_state": "none" if trial.model_family in QML_FAMILIES else None,
            "training_rows": train_indices.size,
            "validation_rows": validation_indices.size,
            "training_groups": len(
                {str(records[index]["group_id"]) for index in train_indices}
            ),
            "validation_groups": len(
                {str(records[index]["group_id"]) for index in validation_indices}
            ),
            "rmse": regression.rmse,
            "nrmse": regression.nrmse,
            "mae": regression.mae,
            "mean_regret_m_s": regret.mean_regret_m_s,
            "no_reference_feasible_rate": regret.no_reference_feasible_rate,
            "training_wall_time_s": training_wall,
            "inference_wall_time_s": inference_wall,
            "feasibility_metric_error": feasibility_error,
            "cost_fitted_trainable_parameter_count": fitted_trainable_parameter_count(
                cost_model
            ),
            "feasibility_fitted_trainable_parameter_count": fitted_trainable_parameter_count(
                feasibility_model
            ),
            **{f"feasibility_{key}": value for key, value in feasibility.items()},
        }
        if trial.model_family == "quantum_kernel":
            row.update(_kernel_diagnostics(x_train, y_train, trial))
        if trial.model_family in {
            "variational_quantum_regressor",
            "hybrid_quantum_residual",
        }:
            row.update(
                {
                    f"cost_{key}": value
                    for key, value in variational_diagnostics(
                    cost_model,
                    int(trial.parameters["qubits"]),
                    int(trial.parameters["data_reupload_layers"]),
                    bool(trial.parameters["entangle"]),
                    ).items()
                }
            )
            classifier_regressor = feasibility_model.regressor_
            row.update(
                {
                    f"feasibility_{key}": value
                    for key, value in variational_diagnostics(
                        classifier_regressor,
                        int(trial.parameters["qubits"]),
                        int(trial.parameters["data_reupload_layers"]),
                        bool(trial.parameters["entangle"]),
                    ).items()
                }
            )
            row["eligible_to_advance"] = bool(
                row["cost_optimization_success"]
                and row["feasibility_optimization_success"]
            )
        else:
            row["eligible_to_advance"] = True
        fold_regimes = _regime_diagnostics(
            records,
            validation_indices,
            y_validation,
            predicted_cost,
            feasible_validation,
            predicted_probability,
            development_scale,
            config,
            f"CV{fold_id:02d}",
        )
        row["fold_end_to_end_wall_time_s"] = time.perf_counter() - fold_started
        fold_results.append(row)
        regime_results.extend(fold_regimes)
        checkpoint = {
            "task_signature": task_signature,
            "source_commit": source_commit,
            "seed_index": resolved_seed_index,
            "training_seed": seed,
            "fold_metrics": row,
            "regime_metrics": fold_regimes,
            "squared_error_sum": squared_error_sum,
            "validation_rows": errors.size,
            "regret_sum_m_s": regret_sum,
            "decision_sets": regret.decision_sets,
            "calibration_rows_read": 0,
            "final_test_rows_read": 0,
        }
        write_fold_checkpoint(checkpoint_path, checkpoint)

    pooled_rmse = math.sqrt(total_squared_error / total_prediction_rows)
    summary = {
        "status": "complete",
        "selection_scope": "development_only",
        "trial": asdict(trial),
        "view": view,
        "rung_samples": rung_samples,
        "matched_qubits": matched_qubits,
        "seed_index": resolved_seed_index,
        "training_seed": seed,
        "pooled_oof_rmse": pooled_rmse,
        "pooled_oof_nrmse": pooled_rmse / development_scale,
        "unweighted_mean_fold_nrmse": float(
            np.mean([row["nrmse"] for row in fold_results])
        ),
        "mean_regret_m_s": all_regret_weighted / all_decision_sets,
        "fold_count": len(fold_results),
        "eligible_to_advance": all(
            bool(row["eligible_to_advance"]) for row in fold_results
        ),
        "source_commit": source_commit,
        "task_signature": task_signature,
        "checkpoint_count": len(fold_results),
        "end_to_end_wall_time_s": setup_wall_time
        + sum(float(row["fold_end_to_end_wall_time_s"]) for row in fold_results),
        "source_split": DEVELOPMENT_SPLIT,
        "calibration_rows_read": 0,
        "final_test_rows_read": 0,
    }
    write_csv_rows(output_dir / "fold_metrics.csv", fold_results)
    write_csv_rows(output_dir / "regime_metrics.csv", regime_results)
    temporary = output_dir / "summary.json.tmp"
    temporary.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    temporary.replace(output_dir / "summary.json")
    return summary
