# D016-C Classical-First Synthetic Compute Preflight

Version: 0.1.0
Decision: D016-C
Protocol: P001
Prepared: 2026-07-14
Accepted: 2026-07-14
Status: Completed with synthetic compute admission PASS; development fitting unauthorized

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

## Outcome

The single authorized D016-C preflight ran from clean source commit
`45409a86a5e450d72ba7f043715956fa5b916974` and passed every admission check.
The projected five-fold, 20-seed scaffold workload used:

- 0.0179 CPU-core-hours of the 250-hour limit.
- 0.000788 wall-days of the five-day limit.
- 1.2207 GiB new artifacts of the 20 GiB limit.
- 0.1713 GiB peak process memory of the 24 GiB limit.
- 46.5275 GiB projected free disk after artifacts against the 20 GiB minimum.
- 0 GPU-hours.

The run used 10,774 synthetic rows and read zero development, calibration, or
final-test rows. It submitted no hardware/GPU job and ran no Gate 6 scenario.
RFIG-033 records the resource margins. The bounded MLP component reached the
configured 50-iteration synthetic limit without convergence, which is retained
as compute-workload evidence only and is not a model-performance claim.
