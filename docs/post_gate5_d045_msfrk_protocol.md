# D045: Multi-Scale Fidelity Residual Kernel Stack

Protocol: P013
Status: accepted for one bounded development-only campaign
Date: 2026-07-15

## 1. Research problem

Can fidelity residual channels at q=4, 6, and 8 provide complementary
multi-scale information beyond a matched multi-scale classical RBF stack?

## 2. Mathematical formulation

For each outer fold, let `e` be the cross-fitted C06 residual on outer-training
rows. Inner grouped folds produce out-of-fold expert predictions
`F_q`, `R25_q`, and `R50_q` for q in {4,6,8}. Define the candidate design

`Psi_A = [1, F_4, F_6, F_8, R25_4, R25_6, R25_8]`

and the matched classical design

`Psi_C = [1, R25_4, R25_6, R25_8, R50_4, R50_6, R50_8]`.

Each coefficient vector solves

`beta = argmin_beta ||e - Psi beta||_2^2 + 0.001||beta_without_intercept||_2^2`.

After refitting all channels on the complete outer-training fold, the
candidate and control predictions are `inverse_scale[b_C06(x) + 0.10*Psi(x)
beta]` with their respective six expert columns.

## 3. Definitions and assumptions

The input is the frozen development feature contract with q=4/6/8 compressed
features and C06 conditioning. The output is decoded physics-residual cost.
The stack has seven columns including an unregularized intercept, six channel
coefficients, alpha=1.0 channel ridge, and lambda=0.10 final shrinkage. Only
development data and grouped inner folds are allowed.

## 4. Scientific status of claims

The multi-scale feature construction and ridge objective are design
assumptions. The claim that fidelity geometry adds complementary information
across q is an empirical hypothesis. Any positive result is development-only.
No NASA, mission, hardware, quantum-advantage, Gate 5, or Gate 6 claim is
authorized.

## 5. Closest prior method

The closest methods are D043's q=8 cross-fitted stack and D044's nonlinear
interaction stack. D045 returns to a linear stack after D044 weakened the
signal and changes only the channel budget from one q to all three q values.

## 6. Reproduction plan

For each outer fold and seed, reproduce C06 cross-fitting and obtain inner OOF
predictions for all three q values. Fit the candidate six-channel stack and
the six-channel two-RBF control on the same OOF rows. Refit all channels on
outer training, apply the fixed coefficients to outer validation, and score
against C06 and the matched control.

## 7. Reproduction success criteria

All 39,000 development rows, five outer folds, four inner folds, q=4/6/8,
and 20 seeds must complete. Candidate/control design matrices must each have
exactly seven columns, use the same rows and ridge penalty, and report zero
outer validation-outcome use and zero locked-data reads in construction.

## 8. Proposed modification

Use all three declared fidelity q channels and RBF-0.25 channels in a linear
ridge stack. The control substitutes RBF-0.50 for the three fidelity channels.
No nonlinear feature map, post-outcome q selection, or threshold change is
allowed.

## 9. Proposed mechanism

D043 selected fidelity at q=8 and cleared C06 but missed the classical rule;
D044 showed that nonlinear interactions were harmful. D045 tests whether q=4
and q=6 contain complementary information that can reduce the residual gap,
with a matched multi-scale RBF control.

## 10. Main hypothesis

MSFRK-ALL will improve pooled OOF NRMSE by at least 5 percent versus C06,
preserve safety metrics, and beat MS-TWO-RBF by at least 5 percent.

## 11. Falsification criteria

Reject if any threshold, paired interval, safety metric, matched-control,
design-shape, coefficient, group, numerical, or data-boundary condition fails.
A complete integrity-valid failure is a scientific negative; an incomplete or
leaked computation is a technical stop.

## 12. Candidate theorem or proposition

With an unregularized intercept and positive ridge penalty on six channel
columns, the normal equations define a finite-dimensional ridge stack. The
candidate and control have equal channel count and identical regularization.

