# Decision and Deviation Log

## Decision Gate 0: Research governance

Date: 2026-07-10  
Status: Accepted  
Decision authority: Human research lead  
Recommendation: Accept

Decision:

The assistant research partner will perform the research operations,
implementation, validation, documentation, and recommendations. The human
research lead will make the final accept, reject, or revise decision at
explicit gates.

Consequence:

Routine technical choices within the accepted protocol do not require repeated
permission. Scope changes, claim changes, post-freeze methodological changes,
and release decisions return to the human research lead.

## Decision Gate 1: Protocol scope

Date opened: 2026-07-10  
Date decided: 2026-07-10  
Status: Accepted  
Recommendation: Accept

Decision requested:

Accept the NASA-first scope using Artemis II flight ephemeris for calibration
and an Artemis IV-relevant Orion trajectory-correction scenario for the future
application.

Evidence package:

- research_protocol.md
- literature/review_protocol.md
- literature/evidence_matrix.csv
- data/source_registry.csv
- configs/constraints.yaml

Risk if accepted:

The work will be relevant to Artemis-class cislunar planning but cannot claim
to reconstruct proprietary Artemis IV or SpaceX HLS operations.

Consequence if rejected:

The project requires a new mission boundary and source audit before simulator
development.

Human decision: Accepted

Consequence:

The NASA-first mission scope is frozen. Gate 2 may define numeric values and
source-qualified assumptions but may not replace the Artemis II calibration
case, Artemis IV-relevant Orion application boundary, post-injection correction
segment, or ground-planning advisory use without a protocol deviation.

## Decision Gate 2: Data and numeric freeze

Date opened: 2026-07-10  
Date package completed: 2026-07-10  
Date decided: 2026-07-11  
Status: Accepted  
Recommendation: Accept

Decision requested:

Approve or reject the audited source set, exact modeling variables, data
splits, uncertainty strata, simulator acceptance tolerances, practical-effect
threshold, and compute budget before simulator calibration and model training.

Evidence package:

- docs/gate2_data_numeric_freeze.md
- data/source_registry.csv
- data/artemis2_event_registry.csv
- data/processed/artemis2/oem_inventory.csv
- data/processed/artemis2/oem_release_revisions.csv
- data/processed/artemis2/oem_detected_discontinuities.csv
- data/processed/artemis2/validation_windows.csv
- data/processed/artemis2/two_body_baseline.csv
- configs/constraints.yaml
- configs/uncertainty_model.yaml
- configs/crew_schedule.yaml
- configs/human_acceleration_limits.yaml
- configs/simulator_acceptance.yaml
- configs/compute_budget.yaml

Recommended decision:

Accept. The package prevents forecast-as-truth leakage, quarantines the
unqualified entry product, uses correction delta-v as the primary endpoint,
and freezes meaningful validation and QML comparison rules before any model
result is visible.

Human decision: Accepted

Consequence:

The public source set, variable roles, Artemis II simulator split, uncertainty
strata, human constraints, simulator tolerances, engineering effect threshold,
algorithm trigger, and compute ceiling are frozen. Any change affecting these
items requires a dated protocol deviation. Gate 3 simulator credibility work
is authorized; ML training remains prohibited until Gate 3 is accepted.

## Decision Gate 3: Simulator credibility

Date opened: 2026-07-11  
Date package completed: 2026-07-11  
Date GMAT comparison completed: 2026-07-11  
Date decided: 2026-07-12
Status: Accepted
Recommendation: Accept with the documented RTC3 eligibility and execution-order limitations

Checkpoint 3A, 2026-07-11: the F0/F1/F2 force model, DE440s source and
checksum, integrator settings, impulsive and finite-burn mass models, public
engine catalog, and crew constraint checks were frozen in versioned code before
the formal validation pipeline was executed. Machine-learning training remains
prohibited.

Checkpoint 3B, 2026-07-11:
- Commit URL: https://github.com/taechasith/QMLforArtemisIV/commit/6ebf5517cfc8438100656a8fa0f934440538f5f6
- Tests and commands run:
  1. `uv run python scripts/validate_simulator.py` (successfully passed all 10 local credibility checks, with GMAT marked pending)
  2. `uv run python -m pytest -q` (37 tests passed, 661 subtests passed)
