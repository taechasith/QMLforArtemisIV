# D041: Hybrid Error-Conditioned Fidelity-RBF Residual Kernel

Protocol: P009
Status: accepted for one bounded development-only campaign
Date: 2026-07-15

## 1. Research problem

Can a fixed mixture of the D039 error-conditioned global-fidelity correction
and an RBF correction retain complementary residual structure, while beating a
matched two-bandwidth classical RBF mixture?

## 2. Mathematical formulation

For each outer fold, let `b_f(x)` be the frozen C06 cost prediction and let
`delta_F`, `delta_R25`, and `delta_R50` be residual corrections fit on the same
cross-fitted C06 residual target and D039 error-conditioned scores. For
`eta in {0.25, 0.50, 0.75}`, define the hybrid candidate

`f_H(x) = b_f(x) + 0.10 * [eta delta_F(x) + (1-eta) delta_R25(x)]`.

The matched classical control is

`f_CC(x) = b_f(x) + 0.10 * [eta delta_R25(x) + (1-eta) delta_R50(x)]`.

The C06 feasibility head remains unchanged. Eta `0.50` at q=8 is the primary
endpoint; eta values and q values are fixed ablations, not post-outcome
selection.

## 3. Definitions and assumptions

`q` is 4, 6, or 8; the fidelity channel has one entangling layer; each channel
uses 256 deterministic landmarks, fixed ridge alpha, and D039's
error-conditioned PLS scores. RBF gamma multipliers are 0.25 and 0.50. Lambda
is fixed at 0.10. Only development rows are allowed.

## 4. Scientific status of claims

Convex mixtures of valid residual predictors are a design construction. The
claim that the channels have complementary errors is an empirical hypothesis.
The fidelity and RBF kernel PSD properties are established for their stated
feature maps. No NASA, mission, hardware, quantum-advantage, Gate 5, or Gate 6
claim is authorized.

## 5. Closest prior method

The closest method is D039 EC-GFRK, which used only the fidelity correction,
and D037/D040, which tested fixed shrinkage and centering. D041 adds a fixed
RBF residual channel and a matched two-bandwidth classical control. D039 and
D040 remain immutable.

## 6. Reproduction plan

Reproduce D039's inner C06 cross-fitting, outer C06 prediction, and
error-conditioned PLS scores. Fit one fidelity correction and RBF corrections
at gamma 0.25 and 0.50 on each outer-training fold. Combine predictions using
the fixed eta grid and compare each endpoint with C06 and the same-weight
two-RBF control.

## 7. Reproduction success criteria

All five outer folds, four inner folds, q=4/6/8, eta=0.25/0.50/0.75, and 20
seeds must complete. Both channels must use identical residual targets and
landmarks where declared, mixture weights must match their control, groups
must be disjoint, and locked-data counters must remain zero.

## 8. Proposed modification

Add one fixed RBF correction channel to the D039 fidelity correction and mix
the two corrections before adding them to C06. Give the classical control two
RBF channels at fixed gamma multipliers 0.25 and 0.50 with the same eta values.

## 9. Proposed mechanism

The D039 result shows useful fidelity residual signal but a near-matching RBF
control. If the two correction channels make different errors, late fusion can
reduce variance or preserve complementary directions. The two-RBF control
tests whether any benefit is merely classical multi-bandwidth ensembling.

## 10. Main hypothesis

HEFRK-08-E050 will reduce pooled OOF NRMSE by at least 5 percent versus C06,
preserve selection safety, and beat TWO-RBF-08-E050 by at least 5 percent.

## 11. Falsification criteria

Reject if any primary improvement, paired interval, safety metric, two-RBF
control comparison, mixture-weight audit, residual-target audit, or fold/seed
integrity check fails.

## 12. Candidate theorem or proposition

For fixed predictors and `eta in [0,1]`, the hybrid correction is a convex
combination of the two channel corrections. If both channel kernels are PSD,
the corresponding weighted sum kernel is PSD for nonnegative weights.

## 13. Proof strategy

