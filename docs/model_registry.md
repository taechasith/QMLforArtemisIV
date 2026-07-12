# Phase 1 Model Registry

Version: 0.3.1
Prepared: 2026-07-12
Status: Gate 4 accepted and frozen; D004 diagnostics added before fitting; synthetic smoke-tested only; no research model fitted

## Registered candidates

Every candidate produces correction-cost predictions and a paired feasibility
probability. One finalist per candidate family may enter the locked test, for a
maximum of nine candidate finalists.

| ID | Family | Implementation | Registered role |
|---|---|---|---|
| C01 | Ridge or elastic net | scikit-learn linear models | Transparent linear baseline |
| C02 | Extra trees | scikit-learn ExtraTrees | Strong nonlinear tree ensemble |
| C03 | Histogram gradient boosting | scikit-learn HistGradientBoosting | Strong tabular baseline |
| C04 | Sparse Gaussian process | Exact GP on a deterministic development subset up to 2,048 rows | Probabilistic kernel baseline within laptop memory |
| C05 | Multilayer perceptron | scikit-learn MLP | Classical neural baseline in matched and unrestricted views |
| C06 | Physics residual | Ridge or boosted residual over frozen low-fidelity cost | Multi-fidelity classical baseline |
| Q01 | Quantum kernel | In-repository statevector overlap kernel with Nystrom landmarks | QML kernel candidate |
| Q02 | Variational quantum regressor | RY/RZ data re-uploading circuit with trainable rotations and linear head | Variational QML candidate |
| Q03 | Hybrid quantum residual | Q02 fitted to high-minus-low-fidelity cost | Multi-fidelity QML candidate |

Reference methods are the numerical trajectory optimizer and a reconstructable
mission baseline. They are not trained model families.

## Required interpretation control

| ID | Family | Rule |
|---|---|---|
| A01 | Random-Fourier ridge | Use the same PCA inputs, sample IDs, feature dimensions, tuning rungs, and seeds as Q01; report beside Q01 but do not treat it as a tenth candidate winner |

Every QML family also registers `entangle=true` and `entangle=false` and feature
scales 0.5, 1.0, and 2.0. The no-entanglement configuration is an ablation, not
a new family. C05 must include a parameter-matched compressed-input view in
addition to its unrestricted classical view.

## Shared input and output contract

Development-fitted imputation, categorical encoding, and scaling are shared.
QML and matched controls use development-fitted PCA with components equal to
qubit count, clipped to three standard deviations and mapped to angles. The
models cannot receive scenario ID, split, group ID, or any final outcome as an
input.

The cost target is `robust_total_correction_delta_v_m_s`. Feasibility is
`independently_propagated_feasible`. Selection uses grouped-development NRMSE
with feasibility-constrained regret as the tie-breaker. Calibration data can
calibrate the selected output but cannot choose a family or hyperparameter.
Decision-set ID and candidate index group five alternative plans for regret;
they are evaluation metadata and never enter a model.

## Frozen tuning and seeds

`tuning_manifest.csv` contains 30 deterministic trials for each of nine
candidate families and A01. Classical candidates use five-fold grouped CV;
the GP uses its registered deterministic subset. QML and matched controls use
five-fold grouped successive-halving rungs of 128, 256, 512, and 1,024
identical rows, retaining 30, 15, 8, and 4 trials respectively.

Tuning uses one common frozen seed per trial. Only the selected development
configuration is rerun over 20 development seeds. Finalists use 30 seeds. A
failed optimizer seed is a reportable result and is not replaced.

## Quantum resource contract

- Required qubits: 4, 6, and 8.
- Unauthorized without a dated compute review: 10 and 12 qubits.
- Encoding: RY/RZ angle encoding with data re-uploading.
- Entanglement: nearest-neighbor CNOT ring or registered no-entanglement ablation.
- Development shots: 1,024; confirmation shots: 4,096.
- Exact statevector and finite-shot results: reported separately.
- Noise sensitivity: fixed, hardware-agnostic depolarizing/readout attenuation; never described as device calibration.
- Execution: one statevector/GPU job at a time with checkpointing by family, qubits, trial, and seed.

The statevector implementation is an auditable research reference, not a QPU
backend. Runtime on a CPU or RTX 4060 cannot support a hardware-speedup or
quantum-advantage claim.

## D004 QML diagnostic contract

D004 adds diagnostics but does not add a candidate family or change finalist
selection thresholds.

Q01 must report quantum-kernel feature scale, centered kernel-target alignment,
off-diagonal concentration, effective rank, condition number, landmark count,
fold, rung, and sample count. These values are computed only inside the
development training folds.

Q02 and Q03 must report optimizer status, loss improvement, gradient-norm proxy
where available, parameter count, circuit depth, two-qubit gate count, wall
time, and seed-level failures. Failed seeds are retained.

Every QML result must be shown beside A01 and the compressed-input C05 view on
identical rows, PCA inputs, folds, rungs, and seeds. Quantum reinforcement
learning, dynamic circuits, quantum annealing, and QAOA remain deferred from
Phase 1 candidate ranking.

## Implementation locations

- Candidate and control factories: `src/openqfuel/models.py`
- Development-only shared preprocessing and PCA: `src/openqfuel/preprocessing.py`
- Circuit, kernel, finite-shot, and noise implementation: `src/openqfuel/qml.py`
- Full search spaces and resource rules: `configs/phase1_benchmark.yaml`
- Frozen trial rows: `data/processed/simulator/tuning_manifest.csv`
- Frozen random seeds: `data/processed/simulator/seed_manifest.csv`

All registry statuses are `frozen_not_run`. Synthetic unit data were used only
to verify interfaces, determinism, shapes, and access controls.
