"""Reusable metrics and evidence helpers for Gate 3 simulator validation."""

from __future__ import annotations

import math
import re
import statistics
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np
from scipy.optimize import minimize_scalar

from .ephemeris import JplEphemeris
from .oem import OemEphemeris, StateVector


UTC = timezone.utc


@dataclass(frozen=True)
class ValidationWindow:
    window_id: str
    phase: str
    start: datetime
    stop: datetime

    @property
    def duration_s(self) -> float:
        return (self.stop - self.start).total_seconds()


@dataclass(frozen=True)
class ErrorMetrics:
    samples: int
    position_rmse_km: float
    position_endpoint_km: float
    velocity_rmse_m_s: float
    velocity_endpoint_m_s: float


@dataclass(frozen=True)
class InterpolationMetrics:
    samples: int
    position_p95_km: float
    velocity_p95_m_s: float
    position_max_km: float
    velocity_max_m_s: float


def iso_utc(value: datetime) -> str:
    """Format a timezone-aware timestamp as canonical UTC."""

    if value.tzinfo is None:
        raise ValueError("UTC timestamps must be timezone-aware")
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def rms(values: Sequence[float]) -> float:
    """Return the root mean square of a nonempty sequence."""

    if not values:
        raise ValueError("RMS requires at least one value")
    return math.sqrt(math.fsum(value * value for value in values) / len(values))


def relative_improvement(baseline: float, candidate: float) -> float:
    """Return fractional error reduction relative to a positive baseline."""

    if baseline <= 0:
        raise ValueError("The comparison baseline must be positive")
    return (baseline - candidate) / baseline


def upper_bound_status(value: float, upper: float) -> str:
    return "pass" if value <= upper else "fail"


def lower_bound_status(value: float, lower: float) -> str:
    return "pass" if value >= lower else "fail"


def aggregate_gate_status(statuses: Iterable[str]) -> str:
    """Map criterion statuses to the frozen Gate 3 release state."""

    values = tuple(statuses)
    if not values:
        raise ValueError("At least one acceptance status is required")
    if "fail" in values:
        return "failed_repair_required"
    if any(value in {"pending", "not_eligible"} for value in values):
        return "pending_external_validation"
    if all(value == "pass" for value in values):
        return "passed_pending_human_acceptance"
    raise ValueError(f"Unknown acceptance statuses: {sorted(set(values))}")


def _norm(left: Sequence[float], right: Sequence[float]) -> float:
    return float(np.linalg.norm(np.asarray(left, dtype=float) - np.asarray(right)))


def _overlaps_exclusion(
    start: datetime,
    stop: datetime,
    exclusions: Sequence[tuple[datetime, datetime]],
) -> bool:
    return any(start <= excluded_stop and stop >= excluded_start for excluded_start, excluded_stop in exclusions)


def leave_one_out_interpolation_metrics(
    ephemeris: OemEphemeris,
    exclusions: Sequence[tuple[datetime, datetime]],
) -> InterpolationMetrics:
    """Evaluate Hermite leave-one-out errors on eligible clean-coast points."""

    position_errors: list[float] = []
    velocity_errors: list[float] = []
    for index in range(1, len(ephemeris.states) - 1):
        left = ephemeris.states[index - 1]
        target = ephemeris.states[index]
        right = ephemeris.states[index + 1]
        if right.epoch > ephemeris.creation_time:
            continue
        if _overlaps_exclusion(left.epoch, right.epoch, exclusions):
            continue

        pair = OemEphemeris(
            ephemeris.path,
            ephemeris.header,
            (left, right),
            ephemeris.wrapper_prefix_lines,
        )
        interpolated = pair.interpolate(target.epoch)
        position_errors.append(
            _norm(interpolated.position_km, target.position_km)
        )
        velocity_errors.append(
            1000.0 * _norm(interpolated.velocity_km_s, target.velocity_km_s)
        )

    if not position_errors:
        raise ValueError("No eligible leave-one-out interpolation points remain")
    return InterpolationMetrics(
        samples=len(position_errors),
        position_p95_km=float(np.percentile(position_errors, 95.0)),
        velocity_p95_m_s=float(np.percentile(velocity_errors, 95.0)),
        position_max_km=max(position_errors),
        velocity_max_m_s=max(velocity_errors),
    )


