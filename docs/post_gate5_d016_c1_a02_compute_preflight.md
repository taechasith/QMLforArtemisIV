# D016-C1 A02 Exact-RBF Compute Preflight Correction

Version: 0.1.0
Decision: D016-C1
Protocol: P001
Prepared: 2026-07-14
Accepted: 2026-07-14
Status: Accepted for one synthetic A02 preflight; result pending

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
