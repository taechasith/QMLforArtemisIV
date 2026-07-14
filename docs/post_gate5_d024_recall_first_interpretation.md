# D024-C Recall-First Interpretation

Version: 0.1.0
Decision: D024-C
Protocol: P001
Prepared: 2026-07-14
Accepted: 2026-07-14
Status: Interpretation complete; no advance

## Decision

D024-C interprets the D023-C development-only recall-first audit. It is not a
new experiment and does not refit models, rerun threshold selection, apply
thresholds to real data, open raw payloads, or touch calibration, final-test,
hardware/GPU, mission-loop, or Gate 6 scopes.

## Interpretation

D023-C found a useful future safety-objective signal: when missed unsafe cases
are prioritized, `calibrated_logistic` becomes the selected CSAFE-RF candidate
with mean recall 0.8043 and false-negative rate 0.1957.

That signal is not sufficient for scientific advance. It is post-D017-informed
development evidence, and its Brier score remains worse than the best-Brier
tree. The correct lesson is that future safety filters must prospectively
freeze both recall or false-negative-cost priority and calibration-quality
constraints before locked-data use.

The QML-style A02 exact-RBF feasibility candidate did not dominate the selected
logistic head under the recall-first audit. It remains appendix or future-work
evidence, not an advancing QML result.

## Boundary

D024-C closes the CSAFE-RF branch into manuscript discussion unless a future
protocol is opened from scratch with prospectively frozen recall, calibration,
false-negative-cost, locked-data, and claim rules. D024-C does not rescue D017,
reinterpret Gate 5, authorize calibration/final-test access, authorize
mission-loop work, claim QML invention or quantum advantage, or open Gate 6.

RFIG-043 records this interpretation boundary.
