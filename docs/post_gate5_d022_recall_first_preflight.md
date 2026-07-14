# D022-C Recall-First Synthetic Compute Preflight

Version: 0.1.0
Decision: D022-C
Protocol: P001
Prepared: 2026-07-14
Accepted: 2026-07-14
Status: Clean-source synthetic compute preflight PASS

## Decision

D022-C authorizes exactly one clean-source synthetic compute preflight for the
CSAFE-RF recall-first guards and metrics implemented under D021-C.

The preflight may use synthetic arrays only. It may benchmark training-fold
threshold selection, held-out recall-first scoring, and selection by recall,
false-negative rate, Brier score, and model complexity.

## Boundary

D022-C authorizes no development-data fitting, threshold application to real
data, calibration access, final-test access, refit, rerank, retry,
hardware/GPU execution, mission-loop work, Gate 5 reinterpretation, QML
invention claim, quantum-advantage claim, or Gate 6.

If the preflight passes, D023 would still be required before any
development-data fitting decision. If it stops, the stop must be recorded as
future-only discussion without retrying or reducing the active workload.

## Outcome

The single authorized clean-source preflight ran from source commit
`b5263ba3876c4e66f3243b58a679e2c29419120f` and passed every admission check.
It projected 0.003798 CPU-core-hours, 0.000174 wall-days, 0.2441 GiB new
artifacts, 0.0363 GiB peak working set, 46.9115 GiB free disk after artifacts,
and zero GPU-hours.

The run used 10,774 synthetic rows. Development rows, calibration rows,
final-test rows, hardware jobs, GPU hours, and Gate 6 runs remained zero.
RFIG-041 records the compute-admission boundary.
