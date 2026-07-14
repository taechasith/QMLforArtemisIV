# D036: Task-Aligned Projected Quantum Kernel

Protocol: P004
Status: accepted for one bounded development-only campaign
Date: 2026-07-15

## 1. Research problem

Can a quantum kernel improve the frozen C06 physics-residual predictor when its
input coordinates are learned from cross-fitted C06 residuals rather than from
unsupervised PCA coordinates?

## 2. Mathematical formulation

For outer fold `f`, let `x in R^q` be the fold-local compressed correction
context, `y` the standardized correction cost, and `b_f(x)` the outer C06
prediction. Four inner whole-group fits produce `e_i = y_i -
b_f^{-inner}(x_i)`. Fit PLS with `q` components to `(x_i, e_i)` on outer
training rows, then standardize its scores using training moments:

`z_i = S(PLS_q(x_i, e_i)) in R^q`.

Encode `z` into the fixed RY/RZ statevector circuit and project to local
Pauli-X/Y/Z expectations `r_Q(z)`. The kernel and prediction are

`K_Q(z,v) = exp(-gamma/2 * ||r_Q(z)-r_Q(v)||_2^2)`

`f_Q(x) = b_f(x) + K_Q(z,Z) alpha`.

`alpha` is the Nyström kernel-ridge coefficient fitted to `e_i`. TAP-RBF uses
the same `z`, landmarks, bandwidth, regularization, and target. The unchanged
C06 feasibility head supplies the safety probability used in plan selection.

## 3. Definitions and assumptions

`q` is 4, 6, or 8; one layer is used; `Z` contains training projections;
`gamma` is the training-fold median-distance rule times 0.25; `alpha=1`; and
there are 256 deterministic SHA-256 landmarks. Inputs, targets, groups, outer
folds, and standardization are inherited from the frozen development benchmark.
Only development rows are permitted.

## 4. Scientific status of claims

The PLS projection is a design assumption. The residual separation is a direct
consequence of inner group exclusion. The PSD kernel property is inherited
from the projected-kernel construction. Better prediction is an empirical
hypothesis. No QML, NASA, mission, hardware, or quantum-advantage claim is
authorized by this protocol.

## 5. Closest prior method

The closest methods are D035 CFQSR and its A02-STACK control. D036 changes only
the fold-local residual-supervised coordinate map. TAP-RBF isolates whether any
gain comes from the classical supervised projection rather than the quantum
map. D034 and D035 remain immutable report-only evidence.

## 6. Reproduction plan

Reproduce C06 on the same five outer grouped folds. Recompute the D035-style
cross-fitted C06 residuals with four inner group folds. Fit PLS only on each
outer training set, transform validation rows with frozen training parameters,
and compare TAPQK to TAP-RBF using shared coordinates and landmarks.

## 7. Reproduction success criteria

All five outer folds, four inner folds, three fixed q values, and 20 seeds must
complete. Inner fit and holdout groups must be disjoint. Projection parameters
must be fit without outer validation rows. All locked-data counters must stay
zero.

## 8. Proposed modification

Replace D035's unsupervised PCA coordinates with a supervised PLS projection
trained on honest, cross-fitted C06 residual targets. Keep the circuit, kernel,
landmark, ridge, safety, split, seed, and resource rules unchanged.

## 9. Proposed mechanism

Unsupervised PCA maximizes input variance, not residual predictability. PLS
maximizes covariance with the residual target and may preserve a direction that
PCA compresses away. This is a testable mechanism, not evidence that the
quantum map itself is superior.

## 10. Main hypothesis

Under the frozen development benchmark, TAPQK-08 will reduce pooled OOF NRMSE
by at least 5 percent versus C06, preserve selection safety, and beat TAP-RBF
by at least 5 percent.

## 11. Falsification criteria

Reject the hypothesis if the 5% improvement, paired interval, regret,
infeasible-selection, or TAP-RBF comparison fails; if projection leakage is
detected; or if any fold, seed, or audit row is missing.

## 12. Candidate theorem or proposition

For fixed training data and deterministic PLS settings, the transformed
validation coordinate `z_v` is a function only of outer training inputs and
cross-fitted residuals. Therefore the transform does not use the outer
validation target.

## 13. Proof strategy

