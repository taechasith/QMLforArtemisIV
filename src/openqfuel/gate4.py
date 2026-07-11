"""Deterministic Gate 4 benchmark-freeze manifests and access controls."""

from __future__ import annotations

import csv
import hashlib
import itertools
import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import yaml


FINAL_SPLITS = frozenset(
    {"in_distribution_final_test", "out_of_distribution_final_test"}
)
MODEL_SELECTION_PURPOSES = frozenset({"fit", "tune", "feature_selection"})


class FinalTestAccessError(RuntimeError):
    """Raised when code attempts to cross the pre-approval final-test lock."""


@dataclass(frozen=True)
class FreezeArtifacts:
    scenario_manifest: Path
    final_test_manifest: Path
    seed_manifest: Path
    tuning_manifest: Path
    scenario_schema: Path
    checksums: Path


def read_yaml(path: Path | str) -> dict[str, Any]:
    with Path(path).open(encoding="utf-8") as handle:
        value = yaml.safe_load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"Expected a mapping in {path}")
    return value


def read_csv(path: Path | str) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path | str, rows: Sequence[Mapping[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"Cannot write an empty manifest: {path}")
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_file(path: Path | str) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def derive_seed(master_seed: int, namespace: str, *parts: object) -> int:
    """Derive a stable unsigned 32-bit seed from the frozen master seed."""

    material = "|".join(str(item) for item in (master_seed, namespace, *parts))
    return int.from_bytes(hashlib.sha256(material.encode("utf-8")).digest()[:4], "big")


def boundary_case_ids(
    master_seed: int,
    fidelity: str,
    group_id: str,
    case_count: int,
    uncertainty_family: str,
) -> list[str]:
    """Return the exact hash-ranked boundary/tail identity set for one group."""

    identities = [
        f"{fidelity}-{group_id}-{index:06d}" for index in range(1, case_count + 1)
    ]
    if uncertainty_family == "U5":
        return identities
    selected_count = (case_count + 3) // 4
    ranked = sorted(
        identities,
        key=lambda scenario_id: sha256_text(
            f"{master_seed}|boundary|{fidelity}|{group_id}|{scenario_id.rsplit('-', 1)[1]}"
        ),
    )
    return sorted(ranked[:selected_count])


def _window_registry(rows: Sequence[Mapping[str, str]]) -> dict[str, Mapping[str, str]]:
    registry = {row["window_id"]: row for row in rows}
    if len(registry) != len(rows):
        raise ValueError("Window IDs must be unique")
    return registry


def model_families(config: Mapping[str, Any]) -> list[dict[str, str]]:
    models = config["models"]
    return [*models["classical"], *models["quantum"]]


def tunable_families(config: Mapping[str, Any]) -> list[dict[str, str]]:
    models = config["models"]
    return [*model_families(config), *models.get("interpretation_controls", [])]


def validate_freeze_config(
    config: Mapping[str, Any], windows: Sequence[Mapping[str, str]]
) -> None:
    _VALID_STATUSES = {
        "gate_4_freeze_candidate_pending_human_approval",
        "gate_4_accepted_development_generation_authorized",
    }
    if config["status"] not in _VALID_STATUSES:
        raise ValueError(
            "Gate 4 configuration status must be a recognised freeze or accepted value"
        )

    scenario = config["scenario_design"]
    fractions = scenario["split_fractions"]
    if abs(sum(float(value) for value in fractions.values()) - 1.0) > 1e-12:
        raise ValueError("Gate 4 split fractions must sum to one")

    groups = scenario["group_registry"]
    expected_groups = scenario["groups_per_split"]
    observed_groups = Counter(group["split"] for group in groups)
    if observed_groups != Counter(expected_groups):
        raise ValueError(
            f"Group allocation differs from frozen split: {dict(observed_groups)}"
        )

    window_by_id = _window_registry(windows)
    group_ids: set[str] = set()
    grouping_keys: set[tuple[str, str, str]] = set()
    for group in groups:
        group_id = str(group["id"])
        if group_id in group_ids:
            raise ValueError(f"Duplicate Gate 4 group ID: {group_id}")
        group_ids.add(group_id)
        base = str(group["base_trajectory"])
        if base not in window_by_id:
            raise ValueError(f"Unknown base trajectory: {base}")
        key = (
            window_by_id[base]["start_utc"],
            str(group["uncertainty_family"]),
            base,
        )
        if key in grouping_keys:
            raise ValueError(f"Group leakage through duplicate key: {key}")
        grouping_keys.add(key)
        is_ood = group["split"] == "out_of_distribution_final_test"
        if is_ood != (group["uncertainty_family"] == "U5"):
            raise ValueError("Only U5 groups may enter the OOD final test")

    group_count = len(groups)
    candidates_per_set = int(scenario["decision_sets"]["candidates_per_set"])
    if candidates_per_set <= 1:
        raise ValueError("Each decision set must contain at least two candidates")
    for fidelity, definition in scenario["fidelities"].items():
        cases = int(definition["cases"])
        if cases % group_count:
            raise ValueError(
                f"{fidelity} case count must divide evenly across {group_count} groups"
            )
        group_size = cases // group_count
        if group_size % candidates_per_set:
            raise ValueError(
                f"{fidelity} group size must divide into complete decision sets"
            )
        for split, fraction in fractions.items():
            expected_cases = int(round(cases * float(fraction)))
            actual_cases = int(expected_groups[split]) * group_size
            if expected_cases != actual_cases:
                raise ValueError(
                    f"{fidelity}/{split} has {actual_cases}, expected {expected_cases}"
                )

    families = model_families(config)
    counts = config["models"]["family_count"]
    if len(config["models"]["classical"]) != int(counts["classical"]):
        raise ValueError("Classical model family count changed")
    if len(config["models"]["quantum"]) != int(counts["quantum"]):
        raise ValueError("Quantum model family count changed")
    if len({family["family"] for family in families}) != len(families):
        raise ValueError("Model family names must be unique")
    tunable = tunable_families(config)
    if len({family["family"] for family in tunable}) != len(tunable):
        raise ValueError("Candidate and control family names must be unique")
    missing_search = {
        family["family"]
        for family in tunable
        if family["family"] not in config["tuning"]["search_values"]
    }
    if missing_search:
        raise ValueError(f"Missing tuning search spaces: {sorted(missing_search)}")


def build_scenario_manifest(
    config: Mapping[str, Any], windows: Sequence[Mapping[str, str]]
) -> list[dict[str, Any]]:
    """Build a compact manifest that deterministically defines all 65,000 IDs."""

    validate_freeze_config(config, windows)
    scenario = config["scenario_design"]
    window_by_id = _window_registry(windows)
    master_seed = int(scenario["master_seed"])
    group_count = len(scenario["group_registry"])
    candidates_per_set = int(scenario["decision_sets"]["candidates_per_set"])
    rows: list[dict[str, Any]] = []

    for fidelity, definition in scenario["fidelities"].items():
        case_count = int(definition["cases"]) // group_count
        decision_set_count = case_count // candidates_per_set
        for group in scenario["group_registry"]:
            base = str(group["base_trajectory"])
            window = window_by_id[base]
            group_key = {
                "mission_epoch_utc": window["start_utc"],
                "uncertainty_family": group["uncertainty_family"],
                "base_trajectory": base,
            }
            group_id = str(group["id"])
            namespace = f"scenario|{fidelity}|{group_id}"
            first_id = f"{fidelity}-{group_id}-000001"
            last_id = f"{fidelity}-{group_id}-{case_count:06d}"
            boundary_ids = boundary_case_ids(
                master_seed,
                fidelity,
                group_id,
                case_count,
                str(group["uncertainty_family"]),
            )
            rows.append(
                {
                    "fidelity": fidelity,
                    "group_id": group_id,
                    "split": group["split"],
                    "base_trajectory": base,
                    "mission_phase": window["phase"],
                    "mission_epoch_utc": window["start_utc"],
                    "uncertainty_family": group["uncertainty_family"],
                    "case_count": case_count,
                    "decision_set_count": decision_set_count,
                    "candidates_per_decision_set": candidates_per_set,
                    "decision_set_id_first": f"{fidelity}-{group_id}-D000001",
                    "decision_set_id_last": (
                        f"{fidelity}-{group_id}-D{decision_set_count:06d}"
                    ),
                    "boundary_or_tail_case_count": len(boundary_ids),
                    "boundary_selection_method": (
                        "all_u5"
                        if group["uncertainty_family"] == "U5"
                        else "sha256_rank_lowest_quarter"
                    ),
                    "boundary_id_commitment": sha256_text("\n".join(boundary_ids)),
                    "scenario_id_first": first_id,
                    "scenario_id_last": last_id,
                    "group_fingerprint": sha256_text(canonical_json(group_key)),
                    "seed_namespace_commitment": sha256_text(
                        f"{master_seed}|{namespace}"
                    ),
                    "feature_payload_status": "not_generated_gate_4_freeze",
                    "label_payload_status": "not_generated_gate_4_freeze",
                }
            )
    return rows


def build_final_test_manifest(
    scenario_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    rows = []
    for row in scenario_rows:
        if row["split"] not in FINAL_SPLITS:
            continue
        commitment = sha256_text(
            canonical_json(
                {
                    "fidelity": row["fidelity"],
                    "group_fingerprint": row["group_fingerprint"],
                    "scenario_id_first": row["scenario_id_first"],
                    "scenario_id_last": row["scenario_id_last"],
                    "case_count": row["case_count"],
                    "decision_set_count": row["decision_set_count"],
                    "candidates_per_decision_set": row["candidates_per_decision_set"],
                }
            )
        )
        rows.append(
            {
                "fidelity": row["fidelity"],
                "split": row["split"],
                "scenario_id_first": row["scenario_id_first"],
                "scenario_id_last": row["scenario_id_last"],
                "case_count": row["case_count"],
                "decision_set_count": row["decision_set_count"],
                "candidates_per_decision_set": row["candidates_per_decision_set"],
                "group_commitment": commitment,
                "feature_payload": "LOCKED_NOT_GENERATED",
                "label_payload": "LOCKED_NOT_GENERATED",
                "access_status": "prohibited_pending_separate_final_test_unlock",
            }
        )
    return rows


def build_seed_manifest(config: Mapping[str, Any]) -> list[dict[str, Any]]:
    master = int(config["scenario_design"]["master_seed"])
    development_count = int(config["randomness"]["development_seeds_per_configuration"])
    finalist_count = int(config["randomness"]["finalist_seeds"])
    gate4_accepted = (
        config["status"] == "gate_4_accepted_development_generation_authorized"
    )
    rows: list[dict[str, Any]] = []
    for family in tunable_families(config):
        family_name = family["family"]
        for index in range(1, finalist_count + 1):
            rows.append(
                {
                    "family_id": family["id"],
                    "model_family": family_name,
                    "seed_index": index,
                    "seed_role": (
                        "development_and_finalist"
                        if index <= development_count
                        else "finalist_extension_only"
                    ),
                    "training_seed": derive_seed(
                        master, "training", family_name, index
                    ),
                    "shot_seed": derive_seed(master, "shots", family_name, index),
                    "development_use_status": (
                        "authorized_after_gate_4_acceptance"
                        if gate4_accepted
                        else "synthetic_smoke_only_pending_gate_4"
                    ),
                    "final_test_use": "prohibited_until_separate_unlock_commit",
                }
            )
    return rows


def _fixed_trial_combinations(
    values: Mapping[str, Sequence[Any]], master_seed: int, family: str, count: int
) -> list[dict[str, Any]]:
    if family == "ridge_elastic_net":
        combinations = [
            {"alpha": alpha, "estimator": "ridge"} for alpha in values["alpha"]
        ]
        combinations.extend(
            {
                "alpha": alpha,
                "estimator": "elastic_net",
                "l1_ratio": l1_ratio,
            }
            for alpha, l1_ratio in itertools.product(
                values["alpha"], values["l1_ratio"]
            )
        )
    else:
        keys = sorted(values)
        combinations = [
            dict(zip(keys, combination))
            for combination in itertools.product(*(values[key] for key in keys))
        ]
    if len(combinations) < count:
        raise ValueError(f"{family} defines only {len(combinations)} tuning trials")
    return sorted(
        combinations,
        key=lambda value: sha256_text(
            f"{master_seed}|tuning|{family}|{canonical_json(value)}"
        ),
    )[:count]


def build_tuning_manifest(config: Mapping[str, Any]) -> list[dict[str, Any]]:
    tuning = config["tuning"]
    count = int(tuning["trials_per_family"])
    master = int(config["scenario_design"]["master_seed"])
    candidates = {item["family"] for item in model_families(config)}
    families = {item["family"]: item for item in tunable_families(config)}
    rows: list[dict[str, Any]] = []
    for family_name, family in families.items():
        values = tuning["search_values"][family_name]
        trials = _fixed_trial_combinations(values, master, family_name, count)
        for index, parameters in enumerate(trials, start=1):
            rows.append(
                {
                    "family_id": family["id"],
                    "model_family": family_name,
                    "candidate_role": (
                        "primary_candidate"
                        if family_name in candidates
                        else "interpretation_control_not_eligible_to_win"
                    ),
                    "trial_id": f"{family['id']}-T{index:02d}",
                    "trial_order": index,
                    "parameters_json": canonical_json(parameters),
                    "selection_objective": tuning["objective"],
                    "tie_breaker": tuning["tie_breaker"],
                    "execution_status": "frozen_not_run",
                }
            )
    return rows


def build_scenario_schema(config: Mapping[str, Any]) -> dict[str, Any]:
    features = config["features"]
    targets = config["targets"]
    numeric = {
        name: {"type": "number"}
        for name in [*features["numeric"], *features["physics_derived"]]
    }
    categorical = {name: {"type": "string"} for name in features["categorical"]}
    outcome_properties: dict[str, Any] = {
        targets["primary_regression"]: {"type": "number"},
        targets["feasibility"]: {"type": "boolean"},
    }
    for name in targets["secondary"]:
        if name == "nonconverged":
            outcome_properties[name] = {"type": "boolean"}
        elif name == "violation_code":
            outcome_properties[name] = {"type": ["string", "null"]}
        elif name == "minimum_lunar_surface_altitude_km":
            outcome_properties[name] = {"type": ["number", "null"]}
        else:
            outcome_properties[name] = {"type": "number"}

    required_inputs = [*numeric, *categorical]
    gate4_accepted = (
        config["status"] == "gate_4_accepted_development_generation_authorized"
    )
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://github.com/taechasith/QMLforArtemisIV/tree/main/data/processed/simulator/scenario_schema.json",
        "title": "QMLforArtemisIV Phase 1 scenario record",
        "description": (
            "Schema only. Gate 4 creates no final-test feature or label payload. "
            "All records are simulated research scenarios, not telemetry."
        ),
        "type": "object",
        "additionalProperties": False,
        "required": [
            "scenario_id",
            "decision_set_id",
            "candidate_index",
            "group_id",
            "base_trajectory",
            "boundary_or_tail",
            "payload_version",
            "fidelity",
            "split",
            "inputs",
        ],
        "properties": {
            "scenario_id": {"type": "string", "pattern": "^F[012]-G[0-9]{2}-[0-9]{6}$"},
            "decision_set_id": {
                "type": "string",
                "pattern": "^F[012]-G[0-9]{2}-D[0-9]{6}$",
            },
            "candidate_index": {
                "type": "integer",
                "minimum": 1,
                "maximum": int(
                    config["scenario_design"]["decision_sets"]["candidates_per_set"]
                ),
            },
            "group_id": {"type": "string", "pattern": "^G[0-9]{2}$"},
            "base_trajectory": {"type": "string", "pattern": "^[CTV][0-9]{2}$"},
            "boundary_or_tail": {"type": "boolean"},
            "payload_version": {"type": "string", "pattern": "^d[0-9]{3}-v[0-9]+$"},
            "fidelity": {"enum": ["F0", "F1", "F2"]},
            "split": {"enum": list(config["scenario_design"]["split_fractions"])},
            "inputs": {
                "type": "object",
                "additionalProperties": False,
                "required": required_inputs,
                "properties": {**numeric, **categorical},
            },
            "outcomes": {
                "type": "object",
                "additionalProperties": False,
                "required": [targets["primary_regression"], targets["feasibility"]],
                "properties": outcome_properties,
            },
        },
        "x-gate4-access": {
            "development": (
                "generation and model development authorized"
                if gate4_accepted
                else "available only after Gate 4 acceptance"
            ),
            "uncertainty_calibration": "not for fitting, tuning, or feature selection",
            "in_distribution_final_test": "locked and not generated",
            "out_of_distribution_final_test": "locked and not generated",
        },
        "x-payload-rules": {
            "development_labeled_record": "outcomes required after authorized generation",
            "final_feature_record": "outcomes prohibited and stored separately",
            "final_label_record": "scenario_id plus outcomes in access-controlled evaluator storage",
        },
    }


def assert_split_access(split: str, purpose: str) -> None:
    """Enforce the lock even when a caller knows a final split name."""

    if split in FINAL_SPLITS:
        raise FinalTestAccessError(
            f"{split} is locked pending an explicit post-Gate-4 unlock commit"
        )
    if split == "uncertainty_calibration" and purpose in MODEL_SELECTION_PURPOSES:
        raise FinalTestAccessError(
            "The uncertainty-calibration split cannot be used for model selection"
        )
    if split != "development" and split != "uncertainty_calibration":
        raise ValueError(f"Unknown Gate 4 split: {split}")


def assert_no_final_payloads(path: Path | str) -> None:
    root = Path(path)
    if not root.exists():
        return
    files = [item for item in root.rglob("*") if item.is_file()]
    if files:
        rendered = ", ".join(str(item) for item in files[:5])
        raise FinalTestAccessError(
            f"Final-test payloads exist before approval: {rendered}"
        )


def manifest_counts(rows: Iterable[Mapping[str, Any]]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for row in rows:
        counts[str(row["split"])] += int(row["case_count"])
    return dict(counts)


def write_freeze_artifacts(
    config_path: Path | str,
    windows_path: Path | str,
    output_dir: Path | str,
) -> FreezeArtifacts:
    config = read_yaml(config_path)
    windows = read_csv(windows_path)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    scenario_rows = build_scenario_manifest(config, windows)
    final_rows = build_final_test_manifest(scenario_rows)
    seed_rows = build_seed_manifest(config)
    tuning_rows = build_tuning_manifest(config)
    schema = build_scenario_schema(config)

    artifacts = FreezeArtifacts(
        output / "scenario_manifest.csv",
        output / "final_test_manifest.csv",
        output / "seed_manifest.csv",
        output / "tuning_manifest.csv",
        output / "scenario_schema.json",
        output / "gate4_freeze_checksums.csv",
    )
    write_csv(artifacts.scenario_manifest, scenario_rows)
    write_csv(artifacts.final_test_manifest, final_rows)
    write_csv(artifacts.seed_manifest, seed_rows)
    write_csv(artifacts.tuning_manifest, tuning_rows)
    artifacts.scenario_schema.write_text(
        json.dumps(schema, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    accepted = config["status"] == "gate_4_accepted_development_generation_authorized"
    freeze_status = (
        "frozen_gate_4_accepted_final_test_separately_locked"
        if accepted
        else "frozen_candidate_pending_human_approval"
    )
    checksums = []
    for path in (
        artifacts.scenario_manifest,
        artifacts.final_test_manifest,
        artifacts.seed_manifest,
        artifacts.tuning_manifest,
        artifacts.scenario_schema,
    ):
        checksums.append(
            {
                "artifact": path.name,
                "size_bytes": path.stat().st_size,
                "sha256": sha256_file(path),
                "status": freeze_status,
            }
        )
    write_csv(artifacts.checksums, checksums)
    return artifacts
