# D046: Orthogonalized Residual Fidelity-RBF Kernel

Protocol: P014  
Status: accepted for one bounded development-only campaign  
Date: 2026-07-15

## 1. Research problem

Does a fidelity kernel predict residual structure that remains after the
shared RBF-0.25 correction has been removed, and does that information exceed
the same second-stage RBF control?

## 2. Mathematical formulation

For an outer fold, let `e` be the cross-fitted C06 residual on outer-training
rows. The first-stage classical correction is fitted as `r25 = RBF_0.25(e)`.
Inner grouped out-of-fold predictions `r25_OOF` define the orthogonalized
second-stage target

`e2 = e - r25_OOF`.

After refitting on all outer-training rows, the candidate and control are

`f_A(x) = inverse_scale[b_C06(x) + 0.10 * (r25(x) + F_q(x; e2))]`

and

`f_C(x) = inverse_scale[b_C06(x) + 0.10 * (r25(x) + RBF_0.50_q(x; e2))]`.

Here `F_q` is the declared q-qubit fidelity channel after one task-aligned
projection layer, and both second-stage channels use the same projected input,
landmarks, ridge, folds, seeds, and target. No outer validation outcome enters
either fit.

## 3. Definitions and assumptions

The input is the frozen development feature contract, the output is the
decoded physics-residual cost, and `q` is one of 4, 6, or 8. The first stage
and both second-stage models use 256 deterministic landmarks and ridge alpha
1.0. The final correction is shrunk by lambda=0.10. The C06 safety head is
unchanged. The experiment assumes the inner grouped OOF RBF prediction is a
valid training-only estimate of the shared first-stage signal.

## 4. Scientific status of claims

The residual decomposition is a design definition. The claim that fidelity
has unique information after RBF removal is an empirical hypothesis. A result
is development-only surrogate evidence and cannot support NASA, mission,
hardware, quantum-advantage, Gate 5, or Gate 6 claims.

## 5. Closest prior method

D045 MSFRK used a six-channel multi-scale stack and showed that adding q=4 and
q=6 fidelity channels did not close the classical-specific gap. D046 changes
only the residual target and stage order: the shared RBF-0.25 signal is fitted
first, then fidelity is compared with RBF-0.50 on the remaining residual.

## 6. Reproduction plan

Reproduce the frozen C06 cross-fitting for each outer fold and seed. Generate
inner grouped OOF fidelity, RBF-0.25, and RBF-0.50 predictions. Compute `e2`
from the inner RBF-0.25 prediction only. Refit the shared first stage and both
second-stage channels on outer-training rows, predict outer validation rows,
and score all q candidates and matched controls.

## 7. Reproduction success criteria

All 39,000 development rows, five outer folds, four inner grouped folds, q=4,
6, 8, and 20 seeds must complete. The candidate and control must share the
first-stage RBF correction and differ only in the declared second-stage
channel. Every audit must report zero validation-outcome use, zero group
overlap, zero locked-data reads, and zero calibration/final-test reads.

## 8. Proposed modification

Replace the D045 multi-scale stack with a two-stage orthogonalized residual
construction. The first stage is RBF-0.25 for both methods. The second stage is
fidelity for ORFRK and RBF-0.50 for the matched control. No threshold, seed,
fold, q value, safety rule, or data boundary changes.

## 9. Proposed mechanism

The mechanism is residual orthogonalization: common RBF-explained variation
is removed before measuring the fidelity channel. A positive classical-specific
result would indicate information not reproduced by the matched second-stage
RBF, rather than merely a larger model or a shared residual improvement.

## 10. Main hypothesis

Under the frozen development protocol, ORFRK-08-R2 will improve pooled OOF
NRMSE by at least 5% versus C06, preserve safety metrics, and improve NRMSE by
at least 5% versus TWO-RBF-08-R2.

## 11. Falsification criteria

Reject the hypothesis if either 5% threshold, paired interval, safety metric,
stage-order audit, numerical check, or data-boundary check fails. A complete
integrity-valid failure is a scientific negative. An incomplete or leaked run
is a technical stop and cannot be interpreted as model evidence.

## 12. Candidate theorem or proposition

For fixed finite design matrices and positive ridge alpha, each first- and
second-stage ridge/RBF coefficient solve has a unique finite solution when the
declared PSD stabilization succeeds. This proposition concerns solvability,
not predictive superiority.

