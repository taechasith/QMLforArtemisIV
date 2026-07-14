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
Status: **All unlocked payloads qualified; D003 scenario-generation repair complete**
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
- The F0/F1-only G01 checkpoint values remain in the audit and ledger CSVs.
  The interim standalone visual was superseded by the three-fidelity checkpoint
  in RFIG-015 after F2 G01 qualified.
- The remaining F1 CPU requirement is projected at approximately 13.8 hours from G01 duration-normalized work; four independent workers imply about 3.5 hours only under ideal balance, so actual group ledgers remain authoritative.
- A four-worker group scheduler is authorized only after this audit. It uses process-isolated ephemerides, one numerical-library thread per worker, atomic payload writes, and an exclusive append lock for the shared v2 ledger.

All-F1 qualification, 2026-07-12:

- All 14 unlocked F1 development/calibration groups completed under D003-v1 and pass the independent strict audit.
- All 35,000 rows pass schema, relationship, finite-value, uncertainty-family, checksum, and decision-set checks. No row is nonconverged, and no final-test payload was generated or read.
- 6,436 of 35,000 candidate rows are feasible. Of 7,000 decision sets, 4,215 have no feasible numerical reference and remain included under the frozen penalty/reporting rule.
- The serial G01 qualification consumed 1,268.159 seconds. The separate four-worker G02-G14 scale-up consumed 63,639.442 seconds of summed group work in 18,148.400 seconds of wall time, yielding effective concurrency 3.51.
- Total measured F1 group work is 64,907.601 seconds (18.030 worker-hours). Combined active wall time for the serial checkpoint and parallel scale-up is 19,416.559 seconds (5.393 hours), excluding the idle interval between stages.
- The pre-scale-up estimate of 13.8 worker-hours and 3.5 ideal wall-hours was optimistic. The scientific workload was not reduced: rows, force models, tolerances, constraints, and worker ceilings remained frozen.
- RFIG-011 and RFIG-012 record full-F1 coverage and reference-laptop runtime.
  The interim F0/F1-only campaign summary was superseded by the full F0/F1/F2
  campaign summary in RFIG-018.
- Outcome-visibility rule: the 4,215 no-reference sets are a reportable development limitation. They cannot motivate post-result candidate redesign or uncertainty retuning under D003.
- Consequence: F1 is qualified. F2 may begin with one serial group and must pass its own strict first-group audit before the authorized two-worker scale-up. Model fitting remains prohibited until the full F2 audit passes.

F2 first-group qualification, 2026-07-12:

- `F2/development/G01` produced 250 D003-v1 rows in 450.835 seconds from source commit `9d18500`.
- All 250 rows pass strict schema, relationship, finite-value, uncertainty, checksum, and decision-set audits. No row is nonconverged, and no final-test payload was generated or read.
- 200 candidate rows are feasible, and all 50 decision sets retain at least one feasible numerical reference.
- F2 required 1.803 seconds per row, 3.555 times the F1 G01 per-row cost. Scaling the measured F1 G02-G14 work by that ratio and the one-tenth F2 row count projects 22,624.046 seconds (6.285 worker-hours) for the remaining groups.
- At the frozen two-worker ceiling, the ideal projection is 11,312.023 seconds (3.142 hours); the planning estimate adds 25% and is 14,140.029 seconds (3.928 hours). Measured F2 ledgers remain authoritative.
- RFIG-015 records exact F0/F1/F2 G01 validity, coverage, normalized runtime, and the scale-up planning boundary.
- Consequence: F2 G01 is qualified. After this checkpoint is committed, G02-G14 may run with at most two process-isolated workers, one numerical-library thread per worker, atomic payload writes, and the locked v2 ledger. No model fitting is authorized before the full-F2 audit passes.

All-F2 qualification, 2026-07-12:

- All 14 unlocked F2 development/calibration groups completed under D003-v1 and pass the independent strict audit.
- All 3,500 rows pass schema, relationship, finite-value, uncertainty-family, checksum, and decision-set checks. No row is nonconverged, and no final-test payload was generated or read.
- 642 of 3,500 candidate rows are feasible. Of 700 decision sets, 423 have no feasible numerical reference and remain included under the frozen penalty/reporting rule.
- The two-worker G02-G14 scale-up consumed 15,604.130 seconds (4.334 worker-hours) of summed group work in 7,978.900 seconds (2.216 wall-hours), yielding effective concurrency 1.956.
- Including serial G01, total measured F2 group work is 16,054.965 seconds (4.460 worker-hours), and combined active wall time is 8,429.735 seconds (2.342 hours), excluding the idle interval between stages.
- Actual scale-up work was 68.97% of the 22,624.046-second projection, and actual wall time was 56.43% of the conservative 14,140.029-second planning estimate. The estimate remains preserved as scheduling evidence.
- RFIG-016 through RFIG-018 record full-F2 coverage, reference-laptop runtime, and the exact F0/F1/F2 campaign summary.
- Outcome-visibility rule: the 423 no-reference sets are a reportable development limitation and cannot motivate candidate redesign, uncertainty retuning, or constraint changes under D003.
- Consequence: D003 scenario generation is complete. All 45,500 unlocked rows across 42 F0/F1/F2 groups are qualified. Registered model fitting may begin on development rows only; calibration remains restricted to post-selection calibration, and final-test payloads remain absent and locked.

### Deviation D004 - Gate 5 literature hardening before model fitting

Date opened: 2026-07-12
Date authorized: 2026-07-12
Status: **Authorized; pre-fit controls added**
Authority: Human research lead

Original rule:

Gate 4 froze the Phase 1 candidate families, splits, thresholds, tuning trials,
seed plan, QML resources, matched control, and analysis plan from the accepted
bounded literature synthesis. D002 already required broader literature closure
before manuscript submission and prohibited outcome-driven model changes after
final-test access.

Revised rule:

Before any research model fit, Gate 5 adds a literature-hardening layer:
source-grade discipline, mandatory quantum-kernel concentration and bandwidth
diagnostics, variational-trainability failure reporting, matched
random-feature and compressed-classical dequantization controls, fixed regime
reports, and RFIG-019. The accepted model families, splits, thresholds, tuning
budgets, sample rungs, seed counts, scenario identities, and final-test lock do
not change.

Reason:

The human research lead requested a stronger Gate 5 process after reviewing the
local QML space-fuel literature note. That note contains useful research leads
but mixes primary papers, arXiv manuscripts, vendor articles, RequestPDF pages,
and broad claims. A high-impact paper needs tighter source vetting and explicit
QML failure diagnostics before model fitting begins.

Outcome visibility and likely bias:

All unlocked F0/F1/F2 scenario audits and no-reference rates were visible. No
research model had been fitted, no calibration data had been used for fitting
or selection, and no final-test payload had been generated or read. Because
scenario-level outcomes were visible, D004 is restricted to diagnostics,
reporting, interpretation, and claim discipline. It cannot be used to redesign
candidate plans, retune uncertainty distributions, change thresholds, alter
ranking objectives, add a candidate family, or promote QRL, dynamic circuits,
quantum annealing, or QAOA into Phase 1.

Controls and evidence:

- `docs/phase1_analysis_plan.md` now requires source-grade screening, kernel diagnostics, trainability diagnostics, dequantization controls, fixed regime reports, and claim-boundary checks.
- `docs/literature_synthesis.md` records the additional primary-source implications and defers adjacent QRL/dynamic-circuit work.
- `data/processed/reporting/gate5_literature_hardening_matrix.csv` is the machine-readable hardening matrix.
- RFIG-019 records the literature-to-control matrix for the paper.

Consequence:

The next technical step is to freeze a Gate 5 runner that emits these
diagnostics before executing any development-only research fit. Final-test
payloads remain absent and locked.

