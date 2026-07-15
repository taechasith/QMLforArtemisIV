# D042: Adaptive-Gated Error-Conditioned Fidelity-RBF Kernel

Protocol: P010
Status: accepted for one bounded development-only campaign
Date: 2026-07-15

## 1. Research problem

Can an outcome-blind regime gate use the frozen C06 feasibility prediction to
apply more fidelity correction where the baseline predicts lower feasibility,
while outperforming both C06 and an identically gated two-RBF control?

## 2. Mathematical formulation

For an outer fold, let `x` be the standardized task input, `b(x)` the frozen
outer-fold C06 standardized cost prediction, and `p(x)` the C06 feasibility
probability from its unchanged outer-fold safety head. Define the fixed gate

`eta(x) = 0.25 + 0.50 * (1 - p(x))`.

Let `z_q(x)` be the D039 error-conditioned task-aligned score in `R^q`. Let
`delta_F,q(x)`, `delta_R25,q(x)`, and `delta_R50,q(x)` be ridge residual
corrections fit only on the outer-training fold using the same cross-fitted
C06 residual target. With `lambda=0.10`, AGEFRK predicts

`f_A,q(x) = inverse_scale[b(x) + lambda * (eta(x)*delta_F,q(x) +
(1-eta(x))*delta_R25,q(x))]`.

The matched classical control is

`f_CC,q(x) = inverse_scale[b(x) + lambda * (eta(x)*delta_R25,q(x) +
(1-eta(x))*delta_R50,q(x))]`.

For a channel feature matrix `Phi`, coefficients solve the training-only ridge
objective

`a = argmin_a ||e - Phi*a||_2^2 + alpha ||a||_2^2`,

where `e_i = y_i - b_inner(x_i)` is the cross-fitted C06 residual. The primary
endpoint is q=8, with the same C06 safety head used for all methods.

## 3. Definitions and assumptions

The input space is the frozen development feature contract plus the q
compressed feature vector and C06 baseline conditioning feature. The output is
the standardized physics-residual cost, decoded to the original cost units.
The data distribution is the fixed grouped development campaign; no
calibration or final-test row is part of `P_development`. Model parameters are
the ridge coefficients and fixed projection/channel parameters. `q` is 4, 6,
or 8; one entangling layer, 256 deterministic landmarks, alpha=1.0, and
lambda=0.10 are fixed.

The gate is a design assumption, not a learned causal rule. It is computed
from predictions only and is not allowed to inspect validation outcomes,
validation feasibility labels, or final-test data. The gate endpoints 0.25 and
0.75 are fixed before fitting and are not selected after outcomes.

## 4. Scientific status of claims

The ridge objective and the row-wise mixture identity are established algebraic
facts. A nonnegative weighted sum of PSD channel kernels is PSD by the
quadratic-form definition. The claim that low C06 feasibility probability
identifies a regime where the fidelity channel is more useful is an empirical
hypothesis. Any improvement is a development-only empirical result. No NASA,
mission, hardware, quantum-advantage, Gate 5, or Gate 6 claim is authorized.

## 5. Closest prior method

The closest method is D041 HEFRK, which used fixed eta values for the same
fidelity and RBF channels. D042 changes only the mixture from a fixed scalar to
a predeclared prediction-only gate and gives the same gate to the classical
control. D041 and all earlier evidence remain immutable.

## 6. Reproduction plan

Reproduce the five grouped outer folds, D039 inner C06 cross-fitting, C06 outer
cost and safety predictions, error-conditioned projection, fidelity channel,
and two RBF channels. Compute eta from outer C06 probabilities only. Evaluate
AGEFRK and the identically gated two-RBF control on every outer validation row
for q=4, 6, and 8, across the frozen 20 seeds.

## 7. Reproduction success criteria

All 39,000 development rows, five outer folds, four inner folds, q=4/6/8,
and 20 seeds must complete. Gate audits must show finite eta in [0.25,0.75],
zero validation-outcome use, zero group overlap, and no locked-data reads.
The candidate and control must have identical row-wise eta values.

## 8. Proposed modification

Replace D041's fixed eta by the declared function of the frozen C06
feasibility probability. No kernel family, feature map, residual target,
shrinkage, seed, split, threshold, or safety rule changes.

## 9. Proposed mechanism

If the C06 feasibility head separates regimes with different residual
structure, a fixed gate may underweight fidelity correction in difficult
regions. The adaptive gate tests this mechanism directly. The identically
gated two-RBF control tests whether any gain is explained by classical
bandwidth mixing rather than the fidelity channel.

## 10. Main hypothesis

AGEFRK-08-ADAPT will improve pooled OOF NRMSE by at least 5 percent versus C06,
preserve feasibility-constrained regret and infeasible selection, and beat
TWO-RBF-08-ADAPT by at least 5 percent.

## 11. Falsification criteria

Reject the hypothesis if any primary threshold, paired interval, safety
metric, classical-control comparison, gate equality, outcome-isolation audit,
fold/seed check, numerical check, or resource boundary fails. A negative is
valid only when the endpoint is complete and all integrity checks pass.

