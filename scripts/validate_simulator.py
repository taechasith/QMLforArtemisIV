#!/usr/bin/env python3
"""Run the frozen Gate 3B simulator credibility checks and write evidence."""

from __future__ import annotations

import argparse
import csv
import os
import shutil
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import yaml


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from openqfuel.dynamics import ForceModelSettings, propagate  # noqa: E402
from openqfuel.ephemeris import JplEphemeris, sha256_file  # noqa: E402
from openqfuel.oem import OemEphemeris, parse_oem, parse_utc  # noqa: E402
from openqfuel.validation import (  # noqa: E402
    ValidationWindow,
    aggregate_gate_status,
    closest_lunar_approach,
    iso_utc,
    leave_one_out_interpolation_metrics,
    lower_bound_status,
    nearest_irregular_oem_epoch,
    parse_gmat_endpoint_report,
    reference_states_for_window,
    relative_improvement,
    render_gmat_script,
    trajectory_error_metrics,
    upper_bound_status,
)


UTC = timezone.utc
DEFAULT_OEM = (
    ROOT
    / "data/raw/artemis2/oem/asc/Artemis_II_OEM_2026_04_10_Post-ICPS-Sep-to-EI.asc"
)
DEFAULT_KERNEL = ROOT / "data/raw/ephemeris/de440s.bsp"
WINDOWS_PATH = ROOT / "data/processed/artemis2/validation_windows.csv"
BASELINE_PATH = ROOT / "data/processed/artemis2/two_body_baseline.csv"
DISCONTINUITIES_PATH = (
    ROOT / "data/processed/artemis2/oem_detected_discontinuities.csv"
)
EVENTS_PATH = ROOT / "data/artemis2_event_registry.csv"
ACCEPTANCE_PATH = ROOT / "configs/simulator_acceptance.yaml"
OUTPUT_DIR = ROOT / "data/processed/simulator"
REPORT_PATH = ROOT / "docs/gate3_simulator_credibility.md"
GMAT_SCRIPT_PATH = ROOT / "scripts/gmat/gate3_same_force_model.script"

