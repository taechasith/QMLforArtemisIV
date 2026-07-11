#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gate 5: Generate development-split scenario payloads.

Reads configs/phase1_benchmark.yaml and data/processed/simulator/scenario_manifest.csv,
propagates each development-split candidate plan through the frozen F0/F1/F2 simulator,
and writes labelled JSONL records conforming to scenario_schema.json.

Design
------
For each manifest group, one nominal (no-burn) propagation establishes the
reference EI endpoint.  Each candidate burn is then evaluated by propagating
the perturbed + corrected trajectory for the same duration.  The outcome
``terminal_position_error_km`` measures how far the corrected trajectory
deviates from that nominal EI endpoint; ``independently_propagated_feasible``
is True when that deviation is < 500 km and speed deviation < 200 m/s.

AUTHORISED after Gate 4 acceptance.  Final-test splits are blocked by
``assert_no_final_payloads`` and ``assert_split_access``.

Usage
-----
    uv run python scripts/generate_scenarios.py [--fidelity F0|F1|F2]
                                                [--split development]
                                                [--group G01]
                                                [--resume]
                                                [--check]
                                                [--dry-run]
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import logging
import math
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from openqfuel.dynamics import (
    EARTH_EQUATORIAL_RADIUS_KM,
    EARTH_MU_KM3_S2,
    ForceModelSettings,
    propagate,
)
from openqfuel.ephemeris import JplEphemeris
from openqfuel.gate4 import (
    assert_no_final_payloads,
    assert_split_access,
    derive_seed,
    read_csv,
    read_yaml,
)
from openqfuel.oem import parse_oem, parse_utc

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
CONFIG_PATH   = ROOT / "configs/phase1_benchmark.yaml"
MANIFEST_PATH = ROOT / "data/processed/simulator/scenario_manifest.csv"
OEM_PATH = (
    ROOT / "data/raw/artemis2/oem/asc"
    / "Artemis_II_OEM_2026_04_10_Post-ICPS-Sep-to-EI.asc"
)
EPHEMERIS_PATH = ROOT / "data/planetary_ephem/spk/de440s.bsp"
OUTPUT_DIR     = ROOT / "data/processed/simulator/scenarios"
LOCKED_ROOT    = ROOT / "data/locked/phase1"

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_EI_RADIUS_KM = 6563.0          # nominal EI geocentric radius (km)
TLI_EPOCH_UTC = "2026-04-04T05:00:00Z"   # approximate TLI time
EI_EPOCH_UTC  = "2026-04-09T22:00:00Z"   # nominal EI time

# Fidelity -> ForceModelSettings
_FIDELITY_SETTINGS: dict[str, ForceModelSettings] = {
    "F0": ForceModelSettings("F0", False, False, False, 1e-10, 1e-12, 600.0),
    "F1": ForceModelSettings("F1", True,  True,  False, 1e-10, 1e-12, 600.0),
    "F2": ForceModelSettings("F2", True,  True,  True,  1e-11, 1e-13, 300.0),
}

# Thrust class -> (thrust_N, isp_s)
_THRUST_CLASSES: dict[str, tuple[float, float]] = {
    "RCS_LOW":  (445.0,  308.0),
    "OMS_MED":  (2224.0, 316.0),
    "OMS_HIGH": (8900.0, 320.0),
}

# Uncertainty family -> 1-sigma parameters
_U_SIGMA: dict[str, dict[str, float]] = {
    "U0": dict(nav_pos_km=0.0,  nav_vel_ms=0.0,  thrust_frac=0.0,  point_deg=0.0,  mass_frac=0.0,  dist=0.0),
    "U1": dict(nav_pos_km=1.0,  nav_vel_ms=0.05, thrust_frac=0.0,  point_deg=0.0,  mass_frac=0.0,  dist=0.0),
    "U2": dict(nav_pos_km=0.0,  nav_vel_ms=0.0,  thrust_frac=0.01, point_deg=0.5,  mass_frac=0.005,dist=0.0),
    "U3": dict(nav_pos_km=1.0,  nav_vel_ms=0.05, thrust_frac=0.01, point_deg=0.5,  mass_frac=0.005,dist=0.0),
    "U4": dict(nav_pos_km=0.5,  nav_vel_ms=0.02, thrust_frac=0.005,point_deg=0.3,  mass_frac=0.003,dist=0.02),
}