def reference_states_for_window(
    ephemeris: OemEphemeris,
    window: ValidationWindow,
) -> tuple[StateVector, ...]:
    """Return OEM samples spanning a frozen window, including exact endpoints."""

    if window.start < ephemeris.start_time or window.stop > ephemeris.creation_time:
        raise ValueError(f"{window.window_id} is outside the eligible OEM interval")
    states = [
        state
        for state in ephemeris.states
        if window.start <= state.epoch <= window.stop
    ]
    if not states or states[0].epoch != window.start:
        states.insert(0, ephemeris.interpolate(window.start))
    if states[-1].epoch != window.stop:
        states.append(ephemeris.interpolate(window.stop))
    return tuple(states)


def trajectory_error_metrics(
    predicted_states: np.ndarray,
    reference_states: Sequence[StateVector],
) -> ErrorMetrics:
    """Calculate position and velocity RMSE and endpoint errors."""

    predicted = np.asarray(predicted_states, dtype=float)
    if predicted.shape != (len(reference_states), 6):
        raise ValueError("Predicted and reference trajectories must align at six-state grain")
    position_errors = [
        _norm(state[:3], reference.position_km)
        for state, reference in zip(predicted, reference_states)
    ]
    velocity_errors = [
        1000.0 * _norm(state[3:6], reference.velocity_km_s)
        for state, reference in zip(predicted, reference_states)
    ]
    return ErrorMetrics(
        samples=len(reference_states),
        position_rmse_km=rms(position_errors),
        position_endpoint_km=position_errors[-1],
        velocity_rmse_m_s=rms(velocity_errors),
        velocity_endpoint_m_s=velocity_errors[-1],
    )


def nearest_irregular_oem_epoch(
    ephemeris: OemEphemeris,
    event_epoch: datetime,
    cadence_tolerance_s: float = 1.0,
) -> datetime:
    """Find the nearest eligible OEM epoch adjacent to a cadence transition."""

    eligible = [state for state in ephemeris.states if state.epoch <= ephemeris.creation_time]
    intervals = [
        (right.epoch - left.epoch).total_seconds()
        for left, right in zip(eligible, eligible[1:])
    ]
    nominal = statistics.median(intervals)
    candidates: list[datetime] = []
    for index, state in enumerate(eligible):
        adjacent = []
        if index > 0:
            adjacent.append((state.epoch - eligible[index - 1].epoch).total_seconds())
        if index < len(eligible) - 1:
            adjacent.append((eligible[index + 1].epoch - state.epoch).total_seconds())
        if any(abs(interval - nominal) > cadence_tolerance_s for interval in adjacent):
            candidates.append(state.epoch)
    if not candidates:
        raise ValueError("No irregular OEM cadence epochs were found")
    return min(candidates, key=lambda epoch: abs((epoch - event_epoch).total_seconds()))


def closest_lunar_approach(
    ephemeris: OemEphemeris,
    jpl: JplEphemeris,
    window: ValidationWindow,
) -> tuple[datetime, float]:
    """Find the OEM-to-DE440s lunar distance minimum inside a frozen window."""

    def distance(elapsed_s: float) -> float:
        epoch = window.start + timedelta(seconds=float(elapsed_s))
        spacecraft = ephemeris.interpolate(epoch).position_km
        moon = jpl.positions(epoch).moon_km
        return _norm(spacecraft, moon)

    result = minimize_scalar(
        distance,
        bounds=(0.0, window.duration_s),
        method="bounded",
        options={"xatol": 0.01},
    )
    if not result.success:
        raise RuntimeError(f"Closest-approach search failed: {result.message}")
    epoch = window.start + timedelta(seconds=float(result.x))
    return epoch, float(result.fun)


def _gmat_epoch(value: datetime) -> str:
    utc = value.astimezone(UTC)
    return utc.strftime("%d %b %Y %H:%M:%S.") + f"{utc.microsecond // 1000:03d}"


