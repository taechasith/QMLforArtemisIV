# D047: Orthogonalized Multi-Scale Fidelity Residual Kernel

Protocol: P015  
Status: accepted for one bounded development-only campaign  
Date: 2026-07-15

## 1. Research problem

After the D046 q=8 fidelity channel cleared C06 but missed the matched
classical threshold, do q=4 and q=6 fidelity channels add complementary
information when all channels share one q=8 classical first-stage correction?

## 2. Mathematical formulation

For an outer fold, let `e` be the cross-fitted C06 residual on outer-training
rows. Fit the shared first-stage q=8 RBF correction and obtain inner grouped
out-of-fold predictions `r25_8_OOF`. Define `e2 = e - r25_8_OOF`. Inner OOF
second-stage predictions produce the fixed designs

`Psi_A = [1, F_4(e2), F_6(e2), F_8(e2)]`

and

`Psi_C = [1, R50_4(e2), R50_6(e2), R50_8(e2)]`.

The coefficients solve `beta = argmin ||e2-Psi beta||^2 +
0.001||beta_without_intercept||^2`. On outer validation rows, both methods use
the same `r25_8` and final prediction

`inverse_scale[b_C06(x) + 0.10 * (r25_8(x) + Psi(x) beta)]`.

## 3. Definitions and assumptions

`F_q` is the one-layer task-aligned q-qubit fidelity channel and `R50_q` is
the matched RBF-0.50 channel. All channels use 256 deterministic landmarks,
ridge alpha=1.0, and the same projected classical input. The second-stage
target is computed only from inner OOF q=8 RBF-0.25 predictions. The C06
safety head is retained unchanged.

## 4. Scientific status of claims

The common residual target, feature order, and ridge stack are design
definitions. Cross-q fidelity complementarity after the shared correction is
an empirical hypothesis. Any positive result is development-only surrogate
evidence and cannot support NASA, mission, hardware, quantum-advantage, Gate
5, or Gate 6 claims.

## 5. Closest prior method

D046 tested one q at a time after q-specific RBF residualization and reached a
5.80% C06 improvement but only 4.65% over its matched control. D047 keeps the
strongest common q=8 correction and tests a fixed cross-q second-stage stack.

## 6. Reproduction plan

Reproduce C06 cross-fitting for every outer fold and seed. Generate q=8 inner
OOF RBF-0.25 predictions and the common `e2`. In each inner grouped fold,
generate q=4/6/8 second-stage fidelity and RBF-0.50 predictions, fit the two
fixed four-column ridge stacks, refit all stages on outer-training rows, and
score outer validation rows.

## 7. Reproduction success criteria

All 39,000 development rows, five outer folds, four inner grouped folds, q=4,
6, 8, and 20 seeds must complete. Candidate and control must have four stack
columns, identical shared first-stage predictions, zero validation-outcome use,
zero group overlap, and zero locked-data or calibration/final-test reads.

## 8. Proposed modification

Replace D046's independent q endpoints with one shared q=8 RBF-0.25 stage and
a predeclared q=4/6/8 second-stage ridge stack. The control uses the same stack
and substitutes RBF-0.50 for fidelity.

## 9. Proposed mechanism

The mechanism is cross-q complementarity after common-signal removal. A
positive result would show that multiple fidelity scales explain residual
structure not reproduced by a matched multi-scale RBF stack, rather than merely
showing that one channel improves C06.

## 10. Main hypothesis

Under the frozen development protocol, OMFRK-ALL will improve pooled OOF NRMSE
by at least 5% versus C06, preserve safety metrics, and improve NRMSE by at
least 5% versus OM-TWO-RBF.

## 11. Falsification criteria

Reject if any threshold, paired interval, safety metric, stack shape, stage
order, numerical check, or data-boundary condition fails. A complete
integrity-valid failure is a scientific negative; an incomplete or leaked run
is a technical stop.

## 12. Candidate theorem or proposition

For fixed finite inner designs and positive ridge penalty, both four-column
stack coefficient systems have unique finite solutions when the channel values
are finite. This is an algebraic solvability claim, not a performance claim.

