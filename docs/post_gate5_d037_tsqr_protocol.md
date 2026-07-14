# D037: Trust-Region Shrunk Quantum Residual

Protocol: P005
Status: accepted for one bounded development-only campaign
Date: 2026-07-15

## 1. Research problem

Can a bounded quantum correction improve C06 when the correction is explicitly
shrunk to avoid the high-variance extrapolation observed in D034-D036?

## 2. Mathematical formulation

Use the D036 fold-local task-aligned score `z in R^q`, where the PLS map is fit
only on cross-fitted C06 residual targets. Let `b_f(x)` be the outer C06 cost
prediction and let `delta_Q(x) = K_Q(z,Z) alpha` be the projected-kernel
residual correction. For fixed `lambda in {0.10, 0.25, 0.50}`, predict

`f_Q_lambda(x) = b_f(x) + lambda * delta_Q(x)`.

The matched classical control is

`f_RBF_lambda(x) = b_f(x) + lambda * delta_RBF(x)`.

The unchanged C06 feasibility head supplies plan-selection probabilities.

## 3. Definitions and assumptions

`q` is 4, 6, or 8; one non-entangling layer is used; the kernel bandwidth and
ridge settings are inherited from D036; and `lambda` is declared before data
fitting. The primary endpoint is q=8, lambda=0.25. Only development rows are
permitted; all earlier evidence is immutable.

## 4. Scientific status of claims

Shrinkage is a design assumption motivated by regularization theory. The
prediction equations are a new derivation from the D036 correction. Improvement
is an empirical hypothesis. The kernel PSD property is inherited. No claim of
NASA use, mission benefit, hardware benefit, or quantum advantage is made.

## 5. Closest prior method

The closest method is D036 TAP-QK, which used the same task-aligned coordinates
and full correction. D037 changes only the declared correction multiplier.
TAP-RBF-SHRUNK isolates whether shrinkage helps the classical representation as
well. D036 remains immutable and is not rerun.

## 6. Reproduction plan

Reproduce the D036 cross-fitted C06 residual and fold-local PLS score map on the
same five outer folds. Fit each full quantum and classical residual correction
once, apply all three predeclared multipliers, and compare each endpoint with
C06 using the same safety guard.

## 7. Reproduction success criteria

All five outer folds, four inner folds, q=4/6/8, lambda=0.10/0.25/0.50, and 20
seeds must complete. Projection and inner groups must be disjoint from their
validation targets. All locked-data counters must remain zero.

## 8. Proposed modification

Multiply the D036 residual correction by a fixed trust-region factor before
adding it to C06. No feature map, split, optimizer, threshold, seed, or safety
guard changes.

## 9. Proposed mechanism

D034-D036 all produced corrections larger than the residual signal needed to
improve C06. Shrinkage can reduce variance when the correction direction is
partly useful but its magnitude is miscalibrated. The matched control tests
whether this is merely classical regularization.

## 10. Main hypothesis

TSQR-08-L025 will reduce pooled OOF NRMSE by at least 5 percent versus C06,
preserve selection safety, and beat the identically shrunk TAP-RBF control by
at least 5 percent.

## 11. Falsification criteria

Reject if any primary improvement, paired interval, regret, infeasible-selection,
or TAP-RBF comparison fails; if shrinkage is applied inconsistently; or if any
fold, seed, projection, or locked-data audit is incomplete.

## 12. Candidate theorem or proposition

For any fixed `lambda in [0,1]`, the shrunk predictor is a convex interpolation
between the C06 baseline and the unshrunk correction when the correction is
written as a residual delta. Therefore it cannot introduce a new feasibility
head or bypass the C06 safety guard.

## 13. Proof strategy

The identity follows directly from the prediction definition. For `lambda=0`,
the cost prediction is exactly C06; for `lambda=1`, it is the D036 full
correction. Numerical tests verify endpoint interpolation and that the same
lambda is used for quantum and classical controls. This is a mathematical
identity, not a performance proof.

## 14. Counterexample search

Test zero correction, negative correction, lambda=0, lambda=1, identical
baseline/correction, and a correction that changes only validation rows. Verify
that lambda=0 reproduces C06 exactly and that all predictions remain finite.

## 15. Experimental design

Use five outer grouped folds, 1,024 outer training rows, four inner grouped
folds, q=4/6/8, lambda=0.10/0.25/0.50, 20 seeds, all outer validation rows,
and a fixed C06 safety head. The primary is q=8/lambda=0.25. No endpoint
reranking is allowed.

## 16. Classical baselines

C06 is the primary baseline. TAP-RBF-SHRUNK uses the same D036 PLS scores,
landmarks, gamma, ridge solve, residual targets, and lambda values as TSQR.

## 17. Quantum baselines

D034 PRQK, D035 CFQSR, and D036 TAP-QK remain immutable historical references.
The tested statevector kernel is classically simulable, so no quantum advantage
claim is possible from this protocol.

## 18. Ablation studies

Lambda 0.10/0.25/0.50 is the fixed shrinkage ablation; q=4/6/8 is the fixed
width ablation. The quantum and classical controls receive identical
ablations. Lambda is not selected after observing endpoint values.

## 19. Statistical analysis

Report all 20 seed-pooled OOF NRMSE, MAE, regret, infeasible selection, Brier,
AUROC, and recall values. Report means, sample standard deviations, and paired
95% bootstrap intervals for TSQR-08-L025 minus C06. The primary decision is
made once on the frozen endpoint.

## 20. Resource analysis

Record PLS and kernel costs, q, layers, landmarks, local observables, lambda,
wall time, CPU time, peak working set, and free disk. Shrinkage itself has
negligible cost but must be included in the end-to-end accounting.

## 21. Noise analysis

Finite-shot and device-noise tests remain deferred unless the exact-statevector
primary passes. Noise cannot rescue a negative exact endpoint.

## 22. Scaling analysis

Report q and lambda sensitivity only within the declared bounded grid. Do not
infer asymptotic quantum scaling.

## 23. Classical-simulability analysis

The q<=8 statevector and projected local-observable kernel are efficiently
classically simulable. A positive result would be a regularized hybrid-surrogate
result, not quantum advantage.

## 24. Data-access cost

All data are classical development rows. Include PLS fitting, state preparation,
kernel construction, Nyström solve, shrinkage, and classical decoding. No QRAM
or quantum memory assumption is made.

## 25. Reproducibility requirements

Commit the protocol, config, launcher, inner/projection/shrinkage audits, raw
seed metrics, summaries, paired interval, figures, registry entries, source
commit, and zero locked-data counters.

## 26. Main scientific risks

The C06 residual may be irreducible; shrinkage may only reduce harm without
creating improvement; TAP-RBF may benefit equally; and cost improvement may not
translate into mission selection benefit.

## 27. Main implementation risks

The risks are applying lambda to only one control, changing the C06 safety
guard, using validation outcomes, and reporting the best lambda as if selected
after the fact. The launcher fails closed on these conditions.

## 28. Minimum publishable result

A complete valid negative establishes that bounded correction magnitude did not
recover the C06 gap and identifies whether shrinkage helped classical and
quantum corrections equally. A positive requires every primary, control,
safety, and integrity rule.

## 29. Recommended first experiment

Run all declared q and lambda combinations, with q=8/lambda=0.25 as the single
primary endpoint and TAP-RBF-SHRUNK as the matched control.

## 30. Final assessment

TSQR is mathematically explicit, falsifiable, computationally bounded, and
directly motivated by the measured D034-D036 correction instability. Its result
is unresolved until the source-bound campaign executes.

Current conclusion: **Proceed only after reproduction**.