### Deviation D005 - Gate 5 runner scientific correction

Date opened: 2026-07-12
Date accepted: 2026-07-12
Status: **Accepted; development-only research fitting authorized**
Authority: Human research lead

Original rule:

Gate 4 froze five-fold grouped CV, hash-selected QML learning rungs, shared
preprocessing, matched controls, target standardization, and residual families.
It did not freeze the exact group-to-fold map, row-hash namespace, weighting of
unequal folds, or the executable mapping from a transformed matrix to the
physical low-fidelity baseline.

Accepted revised rule:

- Assign G01-G12 by deterministic greedy balance of frozen uncertainty family and trajectory family, with master-seeded SHA-256 tie breaks and no outcomes.
- Select nested training rows with `SHA-256(master_seed|gate5_learning_row_v1|scenario_id)` inside each training fold.
- Fit imputation, encoding, feature scaling, target scaling, and PCA inside each training fold only.
- Rank by pooled out-of-fold NRMSE using the frozen full-development denominator; retain unweighted fold NRMSE as a diagnostic.
- Match QML, A01, and compressed C05 by rows, fold, rung, PCA dimension, and seed index while preserving each family's frozen integer seed.
- Cycle A01 and compressed-C05 trial orders across 4/6/8 dimensions, 10 trials each, and retain at least one eligible QML trial per required qubit count at every rung before filling remaining slots by rank.
- Append named low-fidelity cost in fold target-standardized units for C06/Q03; remove it from Q03 circuit inputs before residual addition.
- Make any failed fold ineligible to advance and retain the failure record.
- Checkpoint every completed fold atomically and reject resume when the source/trial/view/rung/dimension signature differs.

Reason:

Fitting transforms on the full development pool would leak validation-fold
statistics. Treating the last transformed column as low-fidelity cost is not
valid after one-hot encoding or PCA. Equal averaging of folds containing two
versus three whole groups changes group weights. Exact integer seed equality
across unlike algorithms does not create common random numbers because their
random-number consumption differs.

Outcome visibility and likely bias:

Scenario outcomes, feasibility rates, and no-reference rates were already
visible under D003/D004. No research model was fitted, no model metric was
visible, no calibration row was used for fitting or selection, and no final
payload was generated or read. Fold and row assignment use identifiers only;
they cannot respond to labels. The proposed correction may change future model
scores relative to a leaky or physically incorrect implementation, which is
the intended preventive effect.

Controls and evidence:

- `openqfuel.gate5` implements development-only loading, audits, hashes, fold-local transforms, target scaling, diagnostics, and execution blocking.
- `scripts/run_phase1_development.py` exposes read-only preflight and guarded trial execution.
- `data/processed/reporting/gate5_cv_fold_manifest.csv` records the label-agnostic fold map.
- `data/processed/reporting/gate5_preflight_audit.json` records 39,000 development rows, 7,800 complete decision sets, both feasibility classes in every fold, and zero calibration/final reads.
- RFIG-020 records fold balance and group isolation for the paper.
- Synthetic tests verify nesting, transform isolation, physical baseline handling, optimizer diagnostics, and the pending-acceptance execution block.

Preflight refinement disclosure:

The first candidate used pure hash round-robin assignment. Its read-only audit
placed both U0 groups in one fold and produced feasibility rates from 5.4% to
80.6%. Before any model fit, D005 replaced that candidate with deterministic
balancing of frozen uncertainty and trajectory-family design strata. Outcome
values are not inputs to the final assignment. The final proposed folds still
show substantial 5.0%-45.0% feasibility variation, which is retained as real
group heterogeneity rather than further tuning folds to outcomes.

Human decision:

The human research lead accepted D005 after the candidate was published at
commit `80ae35d`. Acceptance authorizes development-only fitting under the
corrected runner. It does not authorize calibration use, final-test generation
or access, the Gate 5 algorithm-trigger outcome, or Gate 6.

Consequence:

The research-fit guard is enabled only for the accepted development split.
All formal task checkpoints must name the clean post-acceptance source commit,
and calibration/final-test read counts must remain zero.

### Deviation D006 - Pre-fit campaign and matched-control conformance refinement

Date opened: 2026-07-12
Date accepted: 2026-07-12
Status: **Accepted by the human research lead**
Authority requested: Human research lead

Original rule:

The D005 candidate generated 330 first-stage tasks. A01 and compressed C05
cycled their 30 trial orders over 4/6/8 dimensions, ten trials per dimension,
and the single-task executor did not yet orchestrate successive halving or the
selected-configuration 20-seed stage.

Proposed revised rule:

- Repeat each frozen A01 and compressed-C05 hyperparameter trial at every required 4/6/8 PCA dimension. These are 180 diagnostic execution views, not new tuning trials, producing 450 first-stage tasks in total.
- Advance A01 and compressed C05 independently within each dimension so the interpretation control remains tuned, while also carrying the exact same-index control for every surviving QML task.
- Bind every rung, selection, and 20-seed authorization to immutable source and parent-stage digests; block selection from incomplete work and preserve terminal task failures without silent retry.
- Resolve the selected configuration's existing family seed indices 1-20 explicitly; no seed, model family, parameter value, sample rung, or ranking budget is added.
- Reject campaign, experiment, and direct-run output paths beneath the separately locked final-payload root before creating any lock or failure artifact.
- Require a source-bound, failure-free campaign audit before the technical trigger can pass. D004 feature-scale, entanglement-removal, random-feature, parameter-count, sample/rung, and no-reference checks are mandatory report-only diagnostics; even a technical pass remains pending explicit human interpretation.
- Distinguish a valid scientific `FAIL` from `UNAVAILABLE` evidence. Missing, invalid, source-mismatched, or diagnostically incomplete evidence requires repair and cannot be called a negative benchmark result.
- Vectorize mathematically identical statevector batches to keep the proposed campaign inside the frozen wall-time ceiling. The recorded state/feature/kernel difference is at most `2.67e-15`, with no change to circuits, objectives, optimizers, seeds, or predictions beyond floating-point roundoff.

Reason:

A post-acceptance, pre-fit audit found that independently cycling control
dimensions matched the QML dimension at the same trial/seed index for only
18/30 Q01, 14/30 Q02, and 12/30 Q03 trials. It also found that a low-level
single-task command could not enforce rung advancement, immutable selection,
20-seed reruns, or strong independently tuned controls. Executing the 330-row
plan would therefore contradict the accepted matched-control claim.

Outcome visibility and likely bias:

No research model had been fitted and no model metric was visible. No
calibration or final-test row was read. The expanded mapping uses only the
frozen tuning manifest's trial order and qubit field; it cannot respond to a
model outcome. Candidate families, hyperparameter trials, folds, row hashes,
targets, thresholds, objectives, retention counts, and final locks do not
change. Static task counts fit inside the accepted ceilings, but the full
campaign is not authorized from counts alone: the frozen C04-T02 full-data
view and Q01-T04/Q02-T07/Q03-T14 plus their matched controls at the 1,024-row
rung must establish a runtime/storage projection with 25% margin before
scale-up. These outcome-blindly chosen checkpoint tasks are separately
authorized; their scores do not enter halving or export unless the identical
task is later authorized by its preceding-rung ranking. The projection uses
end-to-end task time rather than fit/predict windows alone. The ceiling remains
1,275 formal tasks and conservatively counts all ten qualification tasks again,
without overlap credit, for at most 1,285 executions in resource projections.

Controls and evidence:

