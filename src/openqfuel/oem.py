"""Small, dependency-free reader for the public Artemis II CCSDS OEM files.

The parser deliberately accepts an HTML prefix because one file distributed in
NASA's archive wraps an otherwise valid OEM message in a web page.  It does not
interpret the separate PROP_MAN/M50 entry product.
"""

from __future__ import annotations

from bisect import bisect_left
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


UTC = timezone.utc


def parse_utc(value: str) -> datetime:
    """Parse a CCSDS UTC timestamp and return a timezone-aware datetime."""

    parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


@dataclass(frozen=True)
class StateVector:
    epoch: datetime
    position_km: tuple[float, float, float]
    velocity_km_s: tuple[float, float, float]


@dataclass(frozen=True)
class OemEphemeris:
    path: Path
    header: dict[str, str]
    states: tuple[StateVector, ...]
    wrapper_prefix_lines: int

    @property
    def creation_time(self) -> datetime:
        return parse_utc(self.header["CREATION_DATE"])

    @property
    def start_time(self) -> datetime:
        return self.states[0].epoch

    @property
    def stop_time(self) -> datetime:
        return self.states[-1].epoch

    def interpolate(self, epoch: datetime) -> StateVector:
        """Interpolate position and velocity with a cubic Hermite segment."""

        epoch = epoch.astimezone(UTC)
        epochs = [state.epoch for state in self.states]
        index = bisect_left(epochs, epoch)
        if index < len(epochs) and epochs[index] == epoch:
            return self.states[index]
        if index == 0 or index == len(epochs):
            raise ValueError(f"{epoch.isoformat()} lies outside the OEM interval")

        left = self.states[index - 1]
        right = self.states[index]
        interval_s = (right.epoch - left.epoch).total_seconds()
        fraction = (epoch - left.epoch).total_seconds() / interval_s

        u = fraction
        u2 = u * u
        u3 = u2 * u
        h00 = 2.0 * u3 - 3.0 * u2 + 1.0
        h10 = u3 - 2.0 * u2 + u
        h01 = -2.0 * u3 + 3.0 * u2
        h11 = u3 - u2

        position = tuple(
            h00 * left.position_km[axis]
            + h10 * interval_s * left.velocity_km_s[axis]
            + h01 * right.position_km[axis]
            + h11 * interval_s * right.velocity_km_s[axis]
            for axis in range(3)
        )

        dh00 = (6.0 * u2 - 6.0 * u) / interval_s
        dh10 = 3.0 * u2 - 4.0 * u + 1.0
        dh01 = (-6.0 * u2 + 6.0 * u) / interval_s
        dh11 = 3.0 * u2 - 2.0 * u
        velocity = tuple(
            dh00 * left.position_km[axis]
            + dh10 * left.velocity_km_s[axis]
            + dh01 * right.position_km[axis]
            + dh11 * right.velocity_km_s[axis]
            for axis in range(3)
        )
        return StateVector(epoch, position, velocity)


def _first_oem_line(lines: Iterable[str]) -> int:
    for index, line in enumerate(lines):
        if line.strip().startswith("CCSDS_OEM_VERS"):
            return index
    raise ValueError("No CCSDS_OEM_VERS record found")


def parse_oem(path: Path | str) -> OemEphemeris:
    """Read a CCSDS OEM 2.0 state-vector message."""

    path = Path(path)
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    start_index = _first_oem_line(lines)
    header: dict[str, str] = {}
    states: list[StateVector] = []

    for line in lines[start_index:]:
        stripped = line.strip()
        if not stripped or stripped.startswith("COMMENT"):
            continue

        fields = stripped.split()
        if len(fields) == 7 and "T" in fields[0]:
            try:
                numeric = tuple(float(value) for value in fields[1:])
            except ValueError:
                pass
            else:
                states.append(
                    StateVector(
                        epoch=parse_utc(fields[0]),
                        position_km=numeric[:3],
                        velocity_km_s=numeric[3:],
                    )
                )
                continue

        if "=" in stripped:
            key, value = stripped.split("=", 1)
            header[key.strip()] = value.strip()

    if header.get("CCSDS_OEM_VERS") != "2.0":
        raise ValueError(f"Unsupported CCSDS OEM version in {path}")
    if not states:
        raise ValueError(f"No state vectors found in {path}")
    if any(right.epoch <= left.epoch for left, right in zip(states, states[1:])):
        raise ValueError(f"Non-increasing state epochs in {path}")

    required = {
        "CREATION_DATE",
        "ORIGINATOR",
        "OBJECT_NAME",
        "CENTER_NAME",
        "REF_FRAME",
        "TIME_SYSTEM",
    }
    missing = required - header.keys()
    if missing:
        raise ValueError(f"Missing OEM metadata in {path}: {sorted(missing)}")
    return OemEphemeris(path, header, tuple(states), start_index)
