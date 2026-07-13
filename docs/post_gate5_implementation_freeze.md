# Post-Gate-5 Exploratory Implementation Freeze

Version: 0.1.1
Decision: D008
Protocol: P001
Prepared: 2026-07-13
Accepted: 2026-07-13
Status: Accepted by human research lead; implementation and synthetic validation authorized; research-data execution remains unauthorized

## Decision

D008 freezes the exact implementation contract for the two post-Gate-5
exploratory tracks. Acceptance authorizes implementation and synthetic
correctness validation only. It does not authorize a research-data fit,
calibration or final-test access, a Gate 5 reinterpretation, hardware
execution, or Gate 6.

The machine-readable authority is `configs/post_gate5_exploratory.yaml`. If
this narrative and the YAML disagree, execution must stop.

## Scientific question

The accepted Gate 5 result showed that the original fidelity-overlap quantum
kernel and the registered variational families did not meet the frozen
development benchmark. P001 asks two narrower prospective questions:

1. Does replacing fidelity overlap with a low-dimensional projected quantum
   kernel improve robust-cost prediction under the same grouped-development
   discipline and strong classical controls?
2. Is that projected kernel more useful for the independently propagated
   feasibility classification task than for cost regression?

These are exploratory questions. A favorable answer can justify a later new
protocol, but cannot revise the accepted Gate 5 `FAIL`.

## Shared projected feature map

Both tracks use the existing fold-local preprocessing and PCA projection with
the PCA dimension equal to 4, 6, or 8 qubits. The encoded circuit is the
existing untrained RY/RZ data-reuploading map with one or two layers, feature
scale 0.5, 1.0, or 2.0, and either the nearest-neighbor CNOT ring or the
required unentangled ablation.

For each encoded state, the implementation measures Pauli X, Y, and Z
expectations on every qubit. These `3q` values represent each one-qubit reduced
density matrix. The projected kernel is

```text
k(x,z) = exp(-gamma * sum_q ||rho_q(x) - rho_q(z)||_F^2)
       = exp(-0.5 * gamma * ||r(x) - r(z)||_2^2).
```

The equality follows from the Bloch representation of a one-qubit density
matrix. Define `D_ij` as the summed squared one-RDM Frobenius distance shown in
the exponent. Gamma is `1 / median(D_ij > 0)` on the training fold, multiplied
by the frozen factor 0.25, 1, or 4. A zero median is a governed ineligible fold,
not permission to invent a replacement bandwidth.

This follows the one-particle reduced-density-matrix projected kernel proposed
by Huang et al., while the paired regression/classification design is informed
by the broad PQK/FQK benchmarking of Schnabel and Roth. The local `FQK` track
ID means **feasibility-only quantum kernel**; it must not be confused with the
literature abbreviation for a fidelity quantum kernel. Historical Q01 is the
fidelity-style reference in this repository.

Primary sources:

- Huang et al., "Power of data in quantum machine learning",
  https://doi.org/10.1038/s41467-021-22539-9.
- Schnabel and Roth, "Quantum Kernel Methods under Scrutiny: A Benchmarking
  Study", https://arxiv.org/abs/2409.04406.
- Havlicek et al., "Supervised learning with quantum-enhanced feature spaces",
  https://doi.org/10.1038/s41586-019-0980-2.

## Frozen trial design

The checked-in manifest contains 30 paired projection IDs. Q01b and FQK use
the same expensive projected states for each ID. The manifest is exactly
balanced marginally across qubit count, layer count, feature scale,
entanglement, gamma multiplier, and regularization.

Each track ranks independently because the endpoints differ. Both use five
grouped development folds and successive-halving rungs of 128, 256, 512, and
1,024 rows, retaining 30, 15, 8, and 4 trials. While slots permit, each rung
retains all three qubit counts and both entanglement states before applying the
endpoint ordering to remaining slots.

The selected configuration is rerun on the 20 frozen seed indices. Exact
statevector output is primary. The 1,024-shot, 4,096-shot, and fixed Gate 4
noise calculations are selected-configuration sensitivities only and cannot
rerank or retune a model.

