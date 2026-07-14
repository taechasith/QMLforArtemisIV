# D020-C Recall-First Safety Freeze Proposal

Version: 0.1.0
Decision: D020-C
Protocol: P001
Prepared: 2026-07-14
Accepted: 2026-07-14
Status: Freeze proposal accepted; no implementation or experiment authorized

## Decision

D020-C freezes a future CSAFE-RF safety-filter direction after D019-C. The
freeze proposal changes the future objective from Brier-first safety selection
to recall-first or false-negative-risk-first safety selection.

This is a proposal boundary only. D020-C does not authorize implementation,
threshold application, development-data fitting, calibration access,
final-test access, hardware/GPU execution, mission-loop work, Gate 5
reinterpretation, QML invention, quantum-advantage claims, or Gate 6.

## Scientific Rationale

D017-C showed that a model can have the best mean Brier score and still be
unsafe for the safety-filter purpose if recall is near zero. D018-C and
D019-C therefore identified the useful future signal: safety selection must
prioritize missed unsafe cases before probability calibration.

D020-C prevents post-outcome rescue by freezing the rule before any new
implementation or data fitting. The logistic head's higher recall remains
future-only motivation; it is not an active replacement for the D017 selector.

## Frozen Future Requirements

Any executable successor must prospectively implement the following:

- primary objective: maximize unsafe-case recall or minimize false-negative
  risk;
- secondary diagnostics: Brier score, calibration, precision, false-positive
  burden, artifact size, and laptop-fit compute;
- selection order: recall, false-negative rate, Brier score, then model
  simplicity;
- threshold policy: select thresholds only inside authorized training folds;
- controls: C02-T02, calibrated logistic, class-weighted tree, A02 exact
  classical RBF, and any later QML candidate only under a separate freeze.

## Next Boundary

D021 would be allowed to implement only synthetic-array guards and metrics if
it is opened later. A separate compute preflight would still be required before
any development-data fitting.

RFIG-039 records the D020-C freeze boundary.
