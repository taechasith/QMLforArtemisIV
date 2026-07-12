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
Recommendation: Accept while explicitly recording that RTC3 was not tested and is not part of the Gate 3 validation claim

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
- Limitation disclosure: the RTC3 timing cross-check was not performed. RTC3 occurred at 2026-04-10T18:53:00Z, after the qualified OEM was created at 2026-04-10T03:22:19Z. Later rows in that OEM are pre-event predictions rather than post-event historical/reconstructed evidence. The recorded status `not_eligible` means not tested with eligible evidence; it is neither a pass nor a failure. This limitation does not block Gate 3 credibility acceptance, and acceptance does not claim RTC3 validation.

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

- All evaluable non-GMAT checks (parser/interpolation, numerical convergence, flight-ephemeris validation, weak-baseline improvement, and five event cross-checks) passed their frozen thresholds.
- RTC3 was not tested because it occurred after the qualified OEM creation time; this is neither a pass nor a failure.
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
- Technical result: 67 criteria passed, 0 failed, and the RTC3 event check was not performed.
- Independent GMAT result: all five position and all five velocity endpoint checks passed their unchanged 0.100 km and 0.010 m/s limits.
- Maximum GMAT differences: 0.046296 km position and 0.004266 m/s velocity, both on V03.
- RTC3 evidence: the event occurred at 2026-04-10T18:53:00Z, 15 hours 30 minutes 41 seconds after the qualified OEM's 2026-04-10T03:22:19Z creation time. OEM rows after that creation time are pre-event predictions, not post-event historical/reconstructed evidence.
- Alternative-source check: the separate `2026.04.10 - Post-RTC3 to EI` product remained quarantined because its mission-relative epoch, M50 frame realization, and eighth-column semantics lacked authoritative definitions.
- Status definition: `not_eligible` means **not tested with eligible evidence; neither pass nor fail**. No RTC3 timing error was computed or inferred.
- Accepted limitation: Gate 3 acceptance does not claim that RTC3 was validated.
- Accepted limitation: a pre-freeze one-off F2 smoke computation weakened ideal blinding, but no constant, force, threshold, window, exclusion, or model parameter was changed after viewing it.
- Human decision: **Accepted**.
- Decision date: 2026-07-12.
- Consequence: Gate 3 is closed as accepted and Gate 4 benchmark preparation is authorized. Final-test labels remain locked until the Gate 4 freeze is explicitly approved.
- Claim boundary: acceptance establishes research-simulator credibility only within the public-data model and tested domain; it does not establish flight readiness or operational approval.



## Decision Gate 4: Phase 1 benchmark freeze

Date opened: 2026-07-12
Date package completed: 2026-07-12
Status: **Accepted**
Decision: Accepted together with Deviation D002

Decision considered:

Accept, reject, or revise the manifest-only scenario design, grouped splits,
feature and target schema, model registry, interpretation controls, tuning
trials, random seeds, QML resource settings, and statistical analysis before
any research model is fitted.

Evidence package:

- `docs/gate4_phase1_freeze.md`
- `docs/literature_synthesis.md`
- `literature/search_log.csv`
- `literature/screening_log.csv`
- `literature/extraction_matrix.csv`
- `data/processed/simulator/data_card.md`
- `configs/phase1_benchmark.yaml`
- `data/processed/simulator/scenario_manifest.csv`
- `data/processed/simulator/final_test_manifest.csv`
- `data/processed/simulator/seed_manifest.csv`
- `data/processed/simulator/tuning_manifest.csv`
- `data/processed/simulator/scenario_schema.json`
- `docs/model_registry.md`
- `docs/phase1_analysis_plan.md`
- `src/openqfuel/gate4.py`
- `src/openqfuel/models.py`
- `src/openqfuel/qml.py`
- `src/openqfuel/phase1_analysis.py`

Freeze facts:

- The compact manifest commits 65,000 candidate-plan identities in 13,000 five-plan decision sets without generating any feature or label payload.
- The final-test commitment covers 19,500 identities and contains no outcome data.
- Nine candidate families and one interpretation control each have 30 frozen tuning rows and 30 seed rows.
- No research scenario, fitted research model, or benchmark metric was generated or inspected.
- Synthetic smoke tests verify interfaces and lock behavior only.
- `data/locked/phase1` is absent and ignored.

