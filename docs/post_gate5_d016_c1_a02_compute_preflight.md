# D016-C1 A02 Exact-RBF Compute Preflight Correction

Version: 0.1.0
Decision: D016-C1
Protocol: P001
Prepared: 2026-07-14
Accepted: 2026-07-14
Status: Completed with synthetic A02 compute admission PASS; development fitting unauthorized

## Reason

A pre-D017 audit found that D016-C passed compute admission for the CRES/CSAFE
scaffolds but did not benchmark the D014-C required A02 exact classical RBF
control. Opening development rows before measuring that missing control would
make the compute boundary incomplete.

## Authorized Work

- Run exactly one clean-source synthetic preflight for A02 exact RBF residual
  and feasibility heads.
- Use the same largest-fold shape as D016-C: 1,024 training rows and 9,750
  validation rows.
- Project five folds and 20 seed replicates with 25% margin and no cache or
  early-stop credit.
- Generate RFIG-036 if terminal evidence is reached.

## Prohibited Work

- Development-data fitting.
- Calibration or final-test reads.
- Refit, rerank, retry, or workload reduction.
- Hardware or GPU execution.
- Gate 5 reinterpretation.
- QML invention or quantum-advantage claims.
- Gate 6.

## Required Next Boundary

D017 may be prepared only if D016-C and D016-C1 both pass. Even then, D017 must
separately authorize development-data fitting.

## Outcome

The single authorized D016-C1 A02 exact-RBF preflight ran from clean source
commit `a40a6687b7c68a04f355ee40e0ff6144482eaf6c` and passed every admission
check. The projected five-fold, 20-seed A02 exact-RBF workload used:

- 0.0109 CPU-core-hours of the 250-hour limit.
- 0.000438 wall-days of the five-day limit.
- 1.2207 GiB new artifacts of the 20 GiB limit.
- 0.2679 GiB peak process memory of the 24 GiB limit.
- 46.5217 GiB projected free disk after artifacts against the 20 GiB minimum.
- 0 GPU-hours.

The run used 10,774 synthetic rows and read zero development, calibration, or
final-test rows. It submitted no hardware/GPU job and ran no Gate 6 scenario.
RFIG-036 records the A02 exact-RBF compute-correction margins.
