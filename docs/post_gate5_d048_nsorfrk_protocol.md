# D048: Nested-Shrinkage Orthogonalized Fidelity-RBF Kernel

Protocol: P016  
Status: accepted for one bounded development-only campaign  
Date: 2026-07-15

## 1. Research problem

Can training-only selection of a small correction-shrinkage grid improve the
D046 q=8 orthogonalized fidelity result without reopening the rejected
multi-scale stack?

## 2. Mathematical formulation

For each outer fold, let `e` be the cross-fitted C06 residual on outer-training
rows. Inner grouped OOF predictions define `r25_8` and `e2=e-r25_8`. Fit the
candidate second-stage fidelity prediction `F_8(e2)` and matched control
`R50_8(e2)`. For each method `m`, select

`lambda_m = argmin_{lambda in {0.05,0.10,0.15}} ||e - lambda*(r25_8+s_m)||_2^2`

on inner-training OOF rows, with ties resolved by the smallest grid value. The
selected value scales the complete two-stage correction. The outer prediction is

`f_m(x)=inverse_scale[b_C06(x)+lambda_m*(r25_8(x)+s_m(x))]`.

The candidate uses `s_A=F_8(e2)` and the control uses `s_C=R50_8(e2)`.

## 3. Definitions and assumptions

Only q=8 and one projection layer are allowed. Both channels use 256
deterministic landmarks and ridge alpha=1.0. Candidate and control receive the
same three shrinkage values, tie rule, inner folds, seeds, data, and selection
budget. The C06 safety head is unchanged.

## 4. Scientific status of claims

The shrinkage grid and nested selection rule are design assumptions. The claim
that fixed-shrinkage amplitude limited D046 is an empirical hypothesis. Any
positive result is development-only surrogate evidence, not a NASA, mission,
hardware, quantum-advantage, Gate 5, or Gate 6 claim.

## 5. Closest prior method

D046 used q=8 orthogonalization with fixed lambda=0.10 and reached 5.80% over
C06 but only 4.65% over the matched control. D047 showed that q=4/6/8 stacking
was harmful. D048 therefore changes only the training-only shrinkage selection
and retains q=8.

## 6. Reproduction plan

Reproduce C06 cross-fitting, q=8 inner OOF RBF-0.25, and the common `e2`.
Generate inner OOF q=8 fidelity and RBF-0.50 second-stage predictions. Select
candidate and control shrinkage independently from the fixed grid using only
outer-training OOF rows. Refit both outer channels, apply the selected values
to outer validation rows, and score.

## 7. Reproduction success criteria

All 39,000 development rows, five outer folds, four inner grouped folds, q=8,
and 20 seeds must complete. Every selection row must identify one grid value,
the candidate/control grid must match, and validation-outcome, locked-data,
calibration, and final-test reads must be zero.

## 8. Proposed modification

Replace D046's fixed final shrinkage with a three-value nested training-only
selection for both q=8 candidate and matched control. No q, circuit, channel,
threshold, split, seed, or data boundary changes.

## 9. Proposed mechanism

Residual corrections can be over-amplified or under-amplified even when their
direction is useful. Selecting amplitude on inner OOF rows may reduce this
calibration error. Equal candidate/control selection budgets prevent a tuning
advantage from being attributed to fidelity.

## 10. Main hypothesis

Under the frozen development protocol, NSORFRK-08 will improve pooled OOF NRMSE
by at least 5% versus C06, preserve safety metrics, and improve NRMSE by at
least 5% versus NSO-TWO-RBF-08.

## 11. Falsification criteria

Reject if either 5% threshold, paired interval, safety metric, grid audit,
nested-selection audit, numerical check, or data boundary fails. A complete
integrity-valid failure is a scientific negative; an incomplete or leaked run
is a technical stop.

## 12. Candidate theorem or proposition

