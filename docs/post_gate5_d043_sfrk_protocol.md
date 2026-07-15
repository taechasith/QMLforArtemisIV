# D043: Cross-Fitted Residual Fidelity-RBF Stack

Protocol: P011
Status: accepted for one bounded development-only campaign
Date: 2026-07-15

## 1. Research problem

Can a convex residual stack learn from training-only out-of-fold expert
predictions whether the D041 fidelity correction or an RBF correction is more
useful, while beating a matched two-RBF stack?

## 2. Mathematical formulation

For an outer fold, let `b(x)` be the outer C06 standardized cost prediction.
The cross-fitted C06 residual target is `e_i = y_i-b_inner(x_i)` for outer
training rows. Let `u_F`, `u_R25`, and `u_R50` be inner out-of-fold predictions
of the fidelity, RBF-0.25, and RBF-0.50 residual channels, respectively.

For two experts `u` and `v`, define the bounded convex stacking weight

`w(u,v) = clip(sum_i (u_i-v_i)(e_i-v_i) /
sum_i (u_i-v_i)^2, 0, 1)`.

The candidate weight is `w_A=w(u_F,u_R25)`. After fitting the channels on all
outer-training rows, the outer-validation prediction is

`f_A(x) = inverse_scale[b(x) + 0.10*(w_A*delta_F(x) +
(1-w_A)*delta_R25(x))]`.

The matched classical control uses `w_C=w(u_R25,u_R50)` and

`f_C(x) = inverse_scale[b(x) + 0.10*(w_C*delta_R25(x) +
(1-w_C)*delta_R50(x))]`.

The stacking objective is the squared residual error on inner out-of-fold
predictions; no outer-validation outcome is used to calculate either weight.

## 3. Definitions and assumptions

Inputs are the frozen development features, q compressed features, and C06
conditioning feature. Outputs are standardized and decoded physics-residual
costs. q is 4, 6, or 8; one entangling layer, 256 deterministic landmarks,
alpha=1.0, and lambda=0.10 are fixed. The four inner folds are grouped and
are used only inside each outer training fold. Weight clipping is part of the
model definition, not post-outcome correction.

## 4. Scientific status of claims

The least-squares scalar weight formula is a new derivation from a one-
parameter convex mixture; its validity follows from differentiating the
quadratic objective and clipping the unconstrained minimizer. The claim that
inner out-of-fold residuals reveal stable expert specialization is an
empirical hypothesis. A positive result is development-only. No NASA, mission,
hardware, quantum-advantage, Gate 5, or Gate 6 claim is authorized.

## 5. Closest prior method

The closest methods are D041 fixed fusion and D042 outcome-blind adaptive
fusion. D043 replaces both fixed or proxy-based weights with a training-only
cross-fitted convex stack. The matched control applies the identical stacking
algorithm to two classical RBF experts.

## 6. Reproduction plan

Within each outer fold and q/seed, reproduce the D039 C06 conditioning. For
each inner grouped fold, fit projection and all required channels on inner-fit
rows, predict its held-out inner rows, and assemble out-of-fold expert
predictions. Fit the two convex weights from those arrays. Refit each channel
on all outer-training rows, apply the frozen weights to outer validation rows,
and score against C06 and the matched control.

## 7. Reproduction success criteria

All five outer folds, four inner folds, q=4/6/8, and 20 seeds must complete.
Each inner holdout must have disjoint groups from its fit rows. Every weight
must be finite and in [0,1]; channel and weight audits must report zero outer
validation-outcome use and zero locked-data reads.

## 8. Proposed modification

Fit a bounded convex residual-mixture weight from inner grouped out-of-fold
channel predictions on outer-training rows. The quantum candidate uses the
fidelity/RBF-0.25 pair; the control uses RBF-0.25/RBF-0.50.

## 9. Proposed mechanism

D041 and D042 show a stable but subthreshold gain from combining channels. A
single fixed mixture may be wrong for the data distribution, while a C06
feasibility proxy may not identify residual regimes. Cross-fitted expert
errors provide a direct training-only estimate of which channel is useful,
without exposing outer validation outcomes.

## 10. Main hypothesis

SFRK-08-CV will improve pooled OOF NRMSE by at least 5 percent versus C06,
preserve feasibility-constrained regret and infeasible selection, and beat
TWO-RBF-08-CV by at least 5 percent.

## 11. Falsification criteria

Reject if any primary threshold, paired interval, safety metric, classical
control comparison, inner group separation, weight-bound, residual-target,
or data-boundary check fails. A complete failure is a valid negative; an
incomplete or leaked fit is a technical stop.

## 12. Candidate theorem or proposition

