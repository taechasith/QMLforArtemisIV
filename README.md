# QMLforArtemisIV

An open, flight-ephemeris-calibrated benchmark of classical and quantum machine
learning for propellant-efficient, crew-constrained cislunar trajectory
correction planning.

## Status

Decision Gate 1 was accepted on 2026-07-10, Gate 2 was accepted on 2026-07-11,
and Gate 3 simulator credibility was accepted on 2026-07-12 with documented
source and execution-order limitations. All 67 Gate 3 checks that could be
evaluated passed. RTC3 was not evaluated because it occurred at
2026-04-10T18:53:00Z, after the qualified OEM was created at
2026-04-10T03:22:19Z; later rows in that OEM are pre-RTC3 predictions, not
post-RTC3 historical evidence. The machine status `not_eligible` therefore
means **not tested with eligible evidence; neither pass nor fail**. Gate 3
acceptance does not claim that RTC3 was validated. Gate 4 and bounded-literature
Deviation D002 were accepted on 2026-07-12. A subsequent pre-D003 run generated
7,000 F0 rows, but the conformance audit found every row invalid; those rows
are excluded from all model and benchmark use and retained only as failed-run
evidence. D003 repaired the scenario generator and qualified every unlocked
development/calibration payload: all 42 groups and 45,500 F0/F1/F2 rows pass
strict audit. The F1 and F2 audits retain no-reference decision sets as
development limitations; they do not retune candidates after seeing those
rates. D004 then hardened Gate 5 before any research model fit by adding
source-vetting, QML diagnostic, matched-control, regime-reporting, and
figure-record requirements. The D005 Gate 5 runner, accepted by the human
research lead on 2026-07-12 from candidate commit `80ae35d`, enforces
fold-local preprocessing/PCA, deterministic whole-group CV, nested matched
samples, explicit physical residual baselines, and fail-closed split access.
D006 now proposes a pre-fit campaign repair after an audit found that the
original cycled control dimensions were not exact matches for many QML trials.
All 30 frozen A01 and compressed-C05 trials now repeat at 4/6/8 dimensions,
with independently advanced strong controls and exact same-index QML controls;
no hyperparameter trial or candidate family would be added. Because D006 is a
material post-acceptance refinement, fitting remains paused pending explicit
human acceptance. No research model or scientific benchmark result exists yet.
Both final-test splits remain locked and require a separate unlock commit.

The D006 candidate preflight again verifies 39,000 development rows and 7,800
complete decision sets with zero calibration/final-test reads. Its exact-lock
validation passes 127 tests and 667 subtests; Ruff is clean. Recorded batched
state/feature/kernel outputs are within `2.67e-15` of the scalar path and reduce
the measured 8-qubit/3-layer batch cost by roughly 7.5-19.4x depending on
operation and rung.
The campaign remains fail-closed until D006 is explicitly accepted, after
which a bounded checkpoint using the frozen C04 trial plus the 1,024-row QML
and matched-control views must pass the 25%-margin compute and storage
projection before full scale-up. It uses end-to-end task timing, keeps
preselection checkpoint scores outside ranking unless independently advanced,
rejects every development output beneath the final-payload root, and preserves
recoverable coordinator failures without freezing a stale scale-up decision.
Final reporting revalidates evidence digests, task signatures, source commit,
selection/control identity, development scope, and zero locked-split reads.
D004 feature-scale, entanglement, random-feature, parameter-count, sample/rung,
and no-reference checks are mandatory report-only diagnostics; a technical
trigger pass still requires the human lead's separate interpretation and
decision. Invalid or incomplete evidence is reported as `UNAVAILABLE` and
requires repair; it is never relabeled as a negative QML result.

Canonical repository: https://github.com/taechasith/QMLforArtemisIV

The recommended mission design is:

- Artemis II flight-derived ephemeris for calibration and held-out validation.
- An Artemis IV-relevant Orion cislunar scenario for future-use simulation.
- Post-injection trajectory-correction planning as the optimization boundary.
- Advisory ground-planning research, not direct flight control.

## Scientific position

