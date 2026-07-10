#!/usr/bin/env python3
"""Evaluate an Earth two-body propagation baseline on frozen Artemis II arcs."""

from __future__ import annotations

import argparse
import csv
import math
import sys
from pathlib import Path

import numpy as np
from scipy.integrate import solve_ivp


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from openqfuel.oem import parse_oem, parse_utc  # noqa: E402


DEFAULT_OEM = (
    ROOT
    / "data/raw/artemis2/oem/asc/Artemis_II_OEM_2026_04_10_Post-ICPS-Sep-to-EI.asc"
)
DEFAULT_WINDOWS = ROOT / "data/processed/artemis2/validation_windows.csv"
DEFAULT_OUTPUT = ROOT / "data/processed/artemis2/two_body_baseline.csv"
EARTH_MU_KM3_S2 = 398600.435507


def dynamics(_time_s: float, state: np.ndarray) -> np.ndarray:
    radius = state[:3]
    distance = np.linalg.norm(radius)
    acceleration = -EARTH_MU_KM3_S2 * radius / distance**3
    return np.concatenate((state[3:], acceleration))


def rms(values: list[float]) -> float:
    return math.sqrt(sum(value * value for value in values) / len(values))


def evaluate(oem_path: Path, windows_path: Path) -> list[dict[str, object]]:
    ephemeris = parse_oem(oem_path)
    with windows_path.open(newline="", encoding="utf-8") as handle:
        windows = list(csv.DictReader(handle))

    rows: list[dict[str, object]] = []
    for window in windows:
        start = parse_utc(window["start_utc"])
        stop = parse_utc(window["stop_utc"])
        reference_states = [
            state for state in ephemeris.states if start <= state.epoch <= stop
        ]
        if not reference_states or reference_states[0].epoch != start:
            initial = ephemeris.interpolate(start)
            reference_states.insert(0, initial)
        if reference_states[-1].epoch != stop:
            reference_states.append(ephemeris.interpolate(stop))

        initial = ephemeris.interpolate(start)
        initial_array = np.array(initial.position_km + initial.velocity_km_s)
        evaluation_s = np.array(
            [(state.epoch - start).total_seconds() for state in reference_states]
        )
        solution = solve_ivp(
            dynamics,
            (0.0, (stop - start).total_seconds()),
            initial_array,
            method="DOP853",
            t_eval=evaluation_s,
            rtol=1e-11,
            atol=1e-12,
        )
        if not solution.success:
            raise RuntimeError(solution.message)

        position_errors: list[float] = []
        velocity_errors: list[float] = []
        for predicted, reference in zip(solution.y.T, reference_states):
            position_errors.append(
                float(np.linalg.norm(predicted[:3] - np.array(reference.position_km)))
            )
            velocity_errors.append(
                1000.0
                * float(
                    np.linalg.norm(predicted[3:] - np.array(reference.velocity_km_s))
                )
            )

        rows.append(
            {
                "window_id": window["window_id"],
                "role": window["role"],
                "phase": window["phase"],
                "samples": len(reference_states),
                "position_rmse_km": f"{rms(position_errors):.9f}",
                "position_endpoint_km": f"{position_errors[-1]:.9f}",
                "velocity_rmse_m_s": f"{rms(velocity_errors):.9f}",
                "velocity_endpoint_m_s": f"{velocity_errors[-1]:.9f}",
                "model": "Earth point mass only",
                "earth_mu_km3_s2": EARTH_MU_KM3_S2,
                "integrator": "scipy DOP853 rtol=1e-11 atol=1e-12",
                "interpretation": "weak analytical benchmark; not a mission simulator",
            }
        )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--oem", type=Path, default=DEFAULT_OEM)
    parser.add_argument("--windows", type=Path, default=DEFAULT_WINDOWS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    rows = evaluate(args.oem, args.windows)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} two-body baseline arc results to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