## 13. Proof strategy

The ridge Hessian is positive definite because alpha times the identity is
added to the finite feature Gram matrix. The implementation checks finite
inputs, finite targets, nonzero distance scale, finite coefficients, and finite
predictions. This proves only the computational contract under those
assumptions.

## 14. Counterexample search

Test zero residuals, identical first-stage predictions, constant inputs,
rank-deficient projected features, one-q inputs, and finite near-zero distance
scales. Verify that `e2` is exactly zero when the OOF first-stage prediction
equals `e`, that candidate/control shapes match, and that no validation outcome
is used in the second-stage target.

## 15. Experimental design

Use five grouped outer folds, 1,024 training rows per fold, four inner grouped
folds, q=4/6/8, 20 seeds, one entangling layer, 256 landmarks, alpha=1.0,
lambda=0.10, and the unchanged C06 safety head. The primary endpoint is
ORFRK-08-R2; q=4 and q=6 are declared secondary configurations, not post hoc
selection.

## 16. Classical baselines

C06 is the frozen primary baseline. TWO-RBF-q-R2 uses the identical first-stage
RBF-0.25 and replaces only the second-stage fidelity channel with RBF-0.50.
This control has the same data access, projections, landmarks, ridge, and
stage count.

## 17. Quantum baselines

D034-D045 remain immutable references. The fidelity channels are exact
statevector simulations at q<=8 and are classically simulable. No quantum
advantage claim is possible from this campaign.

## 18. Ablation studies

The q=4/6/8 endpoints and matched control are fixed. No post-outcome ablation
or q selection is allowed. The first-stage shared RBF and second-stage channel
are not removed after seeing outcomes.

## 19. Statistical analysis

Report all 20 seed-pooled OOF NRMSE, MAE, regret, infeasible selection, Brier,
AUROC, recall, means, sample standard deviations, and paired 95% bootstrap
intervals for the primary candidate minus C06. Report candidate-minus-control
comparison and orthogonalized-target norms.

## 20. Resource analysis

Record first- and second-stage fits, q values, landmarks, CPU time, wall time,
peak working set, free disk, and decoding on the recorded i9-13900HX/32 GiB/
RTX 4060 CPU-only laptop. GPU execution is prohibited.

## 21. Noise analysis

Finite-shot, hardware-noise, and device-specific tests remain deferred. Exact
statevector results at q<=8 cannot establish noisy-hardware robustness.

## 22. Scaling analysis

Report only the declared q=4/6/8 endpoint comparison and stage audit. Do not
infer asymptotic scaling from three q values or one orthogonalization scheme.

## 23. Classical-simulability analysis

The projected features, fidelity expectation values, RBF channels, ridge fits,
and residual subtraction are classically simulable in the tested regime. Any
positive result is a hybrid-surrogate result.

## 24. Data-access cost

All inputs are classical development rows. Inner grouped OOF predictions form
the second-stage target. Outer validation outcomes are evaluation-only. No
QRAM, hardware, hidden source, calibration row, or final-test row is assumed.

## 25. Reproducibility requirements

Commit this protocol, config, launcher, contract tests, result CSV/JSON files,
first/second-stage audits, paired intervals, paper figures, registry entries,
source commit, and zero locked-data counters.

## 26. Main scientific risks

The first-stage RBF may remove most useful residual signal, the fidelity stage
may be redundant with RBF, and any observed gain may be too small for the
frozen threshold. The orthogonalized target can also amplify estimation noise.

## 27. Main implementation risks

Risks include using a validation prediction instead of inner OOF RBF output,
fitting the second stage on the wrong target, giving candidate/control unequal
stage inputs, or mixing q-specific projections. The launcher fails closed on
these cases.

## 28. Minimum publishable result

A complete negative identifies whether fidelity adds unique residual signal
after a shared classical correction. A positive requires all threshold,
safety, control, integrity, statistical, and resource rules.

## 29. Recommended first experiment

Run the declared q=4/6/8 ORFRK endpoints with TWO-RBF-q-R2 controls. Do not run
Gate 6.

## 30. Final assessment

ORFRK is the narrowest next test that directly addresses the remaining
mechanistic ambiguity in D043-D045 without expanding the model family or
changing the frozen decision rule.

Current conclusion: **Proceed only after reproduction**.
