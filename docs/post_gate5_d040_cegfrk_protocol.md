# D040: Centered Error-Conditioned Global Fidelity Residual Kernel

Protocol: P008
Status: accepted for one bounded development-only campaign
Date: 2026-07-15

## 1. Research problem

Can training-only centering of the D039 error-conditioned feature map remove a
dominant common-similarity component and produce a quantum-specific improvement
without changing the residual target, data split, or safety contract?

## 2. Mathematical formulation

D040 retains D039's fold-local error-conditioned score `z in R^q`. For training
rows and deterministic landmarks `Z`, let `K` be either the global fidelity or
classical RBF Gram cross-kernel and let `W` be the PSD-whitening transform of
the landmark Gram matrix. Define `E = K(X_train,Z)W` and
`mu = mean_rows(E)`. The centered feature maps are
`E_c = E - 1 mu^T` and `E_v,c = K(X_val,Z)W - 1 mu^T`. The residual correction
is `delta(x) = E_v,c alpha`, where alpha is the fixed-ridge solution on `E_c`
and cross-fitted C06 residual targets. The prediction is

`f_Q(x) = b_C06^outer(x) + 0.10 * delta_Q(x)`.

The classical control uses the same centered construction with an exact RBF.
The C06 feasibility head is unchanged.

## 3. Definitions and assumptions

`q` is 4, 6, or 8; one entangling layer is fixed; 256 deterministic landmarks
are used; and lambda is fixed at 0.10. The centering mean is computed only from
outer-training feature rows and is reused unchanged for outer validation rows.
Only development rows are permitted.

## 4. Scientific status of claims

Kernel centering is an established feature-space operation. Its use to remove
common similarity in this residual task is a design hypothesis. The centered
prediction is a new derivation from the D039 feature map. Improvement is an
empirical hypothesis. No NASA, mission, hardware, quantum-advantage, Gate 5,
or Gate 6 claim is authorized.

## 5. Closest prior method

The closest method is D039 EC-GFRK. D040 adds only training-only centering to
the whitened fidelity and matched RBF feature maps. D039 remains immutable and
is not rerun.

## 6. Reproduction plan

Reproduce D039's inner C06 cross-fitting, outer C06 prediction, error-conditioned
PLS scores, deterministic landmarks, and residual target. Fit the global
fidelity and RBF feature maps, compute each training mean, center both training
and validation maps with that mean, solve the fixed ridge, and compare with C06.

## 7. Reproduction success criteria

All five outer folds, four inner folds, q=4/6/8, and 20 seeds must complete.
Training and validation centered feature shapes must match, validation rows
must not contribute to the centering mean, PSD/state audits must pass, groups
must be disjoint, and locked-data counters must remain zero.

## 8. Proposed modification

Subtract the outer-training mean of the whitened landmark feature map from both
training and validation feature maps before the ridge residual fit. Apply the
identical operation to the matched classical RBF. No other rule changes.

## 9. Proposed mechanism

If most pairwise fidelity similarity is a common offset unrelated to residual
variation, centering can remove that offset and improve the correction's
effective conditioning. The matched centered RBF determines whether this is a
generic kernel-preprocessing effect.

## 10. Main hypothesis

CE-GFRK-08-L010 will reduce pooled OOF NRMSE by at least 5 percent versus C06,
preserve selection safety, and beat EC-TAP-RBF-C-SHR-q8-L010 by at least 5 percent.

## 11. Falsification criteria

Reject if any primary improvement, paired interval, safety metric, classical
control comparison, centering provenance check, state normalization, or
fold/seed audit fails.

## 12. Candidate theorem or proposition

For any finite training feature matrix `E`, the centered Gram matrix
`H E E^T H`, with `H = I - 11^T/n`, is positive semidefinite. Applying the
same training-derived centering mean to validation rows does not use validation
outcomes.

## 13. Proof strategy

