# Frozen Phase 1 Analysis Plan

Version: 0.6.2
Prepared: 2026-07-12
Status: Gate 4 accepted; D003 data qualified; D004 controls integrated; D005 runner candidate pending human acceptance

## Analysis sequence

1. Admit development scenarios only after Gate 4 acceptance and D003 conformance audit.
2. Fit preprocessing, target scaling, and any PCA separately inside every development-CV training fold.
3. If D005 is accepted, select one configuration per candidate family using pooled out-of-fold development NRMSE, then regret and lower complexity; retain unweighted fold summaries as diagnostics.
4. Rerun selected configurations on 20 development seeds and freeze finalists.
5. Use the calibration split only for uncertainty/probability calibration; do not change features, families, or hyperparameters.
6. Commit finalist identities, fitted preprocessing hashes, and executable analysis state before a separate final-test unlock.
7. Evaluate the ID and OOD final tests once over 30 registered finalist seeds.
8. Preserve and report every failed optimizer, nonconverged propagation, infeasible selection, and missing prediction.

## D004 literature hardening before fitting

The local Gate 5 literature review was tightened before any research model was
fitted. The accepted model families, splits, thresholds, tuning-trial counts,
sample rungs, and final-test lock remain unchanged. The added requirements are
diagnostic and interpretive controls that prevent a weak or cosmetic QML result
from being promoted.

Source vetting is now explicit. Primary research papers, NASA/official
standards, and authoritative mission-design records may support benchmark
rules. Vendor pages, marketing articles, unsourced blog claims, RequestPDF
metadata pages, and broad AI-generated summaries are search leads only. A claim
from those sources cannot change a model, threshold, split, metric, or paper
claim unless a retrievable primary or official source supports it.

The Gate 5 runner must emit these development-only diagnostics:

- Learning-curve parity at 128, 256, 512, and 1,024 rows for QML and matched controls, with same-row classical comparisons reported separately from full-development classical results.
- Quantum-kernel diagnostics for Q01: feature-scale setting, centered kernel-target alignment, off-diagonal concentration, effective rank, condition number, Nystrom landmark count, and fold/rung sample count.
- Variational-trainability diagnostics for Q02 and Q03: optimizer failure status, loss improvement, gradient-norm proxy where available, parameter count, circuit depth, two-qubit gate count, wall time, and seed-level failure rate.
- Dequantization controls for every QML result: A01 random-Fourier ridge and the compressed-input C05 view on identical PCA inputs, sample IDs, folds, rungs, and seeds.
- Fixed regime reports by fidelity, uncertainty family, base-trajectory family, boundary/tail flag, reference-feasible status, and no-reference-feasible decision sets.
- Claim-boundary checks showing whether any apparent QML gain is explained by bandwidth/feature scale, entanglement removal, random-feature approximation, parameter count, sample selection, or a small set of no-reference-feasible cases.

Quantum reinforcement learning, dynamic-circuit qubit reuse, quantum annealing,
and QAOA remain outside the Phase 1 candidate ranking. They may be discussed as
future or exploratory appendix material only after the supervised surrogate
benchmark is completed.

RFIG-019 records the literature-to-control matrix for this hardening step. All
future Gate 5 result figures must retain the same boundary: development-only
evidence before model selection, calibration-only evidence after finalist
selection, and no final-test value until a separate unlock.

## D005 runner correction pending acceptance

The Gate 4 freeze specified five-fold grouped CV and matched hash-selected
learning rungs but did not freeze an exact fold map or hash namespace. It also
did not state whether learned transforms were fit once or inside folds, and the
residual factories defaulted to the last transformed column rather than an
explicit physical baseline. D005 resolves these issues before model outcomes:

- assign all records from one G01-G12 group to one validation fold using frozen uncertainty/trajectory design strata and version-stable SHA-256 tie breaks, without outcomes;
- rank training rows with a separate SHA-256 namespace so the 128/256/512/1,024 rungs are nested and identical for QML, A01, and compressed C05;
- fit imputation, categorical encoding, feature scaling, target scaling, and PCA only on the current fold's selected training rows;
- use pooled out-of-fold squared error for the primary NRMSE so unequal two- and three-group folds do not receive equal aggregate weight, while still reporting every fold separately;
- preserve family-specific frozen training seeds and pair comparisons by `seed_index`, because different algorithms do not consume random streams identically;
- cycle the 30 A01 and compressed-C05 diagnostic trials across 4/6/8 dimensions (10 each) without adding hyperparameter trials, and preserve at least one eligible QML trial per required qubit count at every halving rung;
- append the physical low-fidelity cost in target-standardized units for C06/Q03 and prevent Q03 from treating that appended baseline as a circuit angle.

`scripts/run_phase1_development.py preflight` is read-only. The execution
command fails closed until the D005 status is accepted by the human research
lead. Each completed fold is written atomically with a signature covering the
source commit, trial, view, rung, and matched dimension; resume refuses a
mismatched checkpoint. RFIG-020 records the outcome-blind fold allocation.

## Endpoints

Primary prediction endpoints are robust-cost NRMSE and
feasibility-constrained regret. The NRMSE denominator is the sample standard
deviation of the primary target in development data only. Regret selects the
lowest predicted-cost candidate among each registered five-plan decision set
whose predicted feasibility probability is at least 0.5. An independently
infeasible selection or absence of a predicted feasible candidate receives the
frozen 20 m/s penalty. A set with no independently feasible reference plan is
retained, assigns the same 20 m/s penalty to every model, and contributes to a
separately reported no-reference-feasible rate.

Secondary endpoints are RMSE, MAE, feasibility precision/recall/AUROC/Brier
score/calibration error, burn magnitude and angular error, terminal-margin
error, violation rate, wall time, and inference time. ID and OOD metrics are
never pooled into one favorable average.

Phase 1 prediction performance cannot by itself establish the protocol's
closed-loop mission hypothesis. It can only trigger or reject the Gate 5
algorithm decision. The trigger requires QML prediction error within 5% of the
strongest classical candidate, a stable residual regime, and survival across
grouped validation and at least 20 seeds.

## Confirmatory comparisons

For each Q01-Q03 finalist, compute paired QML-minus-strongest-classical
differences for NRMSE and regret. These six tests form one confirmatory family.
Use a two-sided paired sign-permutation test with 10,000 replicates and apply
Holm adjustment across all six p-values. Report the signed effect and a paired
95% bootstrap interval with 10,000 replicates whether or not significance is
reached.

Interpretation comparisons are mandatory but secondary:

- Q01 against A01 random-Fourier ridge and the classical RBF/GP candidate;
- every QML candidate against the parameter-matched compressed MLP view;
- entangled against unentangled configurations;
- exact statevector against 1,024-shot, 4,096-shot, and fixed-noise sensitivities;
- each learning-curve size and qubit count separately;
- ID against OOD performance without selecting a favorable domain.

No post-test hyperparameter change is allowed. An exploratory subgroup found
after final-test access must be labeled exploratory and cannot rescue a failed
confirmatory claim.

## Calibration, missingness, and failures

Probability calibration and uncertainty-interval calibration may use only the
6,500-row calibration split after model selection. Threshold 0.5 remains fixed
for the primary feasibility decision. Any alternate diagnostic threshold is
exploratory.

The analysis does not drop non-finite predictions, optimizer failures, or
nonconverged scenario labels to improve a score. A model-side failure receives
the registered infeasible regret penalty and is counted in failure-rate tables.
A simulator nonconvergence remains a distinct target outcome. If a metric is
undefined, report the reason and the affected count; do not replace it with
zero.

## Reporting

Every result table includes model version, trial ID, seed, split, fidelity,
qubits, layers, feature scale, entanglement, shots/noise state, sample count,
failed count, wall time, and hardware context. Seed-level rows are retained.
Training, encoding, circuit simulation, sampling, optimizer, and classical
post-processing time are reported separately where measurable.

The executable metric and resampling functions are in
`src/openqfuel/phase1_analysis.py`. Their current tests use synthetic arrays and
contain no research outcome.