Recommended decision:

Accept Gate 4 and D002. The package registers conservative classical controls,
QML ablations, grouped leakage controls, laptop-feasible staging, and a
fail-closed final-test boundary before outcomes. D002 keeps the incomplete
literature coverage visible and makes a broader update mandatory before the
manuscript.

Consequence if accepted:

Development scenario generation and registered tuning may begin. Calibration
remains unavailable for model selection. Final-test features and labels do not
open automatically; a separate commit is required after finalists,
preprocessing, and executable analysis are fixed.

Consequence if rejected or revised:

No research scenario payload or model fit begins. The candidate manifests and
code are revised without access to final-test outcomes.

Human decision: **Accepted**.
Decision date: 2026-07-12.
D002 accepted concurrently.

Consequence: development-split scenario generation, frozen tuning, and calibration
are authorized as of this entry. The calibration split remains unavailable for model
selection, feature selection, or fitting. Final-test features and labels are not
unlocked by this acceptance; a separate commit is required after finalist configurations,
preprocessing state, and the executable analysis script are fixed.

Claim boundary: no research outcome, model fit, or benchmark metric was inspected before
or during this acceptance decision.

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

The fixed COF was used for a complete GMAT rerun in commit `cbd157d`. All 10 independent endpoint thresholds passed without changing the frozen acceptance limits. The human research lead accepted Gate 3 on 2026-07-12 while explicitly retaining RTC3 as not tested, neither pass nor fail, and outside the validation claim.

### Deviation D002 - bounded Gate 4 literature coverage

Date proposed: 2026-07-12
Date accepted: 2026-07-12
Status: **Accepted concurrently with Gate 4**
Authority: Human research lead

Original rule:

The accepted review protocol anticipated a complete systematic scoping search
across NTRS, OpenAlex, Crossref, NASA ADS, AIAA/publisher interfaces, standards,
and connected repositories before the Phase 1 freeze.

Proposed rule:

Use the complete NTRS/arXiv API retrieval, OpenAlex count-only logs, and 23
fully extracted primary or authoritative records to freeze Phase 1. Label the
result a bounded scoping synthesis. Complete the broader database update before
manuscript submission. Literature found after final-test access cannot alter a
registered model, split, threshold, or analysis except through a new dated
deviation.

Reason:

All seven OpenAlex queries returned counts, but metadata export was repeatedly
blocked by HTTP 429 responses. Crossref, NASA ADS, and broad publisher exports
were not completed in this pass. Claiming complete systematic coverage would
therefore be inaccurate.

Outcome visibility and likely bias:

No research feature, label, fit, or benchmark result existed when D002 was
proposed. Missing literature could omit a relevant baseline or negative QML
study. The freeze mitigates that risk with six diverse classical candidates, a
matched random-feature control, scale and entanglement ablations, and mandatory
negative reporting, but cannot prove the missing records are immaterial.

Decision requested: Accept D002 with Gate 4, reject it and hold Gate 4 for a
broader search, or request a specific revision.

Post-acceptance discovery refresh, 2026-07-12:

- The frozen S1-S7 interfaces were retried without changing their concepts or using a research model outcome.
- The current logs contain 4,708 raw API rows and 4,218 unique canonical discovery keys. OpenAlex supplied 3,278 rows: two searches completed pagination and five remain bounded to the first 100 relevance-ranked records.
- Title/abstract triage records 3,288 exclusions, 926 pending full-text screens, and four provisional includes. The 23-record Gate 4 extraction matrix remains unchanged.
- RFIG-014 records the refreshed flow and open queue. This is progress toward the mandatory manuscript update, not closure of D002 and not authorization to alter a frozen model, split, threshold, metric, or claim.

### Deviation D003 - Gate 5 scenario-generator conformance repair

Date opened: 2026-07-12
Date authorized: 2026-07-12
Status: **All F0/F1 groups qualified; F2 first-group qualification pending**
Authority: Human research lead

