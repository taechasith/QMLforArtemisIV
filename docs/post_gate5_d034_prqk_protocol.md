# D034: Physics-Anchored Residual Projected Quantum Kernel

Protocol: P002  
Status: accepted for one bounded development-only campaign  
Date: 2026-07-15

This protocol is a new post-release invention campaign. It does not reopen
Gate 5, change P001 evidence, or authorize Gate 6. The phrase "NASA baseline"
means the repository's physics and mission-design comparator, not a claim that
NASA used QML.

## 1. Research problem

Can a projected quantum kernel improve a learned correction-cost surrogate when
the known low-fidelity physics cost is supplied as an additive baseline?

## 2. Mathematical formulation

For a development row, let `x` be the 28 frozen input features, `y` be
`robust_total_correction_delta_v_m_s`, `c` be independent feasibility, and
`b(x)` be `low_fidelity_cost_m_s`. Each grouped-CV training fold defines a
leakage-safe transform `Phi_f` and PCA map `Pi_f,q`. The quantum input is
`u = Pi_f,q(Phi_f(x))` and the residual target is `r = y - b` after the same
training-fold target standardization used by the accepted pipeline.

The state is

`|psi(u)> = U_L(u)|0^q>`.

Each layer applies `RY(s u_j)` followed by `RZ(s u_(j+1))` on each qubit, then
optionally applies a nearest-neighbor CNOT ring. The projected feature is the
concatenated local Bloch vector
`r_Q(u) = (<X_1>, <Y_1>, <Z_1>, ..., <X_q>, <Y_q>, <Z_q>)`.

The kernel is

`K_Q(u,v) = exp(-gamma * sum_j ||rho_j(u)-rho_j(v)||_F^2)`
`         = exp(-gamma/2 * ||r_Q(u)-r_Q(v)||_2^2)`.

The residual predictor is `f_Q(x) = b(x) + K_Q(u,U) alpha`, where `alpha` is
the ridge solution for the residual target. A separate least-squares kernel
head predicts `p_Q(c=1|x)` and is clipped to `[0,1]` only for scoring. Plan
selection uses predicted cost subject to `p_Q >= 0.5` and the frozen
20 m/s infeasibility penalty.

## 3. Definitions and assumptions

`X` is the frozen development feature space; `Y=R` is standardized correction
cost; `C={0,1}` is independent feasibility; `q in {4,6,8}`; `L=1`; `s=1`;
`gamma=0.25` times the training-fold median-distance inverse; `lambda=1`; and
at most 256 training landmarks are selected by SHA-256 from training scenario
IDs only. Groups, split labels, outcome fields, decision-set IDs, and candidate
indices are excluded from model inputs.

## 4. Scientific status of claims

- The frozen feature, split, target, and feasibility definitions are **design
  assumptions** inherited from the accepted benchmark.
- The one-qubit density-matrix identity used below is an **established
  mathematical identity**.
- Positive semidefiniteness of the Gaussian kernel on the projected real
  vectors is a **direct consequence of a known result**; it does not imply
  quantum advantage.
- Residual anchoring improving prediction is an **empirical hypothesis**.
- PRQK being better than C06 is an **empirical hypothesis**, not a result.
- Any performance result from this campaign is a **known empirical result** only
  after the source-bound run and validation complete.

Citation-dependent claims about mission design must be verified against the
listed primary sources in `paper/references.md`; this protocol makes no claim
that NASA used the PRQK architecture.

## 5. Closest prior method

The closest repository method is P001 Q01b, which used the same local
Pauli-projection kernel on generic compressed features and failed to beat C06.
The closest internal residual method is Q03, which used a trainable variational
quantum residual and did not reach a finalist. The proposed change is a
non-variational projected kernel residual with an explicit additive baseline.

## 6. Reproduction plan

The committed P001 Q01b summary and control table are reproduced as immutable
reference values. The new run reproduces the same grouped folds, preprocessing
discipline, 1,024-row training rung, validation rows, 20 seed indices, target
standardization, 256-landmark rule, and C06 comparator. Historical Q01b is not
refit.

## 7. Reproduction success criteria

The frozen inputs must contain 39,000 development rows, unique scenario IDs,
7,800 decision sets, five valid grouped folds, and zero calibration/final-test
reads. Any mismatch is a technical stop, not a model result.

## 8. Proposed modification

PRQK uses the existing RY/RZ state preparation and local observable projection,
but removes the scalar low-fidelity cost from the encoded vector. It fits the
kernel to `y-b` and adds `b` back at prediction. The feasibility head is
separate and cannot alter the cost target or threshold.

## 9. Proposed mechanism

The mechanism is residual conditioning: the quantum feature map is not asked to
rediscover the dominant physics trend. It is asked to represent only the
remaining correction structure. This is measurable through residual NRMSE,
kernel-target alignment, effective rank, and comparison with the identical-input
classical RBF control.

## 10. Main hypothesis

Under the frozen development distribution, PRQK-08-N will achieve at least a
5 percent lower pooled OOF NRMSE than C06, with no worse safety-constrained
regret and a safety head within the C02 comparator rule.

## 11. Falsification criteria

