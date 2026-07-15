# D044: Nonlinear Interaction Fidelity-RBF Kernel

Protocol: P012
Status: accepted for one bounded development-only campaign
Date: 2026-07-15

## 1. Research problem

Can a fixed nonlinear interaction stack extract complementary residual
information from the D043 fidelity/RBF experts while beating an identical
nonlinear two-RBF control?

## 2. Mathematical formulation

For each outer fold, let `e` be the cross-fitted C06 residual on outer-training
rows. Let `u_F`, `u_R25`, and `u_R50` be inner grouped out-of-fold predictions
of the fidelity, RBF-0.25, and RBF-0.50 residual experts. Define the fixed
quadratic feature map

`psi(u,v) = [1, u, v, u*v, u^2, v^2]`.

The candidate stack coefficient solves

`beta_A = argmin_beta ||e - psi(u_F,u_R25) beta||_2^2 +
0.001 ||beta_without_intercept||_2^2`.

The matched control uses

`beta_C = argmin_beta ||e - psi(u_R25,u_R50) beta||_2^2 +
0.001 ||beta_without_intercept||_2^2`.

After the inner fit, each expert is refit on the complete outer-training fold.
For an outer validation row x, predictions are

`f_A(x) = inverse_scale[b_C06(x) + 0.10*psi(delta_F(x),delta_R25(x))*beta_A]`

and the control substitutes `delta_R50` and `beta_C`.

## 3. Definitions and assumptions

The input is the frozen development feature contract plus the q compressed
features and C06 conditioning feature. The output is decoded physics-residual
cost. q is 4, 6, or 8; one entangling layer, 256 landmarks, alpha=1.0, and
lambda=0.10 are fixed. The interaction map has six columns. Only the five
outer grouped folds and their four inner grouped training folds are used.

## 4. Scientific status of claims

The feature map and ridge solution are design constructions. The ridge solve
is a convex quadratic optimization with a unique solution when its regularized
normal matrix is positive definite. The claim that channel interactions encode
residual structure not captured by linear stacking is an empirical hypothesis.
Any positive result is development-only. No NASA, mission, hardware,
quantum-advantage, Gate 5, or Gate 6 claim is authorized.

## 5. Closest prior method

The closest method is D043 SFRK, which uses a linear convex stack of the same
experts. D044 adds only a predeclared quadratic interaction map and applies the
same map and ridge penalty to the two-RBF control. D043 and earlier evidence
remain immutable.

## 6. Reproduction plan

Reproduce D039 conditioning and D043 inner out-of-fold expert predictions.
Fit the two quadratic stacks on outer-training OOF predictions, refit the
experts on all outer-training rows, apply the fixed stack coefficients to
outer validation predictions, and compare q=4/6/8 with C06 and the matched
two-RBF stack.

## 7. Reproduction success criteria

All 39,000 development rows, five outer folds, four inner folds, q=4/6/8,
and 20 seeds must complete. The candidate and control must have identical
feature-map dimension, ridge penalty, folds, seed schedule, and data scope.
Construction audits must show zero outer validation-outcome use and zero
locked-data reads.

## 8. Proposed modification