REQUIRED_EVENTS = {
    "TLI": "E002",
    "OTC3": "E005",
    "lunar closest approach": "E006",
    "RTC1": "E007",
    "RTC2": "E008",
    "RTC3": "E009",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"No rows available for {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def number(value: float, places: int = 12) -> str:
    return f"{value:.{places}f}"


def load_windows() -> list[ValidationWindow]:
    rows = [row for row in read_csv(WINDOWS_PATH) if row["role"] == "validation"]
    windows = [
        ValidationWindow(
            row["window_id"],
            row["phase"],
            parse_utc(row["start_utc"]),
            parse_utc(row["stop_utc"]),
        )
        for row in rows
    ]
    if [window.window_id for window in windows] != [f"V{index:02d}" for index in range(1, 6)]:
        raise ValueError("The five frozen validation windows are missing or reordered")
    return windows


def load_exclusions() -> list[tuple[datetime, datetime]]:
    intervals = []
    for row in read_csv(DISCONTINUITIES_PATH):
        buffer = timedelta(minutes=float(row["coast_exclusion_buffer_min"]))
        intervals.append(
            (
                parse_utc(row["first_flagged_utc"]) - buffer,
                parse_utc(row["last_flagged_utc"]) + buffer,
            )
        )
    return intervals


def add_acceptance(
    rows: list[dict[str, Any]],
    *,
    check_id: str,
    category: str,
    subject: str,
    metric: str,
    value: str,
    unit: str,
    comparison: str,
    threshold: str,
    status: str,
    evidence_file: str,
    note: str = "",
) -> None:
    rows.append(
        {
            "check_id": check_id,
            "category": category,
            "subject": subject,
            "metric": metric,
            "value": value,
            "unit": unit,
            "comparison": comparison,
            "threshold": threshold,
            "status": status,
            "evidence_file": evidence_file,
            "note": note,
        }
    )


def interpolation_evidence(
    ephemeris: OemEphemeris,
    acceptance: dict[str, Any],
    summary: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    metrics = leave_one_out_interpolation_metrics(ephemeris, load_exclusions())
    config = acceptance["parser_and_interpolation_checks"]
    position_upper = float(config["position_p95_upper_km"])
    velocity_upper = float(config["velocity_p95_upper_m_s"])
    position_status = upper_bound_status(metrics.position_p95_km, position_upper)
    velocity_status = upper_bound_status(metrics.velocity_p95_m_s, velocity_upper)
    add_acceptance(
        summary,
        check_id="interpolation_position_p95",
        category="parser_and_interpolation",
        subject="latest eligible OEM clean-coast points",
        metric="position_p95",
        value=number(metrics.position_p95_km),
        unit="km",
        comparison="<=",
        threshold=number(position_upper),
        status=position_status,
        evidence_file="interpolation_validation.csv",
    )
    add_acceptance(
        summary,
        check_id="interpolation_velocity_p95",
        category="parser_and_interpolation",
        subject="latest eligible OEM clean-coast points",
        metric="velocity_p95",
        value=number(metrics.velocity_p95_m_s),
        unit="m/s",
        comparison="<=",
        threshold=number(velocity_upper),
        status=velocity_status,
        evidence_file="interpolation_validation.csv",
    )
    return [
        {
            "source_release": ephemeris.path.name,
            "creation_utc": iso_utc(ephemeris.creation_time),
            "eligibility_rule": "target and both neighbors no later than CREATION_DATE",
            "exclusion_rule": "entire interpolation segment outside each detected-discontinuity 30-minute buffer",
            "percentile_method": "numpy linear percentile",
            "sample_count": metrics.samples,
            "position_p95_km": number(metrics.position_p95_km),
            "position_upper_km": number(position_upper),
            "position_status": position_status,
            "velocity_p95_m_s": number(metrics.velocity_p95_m_s),
            "velocity_upper_m_s": number(velocity_upper),
            "velocity_status": velocity_status,
            "position_max_km": number(metrics.position_max_km),
            "velocity_max_m_s": number(metrics.velocity_max_m_s),
            "overall_status": "pass"
            if position_status == velocity_status == "pass"
            else "fail",
        }
    ]


def propagate_windows(
    ephemeris: OemEphemeris,
    jpl: JplEphemeris,
    windows: list[ValidationWindow],
    baseline_rows: list[dict[str, str]],
    acceptance: dict[str, Any],
    summary: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, np.ndarray]]:
    convergence_rows: list[dict[str, Any]] = []
    flight_rows: list[dict[str, Any]] = []
    nominal_endpoints: dict[str, np.ndarray] = {}
    baselines = {row["window_id"]: row for row in baseline_rows}
    numerical = acceptance["numerical_verification"]["integrator_convergence"]
    position_convergence_upper = float(numerical["endpoint_position_difference_upper_km"])
    velocity_convergence_upper = float(numerical["endpoint_velocity_difference_upper_m_s"])
    flight = acceptance["flight_ephemeris_validation"]
    improvement_lower = float(flight["required_improvement_fraction_over_weak_baseline"])
    lunar_ids = set(flight["lunar_flyby_validation_arc"]["window_ids"])

    nominal_settings = ForceModelSettings.for_fidelity("F2")
    tightened_settings = nominal_settings.tightened()
    for window in windows:
        references = reference_states_for_window(ephemeris, window)
        initial = np.asarray(references[0].position_km + references[0].velocity_km_s)
        times = [(state.epoch - window.start).total_seconds() for state in references]
        nominal = propagate(
            window.start,
            initial,
            window.duration_s,
            nominal_settings,
            jpl,
            evaluation_times_s=times,
        )
        tightened = propagate(
            window.start,
            initial,
            window.duration_s,
            tightened_settings,
            jpl,
        )
        nominal_endpoints[window.window_id] = nominal.endpoint[:6].copy()
        position_difference = float(
            np.linalg.norm(nominal.endpoint[:3] - tightened.endpoint[:3])
        )
        velocity_difference = 1000.0 * float(
            np.linalg.norm(nominal.endpoint[3:6] - tightened.endpoint[3:6])
        )
        position_status = upper_bound_status(
            position_difference, position_convergence_upper
        )
        velocity_status = upper_bound_status(
            velocity_difference, velocity_convergence_upper
        )
        convergence_row: dict[str, Any] = {
            "window_id": window.window_id,
            "phase": window.phase,
            "start_utc": iso_utc(window.start),
            "stop_utc": iso_utc(window.stop),
            "duration_s": number(window.duration_s, 1),
            "nominal_rtol": f"{nominal_settings.rtol:.1e}",
            "nominal_atol": f"{nominal_settings.atol:.1e}",
            "nominal_max_step_s": number(nominal_settings.max_step_s, 1),
            "tightened_rtol": f"{tightened_settings.rtol:.1e}",
            "tightened_atol": f"{tightened_settings.atol:.1e}",
            "tightened_max_step_s": number(tightened_settings.max_step_s, 1),
        }
        for index, label in enumerate(("x_km", "y_km", "z_km", "vx_km_s", "vy_km_s", "vz_km_s")):
            convergence_row[f"nominal_endpoint_{label}"] = number(nominal.endpoint[index], 15)
            convergence_row[f"tightened_endpoint_{label}"] = number(tightened.endpoint[index], 15)
        convergence_row.update(
            {
                "endpoint_position_difference_km": number(position_difference),
                "position_upper_km": number(position_convergence_upper),
                "position_status": position_status,
                "endpoint_velocity_difference_m_s": number(velocity_difference),
                "velocity_upper_m_s": number(velocity_convergence_upper),
                "velocity_status": velocity_status,
                "overall_status": "pass"
                if position_status == velocity_status == "pass"
                else "fail",
            }
        )
        convergence_rows.append(convergence_row)
        add_acceptance(
            summary,
            check_id=f"{window.window_id}_convergence_position",
            category="numerical_convergence",
            subject=window.window_id,
            metric="endpoint_position_difference",
            value=number(position_difference),
            unit="km",
            comparison="<=",
            threshold=number(position_convergence_upper),
            status=position_status,
            evidence_file="numerical_convergence.csv",
        )
        add_acceptance(
            summary,
            check_id=f"{window.window_id}_convergence_velocity",
            category="numerical_convergence",
            subject=window.window_id,
            metric="endpoint_velocity_difference",
            value=number(velocity_difference),
            unit="m/s",
            comparison="<=",
            threshold=number(velocity_convergence_upper),
            status=velocity_status,
            evidence_file="numerical_convergence.csv",
        )

        metrics = trajectory_error_metrics(nominal.states[:, :6], references)
        limits = (
            flight["lunar_flyby_validation_arc"]
            if window.window_id in lunar_ids
            else flight["non_lunar_validation_arcs"]
        )
        baseline = baselines[window.window_id]
        metric_specs = (
            ("position_rmse", metrics.position_rmse_km, float(limits["position_rmse_upper_km"]), "km"),
            ("position_endpoint", metrics.position_endpoint_km, float(limits["position_endpoint_upper_km"]), "km"),
            ("velocity_rmse", metrics.velocity_rmse_m_s, float(limits["velocity_rmse_upper_m_s"]), "m/s"),
            ("velocity_endpoint", metrics.velocity_endpoint_m_s, float(limits["velocity_endpoint_upper_m_s"]), "m/s"),
        )
        statuses: list[str] = []
        result: dict[str, Any] = {
            "window_id": window.window_id,
            "phase": window.phase,
            "start_utc": iso_utc(window.start),
            "stop_utc": iso_utc(window.stop),
            "samples": metrics.samples,
            "reference_release": ephemeris.path.name,
            "reference_role": "eligible historical/reconstructed public operational solution; not raw telemetry",
            "model": "F2 Earth-Moon-Sun point masses plus Earth J2",
        }
        metric_values = {
            "position_rmse": metrics.position_rmse_km,
            "position_endpoint": metrics.position_endpoint_km,
            "velocity_rmse": metrics.velocity_rmse_m_s,
            "velocity_endpoint": metrics.velocity_endpoint_m_s,
        }
        baseline_fields = {
            "position_rmse": "position_rmse_km",
            "position_endpoint": "position_endpoint_km",
            "velocity_rmse": "velocity_rmse_m_s",
            "velocity_endpoint": "velocity_endpoint_m_s",
        }
        for metric_name, value, upper, unit in metric_specs:
            status = upper_bound_status(value, upper)
            statuses.append(status)
            result[f"{metric_name}_{'m_s' if unit == 'm/s' else 'km'}"] = number(value)
            result[f"{metric_name}_upper_{'m_s' if unit == 'm/s' else 'km'}"] = number(upper)
            result[f"{metric_name}_status"] = status
            add_acceptance(
                summary,
                check_id=f"{window.window_id}_{metric_name}_absolute",
                category="flight_ephemeris_validation",
                subject=window.window_id,
                metric=metric_name,
                value=number(value),
                unit=unit,
                comparison="<=",
                threshold=number(upper),
                status=status,
                evidence_file="f2_flight_validation.csv",
            )
            baseline_value = float(baseline[baseline_fields[metric_name]])
            improvement = relative_improvement(baseline_value, metric_values[metric_name])
            improvement_status = lower_bound_status(improvement, improvement_lower)
            statuses.append(improvement_status)
            result[f"baseline_{metric_name}_{'m_s' if unit == 'm/s' else 'km'}"] = number(baseline_value)
            result[f"{metric_name}_improvement_fraction"] = number(improvement)
            result[f"{metric_name}_improvement_status"] = improvement_status
            add_acceptance(
                summary,
                check_id=f"{window.window_id}_{metric_name}_improvement",
                category="weak_baseline_improvement",
                subject=window.window_id,
                metric=f"{metric_name}_improvement_fraction",
                value=number(improvement),
                unit="fraction",
                comparison=">=",
                threshold=number(improvement_lower),
                status=improvement_status,
                evidence_file="f2_flight_validation.csv",
                note="Applied to each frozen RMSE and endpoint error metric.",
            )
        result["required_improvement_fraction"] = number(improvement_lower)
        result["overall_status"] = "pass" if all(status == "pass" for status in statuses) else "fail"
        flight_rows.append(result)
    return convergence_rows, flight_rows, nominal_endpoints


def event_evidence(
    ephemeris: OemEphemeris,
    jpl: JplEphemeris,
    windows: list[ValidationWindow],
    acceptance: dict[str, Any],
    summary: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    registry = {row["event_id"]: row for row in read_csv(EVENTS_PATH)}
    tolerance = float(acceptance["event_cross_checks"]["timing_tolerance_s"])
    lunar_window = next(window for window in windows if window.window_id == "V03")
    rows: list[dict[str, Any]] = []
    for required_name, event_id in REQUIRED_EVENTS.items():
        event = registry[event_id]
        public_epoch = parse_utc(event["actual_utc"])
        estimated_epoch: datetime | None = None
        distance_km = ""
        method = ""
        note = event["qualification_note"]
        if public_epoch > ephemeris.creation_time:
            status = "not_eligible"
            timing_error = ""
            method = "event occurs after the frozen OEM creation cutoff"
            note = (
                f"{note} The event is not eligible for historical/reconstructed "
                "OEM validation and remains unresolved at Gate 3."
            )
        elif required_name == "lunar closest approach":
            estimated_epoch, distance = closest_lunar_approach(
                ephemeris, jpl, lunar_window
            )
            distance_km = number(distance)
            timing_error_value = abs((estimated_epoch - public_epoch).total_seconds())
            timing_error = number(timing_error_value, 3)
            status = upper_bound_status(timing_error_value, tolerance)
            method = "minimum OEM spacecraft-to-DE440s Moon distance inside V03"
        else:
            estimated_epoch = nearest_irregular_oem_epoch(ephemeris, public_epoch)
            timing_error_value = abs((estimated_epoch - public_epoch).total_seconds())
            timing_error = number(timing_error_value, 3)
            status = upper_bound_status(timing_error_value, tolerance)
            method = "nearest eligible OEM epoch adjacent to a non-nominal cadence interval"
        row = {
            "event_id": event_id,
            "required_event": required_name,
            "registry_event_name": event["event_name"],
            "public_actual_utc": iso_utc(public_epoch),
            "public_time_precision": event["time_precision"],
            "oem_creation_cutoff_utc": iso_utc(ephemeris.creation_time),
            "evidence_method": method,
            "estimated_event_utc": iso_utc(estimated_epoch) if estimated_epoch else "",
            "timing_error_s": timing_error,
            "timing_tolerance_s": number(tolerance, 3),
            "spacecraft_to_moon_distance_km": distance_km,
            "status": status,
            "qualification_note": note,
        }
        rows.append(row)
        add_acceptance(
            summary,
            check_id=f"event_{required_name.lower().replace(' ', '_')}",
            category="event_cross_checks",
            subject=required_name,
            metric="absolute_timing_error",
            value=timing_error,
            unit="s",
            comparison="<=",
            threshold=number(tolerance, 3),
            status=status,
            evidence_file="event_cross_checks.csv",
            note=note,
        )
    return rows


def detect_gmat_console(requested: Path | None) -> Path | None:
    candidates: list[Path] = []
    if requested:
        candidates.append(requested)
    if os.environ.get("GMAT_CONSOLE"):
        candidates.append(Path(os.environ["GMAT_CONSOLE"]))
    command = shutil.which("GmatConsole") or shutil.which("GmatConsole.exe")
    if command:
        candidates.append(Path(command))
    candidates.extend(
        [
            ROOT.parent
            / "openqfuel_handoff_staging/gmat-win-R2026a/bin/GmatConsole.exe",
            Path("C:/Program Files/GMAT/R2026a/bin/GmatConsole.exe"),
        ]
    )
    return next((candidate.resolve() for candidate in candidates if candidate.is_file()), None)


def gmat_evidence(
    console: Path | None,
    windows: list[ValidationWindow],
    ephemeris: OemEphemeris,
    python_endpoints: dict[str, np.ndarray],
    acceptance: dict[str, Any],
    summary: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], str]:
    GMAT_SCRIPT_PATH.parent.mkdir(parents=True, exist_ok=True)
    GMAT_SCRIPT_PATH.write_text(
        render_gmat_script(windows, ephemeris), encoding="utf-8", newline="\n"
    )
    config = acceptance["numerical_verification"]["independent_tool"]
    position_upper = float(config["same_force_model_position_endpoint_difference_upper_km"])
    velocity_upper = float(config["same_force_model_velocity_endpoint_difference_upper_m_s"])
    tool_note = "NASA GMAT R2026a was not found; comparison remains pending."
    endpoints: dict[int, np.ndarray] = {}
    executable_sha = ""
    archive_sha = ""
    execution_status = "pending"

    if console is not None:
        executable_sha = sha256_file(console)
        archive = console.parent.parent.with_suffix(".zip")
        if archive.is_file():
            archive_sha = sha256_file(archive)
        output_path = console.parent.parent / "output/gate3_gmat_endpoints.txt"
        output_path.unlink(missing_ok=True)
        completed = subprocess.run(
            [str(console), "--run", str(GMAT_SCRIPT_PATH)],
            cwd=console.parent,
            capture_output=True,
            text=True,
            timeout=300,
            check=False,
        )
        if completed.returncode == 0 and output_path.is_file():
            try:
                endpoints = parse_gmat_endpoint_report(output_path)
            except ValueError as exc:
                tool_note = f"GMAT ran but its endpoint report was unreadable: {exc}"
            else:
                execution_status = "completed"
                tool_note = "NASA GMAT R2026a console completed the generated same-force script."
        else:
            diagnostic = (completed.stderr or completed.stdout).strip().splitlines()
            detail = diagnostic[-1] if diagnostic else f"exit code {completed.returncode}"
            tool_note = f"GMAT execution did not produce endpoint evidence: {detail}"

    rows: list[dict[str, Any]] = []
    for index, window in enumerate(windows, start=1):
        python_endpoint = python_endpoints[window.window_id]
        gmat_endpoint = endpoints.get(index)
        if gmat_endpoint is None:
            position_difference = ""
            velocity_difference = ""
            position_status = "pending"
            velocity_status = "pending"
        else:
            position_value = float(np.linalg.norm(python_endpoint[:3] - gmat_endpoint[:3]))
            velocity_value = 1000.0 * float(
                np.linalg.norm(python_endpoint[3:6] - gmat_endpoint[3:6])
            )
            position_difference = number(position_value)
            velocity_difference = number(velocity_value)
            position_status = upper_bound_status(position_value, position_upper)
            velocity_status = upper_bound_status(velocity_value, velocity_upper)
        row: dict[str, Any] = {
            "window_id": window.window_id,
            "tool": "NASA GMAT R2026a",
            "execution_status": execution_status,
            "gmat_executable_sha256": executable_sha,
            "gmat_archive_sha256": archive_sha,
            "model": "DE440s SPICE; Earth exact point mass and J2; Luna and Sun exact point masses; no drag/SRP/relativity/tides",
            "gmat_integrator": "RungeKutta89 accuracy=1e-13 max_step=150 s",
        }
        for component, value in zip(
            ("x_km", "y_km", "z_km", "vx_km_s", "vy_km_s", "vz_km_s"),
            python_endpoint,
        ):
            row[f"python_endpoint_{component}"] = number(float(value), 15)
        for component, value in zip(
            ("x_km", "y_km", "z_km", "vx_km_s", "vy_km_s", "vz_km_s"),
            gmat_endpoint if gmat_endpoint is not None else [""] * 6,
        ):
            row[f"gmat_endpoint_{component}"] = (
                number(float(value), 15) if value != "" else ""
            )
        row.update(
            {
                "endpoint_position_difference_km": position_difference,
                "position_upper_km": number(position_upper),
                "position_status": position_status,
                "endpoint_velocity_difference_m_s": velocity_difference,
                "velocity_upper_m_s": number(velocity_upper),
                "velocity_status": velocity_status,
                "overall_status": "pass"
                if position_status == velocity_status == "pass"
                else "fail"
                if "fail" in {position_status, velocity_status}
                else "pending",
                "note": tool_note,
            }
        )
        rows.append(row)
        add_acceptance(
            summary,
            check_id=f"{window.window_id}_gmat_position",
            category="independent_gmat",
            subject=window.window_id,
            metric="endpoint_position_difference",
            value=position_difference,
            unit="km",
            comparison="<=",
            threshold=number(position_upper),
            status=position_status,
            evidence_file="gmat_comparison.csv",
            note=tool_note,
        )
        add_acceptance(
            summary,
            check_id=f"{window.window_id}_gmat_velocity",
            category="independent_gmat",
            subject=window.window_id,
            metric="endpoint_velocity_difference",
            value=velocity_difference,
            unit="m/s",
            comparison="<=",
            threshold=number(velocity_upper),
            status=velocity_status,
            evidence_file="gmat_comparison.csv",
            note=tool_note,
        )
    return rows, tool_note


def markdown_table(headers: list[str], rows: Iterable[Iterable[Any]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "|" + "|".join("---" for _ in headers) + "|",
    ]
    lines.extend("| " + " | ".join(str(value) for value in row) + " |" for row in rows)
    return "\n".join(lines)


def write_report(
    status: str,
    ephemeris: OemEphemeris,
    interpolation: list[dict[str, Any]],
    convergence: list[dict[str, Any]],
    flight: list[dict[str, Any]],
    events: list[dict[str, Any]],
    gmat: list[dict[str, Any]],
    summary: list[dict[str, Any]],
    gmat_note: str,
) -> None:
    failed = [row for row in summary if row["status"] == "fail"]
    pending = [
        row for row in summary if row["status"] in {"pending", "not_eligible"}
    ]
    evaluated = [row for row in summary if row["status"] in {"pass", "fail"}]
    result_text = {
        "failed_repair_required": (
            "Gate 3 failed its frozen acceptance criteria and is in "
            "`failed_repair_required` status. ML and QML work remains prohibited."
        ),
        "pending_external_validation": (
            "Gate 3 is incomplete because required evidence remains pending. "
            "ML and QML work remains prohibited."
        ),
        "passed_pending_human_acceptance": (
            "All frozen criteria passed; Gate 3 now requires explicit human acceptance "
            "before any ML or QML work."
        ),
    }[status]
    interpolation_row = interpolation[0]
    content = [
        "# Gate 3 simulator credibility validation",
        "",
        f"Status: `{status}`  ",
        f"Generated: {datetime.now(UTC).date().isoformat()}  ",
        "Decision authority: Human research lead",
        "",
        "## Technical summary",
        "",
        result_text,
        "",
        f"The run evaluated {len(evaluated)} numeric acceptance checks: "
        f"{len(failed)} failed and {len(pending)} required checks are pending or not eligible. "
        "The public OEM is an operational trajectory solution, not raw telemetry, and "
        "all conclusions are limited to the frozen public-data model.",
        "",
        "## Frozen criteria produced a gate decision",
        "",
        markdown_table(
            ["Category", "Passed", "Failed", "Pending/not eligible"],
            [
                (
                    category,
                    sum(row["status"] == "pass" for row in summary if row["category"] == category),
                    sum(row["status"] == "fail" for row in summary if row["category"] == category),
                    sum(row["status"] in {"pending", "not_eligible"} for row in summary if row["category"] == category),
                )
                for category in dict.fromkeys(row["category"] for row in summary)
            ],
        ),
        "",
        "Every failed criterion is retained in `data/processed/simulator/acceptance_summary.csv`; "
        "thresholds, windows, exclusions, and source roles were not changed after viewing results.",
        "",
        "## Interpolation met its parser-quality thresholds",
        "",
        f"Leave-one-out cubic Hermite interpolation used {interpolation_row['sample_count']} eligible "
        "clean-coast points. Segments touching any frozen 30-minute discontinuity buffer were excluded.",
        "",
        markdown_table(
            ["Metric", "Observed", "Upper bound", "Status"],
            [
                (
                    "Position p95 (km)",
                    interpolation_row["position_p95_km"],
                    interpolation_row["position_upper_km"],
                    interpolation_row["position_status"],
                ),
                (
                    "Velocity p95 (m/s)",
                    interpolation_row["velocity_p95_m_s"],
                    interpolation_row["velocity_upper_m_s"],
                    interpolation_row["velocity_status"],
                ),
            ],
        ),
        "",
        "## Numerical convergence was checked on every frozen window",
        "",
        "Nominal F2 propagation was compared with tolerances tightened by 100x and maximum step halved. "
        "The table reports six-hour endpoint differences; full endpoint states and solver settings are in the CSV.",
        "",
        markdown_table(
            ["Window", "Position difference (km)", "Velocity difference (m/s)", "Status"],
            [
                (
                    row["window_id"],
                    row["endpoint_position_difference_km"],
                    row["endpoint_velocity_difference_m_s"],
                    row["overall_status"],
                )
                for row in convergence
            ],
        ),
        "",
        "## Flight-ephemeris validation exposed the F2 result",
        "",
        "Each window starts from its OEM state and is compared at every public reference epoch. "
        "The 80% weak-baseline improvement rule is applied conservatively to all four error metrics.",
        "",
        markdown_table(
            ["Window", "Position RMSE (km)", "Velocity RMSE (m/s)", "Overall"],
            [
                (
                    row["window_id"],
                    row["position_rmse_km"],
                    row["velocity_rmse_m_s"],
                    row["overall_status"],
                )
                for row in flight
            ],
        ),
        "",
        "This is a descriptive validation against a public operational ephemeris. It does not establish "
        "flight truth, causal model adequacy, or operational certification.",
        "",
        "## Event checks preserve source eligibility",
        "",
        "Burn timing uses the nearest eligible OEM epoch adjacent to a non-nominal cadence interval. "
        "Lunar closest approach is the OEM-to-DE440s distance minimum inside V03. Rounded public event "
        "times are used only for temporal alignment.",
        "",
        markdown_table(
            ["Event", "Estimated UTC", "Error (s)", "Status"],
            [
                (
                    row["required_event"],
                    row["estimated_event_utc"] or "not eligible",
                    row["timing_error_s"] or "n/a",
                    row["status"],
                )
                for row in events
            ],
        ),
        "",
        "## GMAT provides the independent same-force comparison",
        "",
        gmat_note,
        "",
        "The generated `scripts/gmat/gate3_same_force_model.script` uses DE440s through SPICE, "
        "Earth point mass and J2, Luna and Sun point masses, no drag or SRP, and a tight "
        "RungeKutta89 propagation. Executable and archive hashes are retained in the comparison CSV.",
        "",
        markdown_table(
            ["Window", "Position difference (km)", "Velocity difference (m/s)", "Status"],
            [
                (
                    row["window_id"],
                    row["endpoint_position_difference_km"] or "pending",
                    row["endpoint_velocity_difference_m_s"] or "pending",
                    row["overall_status"],
                )
                for row in gmat
            ],
        ),
        "",
        "## Scope, data, and metric definitions",
        "",
        f"- Reference release: `{ephemeris.path.name}`.",
        f"- Eligible reference cutoff: `{iso_utc(ephemeris.creation_time)}`.",
        "- Validation cohort: V01-V05, five frozen six-hour coast windows in UTC.",
        "- Position errors: Euclidean EME2000/EarthMJ2000Eq differences in kilometres.",
        "- Velocity errors: Euclidean inertial differences converted to metres per second.",
        "- Weak baseline: tracked Earth-only DOP853 results in `two_body_baseline.csv`.",
        "- No calibration, threshold changes, window changes, or post-result exclusions were performed.",
        "",
        "Exact audit tables are used instead of charts because each validation family has only five "
        "frozen windows and the gate decision depends on per-window thresholds, not a visual trend.",
        "",
        "## Limitations and robustness boundaries",
        "",
        "- The OEM is not raw tracking or spacecraft telemetry.",
        "- The fixed 2026 UTC-to-TT conversion omits a sub-2 ms periodic TDB term.",
        "- F2 omits solar-radiation pressure, attitude, and mission-owned force and navigation details.",
        "- RTC3 cannot be checked against eligible historical/reconstructed rows when it occurs after the OEM creation cutoff.",
        "- Passing numerical or cross-tool checks would not establish flight readiness.",
        "",
        "## Required next step",
        "",
    ]
    if status == "failed_repair_required":
        content.extend(
            [
                "Publish and review the failed criteria. Any repair requires a dated protocol deviation; "
                "do not change thresholds, windows, splits, or exclusions, and do not begin ML or QML training.",
                "",
                "Decision requested from the human research lead: reject Gate 3 as currently implemented "
                "or authorize a documented simulator-repair protocol deviation.",
            ]
        )
    elif status == "pending_external_validation":
        content.extend(
            [
                "Resolve the pending independent or source-eligibility evidence before a Gate 3 decision. "
                "Do not begin ML or QML training.",
                "",
                "Decision requested from the human research lead: keep Gate 3 open pending the listed evidence.",
            ]
        )
    else:
        content.extend(
            [
                "The human research lead must explicitly accept or reject Gate 3. Do not begin Phase 4 "
                "or any ML/QML experiment until that decision is recorded in `docs/decision_log.md`.",
                "",
                "Decision requested from the human research lead: accept or reject Gate 3.",
            ]
        )
    REPORT_PATH.write_text("\n".join(content) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--oem", type=Path, default=DEFAULT_OEM)
    parser.add_argument("--kernel", type=Path, default=DEFAULT_KERNEL)
    parser.add_argument("--gmat-console", type=Path)
    args = parser.parse_args()

    with ACCEPTANCE_PATH.open(encoding="utf-8") as handle:
        acceptance = yaml.safe_load(handle)
    ephemeris = parse_oem(args.oem)
    expected_kernel_sha = acceptance["reference_data"].get("de440s_sha256")
    if expected_kernel_sha is None:
        with (ROOT / "configs/dynamics.yaml").open(encoding="utf-8") as handle:
            expected_kernel_sha = yaml.safe_load(handle)["public_ephemeris"]["sha256"]
    windows = load_windows()
    summary: list[dict[str, Any]] = []
    interpolation = interpolation_evidence(ephemeris, acceptance, summary)
    with JplEphemeris(args.kernel, expected_kernel_sha) as jpl:
        convergence, flight, python_endpoints = propagate_windows(
            ephemeris,
            jpl,
            windows,
            read_csv(BASELINE_PATH),
            acceptance,
            summary,
        )
        events = event_evidence(ephemeris, jpl, windows, acceptance, summary)
    gmat, gmat_note = gmat_evidence(
        detect_gmat_console(args.gmat_console),
        windows,
        ephemeris,
        python_endpoints,
        acceptance,
        summary,
    )

    gate_status = aggregate_gate_status(row["status"] for row in summary)
    add_acceptance(
        summary,
        check_id="gate3_overall",
        category="overall",
        subject="Gate 3 simulator credibility",
        metric="all required frozen criteria",
        value="",
        unit="",
        comparison="all",
        threshold="pass",
        status=gate_status,
        evidence_file="acceptance_summary.csv",
        note="Human acceptance is required even when all technical criteria pass.",
    )
    write_csv(OUTPUT_DIR / "interpolation_validation.csv", interpolation)
    write_csv(OUTPUT_DIR / "numerical_convergence.csv", convergence)
    write_csv(OUTPUT_DIR / "f2_flight_validation.csv", flight)
    write_csv(OUTPUT_DIR / "event_cross_checks.csv", events)
    write_csv(OUTPUT_DIR / "gmat_comparison.csv", gmat)
    write_csv(OUTPUT_DIR / "acceptance_summary.csv", summary)
    write_report(
        gate_status,
        ephemeris,
        interpolation,
        convergence,
        flight,
        events,
        gmat,
        summary[:-1],
        gmat_note,
    )
    print(f"Gate 3 status: {gate_status}")
    print(f"Wrote validation evidence to {OUTPUT_DIR}")
    print(f"Wrote credibility report to {REPORT_PATH}")
    return 1 if gate_status == "failed_repair_required" else 0


if __name__ == "__main__":
    raise SystemExit(main())
