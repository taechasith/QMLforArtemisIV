# D021-C Recall-First Synthetic Validation

Version: 0.1.0
Decision: D021-C
Protocol: P001
Prepared: 2026-07-14
Accepted: 2026-07-14
Status: Implementation and synthetic validation only

## Decision

D021-C implements CSAFE-RF recall-first scoring and selection guards on
synthetic arrays only. It follows the D020-C freeze: rank eligible candidates
by recall, then false-negative rate, then Brier score, then model simplicity.

D021-C does not authorize development-data fitting, threshold application to
real data, calibration access, final-test access, hardware/GPU work,
mission-loop work, Gate 5 reinterpretation, QML invention claims,
quantum-advantage claims, or Gate 6.

## Synthetic Validation

The validation runner uses synthetic training arrays to select thresholds and
synthetic held-out arrays to score two candidate heads. The evidence is only a
guard and metric validation. It is not model-performance evidence for the
research dataset.

Expected counters remain zero for development rows, calibration rows,
final-test rows, hardware jobs, GPU hours, and Gate 6 runs.

## Boundary

If D021-C passes, the next possible executable step is only a clean-source
synthetic compute preflight or a stop into manuscript discussion. Development
data still require a later prospective decision and compute admission.

RFIG-040 records the synthetic-validation boundary.