PLS is fit before validation transformation and its coefficients are functions
of the permitted training arrays. Standardization uses only training score
moments. Applying this fixed map to validation inputs cannot access validation
outcomes. This proves data separation, not statistical independence of the
physical process. The launcher records projection hashes and row counts.

## 14. Counterexample search

Test a duplicated group, constant target, one-dimensional input, zero residual,
zero-variance PLS score, and an intentionally leaky projection in unit tests.
The valid projection must reject degenerate scores and must remain unchanged
when unrelated validation outcomes are changed.

## 15. Experimental design

Use five outer grouped folds, 1,024 outer training rows, four inner grouped
folds, q=4/6/8, one non-entangling layer, 20 seeds, and all held-out outer
validation rows. Run C06, TAPQK, and TAP-RBF under identical folds and seeds.
No post-outcome reranking is allowed.

## 16. Classical baselines

C06 is the primary physics baseline. TAP-RBF is the parameter- and
input-matched classical control. It uses the same PLS scores, residual targets,
landmarks, gamma rule, regularization, and prediction wrapper.

## 17. Quantum baselines

D035 CFQSR and D034 PRQK are immutable historical references. TAPQK uses the
same exact statevector projected kernel family, so a positive result must beat
TAP-RBF before any quantum-specific interpretation.

## 18. Ablation studies

The q=4/6/8 configurations measure coordinate-width scaling. The historical
D035 PCA-coordinate results are a report-only comparison. Entanglement is held
off because D034's fixed entanglement ablation did not recover the baseline;
reopening it would add post-outcome degrees of freedom.

## 19. Statistical analysis

Report all 20 seed-pooled OOF NRMSE, MAE, regret, infeasible selection, Brier,
AUROC, and recall values. Report means, sample standard deviations, and paired
95% bootstrap intervals for TAPQK-08 minus C06. The primary decision is made
once on the prespecified endpoint.

## 20. Resource analysis

Record trainable parameters (none in the quantum map), PLS parameters, qubits,
depth, local observable count, landmarks, statevector executions, wall time,
CPU time, peak working set, and free disk. Include PLS fitting and classical
data preparation in end-to-end cost.

## 21. Noise analysis

Finite-shot, depolarizing, readout, amplitude-damping, and phase-damping
sensitivity are deferred unless the exact-statevector candidate passes the
development endpoint. Noise cannot rescue a negative exact result.

## 22. Scaling analysis

Report q=4/6/8 and PLS projection cost. These three bounded sizes do not prove
asymptotic quantum scaling.

## 23. Classical-simulability analysis

The q<=8 statevector and local-observable kernel are efficiently classically
simulable. A positive endpoint would be a hybrid predictive result only, not a
quantum-advantage result.

## 24. Data-access cost

All data are classical development rows. Include feature construction, PLS
fit, state preparation, local projection, kernel construction, Nyström solve,
and classical decoding. No QRAM or quantum memory assumption is made.

## 25. Reproducibility requirements

Commit the protocol, config, launcher, projection and inner-fold audits, seed
metrics, summaries, paired interval, figure generator, figure registry rows,
source commit, and zero locked-data counters.

## 26. Main scientific risks

C06 residuals may have no predictable structure; PLS may overfit the small
residual target; TAP-RBF may explain any gain; and lower cost error may not
improve mission selection.

## 27. Main implementation risks

The main risks are fitting PLS on validation rows, accidentally using
in-sample C06 residuals, inconsistent score scaling, mismatched landmarks, and
confusing supervised preprocessing with quantum advantage. The launcher fails
closed on these conditions.

## 28. Minimum publishable result

A complete valid negative establishes that this task-aligned projection did not
beat C06 and identifies whether supervised preprocessing or the quantum map was
the limiting factor. A positive result requires all C06, TAP-RBF, safety, and
integrity rules before any operational interpretation.

## 29. Recommended first experiment

Run TAPQK-08 as the primary endpoint with q=4/6/8 fixed scaling ablations and
TAP-RBF as the identical-input control. Preserve the C06 safety guard exactly.

## 30. Final assessment

The candidate is mathematically specified, directly motivated by D034/D035,
and experimentally falsifiable. Its result is unresolved until the source-bound
campaign executes.

Current conclusion: **Proceed only after reproduction**.
