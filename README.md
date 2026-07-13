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

D009 was accepted for one clean-source synthetic compute preflight. The run
stopped after the first shared 1,024-row projection because the Windows
peak-working-set probe returned no valid process counters. Neither projected
head, any matched control, nor resource admission completed. This is a
telemetry-interface failure, not a QML result or evidence that the workload
exceeds the laptop. P001 fitting remains locked, the run will not be retried
without a new prospective decision, and RFIG-029 records the stop plus its
future-research firewall. RFIG-030 remains absent because no resource-margin
result exists.

D010 was accepted as a prospective telemetry-only correction. It replaces
the untyped Windows process-memory call with explicitly typed operating-system
interfaces, requires agreement with an independent PowerShell working-set
reading, and binds provenance to committed Git blobs. D009 remains an
immutable technical `STOP`. D010 permits one telemetry-only check followed by
one unchanged synthetic preflight attempt; it changes no seed, row count,
circuit, control, projection, margin, or resource ceiling. Development,
calibration, final-test, hardware/GPU, and Gate 6 work remain locked. A PASS
would permit preparation of D011 only, not research-data fitting.

The required telemetry-only check passed with a 49,152-byte adapter-versus-
PowerShell difference against a 64 MiB allowance. The single unchanged D010
attempt 2 then completed every projected head and matched control and passed
all five compute limits. With the frozen 477.5-work-unit projection and 25%
margin, it estimates 1.785 CPU-core-hours, 0.0758 sequential wall-days,
1.166 GiB of new artifacts, 0.201 GiB peak process memory, and 53.743 GiB free
disk after artifacts. Development, calibration, and final-test reads remained
zero; GPU, hardware, and Gate 6 runs remained zero. RFIG-030 records these
margins. This is compute-admission evidence only, not QML performance. D010 is
closed to rerun, and a separately accepted D011 is required before any
development-row fitting.

D011 is now prospectively accepted by the human research lead. A runner audit
found that D010's valid frozen benchmark used 256 validation rows, whereas the
largest real grouped-CV fold has 9,750 validation rows and a complete task has
39,000 held-out predictions. Before any development payload is opened, D011
therefore requires one source-bound 1,024-training/9,750-validation synthetic
bundle containing both projected heads, A02, and every matched control. The
conservative projection charges 1,220 largest-fold bundles with 25% margin
against the unchanged laptop ceilings and gives no credit for cache reuse,
smaller folds, or smaller qubit maps. A preflight `STOP` is terminal and opens
no research data. A `PASS` authorizes exactly one resumable P001
development-only campaign with frozen Q01b/FQK advancement, 20 selected seeds,
report-only shot/noise sensitivities, and planned RFIG-026 through RFIG-031 reporting.
Calibration, final-test, hardware/GPU, Gate 5 reinterpretation, and Gate 6
remain prohibited.

The formal D011 command then stopped during Python import with
`ModuleNotFoundError: No module named 'scripts'`. The failure occurred before
the D011 authority and source-hash checks, before synthetic arrays or resource
admission, and before any development payload was opened. D011 is therefore a
terminal pre-launch technical `STOP`, not a QML or laptop-capacity result.
P001-FR002 records a package-safe launcher and import-only smoke test as
future-only work; it cannot correct or retry D011. RFIG-029 now records both
post-Gate-5 technical stops. RFIG-031 and RFIG-026 through RFIG-028 remain
absent because their governed evidence stages were not reached. A separate
prospective human decision is required before any corrected preflight attempt.

D011-C1 was accepted on 2026-07-14 as that prospective launcher-only
correction. It moved shared synthetic-preflight helpers into the importable
`openqfuel` package, required a clean-source import-only smoke test, and
permitted one unchanged D011-shaped synthetic preflight attempt. The smoke test
passed, but the formal preflight stopped during correction-authority validation
because a pinned raw Git-blob hash for the D011 config was wrong. The original
D011 STOP evidence remains immutable and D011-C1 writes a separate STOP
evidence file. No synthetic workload, resource admission, development-row
fitting, calibration/final-test access, hardware/GPU work, Gate 5
reinterpretation, or Gate 6 work was reached. A new prospective human decision
is required before any hash-corrected launcher attempt.

After reviewing the mismatch, D011-C2 was accepted on 2026-07-14 as a
raw-Git-blob hash correction. It keeps the D011 workload unchanged, requires a
hash-consistency smoke test plus the package import smoke test, and permits one
separate corrected preflight attempt. D011-C2 does not authorize development
execution; a PASS would only establish synthetic compute admission and still
requires a later human decision before campaign resumption.

The D011-C2 smoke tests passed from clean source commit `06381d1`, and the
single unchanged corrected preflight passed every unchanged laptop boundary:
4.7259/250 CPU-core-hours, 0.2002/5 wall-days, 2.9785/20 GiB new artifacts,
0.6339/24 GiB peak process memory, and 45.3606 GiB free disk after artifacts
against the 20 GiB minimum. It used synthetic rows only; development,
calibration, final-test, hardware/GPU, and Gate 6 reads/runs stayed zero.
RFIG-031 records corrected fold-shape compute admission. The next decision is
whether to resume the single D011 development-only campaign.

D011-R1 was accepted on 2026-07-14 to resume exactly that single source-bound
D011 development-only campaign. It opens development rows only under the frozen
Q01b/FQK protocol. Calibration, final-test, hardware/GPU, Gate 5
reinterpretation, and Gate 6 remain locked.