Original implementation:

Commit `61bef3e` added the first scenario generator while recording Gate 4
acceptance. One F0 group was generated and inspected before that generator was
committed. The committed generator and an uncommitted ephemeris-path repair
then produced all 7,000 F0 development/calibration rows. An F1 run was stopped
after its original DE440s path failed and before it wrote an F1 payload.

Observed problems:

- All 7,000 F0 rows omit required top-level `base_trajectory`, so every row fails the frozen JSON Schema.
- Twelve non-U0 groups use hard-coded uncertainty scales rather than `configs/uncertainty_model.yaml`.
- TLI and entry-interface epochs were hard-coded inconsistently with the event registry and qualified OEM metadata.
- Candidate plans use pseudorandom burns rather than the registered Sobol or Latin-hypercube design and reproducible numerical targeting reference.
- Communication delay, burn delay, and burn start are recorded as inputs but do not alter propagation.
- The 500 km and 200 m/s feasibility thresholds are implementation assumptions rather than the frozen entry-interface constraints.
- The original feasibility check does not enforce the frozen lunar-flyby exclusion and treats inertial thrust components as crew-body acceleration components.
- The first generator was not frozen in a separate pre-output commit, weakening ideal execution order.

Machine-readable audit:

- `data/processed/simulator/scenarios/pre_d003_audit.csv`
- `data/processed/simulator/scenarios/pre_d003_audit_summary.json`
- RFIG-002 through RFIG-004 in `artifacts/research_figures/figure_registry.csv`

Audit result:

Fourteen of fourteen groups are invalid. All 7,000 rows fail schema and
metadata relationship checks. Twelve groups fail uncertainty conformance. Of
1,400 decision sets, 1,020 have no independently feasible reference candidate.
No non-finite value or nonconverged propagation was observed. No final-test
payload was generated or read.

Authorized repair:

Preserve the audit and figures as failed-attempt evidence; derive epochs,
uncertainties, constraints, and vehicle values from frozen files; use a seeded
Sobol design and a documented numerical targeting reference; make every timing
and execution input effective in propagation; enforce the lunar-flyby exclusion
and an explicit burn-attitude crew-axis mapping; validate complete payloads
against schema and checksums; commit the repair before replacing payloads; and
rerun F0 before starting F1/F2. Pre-D003 payloads are prohibited from model
training, tuning, calibration, or benchmark claims.

The repair also reconciles acceptance-state metadata in the final-test and
seed manifests; adds top-level `boundary_or_tail` and `payload_version`
provenance; and records sampled lunar surface altitude as a secondary outcome
needed to audit the existing frozen constraint. No scenario identity, split,
model input, primary outcome, tuning trial, seed value, or final-test lock is
changed. Exact artifact hashes are recorded in
`docs/gate4_phase1_freeze.md`.

Outcome visibility and bias control:

F0 feasibility and terminal-error summaries were visible before D003. The
repair criteria are therefore conformance-based and may not be tuned to obtain
a preferred feasibility rate. The paper must show the pre/post repair graphs,
and any further result-changing repair requires a new deviation. No model was
fitted and no final-test feature or label was visible.

Human authorization basis: after being informed that the active F1 process
should stop and the generator required preservation, repair, and graphing, the
human research lead instructed the assistant to continue after the current run
stopped and to record all material changes as research-paper graphs.

First-group qualification, 2026-07-12:

- Repair commit `72f99c4` was pushed before corrected generation began.
- `F0/development/G01` produced 500 D003-v1 rows in 55.929 seconds from source commit `72f99c4`.
- All 500 rows pass schema and metadata relationships, all 100 decision sets are complete, the exact boundary commitment matches, and the payload checksum matches the v2 ledger.
- U0 uncertainty conformance passes; no row is non-finite or nonconverged.
- 400 of 500 candidate rows are feasible, and all 100 decision sets contain at least one feasible numerical reference.
- No final-test payload was generated or read.
- RFIG-005 and RFIG-006 record the pre/post validity and reference-laptop runtime changes.
- Scope: this qualifies only the nominal F0 checkpoint. Non-U0 F0 groups and F1/F2 still require their own audits.

