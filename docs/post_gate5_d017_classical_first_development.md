# D017-C Classical-First Development Campaign

Version: 0.1.0
Decision: D017-C
Protocol: P001
Prepared: 2026-07-14
Accepted: 2026-07-14
Status: Completed with development-only evidence; D018 interpretation required

## Decision

D017-C authorizes exactly one development-only CRES/CSAFE classical-first
campaign after D016-C and D016-C1 both passed synthetic compute admission. The
campaign uses the original grouped development split and does not open
calibration, final-test, hardware, GPU, or Gate 6 work.

## Frozen Scope

- Five grouped development folds.
- Twenty seed replicates.
- 1,024 fold-local training rows per fold.
- Fold-local preprocessing and PCA only.
- CRES residual-cost controls: ridge residual, random-feature RBF residual,
  compressed MLP residual, and A02 exact RBF residual.
- CSAFE safety controls: calibrated logistic, class-weighted tree, and A02
  exact RBF feasibility.
- RFIG-034 for residual-cost results and RFIG-035 for safety-filter results if
  the campaign reaches terminal evidence.

## Prohibited Work

- Calibration or final-test reads.
- Refit, rerank, retry, or post-outcome rescue.
- Hardware or GPU execution.
- Gate 5 reinterpretation.
- QML invention or quantum-advantage claims.
- Mission-loop or Gate 6 work.

## Required Next Boundary

D018 must interpret the D017 development-only result. D017 cannot authorize
calibration, final tests, hardware, Gate 6, or a QML invention claim.

## Outcome

The single authorized D017-C campaign completed from clean source commit
`419844a690d625502718e00b3e4dcafc6d99286c`. It read 39,000 development rows and
zero calibration or final-test rows. Hardware jobs, GPU hours, and Gate 6 runs
remained zero.

CRES residual-cost result: `ridge_residual` had the best mean residual NRMSE at
0.8265. This is development-only evidence and does not establish final-test or
mission-loop performance.

CSAFE safety-filter result: `class_weighted_tree` had the best mean Brier score
at 0.1311, but its mean recall was only 0.0139. That conflict is scientifically
important: D018 must decide whether low Brier with very low recall is usable or
whether the safety-filter objective failed under the frozen threshold rule.

RFIG-034 records CRES residual-cost results. RFIG-035 records CSAFE safety
results. No QML invention, quantum-advantage, calibration, final-test, mission,
hardware, or Gate 6 claim is authorized.