For non-identical expert predictions u and v, the unconstrained minimizer of
`sum_i(e_i-[w*u_i+(1-w)*v_i])^2` is the ratio in Section 2. Clipping that
minimizer gives the global minimizer over the interval [0,1].

## 13. Proof strategy

Set `d_i=u_i-v_i` and `r_i=e_i-v_i`. The objective is
`sum_i(r_i-w*d_i)^2`, a convex quadratic with derivative
`-2 sum_i d_i(r_i-w*d_i)`. If `sum_i d_i^2>0`, the stationary point is the
ratio; projection onto a closed interval is the constrained minimizer. If the
denominator is zero, use the predeclared weight 0.5. This proves optimization
validity, not predictive superiority.

## 14. Counterexample search

Test identical experts, zero experts, opposite experts, constant residuals,
zero denominator, unconstrained weights below 0 or above 1, and exact expert
agreement. Verify the bounded solution, finite predictions, and that the
candidate/control use separate expert pairs but the same algorithm.

## 15. Experimental design

Use five grouped outer folds, 1,024 training rows per outer fold, four inner
grouped folds, q=4/6/8, one entangling layer, 256 landmarks, alpha=1.0,
lambda=0.10, 20 seeds, all outer validation rows, and unchanged C06 safety.
The primary endpoint is q=8; q=4 and q=6 are fixed ablations.

## 16. Classical baselines

C06 is the primary baseline. TWO-RBF-q-CV is the matched classical stack with
inner out-of-fold RBF-0.25 and RBF-0.50 experts, the same folds, seeds,
residual target, projection, ridge, and clipping rule.

## 17. Quantum baselines

D034-D042 remain immutable historical references. The exact statevector
fidelity channel at q<=8 is classically simulable. No quantum advantage can be
inferred from this experiment.

## 18. Ablation studies

q=4 and q=6 are fixed scaling ablations. The two-RBF stack is the required
mechanism ablation. There is no post-outcome weight, q, kernel, or threshold
selection.

## 19. Statistical analysis

Report all 20 seed-pooled OOF NRMSE, MAE, regret, infeasible selection, Brier,
AUROC, and recall values, with means, sample standard deviations, and the
paired 95% bootstrap interval for SFRK-08-CV minus C06. Report the full
outer-fold/seed/q weight distribution.

## 20. Resource analysis

Record inner and outer channel fits, q, landmarks, weights, channel
evaluations, CPU time, wall time, peak working set, free disk, statevector
dimension, and classical decoding. The reference boundary is the recorded
i9-13900HX/32 GiB/RTX 4060 laptop with CPU-only execution.

## 21. Noise analysis

Finite-shot and hardware-noise tests remain deferred. Exact statevector
results in this regime cannot support a noisy-hardware or quantum-advantage
claim.

## 22. Scaling analysis

Report q sensitivity and fitted weight distributions only. Do not infer
asymptotic scaling from q=4/6/8 or from one stacking rule.

## 23. Classical-simulability analysis

The projections, statevector fidelity, RBF channels, inner stack, and ridge
solve are classically simulable. A positive result is a hybrid-surrogate
result, not quantum advantage.

## 24. Data-access cost

All data are classical development rows. Include inner channel fits, outer
channel fits, C06 cross-fitting, stacking, shrinkage, safety prediction, and
decoding. Outer validation labels are read only by the scoring function.

## 25. Reproducibility requirements

Commit this protocol, config, launcher, tests, inner stack audits, channel and
weight audits, seed metrics, summaries, paired interval, paper-ready figures,
registry entries, source commit, and zero locked-data counters.

## 26. Main scientific risks

The inner sample is small, expert weights may be unstable, and cross-fitted
stacking may reproduce a classical RBF gain rather than add fidelity-specific
information. C06 improvement alone is insufficient.

## 27. Main implementation risks

The main risks are using an outer validation label in a weight, fitting an
inner channel with holdout rows, mixing expert pairs between candidate and
control, or silently changing the clipping rule. The launcher fails closed.

## 28. Minimum publishable result

A complete negative identifies whether training-only expert specialization
adds anything beyond fixed and feasibility-gated fusion. A positive requires
all threshold, safety, control, integrity, statistical, and resource rules.

## 29. Recommended first experiment

Run the complete q=4/6/8 campaign with q=8 as the only primary endpoint and
TWO-RBF-08-CV as the matched control. Do not run Gate 6.

## 30. Final assessment

SFRK is mathematically explicit, motivated by D041/D042, and directly tests
whether the observed subthreshold fusion signal can be converted into a
training-only expert-selection rule without validation leakage.

Current conclusion: **Proceed only after reproduction**.