- Files and data added:
  - `src/openqfuel/validation.py`
  - `tests/test_validation.py`
  - `scripts/validate_simulator.py`
  - `scripts/gmat_validation.script`
  - `configs/gmat_earth_j2.cof`
  - `data/processed/simulator/interpolation_validation.csv`
  - `data/processed/simulator/numerical_convergence.csv`
  - `data/processed/simulator/f2_flight_validation.csv`
  - `data/processed/simulator/event_cross_checks.csv`
  - `data/processed/simulator/acceptance_summary.csv`
  - `docs/gate3_simulator_credibility.md`
- Visibility of final-test labels: Prohibited. No final-test labels were inspected.
- Failures or nonconverged cases: None. All 5 validation arcs converged and passed the F2 flight-validation tolerances.
- Protocol deviations: None.
- Limitation disclosure: RTC3 occurs after the OEM creation date and was recorded as `not_eligible` as required. This limitation does not block Gate 3 credibility acceptance.

Execution-order disclosure: during local prototyping, a one-off F2 smoke test
was run on all frozen windows before Checkpoint 3A was committed. No model
constant, force, threshold, window, or exclusion was fitted or changed after
viewing that output, and the exploratory output was not retained as research
evidence. This is recorded as a procedural limitation because it weakens ideal
blinding; Gate 3 acceptance must explicitly accept or reject this handling.

