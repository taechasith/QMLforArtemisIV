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
figure-record requirements. Registered development-only model fitting may begin
only after the Gate 5 runner preserves those D004 controls. No fitted research
model or benchmark result exists yet.
Both final-test splits remain locked and require a separate unlock commit.

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
