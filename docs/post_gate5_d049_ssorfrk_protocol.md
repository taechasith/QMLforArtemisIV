# D049: Stage-Separated Orthogonalized Fidelity-RBF Kernel

Protocol: P017  
Status: accepted for one bounded development-only campaign  
Date: 2026-07-15

## 1. Research problem

After D048 selected the minimum gain for the complete correction, can the
shared classical q=8 correction remain fixed while only the unique second-stage
gain is calibrated fairly for fidelity and RBF control?

## 2. Mathematical formulation

Let `e` be the outer-training cross-fitted C06 residual. Inner grouped OOF
predictions define `r25_8` and `e2=e-r25_8`. For candidate `s_A=F_8(e2)` and
control `s_C=R50_8(e2)`, select

`g_m = argmin_{g in {0.05,0.10,0.15,0.20}} ||e-0.10*r25_8-g*s_m||_2^2`

with ties resolved by the smallest grid value. The outer predictions are

`f_m(x)=inverse_scale[b_C06(x)+0.10*r25_8(x)+g_m*s_m(x)]`.

## 3. Definitions and assumptions

Only q=8 and one projection layer are allowed. Both channels use 256
deterministic landmarks and ridge alpha=1.0. Candidate and control receive
the same second-stage gain grid, tie rule, inner folds, seeds, data, and
selection budget. The shared first-stage gain is fixed at 0.10.

## 4. Scientific status of claims

The stage-separated gain and grid are design assumptions. The claim that the
unique fidelity correction needs a different amplitude from the shared RBF
correction is an empirical hypothesis. Any positive result is development-only
surrogate evidence, not a NASA, mission, hardware, quantum-advantage, Gate 5,
or Gate 6 claim.

## 5. Closest prior method

D046 fixed 0.10 for the complete correction and was near the C06 threshold but
missed the classical-specific rule. D048 selected the complete correction gain
at 0.05 and weakened the endpoint. D049 keeps the shared gain fixed and tunes
only the second-stage gain.

## 6. Reproduction plan

Reproduce C06 cross-fitting, q=8 inner OOF RBF-0.25, and common `e2`. Generate
inner OOF q=8 fidelity and RBF-0.50 second-stage predictions. Select candidate
and control second-stage gains independently from the fixed grid using only
outer-training OOF rows. Refit outer channels and score outer validation rows.

## 7. Reproduction success criteria

All 39,000 development rows, five outer folds, four inner grouped folds, q=8,
and 20 seeds must complete. Every selection row must use shared gain exactly
0.10, one declared grid value, zero validation-outcome use, and zero locked,
calibration, or final-test reads.

## 8. Proposed modification

Replace D048's whole-correction shrinkage with fixed first-stage gain 0.10 and
a four-value second-stage gain selection. No q, circuit, channel, threshold,
split, seed, or data boundary changes.

## 9. Proposed mechanism

The shared RBF channel and unique fidelity channel can have different optimal
amplitudes. Separating the gains may preserve the common correction while
preventing the shared component from suppressing a useful fidelity residual.
Equal candidate/control grids prevent tuning asymmetry.

## 10. Main hypothesis

Under the frozen development protocol, SSORFRK-08 will improve pooled OOF NRMSE
by at least 5% versus C06, preserve safety metrics, and improve NRMSE by at
least 5% versus SSO-TWO-RBF-08.

## 11. Falsification criteria

Reject if either 5% threshold, paired interval, safety metric, fixed-shared-gain
audit, gain grid audit, nested-selection audit, numerical check, or data
boundary fails. A complete integrity-valid failure is a scientific negative;
an incomplete or leaked run is a technical stop.

## 12. Candidate theorem or proposition

The finite second-stage gain argmin exists for each outer fold and seed. The
channel solves remain finite under the existing ridge and PSD checks. This is
selection well-definedness, not predictive superiority.

## 13. Proof strategy

Evaluate the finite objective for every gain, choose the first minimum in
ascending order, and fail closed on non-finite values. The nested split keeps
outer validation outcomes outside gain selection.

## 14. Counterexample search

Test zero second-stage channels, equal gain losses, constant predictions,
non-finite values, identical candidate/control channels, and a residual exactly
explained by the fixed shared stage. Verify ties choose 0.05 and the shared
gain remains exactly 0.10.

## 15. Experimental design

Use five grouped outer folds, 1,024 training rows per fold, four inner grouped
folds, q=8, 20 seeds, one entangling layer, 256 landmarks, alpha=1.0, fixed
shared gain 0.10, and second-stage grid `{0.05,0.10,0.15,0.20}`.

## 16. Classical baselines

C06 is the frozen primary baseline. SSO-TWO-RBF-08 uses the identical q=8
orthogonalized stages, fixed shared gain, and independently selected RBF-0.50
second-stage gain from the same grid.

## 17. Quantum baselines

D034-D048 remain immutable references. The q=8 fidelity channel is an exact
statevector simulation and classically simulable in this regime. No quantum
advantage claim is possible.

## 18. Ablation studies

The fixed shared gain, q, grid, and stage order are fixed. D046 and D048 remain
historical immutable comparisons. No new gain grid or multi-scale ablation is
added after outcomes.

## 19. Statistical analysis

Report all 20 seed-pooled OOF NRMSE, MAE, regret, infeasible selection, Brier,
AUROC, recall, means, standard deviations, paired 95% bootstrap interval, and
selected second-stage gain counts for candidate and control.

## 20. Resource analysis

Record inner gain evaluations, q=8 channel fits, CPU time, wall time, peak
working set, free disk, and decoding on the recorded i9-13900HX/32 GiB/RTX
4060 CPU-only laptop. GPU execution is prohibited.

## 21. Noise analysis

Finite-shot, hardware-noise, and device-specific tests remain deferred. Exact
statevector evidence cannot establish noisy-hardware robustness.

## 22. Scaling analysis

Report only the declared four-point gain grid and q=8 endpoint. Do not infer
asymptotic scaling from one q or four gain values.

## 23. Classical-simulability analysis

All features, fidelity values, RBF values, residual subtraction, gain scoring,
and ridge fits are classically simulable in the tested regime. Any positive
result is a hybrid-surrogate result.

## 24. Data-access cost

All inputs are classical development rows. Inner OOF predictions determine the
second-stage gain. Outer validation outcomes are evaluation-only; no QRAM,
hidden source, calibration row, or final-test row is assumed.

## 25. Reproducibility requirements

Commit this protocol, config, launcher, tests, result JSON/CSV files, selection
and channel audits, paired interval, figures, registry entries, source commit,
and zero locked-data counters.

## 26. Main scientific risks

The selected gain may not generalize, the control may receive equal benefit,
and stage separation may not recover D046's fixed endpoint. The grid does not
support broad hyperparameter conclusions.

## 27. Main implementation risks

Risks include allowing shared gain drift, applying the second-stage gain to the
first stage, using validation outcomes in selection, changing tie order, or
using a gain outside the contract. The launcher fails closed on these cases.

## 28. Minimum publishable result

A complete negative determines whether stage-specific gain calibration helps the
narrow q=8 residualized endpoint. A positive requires every threshold, safety,
control, integrity, statistical, and resource rule.

## 29. Recommended first experiment

Run SSORFRK-08 and SSO-TWO-RBF-08 with fixed shared gain 0.10. Do not run Gate
6.

## 30. Final assessment

SSORFRK is the last narrow calibration test in this q=8 branch: it keeps the
common correction fixed and changes only the unique-stage amplitude.

Current conclusion: **Proceed only after reproduction**.
