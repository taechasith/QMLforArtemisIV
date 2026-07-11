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
Status: Failed – repair required; pending human decision  
Recommendation: Reject current implementation or authorize a documented simulator-repair protocol deviation

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

Decision requested:

Reject Gate 3 as currently implemented (stopping ML/QML work pending a
documented repair), or authorize a dated protocol-deviation entry authorizing a
specific simulator-repair action before any dataset generation or ML training
begins.


## Protocol deviations

No deviations recorded.
