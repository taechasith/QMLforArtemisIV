# D038: Global Fidelity Residual Kernel

Protocol: P006
Status: accepted for one bounded development-only campaign
Date: 2026-07-15

## 1. Research problem

Can a global quantum-state-fidelity kernel learn a useful correction to C06
after local one-RDM projected kernels and their shrunk variants failed?

## 2. Mathematical formulation

Use the D036 task-aligned score `z in R^q` and honest cross-fitted C06 residual
`e_i`. The one-layer entangling state is

`|psi(z)> = U_RY/RZ,CNOT(z)|0^q>`.

The global fidelity kernel and shrunk prediction are

`K_F(z,v) = |<psi(z)|psi(v)>|^2`

`f_Q(x) = b_f(x) + 0.10 * K_F(z,Z) alpha`.

The matched classical control uses the same task-aligned scores, landmarks,
regularization, and `lambda=0.10` with an exact RBF kernel. C06's feasibility
head remains unchanged.

## 3. Definitions and assumptions

`q` is 4, 6, or 8; one entangling layer is fixed; 256 deterministic landmarks
are used; the kernel is exact statevector fidelity; and lambda is fixed at
0.10 before fitting. Only development rows are allowed.

## 4. Scientific status of claims

The state-fidelity kernel is an established positive-semidefinite construction
for normalized state embeddings. Retaining global correlations is a design
hypothesis. Better prediction is an empirical hypothesis. No quantum advantage,
NASA-performance, mission, hardware, Gate 5, or Gate 6 claim is authorized.

## 5. Closest prior method

The closest methods are D036 TAP-QK and D037 TSQR. D038 changes the kernel from
local one-RDM distance to full state fidelity and retains the D037 lambda=0.10
stabilization. TAP-RBF-SHR-q is the matched classical control.

## 6. Reproduction plan

Reproduce D036 cross-fitted C06 residuals and fold-local PLS scores. Fit the
global fidelity kernel on training scores only, apply deterministic Nyström
landmarks, add 0.10 times the residual correction to C06, and compare with the
same-lambda RBF control.

## 7. Reproduction success criteria

All five outer folds, four inner folds, q=4/6/8, and 20 seeds must complete.
Statevector normalization, PSD clipping, landmark provenance, projection
audits, and zero locked-data counters must pass.

## 8. Proposed modification

Replace the local one-RDM projected distance with the global squared overlap of
the full normalized statevectors. Keep the task-aligned preprocessing,
residual target, shrinkage, ridge, split, seeds, and safety guard fixed.

## 9. Proposed mechanism

Local one-RDM expectations discard multi-qubit correlations. The state-fidelity
kernel evaluates the full encoded state and can preserve those correlations.
The matched RBF tests whether any gain is simply due to a different classical
metric on the same coordinates.

## 10. Main hypothesis

GFRK-08-L010 will reduce pooled OOF NRMSE by at least 5 percent versus C06,
preserve selection safety, and beat TAP-RBF-SHR-q8-L010 by at least 5 percent.

## 11. Falsification criteria

Reject if any primary improvement, paired interval, safety metric, classical
control comparison, state normalization, or fold/seed audit fails.

## 12. Candidate theorem or proposition

For normalized state embeddings, `K_F(z,v)=|<psi(z)|psi(v)>|^2` is positive
semidefinite because it is the Hilbert-Schmidt inner product between density
operators `|psi(z)><psi(z)|` and `|psi(v)><psi(v)|`.

## 13. Proof strategy

Map each input to `rho_z=|psi(z)><psi(z)|`. Then
`Tr(rho_z rho_v)=|<psi(z)|psi(v)>|^2`. For coefficients `c`, the quadratic
form is `sum_ij c_i c_j Tr(rho_i rho_j)=Tr((sum_i c_i rho_i)^2)>=0`.
Numerical tests verify normalized states and nonnegative training-kernel
eigenvalues after the prescribed PSD audit. This proves PSD, not superiority.

## 14. Counterexample search

Test identical states, orthogonal states, one qubit, no entanglement, maximal
feature repetition, normalized-state perturbations, and zero residual targets.
The kernel must be one on identical states, zero on orthogonal states, finite,
and symmetric before PSD clipping.

## 15. Experimental design

Use five outer grouped folds, 1,024 training rows per fold, four inner grouped
folds, q=4/6/8, one entangling layer, lambda=0.10, 20 seeds, all outer
validation rows, and the unchanged C06 feasibility head.

## 16. Classical baselines

C06 is the primary baseline. TAP-RBF-SHR-q uses identical task-aligned scores,
landmarks, target residuals, ridge alpha, and lambda=0.10.

## 17. Quantum baselines

D034 PRQK, D035 CFQSR, and D036/D037 remain immutable historical references.
The tested statevector fidelity kernel is classically simulable at q<=8.

## 18. Ablation studies

q=4/6/8 is the fixed width ablation. Entanglement is fixed on because global
correlation retention is the declared mechanism; turning it off would test a
different kernel and is future work.

## 19. Statistical analysis

Report all 20 seed-pooled OOF NRMSE, MAE, regret, infeasible selection, Brier,
AUROC, and recall values, with means, sample standard deviations, and paired
95% bootstrap intervals for GFRK-08-L010 minus C06.

## 20. Resource analysis

Record q, circuit depth, two-qubit gates, statevector dimension, landmarks,
kernel evaluations, PSD clipping, wall time, CPU time, peak working set, and
free disk. Include state preparation and classical decoding.

## 21. Noise analysis

Finite-shot and hardware-noise tests are deferred unless exact GFRK passes.
Noise cannot rescue a negative exact endpoint.

## 22. Scaling analysis

Report q=4/6/8 and statevector dimension. Do not infer asymptotic quantum
scaling from three bounded sizes.

## 23. Classical-simulability analysis

Exact q<=8 statevectors and fidelity matrices are efficiently classically
simulable. A positive result is not quantum advantage.

## 24. Data-access cost

All data are classical development rows. Include PLS fitting, state preparation,
state overlap, Nyström solve, shrinkage, and decoding. No QRAM assumption is
made.

## 25. Reproducibility requirements

Commit protocol, config, launcher, state/PSD audit, inner/projection audit,
seed metrics, summaries, paired interval, figures, registry rows, source
commit, and zero locked-data counters.

## 26. Main scientific risks

Global fidelity may be too concentrated, entanglement may reduce trainability,
the RBF may match it, and a cost correction may not improve plan selection.

## 27. Main implementation risks

The risks are unnormalized states, accidental use of validation rows, random
landmarks, PSD errors, and claiming that global correlations imply advantage.
The launcher fails closed on these conditions.

## 28. Minimum publishable result

A complete negative establishes that global state fidelity did not recover the
C06 gap. A positive requires the C06, matched RBF, safety, PSD, and integrity
rules before any operational interpretation.

## 29. Recommended first experiment

Run q=4/6/8 with q=8/lambda=0.10 as the primary endpoint and TAP-RBF-SHR as the
matched classical control.

## 30. Final assessment

GFRK is mathematically explicit, directly tests the information discarded by
prior local projections, and is computationally bounded on the reference
laptop. Its result is unresolved until the source-bound campaign executes.

Current conclusion: **Proceed only after reproduction**.
