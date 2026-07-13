# D011 Development-Only Exploratory Execution Freeze

Version: 0.1.0
Decision: D011
Protocol: P001
Prepared: 2026-07-13
Accepted: 2026-07-13
Status: Accepted conditionally; fold-shaped synthetic admission must pass before development outcomes are read

## Decision

The human research lead instructed the project to proceed after D010. D011
authorizes a corrected fold-shaped synthetic preflight and, only after that
preflight passes every unchanged laptop ceiling, one resumable development-only
P001 campaign. It does not authorize calibration, final-test, hardware/GPU,
Gate 5 reinterpretation, or Gate 6 work.

The machine-readable authority is
`configs/post_gate5_development_execution.yaml`. The D008 scientific design,
D009 failure record, D010 benchmark result, trial manifest, fold manifest, and
frozen control configurations are pinned by Git-blob hash.

## Pre-execution accounting correction

D010 validly tested its frozen 1,024-training/256-validation synthetic bundle.
The D011 runner audit found that a real grouped-CV task predicts every row in a
held-out fold: 6,500 rows in CV01/CV04/CV05 and 9,750 rows in CV02/CV03. A
complete five-fold task therefore predicts 39,000 validation rows at every
rung. D010 remains a valid synthetic compute result, but its 477.5-unit
projection is not treated as final campaign-shape admission.

D011 must benchmark a conservative 1,024-training/9,750-validation q=8,
two-layer bundle containing both projected heads, A02, and every classical
control. It charges that largest-fold bundle to 1,220 worst-case units with a
25% margin. The count assumes maximally disjoint Q01b/FQK advancement, two
different selected configurations, all 20 seeds, all sensitivities, no smaller
fold or qubit credit, and no cache or control-reuse savings. The unchanged
limits are 250 CPU-core-hours, five wall-days, 20 GiB new artifacts, 24 GiB
peak process memory, at least 20 GiB free disk, and zero GPU-hours.

No development payload may be opened unless this corrected preflight passes.
RFIG-031 records the accounting correction and admission result.

## Frozen execution schedule

Q01b and FQK begin with the same 30 projection IDs at 128 training rows per
fold. They rank independently and retain 15, 8, and 4 configurations at 256,
512, and 1,024 rows. At each advancement point, the best eligible projection
for 4, 6, and 8 qubits is retained first, then a missing entanglement state is
added while capacity permits, and remaining slots follow the endpoint rank.

The union of track-authorized projection IDs may share mathematically
identical projected states, but an endpoint is scored only when that track
authorized the projection at that rung. Q01b may fit the paired feasibility
head solely because feasibility-constrained regret is its frozen tie-breaker;
that auxiliary head does not become FQK evidence after FQK has stopped it.

Every imputer, encoder, scaler, target standardizer, and PCA transform is fit
inside the training portion of one grouped fold and rung. Training rows use the
unchanged nested label-agnostic SHA-256 order. Validation always uses the whole
held-out fold. Checkpoints bind source commit, fold, stage, rung, projection or
control identity, endpoint authorization, seed, and sensitivity condition.
Process interruption may resume valid completed checkpoints; a scientific or
technical task failure is not silently retried.

To fit the recorded laptop without reducing scientific scope, each fold-local
preprocessor/PCA context is reused when its rows and dimensions are identical,
and mathematically identical exact projected states are reused within the same
source-bound invocation. Finite-shot states are not shared across projection
IDs, tracks, seeds, conditions, or train/validation partitions because their
frozen sampling seeds differ. These are exact execution caches, not additional
models or outcome-dependent shortcuts. The runtime guard measures checkpoint
bytes directly, retains the 20 GiB free-disk floor, and checks process memory
and accumulated task time against the unchanged ceilings.

## Endpoints and controls

Q01b ranks by pooled out-of-fold NRMSE, then mean feasibility-constrained
regret, regularized kernel condition number, qubits, layers, and projection
ID. Its controls are C06-T17, A01-T04, exact classical A02 RBF, and compressed
C05-T17. Historical Q01-T17 remains a non-rerun negative reference.

FQK ranks by pooled Brier score, then recall at 0.5, AUROC, precision,
condition number, qubits, and projection ID. Its controls are frozen C01-T18
through C06-T17 feasibility heads where specified by D008, plus A01-T04, A02,
and compressed C05-T17.

The selected configuration for each reached track runs on the 20 frozen seed
indices. Q01b is promising only under the unchanged 5% C06 gap and
dequantization-regime rule. FQK is promising only under the unchanged Brier,
AUROC, recall, fold, and seed requirements. These labels can support a later
D012 interpretation decision only; they cannot revise Gate 5.

The Q01b regime cells are fixed before execution: fidelity, uncertainty
family, base-trajectory family, boundary/tail status, and reference-feasibility
status. A cell is eligible only when Q01b, A01, A02, and compressed C05 have
the same cell in all five folds for every selected seed 1-20. Squared errors
and row counts are pooled across folds using the unchanged full-development
NRMSE denominator. Seed index is the paired bootstrap unit. A cell qualifies
only when the upper two-sided 95% Q01b-minus-control NRMSE bound is below zero
for all three controls. This conjunctive exploratory rule carries no separate
multiplicity-adjusted significance or quantum-advantage claim.

## Sensitivities

Exact statevector output is primary. After selection, 1,024-shot, 4,096-shot,
and fixed Gate 4 noise sensitivities run on each selected seed. Each Pauli
X/Y/Z expectation is sampled independently as a plus/minus-one measurement.
The fixed-noise condition applies the predeclared observable attenuation and
then 4,096-shot sampling. Sensitivities are report-only and cannot rerank,
retune, or alter the promising-signal decision.

## Failure and reporting boundary

A zero median bandwidth or undefined endpoint is a governed ineligible fold,
not permission to substitute a method. Insufficient eligible projections may
terminate a track under its frozen retention count while the other track
continues. Integrity, provenance, leakage, memory, or disk failures stop the
campaign.

Every technical failure, resource stop, undefined metric, terminal
nonadvancement, or scientific negative must add a future-research discussion
row. Its suggestion requires a new protocol and cannot alter or retry P001.
RFIG-026 through RFIG-028 report reached results; RFIG-029 remains the failure
and future-research firewall figure. Missing or unauthorized values are never
shown as zero.
