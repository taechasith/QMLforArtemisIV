"""Public JPL ephemeris access for the cislunar simulator.

The DE440s kernel is not redistributed by this repository.  It is downloaded
from JPL with ``scripts/fetch_public_data.py --id D029`` and checked against the
versioned SHA-256 record before use.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import numpy as np


UNIX_EPOCH_JD = 2440587.5
# TAI-UTC is 37 s for the 2026 Artemis II interval; TT-TAI is 32.184 s.
# The periodic TDB-TT term is below 2 ms and immaterial at the frozen gates.
TT_MINUS_UTC_S_2026 = 69.184


def sha256_file(path: Path | str) -> str:
    """Return the lowercase SHA-256 digest of *path*."""

    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def utc_to_julian_tdb(epoch: datetime) -> float:
    """Convert a 2026 UTC epoch to the DE440 TDB Julian-date argument.

    The fixed leap-second offset is deliberately scoped to the frozen mission
    interval.  A future mission epoch must provide a maintained time-scale
    conversion rather than silently reusing this function.
    """

    if epoch.tzinfo is None:
        raise ValueError("Ephemeris epochs must be timezone-aware UTC datetimes")
    utc = epoch.astimezone(timezone.utc)
    if utc.year != 2026:
        raise ValueError("The fixed UTC-to-TT conversion is valid only for 2026")
    return (
        utc.timestamp() / 86400.0
        + UNIX_EPOCH_JD
        + TT_MINUS_UTC_S_2026 / 86400.0
    )


@dataclass(frozen=True)
class ThirdBodyPositions:
    """Earth-centered inertial positions in J2000/ICRF axes, in kilometres."""

    moon_km: np.ndarray
    sun_km: np.ndarray


class JplEphemeris:
    """Small DE440s adapter exposing Earth-relative Moon and Sun positions."""

    def __init__(
        self,
        kernel_path: Path | str,
        expected_sha256: str | None = None,
    ) -> None:
        self.kernel_path = Path(kernel_path)
        if expected_sha256 is not None:
            actual = sha256_file(self.kernel_path)
            if actual != expected_sha256.lower():
                raise ValueError(
                    f"DE440s checksum mismatch: expected {expected_sha256}, got {actual}"
                )
        try:
            from jplephem.spk import SPK
        except ImportError as exc:  # pragma: no cover - dependency failure path
            raise RuntimeError(
                "jplephem is required; install the locked project environment"
            ) from exc
        self._kernel = SPK.open(str(self.kernel_path))

    def close(self) -> None:
        self._kernel.close()

    def __enter__(self) -> "JplEphemeris":
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()

    def positions(self, epoch: datetime) -> ThirdBodyPositions:
        """Return geocentric Moon and Sun vectors at *epoch*."""

        jd = utc_to_julian_tdb(epoch)
        earth_barycenter = self._kernel[0, 3].compute(jd)
        earth = earth_barycenter + self._kernel[3, 399].compute(jd)
        moon = earth_barycenter + self._kernel[3, 301].compute(jd)
        sun = self._kernel[0, 10].compute(jd)
        return ThirdBodyPositions(
            moon_km=np.asarray(moon - earth, dtype=float),
            sun_km=np.asarray(sun - earth, dtype=float),
        )