- `gate5_initial_execution_plan.csv` is regenerated with 270 candidate tasks and 180 non-winning control views.
- `openqfuel.gate5_campaign` enforces stage authorization, exact control matching, independent control advancement, task validation, atomic locks, terminal-state selection, and formal 20-seed coverage.
- Result CSV digests, task signatures, source commit, development scope, selection identity, control dimension/view, and zero locked-split reads are revalidated before reporting; malformed or incomplete evidence produces an `UNAVAILABLE` repair report rather than a partial pass or negative QML result.
- Statevector equivalence tests cover 4-12 qubits, one to three layers, kernels, features, finite shots, objectives, and numerical gradients.
- Formal fitting still requires a clean tracked tree and leaves calibration and both final-test splits untouched.

Human decision:

The human research lead explicitly accepted D006 after the candidate was
published at commit `3ac9403`. Acceptance lets the 450-task first-stage
contract supersede only the D005 execution-plan mapping and authorizes the
development-only research fitting campaign from a clean post-acceptance source
commit. D006 does not create another candidate family or increase the 30-trial
hyperparameter search.

Consequence:

The bounded ten-task qualification benchmark may run first. Full scale-up is
authorized only if its frozen 25%-margin compute, wall-time, and storage audit
passes. Calibration and both final-test splits remain locked, and the later
Gate 5 scientific trigger remains a separate human accept/reject/revise
decision after development-only evidence is published.

### Deviation D007 - Post-fit terminal-nonadvancement reporting conformance

Date opened: 2026-07-13
Status: **Accepted for reporting-only regeneration on 2026-07-13**
Authority: Human research lead

Original rule:

D006 requires complete, source-bound campaign evidence before the technical
Gate 5 trigger can be classified as `PASS` or `FAIL`. The implemented reporter
interprets completeness as requiring a finalist, all four learning rungs, and
20 selected-configuration seed reruns from every registered QML family.

Observed problem:

The D006 campaign completed 671 tuning tasks and 200 seed tasks: 871/871 are
terminally complete, none failed, and calibration/final-test reads remain zero.
At the 128-row rung, 8/30 Q02 tasks and 4/30 Q03 tasks were eligible, below the
frozen retain count of 15. The immutable ranking therefore recorded all 30
tasks in each family as nonadvancing with `Too few eligible trials to satisfy
the frozen retention count`. Q01 advanced through all four rungs.

The selection artifact nevertheless labels the two registered scientific
stops `incomplete_with_terminal_failures`. There were no terminal task
failures. The reporter also ignores the 150 complete tuning-fold optimizer and
trainability records per stopped family because it demands nonexistent seed
reruns. The first report therefore remains `UNAVAILABLE`.

Proposed revised rule:

- Change reporting semantics only. Do not refit, rerank, retry, or add any model, trial, rung, seed, threshold, split, family, or control.
- Leave every D006 campaign artifact, authorization, score, and digest unchanged.
- Byte-match the reporter, figure generator, campaign audit, rung rankings, and all tuning/seed result, fold, and regime tables to the accepted D007 candidate's Git snapshot before publication. Preserve the D006 campaign source separately from the accepted candidate, clean reporting-source commit, and code hashes. Write the complete derived-package digest manifest last, and require it before figure generation.
- Recognize only the exact Q02/Q03 source-bound terminal-nonadvancement case: all 30 frozen tasks and 150 folds must be signed complete, source-matched, development-only, zero-read, and diagnostically complete; task eligibility must recompute below retain=15; the immutable ranking must contain no selected row and the exact frozen retention error.
- Treat any missing/failed task, digest mismatch, incomplete fold, inconsistent eligibility, unexpected missing family/control, or altered ranking as `UNAVAILABLE`.
- Evaluate learning-rung and trainability completeness over authorized/reached stages. Q01 retains four-rung and 20-seed evidence. Q02/Q03 retain their complete 128-row tuning diagnostics, while later rungs and seed reruns are explicitly `not_reached_under_frozen_eligibility`.
- Never substitute the qualification-only 1,024-row Q02/Q03 tasks into selection or trigger evidence. Evaluate the unchanged trigger only over eligible finalists.

Outcome visibility and likely bias:

At the D007 acceptance decision, development outcomes were visible and Q01
provisionally had mean NRMSE 0.6466,
C06 had 0.00874, their relative gap was 72.99, and no preregistered regime
qualified. D007 could therefore change the official status from `UNAVAILABLE`
to a valid scientific `FAIL`. It cannot improve or recalculate a model score,
but it changes whether existing evidence is decision-eligible, so explicit
post-outcome human acceptance is required.

Human decision:

Accepted on 2026-07-13 against candidate commit
`7a726c8917a85f24313208eb18c33e1ccb5f703e`. This post-outcome acceptance is
limited to the reporting semantics above. It does not accept the resulting
technical Gate 5 outcome and does not authorize refitting, reranking,
calibration/final-test access, Gate 6, or new algorithm work.

Consequence:

Regeneration is authorized only for the report, diagnostic summary, model
registry, reporting CSVs, and RFIG-021 through RFIG-023 from unchanged D006
evidence. The resulting technical outcome still requires a separate human Gate 5
accept/reject/revise decision. Calibration, final tests, Gate 6, and new
algorithm work remain unauthorized.

Reporting completion:

- The reporting-only entry point ran from clean source commit `7b7db694cd7911a2643950c4c57f993046271a95` after byte-matching the D007 implementation and immutable D006 evidence to accepted candidate `7a726c8917a85f24313208eb18c33e1ccb5f703e`.
- The derived-package manifest is complete, all embedded provenance agrees, and RFIG-021 through RFIG-023 match their registered PNG/SVG SHA-256 values.
- The official technical trigger is `FAIL`: Q01 mean NRMSE is `0.6466136067`, C06 mean NRMSE is `0.0087390408`, the relative gap is `72.9913708168`, and zero preregistered regimes qualify.
- Q02 and Q03 are `verified_terminal_nonadvancing`; their absent later rungs and seed reruns are `not_reached_under_frozen_eligibility`, not task failures.
- All 871 campaign tasks remain complete with zero failures, zero calibration reads, and zero final-test reads. Immutable D006 evidence did not change.
- The resulting technical `FAIL` was subsequently accepted under the separate Gate 5 human decision below. RFIG-021 through RFIG-023 and all D006 evidence remain unchanged.

### Decision Gate 5 - Technical FAIL accepted

Date: 2026-07-13
Status: **Accepted with technical outcome `FAIL`**
Authority: Human research lead

Evidence basis:

- Official D007 reporting package published at commit `8ab1ba5114dbf7c5ae1f0ae4e490d501e784796d`.
- All 871 D006 campaign tasks are complete with zero failures, zero calibration reads, and zero final-test reads.
- Q01 mean NRMSE is `0.6466136067` versus C06 at `0.0087390408`; the relative gap is `72.9913708168`, and zero preregistered regimes qualify.
- Q02 and Q03 are verified terminally nonadvancing; later rungs and seed reruns are `not_reached_under_frozen_eligibility`, not failed experiments.

Human decision:

The human research lead accepts the unchanged technical `FAIL` as the official
Gate 5 result. The accepted inference is limited to this preregistered
development benchmark: the registered QML evidence did not satisfy the frozen
algorithm trigger. It is not a universal claim that QML cannot work.

Consequence:

- Gate 5 is closed, and development of the proposed new algorithm is rejected under the frozen trigger.
- No refit, rerank, retry, threshold change, new family, or post-outcome rescue analysis is authorized.
- Calibration and final-test data remain locked. Gate 6 remains unauthorized and requires a separate prospective human decision.
- The D007 report package remains byte-unchanged as the pre-decision evidence snapshot, so its internal `pending_human_accept_reject_or_revise` status is historical rather than the current governance state. `configs/phase1_benchmark.yaml`, this log, and the gate timeline carry the accepted decision.
- RFIG-001 is updated to record the accepted gate state. RFIG-021 through RFIG-023 remain the unchanged scientific evidence.

### Post-Gate-5 exploratory protocol P001 - Q01b and feasibility-only quantum kernel