# ---------------------------------------------------------------------------
# Helper: deterministic per-scenario RNG
# ---------------------------------------------------------------------------
def _rng(master_seed: int, key: str) -> np.random.Generator:
    seed = derive_seed(master_seed, "scenario_rng", key)
    return np.random.default_rng(seed)


# ---------------------------------------------------------------------------
# Helper: physics-derived features
# ---------------------------------------------------------------------------
def _physics_derived(pos_km: np.ndarray, vel_km_s: np.ndarray) -> dict[str, float]:
    r = float(np.linalg.norm(pos_km))
    v = float(np.linalg.norm(vel_km_s))
    h = float(np.linalg.norm(np.cross(pos_km, vel_km_s)))
    eps = 0.5 * v * v - EARTH_MU_KM3_S2 / r
    vr  = float(np.dot(pos_km / r, vel_km_s))
    return dict(radius_km=r, speed_km_s=v,
                specific_orbital_energy_km2_s2=eps,
                angular_momentum_km2_s=h,
                radial_velocity_km_s=vr)


# ---------------------------------------------------------------------------
# Helper: candidate delta-v sampling
# ---------------------------------------------------------------------------
def _candidate_burns(
    rng: np.random.Generator,
    n: int,
    fidelity: str,
) -> list[np.ndarray]:
    """Return n random delta-v vectors (m/s) in random directions."""
    ranges = {"F0": (0.1, 30.0), "F1": (0.5, 50.0), "F2": (1.0, 80.0)}
    lo, hi = ranges.get(fidelity, (0.5, 50.0))
    mags = rng.uniform(lo, hi, size=n)
    dirs = rng.standard_normal(size=(n, 3))
    dirs /= np.maximum(np.linalg.norm(dirs, axis=1, keepdims=True), 1e-12)
    return [mags[i] * dirs[i] for i in range(n)]


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------
@dataclass
class ScenarioOutcomes:
    robust_total_correction_delta_v_m_s: float
    independently_propagated_feasible: bool
    correction_delta_v_m_s: float
    burn_vector_x_m_s: float
    burn_vector_y_m_s: float
    burn_vector_z_m_s: float
    terminal_position_error_km: float
    terminal_velocity_error_m_s: float
    terminal_margin: float
    propellant_used_kg: float
    nonconverged: bool
    violation_code: str | None


