# Gate 5 Preregistered Algorithm Trigger Report

Status: **Technical trigger FAIL**
Scope: development-only grouped CV; 20 frozen seed indices
Campaign source commit: `6e5a6202eec486e88af6b969f6af86571fb0ce32`
Reporting source commit: `7b7db694cd7911a2643950c4c57f993046271a95`
Accepted D007 candidate commit: `7a726c8917a85f24313208eb18c33e1ccb5f703e`
Reporting module SHA-256: `dd56a2ed3b4dc841669f486c14eb7ce8f7da66fbcc3db3883ea4492aed22c7e2`
Reporting script SHA-256: `13c9b3eb1e47d984f87050ea1c972c501b63feed93440e6eb8a2f4a26b92a3d9`
Figure generator SHA-256: `5abc0e5b675daf0f7fa4bf5438eb06856fbfc454557ed0ea59173efa02609fd7`

## Decision result

| Condition | Result |
|---|---|
| Best QML within 5% of strongest classical mean NRMSE | False |
| Reproducible regime survives strongest classical and tuned A01/C05 controls | False |
| Five-fold, 20-seed stability including the upper confidence bound | False |
| Source-bound complete campaign evidence | True |
| Mandatory D004 claim-boundary diagnostics complete | True |

Strongest classical: `C06`.
Best QML: `Q01`.
Mean relative NRMSE gap: `72.99137081675265`.
Qualified preregistered regimes: `0`.

Recommendation: `reject_new_algorithm_development_and_report_negative_result`.

Evidence-contract findings: `[]`.

Selection evidence: `complete_with_scientific_eliminations`. Scientifically
eliminated families: `{'Q02': {'status': 'verified_terminal_nonadvancing', 'last_authorized_rung': 128, 'blocked_next_rung': 256, 'authorized_tasks': 30, 'completed_folds': 150, 'eligible_tasks': 8, 'required_retained_tasks': 15, 'reason': 'Too few eligible trials to satisfy the frozen retention count', 'seed_rerun_status': 'not_reached_under_frozen_eligibility'}, 'Q03': {'status': 'verified_terminal_nonadvancing', 'last_authorized_rung': 128, 'blocked_next_rung': 256, 'authorized_tasks': 30, 'completed_folds': 150, 'eligible_tasks': 4, 'required_retained_tasks': 15, 'reason': 'Too few eligible trials to satisfy the frozen retention count', 'seed_rerun_status': 'not_reached_under_frozen_eligibility'}}`. A
terminally nonadvancing family remains excluded from seed comparisons and the
trigger; no missing seed evidence is imputed.

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