Replace D043's linear convex stack with the fixed quadratic map `[1,u,v,u*v,
u^2,v^2]`. No data split, residual target, quantum channel, classical
control family, safety rule, or primary threshold changes.

## 9. Proposed mechanism

D043 shows that a linear training-only stack clears C06 but leaves a smaller
classical-specific gap. The interaction terms test whether one expert's
correction is useful conditionally on the magnitude or sign of the other
expert, while the identical two-RBF map controls for generic nonlinear
ensembling.

## 10. Main hypothesis

NIFRK-08-NL will improve pooled OOF NRMSE by at least 5 percent versus C06,
preserve safety metrics, and beat TWO-RBF-08-NL by at least 5 percent.

## 11. Falsification criteria

Reject if any threshold, paired interval, safety metric, matched-control,
feature-map, ridge, inner-group, numerical, or data-boundary condition fails.
A complete integrity-valid failure is a scientific negative; an incomplete
or leaked computation is a technical stop.

## 12. Candidate theorem or proposition

With an intercept unregularized and positive ridge penalty on the other five
columns, the normal matrix `Psi^T Psi + R` is positive definite on the
regularized subspace and the stated linear system has a unique minimum-norm
solution for the intercept component. The model remains a finite-dimensional
classical ridge stack.

## 13. Proof strategy

The objective is a quadratic with Hessian `2(Psi^T Psi + R)`. The positive
ridge term removes singularity in non-intercept directions; if the intercept
is collinear with a zero-variance design, solve with the declared linear
solver and fail closed on non-finite output. This establishes numerical model
validity, not generalization or superiority.

## 14. Counterexample search

Test constant experts, identical experts, zero experts, opposite experts,
zero interaction, large finite corrections, and rank-deficient feature maps.
Verify the intercept handling, finite coefficients, identical feature columns
for candidate/control, and no outer validation label in the fit.

## 15. Experimental design

Use five grouped outer folds, 1,024 training rows per fold, four inner grouped
folds, q=4/6/8, 20 seeds, one entangling layer, 256 landmarks, alpha=1.0,
lambda=0.10, and the unchanged C06 safety head. q=8 is the only primary.

## 16. Classical baselines

C06 is the primary baseline. TWO-RBF-q-NL uses RBF-0.25 and RBF-0.50 with
the same inner expert predictions, quadratic map, ridge penalty, and decoding.

## 17. Quantum baselines

D034-D043 remain immutable references. The exact fidelity statevector channel
at q<=8 and the interaction stack are classically simulable. No quantum
advantage claim is possible from this protocol.

## 18. Ablation studies

q=4 and q=6 are fixed scaling ablations. The two-RBF quadratic stack is the
mechanism ablation. The interaction map and ridge penalty are not tuned after
outcomes.

## 19. Statistical analysis

Report all 20 seed-pooled OOF NRMSE, MAE, regret, infeasible selection, Brier,
AUROC, and recall values, means, sample standard deviations, and the paired
95% bootstrap interval for NIFRK-08-NL minus C06. Report coefficient and
interaction-norm audits.

## 20. Resource analysis

Record inner/outer channel fits, q, interaction features, ridge solves,
landmarks, CPU time, wall time, peak working set, free disk, and decoding.
The reference boundary is the recorded i9-13900HX/32 GiB/RTX 4060 laptop with
CPU-only execution.

## 21. Noise analysis

Finite-shot and hardware-noise tests remain deferred. Exact statevector
results at q<=8 cannot support a noisy-hardware or quantum-advantage claim.

## 22. Scaling analysis

Report q sensitivity and coefficient distributions only. Do not infer
asymptotic scaling from q=4/6/8 or one polynomial map.

## 23. Classical-simulability analysis

All tested projections, kernels, inner OOF predictions, polynomial features,
and ridge solves are classically simulable. A positive result is a
hybrid-surrogate result, not quantum advantage.

## 24. Data-access cost

All inputs are classical development rows. Inner training labels are used only
to form the cross-fitted residual target and stack fit. Outer validation labels
are evaluation-only. No QRAM, hardware, or hidden data source is assumed.

## 25. Reproducibility requirements

Commit this protocol, config, launcher, tests, interaction/channel audits,
inner audits, seed metrics, summaries, paired interval, paper figures,
registry entries, source commit, and zero locked-data counters.

## 26. Main scientific risks

The interaction terms may overfit the small outer-training sample, reproduce
classical nonlinear stacking, or fail to add any fidelity-specific signal.
The candidate cannot pass on C06 improvement alone.

## 27. Main implementation risks

Risks include regularizing the intercept inconsistently, using validation
labels, fitting candidate/control maps with different columns, or silently
changing the ridge penalty. The launcher fails closed on these conditions.

## 28. Minimum publishable result

A complete negative determines whether nonlinear expert interactions add
anything beyond linear stacking and a matched classical nonlinear control. A
positive requires every threshold, safety, control, integrity, statistical,
and resource condition.

## 29. Recommended first experiment

Run the complete q=4/6/8 campaign with q=8 primary and TWO-RBF-08-NL as the
matched control. Do not run Gate 6.

## 30. Final assessment

NIFRK is an explicit, bounded extension of D043 that tests a measurable
interaction mechanism while preserving the strict classical-control boundary.

Current conclusion: **Proceed only after reproduction**.
