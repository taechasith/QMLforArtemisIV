#!/usr/bin/env python3
"""Audit generated scenario payloads without modifying them."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from statistics import median
from typing import Any, Iterable, Mapping

import numpy as np
from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from openqfuel.gate4 import FINAL_SPLITS, read_csv, read_yaml  # noqa: E402


SCENARIO_ROOT = ROOT / "data/processed/simulator/scenarios"
MANIFEST_PATH = ROOT / "data/processed/simulator/scenario_manifest.csv"
SCHEMA_PATH = ROOT / "data/processed/simulator/scenario_schema.json"
UNCERTAINTY_PATH = ROOT / "configs/uncertainty_model.yaml"
LEDGER_PATH = SCENARIO_ROOT / "generation_ledger.csv"
DEFAULT_AUDIT_PATH = SCENARIO_ROOT / "pre_d003_audit.csv"
DEFAULT_SUMMARY_PATH = SCENARIO_ROOT / "pre_d003_audit_summary.json"


FIELDS = (
    "audit_label",
    "fidelity",
    "split",
    "group_id",
    "base_trajectory",
    "uncertainty_family",
    "expected_records",
    "observed_records",
    "expected_decision_sets",
    "observed_decision_sets",
    "schema_error_records",
    "relationship_error_records",
    "nonfinite_records",
    "feasible_records",
    "feasibility_rate",
    "no_reference_feasible_sets",
    "no_reference_feasible_rate",
    "nonconverged_records",
    "median_robust_delta_v_m_s",
    "median_terminal_position_error_km",
    "p95_terminal_position_error_km",
    "median_terminal_velocity_error_m_s",
    "uncertainty_conformance",
    "uncertainty_notes",
    "payload_sha256",
    "latest_ledger_sha256",
    "ledger_matches_payload",
    "audit_status",
    "error_example",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number}: invalid JSON: {exc}") from exc
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_number}: record is not an object")
            records.append(value)
    return records


def latest_ledger_hashes(path: Path) -> dict[tuple[str, str, str], str]:
    if not path.exists():
        return {}
    latest: dict[tuple[str, str, str], str] = {}
    for row in read_csv(path):
        latest[(row["fidelity"], row["split"], row["group_id"])] = row["sha256"]
    return latest


def numeric_values(record: Mapping[str, Any]) -> Iterable[float]:
    for section in (record.get("inputs", {}), record.get("outcomes", {})):
        if not isinstance(section, Mapping):
            continue
        for value in section.values():
            if isinstance(value, bool) or value is None or isinstance(value, str):
                continue
            try:
                yield float(value)
            except (TypeError, ValueError):
                yield math.nan


def expected_uncertainty_scales(config: Mapping[str, Any]) -> dict[str, float]:
    navigation = config["initial_navigation_uncertainty_3sigma"]
    execution = config["thruster_execution_3sigma"]
    return {
        "nav_position_km": float(navigation["position_km"]) / 3.0,
        "nav_velocity_m_s": float(navigation["velocity_m_s"]) / 3.0,
        "thrust_fraction": float(execution["scale_factor_ppm"]) / 3.0e6,
        "pointing_deg": float(execution["misalignment_deg"]) / 3.0,
    }


def relative_scale_ok(
    observed: float, expected: float, tolerance: float = 0.25
) -> bool:
    if expected == 0.0:
        return observed == 0.0
    return abs(observed / expected - 1.0) <= tolerance


def uncertainty_audit(
    records: list[dict[str, Any]], family: str, config: Mapping[str, Any]
) -> tuple[bool, str]:
    scales = expected_uncertainty_scales(config)
    first_by_set: dict[str, Mapping[str, Any]] = {}
    for record in records:
        first_by_set.setdefault(record["decision_set_id"], record["inputs"])
    set_inputs = list(first_by_set.values())

    nav_position = np.asarray(
        [
            component
            for inputs in set_inputs
            for component in (
                inputs["navigation_dx_km"],
                inputs["navigation_dy_km"],
                inputs["navigation_dz_km"],
            )
        ],
        dtype=float,
    )
    nav_velocity = np.asarray(
        [
            component
            for inputs in set_inputs
            for component in (
                inputs["navigation_dvx_m_s"],
                inputs["navigation_dvy_m_s"],
                inputs["navigation_dvz_m_s"],
            )
        ],
        dtype=float,
    )
    thrust = np.asarray(
        [record["inputs"]["thrust_scale"] - 1.0 for record in records], dtype=float
    )
    pointing = np.asarray(
        [record["inputs"]["pointing_bias_deg"] for record in records], dtype=float
    )
    observed = {
        "nav_position_km": float(np.std(nav_position, ddof=1)),
        "nav_velocity_m_s": float(np.std(nav_velocity, ddof=1)),
        "thrust_fraction": float(np.std(thrust, ddof=1)),
        "pointing_deg": float(np.std(pointing, ddof=1)),
    }

    navigation_active = family in {"U1", "U3", "U4"}
    execution_active = family in {"U2", "U3", "U4"}
    checks = {
        "nav_position_km": (
            relative_scale_ok(observed["nav_position_km"], scales["nav_position_km"])
            if navigation_active
            else observed["nav_position_km"] == 0.0
        ),
        "nav_velocity_m_s": (
            relative_scale_ok(observed["nav_velocity_m_s"], scales["nav_velocity_m_s"])
            if navigation_active
            else observed["nav_velocity_m_s"] == 0.0
        ),
        "thrust_fraction": (
            relative_scale_ok(observed["thrust_fraction"], scales["thrust_fraction"])
            if execution_active
            else observed["thrust_fraction"] == 0.0
        ),
        "pointing_deg": (
            relative_scale_ok(observed["pointing_deg"], scales["pointing_deg"])
            if execution_active
            else observed["pointing_deg"] == 0.0
        ),
    }
    if family == "U4":
        checks["bounded_nav_position"] = bool(
            np.max(np.abs(nav_position)) <= 3.0 * scales["nav_position_km"] + 1e-12
        )
        checks["bounded_nav_velocity"] = bool(
            np.max(np.abs(nav_velocity)) <= 3.0 * scales["nav_velocity_m_s"] + 1e-12
        )
        checks["bounded_thrust"] = bool(
            np.max(np.abs(thrust)) <= 3.0 * scales["thrust_fraction"] + 1e-12
        )
        checks["bounded_pointing"] = bool(
            np.max(np.abs(pointing)) <= 3.0 * scales["pointing_deg"] + 1e-12
        )

    notes = ";".join(
        [
            *(f"observed_{name}={value:.9g}" for name, value in observed.items()),
            *(f"failed_{name}" for name, passed in checks.items() if not passed),
        ]
    )
    return all(checks.values()), notes


def relationship_errors(
    records: list[dict[str, Any]], manifest: Mapping[str, str]
) -> tuple[int, str]:
    errors = 0
    example = ""
    candidates_per_set = int(manifest["candidates_per_decision_set"])
    sets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    observed_ids: set[str] = set()
    boundary_ids: list[str] = []
    for record_index, record in enumerate(records, start=1):
        expected = {
            "fidelity": manifest["fidelity"],
            "split": manifest["split"],
            "group_id": manifest["group_id"],
            "base_trajectory": manifest["base_trajectory"],
        }
        bad = [name for name, value in expected.items() if record.get(name) != value]
        if bad:
            errors += 1
            example = example or f"metadata mismatch: {','.join(bad)}"
        scenario_id = str(record.get("scenario_id"))
        if scenario_id in observed_ids:
            errors += 1
            example = example or f"duplicate scenario ID: {scenario_id}"
        observed_ids.add(scenario_id)
        expected_set_index = (record_index - 1) // candidates_per_set + 1
        expected_candidate = (record_index - 1) % candidates_per_set + 1
        expected_set_id = (
            f"{manifest['fidelity']}-{manifest['group_id']}-D{expected_set_index:06d}"
        )
        if (
            record.get("decision_set_id") != expected_set_id
            or record.get("candidate_index") != expected_candidate
        ):
            errors += 1
            example = example or f"identity relationship mismatch: {scenario_id}"
        if record.get("boundary_or_tail") is True:
            boundary_ids.append(scenario_id)
        sets[str(record.get("decision_set_id"))].append(record)

    for set_id, members in sets.items():
        indices = sorted(member.get("candidate_index") for member in members)
        if len(members) != candidates_per_set or indices != list(
            range(1, candidates_per_set + 1)
        ):
            errors += len(members)
            example = example or f"invalid decision set membership: {set_id}"
    boundary_field_present = all("boundary_or_tail" in record for record in records)
    if boundary_field_present:
        commitment = hashlib.sha256("\n".join(boundary_ids).encode()).hexdigest()
        if (
            len(boundary_ids) != int(manifest["boundary_or_tail_case_count"])
            or commitment != manifest["boundary_id_commitment"]
        ):
            errors += len(records)
            example = example or "boundary/tail commitment mismatch"
    return errors, example


def percentile(values: list[float], quantile: float) -> float:
    return float(np.quantile(np.asarray(values, dtype=float), quantile))


def audit_group(
    path: Path,
    manifest: Mapping[str, str],
    validator: Draft202012Validator,
    uncertainty: Mapping[str, Any],
    ledger_hash: str,
    label: str,
) -> dict[str, Any]:
    records = load_jsonl(path)
    schema_error_records = 0
    error_example = ""
    expected_outcomes = set(
        validator.schema["properties"]["outcomes"]["properties"]
    )
    for record in records:
        errors = list(validator.iter_errors(record))
        outcome_fields_valid = set(record.get("outcomes", {})) == expected_outcomes
        if errors or not outcome_fields_valid:
            schema_error_records += 1
            error_example = error_example or (
                errors[0].message if errors else "incomplete outcome fields"
            )

    relationship_error_records, relationship_example = relationship_errors(
        records, manifest
    )
    error_example = error_example or relationship_example
    nonfinite_records = sum(
        not all(math.isfinite(value) for value in numeric_values(record))
        for record in records
    )
    sets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        sets[record["decision_set_id"]].append(record)
    no_reference = sum(
        not any(
            member["outcomes"]["independently_propagated_feasible"]
            for member in members
        )
        for members in sets.values()
    )
    feasible = sum(
        bool(record["outcomes"]["independently_propagated_feasible"])
        for record in records
    )
    nonconverged = sum(bool(record["outcomes"]["nonconverged"]) for record in records)
    uncertainty_ok, uncertainty_notes = uncertainty_audit(
        records, manifest["uncertainty_family"], uncertainty
    )
    position_errors = [
        float(record["outcomes"]["terminal_position_error_km"]) for record in records
    ]
    velocity_errors = [
        float(record["outcomes"]["terminal_velocity_error_m_s"]) for record in records
    ]
    robust_cost = [
        float(record["outcomes"]["robust_total_correction_delta_v_m_s"])
        for record in records
    ]
    payload_hash = sha256_file(path)
    expected_records = int(manifest["case_count"])
    expected_sets = int(manifest["decision_set_count"])
    valid = all(
        (
            len(records) == expected_records,
            len(sets) == expected_sets,
            schema_error_records == 0,
            relationship_error_records == 0,
            nonfinite_records == 0,
            uncertainty_ok,
            bool(ledger_hash),
            ledger_hash == payload_hash,
        )
    )
    return {
        "audit_label": label,
        "fidelity": manifest["fidelity"],
        "split": manifest["split"],
        "group_id": manifest["group_id"],
        "base_trajectory": manifest["base_trajectory"],
        "uncertainty_family": manifest["uncertainty_family"],
        "expected_records": expected_records,
        "observed_records": len(records),
        "expected_decision_sets": expected_sets,
        "observed_decision_sets": len(sets),
        "schema_error_records": schema_error_records,
        "relationship_error_records": relationship_error_records,
        "nonfinite_records": nonfinite_records,
        "feasible_records": feasible,
        "feasibility_rate": round(feasible / len(records), 9),
        "no_reference_feasible_sets": no_reference,
        "no_reference_feasible_rate": round(no_reference / len(sets), 9),
        "nonconverged_records": nonconverged,
        "median_robust_delta_v_m_s": round(median(robust_cost), 9),
        "median_terminal_position_error_km": round(median(position_errors), 9),
        "p95_terminal_position_error_km": round(percentile(position_errors, 0.95), 9),
        "median_terminal_velocity_error_m_s": round(median(velocity_errors), 9),
        "uncertainty_conformance": str(uncertainty_ok).lower(),
        "uncertainty_notes": uncertainty_notes,
        "payload_sha256": payload_hash,
        "latest_ledger_sha256": ledger_hash,
        "ledger_matches_payload": str(ledger_hash == payload_hash).lower(),
        "audit_status": "valid" if valid else "invalid",
        "error_example": error_example,
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", default="pre_d003")
    parser.add_argument("--output", type=Path, default=DEFAULT_AUDIT_PATH)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY_PATH)
    parser.add_argument("--ledger", type=Path, default=LEDGER_PATH)
    parser.add_argument("--fidelity", choices=("F0", "F1", "F2"))
    parser.add_argument("--split", choices=("development", "uncertainty_calibration"))
    parser.add_argument("--group")
    parser.add_argument("--strict", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    uncertainty = read_yaml(UNCERTAINTY_PATH)
    ledger = latest_ledger_hashes(args.ledger)
    manifest_rows = [
        row
        for row in read_csv(MANIFEST_PATH)
        if (args.fidelity is None or row["fidelity"] == args.fidelity)
        and (args.split is None or row["split"] == args.split)
        and (args.group is None or row["group_id"] == args.group)
    ]

    rows: list[dict[str, Any]] = []
    for manifest in manifest_rows:
        if manifest["split"] in FINAL_SPLITS:
            continue
        path = (
            SCENARIO_ROOT
            / manifest["fidelity"]
            / manifest["split"]
            / f"{manifest['group_id']}.jsonl"
        )
        if not path.exists():
            continue
        key = (manifest["fidelity"], manifest["split"], manifest["group_id"])
        rows.append(
            audit_group(
                path,
                manifest,
                validator,
                uncertainty,
                ledger.get(key, ""),
                args.label,
            )
        )
    rows.sort(key=lambda row: (row["fidelity"], row["split"], row["group_id"]))
    if not rows:
        raise RuntimeError("No generated development/calibration payloads were found")
    write_csv(args.output, rows)

    totals = {
        "audit_label": args.label,
        "groups_audited": len(rows),
        "valid_groups": sum(row["audit_status"] == "valid" for row in rows),
        "invalid_groups": sum(row["audit_status"] != "valid" for row in rows),
        "records_audited": sum(int(row["observed_records"]) for row in rows),
        "schema_error_records": sum(int(row["schema_error_records"]) for row in rows),
        "relationship_error_records": sum(
            int(row["relationship_error_records"]) for row in rows
        ),
        "nonfinite_records": sum(int(row["nonfinite_records"]) for row in rows),
        "feasible_records": sum(int(row["feasible_records"]) for row in rows),
        "decision_sets": sum(int(row["observed_decision_sets"]) for row in rows),
        "no_reference_feasible_sets": sum(
            int(row["no_reference_feasible_sets"]) for row in rows
        ),
        "final_test_payloads_read": 0,
        "status": "valid"
        if all(row["audit_status"] == "valid" for row in rows)
        else "invalid",
    }
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(
        json.dumps(totals, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(totals, sort_keys=True))
    return 1 if args.strict and totals["status"] != "valid" else 0


if __name__ == "__main__":
    raise SystemExit(main())
