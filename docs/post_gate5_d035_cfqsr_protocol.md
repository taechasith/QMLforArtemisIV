# D035: Cross-Fitted C06-Stacked Quantum Residual

Protocol: P003  
Status: accepted for one bounded development-only campaign  
Date: 2026-07-15

## 1. Research problem

Can a quantum kernel improve the residual error of the strongest frozen C06
physics-residual predictor without learning from in-sample C06 errors?

## 2. Mathematical formulation

For each outer grouped fold `f`, let `x` be the frozen transformed inputs, `u`
the q-dimensional PCA-compressed input, `y` the standardized robust correction
cost, and `b_f(x)` the C06 outer-fold prediction. Split the 1,024 outer-training
rows into four deterministic inner whole-group folds. For an inner holdout row,
fit C06 on the other inner groups and define the cross-fitted residual
`e_i = y_i - b_f^{-inner}(x_i)`.

The quantum state and local projected vector are the P002 definitions. With
kernel `K_Q`, the candidate is

`f_Q(x) = b_f(x) + K_Q(u,U) alpha`,

where `alpha` is fitted to the cross-fitted residuals. The outer C06 feasibility
head remains the unchanged safety guard. A02-STACK fits the same residuals with
the same landmark IDs and an exact classical RBF kernel.

## 3. Definitions and assumptions

The outer split, 39,000 development rows, 1,024 outer-training rows, target,
feasibility outcome, preprocessing, q values, 20 seeds, and 20 m/s infeasible
penalty remain inherited frozen assumptions. Inner folds use group IDs only and
never use outcome labels. No calibration or final-test row is available.

## 4. Scientific status of claims

The cross-fitted residual construction is a design assumption and a new
derivation of the training target. Its no-target-leakage property is a direct
consequence of fitting each inner C06 baseline without the held-out group. The
kernel PSD property is inherited from P002. Improved prediction is an empirical
hypothesis. No quantum advantage is claimed because q<=8 exact statevectors are
classically simulable.

## 5. Closest prior method

The closest repository method is C06, the frozen physics residual. The closest
QML method is P002 PRQK, which learned a correction over the raw low-fidelity
cost and failed. D035 changes only the residual baseline and makes its training
error cross-fitted. The closest classical control is an identical-input stacked
RBF.

## 6. Reproduction plan

Reproduce C06 on the same outer folds and compare the cross-fitted C06 stack to
the exact A02-STACK control. Verify that every quantum residual target was
computed from an inner model that excluded its group.

## 7. Reproduction success criteria

All five outer folds, four inner group folds, three q configurations, and 20
seeds must complete. The inner and outer group sets must be disjoint at every
prediction, and all locked-data counters must remain zero.

## 8. Proposed modification

Replace the raw low-fidelity baseline in P002 with a cross-fitted prediction from
the frozen C06 model. Keep the quantum map, kernel, landmark rule, and safety
guard unchanged.

## 9. Proposed mechanism

C06 already explains most cost variation. The remaining C06 errors may contain
structured nonlinear information. Cross-fitting creates an honest residual
target; the kernel is tested only on that residual and cannot exploit in-sample
tree overfit.

## 10. Main hypothesis

CFQSR-08-N will reduce pooled OOF NRMSE by at least 5 percent versus C06 and
will not worsen selection regret or safety because the C06 safety guard is
unchanged.

## 11. Falsification criteria

Reject if the 5% improvement, paired interval, regret, or A02-STACK comparison
fails, if any inner group is used in its own C06 baseline fit, or if any seed or
fold is missing.

## 12. Candidate theorem or proposition

Under group-disjoint inner fitting, each cross-fitted residual target is
independent of the fitted C06 model's training outcome for its held-out group,
conditional on the frozen input and group design.

## 13. Proof strategy

Condition on the deterministic group partition and training algorithm. The
inner model for group `g` is a function only of rows whose group is not `g`.
Therefore its prediction for `g` cannot use that group's target through model
fitting. This is a data-separation property, not a statistical independence
claim about the physical process. Numerical verification records inner train
and holdout group intersections and checks equality of the residual construction
to an independently recomputed audit.

## 14. Counterexample search

Test one-group inner folds, duplicate group IDs, identical inputs, zero
residuals, and a deliberately leaky in-sample baseline on synthetic arrays.
The leaky baseline must be rejected by the guard; the honest baseline must pass.

## 15. Experimental design

Five outer grouped folds, four inner grouped folds, q=4/6/8, no entanglement,
one layer, 20 seeds, all held-out outer validation rows, and identical C06 and
A02-STACK controls. No post-outcome reranking is allowed.

## 16. Classical baselines

C06 is the primary comparator. A02-STACK is the identical-input exact RBF
control. Its residual targets, landmark IDs, regularization, folds, and seeds
are identical to CFQSR.

## 17. Quantum baselines

P001 Q01b and P002 PRQK remain immutable report-only references. CFQSR is a new
hybrid workflow, not a re-fit of either prior candidate.

## 18. Ablation studies

Report q=4/6/8 scaling and compare CFQSR with A02-STACK. The C06 safety guard
is intentionally held fixed; removing it would create an unsafe, unregistered
objective and is not authorized.

## 19. Statistical analysis

Report all 20 seed-pooled OOF NRMSE, MAE, regret, and infeasible-selection
values, with mean, standard deviation, and paired 95% bootstrap intervals.

## 20. Resource analysis

Record wall time, CPU time, peak working set, free disk, q, inner-fold count,
landmarks, and circuit execution count. CPU-only exact statevector is required.

## 21. Noise analysis

Finite-shot and device-noise sensitivity are deferred until a candidate passes
the exact statevector endpoint. They cannot select or rescue D035.

## 22. Scaling analysis

Report q=4/6/8 and the exact inner-fold overhead. Do not infer asymptotic
quantum scaling from these bounded sizes.

## 23. Classical-simulability analysis

The tested q<=8 local statevector is efficiently classically simulable. A
positive result would be a predictive hybrid-surrogate result, not quantum
advantage.

## 24. Data-access cost

All data are classical development rows. Inner C06 fitting, state preparation,
local observable projection, kernel construction, and classical decoding are
included. No QRAM assumption is made.

## 25. Reproducibility requirements

Commit the protocol, config, launcher, inner-fold audit, raw seed metrics,
aggregate summary, paired interval, figures, registry entries, source commit,
and zero locked-data counters.

## 26. Main scientific risks

C06 may have no learnable residual structure; cross-fitting may make residuals
too noisy; A02-STACK may match or beat CFQSR; and a cost-only improvement may
not translate into mission selection benefit.

## 27. Main implementation risks

The key risks are inner-group leakage, accidentally using outer validation rows
in inner fits, mismatched landmarks, and confusing a C06 safety guard with a
quantum safety result. The launcher fails closed on each.

## 28. Minimum publishable result

A complete negative is publishable as an honest stacked-residual test. A
positive requires the paired C06 and A02-STACK superiority rules before any
mission experiment or operational interpretation.

## 29. Recommended first experiment

Run CFQSR-08-N with q=4/6/8 as fixed scaling ablations and A02-STACK as the
matched classical control. Preserve the C06 safety guard exactly.

## 30. Final assessment

The cross-fitted stacked residual is mathematically testable and directly uses
the D034 lesson. Its predictive value is unresolved until D035 executes.

Current conclusion: **Proceed only after reproduction**.