# ---------------------------------------------------------------------------
# Core evaluation
# ---------------------------------------------------------------------------
def _evaluate_candidate(
    # state
    pos0_km: np.ndarray,
    vel0_km_s: np.ndarray,
    mass0_kg: float,
    usable_prop_kg: float,
    # nav uncertainty
    nav_pos_km: np.ndarray,
    nav_vel_km_s: np.ndarray,
    # burn
    dv_m_s: np.ndarray,          # candidate delta-v in m/s (3-vector)
    thrust_scale: float,
    pointing_deg: float,
    mass_error_frac: float,
    disturbance_scale: float,
    thrust_class: str,
    # propagation
    epoch: datetime,
    duration_s: float,
    settings: ForceModelSettings,
    ephemeris,
    # reference
    nominal_ei_pos_km: np.ndarray,
    nominal_ei_vel_km_s: np.ndarray,
    scenario_id: str,
) -> ScenarioOutcomes:
    """Evaluate one candidate burn against the nominal EI endpoint."""
    thrust_n, isp_s = _THRUST_CLASSES.get(thrust_class, (445.0, 308.0))

    # Scale and rotate the burn vector
    dv_executed = (dv_m_s / 1000.0) * max(0.0, thrust_scale)  # km/s
    if pointing_deg != 0.0 and np.linalg.norm(dv_executed) > 1e-12:
        angle = math.radians(pointing_deg)
        unit  = dv_executed / np.linalg.norm(dv_executed)
        perp  = np.array([-unit[1], unit[0], 0.0])
        if np.linalg.norm(perp) < 1e-12:
            perp = np.array([0.0, -unit[2], unit[1]])
        perp /= np.linalg.norm(perp)
        dv_executed = dv_executed * math.cos(angle) + np.cross(perp, dv_executed) * math.sin(angle)

    dv_mag_m_s = float(np.linalg.norm(dv_executed)) * 1000.0

    propellant_kg = 0.0
    nonconverged  = False
    violation     = None

    try:
        if dv_mag_m_s > 0.01:
            mass_eff = mass0_kg * (1.0 + mass_error_frac)
            propellant_kg = mass_eff * (1.0 - math.exp(-dv_mag_m_s / (isp_s * 9.80665)))
            pos_p = pos0_km + nav_pos_km
            vel_p = vel0_km_s + nav_vel_km_s + dv_executed
            ic    = list(pos_p) + list(vel_p) + [max(mass_eff - propellant_kg, 1.0)]
        else:
            ic = list(pos0_km + nav_pos_km) + list(vel0_km_s + nav_vel_km_s) + [mass0_kg]

        result  = propagate(epoch, ic, duration_s, settings, ephemeris)
        pos_end = np.array(result.endpoint[:3])
        vel_end = np.array(result.endpoint[3:6])

        terminal_pos_err = float(np.linalg.norm(pos_end - nominal_ei_pos_km))
        terminal_spd_m_s = float(np.linalg.norm(vel_end)) * 1000.0
        nominal_spd_m_s  = float(np.linalg.norm(nominal_ei_vel_km_s)) * 1000.0
        terminal_vel_err = abs(terminal_spd_m_s - nominal_spd_m_s)
        terminal_margin  = _EI_RADIUS_KM - float(np.linalg.norm(pos_end))

        feasible = (
            terminal_pos_err < 500.0
            and terminal_vel_err < 200.0
            and propellant_kg <= usable_prop_kg
        )

    except Exception as exc:
        log.debug("Propagation failed for %s: %s", scenario_id, exc)
        nonconverged     = True
        violation        = "propagation_failed"
        feasible         = False
        dv_mag_m_s       = 0.0
        propellant_kg    = 0.0
        terminal_pos_err = 9999.0
        terminal_vel_err = 9999.0
        terminal_margin  = -9999.0
        dv_executed      = np.zeros(3)

    robust_dv = dv_mag_m_s * (1.0 + disturbance_scale)

    return ScenarioOutcomes(
        robust_total_correction_delta_v_m_s=round(robust_dv, 6),
        independently_propagated_feasible=feasible,
        correction_delta_v_m_s=round(dv_mag_m_s, 6),
        burn_vector_x_m_s=round(float(dv_executed[0]) * 1000.0, 6),
        burn_vector_y_m_s=round(float(dv_executed[1]) * 1000.0, 6),
        burn_vector_z_m_s=round(float(dv_executed[2]) * 1000.0, 6),
        terminal_position_error_km=round(terminal_pos_err, 6),
        terminal_velocity_error_m_s=round(terminal_vel_err, 6),
        terminal_margin=round(terminal_margin, 6),
        propellant_used_kg=round(propellant_kg, 6),
        nonconverged=nonconverged,
        violation_code=violation,
    )