Date opened: 2026-07-13
Status: **Opened prospectively; no experiment authorized**
Authority: Human research lead

Human decision:

Open a new post-Gate-5 exploratory protocol with `Q01b` projected quantum
kernel and `FQK` feasibility-only quantum kernel as the only near-term QML
tests. Quantum reinforcement learning, dynamic circuits, quantum annealing,
QAOA, new variational QML architectures, larger-qubit circuits, and hardware
execution remain appendix or future-work topics only.

Reason:

The accepted Gate 5 result is a valid negative result for the preregistered
development benchmark, but it is not a universal claim that QML cannot work.
The literature review identified projected quantum kernels and feasibility
classification as the only near-term QML directions that still map cleanly to
the original supervised surrogate, grouped-development, matched-control, and
safety-filter pipeline.

Outcome visibility and likely bias:

The Gate 5 development result is fully visible: Q01 failed the frozen trigger,
and Q02/Q03 were verified terminally nonadvancing. This creates post-outcome
bias risk. P001 therefore cannot change the Gate 5 result, refit D006 evidence,
alter thresholds, unlock calibration/final-test rows, or authorize Gate 6. Any
future execution must be frozen in a separate pre-result implementation
decision before any new model output is inspected.

Controls and evidence:

- `docs/post_gate5_exploratory_protocol.md` defines the hard boundaries.
- `data/processed/reporting/post_gate5_exploratory_protocol_matrix.csv`
  records near-term versus appendix/future-only scope.
- `configs/phase1_benchmark.yaml` records zero calibration/final-test access,
  no Gate 6 authorization, and no D006 refit authorization.
- RFIG-024 records the protocol boundary for paper reporting.

Consequence:

The next allowed technical step is an implementation freeze for Q01b and FQK
only. No exploratory model fit, calibration read, final-test read, hardware
claim, or Gate 6 run is authorized by this entry.

### D008 accepted - post-Gate-5 exploratory implementation freeze

Date prepared: 2026-07-13
Date accepted: 2026-07-13
Status: **Accepted for implementation and synthetic validation only; research-data execution unauthorized**
Authority required: Human research lead

Decision:

The human research lead accepted the exact implementation contract for Q01b
projected quantum-kernel cost regression and FQK feasibility-only
quantum-kernel classification. The accepted scope authorizes implementation
and synthetic correctness validation only. A separate clean-source execution
decision is still required before any development-row fit.

Accepted freeze:

- Use the existing five grouped development folds, fold-local preprocessing,
  nested hash-selected rung rows, and locked calibration/final boundaries.
- Reuse one set of 30 exactly balanced projected-state configurations across
  Q01b and FQK: 4/6/8 qubits, one/two data-reupload layers, feature scales
  0.5/1/2, entangled/unentangled maps, median-distance gamma multipliers
  0.25/1/4, and kernel regularization 0.0001/0.01/1.
- Project each encoded state to Pauli X/Y/Z expectations for every qubit,
  representing the one-qubit reduced density matrices. Use the frozen RBF on
  one-RDM Frobenius distances with at most 256 Nyström landmarks.
- Rank Q01b by robust-cost NRMSE then constrained regret. Rank FQK by Brier
  score, fixed-threshold recall, AUROC, then precision. The local FQK ID means
  feasibility-only quantum kernel, not fidelity quantum kernel.
- Preserve the original 128/256/512/1,024-row successive-halving structure and
  20 selected-configuration seed indices. Shot/noise views are report-only and
  cannot rerank or retune.
- Require C06, A01, compressed C05, and an exact classical RBF-on-PCA control
  for Q01b; require all frozen selected classical feasibility heads plus the
  same dequantization controls for FQK.
- Fit the reference i9-13900HX/32 GiB laptop by sharing projected features,
  allowing one statevector task, starting classical controls at four workers,
  and requiring a representative pre-execution benchmark with 25% margin.

Failure-discussion rule:

Every technical failure, resource stop, undefined metric, terminal
nonadvancement, or scientific negative must be committed with its evidence,
bounded interpretation, and an improvement suggested for future research.
Every such suggestion must state `new_protocol_required=true`,
`active_pipeline_change_authorized=false`, and
`post_outcome_retry_authorized=false`. The record informs the paper discussion
but cannot alter, extend, retry, or rescue P001.

Evidence accepted:

- `configs/post_gate5_exploratory.yaml` is the machine-readable freeze.
- `docs/post_gate5_implementation_freeze.md` is the human-readable contract.
- `data/processed/reporting/post_gate5_exploratory_trial_manifest.csv` contains
  30 paired rows, all marked `frozen_not_run`.
- `data/processed/reporting/post_gate5_future_research_discussion.csv` contains
  only the required schema header; no outcome exists.
- RFIG-025 is a pre-execution methods diagram, not performance evidence.

Consequence after acceptance:

Implementation and synthetic validation are authorized. Research fit,
calibration/final-test read, hardware run, larger-qubit run, Gate 5
reinterpretation, and Gate 6 work remain unauthorized by D008.

Implementation and synthetic validation record:

- `src/openqfuel/qml.py` now implements Pauli X/Y/Z one-RDM projection,
  projected one-RDM Frobenius distances, fold-local median-distance gamma,
  deterministic SHA-256 Nystrom landmarks, PSD clipping diagnostics, and
  projected-kernel regressors/classifiers for Q01b and FQK.
- `src/openqfuel/post_gate5.py` enforces the D008 boundary: implementation and
  synthetic validation may run, while development-row fitting,
  calibration/final-test reads, hardware execution, and Gate 6 remain locked.
- `tests/test_post_gate5_projected_kernel.py` validates only synthetic arrays
  and explicit toy statevectors. It does not load development payloads,
  calibration rows, final-test rows, hardware devices, or Gate 6 scenarios.

Consequence after implementation:

The next allowed process step is a separate clean-source compute preflight and
execution decision before any exploratory development-row fit. A failure in a
future step must still commit a future-research discussion record without
changing or retrying the active P001 pipeline.

### D009 accepted - clean-source synthetic compute preflight

Date prepared: 2026-07-13
Date accepted: 2026-07-13
Status: **Accepted for one synthetic compute preflight; outcome pending; research-data execution unauthorized**
Authority required: Human research lead

Decision:

The human research lead instructed the project to proceed with the recommended
next step. D009 therefore authorizes exactly one clean-source synthetic compute
admission benchmark for the accepted D008 implementation. It does not
authorize a development-row fit, calibration/final-test access, model
selection, hardware/GPU execution, Gate 5 reinterpretation, or Gate 6.

Accepted preflight:

- Use 1,024 deterministic synthetic training rows and 256 deterministic
  synthetic validation rows, with 64 primary-control features and eight
  compressed circuit features.
- Benchmark the worst admitted near-term circuit size: eight qubits, two
  data-reupload layers, entanglement enabled, one exact statevector task, and
  256 deterministic Nystrom landmarks.
- Share the quantum projection across Q01b cost and FQK feasibility heads.
- Execute every unique D008 matched control using its frozen Gate 5 parameter
  record, including C01-C06 where applicable, A01-T04, A02 classical RBF, and
  compressed C05-T17.
- Project the complete branch as 477.5 equivalent 1,024-row units and charge
  the full benchmark to every unit before applying a 25% margin. This is a
  conservative admission bound and assumes no cache savings.
- Require no more than 250 CPU-core-hours, five sequential wall-clock days,
  20 GiB new artifacts, and 24 GiB peak process working set, while retaining at
  least 20 GiB free disk after projected artifacts.

Evidence frozen before execution:

