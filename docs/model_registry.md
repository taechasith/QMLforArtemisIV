# Phase 1 Model Registry

Version: 0.3.8
Prepared: 2026-07-12
Status: Gate 5 accepted with technical outcome FAIL; D008 exploratory implementation freeze candidate pending; Gate 6 unauthorized

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

At the Gate 4 freeze all registry statuses were `frozen_not_run`. The D006
development campaign has now fitted the authorized grouped-CV tasks; no
calibration or final-test model has been fitted.

## D005 implementation correction

C06 and Q03 no longer infer the physical low-fidelity baseline from the last
shared transformed feature. The runner appends the named
`low_fidelity_cost_m_s` value after applying the training-fold target scaler.
C06 may use that value as a residual predictor; Q03 removes the appended value
from its circuit input and adds it only as the physical baseline. This prevents
a one-hot or PCA component from being mistaken for correction delta-v.

All preprocessing and PCA objects are new per CV fold and are fitted only on
that fold's selected training rows. A01 and compressed C05 are interpretation
views at 4, 6, and 8 PCA dimensions. D006 repeats their 30 existing trial
orders at every dimension, so no new hyperparameter trial is added. Controls
advance independently within each dimension, while the exact same-index view
also follows each surviving QML trial. QML successive halving preserves at
least one eligible trial per required qubit count before filling remaining
slots by rank. Interpretation views remain ineligible to add a candidate
winner. D005 and the D006 execution-only conformance refinement were accepted
on 2026-07-12. Development-only fitting is authorized from a clean tracked
source commit, with full scale-up contingent on the bounded benchmark audit.

## Accepted D006 execution roles

The 450-task first stage contains 270 candidate tasks and 180 control views.
The extra views do not change any of the 30 frozen A01 or C05 hyperparameter
rows. Each QML result receives a control with the same fold, selected rows,
rung, PCA dimension, and seed index. Separately ranked per-dimension controls
prevent an unfavorable fixed-index control from being mistaken for the
strongest classical explanation of a QML result. Both roles are reported, and
neither can become a tenth candidate finalist.

The generated registry retains effective qubit dimension in its identity, so
one A01 or compressed-C05 trial selected at multiple dimensions cannot be
collapsed. Only signed, eligible completed seed rows are registered. The
source-bound campaign audit and mandatory D004 claim-boundary diagnostic
package must be complete before a technical Gate 5 pass can be reported.

## D006 development selection and D007 reporting outcome

The immutable source-bound selection contains C01-T18, C02-T02, C03-T13,
C04-T28, C05-T12, C06-T17, and Q01-T17. Q01-T17 uses four effective qubits at
the 1,024-row rung. Its exact matched A01/C05-T17 views and independently tuned
A01-T04/C05-T17 controls received the frozen 20 seed reruns. All 200 seed tasks
completed.

Q02 and Q03 have no finalist. At rung 128, 8/30 Q02 tasks and 4/30 Q03 tasks
were eligible, below the frozen retain count of 15. All 150 fold diagnostics
per family exist, and the ranking records terminal nonadvancement; later rungs
and selected-configuration seed reruns were never authorized. Accepted D007
reporting records those absences as `not_reached_under_frozen_eligibility`, not
as terminal campaign failures. The source-bound reporting package is complete:
Q01 mean NRMSE is 0.6466 versus 0.00874 for C06, and zero preregistered regimes
qualify. The human research lead accepted the resulting technical `FAIL` on
2026-07-13. No proposed new algorithm is authorized, and calibration,
final-test access, refitting, and Gate 6 remain locked pending a separate
prospective decision.

## Post-Gate-5 exploratory registry boundary

P001 opens a separate exploratory protocol after the accepted Gate 5 negative
result. The entries below are not Phase 1 registered finalists, do not change
the accepted Gate 5 result, and may not run until a later implementation freeze
is accepted.

| ID | Family | Exploratory role | Required boundary |
|---|---|---|---|
| Q01b | Projected quantum kernel | Supervised robust-cost/regret surrogate using projected quantum features on the original grouped-development pipeline | Must compare against C06, A01, compressed C05, and historical Q01 without refitting D006 evidence |
| FQK | Feasibility-only quantum kernel | Classifier for `independently_propagated_feasible` and safety-filter diagnostics | Cannot claim cost-regression improvement and cannot unlock calibration/final-test rows |

Quantum reinforcement learning, dynamic circuits, quantum annealing, QAOA, new
variational QML architectures, larger-qubit circuits, and hardware execution
are appendix or future-work topics only under P001.

D008 is now prepared as a candidate implementation freeze. It binds Q01b and
FQK to the same 30 balanced projection IDs and exact projected-state cache,
while allowing each track to rank independently on its preregistered endpoint.
It adds the exact classical RBF-on-PCA control because a projected-kernel gain
is not interpretable without testing ordinary nonlinear geometry on identical
compressed inputs. D008 is not accepted and neither registry entry may run.

The local ID `FQK` means feasibility-only quantum kernel. It is not the common
literature abbreviation for a fidelity quantum kernel; historical Q01 is this
repository's fidelity-style kernel reference.
