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
D006 was accepted by the human research lead on 2026-07-12 from candidate
commit `3ac9403`. It repairs the pre-fit campaign after an audit found that the
original cycled control dimensions were not exact matches for many QML trials.
All 30 frozen A01 and compressed-C05 trials now repeat at 4/6/8 dimensions,
with independently advanced strong controls and exact same-index QML controls;
no hyperparameter trial or candidate family is added. Acceptance authorizes
development-only research fitting under the frozen contract. The authorization
was published at commit `6e5a620`, and the campaign completed on 2026-07-13:
671 tuning tasks and 200 exact seed reruns are terminally complete, with zero
task failures, zero calibration reads, and zero final-test reads. Calibration
and both final-test splits remain locked.

The accepted D006 preflight verifies 39,000 development rows and 7,800
complete decision sets with zero calibration/final-test reads. Its exact-lock
validation passes 132 tests and 667 subtests; Ruff is clean. Recorded batched
state/feature/kernel outputs are within `2.67e-15` of the scalar path and reduce
the measured 8-qubit/3-layer batch cost by roughly 7.5-19.4x depending on
operation and rung.
The bounded qualification passed before scale-up: its 25%-margin ceiling case
projected 328.84 core-hours, 13.15 wall-days with two classical workers, and
0.081 GiB storage. The campaign used end-to-end task timing, kept
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

Q01-T17 became the only eligible QML finalist. Q02 and Q03 stopped at the
128-row retention gate: 8/30 and 4/30 tasks, respectively, were eligible, below
the frozen retain count of 15. All 300 associated tuning folds and optimizer
diagnostics exist; neither family was refit or promoted after outcomes became
visible.

The first derived report is preserved as `UNAVAILABLE`, because the frozen
reporter calls those registered early stops `incomplete_with_terminal_failures`
despite the zero-failure audit and also demands nonexistent later-rung/seed
diagnostics. The human research lead accepted D007 on 2026-07-13 from candidate
commit `7a726c8917a85f24313208eb18c33e1ccb5f703e`. This reporting-only correction
recognizes the exact
source-bound terminal-nonadvancement case, evaluates D004 completeness over
authorized/reached stages, and leaves every model score, ranking, threshold,
seed, and campaign digest unchanged. D007 authorized only the report and
RFIG-021 through RFIG-023 for regeneration; both reporting entry points verify
the accepted candidate before writing. The official D007 package now
validates cleanly and preserves `6e5a620` as the campaign source while separately
recording the accepted D007 candidate, the clean reporting-source commit, and
reporter/generator hashes. Publication also byte-checks the reporter and every
immutable D006 campaign evidence file against the accepted candidate's Git
snapshot. A digest-bound reporting-package manifest is written last, and the
figure generator refuses incomplete, stale, or provenance-inconsistent inputs.
The official technical trigger is `FAIL`: Q01's mean NRMSE is 0.6466 versus
0.00874 for C06, the relative gap is 72.99, and no regime qualifies. RFIG-021
through RFIG-023 preserve the reached-rung, 20-seed, and regime evidence. This
negative result applies only to the preregistered development benchmark; it
does not establish that QML can never work. The human research lead accepted
this technical `FAIL` as the official Gate 5 result on 2026-07-13. Gate 5 is
therefore closed, and the proposed new algorithm is not authorized under the
frozen trigger. This decision does not authorize refitting, new algorithm work,
calibration or final-test access, or Gate 6. RFIG-001 records the accepted gate
state; RFIG-021 through RFIG-023 remain the unchanged scientific evidence.

Post-Gate-5 exploratory protocol P001 is now open as a prospective planning
branch only. The only near-term QML designs allowed under that branch are Q01b
projected quantum kernel and FQK feasibility-only quantum kernel, both tied to
the original grouped-development pipeline and matched-control discipline.
Quantum reinforcement learning, dynamic circuits, quantum annealing, QAOA, new
variational QML architectures, larger-qubit circuits, and hardware execution
remain appendix or future-work topics. P001 does not authorize an experiment,
calibration/final-test access, or Gate 6. RFIG-024 records this boundary.

D008 is accepted as the implementation freeze for P001. It fixes 30 paired
projected-kernel configurations, shared Q01b/FQK projections, grouped
development folds, matched controls, compute ceilings for the reference
laptop, staged reporting figures, and a mandatory future-research record for
every failure or stop. Those records may explain what a later study could
improve, but cannot alter or retry the active pipeline. D008 authorizes
implementation and synthetic validation only; research-data fitting still
requires a separate clean-source execution decision. RFIG-025 records the
accepted pre-execution freeze.

The D008 projected-kernel primitives and synthetic validation guards are now
implemented. Synthetic tests cover Pauli X/Y/Z one-RDM projection, the
fold-local median-distance bandwidth, deterministic Nystrom landmark sharing,
projected-kernel regressors/classifiers, PSD clipping, locked-scope guards,
and the future-research firewall. No development-row fit, calibration/final
read, hardware run, or Gate 6 work has been authorized.

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
- docs/post_gate5_exploratory_protocol.md: prospective exploratory Q01b/FQK protocol opened after the accepted Gate 5 negative result.
- docs/post_gate5_implementation_freeze.md: D008 accepted implementation freeze defining exact Q01b/FQK methods, controls, stopping, compute, and failure-discussion rules.
- docs/decision_log.md: acceptance and deviation history.
- data/processed/reporting/gate5_literature_hardening_matrix.csv: D004 source-to-control matrix for RFIG-019.
- data/processed/reporting/post_gate5_exploratory_protocol_matrix.csv: P001 near-term versus appendix/future QML boundary for RFIG-024.
- data/processed/reporting/post_gate5_exploratory_trial_manifest.csv: 30 balanced paired projected-kernel configurations frozen but not run.
- data/processed/reporting/post_gate5_future_research_discussion.csv: schema-locked register for evidence-based future-work suggestions after failures or stops.
- data/processed/reporting/gate5_cv_fold_manifest.csv: label-agnostic D005 whole-group CV assignment for RFIG-020.
- data/processed/reporting/gate5_preflight_audit.json: development-only Gate 5 data and lock audit.
- data/processed/reporting/gate5_initial_execution_plan.csv: all 450 accepted D006 first-stage tasks (270 candidates and 180 non-winning matched-control views), ready under the clean-source fit guard.
- scripts/run_gate5_campaign.py: immutable, resumable successive-halving and 20-seed Gate 5 scheduler.
- experiments/: source-bound D006 campaign tables plus the official D007 `FAIL` report package, diagnostics, and model registry.
- data/processed/reporting/gate5_statevector_batch_benchmark.json: locked-environment synthetic equivalence/runtime record for D006, bound to QML-source, benchmark-script, and lockfile hashes.
- src/openqfuel/gate5_reporting.py: source-bound 20-seed, five-fold, matched-control trigger evaluator, D004 diagnostic auditor, and negative-result-safe report exporter.
- scripts/make_gate5_result_figures.py: predeclared RFIG-021 through RFIG-023 development-result figures.
- scripts/make_post_gate5_exploratory_figures.py: RFIG-024 protocol-boundary diagram generator.
- scripts/make_post_gate5_implementation_figure.py: RFIG-025 D008 implementation-freeze and future-research-firewall diagram generator.
- src/openqfuel/post_gate5.py: D008 synthetic-only scope guard and future-research firewall validator.
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