- `configs/post_gate5_preflight.yaml` is the machine-readable authority.
- `docs/post_gate5_compute_preflight.md` records the human-readable contract.
- `scripts/run_post_gate5_compute_preflight.py` is the synthetic-only runner.
- `tests/test_post_gate5_compute_preflight.py` verifies scope, accounting,
  controls, and fail-closed admission logic.
- RFIG-030 is reserved for source-bound compute margins after execution.

Consequence:

A PASS permits preparation of D010 only; it does not unlock research-data
fitting. A STOP must be committed with the D008 future-research discussion
record and cannot reduce, retry, or rescue the active P001 design.

D009 execution outcome:

- Source commit: `7aade60d61897781076730676aafca000ca52ad0` on clean `main`.
- Terminal status: **STOP - technical failure**.
- The first shared 1,024-row synthetic training projection completed.
- The Windows peak-working-set probe then raised
  `OSError: Unable to read Windows process memory counters`.
- Validation projection, projected-kernel geometry, Q01b/FQK heads, matched
  controls, and resource admission were not reached.
- Development, calibration, and final-test reads remained zero. No hardware,
  GPU, or Gate 6 job ran.
- This is not a QML result and not evidence that the workload exceeds the
  laptop. Resource admission is unavailable.
- P001-FR001 records a future-only proposal to validate a correctly typed
  Windows memory adapter against an independent OS reading before a later
  prospective preflight. It authorizes no active correction or retry.
- RFIG-029 records the failure/stop disposition. RFIG-030 remains absent
  because no resource-margin values exist.
- Failure evidence and P001-FR001 are anchored to reporting commit
  `89cb841d8b48fd6a7c0c60a6d95a651dbcfaf5ab`.

Consequence after STOP:

P001 research-data fitting remains locked. The failed D009 run will not be
silently retried. Any telemetry correction and preflight rerun require a new
prospective human decision; the scientific design, rows, folds, controls,
thresholds, and Gate 5 result remain unchanged.

### D010 accepted - telemetry-only D009 correction and one unchanged rerun

Date prepared: 2026-07-13
Date accepted: 2026-07-13
Status: **Completed: synthetic compute admission PASS; research-data execution unauthorized**
Authority: Human research lead instruction to perform the next process step

Decision:

D010 corrects only the process-memory interface that stopped D009. It permits
one telemetry-only validation and, only after a PASS, one rerun of the
unchanged D009 synthetic compute preflight. D009 attempt 1 and P001-FR001
remain immutable historical evidence.

Authorized correction:

- Declare the Windows PSAPI process handle, pointer, integer, and Boolean types
  explicitly and type `GlobalMemoryStatusEx` in the same manner.
- Compare the adapter's current working set with PowerShell `WorkingSet64` and
  require positive, internally consistent counters within the larger of
  64 MiB or 25%.
- Hash committed Git blobs rather than checkout-dependent file bytes.
- Preserve the D009 seed, synthetic rows, feature widths, q=8/two-layer
  circuit, heads, controls, landmarks, 477.5 work units, 25% margin, and every
  resource ceiling.

Execution and consequence:

The corrected source and tests must be committed before either accepted check
runs. The full preflight may run once only after the telemetry-only check
passes. A PASS permits preparation of D011 but does not unlock development
rows. A STOP is terminal for this authority and must be recorded under the
future-research firewall. Calibration/final-test access, hardware/GPU work,
Gate 5 reinterpretation, and Gate 6 remain prohibited.

D010 execution outcome:

- Freeze/source commit: `882bfd58d1154194b011dfc6fcef974cfe96ead3`.
- The telemetry-only check passed with a 49,152-byte adapter-versus-PowerShell
  difference against a 67,108,864-byte allowance.
- The one authorized unchanged attempt 2 completed both projected heads and
  every matched control with finite outputs.
- All five limits passed: 1.7849/250 CPU-core-hours, 0.0758/5 sequential
  wall-days, 1.1658/20 GiB new artifacts, 0.2014/24 GiB peak process memory,
  and 53.7426 GiB free disk after artifacts versus a 20 GiB minimum.
- Development, calibration, and final-test reads remained zero. No hardware,
  GPU, or Gate 6 job ran.
- RFIG-030 records the source-bound resource margins. RFIG-029 and the D009
  technical STOP remain unchanged.

Consequence after PASS:

D010 is closed and cannot be rerun. The result establishes synthetic compute
admission on the reference laptop only. It permits preparation of D011 but
does not authorize development-row fitting, claim QML performance, reinterpret
Gate 5, or open Gate 6.

### D011 accepted - corrected fold-shape admission and one P001 campaign

Date prepared: 2026-07-13
Date accepted: 2026-07-13
Initial status: **Accepted conditionally; largest-fold synthetic preflight required**
Current status: **Terminal pre-launch technical STOP; conditional campaign authority never activated**
Authority: Human research lead instruction to proceed with the next step

Finding before outcome access:

D010 remains valid under its frozen 1,024-training/256-validation benchmark,
but the D011 runner audit found that the real validation folds contain 6,500
or 9,750 rows and that each complete five-fold task predicts 39,000 held-out
rows. Treating D010 as final campaign-shape admission would therefore
understate validation projection and inference work.

Decision:

- Freeze a 1,024-training/9,750-validation synthetic bundle with q=8, two
  layers, both projected heads, A02, and every matched control.
- Project 1,220 largest-fold bundle units with 25% margin against the unchanged
  250 core-hour, five-day, 20 GiB artifact, 24 GiB memory, and 20 GiB minimum
  free-disk boundaries. Credit no smaller folds/qubits, sharing, or cache reuse.
- Open no development payload unless every source-bound preflight check passes.
- After a PASS, authorize exactly one source-bound, resumable P001 development
  campaign. Process interruption may resume valid checkpoints; a recorded
  technical failure or governed STOP cannot be silently retried.
- Preserve the D008 trial manifest, grouped folds, rows, transforms, endpoints,
  thresholds, controls, seed indices, sensitivity conditions, and claim limits.
- Keep all calibration/final-test payloads, hardware/GPU execution, Gate 5
  reinterpretation, and Gate 6 locked.

Prospective reporting freeze:

Q01b and FQK rank and stop independently. Q01b's fixed regime cells are the
five predeclared Gate 5 dimensions and must be complete in all five folds and
20 selected seeds. The paired seed-index bootstrap must place the upper 95%
Q01b-minus-control NRMSE bound below zero against A01, A02, and compressed C05
for a qualifying dequantization regime. FQK retains the frozen Brier, AUROC,
recall, and completeness conjunction. Exact statevector is primary;
finite-shot/noise results cannot affect selection or the promising label.

RFIG-031 will record corrected admission. RFIG-026 through RFIG-028 will report
reached outcomes, and RFIG-029 will be updated for any governed ineligibility,
terminal nonadvancement, technical failure, resource STOP, or scientific
negative. Every future-research suggestion requires a new protocol and cannot
alter or rescue P001. No D011 outcome was read when this decision was frozen.

Execution outcome:

The formal command
`uv run --frozen python scripts/run_post_gate5_fold_shape_preflight.py`
exited with code 1 during import. Direct-file Python execution could not
resolve `scripts.run_post_gate5_compute_preflight`, so the failure preceded
`verify_d011_authority`, source-hash verification, synthetic arrays, resource
admission, and all research-data access. Development, calibration, and
final-test reads are zero; no hardware/GPU or Gate 6 job ran.

D011 is closed as a terminal pre-launch technical `STOP`. It provides no QML
performance or laptop-capacity result. P001-FR002 records a package-safe
launcher/import and clean-source import-only smoke test for a later prospective
decision, without changing or retrying D011. RFIG-029 is updated cumulatively;
RFIG-031 and RFIG-026 through RFIG-028 remain absent because their governed
evidence was not reached.

### D011-C1 accepted - launcher correction and one unchanged preflight attempt

