#!/usr/bin/env python3
"""Audit Artemis II public ephemeris releases and quantify release revisions."""

from __future__ import annotations

import argparse
import csv
import hashlib
import math
import statistics
import sys
from datetime import timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from openqfuel.oem import OemEphemeris, parse_oem  # noqa: E402


DEFAULT_INPUT = ROOT / "data" / "raw" / "artemis2" / "oem" / "asc"
DEFAULT_OUTPUT = ROOT / "data" / "processed" / "artemis2"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def norm(values: tuple[float, float, float]) -> float:
    return math.sqrt(sum(value * value for value in values))


def difference(
    left: tuple[float, float, float], right: tuple[float, float, float]
) -> tuple[float, float, float]:
    return tuple(a - b for a, b in zip(left, right))


def iso(value) -> str:
    return value.isoformat().replace("+00:00", "Z")


def inventory_row(ephemeris: OemEphemeris) -> dict[str, object]:
    cadence = [
        (right.epoch - left.epoch).total_seconds()
        for left, right in zip(ephemeris.states, ephemeris.states[1:])
    ]
    historical = sum(
        state.epoch <= ephemeris.creation_time for state in ephemeris.states
    )
    return {
        "filename": ephemeris.path.name,
        "format": "CCSDS_OEM_2.0",
        "audit_status": "eligible_after_split",
        "sha256": sha256_file(ephemeris.path),
        "creation_utc": iso(ephemeris.creation_time),
        "start_utc": iso(ephemeris.start_time),
        "stop_utc": iso(ephemeris.stop_time),
        "state_rows": len(ephemeris.states),
        "historical_or_reconstructed_rows": historical,
        "predicted_rows": len(ephemeris.states) - historical,
        "median_cadence_s": f"{statistics.median(cadence):.3f}",
        "minimum_cadence_s": f"{min(cadence):.3f}",
        "maximum_cadence_s": f"{max(cadence):.3f}",
        "object_name": ephemeris.header["OBJECT_NAME"],
        "center_name": ephemeris.header["CENTER_NAME"],
        "reference_frame": ephemeris.header["REF_FRAME"],
        "time_system": ephemeris.header["TIME_SYSTEM"],
        "position_unit": "km",
        "velocity_unit": "km/s",
        "wrapper_prefix_lines": ephemeris.wrapper_prefix_lines,
        "qualification_note": (
            "Epoch classification is an audit convention: states at or before "
            "CREATION_DATE are historical/reconstructed; later states are predicted."
        ),
    }


def propman_inventory_row(path: Path) -> dict[str, object]:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    data_rows = sum(
        1
        for line in lines
        if len(line.split()) == 8 and line.split()[0].replace(".", "", 1).isdigit()
    )
    return {
        "filename": path.name,
        "format": "PROP_MAN_11.0",
        "audit_status": "quarantined_pending_frame_and_column_definition",
        "sha256": sha256_file(path),
        "creation_utc": "",
        "start_utc": "",
        "stop_utc": "",
        "state_rows": data_rows,
        "historical_or_reconstructed_rows": "",
        "predicted_rows": "",
        "median_cadence_s": "1.000",
        "minimum_cadence_s": "",
        "maximum_cadence_s": "",
        "object_name": "",
        "center_name": "",
        "reference_frame": "M50",
        "time_system": "mission-relative epoch not yet qualified",
        "position_unit": "ft",
        "velocity_unit": "ft/s",
        "wrapper_prefix_lines": 0,
        "qualification_note": (
            "Excluded until PROP_MAN epoch, M50 realization, and eighth-column "
            "semantics are supported by an authoritative definition."
        ),
    }


def revision_rows(releases: list[OemEphemeris]) -> list[dict[str, object]]:
    releases = sorted(releases, key=lambda item: item.creation_time)
    rows: list[dict[str, object]] = []
    for old, new in zip(releases, releases[1:]):
        for horizon_h in (0, 6, 24, 48):
            epoch = new.creation_time + timedelta(hours=horizon_h)
            if not (
                old.start_time <= epoch <= old.stop_time
                and new.start_time <= epoch <= new.stop_time
            ):
                continue
            old_state = old.interpolate(epoch)
            new_state = new.interpolate(epoch)
            rows.append(
                {
                    "older_release": old.path.name,
                    "newer_release": new.path.name,
                    "newer_creation_utc": iso(new.creation_time),
                    "horizon_from_newer_creation_h": horizon_h,
                    "evaluation_utc": iso(epoch),
                    "older_solution_role": "prediction",
                    "newer_solution_role": (
                        "historical_or_reconstructed" if horizon_h == 0 else "prediction"
                    ),
                    "position_revision_km": f"{norm(difference(old_state.position_km, new_state.position_km)):.9f}",
                    "velocity_revision_m_s": f"{1000.0 * norm(difference(old_state.velocity_km_s, new_state.velocity_km_s)):.9f}",
                    "interpretation": "solution revision, not measurement error or truth residual",
                }
            )
    return rows


