"""Crew-schedule and human-acceleration checks for candidate burns."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Sequence

import yaml

from .oem import parse_utc


@dataclass(frozen=True)
class ConstraintCheck:
    passed: bool
    violations: tuple[str, ...]


def _load_yaml(path: Path | str) -> dict:
    with Path(path).open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def acceleration_limit_m_s2(
    acceleration_config: dict,
    axis: str,
    sign: str,
    duration_s: float,
) -> float:
    """Return the conservative tabulated limit for an axis and duration."""

    if duration_s <= 0:
        raise ValueError("duration_s must be positive")
    envelope = acceleration_config["deconditioned_conservative_envelopes"][axis][
        sign
    ]
    durations = envelope["duration_s"]
    values = envelope["acceleration_m_s2"]
    if duration_s <= durations[0]:
        raw = values[0]
    else:
        raw = values[-1]
        for index in range(1, len(durations)):
            if duration_s <= durations[index]:
                adjacent = values[index - 1 : index + 1]
                raw = min(adjacent) if sign == "upper" else max(adjacent)
                break
    margin = float(acceleration_config["application_rule"]["margin_fraction"])
    return float(raw) * (1.0 - margin)


def check_candidate_burn(
    start_utc: datetime,
    duration_s: float,
    crew_axis_acceleration_m_s2: Sequence[float],
    crew_schedule_path: Path | str,
    acceleration_path: Path | str,
    emergency_override: bool = False,
    override_reason: str | None = None,
) -> ConstraintCheck:
    """Apply protected-sleep and per-axis acceleration limits."""

    if start_utc.tzinfo is None:
        raise ValueError("Burn time must be timezone-aware")
    if duration_s <= 0:
        raise ValueError("Burn duration must be positive")
    if len(crew_axis_acceleration_m_s2) != 3:
        raise ValueError("Crew acceleration must contain x, y, and z components")
    schedule = _load_yaml(crew_schedule_path)
    acceleration = _load_yaml(acceleration_path)
    violations: list[str] = []

    buffer = timedelta(minutes=schedule["policy"]["blackout_buffer_before_after_min"])
    burn_stop = start_utc + timedelta(seconds=duration_s)
    for interval in schedule["protected_intervals"]:
        protected_start = parse_utc(interval["start_utc"]) - buffer
        protected_stop = parse_utc(interval["stop_utc"]) + buffer
        if start_utc < protected_stop and burn_stop > protected_start:
            if not emergency_override:
                violations.append(f"protected_crew_interval:{interval['id']}")
            elif not override_reason:
                violations.append("emergency_override_missing_reason")

    for axis, value in zip(("x_axis", "y_axis", "z_axis"), crew_axis_acceleration_m_s2):
        upper = acceleration_limit_m_s2(acceleration, axis, "upper", duration_s)
        lower = acceleration_limit_m_s2(acceleration, axis, "lower", duration_s)
        if not lower <= value <= upper:
            violations.append(
                f"acceleration:{axis}:{value:.9g}_outside_[{lower:.9g},{upper:.9g}]"
            )
    return ConstraintCheck(not violations, tuple(violations))