Date prepared: 2026-07-14
Date accepted: 2026-07-14
Initial status: **Accepted; import smoke test and one corrected preflight pending**
Current status: **Terminal authority-hash technical STOP; corrected fold-shaped workload not reached**
Authority: Human research lead accepted D011-C1 launcher correction and one unchanged preflight attempt

Finding before correction:

D011 did not reach its governed preflight. The direct-file launcher failed while
importing another script module, before authority verification, source-hash
verification, synthetic arrays, resource admission, development rows,
calibration rows, final-test rows, hardware/GPU work, or Gate 6.

Decision:

- Preserve the original D011 terminal STOP evidence as immutable.
- Correct only the launcher/import path by moving shared synthetic-preflight
  helpers into an importable `openqfuel` module.
- Require a clean-source import-only smoke test before running the preflight.
- Run at most one unchanged D011-shaped preflight attempt with the same 1,024
  training rows, 9,750 validation rows, q=8/two-layer benchmark, controls,
  1,220 bundle-unit accounting, 25% margin, and laptop ceilings.
- Open no development payload under D011-C1. A PASS can support a later human
  decision on campaign resumption only; it does not itself authorize campaign
  execution.
- If the smoke test or preflight stops, record the stop and future-only
  improvement without retrying or reducing the active design.

Reporting:

D011-C1 writes separate evidence at
`data/processed/reporting/post_gate5_d011_c1_fold_shape_preflight.json`.
RFIG-031 records reached corrected admission. RFIG-029 is updated only if a
governed D011-C1 stop occurs. RFIG-026 through RFIG-028 remain unauthorized
until a later decision permits and the campaign actually reaches development
evidence.

Execution outcome:

The import-only smoke test passed from clean source commit `ce65b1a`. The
formal preflight command then stopped during D011-C1 authority verification:
the pinned raw Git-blob hash for `configs/post_gate5_development_execution.yaml`
did not match the actual raw Git blob. Synthetic arrays, workload source-hash
verification, resource admission, development rows, calibration rows, final-test
rows, hardware/GPU work, and Gate 6 were not reached.

D011-C1 is closed as a terminal technical `STOP`. P001-FR003 records that any
successor correction must verify raw dependency hashes before acceptance while
leaving the D011 scientific workload unchanged. RFIG-029 is updated
cumulatively. RFIG-031 remains absent because corrected admission was not
reached.

### D011-C2 accepted - raw-blob hash correction and one unchanged preflight attempt

Date prepared: 2026-07-14
Date accepted: 2026-07-14
Initial status: **Accepted; hash smoke test and one corrected preflight pending**
Current status: **Completed with synthetic corrected fold-shape admission PASS; development campaign still requires separate human decision**
Authority: Human research lead supported D011-C2 after review of the D011-C1 hash mismatch, docs, and evidence

Finding before correction:

D011-C1 fixed the launcher import and passed the import smoke test, but the
formal command stopped while checking C1's accepted dependency hashes. The
actual raw Git blobs for the D011 config, D011 STOP evidence, and D011 launcher
script were stable, but their C1-pinned hashes had been computed through a
non-raw text path. This was a governance-metadata failure before the synthetic
workload, not QML or resource-admission evidence.

Decision:

- Preserve D011 and D011-C1 STOP evidence as immutable.
- Replace only the prospective correction authority with independently verified
  raw Git-blob SHA-256 dependency hashes.
- Require a clean-source hash-consistency smoke test and direct-file import
  smoke test before running the preflight.
- Run at most one unchanged D011-shaped preflight attempt with the same 1,024
  training rows, 9,750 validation rows, q=8/two-layer benchmark, controls,
  1,220 bundle-unit accounting, 25% margin, and laptop ceilings.
- Open no development payload under D011-C2. A PASS can support a later human
  decision on campaign resumption only; it does not itself authorize campaign
  execution.
- If the smoke tests or preflight stop, record the stop and future-only
  improvement without retrying or reducing the active design.

Reporting:

D011-C2 writes separate evidence at
`data/processed/reporting/post_gate5_d011_c2_fold_shape_preflight.json`.
RFIG-031 records reached corrected admission. RFIG-029 is updated only if a
governed D011-C2 stop occurs. RFIG-026 through RFIG-028 remain unauthorized
until a later decision permits and the campaign actually reaches development
evidence.

Execution outcome:

The hash-consistency smoke test and direct-file import smoke test both passed
from clean source commit `06381d1`. The single unchanged D011-C2 preflight then
passed all five unchanged laptop boundaries: 4.7259 of 250 CPU-core-hours,
0.2002 of five wall-days, 2.9785 of 20 GiB new artifacts, 0.6339 of 24 GiB peak
process memory, and 45.3606 GiB free disk after artifacts against the 20 GiB
minimum. Development, calibration, and final-test reads were zero; hardware,
GPU, and Gate 6 runs were zero.

D011-C2 is closed to rerun. This PASS is corrected synthetic compute-admission
evidence only. It does not authorize development execution by itself; the next
human decision is whether to resume the single D011 development-only campaign.

### D011-R1 accepted - resume the single development-only campaign

Date prepared: 2026-07-14
Date accepted: 2026-07-14
Initial status: **Accepted; campaign execution pending**
Outcome status: **Completed; valid development-only exploratory negatives**
Authority: Human research lead instructed the project to resume the D011 development-only campaign after D011-C2 PASS

Decision:

- Resume exactly one source-bound D011 development-only P001 campaign.
- Use only the frozen D011 Q01b projected-kernel and FQK feasibility-only
  protocol, folds, rows, controls, endpoint orderings, selected-seed rules,
  sensitivity rules, and claim boundaries.
- Treat the D011-C2 PASS as corrected fold-shape compute admission for campaign
  entry while preserving D011 and D011-C1 STOP evidence.
- Open development rows only; keep calibration rows, final-test rows,
  hardware/GPU execution, Gate 5 reinterpretation, and Gate 6 locked.
- Stop or continue only under the frozen D011 failure and eligibility policy.
  Every technical failure, resource stop, terminal nonadvancement, or negative
  scientific result requires future-only discussion and the required figures.

Expected reporting:

RFIG-026 through RFIG-028 report reached development evidence. RFIG-029 updates
for any governed stop, terminal nonadvancement, or valid negative outcome.
RFIG-031 remains the corrected synthetic compute-admission evidence.

Result:

- The campaign completed from source commit `083d777` with 39,000 development
  rows read and zero calibration/final-test rows, hardware/GPU jobs, or Gate 6
  runs.
- Q01b completed all five folds and 20 selected seeds but was not promising:
  mean pooled OOF NRMSE was 0.6612 versus C06 at 0.0068328, relative gap was
  95.769x, and qualified dequantization regimes were zero.
- FQK completed all five folds and 20 selected seeds but was not promising:
  mean AUROC was 0.7436, mean Brier was 0.1561, and recall at 0.5 was 0.1089
  versus C02-T02 at 0.9134, 0.1062, and 0.3233.
- P001-FR004 and P001-FR005 record future-only improvements. These suggestions
  require a new protocol and do not alter, rescue, or extend the active P001
  experiment.

### D012 opened - future protocol discussion from D011-R1 negatives

Date prepared: 2026-07-14
Date accepted: 2026-07-14
Status: **Opened; discussion-only**
Authority: Human research lead instructed the project to open a future protocol discussion while keeping Gate 6 unauthorized

Decision:

- Open D012 only as interpretation and future-protocol discussion from the
  completed D011-R1 negative results.
- Do not authorize implementation, new experiments, refits, reranking, retries,
  calibration/final-test reads, hardware/GPU execution, Gate 5 reinterpretation,
  quantum-advantage claims, or Gate 6.
- Preserve D011-R1 as valid development-only exploratory negative evidence.
- Reserve D013 as the next required prospective decision before any successor
  protocol can be implemented or run.