def detected_discontinuity_rows(
    ephemeris: OemEphemeris,
    position_threshold_km: float = 0.05,
    velocity_threshold_m_s: float = 0.05,
) -> list[dict[str, object]]:
    """Flag state transitions using leave-one-out Hermite inconsistency.

    This is intentionally a conservative coast-arc exclusion heuristic.  A flag
    is not interpreted as proof that a burn occurred.
    """

    anomalies: list[dict[str, object]] = []
    for index in range(1, len(ephemeris.states) - 1):
        state = ephemeris.states[index]
        if state.epoch > ephemeris.creation_time:
            continue
        left = ephemeris.states[index - 1]
        right = ephemeris.states[index + 1]
        if max(
            (state.epoch - left.epoch).total_seconds(),
            (right.epoch - state.epoch).total_seconds(),
        ) > 300.0:
            continue
        pair = OemEphemeris(
            ephemeris.path,
            ephemeris.header,
            (left, right),
            ephemeris.wrapper_prefix_lines,
        )
        interpolated = pair.interpolate(state.epoch)
        position_error = norm(
            difference(interpolated.position_km, state.position_km)
        )
        velocity_error = 1000.0 * norm(
            difference(interpolated.velocity_km_s, state.velocity_km_s)
        )
        if (
            position_error > position_threshold_km
            or velocity_error > velocity_threshold_m_s
        ):
            anomalies.append(
                {
                    "epoch": state.epoch,
                    "position_loo_error_km": position_error,
                    "velocity_loo_error_m_s": velocity_error,
                }
            )

    clusters: list[list[dict[str, object]]] = []
    for anomaly in anomalies:
        if (
            not clusters
            or anomaly["epoch"] - clusters[-1][-1]["epoch"] > timedelta(minutes=20)
        ):
            clusters.append([anomaly])
        else:
            clusters[-1].append(anomaly)

    rows: list[dict[str, object]] = []
    for index, cluster in enumerate(clusters, start=1):
        rows.append(
            {
                "discontinuity_id": f"X{index:02d}",
                "first_flagged_utc": iso(cluster[0]["epoch"]),
                "last_flagged_utc": iso(cluster[-1]["epoch"]),
                "flagged_state_count": len(cluster),
                "maximum_position_loo_error_km": f"{max(float(item['position_loo_error_km']) for item in cluster):.9f}",
                "maximum_velocity_loo_error_m_s": f"{max(float(item['velocity_loo_error_m_s']) for item in cluster):.9f}",
                "position_threshold_km": position_threshold_km,
                "velocity_threshold_m_s": velocity_threshold_m_s,
                "coast_exclusion_buffer_min": 30,
                "interpretation": (
                    "State transition or locally high-curvature interval; used only "
                    "to exclude clean coast arcs and not labeled as a maneuver."
                ),
            }
        )
    return rows


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise ValueError(f"No rows available for {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    releases: list[OemEphemeris] = []
    inventory: list[dict[str, object]] = []
    for path in sorted(item for item in args.input.iterdir() if item.is_file()):
        prefix = path.read_text(encoding="utf-8", errors="replace")[:16384]
        if "CCSDS_OEM_VERS" in prefix:
            release = parse_oem(path)
            releases.append(release)
            inventory.append(inventory_row(release))
        elif prefix.lstrip().startswith("PROP_MAN"):
            inventory.append(propman_inventory_row(path))
        else:
            raise ValueError(f"Unrecognized ephemeris product: {path}")

    inventory.sort(key=lambda row: (row["format"] != "CCSDS_OEM_2.0", row["creation_utc"]))
    write_csv(args.output / "oem_inventory.csv", inventory)
    revisions = revision_rows(releases)
    write_csv(args.output / "oem_release_revisions.csv", revisions)
    latest = max(releases, key=lambda item: item.creation_time)
    discontinuities = detected_discontinuity_rows(latest)
    write_csv(args.output / "oem_detected_discontinuities.csv", discontinuities)
    print(f"Audited {len(releases)} CCSDS OEM releases and {len(inventory) - len(releases)} quarantined product.")
    print(f"Wrote {len(revisions)} adjacent-release revision comparisons.")
    print(f"Flagged {len(discontinuities)} conservative coast-exclusion intervals.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