For any coefficient vector `a`, the quadratic form of
`eta K_F + (1-eta)K_R` is the same weighted sum of two nonnegative quadratic
forms, hence nonnegative. The prediction identity follows by linearity. This
proves algebraic validity, not predictive superiority.

## 14. Counterexample search

Test eta 0, eta 1, identical channel corrections, zero corrections, opposite
corrections, constant corrections, identical RBF bandwidths, and finite
predictions. Verify that eta is applied identically to the candidate and
two-RBF control and that eta=1 reproduces the fidelity channel correction.

## 15. Experimental design

Use five outer grouped folds, 1,024 training rows per fold, four inner grouped
folds, q=4/6/8, eta=0.25/0.50/0.75, one entangling layer, lambda=0.10, 20
seeds, all outer validation rows, and the unchanged C06 safety head. The
primary is q=8, eta=0.50.

## 16. Classical baselines

C06 is the primary baseline. TWO-RBF-q-E uses the same error-conditioned PLS
scores, landmarks, ridge, residual target, eta, and lambda while mixing RBF
gamma 0.25 and 0.50 corrections.

## 17. Quantum baselines

D034 through D040 remain immutable historical references. The exact statevector
fidelity channel at q<=8 is classically simulable, so no quantum advantage
claim is possible from this protocol.

## 18. Ablation studies

q and eta are fixed ablations. The eta grid is declared before development
payload access. The two RBF gamma channels are a matched classical ablation;
no other bandwidth or mixture is selected after outcomes.

## 19. Statistical analysis

Report all 20 seed-pooled OOF NRMSE, MAE, regret, infeasible selection, Brier,
AUROC, and recall values. Report means, sample standard deviations, and paired
95% bootstrap intervals for HEFRK-08-E050 minus C06. Apply the same fixed
decision rules to the TWO-RBF-08-E050 control.

## 20. Resource analysis

Record q, eta, circuit depth, two-qubit gates, statevector dimension, landmarks,
RBF bandwidths, channel evaluations, wall time, CPU time, peak working set,
free disk, state preparation, and classical decoding.

## 21. Noise analysis

Finite-shot and hardware-noise tests remain deferred unless the exact
statevector primary passes. Noise cannot rescue a negative exact endpoint.

## 22. Scaling analysis

Report q and eta sensitivity only within the declared bounded grid. Do not
infer asymptotic quantum scaling from three q values or three mixture weights.

## 23. Classical-simulability analysis

The fidelity channel, RBF channels, and their mixtures are classically
simulable at q<=8. A positive result would be a hybrid-surrogate result, not
quantum advantage.

## 24. Data-access cost

All data are classical development rows. Include inner C06 fitting, outer C06
fitting, error-conditioned PLS, fidelity and RBF channel fitting, mixture,
shrinkage, and decoding. No QRAM or quantum-memory assumption is made.

## 25. Reproducibility requirements

Commit the protocol, config, launcher, mixture/channel audits, inner/projection
audits, seed metrics, summaries, paired interval, figures, registry rows,
source commit, and zero locked-data counters.

## 26. Main scientific risks

The fidelity correction may be redundant with RBF, the two-RBF control may be
stronger, and fixed fusion may not improve either endpoint. A lower NRMSE than
C06 alone is not enough if the matched control also improves.

## 27. Main implementation risks

The risks are applying different eta weights, using different residual targets,
fitting the second RBF with validation information, or treating the best eta
as the primary endpoint. The launcher fails closed on these conditions.

## 28. Minimum publishable result

A complete valid negative identifies whether fidelity and RBF residual channels
are complementary beyond two classical bandwidths. A positive requires every
C06, two-RBF, safety, integrity, and resource condition.

## 29. Recommended first experiment

Run all declared q and eta values with q=8, eta=0.50 as the single primary
endpoint and TWO-RBF-08-E050 as the matched control.

## 30. Final assessment

HEFRK is mathematically explicit, directly motivated by D039/D040, and bounded
for the reference laptop because the extra RBF bandwidth reuses the same small
landmark workload. Its result is unresolved until the source-bound campaign
executes.

Current conclusion: **Proceed only after reproduction**.