Discussion candidates:

- D012-A: task-informed local-observable projected kernel, motivated by Q01b
  NRMSE failure and zero qualified dequantization regimes.
- D012-B: class-sensitive feasibility quantum kernel, motivated by FQK
  AUROC/Brier/recall underperformance and high false-negative rate.
- D012-C: classical-first residual and safety-filter hardening, recommended
  before any new QML experiment because both QML tracks were weaker than strong
  classical controls.

Reporting:

RFIG-026 through RFIG-028 remain the D011-R1 reached evidence. RFIG-029 remains
the future-research firewall figure. No new figure is required for D012 unless
a later D013 protocol is prospectively prepared.

### D013-C accepted - classical-first planning before QML invention

Date prepared: 2026-07-14
Date accepted: 2026-07-14
Status: **Accepted; planning-only; no experiment authorized**
Authority: Human research lead instructed the assistant to choose and commit the recommended next decision before the QML invention phase

Decision:

- Select D012-C as the next path because it is the scientifically safest
  response to D011-R1: both tested QML tracks were weaker than strong classical
  controls.
- Open planning for stronger classical residual-cost and safety-filter
  baselines before inventing a new QML method.
- Record the long-term invention goal: after the experimental program is
  complete, use labeled evidence to design a new QML method that can beat the
  strongest documented NASA-relevant and repository baselines under fair
  locked-split tests.
- Do not claim NASA used a specific QML method unless a cited public source
  identifies one.
- Require every completed result, technical stop, and negative result to label
  its useful signal for later QML invention and its prohibited post-outcome
  rescue use.

Boundary:

D013-C authorizes no implementation, new experiment, refit, rerank, retry,
calibration/final-test read, hardware/GPU execution, Gate 5 reinterpretation,
quantum-advantage claim, or Gate 6. D014 is required before any executable
successor work.

### D014-C accepted - classical-first freeze proposal

Date prepared: 2026-07-14
Date accepted: 2026-07-14
Status: **Accepted; freeze proposal only; no execution authorized**
Authority: Assistant-selected next step under delegated planning authority

Decision:

- Freeze the next classical-first proposal before any implementation or fitting.
- Lock `CRES` residual-cost hardening with C06-T17, A02 exact classical RBF,
  random-feature RBF residual, compressed MLP residual, and ridge residual
  controls.
- Lock `CSAFE` safety-filter hardening with C02-T02, calibrated logistic,
  class-weighted tree ensemble, conformal or quantile threshold, and A02
  feasibility controls.
- Require conservative clean-source compute admission before any future
  development-data fitting.
- Reserve RFIG-032 through RFIG-035 for the freeze map, future compute
  admission, residual-cost results, and safety-filter results if those stages
  are later accepted and reached.

Boundary:

D014-C authorizes no implementation, synthetic validation, development-data
fitting, refit, rerank, retry, calibration/final-test read, hardware/GPU
execution, Gate 5 reinterpretation, QML invention claim, quantum-advantage
claim, or Gate 6. D015 is required before implementation or synthetic
validation.

### D015-C accepted - implementation and synthetic validation only

Date prepared: 2026-07-14
Date accepted: 2026-07-14
Status: **Accepted; implementation and synthetic validation only**
Authority: Assistant-selected next step after D014-C

Decision:

- Authorize implementation scaffolding for CRES residual-cost hardening and
  CSAFE safety-filter hardening.
- Authorize synthetic-array validation of preprocessing isolation, residual
  equations, safety-threshold isolation, invention-readiness labels, and
  fail-closed split/Gate 6 guards.
- Generate RFIG-032 from the D014-C freeze proposal.

Boundary:

D015-C authorizes no development-data fitting, calibration/final-test read,
refit, rerank, retry, hardware/GPU execution, Gate 5 reinterpretation, QML
invention claim, quantum-advantage claim, or Gate 6. D016 is required before
clean-source synthetic compute admission, and a later decision is required
before any development-data fitting.

Outcome:

- Implemented synthetic-only CRES/CSAFE scaffolds in
  `src/openqfuel/post_gate5_classical.py`.
- Added tests for D015 scope guards, residual target equations, residual-cost
  metrics, training-only safety-threshold selection, held-out safety metrics,
  invalid-input rejection, and invention-readiness labels.
- No development, calibration, final-test, hardware/GPU, Gate 5
  reinterpretation, QML invention claim, or Gate 6 path was opened.

### D016-C accepted - clean-source synthetic compute preflight

Date prepared: 2026-07-14
Date accepted: 2026-07-14
Status: **Completed; synthetic compute admission PASS**
Authority: Assistant-selected next step after D015-C synthetic scaffolds

Decision:

- Authorize exactly one clean-source synthetic compute-admission preflight for
  the D014-C CRES/CSAFE classical-first scaffolds.
- Benchmark the largest-fold synthetic CRES/CSAFE workload and conservatively
  project it across five folds and 20 seeds with 25% margin.
- Generate RFIG-033 only if terminal D016-C evidence is reached.
- Do not use cache, early stopping, smaller folds, or post-outcome reduction as
  admission credit.

Boundary:

D016-C authorizes no development-data fitting, calibration/final-test read,
refit, rerank, retry, hardware/GPU execution, Gate 5 reinterpretation, QML
invention claim, quantum-advantage claim, or Gate 6. A PASS permits only
preparation of D017; it does not itself open development rows.

Outcome:

- The single authorized preflight ran from clean source commit
  `45409a86a5e450d72ba7f043715956fa5b916974`.
- Admission status: `PASS`.
- Projected resource use after 25% margin: 0.0179/250 CPU-core-hours,
  0.000788/5 wall-days, 1.2207/20 GiB artifacts, 0.1713/24 GiB peak working
  set, 46.5275 GiB free disk after artifacts against the 20 GiB minimum, and
  zero GPU-hours.
- Integrity counters: 10,774 synthetic rows used; zero development,
  calibration, final-test, hardware, GPU, and Gate 6 reads/runs.
- RFIG-033 records the compute-admission margins.
- Development-data fitting remains unauthorized and requires D017.

### D016-C1 accepted - A02 exact-RBF compute correction

Date prepared: 2026-07-14
Date accepted: 2026-07-14
Status: **Completed; A02 exact-RBF synthetic compute admission PASS**
Authority: Assistant-selected correction after pre-D017 audit

Decision:

- Record that D016-C passed but did not benchmark the D014-C required A02 exact
  classical RBF control.
- Authorize exactly one clean-source synthetic preflight for A02 exact RBF
  residual-cost and feasibility heads.
- Use the same 1,024-training/9,750-validation largest-fold shape and project
  five folds and 20 seeds with 25% margin.
- Generate RFIG-036 if terminal evidence is reached.

Boundary:

D016-C1 authorizes no development-data fitting, calibration/final-test read,
refit, rerank, retry, hardware/GPU execution, Gate 5 reinterpretation, QML
invention claim, quantum-advantage claim, or Gate 6. D017 cannot proceed until
D016-C1 is terminal.

Outcome:

- The single authorized A02 preflight ran from clean source commit
  `a40a6687b7c68a04f355ee40e0ff6144482eaf6c`.
- Admission status: `PASS`.
- Projected resource use after 25% margin: 0.0109/250 CPU-core-hours,
  0.000438/5 wall-days, 1.2207/20 GiB artifacts, 0.2679/24 GiB peak working
  set, 46.5217 GiB free disk after artifacts against the 20 GiB minimum, and
  zero GPU-hours.
- Integrity counters: 10,774 synthetic rows used; zero development,
  calibration, final-test, hardware, GPU, and Gate 6 reads/runs.
- RFIG-036 records the A02 exact-RBF compute-correction margins.
- Development-data fitting remains unauthorized and requires D017.