The D011-R1 campaign completed from source commit `083d777` with 39,000
development rows read and zero calibration/final-test reads, hardware/GPU jobs,
or Gate 6 runs. Both near-term QML tracks are valid exploratory negatives:
Q01b selected PX-03 but averaged NRMSE 0.6612 versus C06 at 0.0068328 with no
qualifying dequantization regime, and FQK selected PX-03 but averaged AUROC
0.7436, Brier 0.1561, and recall 0.1089 versus strongest comparator C02-T02 at
0.9134, 0.1062, and 0.3233. RFIG-026 through RFIG-028 record the reached
development evidence; RFIG-029 records the future-only discussion boundary.

D012 is now open as discussion-only future-protocol interpretation. It may
compare possible D013 directions, but it does not authorize implementation,
refit, rerank, calibration/final-test access, hardware/GPU execution, Gate 5
reinterpretation, or Gate 6. The current recommendation is classical-first
residual and safety-filter hardening before any further QML experiment, unless
the paper explicitly needs a new prospectively frozen QML branch.

D013-C is accepted as that planning-only recommended path. It does not run a
new experiment. It records the long-term invention goal: after the experimental
program is complete, use the labeled evidence to design a new QML method that
beats the strongest documented NASA-relevant and repository baselines under
fair locked-split tests. The repository does not claim NASA used a specific QML
method unless a cited public source identifies one. Each result now needs an
invention-readiness label separating useful design evidence from prohibited
post-outcome rescue use.

D014-C is accepted as the freeze proposal for that path. It locks two future
classical-first tracks, `CRES` residual-cost hardening and `CSAFE`
safety-filter hardening, plus required controls, metrics, compute-admission
rules, and RFIG-032 through RFIG-035 planning. It still authorizes no
implementation, synthetic validation, development-data fitting,
calibration/final-test access, hardware/GPU execution, Gate 5 reinterpretation,
or Gate 6.

D015-C is accepted for implementation and synthetic validation only. It may
create CRES/CSAFE scaffolds and synthetic-array tests, but it still cannot fit
development data, read calibration/final-test data, run hardware/GPU work,
reinterpret Gate 5, claim a new QML invention, or open Gate 6.

D015-C synthetic scaffolds are implemented in `src/openqfuel/
post_gate5_classical.py` with tests that use synthetic arrays only. They cover
explicit residual targets, residual-cost metrics, safety threshold selection,
held-out safety metrics, scope guards, and invention-readiness labels.

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

The long-term aim is not to make the current failed QML variants look better.
It is to learn from every valid failure, stop, and negative result so a later
prospectively frozen QML invention can be tested against stronger baselines.

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
- docs/post_gate5_d012_future_protocol_discussion.md: discussion-only interpretation of the D011-R1 negative results.
- docs/post_gate5_d013_classical_first_protocol.md: planning-only classical-first residual and safety-filter path before QML invention.
- docs/post_gate5_d014_classical_first_freeze.md: freeze proposal for CRES/CSAFE tracks before any implementation.
- docs/post_gate5_d015_implementation_synthetic_validation.md: implementation and synthetic-validation authorization without data fitting.
- docs/qml_invention_readiness_ledger.md: labels each result's useful invention signal and prohibited post-outcome use.
- docs/post_gate5_implementation_freeze.md: D008 accepted implementation freeze defining exact Q01b/FQK methods, controls, stopping, compute, and failure-discussion rules.
- docs/post_gate5_compute_preflight.md: D009 synthetic-only clean-source compute-admission contract and pass/stop rules.
- docs/post_gate5_telemetry_correction.md: D010 typed-memory correction, independent validation, and one-rerun authority.
- docs/post_gate5_development_execution.md: D011 corrected fold-shape admission, one-campaign authority, endpoint rules, and reporting contract.
- docs/post_gate5_d011_c1_launcher_correction.md: D011-C1 launcher-only correction, import smoke test, and one unchanged preflight attempt.
- docs/post_gate5_d011_c2_hash_correction.md: D011-C2 raw-blob hash correction, hash smoke test, and one unchanged preflight attempt.
- docs/decision_log.md: acceptance and deviation history.
- data/processed/reporting/gate5_literature_hardening_matrix.csv: D004 source-to-control matrix for RFIG-019.
- data/processed/reporting/post_gate5_exploratory_protocol_matrix.csv: P001 near-term versus appendix/future QML boundary for RFIG-024.
- data/processed/reporting/post_gate5_exploratory_trial_manifest.csv: 30 balanced paired projected-kernel configurations frozen but not run.
- data/processed/reporting/post_gate5_future_research_discussion.csv: schema-locked register for evidence-based future-work suggestions after failures or stops.
- data/processed/reporting/post_gate5_compute_preflight_rerun.json: source-bound D010 synthetic compute-admission PASS evidence.
- data/processed/reporting/post_gate5_d011_fold_shape_preflight.json: source-bound D011 pre-launch technical-STOP evidence; corrected fold-shape admission was not reached.
- data/processed/reporting/post_gate5_d011_c1_fold_shape_preflight.json: source-bound D011-C1 authority-hash technical-STOP evidence; corrected fold-shape admission was still not reached.
- data/processed/reporting/post_gate5_d011_c2_fold_shape_preflight.json: source-bound D011-C2 corrected fold-shape synthetic compute-admission PASS evidence.
- data/processed/reporting/post_gate5_p001/: reserved compact D011 campaign, comparison, sensitivity, and decision evidence.
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
- scripts/make_post_gate5_preflight_result_figure.py: RFIG-030 D010 laptop resource-admission chart generator.
- scripts/run_post_gate5_compute_preflight.py: D010-corrected D009 synthetic-only resource benchmark; it cannot read research rows or authorize fitting.
- scripts/run_post_gate5_fold_shape_preflight.py: D011-C2 guarded largest-fold synthetic preflight launcher.
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
