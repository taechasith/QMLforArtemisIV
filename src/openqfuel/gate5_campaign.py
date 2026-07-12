"""Resumable campaign orchestration for the accepted Gate 5 runner."""

from __future__ import annotations

import csv
import hashlib
import importlib.metadata
import json
import platform
import subprocess
import sys
import time
import traceback
from concurrent.futures import ProcessPoolExecutor, as_completed
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from threadpoolctl import threadpool_limits

try:  # POSIX and Windows both remain supported by the published runner.
    import fcntl
except ImportError:  # pragma: no cover - exercised on Windows
    fcntl = None  # type: ignore[assignment]
    import msvcrt

from .gate4 import read_csv, read_yaml, sha256_file
from .gate5 import (
    QML_FAMILIES,
    RUNNER_ACCEPTED_STATUS,
    _clean_source_commit,
    execute_trial,
    gate5_preflight,
    initial_execution_plan,
    load_trial,
    rank_rung_summaries,
    trial_seed,
    validate_development_output_path,
    write_csv_rows,
)


QML_IDS = ("Q01", "Q02", "Q03")
CANDIDATE_IDS = ("C01", "C02", "C03", "C04", "C05", "C06", *QML_IDS)
CONTROL_VIEWS = (("A01", "primary"), ("C05", "compressed_c05"))
RUNG_RETAIN = {128: 15, 256: 8, 512: 4}
RUNG_SEQUENCE = (128, 256, 512, 1024)


def expected_scientific_versions() -> dict[str, str]:
    python_312_or_later = sys.version_info >= (3, 12)
    return {
        "numpy": "2.5.1" if python_312_or_later else "2.4.6",
        "scipy": "1.18.0" if python_312_or_later else "1.17.1",
        "scikit-learn": "1.9.0",
        "PyYAML": "6.0.3",
        "threadpoolctl": "3.6.0",
        "jplephem": "2.24",
        "jsonschema": "4.26.0",
    }


def verify_scientific_environment(root: Path) -> dict[str, str]:
    expected = expected_scientific_versions()
    actual = {name: importlib.metadata.version(name) for name in expected}
    mismatches = {
        name: {"expected": expected[name], "actual": actual[name]}
        for name in expected
        if actual[name] != expected[name]
    }
    if mismatches:
        raise PermissionError(
            "Scientific environment differs from uv.lock; run "
            f"`uv sync --frozen --extra figures`: {mismatches}"
        )
    return actual


@dataclass(frozen=True)
class CampaignTask:
    """One signed call to :func:`execute_trial`."""

    stage: str
    family_id: str
    model_family: str
    trial_id: str
    trial_order: int
    view: str = "primary"
    rung_samples: int | None = None
    matched_qubits: int | None = None
    seed_index: int | None = None
    candidate_role: str = "primary_candidate"
    control_for: str = ""
    advancement_basis: str = "candidate"

    @property
    def key(self) -> str:
        rung = self.rung_samples if self.rung_samples is not None else "full"
        qubits = self.matched_qubits if self.matched_qubits is not None else "raw"
        seed = self.seed_index if self.seed_index is not None else self.trial_order
        return f"{self.trial_id}__{self.view}__r{rung}__q{qubits}__s{seed:02d}"


def _head(root: Path) -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True
    ).strip()


@contextmanager
def _file_lock(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+", encoding="utf-8") as handle:
        try:
            if fcntl is not None:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            else:  # pragma: no cover - exercised on Windows
                handle.seek(0, 2)
                if handle.tell() == 0:
                    handle.write("\0")
                    handle.flush()
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        except (BlockingIOError, OSError) as error:
            raise RuntimeError(f"Campaign work is already locked: {path}") from error
        try:
            yield
        finally:
            if fcntl is not None:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            else:  # pragma: no cover - exercised on Windows
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)


def campaign_lock(output_root: Path):
    return _file_lock(output_root / ".campaign.lock")


def _atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def _freeze_json(path: Path, value: Mapping[str, Any]) -> None:
    if path.is_file():
        existing = json.loads(path.read_text(encoding="utf-8"))
        if existing != value:
            raise PermissionError(f"Frozen campaign JSON differs on resume: {path}")
        return
    _atomic_json(path, value)


def _write_union_csv(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    if not rows:
        raise ValueError("Cannot write an empty CSV")
    leading = list(rows[0])
    trailing = sorted({key for row in rows for key in row if key not in leading})
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[*leading, *trailing],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


def _write_rows_or_empty_header(
    path: Path,
    rows: Sequence[Mapping[str, Any]],
    empty_fields: Sequence[str],
) -> None:
    if rows:
        _write_union_csv(path, rows)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=list(empty_fields), lineterminator="\n"
        )
        writer.writeheader()
    temporary.replace(path)