## 13. Proof strategy

The Hessian is `2(Psi^T Psi + R)` with positive diagonal regularization on all
non-intercept columns. Solve the linear system and fail closed on non-finite
coefficients. This proves algebraic validity, not predictive superiority.

## 14. Counterexample search

Test identical q channels, zero channels, one dominant channel, rank-deficient
designs, and all-zero interaction-free inputs. Verify seven columns, finite
coefficients, equal candidate/control sample counts, and no validation outcome
in coefficient fitting.

## 15. Experimental design

Use five grouped outer folds, 1,024 training rows per fold, four inner grouped
folds, q=4/6/8, 20 seeds, one entangling layer, 256 landmarks per channel,
alpha=1.0, stack ridge=0.001, lambda=0.10, and unchanged C06 safety. The
single primary model is the all-q stack.

## 16. Classical baselines

C06 is the primary baseline. MS-TWO-RBF uses q=4/6/8 RBF-0.25 and RBF-0.50
experts, the same six-channel budget, OOF rows, ridge penalty, and decoding.

## 17. Quantum baselines

D034-D044 remain immutable references. All exact fidelity channels at q<=8
and the stack are classically simulable. No quantum advantage claim is
possible from this experiment.

## 18. Ablation studies

The q=4/6/8 channels are fixed components of the primary mechanism. The
six-channel two-RBF stack is the required control. No q or channel is removed
after outcomes.

## 19. Statistical analysis

Report all 20 seed-pooled OOF NRMSE, MAE, regret, infeasible selection, Brier,
AUROC, recall, means, sample standard deviations, and the paired 95% bootstrap
interval for MSFRK-ALL minus C06. Report q coefficient norms and channel audit
counts.

## 20. Resource analysis

Record all 3-q inner and outer channel fits, seven-column stack solves,
landmarks, CPU time, wall time, peak working set, free disk, and decoding on
the recorded i9-13900HX/32 GiB/RTX 4060 CPU-only laptop.

## 21. Noise analysis

Finite-shot and hardware-noise tests remain deferred. Exact statevector
results at q<=8 cannot support a noisy-hardware or quantum-advantage claim.

## 22. Scaling analysis

Report q-channel coefficient sensitivity only. Do not infer asymptotic scaling
from three q values or one multi-scale stack.

## 23. Classical-simulability analysis

All q channels, projections, kernels, OOF stack, and ridge solve are
classically simulable. Any positive result is a hybrid-surrogate result.

## 24. Data-access cost

All inputs are classical development rows. Inner training labels form the
cross-fitted residual and stack fit; outer validation labels are evaluation
only. No QRAM, hardware, or hidden data source is assumed.

## 25. Reproducibility requirements

Commit this protocol, config, launcher, tests, multi-scale/channel audits,
inner audits, seed metrics, summaries, paired interval, figures, registry
entries, source commit, and zero locked-data counters.

## 26. Main scientific risks

q channels may be redundant, the larger stack may overfit, and any gain may be
explained by classical multi-bandwidth RBF structure. C06 improvement alone is
insufficient.

## 27. Main implementation risks

Risks include unequal candidate/control channel budgets, q-specific leakage,
coefficient fitting on validation outcomes, or inconsistent feature order. The
launcher fails closed on these cases.

## 28. Minimum publishable result

A complete negative determines whether q-scale fidelity complementarity adds
anything beyond linear q-scale classical RBF stacking. A positive requires
all threshold, safety, control, integrity, statistical, and resource rules.

## 29. Recommended first experiment

Run the all-q stack with MS-TWO-RBF as the matched control. Do not run Gate 6.

## 30. Final assessment

MSFRK is a bounded linear extension selected from the D043/D044 contrast and
tests a concrete q-scale complementarity mechanism without expanding the
nonlinear branch.

Current conclusion: **Proceed only after reproduction**.