## Q01b endpoint and controls

Q01b uses Nyström kernel ridge regression with at most 256 training-fold
landmarks. Landmark IDs are the SHA-256 ranking of source row ID, projection
ID, fold ID, and seed index; Q01b and FQK share them for a paired run. Its
primary endpoint is pooled out-of-fold robust-cost NRMSE;
feasibility-constrained regret is the first tie-breaker.

Required controls are the frozen C06-T17 physics-residual configuration,
A01-T04 random features, an exact classical RBF kernel on the same PCA rows,
and the C05-T17 compressed MLP. Historical Q01-T17 is reported only as a
non-rerun negative reference. The exact classical RBF control is essential:
it tests whether any apparent gain comes from the projected quantum features
rather than ordinary nonlinear geometry on the compressed classical inputs.

A Q01b result is only a `promising_for_new_protocol` signal when its mean
relative NRMSE gap to C06 is no greater than 5%, all grouped folds and 20 seeds
are complete, and at least one preregistered regime is reproducibly better
than every matched dequantization control. This label does not reopen Gate 5.

## FQK endpoint and controls

FQK predicts only `independently_propagated_feasible`. It uses a Nyström
kernel least-squares classifier whose outputs are clipped to `[0,1]`; it does
not use post-hoc calibration. The primary endpoint is pooled out-of-fold Brier
score, followed by recall at the fixed 0.5 threshold, AUROC, and precision.

The controls are the frozen feasibility heads for C01-T18, C02-T02, C03-T13,
C04-T28, C05-T12, and C06-T17, plus A01-T04, the exact classical RBF control,
and compressed C05-T17 on identical rows.

FQK is only `promising_for_new_protocol` when Brier score is no more than 5%
above the strongest classical feasibility comparator, AUROC is no more than
0.01 lower, recall is no more than 0.02 lower, and all grouped folds and 20
seeds are complete. It cannot make a robust-cost or mission-performance claim.

## Failure and future-research firewall

Every technical failure, resource stop, undefined metric, terminal
nonadvancement, or scientific negative result must create a row in
`data/processed/reporting/post_gate5_future_research_discussion.csv`. The row
must state what was observed, the bounded interpretation, and what a later
study could improve based on that evidence.

The discussion row is committed with the corresponding reporting change
before the step is closed. Every improvement remains future research only:

- `new_protocol_required` is `true`;
- `active_pipeline_change_authorized` is `false`;
- `post_outcome_retry_authorized` is `false`.

This rule records what the project learned without turning a failed step into
post-outcome tuning. A correction or retry requires a new prospective
deviation accepted before execution. Failure suggestions cannot change the
current trial manifest, feature map, controls, rungs, thresholds, or figures.

## Local compute admission

The design is bounded for the recorded i9-13900HX laptop with 32 GiB RAM and
RTX 4060 Laptop GPU. Only one statevector task may run at a time. Classical
controls start at four workers and may rise to eight only after benchmarking.
The project working set is capped at 24 GiB RAM, GPU use is not authorized,
and at least 20 GiB disk must remain free.

Before research-data fitting can be proposed, a representative q=8,
two-layer, 1,024-row benchmark must cover projection, both heads, and every
matched control. With a 25% margin, the projected campaign must remain within
250 CPU-core-hours, 20 GiB of new artifacts, and five wall-clock days. If it
does not fit, the scientific design is not reduced; execution stops for a
prospective compute decision.

## Paper-ready figure plan

RFIG-024 records the protocol boundary. RFIG-025 records this implementation
freeze and the future-research firewall before any outcome exists. If later
execution is separately accepted, RFIG-026 through RFIG-028 will cover learning
curves, kernel/dequantization diagnostics, and FQK safety metrics. RFIG-029 is
mandatory when any governed failure or stop occurs and must distinguish the
observed evidence from discussion-only future improvements.

## Acceptance boundary

D008 is accepted for implementation and synthetic validation only. A clean
source-bound preflight and a separate execution decision are required before
any development-row fit. Calibration rows, final-test rows, hardware runs,
larger-qubit runs, and Gate 6 remain locked.