All-F0 qualification, 2026-07-12:

- All 14 unlocked F0 development/calibration groups were replaced and independently audited under D003-v1.
- All 7,000 rows pass schema and relationship checks; every payload checksum matches its v2 ledger entry; all 14 uncertainty-family checks pass.
- No row is non-finite or nonconverged. No final-test payload was generated or read.
- 2,339 of 7,000 candidate rows are feasible. 319 of 1,400 decision sets have no feasible reference and remain retained under the frozen penalty/reporting rule.
- Measured group work totals 542.060 seconds, with 16.363-56.662 seconds per 500-row group on the reference laptop.
- RFIG-007 through RFIG-009 record aggregate conformance, valid feasibility coverage, and runtime.
- Outcome-visibility rule: the 319 no-reference sets are a reportable development limitation and cannot be reduced by post-result candidate retuning under D003.
- Consequence: F0 repair is qualified. F1 may begin with one group followed by a separate full audit before scale-up; F2 remains pending.

Post-F0 compute adaptation:

Before F1, the implementation added a deterministic within-group cache for
zero-delta-v candidates with byte-identical true states. It retains each
candidate's actual-start metadata and does not cache nonzero burns or distinct
uncertainty states. This is an execution-only laptop adaptation under the
already frozen compute rule; it does not alter scenario identities, sampled
inputs, force models, outcomes, constraints, or acceptance criteria.

F1 first-group qualification, 2026-07-12:

- `F1/development/G01` produced 2,500 D003-v1 rows in 1,268.159 seconds from source commit `f124327`.
- All 2,500 rows pass strict schema, relationship, finite-value, uncertainty, checksum, and decision-set audits.
- 2,000 candidate rows are feasible; all 500 decision sets retain at least one feasible reference; no row is nonconverged.
- No final-test payload was generated or read.
- RFIG-010 records F0/F1 G01 coverage and the 22.7-fold observed F1/F0 wall-time ratio.
- The remaining F1 CPU requirement is projected at approximately 13.8 hours from G01 duration-normalized work; four independent workers imply about 3.5 hours only under ideal balance, so actual group ledgers remain authoritative.
- A four-worker group scheduler is authorized only after this audit. It uses process-isolated ephemerides, one numerical-library thread per worker, atomic payload writes, and an exclusive append lock for the shared v2 ledger.

All-F1 qualification, 2026-07-12:

- All 14 unlocked F1 development/calibration groups completed under D003-v1 and pass the independent strict audit.
- All 35,000 rows pass schema, relationship, finite-value, uncertainty-family, checksum, and decision-set checks. No row is nonconverged, and no final-test payload was generated or read.
- 6,436 of 35,000 candidate rows are feasible. Of 7,000 decision sets, 4,215 have no feasible numerical reference and remain included under the frozen penalty/reporting rule.
- The serial G01 qualification consumed 1,268.159 seconds. The separate four-worker G02-G14 scale-up consumed 63,639.442 seconds of summed group work in 18,148.400 seconds of wall time, yielding effective concurrency 3.51.
- Total measured F1 group work is 64,907.601 seconds (18.030 worker-hours). Combined active wall time for the serial checkpoint and parallel scale-up is 19,416.559 seconds (5.393 hours), excluding the idle interval between stages.
- The pre-scale-up estimate of 13.8 worker-hours and 3.5 ideal wall-hours was optimistic. The scientific workload was not reduced: rows, force models, tolerances, constraints, and worker ceilings remained frozen.
- RFIG-011 through RFIG-013 record full-F1 coverage, reference-laptop runtime, and the exact F0/F1 campaign summary.
- Outcome-visibility rule: the 4,215 no-reference sets are a reportable development limitation. They cannot motivate post-result candidate redesign or uncertainty retuning under D003.
- Consequence: F1 is qualified. F2 may begin with one serial group and must pass its own strict first-group audit before the authorized two-worker scale-up. Model fitting remains prohibited until the full F2 audit passes.

