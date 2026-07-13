# D015-C Implementation And Synthetic Validation Authorization

Version: 0.1.0
Decision: D015-C
Protocol: P001
Prepared: 2026-07-14
Accepted: 2026-07-14
Status: Implementation and synthetic validation complete; no data fitting

## Decision

D015-C authorizes implementation scaffolding and synthetic-only validation for
the D014-C classical-first freeze. The allowed work is limited to CRES
residual-cost hardening and CSAFE safety-filter hardening infrastructure.

This does not authorize development-data fitting. A later clean-source compute
admission decision, currently reserved as D016, is required before any
development payload is opened.

## Allowed Work

- Implement CRES residual-cost metrics and scaffolds.
- Implement CSAFE safety-filter metrics and scaffolds.
- Add synthetic-only tests for fold-local preprocessing, residual equations,
  safety-threshold isolation, invention-readiness labels, and fail-closed
  locked-split guards.
- Generate RFIG-032 from D014-C freeze evidence.

## Prohibited Work

- Development-data fitting.
- Calibration or final-test reads.
- New QML architecture implementation.
- Hardware or GPU execution.
- Gate 5 reinterpretation.
- QML invention or quantum-advantage claims.
- Gate 6.

## Required Next Boundary

D016 has passed clean-source synthetic compute admission for the D014-C
CRES/CSAFE scaffolds. D017 must prospectively authorize any development-data
fitting. Missing or unauthorized RFIG-034 through RFIG-035 remain absent.

## Implementation Outcome

The D015-C synthetic scaffolds are implemented in
`src/openqfuel/post_gate5_classical.py`. They are array-only helpers for CRES
and CSAFE:

- D015 scope guard.
- Explicit high-minus-low residual target construction.
- Residual-cost RMSE, NRMSE, MAE, and tail-error metrics.
- Training-only safety-threshold selection.
- Held-out Brier, AUROC, recall, precision, false-negative, false-positive,
  expected-calibration-error, and intervention-rate metrics.
- Invention-readiness labels that require prohibited rescue use to be stated.

The corresponding tests use synthetic arrays only. Development-data fitting
remains unauthorized.