### D017-C accepted - development-only classical-first campaign

Date prepared: 2026-07-14
Date accepted: 2026-07-14
Status: **Completed; development-only evidence requires D018 interpretation**
Authority: Assistant-selected next step after D016-C and D016-C1 PASS

Decision:

- Authorize exactly one source-bound CRES/CSAFE development-only campaign.
- Use the original grouped development split, five folds, 20 seed replicates,
  1,024 fold-local training rows, and fold-local preprocessing/PCA.
- Fit only the frozen classical-first residual-cost and safety-filter controls.
- Generate RFIG-034 and RFIG-035 only if terminal D017-C evidence is reached.

Boundary:

D017-C authorizes no calibration/final-test read, refit, rerank, retry,
hardware/GPU execution, Gate 5 reinterpretation, QML invention claim,
quantum-advantage claim, mission-loop work, or Gate 6. D018 must interpret any
terminal D017-C result before another successor step.

Outcome:

- Completed from clean source commit
  `419844a690d625502718e00b3e4dcafc6d99286c`.
- Read 39,000 development rows and zero calibration/final-test rows.
- Hardware jobs, GPU hours, and Gate 6 runs remained zero.
- CRES best mean residual NRMSE: `ridge_residual`, 0.8265.
- CSAFE best mean Brier: `class_weighted_tree`, 0.1311, but mean recall was
  only 0.0139.
- RFIG-034 records residual-cost results; RFIG-035 records safety-filter
  results.
- D018 must interpret the result before any claim, successor experiment,
  calibration/final-test access, hardware/GPU work, mission-loop work, or Gate 6.

### D018-C completed - D017 development-only interpretation

Date prepared: 2026-07-14
Date accepted: 2026-07-14
Status: **Completed; official status NO_ADVANCE**
Authority: Assistant-selected interpretation step after D017-C

Decision:

- Interpret D017-C as development-only evidence that does not advance to
  calibration, final-test, mission-loop, hardware, or Gate 6.
- Treat CRES as a useful baseline and future QML target, not a qualifying
  result.
- Treat CSAFE as failed safety utility under the frozen selection rule because
  the best-Brier model has mean recall 0.0139.
- Treat the logistic head's higher recall as future-only signal for a later
  recall-first safety objective, not an active rescue selection.
- Generate RFIG-037 for the interpretation boundary.

Boundary:

D018-C authorizes no experiment, development refit, rerank, retry,
calibration/final-test read, hardware/GPU execution, mission-loop work, Gate 5
reinterpretation, QML invention claim, quantum-advantage claim, or Gate 6.

Correction note:

- The first D017-C launch stopped before development data were opened because
  the runner attempted to hash `source_binding.output_root` as if it were a
  committed source file.
- Development rows read, calibration rows read, final-test rows read, hardware
  jobs, GPU hours, and Gate 6 runs were all zero.
- Corrective improvement: source bindings must distinguish committed source
  inputs from generated output destinations before a clean-source campaign run.
  The corrected runner excludes `output_root` from committed blob hashing and
  keeps all scientific workload settings unchanged.

### D019-C opened - safety-objective redesign discussion

Date prepared: 2026-07-14
Date accepted: 2026-07-14
Status: **Opened; discussion-only; no experiment authorized**
Authority: Assistant-selected next step after D018-C `NO_ADVANCE`

Decision:

- Open a future-only safety-objective redesign discussion from the D018-C CSAFE
  failure.
- Record that the frozen D017 best-Brier model, `class_weighted_tree`, had mean
  Brier 0.1311 but mean recall only 0.0139.
- Record that the `calibrated_logistic` head had worse mean Brier 0.1422 but
  much higher mean recall 0.8043, making it a future-only signal for a
  recall-first safety objective.
- Require any executable successor to prospectively freeze recall or
  false-negative-cost priority, secondary Brier/calibration diagnostics,
  threshold-selection rules, matched controls, compute admission, stop rules,
  and minimum safety utility.
- Generate RFIG-038 for the redesign boundary.

Boundary:

D019-C authorizes no implementation, experiment, development fitting, refit,
rerank, retry, threshold change, calibration/final-test read, hardware/GPU
execution, mission-loop work, Gate 5 reinterpretation, QML invention claim,
quantum-advantage claim, or Gate 6. It does not rescue or reinterpret D017.

### D020-C accepted - recall-first safety freeze proposal

Date prepared: 2026-07-14
Date accepted: 2026-07-14
Status: **Accepted; freeze proposal only; no implementation authorized**
Authority: Assistant-selected next step after D019-C

Decision:

- Freeze the future CSAFE-RF safety-filter direction as recall-first or
  false-negative-risk-first.
- Retain Brier score, calibration, precision, false-positive burden, artifact
  size, and laptop-fit compute as secondary diagnostics.
- Freeze future model selection order as mean unsafe-case recall, lower
  false-negative rate, lower Brier score, then simpler model family.
- Freeze threshold discipline: any future threshold must be selected inside
  authorized training folds only, and D017/D018 held-out outcomes cannot tune an
  active threshold.
- Require C02-T02, calibrated logistic, class-weighted tree, A02 exact
  classical RBF, and any later QML candidate only under a separate prospective
  freeze.
- Generate RFIG-039 for the freeze boundary.

Boundary:

D020-C authorizes no implementation, experiment, development fitting,
threshold application, refit, rerank, retry, calibration/final-test read,
hardware/GPU execution, mission-loop work, Gate 5 reinterpretation, QML
invention claim, quantum-advantage claim, or Gate 6. D021 is required before
any synthetic implementation or validation.

### D021-C completed - recall-first synthetic validation

Date prepared: 2026-07-14
Date accepted: 2026-07-14
Status: **Completed; synthetic validation PASS**
Authority: Assistant-selected next step after D020-C

Decision:

- Implement D021 scope guards for implementation and synthetic validation only.
- Add CSAFE-RF recall-first candidate scoring.
- Select synthetic candidates by recall, false-negative rate, Brier score, and
  model complexity.
- Validate the rule on synthetic arrays only.
- Generate RFIG-040 for the synthetic-validation evidence.

Outcome:

- Selected `synthetic_recall_first_logistic`.
- Selected recall: 0.75.
- Selected false-negative rate: 0.25.
- Selected Brier score: 0.08064.
- The lower-Brier synthetic tree fixture was not selected because its recall
  was only 0.25.
- Development rows, calibration rows, final-test rows, hardware jobs, GPU
  hours, and Gate 6 runs were all zero.

Boundary:

D021-C authorizes no development-data fitting, threshold application to real
data, calibration/final-test read, hardware/GPU execution, mission-loop work,
Gate 5 reinterpretation, QML invention claim, quantum-advantage claim, or Gate
6. D022 clean-source synthetic compute preflight is required before any
development-data decision.

### D022-C accepted - recall-first clean-source synthetic preflight

Date prepared: 2026-07-14
Date accepted: 2026-07-14
Status: **Accepted; one clean-source synthetic preflight authorized**
Authority: Assistant-selected next step after D021-C

Decision:

- Authorize exactly one clean-source synthetic compute preflight for CSAFE-RF.
- Benchmark synthetic training-threshold selection, synthetic held-out
  recall-first scoring, and selection by recall, false-negative rate, Brier
  score, and model complexity.
- Require clean `main` source before execution.
- Generate RFIG-041 only if terminal preflight evidence is reached.

Boundary:

D022-C authorizes no development-data fitting, threshold application to real
data, calibration/final-test read, refit, rerank, retry, hardware/GPU
execution, mission-loop work, Gate 5 reinterpretation, QML invention claim,
quantum-advantage claim, or Gate 6. If the preflight stops, the stop is
terminal unless a later prospective correction is accepted.