This project does not assume that a quantum model will outperform a classical
model. A negative result is an acceptable outcome. Any QML model must be tested
against strong, tuned classical baselines under identical data splits,
optimization budgets, random scenarios, safety constraints, and reporting
rules.

The phrase quantum advantage is prohibited unless an end-to-end hardware
experiment demonstrates a practical advantage after data encoding, sampling,
error mitigation, communication, and classical-compute costs are included.

## Governance

The assistant research partner performs the technical work and produces a
recommendation at every decision gate. The human research lead accepts,
rejects, or requests revision. Frozen protocol decisions may be changed only
through a dated deviation record.

## Repository map

- research_protocol.md: master preregistration and analysis plan.
- literature/review_protocol.md: reproducible evidence-review method.
- literature/evidence_matrix.csv: seed evidence map.
- literature/search_log.csv and screening_log.csv: Gate 4 search audit trail.
- literature/extraction_matrix.csv: curated primary evidence extraction.
- data/source_registry.csv: public-source provenance and download status.
- data/artemis2_event_registry.csv: planned-versus-flown mission events.
- data/processed/artemis2/: reproducible OEM audit and weak-baseline outputs.
- configs/constraints.yaml: machine-readable mission assumptions and gates.
- configs/uncertainty_model.yaml: public 3-sigma inputs and sensitivity strata.
- configs/simulator_acceptance.yaml: frozen verification and validation tests.
- configs/dynamics.yaml: frozen Gate 3 force and numerical model.
- configs/compute_budget.yaml: fixed experiment and resource ceilings.
- configs/phase1_benchmark.yaml: accepted Gate 4 scenario, model, tuning, and analysis freeze.
- configs/scenario_generation.yaml: D003 scenario-generation implementation freeze.
- docs/computational_methodology.md: published reference hardware and
  hardware-aware execution method.
- docs/gate2_data_numeric_freeze.md: Gate 2 evidence and recommendation.
- docs/gate4_phase1_freeze.md: accepted Gate 4 decision package and lock audit.
- docs/model_registry.md and docs/phase1_analysis_plan.md: frozen comparison and statistics.
- docs/research_figure_policy.md: required visual, provenance, and claim-boundary workflow.
- docs/research_execution_map.md: work ownership and future decision gates.
- docs/decision_log.md: acceptance and deviation history.
- data/processed/reporting/gate5_literature_hardening_matrix.csv: D004 source-to-control matrix for RFIG-019.
- data/processed/reporting/gate5_cv_fold_manifest.csv: label-agnostic D005 whole-group CV assignment for RFIG-020.
- data/processed/reporting/gate5_preflight_audit.json: development-only Gate 5 data and lock audit.
- data/processed/reporting/gate5_initial_execution_plan.csv: all 450 proposed D006 first-stage tasks (270 candidates and 180 non-winning matched-control views), blocked pending acceptance.
- scripts/run_gate5_campaign.py: immutable, resumable successive-halving and 20-seed Gate 5 scheduler.
- data/processed/reporting/gate5_statevector_batch_benchmark.json: locked-environment synthetic equivalence/runtime record for D006, bound to QML-source, benchmark-script, and lockfile hashes.
- src/openqfuel/gate5_reporting.py: source-bound 20-seed, five-fold, matched-control trigger evaluator, D004 diagnostic auditor, and negative-result-safe report exporter.
- scripts/make_gate5_result_figures.py: predeclared RFIG-021 through RFIG-023 development-result figures.
- scripts/fetch_public_data.py: immutable-source downloader.
- scripts/extract_artemis2_oem.py: safe nested-archive extraction and hashing.
- scripts/audit_artemis2_oem.py: OEM qualification and revision audit.
- scripts/evaluate_two_body_baseline.py: weak physics baseline.
- tests/: repository and source-registry checks.

## Reproducibility rule

Raw public data are never silently edited. Derived data must be generated by
versioned scripts. Every result must be reproducible from a configuration file,
software environment, random seed set, and source manifest.

## License

Code is released under Apache-2.0. Source data retain the terms and attribution
requirements of their original providers. Research text and figures will
receive a separate open-content license at the publication checkpoint.