# ---------------------------------------------------------------------------
# Group generator
# ---------------------------------------------------------------------------
def generate_group_scenarios(
    group_row: Mapping[str, str],
    config: Mapping[str, Any],
    oem,
    ephemeris,
) -> list[dict[str, Any]]:
    """Generate all scenario records for one manifest group row."""
    assert_split_access(group_row["split"], "generation")

    fidelity     = group_row["fidelity"]
    group_id     = group_row["group_id"]
    split        = group_row["split"]
    mission_phase = group_row["mission_phase"]
    epoch_utc    = parse_utc(group_row["mission_epoch_utc"])
    unc_family   = group_row["uncertainty_family"]
    case_count   = int(group_row["case_count"])
    n_per_set    = int(config["scenario_design"]["decision_sets"]["candidates_per_set"])
    master_seed  = int(config["scenario_design"]["master_seed"])
    u_sigma      = _U_SIGMA.get(unc_family, _U_SIGMA["U0"])
    settings     = _FIDELITY_SETTINGS[fidelity]

    # Base trajectory state
    sv   = oem.interpolate(epoch_utc)
    pos0 = np.array(sv.position_km)
    vel0 = np.array(sv.velocity_km_s)

    # Time markers
    tli_epoch = parse_utc(TLI_EPOCH_UTC)
    ei_epoch  = parse_utc(EI_EPOCH_UTC)
    elapsed_h = (epoch_utc - tli_epoch).total_seconds() / 3600.0
    tte_h     = (ei_epoch  - epoch_utc).total_seconds() / 3600.0
    dur_s     = tte_h * 3600.0

    # Nominal (no-burn) propagation to EI for this group
    try:
        nom = propagate(epoch_utc, list(pos0) + list(vel0), dur_s, settings, ephemeris)
        nom_ei_pos = np.array(nom.endpoint[:3])
        nom_ei_vel = np.array(nom.endpoint[3:6])
    except Exception as exc:
        log.warning("Nominal propagation failed for %s: %s", group_id, exc)
        nom_ei_pos = np.array([_EI_RADIUS_KM, 0.0, 0.0])
        nom_ei_vel = np.array([0.0, 7.8, 0.0])

    phys             = _physics_derived(pos0, vel0)
    initial_mass_kg  = 26520.0
    usable_prop_kg   = 1200.0
    n_sets           = case_count // n_per_set
    records: list[dict[str, Any]] = []

    for set_idx in range(1, n_sets + 1):
        set_id  = f"{fidelity}-{group_id}-D{set_idx:06d}"
        set_rng = _rng(master_seed, set_id)

        nav_pos = set_rng.normal(0.0, u_sigma["nav_pos_km"], 3)  # km
        nav_vel = set_rng.normal(0.0, u_sigma["nav_vel_ms"],  3) / 1000.0  # km/s

        candidate_dvs = _candidate_burns(set_rng, n_per_set, fidelity)  # m/s

        for cand_idx, dv_m_s in enumerate(candidate_dvs, start=1):
            rep_idx     = (set_idx - 1) * n_per_set + cand_idx
            scenario_id = f"{fidelity}-{group_id}-{rep_idx:06d}"
            crng        = _rng(master_seed, scenario_id)

            thrust_scale = float(1.0 + crng.normal(0.0, u_sigma["thrust_frac"]))
            pointing_deg = float(crng.normal(0.0, u_sigma["point_deg"]))
            mass_frac    = float(crng.normal(0.0, u_sigma["mass_frac"]))
            disturbance  = float(abs(crng.normal(0.0, u_sigma["dist"])))
            burn_start_s = float(crng.uniform(0, 3600))
            dv_mag       = float(np.linalg.norm(dv_m_s))
            burn_dur_s   = max(10.0, dv_mag * initial_mass_kg / 445.0)
            comm_hold    = float(crng.uniform(0, 30))
            burn_delay   = float(crng.uniform(0, 15))

            lf_cost      = dv_mag
            lf_term_err  = max(0.0, abs(phys["radius_km"] - _EI_RADIUS_KM) - 50.0)
            tclass       = "RCS_LOW" if dv_mag < 5.0 else ("OMS_MED" if dv_mag < 25.0 else "OMS_HIGH")
            nav_mode     = "autonomous" if unc_family in {"U1", "U3"} else "nominal"

            outcomes = _evaluate_candidate(
                pos0_km=pos0, vel0_km_s=vel0,
                mass0_kg=initial_mass_kg, usable_prop_kg=usable_prop_kg,
                nav_pos_km=nav_pos, nav_vel_km_s=nav_vel,
                dv_m_s=dv_m_s,
                thrust_scale=thrust_scale, pointing_deg=pointing_deg,
                mass_error_frac=mass_frac, disturbance_scale=disturbance,
                thrust_class=tclass,
                epoch=epoch_utc, duration_s=dur_s,
                settings=settings, ephemeris=ephemeris,
                nominal_ei_pos_km=nom_ei_pos, nominal_ei_vel_km_s=nom_ei_vel,
                scenario_id=scenario_id,
            )

            record: dict[str, Any] = {
                "scenario_id":    scenario_id,
                "decision_set_id": set_id,
                "candidate_index": cand_idx,
                "group_id":        group_id,
                "fidelity":        fidelity,
                "split":           split,
                "inputs": {
                    "elapsed_since_tli_h":               round(elapsed_h, 6),
                    "time_to_entry_interface_h":          round(tte_h, 6),
                    "initial_x_km":                      round(float(pos0[0]), 9),
                    "initial_y_km":                      round(float(pos0[1]), 9),
                    "initial_z_km":                      round(float(pos0[2]), 9),
                    "initial_vx_km_s":                   round(float(vel0[0]), 12),
                    "initial_vy_km_s":                   round(float(vel0[1]), 12),
                    "initial_vz_km_s":                   round(float(vel0[2]), 12),
                    "initial_mass_kg":                   initial_mass_kg,
                    "usable_propellant_remaining_kg":     usable_prop_kg,
                    "navigation_dx_km":                  round(float(nav_pos[0]), 9),
                    "navigation_dy_km":                  round(float(nav_pos[1]), 9),
                    "navigation_dz_km":                  round(float(nav_pos[2]), 9),
                    "navigation_dvx_m_s":                round(float(nav_vel[0]) * 1000.0, 9),
                    "navigation_dvy_m_s":                round(float(nav_vel[1]) * 1000.0, 9),
                    "navigation_dvz_m_s":                round(float(nav_vel[2]) * 1000.0, 9),
                    "candidate_burn_start_offset_s":     round(burn_start_s, 3),
                    "candidate_burn_duration_s":         round(burn_dur_s, 3),
                    "candidate_delta_v_x_m_s":           round(float(dv_m_s[0]), 9),
                    "candidate_delta_v_y_m_s":           round(float(dv_m_s[1]), 9),
                    "candidate_delta_v_z_m_s":           round(float(dv_m_s[2]), 9),
                    "thrust_scale":                      round(thrust_scale, 9),
                    "pointing_bias_deg":                 round(pointing_deg, 6),
                    "mass_error_fraction":               round(mass_frac, 9),
                    "communication_hold_min":            round(comm_hold, 3),
                    "burn_delay_min":                    round(burn_delay, 3),
                    "disturbance_scale":                 round(disturbance, 9),
                    "low_fidelity_cost_m_s":             round(lf_cost, 6),
                    "low_fidelity_terminal_error_km":    round(lf_term_err, 6),
                    "radius_km":                         round(phys["radius_km"], 6),
                    "speed_km_s":                        round(phys["speed_km_s"], 9),
                    "specific_orbital_energy_km2_s2":    round(phys["specific_orbital_energy_km2_s2"], 6),
                    "angular_momentum_km2_s":            round(phys["angular_momentum_km2_s"], 6),
                    "radial_velocity_km_s":              round(phys["radial_velocity_km_s"], 9),
                    "mission_phase":                     mission_phase,
                    "uncertainty_family":                unc_family,
                    "navigation_mode":                   nav_mode,
                    "thrust_class":                      tclass,
                    "fidelity":                          fidelity,
                },
                "outcomes": asdict(outcomes),
            }
            records.append(record)

    return records


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------
def _out_path(fidelity: str, split: str, group_id: str) -> Path:
    return OUTPUT_DIR / fidelity / split / f"{group_id}.jsonl"