`H` is symmetric and idempotent. For any vector `a`,
`a^T H E E^T H a = ||E^T H a||^2 >= 0`, proving PSD. The data-access claim
follows because `mu` is computed only from training rows and is reused for
validation rows without fitting. This proves validity, not performance.

## 14. Counterexample search

Test a constant feature map, zero-mean feature map, one-row training map,
identical states, orthogonal states, repeated baseline features, no
entanglement, zero residuals, and a validation map shifted after fitting.
Verify that training centering gives zero column means, validation does not
change the stored mean, all predictions remain finite, and PSD clipping remains
the only numerical correction.

## 15. Experimental design

Use five outer grouped folds, 1,024 training rows per fold, four inner grouped
folds, q=4/6/8, one entangling layer, lambda=0.10, 20 seeds, all outer
validation rows, and the unchanged C06 safety head. The primary is q=8.

## 16. Classical baselines

C06 is the primary baseline. EC-TAP-RBF-C-SHR-q uses the identical
error-conditioned scores, landmarks, whitening, training-only centering, ridge
solve, residual targets, and lambda as CE-GFRK.

## 17. Quantum baselines

D034 through D039 remain immutable historical references. The q<=8 statevector
and fidelity computations are classically simulable, so no quantum advantage
claim is possible.

## 18. Ablation studies

q=4/6/8 is the fixed width ablation. D039 is the historical uncentered
comparison, not a post-outcome reranking. Removing centering inside D040 is not
an unregistered endpoint.

## 19. Statistical analysis

Report all 20 seed-pooled OOF NRMSE, MAE, regret, infeasible selection, Brier,
AUROC, and recall values, with means, sample standard deviations, and paired
95% bootstrap intervals for CE-GFRK-08-L010 minus C06. Use the same primary
and classical-control decision rules.

## 20. Resource analysis

Record q, circuit depth, two-qubit gates, statevector dimension, landmarks,
centering mean width, kernel evaluations, PSD clipping, wall time, CPU time,
peak working set, free disk, state preparation, and classical decoding.

## 21. Noise analysis

Finite-shot and hardware-noise tests remain deferred unless the exact
statevector primary passes. Noise cannot rescue a negative exact endpoint.

## 22. Scaling analysis

Report q=4/6/8 and centered feature width. Do not infer asymptotic quantum
scaling from three bounded sizes.

## 23. Classical-simulability analysis

Exact q<=8 statevectors and fidelity matrices are efficiently classically
simulable. A positive result would be a centered hybrid-surrogate result, not
quantum advantage.

## 24. Data-access cost

All data are classical development rows. Include inner C06 fitting, outer C06
fitting, error-conditioned PLS, landmark state preparation, kernel evaluation,
training-only centering, ridge solve, shrinkage, and decoding. No QRAM or
quantum-memory assumption is made.

## 25. Reproducibility requirements

Commit the protocol, config, launcher, centering/projection/inner/fidelity
audits, seed metrics, summaries, paired interval, figures, registry rows,
source commit, and zero locked-data counters.

## 26. Main scientific risks

Centering may remove useful signal, amplify numerical noise, or improve the
classical control equally. The observed D039 gain may be entirely classical.

## 27. Main implementation risks

The risks are centering validation rows, using a separate mean for validation,
inconsistent centering between quantum and control, and claiming a negative
classical-control result as quantum superiority. The launcher fails closed.

## 28. Minimum publishable result

A complete valid negative identifies whether common-similarity centering adds
anything beyond D039 and records the result as future invention evidence. A
positive requires every C06, classical-control, safety, integrity, and resource
condition.

## 29. Recommended first experiment

Run all declared q values with q=8/lambda=0.10 as the single primary endpoint
and EC-TAP-RBF-C-SHR as the matched control.

## 30. Final assessment

CE-GFRK is mathematically explicit, directly motivated by the D039 audit, and
bounded for the reference laptop. Its result is unresolved until the
source-bound campaign executes.

Current conclusion: **Proceed only after reproduction**.
