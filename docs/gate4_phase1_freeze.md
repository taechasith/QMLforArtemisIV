# Gate 4 Phase 1 Benchmark Freeze

Version: 0.3.0
Prepared: 2026-07-12
Decision date: 2026-07-12
Status: `accepted`
Decision authority: Human research lead

## Decision outcome

The human research lead accepted Gate 4 together with Deviation D002 on
2026-07-12, before any research model was fitted or final-test payload was
generated. D002 preserves the bounded literature-search limitation and
requires a broader review update before manuscript submission.

Acceptance authorizes development-split scenario generation, frozen
tuning, and calibration under this package. It would not immediately unlock
either final-test split. Final access still requires a separate commit after
the selected model configurations, preprocessing state, and executable
analysis are fixed.

## Package frozen for decision

- 65,000 deterministic candidate-plan identities in 13,000 five-plan decision sets: 10,000 F0, 50,000 F1, and 5,000 F2 rows.
- Whole-group 60/10/15/15 allocation with 39,000 development, 6,500 calibration, 9,750 ID-final, and 9,750 OOD-final identities.
- 23,571 boundary/tail identities and retention of every future nonconvergence.
- Exact feature/target schema and development-only preprocessing.
- Six classical candidates, three QML candidates, and one mandatory random-feature interpretation control.
- Thirty frozen tuning trials per candidate/control, 20 development seeds, and 30 finalist seeds.
- Required 4/6/8-qubit, bandwidth, entanglement, finite-shot, and fixed-noise comparisons.
- Frozen regression, feasibility, regret, resampling, multiplicity, and failure-handling code.
- A 1,406-row screening ledger and 23-record extraction matrix, explicitly labeled as a bounded synthesis.

## Final-test lock audit

`final_test_manifest.csv` contains only group commitments and identity ranges.
All 19,500 final identities are marked `LOCKED_NOT_GENERATED`. The schema
contains no outcome data, tuning rows are `frozen_not_run`, development seed
rows are authorized after Gate 4 acceptance, and every final-test seed use
remains prohibited pending a separate unlock commit.

The final payload root is `data/locked/phase1`, is excluded by `.gitignore`, and
is absent. `openqfuel.gate4.assert_split_access` rejects both final split names
for every access purpose and rejects calibration use for fitting, tuning, or
feature selection. `scripts/prepare_gate4_freeze.py --check` also fails if any
file appears under the locked root.

Current artifact commitments are:

| Artifact | SHA-256 |
|---|---|
| `scenario_manifest.csv` | `3fbfd762a97b53e4689af13adb7b2cae06d7b17171af8ff2e8c75a2fd775de9d` |
| `final_test_manifest.csv` | `602289b43aab1a7eced04d5847c7df7cf522828b13008115d9937ee05498dd80` |
| `seed_manifest.csv` | `501dbc6149624c172b50d9d3c4fe1108e3407eaaecca3a0208cb007b5758fb40` |
| `tuning_manifest.csv` | `cd8a83408477eea05eb1c34c001b9726bf3c11f608e5ded040f50b8e3089ef32` |
| `scenario_schema.json` | `1a89391015c0b48d1279ea2a548654e1bf6a6acb843b448f8cfa9469e7eee3be` |

The post-acceptance checksum change is administrative/D003 metadata
reconciliation: final and seed statuses now state the accepted development
authorization while preserving the separate final lock, and the schema adds
`boundary_or_tail`, `payload_version`, and the secondary
`minimum_lunar_surface_altitude_km` audit outcome. Scenario identities, model
features, primary outcomes, tuning rows, and seed values are unchanged.

## Evidence and rationale

The literature package supports a cost-plus-feasibility task, independent
repropagation, strong tree/neural/kernel/physics classical baselines, explicit
QML bandwidth and entanglement controls, and seed-level negative reporting.
It does not support a prior expectation of QML superiority.

The laptop-aware staging preserves the accepted scientific budget while
avoiding an infeasible Cartesian execution. Classical trials use grouped CV;
QML and matched controls use frozen successive-halving rungs up to 1,024 rows.
Only selected configurations receive 20 development seeds. Jobs are
checkpointed and one statevector/GPU job runs at a time. Worker counts and
chunks may adapt; cases, splits, seeds, thresholds, and model comparisons may
not.

## Unresolved risks

- OpenAlex returned query counts but blocked metadata export with persistent HTTP 429; planned Crossref, ADS, and broader publisher coverage also remains incomplete.
- The first post-acceptance generator produced 7,000 invalid F0 rows; D003 preserves their audit and figures, prohibits their research use, and requires a committed first-group repair audit before scale-up.
- The in-repository quantum implementation is a statevector research reference, not validated quantum hardware.
- Public-data simulation cannot establish Artemis IV flight performance or operational safety.
- RTC3 remains outside the Gate 3 validation claim because eligible post-event evidence was unavailable.

## Decision rationale

Gate 4 with D002 was accepted because all outcome-sensitive choices were
explicit and locked, the missing literature coverage was visible before
results, and the benchmark includes conservative controls that make a negative
QML result valid.

No research outcome was generated or inspected during Gate 4 preparation or
its acceptance decision. The later invalid pre-D003 run is separately labeled
and cannot support a benchmark claim.