Checkpoint 3C, 2026-07-11 – GMAT R2026a independent comparison completed:
- Tool: NASA GMAT R2026a (official release, https://github.com/nasa/GMAT/releases/tag/R2026a)
- GMAT executable SHA-256: `36c880ad6c3f5e69b2e7e90c9d9cec4086eced9c1073fc5b289966d54db15f5f`
- GMAT archive SHA-256: `f7b00bdeb51e75f5f0a93380a97109f0505e75396f69a43cd5583c21f5fed9fc`
- Script: `scripts/gmat/gate3_same_force_model.script` (DE440s/SPICE; Earth point mass + J2; Luna and Sun point masses; no drag/SRP; RungeKutta89 accuracy=1e-13 max_step=150 s)
- Result data: `data/processed/simulator/gmat_comparison.csv`
- Frozen thresholds: position ≤ 0.100 km, velocity ≤ 0.010 m/s (both from configs/simulator_acceptance.yaml; not changed)
- All 10 independent endpoint thresholds failed:

| Window | Position difference (km) | Limit (km) | Velocity difference (m/s) | Limit (m/s) |
|---|---|---|---|---|
| V01 | 11.276 | 0.100 | 0.986 | 0.010 |
| V02 | 2.190 | 0.100 | 0.197 | 0.010 |
| V03 | 1.699 | 0.100 | 0.141 | 0.010 |
| V04 | 5.168 | 0.100 | 0.497 | 0.010 |
| V05 | 14.094 | 0.100 | 1.402 | 0.010 |

- All non-GMAT checks (parser/interpolation, numerical convergence, flight-ephemeris validation, weak-baseline improvement, event cross-checks) passed their frozen thresholds.
- RTC3 remains not eligible (occurs after OEM creation cutoff).
- No threshold, window, exclusion, or model parameter was changed after viewing these results.
- Files added in this corrective commit: `data/processed/simulator/gmat_comparison.csv`,
  `scripts/gmat/gate3_same_force_model.script`; modified files update the
  credibility report, acceptance summary, and all intermediate validation CSVs
  to reflect the completed GMAT outcome and `failed_repair_required` status.
- Corrective commit URL: https://github.com/taechasith/QMLforArtemisIV/commit/d29a035

Gate 3 credibility report status: `failed_repair_required`. The full criterion
table is in `data/processed/simulator/acceptance_summary.csv`.

Decision requested before D001 repair:

Reject Gate 3 as currently implemented (stopping ML/QML work pending a
documented repair), or authorize a dated protocol-deviation entry authorizing a
specific simulator-repair action before any dataset generation or ML training
begins.

Checkpoint 3D, 2026-07-12 – repaired comparison reviewed and Gate 3 accepted:

- Repair commit: https://github.com/taechasith/QMLforArtemisIV/commit/cbd157dcba8449833eedc5b79ae5996da51b9e0f
- Technical result: 67 criteria passed, 0 failed, and RTC3 remained `not_eligible` under the frozen OEM creation cutoff.
- Independent GMAT result: all five position and all five velocity endpoint checks passed their unchanged 0.100 km and 0.010 m/s limits.
- Maximum GMAT differences: 0.046296 km position and 0.004266 m/s velocity, both on V03.
- Accepted limitation: RTC3 cannot be treated as eligible historical/reconstructed evidence from the frozen OEM release.
- Accepted limitation: a pre-freeze one-off F2 smoke computation weakened ideal blinding, but no constant, force, threshold, window, exclusion, or model parameter was changed after viewing it.
- Human decision: **Accepted**.
- Decision date: 2026-07-12.
- Consequence: Gate 3 is closed as accepted and Gate 4 benchmark preparation is authorized. Final-test labels remain locked until the Gate 4 freeze is explicitly approved.
- Claim boundary: acceptance establishes research-simulator credibility only within the public-data model and tested domain; it does not establish flight readiness or operational approval.



## Protocol deviations

### Deviation D001 — Gate 3 GMAT COF POTFIELD format repair

Date: 2026-07-11  
Status: Applied, independently rerun, and accepted
Authority: Human research lead (user instruction: "continue")  
Scope: Repair of `configs/gmat_earth_j2.cof` only — no threshold, model constant, window, or Python dynamics change.

#### Root-cause diagnosis

A diagnostic campaign was executed on 2026-07-11 to identify the source of the Gate 3 GMAT discrepancy. The campaign used three incremental GMAT runs from the V01 initial state, all with identical 6-hour duration and identical Python DOP853 baseline:

| GMAT configuration | GMAT J2-effect on Z | Python J2-effect on Z | Agreement |
|---|---|---|---|
| F0: Earth point-mass only, no J2, no Moon/Sun | −123986.199414 km | −123986.199422 km | **0.000020 km** ← perfect |
| J2-only: Earth + J2 (openqfuel_earth_j2.cof), no Moon/Sun | −123974.925816 km | −123986.198295 km | **11.277 km** ← FAIL |
| Full model (Gate 3): Earth + J2 + Luna + Sun | −123975.203404 km | — | (from Gate 3 CSV) |

Key observations:
1. **F0 (no J2) agreement is perfect** (20 m): the integrator, time conversion, initial state, and point-mass gravity are all consistent between GMAT and Python.
2. **Enabling J2 introduces the entire 11.277 km error**: the third-body forces (Moon and Sun) were confirmed separately to account for 29.131 km in the Gate 3 full-model run, which is not the cause of the Gate 3 reported 11.276 km discrepancy.
3. **GMAT EGM96.cof at degree=2, order=0 gives +0.001128 km J2 effect** — matching Python's +0.001127 km and the physics estimate of ≈1.4 m at 256,000 km altitude.
4. **Our custom openqfuel_earth_j2.cof at the same degree=2, order=0 gives +11.274 km** — a factor of ~10,000 too large.

#### Confirmed cause

The `POTFIELD` line in `configs/gmat_earth_j2.cof` used inconsistent whitespace:

```
% BROKEN (original)
POTFIELD 2 0  1 3.98600435507000e+14 6.37813630000000e+06 1.00000000000000e+00
```

GMAT R2026a expects the same fixed-column format used in EGM96.cof (double-space delimiters between all fields). The inconsistent spacing caused GMAT to mis-align its column parser, reading the GM and/or equatorial radius fields with a numerical shift that produced an effective gravitational parameter approximately 10,000× too large for the J2 harmonic evaluation. The point-mass term (which uses GMAT's internal Earth.Mu, not the COF GM) was unaffected, explaining why F0 passed perfectly.

#### Fix applied

`configs/gmat_earth_j2.cof` POTFIELD line corrected to:

```
% FIXED
POTFIELD  2  0  1 3.98600435507000E+14 6.37813630000000E+06 1.00000000000000E+00
```

Verified: GMAT with the fixed COF gives J2-only Z-effect = +0.001119 km, consistent with EGM96 (+0.001128 km) and Python (+0.001127 km) to within 9 mm.

New COF SHA-256: `3a3ff03505c29f45d7ceadfcd0ad1ba36d1f10b2d28fd07b227939f0876d86ea`

#### Quantities NOT changed by this deviation

- Python dynamics constants (mu, J2, Re) — unchanged
- Acceptance thresholds — unchanged
- Validation windows — unchanged
- Integrator settings — unchanged
- Force model physics — unchanged (same J2 physics, now correctly transmitted to GMAT)

#### Completed follow-up

The fixed COF was used for a complete GMAT rerun in commit `cbd157d`. All 10 independent endpoint thresholds passed without changing the frozen acceptance limits. The human research lead accepted Gate 3 on 2026-07-12 with the RTC3 eligibility and execution-order limitations explicitly retained.

