#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gate 3 diagnostic: Earth-only 6-hour propagation from V01 initial state.

Runs Python (DOP853) and GMAT R2026a (RungeKutta89) with IDENTICAL force
model: Earth point mass + J2 only, Moon and Sun disabled.

If endpoint agreement < 0.010 km -> H1 or H2 is confirmed (third-body
force-model frame/ephemeris mismatch is the root cause of Gate 3 failure).

If endpoint disagreement persists in Earth-only mode -> the issue is in
time conversion, initial-state frame, or integrator implementation.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import io
import numpy as np
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from openqfuel.dynamics import ForceModelSettings, propagate  # noqa: E402
from openqfuel.ephemeris import sha256_file  # noqa: E402
from openqfuel.oem import parse_oem, parse_utc  # noqa: E402
from openqfuel.validation import ValidationWindow  # noqa: E402

UTC = timezone.utc

# ── paths ─────────────────────────────────────────────────────────────────────
OEM_PATH = (
    ROOT
    / "data/raw/artemis2/oem/asc"
    / "Artemis_II_OEM_2026_04_10_Post-ICPS-Sep-to-EI.asc"
)
KERNEL_PATH = ROOT / "data/raw/ephemeris/de440s.bsp"
KERNEL_SHA256 = "c1c7feeab882263fc493a9d5a5b2ddd71b54826cdf65d8d17a76126b260a49f2"
GMAT_CONSOLE = Path(
    r"C:\Users\HP OMEN\openqfuel_handoff_staging\gmat-win-R2026a\bin\GmatConsole.exe"
)
GMAT_ROOT = GMAT_CONSOLE.parent.parent
DIAG_SCRIPT = ROOT / "scripts/gmat/gate3_earth_only_diagnostic.script"
DIAG_OUTPUT = GMAT_ROOT / "output/gate3_earth_only_endpoints.txt"

# ── V01 window ─────────────────────────────────────────────────────────────────
V01 = ValidationWindow(
    window_id="V01",
    phase="outbound_mid",
    start=parse_utc("2026-04-04T11:00:00Z"),
    stop=parse_utc("2026-04-04T17:00:00Z"),
)
DURATION_S = V01.duration_s  # 21600.0


# ── helpers ────────────────────────────────────────────────────────────────────
def _gmat_epoch(dt: datetime) -> str:
    u = dt.astimezone(UTC)
    months = [
        "Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
    ]
    return (
        f"{u.day:02d} {months[u.month - 1]} {u.year} "
        f"{u.hour:02d}:{u.minute:02d}:{u.second:02d}.{u.microsecond // 1000:03d}"
    )


def build_earth_only_gmat_script(
    x: float, y: float, z: float,
    vx: float, vy: float, vz: float,
    duration_s: float,
) -> str:
    """GMAT script: Earth point-mass + J2 ONLY. No Luna or Sun."""
    lines = [
        "% Gate 3 diagnostic: Earth-only propagation (no Moon, no Sun)",
        "% Tool: NASA GMAT R2026a",
        "% Purpose: isolate H1/H2 (third-body) vs time/frame/integrator",
        "",
        "SolarSystem.EphemerisSource = 'SPICE';",
        "SolarSystem.SPKFilename = '../data/planetary_ephem/spk/de440s.bsp';",
        "",
        "Create Spacecraft V01;",
        "V01.DateFormat = UTCGregorian;",
        f"V01.Epoch = '{_gmat_epoch(V01.start)}';",
        "V01.CoordinateSystem = EarthMJ2000Eq;",
        "V01.DisplayStateType = Cartesian;",
        f"V01.X  = {x:.15f};",
        f"V01.Y  = {y:.15f};",
        f"V01.Z  = {z:.15f};",
        f"V01.VX = {vx:.15f};",
        f"V01.VY = {vy:.15f};",
        f"V01.VZ = {vz:.15f};",
        "",
        "Create ForceModel EarthOnlyFM;",
        "EarthOnlyFM.CentralBody = Earth;",
        "EarthOnlyFM.PrimaryBodies = {Earth};",
        "% PointMasses intentionally empty - Luna and Sun DISABLED",
        "EarthOnlyFM.PointMasses = {};",
        "EarthOnlyFM.Drag = None;",
        "EarthOnlyFM.SRP = Off;",
        "EarthOnlyFM.RelativisticCorrection = Off;",
        "EarthOnlyFM.ErrorControl = RSSStep;",
        "EarthOnlyFM.GravityField.Earth.Degree = 2;",
        "EarthOnlyFM.GravityField.Earth.Order = 0;",
        "EarthOnlyFM.GravityField.Earth.PotentialFile = 'openqfuel_earth_j2.cof';",
        "EarthOnlyFM.GravityField.Earth.TideModel = 'None';",
        "",
        "Create Propagator EarthOnlyProp;",
        "EarthOnlyProp.FM = EarthOnlyFM;",
        "EarthOnlyProp.Type = RungeKutta89;",
        "EarthOnlyProp.InitialStepSize = 60;",
        "EarthOnlyProp.Accuracy = 1e-13;",
        "EarthOnlyProp.MinStep = 0.001;",
        "EarthOnlyProp.MaxStep = 150;",
        "EarthOnlyProp.MaxStepAttempts = 50;",
        "EarthOnlyProp.StopIfAccuracyIsViolated = true;",
        "",
        "Create ReportFile DiagReport;",
        "DiagReport.Filename = 'gate3_earth_only_endpoints.txt';",
        "DiagReport.Precision = 16;",
        "DiagReport.WriteHeaders = false;",
        "",
        "BeginMissionSequence;",
        f"Propagate EarthOnlyProp(V01) {{V01.ElapsedSecs = {duration_s:.1f}}};",
        "Report DiagReport V01.ElapsedSecs "
        "V01.EarthMJ2000Eq.X V01.EarthMJ2000Eq.Y V01.EarthMJ2000Eq.Z "
        "V01.EarthMJ2000Eq.VX V01.EarthMJ2000Eq.VY V01.EarthMJ2000Eq.VZ;",
    ]
    return "\n".join(lines) + "\n"


