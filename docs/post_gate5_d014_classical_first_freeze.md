# D014-C Classical-First Freeze Proposal

Version: 0.1.0
Decision: D014-C
Protocol: P001
Prepared: 2026-07-14
Accepted: 2026-07-14
Status: Freeze proposal accepted; no implementation or experiment authorized

## Decision

D014-C freezes the next scientifically appropriate proposal after D013-C:
classical-first residual and safety-filter hardening. This is the target
definition step before any later QML invention. It does not implement models or
open data.

The reason for this order is direct: D011-R1 showed both tested QML tracks were
weaker than strong classical controls. A new QML method should not be invented
against weak or informal controls. D014-C defines the stronger controls and
diagnostics that a later QML invention must beat.

## Authority Boundary

D014-C authorizes only the freeze proposal. It does not authorize:

- Implementation.
- Synthetic validation.
- Development-data fitting.
- Calibration or final-test access.
- Refit, rerank, retry, or post-outcome rescue.
- Hardware or GPU execution.
- Gate 5 reinterpretation.
- QML invention claims or quantum-advantage claims.
- Gate 6.

D015 must be accepted before implementation or synthetic validation. A later
clean-source compute-admission decision must pass before development-data
fitting.

## Locked Tracks

### CRES: Residual-Cost Hardening

Target: robust total correction delta-v.

Primary metric: pooled out-of-fold NRMSE.

Required controls:

- C06-T17 frozen physics residual.
- A02 exact classical RBF on identical fold-local PCA rows.
- Random-feature RBF residual.
- Compressed MLP residual.
- Ridge residual over explicit low-fidelity cost.

Before execution, a later decision must freeze the residual equation,
fold-local preprocessing, target standardization, candidate hyperparameter
grid, grouped folds, row IDs, compute budget, and result figures.

### CSAFE: Safety-Filter Hardening

Target: independently propagated feasibility.

Primary metric: pooled out-of-fold Brier score.

Secondary metrics: AUROC, recall at frozen threshold, false-negative rate,
expected calibration error, and safety-filter intervention rate.

Required controls:

- C02-T02 strongest D011 feasibility comparator.
- Calibrated logistic safety head.
- Class-weighted tree ensemble.
- Conformal or quantile safety threshold.
- A02 exact classical RBF feasibility head.

Before execution, a later decision must freeze the threshold-selection rule,
false-negative priority, acceptable intervention-rate tradeoff, calibration
diagnostics, grouped folds, row IDs, compute budget, and result figures.

## Compute Admission

No development-data fitting is allowed until a later clean-source synthetic
preflight estimates the largest grouped-fold workload against the recorded
local laptop limits:

- 250 CPU-core-hours.
- Five wall-days.
- 20 GiB new artifacts.
- 24 GiB peak process memory.
- At least 20 GiB free disk after artifacts.
- Zero GPU-hours.

The preflight must conservatively charge every candidate control and may not
claim cache or early-stopping savings unless measured prospectively.

## Figure Plan

- RFIG-032: D014-C classical-first freeze map and authority boundary.
- RFIG-033: future compute-admission margins if a later preflight is accepted
  and reached.
- RFIG-034: residual-cost hardening results if a later development-only
  campaign is accepted and reached.
- RFIG-035: safety-filter hardening results if a later development-only
  campaign is accepted and reached.

Missing or unauthorized figures must remain absent rather than being plotted as
zero.

## Current Recommendation

D015-C has implemented synthetic scaffolds, and D016-C has passed synthetic
compute admission for those scaffolds. Development-data fitting still requires
D017. Gate 6 remains unauthorized.