def _freeze_csv(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    if path.is_file():
        with path.open(encoding="utf-8") as handle:
            existing = list(csv.DictReader(handle))
        if _normalized_rows(existing) != _normalized_rows(rows):
            raise PermissionError(f"Frozen campaign CSV differs on resume: {path}")
        return
    _write_union_csv(path, rows)


def _authorization_sidecar(path: Path) -> Path:
    return path.with_suffix(path.suffix + ".json")


def freeze_task_authorization(
    root: Path,
    path: Path,
    tasks: Sequence[CampaignTask],
    parent_digest: str,
) -> None:
    raw = [asdict(task) for task in tasks]
    digest = hashlib.sha256(
        json.dumps(raw, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    _freeze_csv(path, raw)
    _freeze_json(
        _authorization_sidecar(path),
        {
            "source_commit": _head(root),
            "parent_digest": parent_digest,
            "task_count": len(tasks),
            "task_sha256": digest,
            "tasks": raw,
        },
    )


def _trial_rows(root: Path) -> dict[tuple[str, int], dict[str, str]]:
    rows = read_csv(root / "data/processed/simulator/tuning_manifest.csv")
    return {(row["family_id"], int(row["trial_order"])): row for row in rows}


def initial_campaign_tasks(root: Path) -> list[CampaignTask]:
    """Return the frozen first rung, including exactly matched control repeats."""

    return [
        CampaignTask(
            stage="tuning",
            family_id=str(row["family_id"]),
            model_family=str(row["model_family"]),
            trial_id=str(row["trial_id"]),
            trial_order=int(row["trial_order"]),
            view=str(row["view"]),
            rung_samples=(
                None if row["rung_samples"] in (None, "") else int(row["rung_samples"])
            ),
            matched_qubits=(
                int(row["effective_qubits"])
                if row["family_id"] in QML_IDS
                else (
                    None
                    if row["matched_qubits"] in (None, "")
                    else int(row["matched_qubits"])
                )
            ),
            candidate_role=str(row["candidate_role"]),
            control_for=str(row.get("control_for", "")),
            advancement_basis=str(row["advancement_basis"]),
        )
        for row in initial_execution_plan(root)
    ]


def matched_control_tasks(
    root: Path,
    qml_tasks: Sequence[CampaignTask],
    stage: str,
    seed_index: int | None = None,
) -> list[CampaignTask]:
    """Repeat frozen controls at every QML trial-order/dimension pair."""

    if not qml_tasks:
        return []
    rows = _trial_rows(root)
    paired: dict[tuple[int, int], set[str]] = {}
    for task in qml_tasks:
        if task.family_id not in QML_IDS or task.matched_qubits is None:
            raise ValueError("Matched controls require QML task dimensions")
        paired.setdefault((task.trial_order, task.matched_qubits), set()).add(
            task.family_id
        )

    tasks: list[CampaignTask] = []
    for (trial_order, qubits), qml_ids in sorted(paired.items()):
        for family_id, view in CONTROL_VIEWS:
            row = rows[(family_id, trial_order)]
            tasks.append(
                CampaignTask(
                    stage=stage,
                    family_id=family_id,
                    model_family=row["model_family"],
                    trial_id=row["trial_id"],
                    trial_order=trial_order,
                    view=view,
                    rung_samples=qml_tasks[0].rung_samples,
                    matched_qubits=qubits,
                    seed_index=seed_index,
                    candidate_role="interpretation_control_not_eligible_to_win",
                    control_for=";".join(sorted(qml_ids)),
                    advancement_basis="qml_matched",
                )
            )
    return tasks


def task_output_dir(output_root: Path, task: CampaignTask) -> Path:
    return output_root / "tasks" / task.stage / task.key


def validate_task(root: Path, task: CampaignTask) -> None:
    trial = load_trial(root, task.trial_id)
    if (
        task.family_id != trial.family_id
        or task.model_family != trial.model_family
        or task.trial_order != trial.trial_order
    ):
        raise PermissionError(f"Task metadata differs from frozen trial: {task.key}")
    if task.family_id in QML_IDS:
        expected_qubits = int(trial.parameters["qubits"])
        if task.view != "primary" or task.matched_qubits != expected_qubits:
            raise PermissionError(f"QML task view/dimension mismatch: {task.key}")
    elif task.family_id == "A01":
        if task.view != "primary" or task.matched_qubits not in {4, 6, 8}:
            raise PermissionError(f"A01 task view/dimension mismatch: {task.key}")
    elif task.view == "compressed_c05":
        if task.family_id != "C05" or task.matched_qubits not in {4, 6, 8}:
            raise PermissionError(f"Compressed C05 task mismatch: {task.key}")
    elif task.view != "primary" or task.matched_qubits is not None:
        raise PermissionError(f"Unrestricted classical task mismatch: {task.key}")
    resolved_seed = task.trial_order if task.seed_index is None else task.seed_index
    trial_seed(root, trial, resolved_seed)
    projected = (
        task.family_id in QML_IDS
        or task.family_id == "A01"
        or task.view == "compressed_c05"
    )
    if projected and task.rung_samples not in RUNG_SEQUENCE:
        raise PermissionError(f"Projected task has an invalid rung: {task.key}")
    if not projected and task.rung_samples is not None:
        raise PermissionError(f"Unrestricted task has a projected rung: {task.key}")
    if task.stage == "seed_rerun" and task.seed_index not in range(1, 21):
        raise PermissionError(f"Seed rerun is outside frozen indices: {task.key}")
    if task.stage not in {"tuning", "seed_rerun"}:
        raise PermissionError(f"Unknown campaign stage: {task.stage}")


def _summary_matches(
    root: Path, task: CampaignTask, summary: Mapping[str, Any]
) -> bool:
    resolved_seed = task.trial_order if task.seed_index is None else task.seed_index
    trial = load_trial(root, task.trial_id)
    expected_training_seed = trial_seed(root, trial, resolved_seed)
    return all(
        (
            summary.get("source_commit") == _head(root),
            summary.get("trial", {}).get("trial_id") == task.trial_id,
            summary.get("view") == task.view,
            summary.get("rung_samples") == task.rung_samples,
            summary.get("matched_qubits") == task.matched_qubits,
            summary.get("seed_index") == resolved_seed,
            summary.get("training_seed") == expected_training_seed,
        )
    )


def load_task_summary(
    root: Path, output_root: Path, task: CampaignTask
) -> dict[str, Any] | None:
    path = task_output_dir(output_root, task) / "summary.json"
    if not path.is_file():
        return None
    summary = json.loads(path.read_text(encoding="utf-8"))
    if not _summary_matches(root, task, summary):
        raise PermissionError(f"Campaign summary signature mismatch: {path}")
    return summary


def task_terminal_result(
    root: Path, output_root: Path, task: CampaignTask
) -> tuple[str, dict[str, Any] | None]:
    summary_path = task_output_dir(output_root, task) / "summary.json"
    failure_path = task_output_dir(output_root, task) / "failure.json"
    if summary_path.is_file() and failure_path.is_file():
        raise PermissionError(
            f"Task has both success and failure artifacts: {task.key}"
        )
    summary = load_task_summary(root, output_root, task)
    if summary is not None:
        return "complete", summary
    if failure_path.is_file():
        failure = json.loads(failure_path.read_text(encoding="utf-8"))
        if failure.get("source_commit") != _head(root):
            raise PermissionError(f"Stale task failure artifact: {failure_path}")
        if failure.get("task") != asdict(task):
            raise PermissionError(f"Task failure identity mismatch: {failure_path}")
        return "failed", failure
    return "missing", None


def conservative_task_wall_time(
    current_elapsed: float, summary: Mapping[str, Any]
) -> float:
    """Never let a resumed invocation erase time recorded in fold checkpoints."""

    return max(
        current_elapsed,
        float(summary.get("end_to_end_wall_time_s") or 0.0),
    )


def _execute_task_worker(
    root_text: str, output_text: str, raw_task: Mapping[str, Any]
) -> dict[str, Any]:
    root = Path(root_text)
    output_root = Path(output_text)
    task = CampaignTask(**raw_task)
    validate_task(root, task)
    output_dir = task_output_dir(output_root, task)
    with _file_lock(output_dir / ".task.lock"):
        state, terminal = task_terminal_result(root, output_root, task)
        if state == "complete":
            runtime_path = output_dir / "runtime.json"
            if not runtime_path.is_file() and terminal is not None:
                _freeze_json(
                    runtime_path,
                    {
                        "task": asdict(task),
                        "source_commit": _head(root),
                        "task_signature": terminal["task_signature"],
                        "end_to_end_task_wall_time_s": terminal.get(
                            "end_to_end_wall_time_s"
                        ),
                        "measurement_scope": "summary_fallback_after_completed_resume",
                    },
                )
            return {"task_key": task.key, "status": "resumed_complete"}
        if state == "failed":
            return {"task_key": task.key, "status": "preserved_failed"}
        started = time.perf_counter()
        try:
            with threadpool_limits(limits=1):
                summary = execute_trial(
                    root,
                    task.trial_id,
                    output_dir,
                    rung_samples=task.rung_samples,
                    matched_qubits=task.matched_qubits,
                    view=task.view,
                    seed_index=task.seed_index,
                )
        except Exception as error:  # preserve failures and continue the frozen stage
            failure = {
                "status": "failed",
                "task": asdict(task),
                "source_commit": _head(root),
                "exception_type": type(error).__name__,
                "exception_message": str(error),
                "traceback": traceback.format_exc(),
                "wall_time_s_before_failure": time.perf_counter() - started,
                "calibration_rows_read": 0,
                "final_test_rows_read": 0,
            }
            _atomic_json(output_dir / "failure.json", failure)
            return {
                "task_key": task.key,
                "status": "failed",
                "exception_type": type(error).__name__,
                "exception_message": str(error),
            }
        current_elapsed = time.perf_counter() - started
        measured_elapsed = conservative_task_wall_time(current_elapsed, summary)
        _freeze_json(
            output_dir / "runtime.json",
            {
                "task": asdict(task),
                "source_commit": _head(root),
                "task_signature": summary["task_signature"],
                "end_to_end_task_wall_time_s": measured_elapsed,
                "measurement_scope": "execute_trial_call_including_data_audit_and_scientific_artifact_writes",
            },
        )
    return {"task_key": task.key, "status": "complete"}


def representative_benchmark_tasks(root: Path) -> list[CampaignTask]:
    """Return the outcome-blind worst-shape checkpoint frozen by D006."""

    initial = initial_campaign_tasks(root)
    trial_ids = {"C04-T02", "Q01-T04", "Q02-T07", "Q03-T14"}
    candidates = [
        task
        for task in initial
        if task.trial_id in trial_ids and task.candidate_role == "primary_candidate"
    ]
    candidates = [
        (
            CampaignTask(**{**asdict(task), "rung_samples": 1024})
            if task.family_id in QML_IDS
            else task
        )
        for task in candidates
    ]
    qml = [task for task in candidates if task.family_id in QML_IDS]
    return _merge_tasks(
        [*candidates, *matched_control_tasks(root, qml, stage="tuning")]
    )


def _task_measured_wall(
    root: Path, output_root: Path, task: CampaignTask
) -> float | None:
    task_dir = task_output_dir(output_root, task)
    runtime_path = task_dir / "runtime.json"
    if runtime_path.is_file():
        runtime = json.loads(runtime_path.read_text(encoding="utf-8"))
        summary = load_task_summary(root, output_root, task)
        if runtime.get("source_commit") != _head(root) or runtime.get("task") != asdict(
            task
        ):
            raise PermissionError(
                f"Benchmark runtime identity mismatch: {runtime_path}"
            )
        if summary is None or runtime.get("task_signature") != summary.get(
            "task_signature"
        ):
            raise PermissionError(
                f"Benchmark runtime signature mismatch: {runtime_path}"
            )
        measured = runtime.get("end_to_end_task_wall_time_s")
        return None if measured is None else float(measured)
    return None


def _directory_bytes(path: Path) -> int:
    return sum(item.stat().st_size for item in path.rglob("*") if item.is_file())


def run_campaign_benchmark(
    root: Path,
    output_root: Path,
    classical_workers: int = 2,
) -> dict[str, Any]:
    """Run the bounded checkpoint required before full D006 scale-up."""

    validate_development_output_path(root, output_root)
    verify_campaign_contract(root)
    initial = initial_campaign_tasks(root)
    _write_campaign_contract(root, output_root, initial)
    initial_digest = hashlib.sha256(
        json.dumps(
            [asdict(task) for task in initial],
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()
    freeze_task_authorization(
        root,
        output_root / "initial_tasks.csv",
        initial,
        parent_digest=initial_digest,
    )
    tasks = representative_benchmark_tasks(root)
    freeze_task_authorization(
        root,
        output_root / "authorizations" / "benchmark.csv",
        tasks,
        parent_digest=initial_digest,
    )
    execute_tasks(root, output_root, tasks, classical_workers)

    measured: list[dict[str, Any]] = []
    all_complete = True
    all_terminal = True
    for task in tasks:
        state, result = task_terminal_result(root, output_root, task)
        wall = _task_measured_wall(root, output_root, task)
        all_terminal &= state != "missing" and not (
            state == "complete" and wall is None
        )
        all_complete &= state == "complete" and wall is not None
        measured.append(
            {
                "task_key": task.key,
                "family_id": task.family_id,
                "model_family": task.model_family,
                "state": state,
                "eligible_to_advance": (
                    bool(result.get("eligible_to_advance"))
                    if state == "complete" and result is not None
                    else False
                ),
                "measured_end_to_end_wall_s": wall,
                "task_directory_bytes": _directory_bytes(
                    task_output_dir(output_root, task)
                ),
            }
        )
    qml_walls = [
        float(row["measured_end_to_end_wall_s"])
        for row in measured
        if row["family_id"] in QML_IDS and row["measured_end_to_end_wall_s"] is not None
    ]
    classical_walls = [
        float(row["measured_end_to_end_wall_s"])
        for row in measured
        if row["family_id"] not in QML_IDS
        and row["measured_end_to_end_wall_s"] is not None
    ]
    margin = 1.25
    projected_qml_tasks = 234
    projected_classical_tasks = 1051
    projected_core_hours = None
    projected_wall_days = None
    if qml_walls and classical_walls:
        qml_ceiling_s = max(qml_walls)
        classical_ceiling_s = max(classical_walls)
        projected_core_hours = (
            margin
            * (
                qml_ceiling_s * projected_qml_tasks
                + classical_ceiling_s * projected_classical_tasks
            )
            / 3600.0
        )
        projected_wall_days = (
            margin
            * (
                qml_ceiling_s * projected_qml_tasks
                + classical_ceiling_s
                * projected_classical_tasks
                / max(1, classical_workers)
            )
            / 86400.0
        )
    mean_bytes = sum(int(row["task_directory_bytes"]) for row in measured) / len(
        measured
    )
    projected_storage_gb = margin * mean_bytes * 1285 / 1_000_000_000.0
    scale_up = bool(
        all_complete
        and projected_core_hours is not None
        and projected_wall_days is not None
        and projected_core_hours <= 10000
        and projected_wall_days <= 30
        and projected_storage_gb <= 250
    )
    audit = {
        "status": "pass" if scale_up else "fail",
        "scale_up_authorized": scale_up,
        "source_commit": _head(root),
        "benchmark_task_count": len(tasks),
        "projection_margin": margin,
        "classical_workers_for_projection": classical_workers,
        "projected_core_hours_ceiling_case": projected_core_hours,
        "projected_wall_days_ceiling_case": projected_wall_days,
        "projected_storage_gb": projected_storage_gb,
        "cpu_core_hour_ceiling": 10000,
        "wall_day_ceiling": 30,
        "storage_gb_ceiling": 250,
        "tasks": measured,
        "calibration_rows_read": 0,
        "final_test_rows_read": 0,
    }
    if not all_terminal:
        _atomic_json(
            output_root / "benchmark_progress.json",
            {
                **audit,
                "status": "incomplete_recoverable_coordinator_failure",
                "scale_up_authorized": False,
            },
        )
        raise RuntimeError(
            "Gate 5 benchmark has non-terminal coordinator work; resume the benchmark"
        )
    _freeze_json(output_root / "benchmark_audit.json", audit)
    return audit


def verify_benchmark_scaleup(root: Path, output_root: Path) -> None:
    path = output_root / "benchmark_audit.json"
    if not path.is_file():
        raise PermissionError("Full campaign requires the frozen D006 benchmark")
    audit = json.loads(path.read_text(encoding="utf-8"))
    if audit.get("source_commit") != _head(root) or not audit.get(
        "scale_up_authorized"
    ):
        raise PermissionError("D006 benchmark did not authorize full scale-up")


def execute_tasks(
    root: Path,
    output_root: Path,
    tasks: Sequence[CampaignTask],
    classical_workers: int = 4,
) -> list[dict[str, Any]]:
    """Run classical work in bounded processes and statevector work serially."""

    if not 1 <= classical_workers <= 8:
        raise ValueError("classical_workers must be between 1 and 8")
    deduplicated = {task.key: task for task in tasks}
    if len(deduplicated) != len(tasks):
        raise ValueError("Campaign task keys must be unique")
    for task in tasks:
        validate_task(root, task)
    classical = [
        task
        for task in tasks
        if load_trial(root, task.trial_id).model_family not in QML_FAMILIES
    ]
    quantum = [
        task
        for task in tasks
        if load_trial(root, task.trial_id).model_family in QML_FAMILIES
    ]
    results: list[dict[str, Any]] = []

    if classical:
        with ProcessPoolExecutor(max_workers=classical_workers) as pool:
            futures = {
                pool.submit(
                    _execute_task_worker,
                    str(root),
                    str(output_root),
                    asdict(task),
                ): task
                for task in classical
            }
            for future in as_completed(futures):
                task = futures[future]
                try:
                    result = future.result()
                except Exception as error:
                    coordinator_failure = {
                        "status": "coordinator_failure",
                        "task": asdict(task),
                        "source_commit": _head(root),
                        "exception_type": type(error).__name__,
                        "exception_message": str(error),
                        "traceback": traceback.format_exc(),
                        "calibration_rows_read": 0,
                        "final_test_rows_read": 0,
                    }
                    task_dir = task_output_dir(output_root, task)
                    attempt = len(list(task_dir.glob("coordinator_failure_*.json"))) + 1
                    _atomic_json(
                        task_dir / f"coordinator_failure_{attempt:03d}.json",
                        coordinator_failure,
                    )
                    result = {
                        "task_key": task.key,
                        "status": "coordinator_failure",
                    }
                results.append(result)
                print(
                    f"[{len(results)}/{len(tasks)}] {result['status']} "
                    f"{result['task_key']}",
                    flush=True,
                )

    for task in quantum:
        result = _execute_task_worker(str(root), str(output_root), asdict(task))
        results.append(result)
        print(
            f"[{len(results)}/{len(tasks)}] {result['status']} {result['task_key']}",
            flush=True,
        )
    return results


def _qml_tasks_for_rung(
    root: Path,
    output_root: Path,
    previous: Sequence[CampaignTask],
    previous_rung: int,
    next_rung: int,
) -> tuple[list[CampaignTask], list[dict[str, Any]]]:
    selected_tasks: list[CampaignTask] = []
    ranking_rows: list[dict[str, Any]] = []
    retain = RUNG_RETAIN[previous_rung]
    for family_id in QML_IDS:
        family_tasks = [task for task in previous if task.family_id == family_id]
        summaries = []
        failures: list[CampaignTask] = []
        for task in family_tasks:
            state, result = task_terminal_result(root, output_root, task)
            if state == "missing":
                raise RuntimeError(
                    f"Cannot rank interrupted {family_id} rung {previous_rung}: "
                    f"{task.key} is not terminal"
                )
            if state == "failed":
                failures.append(task)
            else:
                assert result is not None
                summaries.append(result)
        advancement_error = ""
        try:
            ranked = rank_rung_summaries(
                summaries, retain=retain, preserve_required_qubits=True
            )
        except ValueError as error:
            advancement_error = str(error)
            ranked = [
                {
                    "rank": "",
                    "trial_id": summary["trial"]["trial_id"],
                    "model_family": summary["trial"]["model_family"],
                    "pooled_oof_nrmse": summary["pooled_oof_nrmse"],
                    "mean_regret_m_s": summary["mean_regret_m_s"],
                    "complexity_proxy": "",
                    "effective_qubits": summary["trial"]["parameters"].get(
                        "qubits", summary.get("matched_qubits")
                    ),
                    "selected_for_next_rung": False,
                }
                for summary in summaries
            ]
        selected_ids = {
            row["trial_id"] for row in ranked if row["selected_for_next_rung"]
        }
        ranking_rows.extend(
            {
                "family_id": family_id,
                "completed_rung": previous_rung,
                "next_rung": next_rung,
                "task_status": (
                    "complete" if not advancement_error else "nonadvancing"
                ),
                "advancement_error": advancement_error,
                **row,
            }
            for row in ranked
        )
        ranking_rows.extend(
            {
                "family_id": family_id,
                "completed_rung": previous_rung,
                "next_rung": next_rung,
                "task_status": "failed",
                "advancement_error": advancement_error,
                "rank": "",
                "trial_id": task.trial_id,
                "model_family": task.model_family,
                "pooled_oof_nrmse": "",
                "mean_regret_m_s": "",
                "complexity_proxy": "",
                "effective_qubits": task.matched_qubits,
                "selected_for_next_rung": False,
            }
            for task in failures
        )
        for task in family_tasks:
            if task.trial_id in selected_ids:
                selected_tasks.append(
                    CampaignTask(
                        **{
                            **asdict(task),
                            "rung_samples": next_rung,
                            "stage": "tuning",
                        }
                    )
                )
    return selected_tasks, ranking_rows


def _control_tasks_for_rung(
    root: Path,
    output_root: Path,
    previous: Sequence[CampaignTask],
    previous_rung: int,
    next_rung: int,
) -> tuple[list[CampaignTask], list[dict[str, Any]]]:
    selected_tasks: list[CampaignTask] = []
    ranking_rows: list[dict[str, Any]] = []
    retain = RUNG_RETAIN[previous_rung]
    for family_id, view in CONTROL_VIEWS:
        for qubits in (4, 6, 8):
            tasks = [
                task
                for task in previous
                if task.family_id == family_id
                and task.view == view
                and task.matched_qubits == qubits
                and "control_ranked" in task.advancement_basis
            ]
            summaries: list[dict[str, Any]] = []
            failures: list[CampaignTask] = []
            for task in tasks:
                state, result = task_terminal_result(root, output_root, task)
                if state == "missing":
                    raise RuntimeError(
                        f"Cannot rank interrupted {family_id}/q{qubits} "
                        f"rung {previous_rung}: {task.key} is not terminal"
                    )
                if state == "failed":
                    failures.append(task)
                else:
                    assert result is not None
                    summaries.append(result)
            advancement_error = ""
            try:
                ranked = rank_rung_summaries(summaries, retain=retain)
            except ValueError as error:
                advancement_error = str(error)
                ranked = [
                    {
                        "rank": "",
                        "trial_id": summary["trial"]["trial_id"],
                        "model_family": summary["trial"]["model_family"],
                        "pooled_oof_nrmse": summary["pooled_oof_nrmse"],
                        "mean_regret_m_s": summary["mean_regret_m_s"],
                        "complexity_proxy": "",
                        "effective_qubits": qubits,
                        "selected_for_next_rung": False,
                    }
                    for summary in summaries
                ]
            selected_ids = {
                row["trial_id"] for row in ranked if row["selected_for_next_rung"]
            }
            ranking_rows.extend(
                {
                    "family_id": family_id,
                    "view": view,
                    "completed_rung": previous_rung,
                    "next_rung": next_rung,
                    "task_status": (
                        "complete" if not advancement_error else "nonadvancing"
                    ),
                    "advancement_error": advancement_error,
                    **row,
                }
                for row in ranked
            )
            ranking_rows.extend(
                {
                    "family_id": family_id,
                    "view": view,
                    "completed_rung": previous_rung,
                    "next_rung": next_rung,
                    "task_status": "failed",
                    "advancement_error": advancement_error,
                    "rank": "",
                    "trial_id": task.trial_id,
                    "model_family": task.model_family,
                    "pooled_oof_nrmse": "",
                    "mean_regret_m_s": "",
                    "complexity_proxy": "",
                    "effective_qubits": qubits,
                    "selected_for_next_rung": False,
                }
                for task in failures
            )
            for task in tasks:
                if task.trial_id in selected_ids:
                    selected_tasks.append(
                        CampaignTask(
                            **{
                                **asdict(task),
                                "rung_samples": next_rung,
                                "stage": "tuning",
                                "advancement_basis": "control_ranked",
                            }
                        )
                    )
    return selected_tasks, ranking_rows


def _merge_tasks(tasks: Sequence[CampaignTask]) -> list[CampaignTask]:
    merged: dict[str, CampaignTask] = {}
    for task in tasks:
        existing = merged.get(task.key)
        if existing is None:
            merged[task.key] = task
            continue
        bases = set(existing.advancement_basis.split("_and_"))
        bases.update(task.advancement_basis.split("_and_"))
        controls = set(filter(None, existing.control_for.split(";")))
        controls.update(filter(None, task.control_for.split(";")))
        merged[task.key] = CampaignTask(
            **{
                **asdict(existing),
                "advancement_basis": "_and_".join(sorted(bases)),
                "control_for": ";".join(sorted(controls)),
            }
        )
    return list(merged.values())


def _write_campaign_contract(
    root: Path, output_root: Path, tasks: Sequence[CampaignTask]
) -> None:
    raw = [asdict(task) for task in tasks]
    digest = hashlib.sha256(
        json.dumps(raw, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    _freeze_json(
        output_root / "campaign_contract.json",
        {
            "status": "accepted_runner_campaign_ready",
            "source_commit": _head(root),
            "initial_task_count": len(tasks),
            "initial_plan_sha256": digest,
            "projected_task_ceiling": {
                "qualification_tasks": 10,
                "tuning_tasks": 855,
                "seed_rerun_tasks": 420,
                "total_tasks": 1275,
                "conservative_total_executions_including_qualification": 1285,
                "total_folds": 6375,
                "model_fits": 12750,
                "conservative_folds_including_qualification": 6425,
                "conservative_model_fits_including_qualification": 12850,
                "formula": "10 qualification tasks plus 450 initial + at most 225/120/60 later-rung tasks + at most 420 twenty-seed tasks; qualification overlap is not credited in the conservative ceiling",
            },
            "compute_ceiling": {
                "cpu_core_hours": 10000,
                "wall_clock_days": 30,
                "persistent_storage_gb": 250,
                "status": "authorized ceiling unchanged; measured ledgers remain authoritative",
            },
            "calibration_rows_read": 0,
            "final_test_rows_read": 0,
            "tasks": raw,
            "execution_environment": {
                "platform": platform.platform(),
                "machine": platform.machine(),
                "processor": platform.processor(),
                "python": sys.version,
                "packages": verify_scientific_environment(root),
                "uv_lock_sha256": sha256_file(root / "uv.lock"),
                "classical_worker_threads": 1,
                "concurrent_statevector_tasks": 1,
            },
        },
    )


def _normalized_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, str]]:
    return [
        {str(key): "" if value is None else str(value) for key, value in row.items()}
        for row in rows
    ]


def _rows_digest(rows: Sequence[Mapping[str, Any]]) -> str:
    return hashlib.sha256(
        json.dumps(
            _normalized_rows(rows),
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()


def _csv_digest(path: Path) -> str:
    with path.open(encoding="utf-8") as handle:
        return _rows_digest(list(csv.DictReader(handle)))


def verify_campaign_contract(root: Path) -> None:
    """Fail closed if tracked pre-fit manifests differ from generated plans."""

    config = read_yaml(root / "configs/phase1_benchmark.yaml")
    runner = config.get("gate5_runner_freeze", {})
    if (
        runner.get("status") != RUNNER_ACCEPTED_STATUS
        or runner.get("research_fit_authorized") is not True
    ):
        raise PermissionError(
            "The active D005/D006 campaign contract is not authorized for fitting"
        )
    verify_scientific_environment(root)
    _clean_source_commit(root)
    _, generated_folds = gate5_preflight(root)
    tracked_folds = read_csv(
        root / "data/processed/reporting/gate5_cv_fold_manifest.csv"
    )
    if _normalized_rows(generated_folds) != _normalized_rows(tracked_folds):
        raise PermissionError("Tracked Gate 5 fold manifest differs from preflight")
    generated_plan = initial_execution_plan(root)
    tracked_plan = read_csv(
        root / "data/processed/reporting/gate5_initial_execution_plan.csv"
    )
    if _normalized_rows(generated_plan) != _normalized_rows(tracked_plan):
        raise PermissionError("Tracked Gate 5 execution plan differs from runner")
    if {row["execution_status"] for row in generated_plan} != {"ready"}:
        raise PermissionError("Gate 5 campaign is not accepted and ready")


def run_tuning_campaign(
    root: Path, output_root: Path, classical_workers: int = 4
) -> list[CampaignTask]:
    """Run or resume all registered tuning and matched-control rungs."""

    validate_development_output_path(root, output_root)
    verify_campaign_contract(root)
    verify_benchmark_scaleup(root, output_root)
    initial = initial_campaign_tasks(root)
    _write_campaign_contract(root, output_root, initial)
    freeze_task_authorization(
        root,
        output_root / "initial_tasks.csv",
        initial,
        parent_digest=hashlib.sha256(
            json.dumps(
                [asdict(task) for task in initial],
                sort_keys=True,
                separators=(",", ":"),
            ).encode()
        ).hexdigest(),
    )
    execute_tasks(root, output_root, initial, classical_workers)
    previous = list(initial)
    all_tasks = list(initial)
    for previous_rung, next_rung in zip(RUNG_SEQUENCE, RUNG_SEQUENCE[1:]):
        qml_tasks, qml_rankings = _qml_tasks_for_rung(
            root, output_root, previous, previous_rung, next_rung
        )
        ranked_controls, control_rankings = _control_tasks_for_rung(
            root, output_root, previous, previous_rung, next_rung
        )
        matched_controls = matched_control_tasks(root, qml_tasks, "tuning")
        authorized = _merge_tasks([*qml_tasks, *ranked_controls, *matched_controls])
        if not authorized:
            break
        ranking_rows = [*qml_rankings, *control_rankings]
        ranking_path = output_root / "rankings" / f"rung_{previous_rung}.csv"
        _freeze_csv(ranking_path, ranking_rows)
        ranking_digest = hashlib.sha256(
            json.dumps(
                _normalized_rows(ranking_rows),
                sort_keys=True,
                separators=(",", ":"),
            ).encode()
        ).hexdigest()
        freeze_task_authorization(
            root,
            output_root / "authorizations" / f"rung_{next_rung}.csv",
            authorized,
            parent_digest=ranking_digest,
        )
        execute_tasks(root, output_root, authorized, classical_workers)
        all_tasks.extend(authorized)
        previous = authorized
    return all_tasks


def _rank_one(
    root: Path, output_root: Path, tasks: Sequence[CampaignTask]
) -> CampaignTask | None:
    summaries: list[dict[str, Any]] = []
    summary_to_task: dict[tuple[str, int | None], CampaignTask] = {}
    for task in tasks:
        state, result = task_terminal_result(root, output_root, task)
        if state == "missing":
            raise RuntimeError(
                f"Cannot select from an interrupted stage: {task.key} is not terminal"
            )
        if state == "failed":
            continue
        assert result is not None
        summaries.append(result)
        summary_to_task[(task.trial_id, task.matched_qubits)] = task
    if not summaries:
        return None
    try:
        ranked = rank_rung_summaries(summaries, retain=1)
    except ValueError:
        return None
    selected = next(row for row in ranked if row["selected_for_next_rung"])
    key = (selected["trial_id"], selected["effective_qubits"])
    return summary_to_task[key]


def select_finalists(
    root: Path, output_root: Path, tuning_tasks: Sequence[CampaignTask]
) -> tuple[list[CampaignTask], list[CampaignTask]]:
    """Freeze one development configuration per registered candidate family."""

    validate_development_output_path(root, output_root)
    finalists: list[CampaignTask] = []
    for family_id in CANDIDATE_IDS:
        family_tasks = [
            task
            for task in tuning_tasks
            if task.family_id == family_id
            and task.candidate_role == "primary_candidate"
            and (
                task.rung_samples is None
                if family_id.startswith("C")
                else task.rung_samples == 1024
            )
        ]
        selected = _rank_one(root, output_root, family_tasks)
        if selected is not None:
            finalists.append(selected)
    qml_dimensions = {
        task.matched_qubits for task in finalists if task.family_id in QML_IDS
    }
    control_finalists: list[CampaignTask] = []
    for family_id, view in CONTROL_VIEWS:
        for qubits in sorted(qml_dimensions):
            control_tasks = [
                task
                for task in tuning_tasks
                if task.family_id == family_id
                and task.view == view
                and task.rung_samples == 1024
                and task.matched_qubits == qubits
                and "control_ranked" in task.advancement_basis
            ]
            selected = _rank_one(root, output_root, control_tasks)
            if selected is not None:
                qml_ids = sorted(
                    task.family_id
                    for task in finalists
                    if task.family_id in QML_IDS and task.matched_qubits == qubits
                )
                control_finalists.append(
                    CampaignTask(
                        **{
                            **asdict(selected),
                            "control_for": ";".join(qml_ids),
                            "advancement_basis": "control_ranked",
                        }
                    )
                )
    missing_candidates = sorted(
        set(CANDIDATE_IDS) - {task.family_id for task in finalists}
    )
    expected_controls = {
        (family_id, view, qubits)
        for family_id, view in CONTROL_VIEWS
        for qubits in qml_dimensions
    }
    actual_controls = {
        (task.family_id, task.view, task.matched_qubits) for task in control_finalists
    }
    missing_controls = sorted(expected_controls - actual_controls)
    _freeze_json(
        output_root / "selection_manifest.json",
        {
            "status": (
                "complete"
                if not missing_candidates and not missing_controls
                else "incomplete_with_terminal_failures"
            ),
            "source_commit": _head(root),
            "selection_scope": "development_only",
            "candidate_family_count": len(CANDIDATE_IDS),
            "selected_family_count": len(finalists),
            "missing_candidate_families": missing_candidates,
            "missing_tuned_controls": [list(value) for value in missing_controls],
            "calibration_rows_read": 0,
            "final_test_rows_read": 0,
            "finalists": [asdict(task) for task in finalists],
            "tuned_control_finalists": [asdict(task) for task in control_finalists],
        },
    )
    return finalists, control_finalists


def seed_rerun_tasks(
    root: Path,
    finalists: Sequence[CampaignTask],
    tuned_controls: Sequence[CampaignTask],
    seeds: int = 20,
) -> list[CampaignTask]:
    if seeds != 20:
        raise ValueError("Formal Gate 5 stability reruns require exactly 20 seeds")
    candidates = [
        CampaignTask(
            **{
                **asdict(task),
                "stage": "seed_rerun",
                "seed_index": seed_index,
            }
        )
        for task in finalists
        for seed_index in range(1, seeds + 1)
    ]
    qml = [task for task in finalists if task.family_id in QML_IDS]
    controls: list[CampaignTask] = []
    for seed_index in range(1, seeds + 1):
        controls.extend(
            matched_control_tasks(
                root,
                qml,
                stage="seed_rerun",
                seed_index=seed_index,
            )
        )
    ranked_controls = [
        CampaignTask(
            **{
                **asdict(task),
                "stage": "seed_rerun",
                "seed_index": seed_index,
                "advancement_basis": "control_ranked",
            }
        )
        for task in tuned_controls
        for seed_index in range(1, seeds + 1)
    ]
    return _merge_tasks([*candidates, *controls, *ranked_controls])


def run_seed_reruns(
    root: Path,
    output_root: Path,
    finalists: Sequence[CampaignTask],
    tuned_controls: Sequence[CampaignTask],
    classical_workers: int = 4,
    seeds: int = 20,
) -> list[CampaignTask]:
    validate_development_output_path(root, output_root)
    verify_campaign_contract(root)
    selection = json.loads(
        (output_root / "selection_manifest.json").read_text(encoding="utf-8")
    )
    if [asdict(task) for task in finalists] != selection.get("finalists") or [
        asdict(task) for task in tuned_controls
    ] != selection.get("tuned_control_finalists"):
        raise PermissionError("Seed inputs differ from the frozen selection")
    tasks = seed_rerun_tasks(root, finalists, tuned_controls, seeds)
    selection_digest = hashlib.sha256(
        json.dumps(selection, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    freeze_task_authorization(
        root,
        output_root / "authorizations" / "seed_reruns.csv",
        tasks,
        parent_digest=selection_digest,
    )
    execute_tasks(root, output_root, tasks, classical_workers)
    return tasks


def _task_result_row(
    root: Path, output_root: Path, task: CampaignTask
) -> dict[str, Any]:
    summary = load_task_summary(root, output_root, task)
    resolved_seed = task.trial_order if task.seed_index is None else task.seed_index
    base: dict[str, Any] = {
        **asdict(task),
        "task_key": task.key,
        "effective_qubits": task.matched_qubits,
        "resolved_seed_index": resolved_seed,
    }
    if summary is None:
        failure_path = task_output_dir(output_root, task) / "failure.json"
        failure = (
            json.loads(failure_path.read_text(encoding="utf-8"))
            if failure_path.is_file()
            else {}
        )
        return {
            **base,
            "status": "failed",
            "training_seed": "",
            "pooled_oof_rmse": "",
            "pooled_oof_nrmse": "",
            "unweighted_mean_fold_nrmse": "",
            "mean_regret_m_s": "",
            "fold_count": "",
            "eligible_to_advance": False,
            "task_signature": "",
            "source_commit": failure.get("source_commit", _head(root)),
            "source_split": "development",
            "exception_type": failure.get("exception_type", "missing_result"),
            "exception_message": failure.get("exception_message", ""),
            "calibration_rows_read": 0,
            "final_test_rows_read": 0,
        }
    return {
        **base,
        "status": summary["status"],
        "training_seed": summary["training_seed"],
        "pooled_oof_rmse": summary["pooled_oof_rmse"],
        "pooled_oof_nrmse": summary["pooled_oof_nrmse"],
        "unweighted_mean_fold_nrmse": summary["unweighted_mean_fold_nrmse"],
        "mean_regret_m_s": summary["mean_regret_m_s"],
        "fold_count": summary["fold_count"],
        "eligible_to_advance": summary["eligible_to_advance"],
        "task_signature": summary["task_signature"],
        "source_commit": summary["source_commit"],
        "source_split": summary["source_split"],
        "exception_type": "",
        "exception_message": "",
        "calibration_rows_read": summary["calibration_rows_read"],
        "final_test_rows_read": summary["final_test_rows_read"],
    }


def export_result_tables(
    root: Path,
    output_root: Path,
    experiment_dir: Path,
    tuning_tasks: Sequence[CampaignTask],
    seed_tasks: Sequence[CampaignTask],
) -> None:
    """Export compact, tracked evidence from ignored atomic task outputs."""

    validate_development_output_path(root, output_root)
    validate_development_output_path(root, experiment_dir)
    for task in [*tuning_tasks, *seed_tasks]:
        state, _ = task_terminal_result(root, output_root, task)
        if state == "missing":
            raise RuntimeError(f"Formal export blocked by missing task: {task.key}")
    experiment_dir.mkdir(parents=True, exist_ok=True)
    write_csv_rows(
        experiment_dir / "phase1_tuning_results.csv",
        [_task_result_row(root, output_root, task) for task in tuning_tasks],
    )
    write_csv_rows(
        experiment_dir / "phase1_seed_results.csv",
        [_task_result_row(root, output_root, task) for task in seed_tasks],
    )
    ranking_rows: list[dict[str, Any]] = []
    for rung in (128, 256, 512):
        ranking_path = output_root / "rankings" / f"rung_{rung}.csv"
        if ranking_path.is_file():
            with ranking_path.open(encoding="utf-8") as handle:
                ranking_rows.extend(csv.DictReader(handle))
    if ranking_rows:
        _write_union_csv(experiment_dir / "phase1_rung_rankings.csv", ranking_rows)

    def detailed_rows(
        tasks: Sequence[CampaignTask], filename: str
    ) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for task in tasks:
            path = task_output_dir(output_root, task) / filename
            if not path.is_file():
                continue
            summary = load_task_summary(root, output_root, task)
            if summary is None:
                continue
            metadata = {
                "task_key": task.key,
                "task_signature": summary["task_signature"],
                "source_commit": summary["source_commit"],
                "stage": task.stage,
                "family_id": task.family_id,
                "model_family": task.model_family,
                "trial_id": task.trial_id,
                "trial_order": task.trial_order,
                "view": task.view,
                "rung_samples": task.rung_samples,
                "matched_qubits": task.matched_qubits,
                "seed_index": (
                    task.trial_order if task.seed_index is None else task.seed_index
                ),
                "candidate_role": task.candidate_role,
                "control_for": task.control_for,
                "advancement_basis": task.advancement_basis,
                "source_split": summary["source_split"],
                "calibration_rows_read": summary["calibration_rows_read"],
                "final_test_rows_read": summary["final_test_rows_read"],
            }
            with path.open(encoding="utf-8") as handle:
                rows.extend({**metadata, **row} for row in csv.DictReader(handle))
        return rows

    detail_fields = [
        "task_key",
        "task_signature",
        "source_commit",
        "source_split",
        "stage",
        "family_id",
        "model_family",
        "trial_id",
        "trial_order",
        "view",
        "rung_samples",
        "matched_qubits",
        "seed_index",
        "candidate_role",
        "control_for",
        "advancement_basis",
        "calibration_rows_read",
        "final_test_rows_read",
        "fold_id",
    ]
    _write_rows_or_empty_header(
        experiment_dir / "phase1_tuning_fold_metrics.csv",
        detailed_rows(tuning_tasks, "fold_metrics.csv"),
        detail_fields,
    )
    _write_rows_or_empty_header(
        experiment_dir / "phase1_tuning_regime_metrics.csv",
        detailed_rows(tuning_tasks, "regime_metrics.csv"),
        [*detail_fields, "dimension", "value", "rows", "nrmse"],
    )
    _write_rows_or_empty_header(
        experiment_dir / "phase1_seed_fold_metrics.csv",
        detailed_rows(seed_tasks, "fold_metrics.csv"),
        detail_fields,
    )
    _write_rows_or_empty_header(
        experiment_dir / "phase1_seed_regime_metrics.csv",
        detailed_rows(seed_tasks, "regime_metrics.csv"),
        [*detail_fields, "dimension", "value", "rows", "nrmse"],
    )

    all_tasks = [*tuning_tasks, *seed_tasks]
    attempts: list[dict[str, Any]] = []
    state_counts = {"complete": 0, "failed": 0}
    for task in all_tasks:
        state, result = task_terminal_result(root, output_root, task)
        state_counts[state] = state_counts.get(state, 0) + 1
        task_dir = task_output_dir(output_root, task)
        attempt_paths = [task_dir / "failure.json"]
        attempt_paths.extend(sorted(task_dir.glob("coordinator_failure_*.json")))
        for path in attempt_paths:
            if not path.is_file():
                continue
            raw = json.loads(path.read_text(encoding="utf-8"))
            coordinator = path.name.startswith("coordinator_failure_")
            attempts.append(
                {
                    "task_key": task.key,
                    "attempt_type": path.stem,
                    "terminal_state": state,
                    "recovered_after_infrastructure_failure": (
                        coordinator and state == "complete"
                    ),
                    "exception_type": raw.get("exception_type", ""),
                    "exception_message": raw.get("exception_message", ""),
                    "source_commit": raw.get("source_commit", ""),
                    "calibration_rows_read": 0,
                    "final_test_rows_read": 0,
                }
            )
    if attempts:
        _write_union_csv(experiment_dir / "phase1_failure_attempts.csv", attempts)
    contract = json.loads(
        (output_root / "campaign_contract.json").read_text(encoding="utf-8")
    )
    selection = json.loads(
        (output_root / "selection_manifest.json").read_text(encoding="utf-8")
    )
    benchmark = json.loads(
        (output_root / "benchmark_audit.json").read_text(encoding="utf-8")
    )
    evidence_names = [
        "phase1_tuning_results.csv",
        "phase1_seed_results.csv",
        "phase1_tuning_fold_metrics.csv",
        "phase1_tuning_regime_metrics.csv",
        "phase1_seed_fold_metrics.csv",
        "phase1_seed_regime_metrics.csv",
    ]
    evidence_names.extend(
        name
        for name in ("phase1_rung_rankings.csv", "phase1_failure_attempts.csv")
        if (experiment_dir / name).is_file()
    )
    evidence_sha256 = {
        name: sha256_file(experiment_dir / name) for name in evidence_names
    }
    _atomic_json(
        experiment_dir / "gate5_campaign_audit.json",
        {
            "status": "complete_with_terminal_failures"
            if state_counts.get("failed", 0)
            else "complete",
            "source_commit": _head(root),
            "authorized_tuning_tasks": len(tuning_tasks),
            "authorized_seed_tasks": len(seed_tasks),
            "task_states": state_counts,
            "failure_attempt_records": len(attempts),
            "campaign_contract": contract,
            "benchmark_audit": benchmark,
            "selection_manifest": selection,
            "evidence_sha256": evidence_sha256,
            "calibration_rows_read": 0,
            "final_test_rows_read": 0,
        },
    )


def load_authorized_tasks(
    path: Path,
    root: Path | None = None,
    expected_parent_digest: str | None = None,
) -> list[CampaignTask]:
    sidecar_path = _authorization_sidecar(path)
    if not sidecar_path.is_file():
        raise FileNotFoundError(f"Missing task authorization sidecar: {sidecar_path}")
    sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
    if root is not None and sidecar.get("source_commit") != _head(root):
        raise PermissionError(f"Stale task authorization: {path}")
    if (
        expected_parent_digest is not None
        and sidecar.get("parent_digest") != expected_parent_digest
    ):
        raise PermissionError(f"Task authorization parent mismatch: {path}")
    with path.open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    tasks = []
    for row in rows:
        raw: dict[str, Any] = dict(row)
        for name in ("trial_order", "rung_samples", "matched_qubits", "seed_index"):
            raw[name] = None if raw[name] == "" else int(raw[name])
        tasks.append(CampaignTask(**raw))
    raw_tasks = [asdict(task) for task in tasks]
    digest = hashlib.sha256(
        json.dumps(raw_tasks, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    if digest != sidecar.get("task_sha256") or raw_tasks != sidecar.get("tasks"):
        raise PermissionError(f"Task authorization content mismatch: {path}")
    if root is not None:
        for task in tasks:
            validate_task(root, task)
    return tasks


def load_tuning_authorization_chain(
    root: Path, output_root: Path
) -> list[CampaignTask]:
    contract_path = output_root / "campaign_contract.json"
    if not contract_path.is_file():
        raise FileNotFoundError("Gate 5 campaign contract is missing")
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    if contract.get("source_commit") != _head(root):
        raise PermissionError("Gate 5 campaign contract is stale")
    tasks = load_authorized_tasks(
        output_root / "initial_tasks.csv",
        root,
        expected_parent_digest=str(contract["initial_plan_sha256"]),
    )
    for previous_rung, next_rung in ((128, 256), (256, 512), (512, 1024)):
        ranking_path = output_root / "rankings" / f"rung_{previous_rung}.csv"
        authorization_path = output_root / "authorizations" / f"rung_{next_rung}.csv"
        if not ranking_path.is_file() or not authorization_path.is_file():
            raise FileNotFoundError(
                f"Incomplete Gate 5 authorization chain at rung {next_rung}"
            )
        tasks.extend(
            load_authorized_tasks(
                authorization_path,
                root,
                expected_parent_digest=_csv_digest(ranking_path),
            )
        )
    return tasks


def load_seed_authorization_chain(root: Path, output_root: Path) -> list[CampaignTask]:
    selection_path = output_root / "selection_manifest.json"
    if not selection_path.is_file():
        raise FileNotFoundError("Gate 5 selection manifest is missing")
    selection = json.loads(selection_path.read_text(encoding="utf-8"))
    if selection.get("source_commit") != _head(root):
        raise PermissionError("Gate 5 selection manifest is stale")
    selection_digest = hashlib.sha256(
        json.dumps(selection, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return load_authorized_tasks(
        output_root / "authorizations" / "seed_reruns.csv",
        root,
        expected_parent_digest=selection_digest,
    )