The finite grid argmin exists because the grid is nonempty and finite. Each
channel prediction is finite under the existing ridge and PSD checks. This
establishes selection well-definedness, not predictive superiority.

## 13. Proof strategy

Evaluate the declared finite objective for each grid value, choose the first
minimum in ascending order, and fail closed on non-finite values. The nested
split ensures the objective cannot use outer validation outcomes.

## 14. Counterexample search

Test zero residual, zero second-stage channel, equal grid losses, constant
predictions, non-finite values, and identical candidate/control channels. Verify
the tie rule chooses 0.05 and that candidate/control receive the same grid.

## 15. Experimental design

Use five grouped outer folds, 1,024 training rows per fold, four inner grouped
folds, q=8, 20 seeds, one entangling layer, 256 landmarks, alpha=1.0, and grid
`{0.05,0.10,0.15}`. The primary endpoint is NSORFRK-08.

## 16. Classical baselines

C06 is the frozen primary baseline. NSO-TWO-RBF-08 uses the identical q=8
orthogonalized stages and independently selects the same grid for the RBF-0.50
second-stage channel.

## 17. Quantum baselines

D034-D047 remain immutable references. The q=8 fidelity channel is an exact
statevector simulation and classically simulable in this regime. No quantum
advantage claim is possible.

## 18. Ablation studies

The grid, q, and stage order are fixed. The fixed-lambda D046 result is an
immutable historical comparison, not a post-outcome rerun. No additional grid,
q, or lambda is added after results are observed.

## 19. Statistical analysis

Report all 20 seed-pooled OOF NRMSE, MAE, regret, infeasible selection, Brier,
AUROC, recall, means, standard deviations, paired 95% bootstrap interval, and
selected-lambda counts for candidate and control.

## 20. Resource analysis

Record inner grid evaluations, q=8 channel fits, CPU time, wall time, peak
working set, free disk, and decoding on the recorded i9-13900HX/32 GiB/RTX
4060 CPU-only laptop. GPU execution is prohibited.

## 21. Noise analysis

Finite-shot, hardware-noise, and device-specific tests remain deferred. Exact
statevector evidence cannot establish noisy-hardware robustness.

## 22. Scaling analysis

Report only the declared three-point shrinkage grid and q=8 endpoint. Do not
infer asymptotic scaling from one q or three amplitude values.

## 23. Classical-simulability analysis

All features, fidelity values, RBF values, residual subtraction, grid scoring,
and ridge fits are classically simulable in the tested regime. Any positive
result is a hybrid-surrogate result.

## 24. Data-access cost

All inputs are classical development rows. Inner OOF predictions determine the
target and shrinkage selection. Outer validation outcomes are evaluation-only;
no QRAM, hidden source, calibration row, or final-test row is assumed.

## 25. Reproducibility requirements

Commit this protocol, config, launcher, tests, result JSON/CSV files, selection
and channel audits, paired interval, figures, registry entries, source commit,
and zero locked-data counters.

## 26. Main scientific risks

The grid may select noise, the control may receive equal or greater benefit,
and D046's near-threshold difference may not be stable under nested selection.
The three values do not support broad hyperparameter conclusions.

## 27. Main implementation risks

Risks include using outer validation outcomes in lambda selection, applying a
selected value to the wrong model, changing tie order, or using a grid value
outside the contract. The launcher fails closed on these cases.

## 28. Minimum publishable result

A complete negative determines whether training-only amplitude selection helps
the narrow q=8 residualized endpoint. A positive requires all threshold,
safety, control, integrity, statistical, and resource rules.

## 29. Recommended first experiment

Run NSORFRK-08 and NSO-TWO-RBF-08 with the fixed grid. Do not run Gate 6.

## 30. Final assessment

NSORFRK is the narrowest next test after D047: it keeps the only promising q=8
mechanism and changes one training-only amplitude decision without reopening
multi-scale stacking.

Current conclusion: **Proceed only after reproduction**.
