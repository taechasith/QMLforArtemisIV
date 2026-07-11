# Gate 4 Phase 1 Benchmark Freeze

Version: 0.3.0
Prepared: 2026-07-12
Status: `pending_human_approval`
Decision authority: Human research lead

## Decision requested

Accept, reject, or revise the Phase 1 benchmark freeze before any research
model is fitted or any final-test payload is generated. The recommended choice
is **accept Gate 4 together with proposed Deviation D002**, which preserves the
bounded literature-search limitation and requires a broader review update
before manuscript submission.

Acceptance would authorize development-split scenario generation, frozen
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
contains no outcome data, tuning rows are `frozen_not_run`, and seed rows permit
only synthetic smoke tests before approval.

The final payload root is `data/locked/phase1`, is excluded by `.gitignore`, and
is absent. `openqfuel.gate4.assert_split_access` rejects both final split names
for every access purpose and rejects calibration use for fitting, tuning, or
feature selection. `scripts/prepare_gate4_freeze.py --check` also fails if any
file appears under the locked root.

Current artifact commitments are:

| Artifact | SHA-256 |
|---|---|
| `scenario_manifest.csv` | `3fbfd762a97b53e4689af13adb7b2cae06d7b17171af8ff2e8c75a2fd775de9d` |
| `final_test_manifest.csv` | `8fdc689064bc74c394bbf551ceb5c5b0029341bb73eb29d9c35d4da64e94886f` |
| `seed_manifest.csv` | `5a79674adeb9dc390bfa64470d7ba10f981f9e250a183627792484093aea5b40` |
| `tuning_manifest.csv` | `cd8a83408477eea05eb1c34c001b9726bf3c11f608e5ded040f50b8e3089ef32` |
| `scenario_schema.json` | `92b2d7f10ca866944e6be6faeda6c49d894aab8ba852790a055218ff4d00b228` |

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
- Scenario payload generators are deliberately not run yet, so throughput and realized failure rates remain unmeasured.
- The in-repository quantum implementation is a statevector research reference, not validated quantum hardware.
- Public-data simulation cannot establish Artemis IV flight performance or operational safety.
- RTC3 remains outside the Gate 3 validation claim because eligible post-event evidence was unavailable.

## Recommendation

Accepting Gate 4 with D002 is recommended because all outcome-sensitive choices
are now explicit and locked, the missing literature coverage is visible before
results, and the benchmark includes conservative controls that make a negative
QML result valid. Reject or revise if the human research lead requires a
complete multi-database systematic review before any development scenario is
generated.

No research outcome has been generated or inspected during Gate 4 preparation.