## 13. Proof strategy

The intercept is unregularized and each of the three channel coefficients has
positive ridge penalty. The resulting normal-equation matrix is positive
definite on the regularized subspace; the launcher additionally checks finite
inputs, coefficients, predictions, and exact design shapes.

## 14. Counterexample search

Test identical q channels, zero second-stage target, constant inputs,
rank-deficient stacks, one-feature projections, and near-zero RBF distance
scales. Verify exact zero `e2` when the shared q=8 OOF correction equals `e`,
equal candidate/control rows, and no validation outcome in stack fitting.

## 15. Experimental design

Use five grouped outer folds, 1,024 training rows per fold, four inner grouped
folds, q=4/6/8, 20 seeds, one entangling layer, 256 landmarks, alpha=1.0,
stack ridge=0.001, lambda=0.10, and the unchanged C06 safety head. OMFRK-ALL
is the sole primary endpoint; q-scale columns are fixed, not selected.

## 16. Classical baselines

C06 is the frozen primary baseline. OM-TWO-RBF has the identical shared q=8
RBF-0.25 stage and four-column second-stage stack using q=4/6/8 RBF-0.50
channels. It receives the same data, projections, landmarks, and ridge.

## 17. Quantum baselines

D034-D046 remain immutable references. The fidelity channels are exact
statevector simulations at q<=8 and are classically simulable. No quantum
advantage claim is possible.

## 18. Ablation studies

The q=4/6/8 columns and shared q=8 stage are fixed. No post-outcome q removal,
weight change, or channel ablation is permitted.

## 19. Statistical analysis

Report all 20 seed-pooled OOF NRMSE, MAE, regret, infeasible selection, Brier,
AUROC, recall, means, sample standard deviations, and the paired 95% bootstrap
interval for OMFRK-ALL minus C06. Report candidate-control difference and stack
coefficient audits.

## 20. Resource analysis

Record shared-stage fits, q-channel fits, four-column solves, CPU time, wall
time, peak working set, free disk, and decoding on the recorded
i9-13900HX/32 GiB/RTX 4060 CPU-only laptop. GPU execution is prohibited.

## 21. Noise analysis

Finite-shot, hardware-noise, and device-specific tests remain deferred. Exact
statevector results at q<=8 cannot establish hardware robustness.

## 22. Scaling analysis

Report only the declared q=4/6/8 stack and its resource audit. Do not infer
asymptotic scaling from three q values or one stack.

## 23. Classical-simulability analysis

All projected features, fidelity expectation values, RBF channels, residual
subtraction, and ridge stacks are classically simulable in the tested regime.
Any positive result is a hybrid-surrogate result.

## 24. Data-access cost

All inputs are classical development rows. Inner OOF q=8 RBF predictions form
the common second-stage target. Outer validation outcomes are evaluation-only;
no QRAM, hidden source, calibration row, or final-test row is assumed.

## 25. Reproducibility requirements

Commit this protocol, config, launcher, tests, raw result CSV/JSON files, shared
and second-stage audits, paired intervals, figures, registry entries, source
commit, and zero locked-data counters.

## 26. Main scientific risks

The q=4/6 channels may be redundant with q=8, the stack may overfit inner OOF
predictions, and any gain may be reproduced by the classical control. The
common target can also magnify estimation noise.

## 27. Main implementation risks

Risks include using q-specific rather than common q=8 residualization, fitting
stacks on outer validation outcomes, unequal controls, or post-outcome q
selection. The launcher fails closed on these cases.

## 28. Minimum publishable result

A complete negative determines whether cross-q fidelity complementarity remains
after shared classical correction. A positive requires every threshold,
safety, control, integrity, statistical, and resource rule.

## 29. Recommended first experiment

Run the declared OMFRK-ALL and OM-TWO-RBF endpoints. Do not run Gate 6.

## 30. Final assessment

OMFRK is the narrowest next test of the D046 signal: it adds only fixed cross-q
second-stage complementarity while preserving a common classical first stage.

Current conclusion: **Proceed only after reproduction**.
