#!/usr/bin/env python3
"""Generate D003 development/calibration scenarios with fail-closed validation."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import logging
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from openqfuel.ephemeris import JplEphemeris  # noqa: E402
from openqfuel.gate4 import (  # noqa: E402
    assert_no_final_payloads,
    assert_split_access,
    read_csv,
    read_yaml,
)
from openqfuel.oem import parse_oem, parse_utc  # noqa: E402
from openqfuel.scenarios import generate_group_records  # noqa: E402


PHASE1_CONFIG = ROOT / "configs/phase1_benchmark.yaml"
GENERATION_CONFIG = ROOT / "configs/scenario_generation.yaml"
UNCERTAINTY_CONFIG = ROOT / "configs/uncertainty_model.yaml"
CONSTRAINTS_CONFIG = ROOT / "configs/constraints.yaml"
SCHEMA_PATH = ROOT / "data/processed/simulator/scenario_schema.json"
MANIFEST_PATH = ROOT / "data/processed/simulator/scenario_manifest.csv"
EVENTS_PATH = ROOT / "data/artemis2_event_registry.csv"
CREW_SCHEDULE = ROOT / "configs/crew_schedule.yaml"
ACCELERATION_LIMITS = ROOT / "configs/human_acceleration_limits.yaml"
OUTPUT_ROOT = ROOT / "data/processed/simulator/scenarios"
LOCKED_ROOT = ROOT / "data/locked/phase1"
INVALID_AUDIT = OUTPUT_ROOT / "pre_d003_audit.csv"
LEDGER = OUTPUT_ROOT / "generation_ledger_v2.csv"
LEDGER_LOCK = OUTPUT_ROOT / "generation_ledger_v2.lock"
QUALIFICATION_SUMMARIES = {
    "F0": OUTPUT_ROOT / "post_d003_f0_audit_summary.json",
    "F1": OUTPUT_ROOT / "post_d003_f1_g01_audit_summary.json",
    "F2": OUTPUT_ROOT / "post_d003_f2_g01_audit_summary.json",
}
GENERATION_SOURCE_PATHS = (
    "configs/constraints.yaml",
    "configs/crew_schedule.yaml",
    "configs/dynamics.yaml",
    "configs/human_acceleration_limits.yaml",
    "configs/scenario_generation.yaml",
    "configs/phase1_benchmark.yaml",
    "configs/uncertainty_model.yaml",
    "data/artemis2_event_registry.csv",
    "data/source_registry.csv",
    "data/processed/simulator/scenario_manifest.csv",
    "data/processed/simulator/scenario_schema.json",
    "pyproject.toml",
    "scripts/generate_scenarios.py",
    "src/openqfuel/constraints.py",
    "src/openqfuel/dynamics.py",
    "src/openqfuel/ephemeris.py",
    "src/openqfuel/gate4.py",
    "src/openqfuel/oem.py",
    "src/openqfuel/scenarios.py",
    "uv.lock",
)

LEDGER_FIELDS = (
    "attempt_id",
    "payload_version",
    "config_sha256",
    "fidelity",
    "split",
    "group_id",
    "records",
    "elapsed_s",
    "sha256",
    "timestamp_utc",
    "schema_valid",
    "source_commit",
)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
LOG = logging.getLogger(__name__)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def resolve_source(root: Path, definition: Mapping[str, Any]) -> Path:
    path = root / str(definition["path"])
    if not path.is_file():
        raise FileNotFoundError(path)
    observed = sha256_file(path)
    expected = str(definition["sha256"]).lower()
    if observed != expected:
        raise ValueError(
            f"Source checksum mismatch for {path}: {observed} != {expected}"
        )
    return path


def event_epoch(event_id: str) -> datetime:
    rows = read_csv(EVENTS_PATH)
    matching = [row for row in rows if row["event_id"] == event_id]
    if len(matching) != 1 or not matching[0]["actual_utc"]:
        raise ValueError(f"Expected one actual UTC for event {event_id}")
    return parse_utc(matching[0]["actual_utc"])


def output_path(row: Mapping[str, str]) -> Path:
    return OUTPUT_ROOT / row["fidelity"] / row["split"] / f"{row['group_id']}.jsonl"


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number}: {exc}") from exc
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_number}: record is not an object")
            records.append(value)
    return records


def validate_records(
    records: list[dict[str, Any]],
    row: Mapping[str, str],
    validator: Draft202012Validator,
    payload_version: str,
) -> None:
    expected_count = int(row["case_count"])
    if len(records) != expected_count:
        raise ValueError(
            f"{row['group_id']} produced {len(records)} records, expected {expected_count}"
        )
    expected_ids = {
        f"{row['fidelity']}-{row['group_id']}-{index:06d}"
        for index in range(1, expected_count + 1)
    }
    observed_ids: set[str] = set()
    decision_sets: dict[str, set[int]] = {}
    boundary_ids: list[str] = []
    expected_outcomes = set(validator.schema["properties"]["outcomes"]["properties"])
    for index, record in enumerate(records, start=1):
        errors = list(validator.iter_errors(record))
        if errors:
            path = ".".join(str(part) for part in errors[0].absolute_path)
            raise ValueError(
                f"{row['group_id']} record {index} schema error at {path or '<root>'}: "
                f"{errors[0].message}"
            )
        if record["payload_version"] != payload_version:
            raise ValueError("Payload version differs from generation config")
        if set(record.get("outcomes", {})) != expected_outcomes:
            raise ValueError(f"{record['scenario_id']} has incomplete outcome fields")
        for field in ("fidelity", "split", "group_id", "base_trajectory"):
            if record[field] != row[field]:
                raise ValueError(f"{record['scenario_id']} has incorrect {field}")
        observed_ids.add(record["scenario_id"])
        expected_set_index = (index - 1) // int(row["candidates_per_decision_set"]) + 1
        expected_candidate_index = (index - 1) % int(
            row["candidates_per_decision_set"]
        ) + 1
        expected_set_id = (
            f"{row['fidelity']}-{row['group_id']}-D{expected_set_index:06d}"
        )
        if record["decision_set_id"] != expected_set_id:
            raise ValueError(f"{record['scenario_id']} has incorrect decision_set_id")
        if int(record["candidate_index"]) != expected_candidate_index:
            raise ValueError(f"{record['scenario_id']} has incorrect candidate_index")
        decision_sets.setdefault(record["decision_set_id"], set()).add(
            int(record["candidate_index"])
        )
        if record["boundary_or_tail"]:
            boundary_ids.append(record["scenario_id"])
    if observed_ids != expected_ids:
        raise ValueError(f"{row['group_id']} scenario identity set is incomplete")
    expected_sets = int(row["decision_set_count"])
    if len(decision_sets) != expected_sets:
        raise ValueError(f"{row['group_id']} decision-set count is incorrect")
    if any(indices != {1, 2, 3, 4, 5} for indices in decision_sets.values()):
        raise ValueError(f"{row['group_id']} has invalid candidate membership")
    if len(boundary_ids) != int(row["boundary_or_tail_case_count"]):
        raise ValueError(f"{row['group_id']} has incorrect boundary/tail count")
    boundary_commitment = hashlib.sha256("\n".join(boundary_ids).encode()).hexdigest()
    if boundary_commitment != row["boundary_id_commitment"]:
        raise ValueError(f"{row['group_id']} boundary/tail commitment mismatch")


def invalid_replacement_authorized(row: Mapping[str, str]) -> bool:
    if not INVALID_AUDIT.exists():
        return False
    for audit in read_csv(INVALID_AUDIT):
        if (
            audit["fidelity"] == row["fidelity"]
            and audit["split"] == row["split"]
            and audit["group_id"] == row["group_id"]
            and audit["audit_status"] == "invalid"
        ):
            return True
    return False


def write_atomic(records: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True, separators=(",", ":")))
            handle.write("\n")
    temporary.replace(path)


def current_commit() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


@contextmanager
def exclusive_file_lock(
    lock_path: Path, timeout_s: float = 60.0, stale_after_s: float = 300.0
):
    deadline = time.monotonic() + timeout_s
    descriptor: int | None = None
    while descriptor is None:
        try:
            descriptor = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(
                descriptor,
                f"pid={os.getpid()} utc={datetime.now(timezone.utc).isoformat()}".encode(),
            )
        except FileExistsError:
            try:
                age_s = time.time() - lock_path.stat().st_mtime
                if age_s > stale_after_s:
                    lock_path.unlink()
                    continue
            except FileNotFoundError:
                continue
            if time.monotonic() >= deadline:
                raise TimeoutError(f"Timed out waiting for ledger lock: {lock_path}")
            time.sleep(0.05)
    try:
        yield
    finally:
        os.close(descriptor)
        lock_path.unlink(missing_ok=True)


def assert_generation_sources_committed() -> None:
    result = subprocess.run(
        ["git", "status", "--porcelain=v1", "--", *GENERATION_SOURCE_PATHS],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    if result.stdout.strip():
        raise RuntimeError(
            "Generation source/config files differ from HEAD; commit the D003 repair "
            "before writing scientific payloads"
        )


def append_ledger(
    row: Mapping[str, str],
    path: Path,
    records: int,
    elapsed_s: float,
    config_hash: str,
    payload_version: str,
) -> None:
    timestamp = datetime.now(timezone.utc).isoformat()
    attempt_id = hashlib.sha256(
        f"{payload_version}|{row['fidelity']}|{row['split']}|{row['group_id']}|{timestamp}".encode()
    ).hexdigest()[:16]
    ledger_row = {
        "attempt_id": attempt_id,
        "payload_version": payload_version,
        "config_sha256": config_hash,
        "fidelity": row["fidelity"],
        "split": row["split"],
        "group_id": row["group_id"],
        "records": records,
        "elapsed_s": f"{elapsed_s:.3f}",
        "sha256": sha256_file(path),
        "timestamp_utc": timestamp,
        "schema_valid": "true",
        "source_commit": current_commit(),
    }
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    with exclusive_file_lock(LEDGER_LOCK):
        exists = LEDGER.exists()
        with LEDGER.open("a", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(
                handle, fieldnames=LEDGER_FIELDS, lineterminator="\n"
            )
            if not exists:
                writer.writeheader()
            writer.writerow(ledger_row)


def assert_parallel_qualification(fidelity: str) -> None:
    path = QUALIFICATION_SUMMARIES[fidelity]
    if not path.is_file():
        raise RuntimeError(
            f"Parallel {fidelity} generation requires a preserved first-group audit: {path}"
        )
    summary = json.loads(path.read_text(encoding="utf-8"))
    if summary.get("status") != "valid" or int(summary.get("invalid_groups", 1)):
        raise RuntimeError(f"Parallel {fidelity} generation is blocked by {path}")


def _campaign_child(
    row: Mapping[str, str], args: argparse.Namespace
) -> tuple[Mapping[str, str], subprocess.CompletedProcess[str]]:
    command = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--fidelity",
        row["fidelity"],
        "--split",
        row["split"],
        "--group",
        row["group_id"],
    ]
    if args.resume:
        command.append("--resume")
    if args.replace_invalid:
        command.append("--replace-invalid")
    environment = os.environ.copy()
    for variable in (
        "OMP_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "MKL_NUM_THREADS",
        "NUMEXPR_NUM_THREADS",
    ):
        environment[variable] = "1"
    result = subprocess.run(
        command,
        cwd=ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    return row, result


def run_parallel_campaign(
    rows: list[dict[str, str]], args: argparse.Namespace, jobs: int
) -> int:
    failures = 0
    with ThreadPoolExecutor(max_workers=jobs) as executor:
        futures = [executor.submit(_campaign_child, row, args) for row in rows]
        for future in as_completed(futures):
            row, result = future.result()
            label = f"{row['fidelity']} {row['split']} {row['group_id']}"
            if result.stderr.strip():
                for line in result.stderr.strip().splitlines():
                    LOG.info("[%s] %s", label, line)
            if result.stdout.strip():
                for line in result.stdout.strip().splitlines():
                    LOG.info("[%s] %s", label, line)
            if result.returncode:
                failures += 1
                LOG.error("FAILED %s with exit code %s", label, result.returncode)
            else:
                LOG.info("COMPLETE %s", label)
    return 1 if failures else 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fidelity", choices=("F0", "F1", "F2"))
    parser.add_argument("--split", choices=("development", "uncertainty_calibration"))
    parser.add_argument("--group")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--replace-invalid", action="store_true")
    parser.add_argument("--continue-after-first", action="store_true")
    parser.add_argument("--jobs", type=int, default=1)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    assert_no_final_payloads(LOCKED_ROOT)
    phase1 = read_yaml(PHASE1_CONFIG)
    generation = read_yaml(GENERATION_CONFIG)
    uncertainty = read_yaml(UNCERTAINTY_CONFIG)
    constraints = read_yaml(CONSTRAINTS_CONFIG)
    if phase1["status"] != "gate_4_accepted_development_generation_authorized":
        raise RuntimeError("Gate 4 development generation is not authorized")
    if generation["status"] != "d003_repair_authorized_pre_model_fit":
        raise RuntimeError("D003 generator repair is not authorized")

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    payload_version = str(generation["payload_version"])
    config_hash = sha256_file(GENERATION_CONFIG)
    rows = [
        row
        for row in read_csv(MANIFEST_PATH)
        if row["split"] in {"development", "uncertainty_calibration"}
        and (args.fidelity is None or row["fidelity"] == args.fidelity)
        and (args.split is None or row["split"] == args.split)
        and (args.group is None or row["group_id"] == args.group)
    ]
    if not rows:
        raise RuntimeError("No unlocked manifest rows match the requested filters")
    for row in rows:
        assert_split_access(row["split"], "generation")

    if args.dry_run:
        for row in rows:
            LOG.info(
                "PLAN %s %s %s: %s rows -> %s",
                row["fidelity"],
                row["split"],
                row["group_id"],
                row["case_count"],
                output_path(row).relative_to(ROOT),
            )
        return 0

    if args.jobs < 1:
        raise ValueError("--jobs must be positive")
    worker_ceiling = int(generation["compute"]["post_audit_worker_ceiling"])
    if args.jobs > worker_ceiling:
        raise ValueError(f"--jobs exceeds the frozen ceiling of {worker_ceiling}")

    if args.check:
        failures = 0
        for row in rows:
            path = output_path(row)
            try:
                validate_records(read_jsonl(path), row, validator, payload_version)
                LOG.info("VALID %s", path.relative_to(ROOT))
            except Exception as exc:
                failures += 1
                LOG.error("INVALID %s: %s", path.relative_to(ROOT), exc)
        return 1 if failures else 0

    assert_generation_sources_committed()

    if args.jobs > 1:
        if not args.continue_after_first:
            raise RuntimeError(
                "Parallel scale-up requires --continue-after-first after qualification"
            )
        fidelities = {row["fidelity"] for row in rows}
        if len(fidelities) != 1:
            raise RuntimeError("Parallel scale-up must select exactly one fidelity")
        fidelity = next(iter(fidelities))
        assert_parallel_qualification(fidelity)
        return run_parallel_campaign(rows, args, args.jobs)

    oem_path = resolve_source(ROOT, generation["sources"]["qualified_oem"])
    oem = parse_oem(oem_path)
    target_epoch = parse_utc(oem.header["USEABLE_STOP_TIME"])
    tli_epoch = event_epoch("E002")
    lunar_flyby_epoch = event_epoch("E006")
    ephemeris_path = resolve_source(ROOT, generation["sources"]["de440s"])
    ephemeris = JplEphemeris(ephemeris_path)

    processed = 0
    for row in rows:
        path = output_path(row)
        if path.exists():
            try:
                validate_records(read_jsonl(path), row, validator, payload_version)
                if args.resume:
                    LOG.info("SKIP valid payload %s", path.relative_to(ROOT))
                    continue
                raise FileExistsError(
                    f"Valid payload already exists: {path}; use --resume"
                )
            except FileExistsError:
                raise
            except Exception as exc:
                if not args.replace_invalid:
                    raise RuntimeError(
                        f"Existing payload is invalid ({exc}); --replace-invalid required"
                    ) from exc
                if not invalid_replacement_authorized(row):
                    raise RuntimeError(
                        f"No preserved invalid audit authorizes replacement of {path}"
                    ) from exc
                LOG.warning(
                    "Replacing audited invalid payload %s", path.relative_to(ROOT)
                )

        started = time.monotonic()
        records = generate_group_records(
            row,
            phase1,
            generation,
            uncertainty,
            constraints,
            oem,
            ephemeris,
            tli_epoch,
            target_epoch,
            lunar_flyby_epoch,
            CREW_SCHEDULE,
            ACCELERATION_LIMITS,
        )
        validate_records(records, row, validator, payload_version)
        write_atomic(records, path)
        validate_records(read_jsonl(path), row, validator, payload_version)
        elapsed = time.monotonic() - started
        append_ledger(
            row,
            path,
            len(records),
            elapsed,
            config_hash,
            payload_version,
        )
        LOG.info(
            "WROTE %s rows to %s in %.1fs",
            len(records),
            path.relative_to(ROOT),
            elapsed,
        )
        processed += 1
        if not args.continue_after_first and len(rows) > 1:
            LOG.warning(
                "Stopped after one group for the required full audit; "
                "rerun with --continue-after-first only after review"
            )
            break
    return 0 if processed else 0


if __name__ == "__main__":
    raise SystemExit(main())