Reject the hypothesis if the improvement is below 5 percent, the paired 95
percent bootstrap upper bound is not below zero, any fold or seed is missing,
regret or infeasible selection worsens, the safety rule fails, or A02-R obtains
the same improvement. A negative result is valid if all integrity checks pass.

## 12. Candidate theorem or proposition

For finite projected Bloch vectors, `K_Q` is positive semidefinite.

## 13. Proof strategy

For a one-qubit state, `rho=(I+r dot sigma)/2`. Therefore
`||rho-rho'||_F^2 = ||r-r'||_2^2/2`. Summing over qubits embeds every state in
Euclidean space. The Gaussian radial basis kernel on a Euclidean space is
positive semidefinite, so its composition with the embedding is positive
semidefinite. The implementation additionally records numerical eigenvalue
clipping. This proves kernel validity, not predictive superiority.

## 14. Counterexample search

The implementation tests identical inputs, one-qubit basis states, orthogonal
states, no entanglement, entangled Bell states, zero residuals, duplicate
projected vectors, and finite numerical eigenvalues. The known counterexample to
an advantage claim is a low-rank projected map whose exact simulation is cheap;
this campaign therefore makes no quantum-advantage claim.

## 15. Experimental design

Use all five whole-group folds, 1,024 nested training rows per fold, every held-
out validation row, and seeds 1 through 20. Evaluate six prespecified configs:
q=4,6,8 crossed with entanglement off/on. The q and entanglement variants are
ablations, not outcome-selected tuning. C06, BASELINE, and A02-R use the same
rows and fold-local transforms.

## 16. Classical baselines

C06 is the frozen boosted physics residual. BASELINE is the low-fidelity cost
alone. A02-R is an exact classical RBF residual kernel on exactly the same
compressed, baseline-excluded inputs, landmark IDs, and regularization.

## 17. Quantum baselines

P001 Q01b is the committed historical projected-kernel result. Q03 is the
committed variational residual family. Neither is silently refit in this
campaign. PRQK's six configurations are compared as a new residual-kernel
family and ablation set.

## 18. Ablation studies

Compare q=4/6/8 scaling, entanglement off/on, BASELINE versus learned residual,
and PRQK versus A02-R. Removing the baseline from the model definition is not
an after-the-fact ablation; it is the preregistered mechanism.

## 19. Statistical analysis

Report all 20 seeds, fold-pooled NRMSE, MAE, regret, safety Brier, AUROC,
recall, calibration error, means, standard deviations, and paired 95 percent
bootstrap intervals. The paired unit is seed index with identical folds and
rows. No post-outcome hyperparameter reranking is allowed.

## 20. Resource analysis

The reference execution is CPU-only exact statevector, q<=8, 24 GiB working-set
ceiling, 250 CPU core-hours, five-day wall-clock ceiling, 20 GiB artifact
ceiling, and 20 GiB minimum free disk. Statevector projection is cached once
per fold/config; landmark fitting is repeated by seed.

## 21. Noise analysis

Finite-shot and fixed-noise tests are not used to select the candidate. If the
exact development endpoint is valid, a separate report-only sensitivity may be
generated using 1,024/4,096 shots and the inherited hardware-agnostic noise
model. No QPU or calibration claim follows.

## 22. Scaling analysis

The campaign directly measures q=4,6,8 and reports statevector time, peak
memory, kernel dimension, and landmark count. It does not infer asymptotic
scaling from three points; the result is a bounded systems observation.

## 23. Classical-simulability analysis

The model uses exact local statevectors and local observables at q<=8. It is
classically reproducible in the tested regime. A PRQK improvement would be a
predictive or trainability result, not a quantum computational advantage.

## 24. Data-access cost

All source data are classical development rows. The data-loading cost, fold-local
preprocessing, state preparation, statevector simulation, measurement projection,
kernel construction, landmark solve, and decoding are included in the CPU
campaign. No QRAM or quantum-memory assumption is made.

## 25. Reproducibility requirements

Commit the protocol, config, source-bound script, tests, raw per-seed metrics,
aggregate summaries, figure source tables, figures, dependency lockfile, source
commit, machine description, and zero locked-data read counters.

## 26. Main scientific risks

The residual may be too weak or noisy for the projected map; the baseline may
already explain nearly all cost variation; a classical RBF may match or exceed
PRQK; and local observables may discard the correlations needed for selection.

## 27. Main implementation risks

Potential risks are baseline leakage into the circuit, fold contamination,
incorrect Nystrom landmarks, PSD numerical instability, memory growth from
statevectors, and accidental access to locked payloads. Fail closed on each.

## 28. Minimum publishable result

A valid negative is publishable as a reproducible residual-conditioning test if
the controls, uncertainty, resource accounting, and claim boundaries are
complete. A positive requires the frozen superiority rule and an independent
reproduction before any mission-level claim.

## 29. Recommended first experiment

Run PRQK-08-N at the full 20-seed grouped-CV endpoint, with q=4/6/8 and
entanglement variants as prespecified ablations and A02-R as the identical-input
control. Do not add a second architecture until the result is classified.

## 30. Final assessment

The mathematical kernel contract is valid and the residual mechanism is
testable. Predictive superiority remains unresolved until D034 executes.

Current conclusion: **Proceed only after reproduction**.