## 12. Candidate theorem or proposition

For fixed channel predictors and `eta(x) in [0,1]`, AGEFRK is a pointwise
convex combination of the fidelity and RBF corrections. If both channel kernel
matrices are PSD, each fixed-x mixture kernel is PSD when the same nonnegative
weights are used in its kernel construction.

## 13. Proof strategy

For each fixed x, the prediction identity follows by distributivity. For a
fixed scalar eta, the PSD claim follows from `v^T(eta*K_F+(1-eta)*K_R)v` being
the sum of nonnegative quadratic forms. The implementation uses the gate for
prediction mixing, so the predictive result is algebraically valid; this does
not prove generalization or superiority.

## 14. Counterexample search

Check p=0, p=1, p=0.5, identical channels, zero channels, opposite channels,
constant channels, identical RBF bandwidths, and finite input arrays. Verify
that eta is monotone decreasing in p, remains bounded, and is identical for
candidate and control. Reject NaN, infinity, shape mismatch, or any outcome
access.

## 15. Experimental design

Use five grouped outer folds, 1,024 training rows per fold, four inner grouped
folds, q=4/6/8, one entangling layer, 256 landmarks, alpha=1.0, lambda=0.10,
20 seeds, all outer validation rows, and the unchanged C06 safety head. The
single primary endpoint is q=8; q=4 and q=6 are fixed scaling ablations.

## 16. Classical baselines

C06 is the primary baseline. TWO-RBF-q-ADAPT uses the same scores, landmarks,
ridge, residual target, shrinkage, C06 probabilities, and row-wise eta while
mixing RBF multipliers 0.25 and 0.50.

## 17. Quantum baselines

D034-D041 remain immutable historical references. The fidelity channel uses
the exact statevector kernel at q<=8 and is efficiently classically
simulable. Therefore D042 cannot establish quantum advantage.

## 18. Ablation studies

q=4 and q=6 are declared ablations. The q=8 classical control is the required
mechanism ablation. No alternative gate, threshold, bandwidth, or weight may
be selected after observing results.

## 19. Statistical analysis

Report all 20 seed-pooled OOF NRMSE, MAE, regret, infeasible selection, Brier,
AUROC, and recall values. Report means, sample standard deviations, and the
paired 95% bootstrap interval for AGEFRK-08-ADAPT minus C06. Apply the same
fixed decision checks to TWO-RBF-08-ADAPT.

## 20. Resource analysis

Record q, gate range and distribution, fidelity/RBF evaluations, landmarks,
statevector dimensions, CPU time, wall time, peak working set, free disk,
state preparation, and classical decoding. The reference limit is the
recorded i9-13900HX/32 GiB/RTX 4060 laptop with CPU-only execution.

## 21. Noise analysis

Finite-shot and hardware-noise tests remain deferred. Exact statevector
evidence at q<=8 cannot support a noisy-hardware or quantum-advantage claim.

## 22. Scaling analysis

Report q sensitivity and the observed eta distribution. Do not infer
asymptotic scaling from q=4/6/8 or from a single gate formula.

## 23. Classical-simulability analysis

The fidelity channel, RBF channels, projection, gate, and ridge solve are
classically simulable in this tested regime. Any positive result is a
hybrid-surrogate result and must not be labeled quantum advantage.

## 24. Data-access cost

All inputs are classical development rows. Include feature construction,
cross-fitted C06 fitting, outer safety prediction, projection, channel fits,
gate calculation, mixture, shrinkage, and decoding. No QRAM, quantum memory,
hardware, or hidden data source is assumed.

## 25. Reproducibility requirements

Commit this protocol, config, launcher, contract tests, gate/channel/projection
audits, inner audits, seed metrics, summaries, paired interval, paper-ready
figures, registry entries, source commit, and zero locked-data counters.

## 26. Main scientific risks

The C06 feasibility probability may be a poor proxy for residual regime, the
adaptive gate may merely reproduce classical mixture behavior, and the fixed
fidelity channel may remain redundant. A lower NRMSE than C06 alone is not
enough if the matched classical control also improves.

## 27. Main implementation risks

The main risks are accidentally using validation labels in eta, applying
different eta arrays to candidate and control, fitting channels with leakage,
or silently tuning gate endpoints. The launcher fails closed on these cases.

## 28. Minimum publishable result

A complete valid negative identifies whether outcome-blind feasibility gating
adds useful information beyond fixed fusion and classical bandwidth mixing. A
positive requires all threshold, safety, classical-control, statistical,
integrity, and resource conditions.

## 29. Recommended first experiment

Run the complete declared q=4/6/8 campaign with q=8 as the only primary
endpoint and TWO-RBF-08-ADAPT as the matched control. Do not run Gate 6.

## 30. Final assessment

AGEFRK is mathematically explicit, directly motivated by the D041 negative,
and bounded for the reference laptop because it reuses the D041 channels and
adds only vectorized row-wise gating.

Current conclusion: **Proceed only after reproduction**.
