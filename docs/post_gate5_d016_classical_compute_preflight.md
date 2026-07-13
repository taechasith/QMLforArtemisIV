# D016-C Classical-First Synthetic Compute Preflight

Version: 0.1.0
Decision: D016-C
Protocol: P001
Prepared: 2026-07-14
Accepted: 2026-07-14
Status: Accepted for one clean-source synthetic preflight; result pending

## Decision

D016-C authorizes exactly one clean-source synthetic compute-admission
preflight for the D014-C classical-first CRES and CSAFE scaffolds implemented
under D015-C. This is a resource and integrity boundary only.

The preflight may use synthetic arrays and the committed CRES/CSAFE utilities.
It may not open development, calibration, final-test, hardware, GPU, or Gate 6
work.

## Authorized Work

- Run `scripts/run_post_gate5_d016_preflight.py` once from a clean `main`
  worktree.
- Benchmark the largest-fold synthetic CRES/CSAFE workload.
- Project the measured workload across five folds and 20 seed replicates with a
  25% margin and no cache or early-stop credit.
- Generate RFIG-033 only if the preflight reaches result evidence.

## Prohibited Work

- Development-data fitting.
- Calibration or final-test reads.
- Refit, rerank, retry, or threshold rescue.
- Hardware or GPU execution.
- Gate 5 reinterpretation.
- QML invention or quantum-advantage claims.
- Gate 6.

## Required Next Boundary

If D016-C passes, D017 is still required before any development-data fitting.
If D016-C stops, the stop must be recorded as future-only discussion and must
not reduce or retry the active workload.
