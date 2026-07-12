# Frozen Phase 1 Analysis Plan

Version: 0.4.0
Prepared: 2026-07-12
Status: Gate 4 accepted; D003 F0/F1 qualified, F2 pending; analysis functions tested only with synthetic data

## Analysis sequence

1. Admit development scenarios only after Gate 4 acceptance and D003 conformance audit.
2. Fit preprocessing on development rows and execute the frozen grouped-CV tuning manifest.
3. Select one configuration per candidate family using mean development NRMSE, then regret and lower complexity as frozen tie-breakers.
4. Rerun selected configurations on 20 development seeds and freeze finalists.
5. Use the calibration split only for uncertainty/probability calibration; do not change features, families, or hyperparameters.
6. Commit finalist identities, fitted preprocessing hashes, and executable analysis state before a separate final-test unlock.
7. Evaluate the ID and OOD final tests once over 30 registered finalist seeds.
8. Preserve and report every failed optimizer, nonconverged propagation, infeasible selection, and missing prediction.

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
