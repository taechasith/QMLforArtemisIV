# Post-Gate-5 Exploratory Protocol

Version: 0.2.1
Opened: 2026-07-13
Status: Opened prospectively; D008 implementation freeze accepted; implementation and synthetic validation authorized; research-data execution remains unauthorized

## Purpose

Gate 5 closed with an accepted technical `FAIL` for the preregistered
development benchmark. The accepted result rejects the proposed multi-fidelity
physics-constrained quantum residual surrogate under the frozen trigger. It
does not prove that no QML method can work on this problem.

This protocol opens a narrow exploratory branch that remains tied to the
original pipeline. It is not a Gate 5 rescue, not a refit of D006 evidence, and
not a Gate 6 mission experiment.

## Hard boundaries

- The Gate 5 result remains unchanged and accepted as a benchmark-specific
  negative result.
- D006 and D007 evidence must not be refit, reranked, retried, relabeled, or
  used to tune a new threshold.
- Calibration rows, final-test rows, and Gate 6 mission scenarios remain
  locked until a separate prospective decision explicitly opens them.
- The original grouped-development split, row identity discipline, fold-local
  preprocessing, target definitions, feasibility labels, and safety-filter
  interpretation remain the default pipeline.
- Four, six, and eight qubits remain the near-term resource envelope on the
  reference laptop. Ten or twelve qubits require a new compute review.
- One statevector or GPU-heavy job runs at a time unless a new benchmark proves
  otherwise on the recorded local hardware.
- Any result from the local simulator is a classical simulation result, not a
  quantum-advantage or hardware-speedup claim.

## Literature basis

The near-term branch is based on sources that directly fit supervised quantum
kernel learning rather than adjacent optimization or control claims.

- Projected quantum kernels are retained because recent benchmarking compares
  fidelity and projected quantum kernels across classification and regression
  tasks and shows that kernel construction and hyperparameter design are
  material. This motivates testing a different quantum readout from the failed
  Q01 fidelity-overlap style kernel while keeping the same benchmark controls.
  Source: Schnabel and Roth, "Quantum Kernel Methods under Scrutiny: A
  Benchmarking Study", https://arxiv.org/abs/2409.04406.
- A feasibility-only quantum-kernel classifier is retained because quantum
  feature-space methods were originally framed around supervised
  classification and kernel estimation. The project already has an
  independently propagated feasibility label and a safety-filter threshold, so
  this can be tested without changing the original mission-planning boundary.
  Source: Havlicek et al., "Supervised learning with quantum enhanced feature
  spaces", https://arxiv.org/abs/1804.11326.
- New variational QML architectures are not near-term tests because Q02 and Q03
  already exposed trainability and eligibility failures. Barren-plateau
  literature supports a trainability audit before any performance campaign, not
  post-outcome replacement of the failed families. Source: McClean et al.,
  "Barren plateaus in quantum neural network training landscapes",
  https://www.nature.com/articles/s41467-018-07090-4.

## Near-term QML tests

### `Q01b` projected quantum kernel

Q01b is an exploratory supervised surrogate that replaces the Q01
state-overlap kernel with projected quantum features. It must use the same
development rows, grouped folds, PCA input dimensions, sample rungs, target
standardization, and seed accounting unless a later accepted implementation
freeze states a stricter rule before execution.

Required comparators are C06, A01 on identical compressed inputs, compressed
C05, and the historical Q01 result as a negative reference. Historical Q01 may
orient interpretation but cannot be rerun or reweighted to make Q01b look
better.

Primary exploratory endpoints are robust-cost NRMSE and
feasibility-constrained regret. Required diagnostics include projected-feature
dimension, observable set, feature-scale setting, kernel-target alignment,
off-diagonal concentration, effective rank, condition number, fold/rung sample
count, wall time, and matched-control deltas.

### `FQK` feasibility-only quantum kernel

FQK is a quantum-kernel classifier for
`independently_propagated_feasible`. It does not predict robust correction
delta-v as a primary target and cannot be used to claim cost-regression
improvement.

Primary exploratory endpoints are AUROC, Brier score, recall/precision at the
frozen 0.5 feasibility threshold, calibration diagnostics on development folds
only, and safety-filter consequences under the existing regret penalty rule.
If the classifier is later allowed to use calibration rows, that must be a
separate decision after the classifier identity and code are frozen.

Required comparators are the strongest available classical feasibility heads,
an A01 or projected-feature classical kernel control on identical rows, and a
compressed C05 classifier view.

## Appendix and future-only methods

Quantum reinforcement learning, dynamic circuits, quantum annealing, QAOA, new
variational QML architectures, larger-qubit circuits, and hardware execution
are not near-term tests under this protocol. They remain appendix or future-work topics only.
Any later experiment involving them requires a new prospective
protocol, stronger classical baselines in the same task class, new resource
accounting, and new paper-ready figures.

## Required records before any execution

- An implementation freeze describing exact feature maps, projected
  observables, kernels, hyperparameter budgets, controls, and stopping rules.
- A source-bound preflight proving zero calibration/final-test reads and no
  write path beneath locked final payloads.
- A compute review against the reference laptop before scale-up.
- A new figure series for the exploratory branch, beginning with RFIG-024,
  that records the protocol boundary before any new model result.
- A validation suite covering leakage guards, matched rows, source provenance,
  diagnostic completeness, and fail-closed reporting.
- A committed future-research discussion row for every failure, resource stop,
  undefined metric, terminal nonadvancement, or scientific negative result.
  The suggestion must remain outside the active pipeline and require a new
  prospective protocol before it can be tested.

D008 now provides the accepted implementation freeze in
`docs/post_gate5_implementation_freeze.md` and
`configs/post_gate5_exploratory.yaml`. The accepted scope authorizes
implementation and synthetic validation only; a separate clean-source
execution decision is still required before any development-row fit.

## Machine-readable source

The near-term and future-only boundaries are recorded in
`data/processed/reporting/post_gate5_exploratory_protocol_matrix.csv`.