def parse_endpoint_report(path: Path) -> np.ndarray | None:
    number_re = re.compile(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][-+]?\d+)?")
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        values = [float(v) for v in number_re.findall(line)]
        if len(values) == 7:  # elapsed_secs + x y z vx vy vz
            return np.asarray(values[1:], dtype=float)
    return None


def run_python_earth_only(ic: np.ndarray, start: datetime) -> np.ndarray:
    """DOP853 with Earth point-mass + J2 only."""
    settings = ForceModelSettings(
        fidelity="F2",
        moon_gravity=False,  # DISABLED
        sun_gravity=False,   # DISABLED
        earth_j2=True,
        rtol=1e-11,
        atol=1e-13,
        max_step_s=300.0,
    )
    result = propagate(
        start_epoch=start,
        initial_state=ic.tolist(),
        duration_s=DURATION_S,
        settings=settings,
        ephemeris=None,
    )
    return result.endpoint


def stage(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if not dst.exists() or sha256_file(dst) != sha256_file(src):
        shutil.copy2(src, dst)
        print(f"  Staged: {dst.name}")
    else:
        print(f"  Already staged: {dst.name}")


# ── main ───────────────────────────────────────────────────────────────────────
def main() -> None:
    sep = "=" * 70
    print(sep)
    print("Gate 3 Diagnostic: Earth-Only 6-Hour Propagation — V01")
    print("Hypothesis test: is the Gate 3 discrepancy caused by third-body")
    print("  forces (H1 frame / H2 competing ephemeris) or something else?")
    print(sep)

    # 1. Load OEM
    print("\n[1] Loading Artemis II OEM ...")
    if not OEM_PATH.exists():
        sys.exit(
            f"  ERROR: OEM not found: {OEM_PATH}\n"
            "  Run: uv run python scripts/fetch_public_data.py --id D001\n"
            "       uv run python scripts/extract_artemis2_oem.py"
        )
    oem = parse_oem(OEM_PATH)
    sv = oem.interpolate(V01.start)
    ic = np.array(list(sv.position_km) + list(sv.velocity_km_s))
    print(f"  V01 start : {V01.start.isoformat()}")
    print(f"  Position  : [{ic[0]:.6f}, {ic[1]:.6f}, {ic[2]:.6f}] km")
    print(f"  Velocity  : [{ic[3]:.9f}, {ic[4]:.9f}, {ic[5]:.9f}] km/s")

    # 2. Python Earth-only
    print("\n[2] Running Python DOP853 Earth-only (J2, no Moon, no Sun) ...")
    py_ep = run_python_earth_only(ic, V01.start)
    print(f"  Endpoint pos: [{py_ep[0]:.6f}, {py_ep[1]:.6f}, {py_ep[2]:.6f}] km")
    print(f"  Endpoint vel: [{py_ep[3]:.9f}, {py_ep[4]:.9f}, {py_ep[5]:.9f}] km/s")

    # 3. Generate GMAT script
    print("\n[3] Generating GMAT Earth-only script ...")
    DIAG_SCRIPT.parent.mkdir(parents=True, exist_ok=True)
    DIAG_SCRIPT.write_text(
        build_earth_only_gmat_script(*ic, DURATION_S),
        encoding="utf-8", newline="\n",
    )
    print(f"  Written: {DIAG_SCRIPT}")

    # 4. Stage GMAT dependencies
    print("\n[4] Staging GMAT dependencies ...")
    if not GMAT_CONSOLE.exists():
        sys.exit(f"  ERROR: GMAT console not found: {GMAT_CONSOLE}")
    if not KERNEL_PATH.exists():
        sys.exit(f"  ERROR: DE440s kernel not found: {KERNEL_PATH}")
    stage(KERNEL_PATH, GMAT_ROOT / "data/planetary_ephem/spk/de440s.bsp")
    stage(ROOT / "configs/gmat_earth_j2.cof",
          GMAT_ROOT / "data/gravity/Earth/openqfuel_earth_j2.cof")

    # 5. Run GMAT
    print("\n[5] Running GMAT R2026a Earth-only propagation ...")
    DIAG_OUTPUT.unlink(missing_ok=True)
    proc = subprocess.run(
        [str(GMAT_CONSOLE), "--run", str(DIAG_SCRIPT)],
        cwd=str(GMAT_CONSOLE.parent),
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    if proc.returncode != 0:
        sys.exit(
            f"  GMAT exited with code {proc.returncode}\n"
            + (proc.stderr or proc.stdout)[:600]
        )
    if not DIAG_OUTPUT.exists():
        sys.exit(
            f"  ERROR: GMAT output not found: {DIAG_OUTPUT}\n"
            + proc.stdout[:600]
        )
    gmat_ep = parse_endpoint_report(DIAG_OUTPUT)
    if gmat_ep is None:
        sys.exit(
            "  ERROR: Could not parse GMAT endpoint.\n"
            + DIAG_OUTPUT.read_text()[:400]
        )
    print(f"  Endpoint pos: [{gmat_ep[0]:.6f}, {gmat_ep[1]:.6f}, {gmat_ep[2]:.6f}] km")
    print(f"  Endpoint vel: [{gmat_ep[3]:.9f}, {gmat_ep[4]:.9f}, {gmat_ep[5]:.9f}] km/s")

    # 6. Differences
    pos_diff_km = float(np.linalg.norm(py_ep[:3] - gmat_ep[:3]))
    vel_diff_ms = 1000.0 * float(np.linalg.norm(py_ep[3:6] - gmat_ep[3:6]))
    dpos = py_ep[:3] - gmat_ep[:3]
    dvel = (py_ep[3:6] - gmat_ep[3:6]) * 1000.0

    print(f"\n{sep}")
    print("DIAGNOSTIC RESULT")
    print(sep)
    print(f"\n  Position difference (Earth-only): {pos_diff_km:.9f} km")
    print(f"  Velocity difference (Earth-only): {vel_diff_ms:.9f} m/s")
    print("  Component differences (Python minus GMAT):")
    print(f"    dX  = {dpos[0]:+.9f} km")
    print(f"    dY  = {dpos[1]:+.9f} km")
    print(f"    dZ  = {dpos[2]:+.9f} km")
    print(f"    dVX = {dvel[0]:+.9f} m/s")
    print(f"    dVY = {dvel[1]:+.9f} m/s")
    print(f"    dVZ = {dvel[2]:+.9f} m/s")

    GATE3_V01 = 11.276084294437  # km — from Gate 3 full-model comparison
    third_body_frac = (GATE3_V01 - pos_diff_km) / GATE3_V01 * 100.0

    print(f"\n  Gate 3 full-model error (V01): {GATE3_V01:.6f} km")
    print(f"  Earth-only error       (V01): {pos_diff_km:.6f} km")
    print(f"  Third-body contribution:  ~{GATE3_V01 - pos_diff_km:.3f} km "
          f"({third_body_frac:.1f}% of Gate 3 error)")

    print()
    THRESHOLD = 0.010
    if pos_diff_km < THRESHOLD:
        print(f"  VERDICT  Earth-only agreement < {THRESHOLD} km ({pos_diff_km*1000:.0f} m)")
        print()
        print("  H1 / H2 CONFIRMED as the primary root cause.")
        print("  The 11.3 km Gate 3 discrepancy at V01 is caused by the")
        print("  THIRD-BODY FORCE MODEL — either:")
        print("    H1: GMAT transforms Moon/Sun positions from ICRF to FK5/")
        print("        EarthMJ2000Eq each step; Python uses ICRF directly.")
        print("    H2: GMAT loads a competing default SPK (de432s.bsp) that")
        print("        provides different Moon/Sun positions than DE440s.")
        print()
        print("  Recommended next diagnostic: re-run Gate 3 full model with")
        print("  Moon-only (Sun disabled) then Sun-only (Moon disabled) to")
        print("  identify which body dominates the error.")
    elif pos_diff_km < 1.0:
        print(f"  VERDICT  Earth-only moderate disagreement: {pos_diff_km:.6f} km")
        print()
        print("  The tools disagree even without Moon/Sun. Check:")
        print("    - Did GMAT load openqfuel_earth_j2.cof? (see GMAT log)")
        print("    - What is GMAT's Earth.Mu in SPICE mode?")
        print("    - Is there a frame rotation in the initial state?")
    else:
        print(f"  VERDICT  Earth-only large disagreement: {pos_diff_km:.6f} km")
        print()
        print("  Something fundamental differs. Check:")
        print("    - GMAT COF file fallback to default higher-degree gravity")
        print("    - GMAT Earth.Mu vs 398600.435507 km^3/s^2")
        print("    - GMAT integration accuracy settings actually applied")

    print(f"\n{sep}\n")


if __name__ == "__main__":
    main()
