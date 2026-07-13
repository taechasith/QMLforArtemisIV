# Gate 5 Preregistered Algorithm Trigger Report

Status: **Technical trigger UNAVAILABLE**
Scope: development-only grouped CV; 20 frozen seed indices
Source commit: `6e5a6202eec486e88af6b969f6af86571fb0ce32`

## Decision result

| Condition | Result |
|---|---|
| Best QML within 5% of strongest classical mean NRMSE | False |
| Reproducible regime survives strongest classical and tuned A01/C05 controls | False |
| Five-fold, 20-seed stability including the upper confidence bound | False |
| Source-bound complete campaign evidence | False |
| Mandatory D004 claim-boundary diagnostics complete | False |

Strongest classical: `C06`.
Best QML: `Q01`.
Mean relative NRMSE gap: `72.99137081675265`.
Qualified preregistered regimes: `0`.

Recommendation: `repair_or_complete_evidence_before_gate5_decision`.

Evidence-contract findings: `['selection manifest is incomplete']`.

D004 claim-boundary handling: `mandatory_report_only_pending_human_interpretation`. The
feature-scale, entanglement-removal, random-feature, parameter-count,
sample/rung, and no-reference summaries are frozen in
`gate5_claim_boundary_diagnostics.json` and require human interpretation.

## Governance boundary

This report makes no final-test, mission-performance, hardware-speedup, quantum
advantage, or flight-suitability claim. Calibration rows read:
**0**. Final-test rows read:
**0**. An `UNAVAILABLE` report must be repaired
before a Gate 5 decision. Once evidence is available, the human research lead
must separately accept, reject, or revise the trigger result before Gate 6 or
any new algorithm work.