def render_gmat_script(
    windows: Sequence[ValidationWindow],
    ephemeris: OemEphemeris,
) -> str:
    """Render the independent R2026a same-force-model endpoint comparison."""

    lines = [
        "% OpenQFuel-Cislunar Gate 3 independent comparison",
        "% Required tool: NASA GMAT R2026a",
        "% Frame: EarthMJ2000Eq (OEM EME2000-compatible inertial axes)",
        "% Forces: Earth point mass and J2, Luna point mass, Sun point mass",
        "% Disabled: drag, SRP, tides, and relativistic correction",
        "SolarSystem.EphemerisSource = 'SPICE';",
        "SolarSystem.SPKFilename = '../../data/raw/ephemeris/de440s.bsp';",
        "Luna.Mu = 4902.800118;",
        "Sun.Mu = 132712440041.9394;",
        "",
    ]
    for window in windows:
        state = ephemeris.interpolate(window.start)
        values = state.position_km + state.velocity_km_s
        lines.extend(
            [
                f"Create Spacecraft {window.window_id};",
                f"{window.window_id}.DateFormat = UTCGregorian;",
                f"{window.window_id}.Epoch = '{_gmat_epoch(window.start)}';",
                f"{window.window_id}.CoordinateSystem = EarthMJ2000Eq;",
                f"{window.window_id}.DisplayStateType = Cartesian;",
                f"{window.window_id}.X = {values[0]:.15f};",
                f"{window.window_id}.Y = {values[1]:.15f};",
                f"{window.window_id}.Z = {values[2]:.15f};",
                f"{window.window_id}.VX = {values[3]:.15f};",
                f"{window.window_id}.VY = {values[4]:.15f};",
                f"{window.window_id}.VZ = {values[5]:.15f};",
                "",
            ]
        )
    lines.extend(
        [
            "Create ForceModel F2ForceModel;",
            "F2ForceModel.CentralBody = Earth;",
            "F2ForceModel.PrimaryBodies = {Earth};",
            "F2ForceModel.PointMasses = {Luna, Sun};",
            "F2ForceModel.Drag = None;",
            "F2ForceModel.SRP = Off;",
            "F2ForceModel.RelativisticCorrection = Off;",
            "F2ForceModel.ErrorControl = RSSStep;",
            "F2ForceModel.GravityField.Earth.Degree = 2;",
            "F2ForceModel.GravityField.Earth.Order = 0;",
            "F2ForceModel.GravityField.Earth.PotentialFile = '../../configs/gmat_earth_j2.cof';",
            "F2ForceModel.GravityField.Earth.TideModel = 'None';",
            "",
            "Create Propagator F2Propagator;",
            "F2Propagator.FM = F2ForceModel;",
            "F2Propagator.Type = RungeKutta89;",
            "F2Propagator.InitialStepSize = 60;",
            "F2Propagator.Accuracy = 1e-13;",
            "F2Propagator.MinStep = 0.001;",
            "F2Propagator.MaxStep = 150;",
            "F2Propagator.MaxStepAttempts = 50;",
            "F2Propagator.StopIfAccuracyIsViolated = true;",
            "",
            "Create ReportFile EndpointReport;",
            "EndpointReport.Filename = 'gate3_gmat_endpoints.txt';",
            "EndpointReport.Precision = 16;",
            "EndpointReport.WriteHeaders = false;",
            "Create Variable WindowIndex;",
            "",
            "BeginMissionSequence;",
        ]
    )
    for index, window in enumerate(windows, start=1):
        lines.extend(
            [
                f"Propagate F2Propagator({window.window_id}) "
                f"{{{window.window_id}.ElapsedSecs = {window.duration_s:.1f}}};",
                f"WindowIndex = {index};",
                "Report EndpointReport WindowIndex "
                f"{window.window_id}.ElapsedSecs "
                f"{window.window_id}.EarthMJ2000Eq.X "
                f"{window.window_id}.EarthMJ2000Eq.Y "
                f"{window.window_id}.EarthMJ2000Eq.Z "
                f"{window.window_id}.EarthMJ2000Eq.VX "
                f"{window.window_id}.EarthMJ2000Eq.VY "
                f"{window.window_id}.EarthMJ2000Eq.VZ;",
            ]
        )
    return "\n".join(lines) + "\n"


def parse_gmat_endpoint_report(path: Path | str) -> dict[int, np.ndarray]:
    """Parse window index, elapsed seconds, and six endpoint components."""

    rows: dict[int, np.ndarray] = {}
    number = re.compile(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][-+]?\d+)?")
    for line in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
        values = [float(item) for item in number.findall(line)]
        if len(values) != 8:
            continue
        index = int(round(values[0]))
        rows[index] = np.asarray(values[2:], dtype=float)
    if not rows:
        raise ValueError(f"No GMAT endpoint rows found in {path}")
    return rows