def _write_jsonl(records: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        for r in records:
            fh.write(json.dumps(r, separators=(",", ":")) + "\n")


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--fidelity", choices=["F0", "F1", "F2"])
    p.add_argument("--split",    choices=["development", "uncertainty_calibration"])
    p.add_argument("--group",    help="e.g. G01")
    p.add_argument("--resume",   action="store_true",
                   help="skip already-completed output files")
    p.add_argument("--check",    action="store_true",
                   help="verify existing outputs without regenerating")
    p.add_argument("--dry-run",  action="store_true")
    return p.parse_args()


def main() -> int:
    args = _parse_args()
    assert_no_final_payloads(LOCKED_ROOT)

    config = read_yaml(CONFIG_PATH)
    if config["status"] != "gate_4_accepted_development_generation_authorized":
        log.error("Gate 4 acceptance required. Current status: %s", config["status"])
        return 1

    manifest = read_csv(MANIFEST_PATH)
    allowed  = {"development", "uncertainty_calibration"}
    rows = [
        r for r in manifest
        if r["split"] in allowed
        and (args.fidelity is None or r["fidelity"] == args.fidelity)
        and (args.split    is None or r["split"]    == args.split)
        and (args.group    is None or r["group_id"] == args.group)
    ]
    if not rows:
        log.error("No matching manifest rows.")
        return 1

    total = sum(int(r["case_count"]) for r in rows)
    log.info("Planning %d scenario cases across %d manifest rows", total, len(rows))

    if args.dry_run:
        for r in rows:
            log.info("  would generate: %s %s %s (%s cases)",
                     r["fidelity"], r["split"], r["group_id"], r["case_count"])
        return 0

    # Load OEM and ephemeris
    log.info("Loading Artemis II OEM ...")
    oem = parse_oem(OEM_PATH)

    needs_eph = any(r["fidelity"] in {"F1", "F2"} for r in rows)
    ephemeris = JplEphemeris(EPHEMERIS_PATH) if needs_eph else None
    if needs_eph:
        log.info("Loaded DE440s ephemeris.")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ledger = OUTPUT_DIR / "generation_ledger.csv"
    completed, failed = 0, 0

    for row in rows:
        fid, spl, gid = row["fidelity"], row["split"], row["group_id"]
        n = int(row["case_count"])
        out = _out_path(fid, spl, gid)

        if args.check:
            if out.exists():
                actual = sum(1 for _ in open(out, encoding="utf-8"))
                log.info("CHECK %s %s %s: %s", fid, spl, gid,
                         "OK" if actual == n else f"WRONG_COUNT:{actual}/{n}")
            else:
                log.warning("CHECK %s %s %s: MISSING", fid, spl, gid)
            continue

        if args.resume and out.exists():
            log.info("Skipping (exists): %s/%s/%s", fid, spl, gid)
            completed += n
            continue

        log.info("Generating %s %s %s (%d cases) ...", fid, spl, gid, n)
        t0 = time.monotonic()
        try:
            records = generate_group_scenarios(row, config, oem, ephemeris)
            _write_jsonl(records, out)
            elapsed = time.monotonic() - t0
            cksum   = _sha256_file(out)
            log.info("  Done: %d records in %.1fs | %s...", len(records), elapsed, cksum[:16])
            completed += len(records)

            with open(ledger, "a", newline="", encoding="utf-8") as lf:
                w = csv.writer(lf)
                w.writerow([fid, spl, gid, len(records),
                            round(elapsed, 2), cksum,
                            datetime.now(timezone.utc).isoformat()])
        except Exception as exc:
            log.error("FAILED %s %s %s: %s", fid, spl, gid, exc)
            failed += 1

    if args.check:
        return 0
    log.info("Done: %d cases written, %d groups failed.", completed, failed)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
