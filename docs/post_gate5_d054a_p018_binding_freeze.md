# D054-A P018 Stage 1 Binding Freeze

Version: 0.1.0
Decision: D054-A
Parent: D053-C
Prospective protocol: P018
Prepared and accepted: 2026-07-16
Status: **Binding freeze only; no audit execution, data read, dataset generation, model fit, or Gate 6 authority**

## 1. Purpose

D054-A binds every input that D053-C intentionally left open before a future
Stage 1 numerical audit. It is a prospective methods record, not execution
authority. The machine-readable contract is
`configs/post_gate5_d054a_p018_binding_freeze.yaml`.

The binding uses only source code and frozen configuration semantics. It does
not read a scenario manifest, development feature row, outcome label,
calibration row, or final-test row. It creates no DLA, no numerical audit
result, no dataset, and no model.

## 2. Fixed physical scope

The audit state is `z=(r,v,m)` in Earth-centered J2000/ICRF-compatible inertial
Cartesian axes, with position in km, velocity in km/s, and mass in kg. The base
coordinate group is proper rotation `SO(3)`. Translations and reflections are
not included.

F0 is Earth point-mass gravity; F1 adds Moon and Sun third-body gravity; F2
adds Earth J2. Deterministic solar radiation pressure is explicitly excluded.
The frozen simulator has no directional SRP acceleration, and the selected
scenario disturbance is scalar pressure-swing noise rather than the dormant
SRP process-noise entry. Adding SRP would be a new force-model and validation
protocol, not a P018 schema change.

The future context record has fixed Moon/Sun position vectors, the Earth J2
axis, and target position/velocity vectors. Candidate burn direction is a
transformed input, not fixed context. The frozen crew-axis mapping introduces
no inertial body-axis vector because attitude is aligned to the burn before
that check.

## 3. Algebraic binding

The audit uses four spin-half qubits with

`V(R)=u(R) tensor-product u(R) tensor-product u(R) tensor-product u(R)`.

Because four is even, the two possible `SU(2)` lifts of an `SO(3)` rotation have
the same four-qubit action. The raw collective generators are

`J_x=-0.5i sum_l X_l`, `J_y=-0.5i sum_l Y_l`, and
`J_z=-0.5i sum_l Z_l` for `l=0,...,3`.

The real DLA basis is the complete 255-element trace-free Pauli basis
`B_P=iP`, for nonidentity `P` in `{I,X,Y,Z}^4`, ordered lexicographically with
qubit 0 leftmost. The inner product is

`<A,B>=Re Tr(A^dagger B)/2^4`.

The only admitted algebra generators are local `X_l` and `Z_l` controls plus
nearest-neighbor `Z0Z1`, `Z1Z2`, and `Z2Z3` entanglers. A future audit must
verify that their coefficient-space Lie closure is exactly 255 dimensional.
If it is not, the audit stops; it cannot adapt the basis or generator set.

This binds an algebraic probe only. It does not define a PQC encoding, ansatz,
measurement, optimizer, or a horizontal-generator claim.

## 4. Context, rotations, and cases

D054-A binds both a dynamical stabilizer and a task stabilizer. The former uses
only active force vectors; the latter also includes the fixed target frame.
The latter may define `c_H` for a future model mechanism because the label and
constraints use the target frame. The generic rule is exact: zero independent
directions implies `SO(3)`, one implies axial `SO(2)`, and two or more imply an
identity connected stabilizer. The rank uses direct SVD and the D053-C relative
threshold rule.

The rotation suite contains identity, 90-degree axis rotations, a diagonal
pi rotation, and two non-axis-aligned rotations. Every rotation is constructed
with float64 Rodrigues arithmetic and checked for orthogonality and determinant
one. Joint covariance rotates state, all context vectors, and burn direction;
fixed-context breaking rotates state and burn direction only.

The future audit is bound to the 36 label-blind identities
`{F0,F1,F2} x {G01,...,G12} x replicate 000002`. These are candidate-2,
decision-set-1 identities across every development group, covering U0-U4 and
the C/T base trajectories. Calibration and both final-test splits are
prohibited. Existing D006-D049 rows cannot be used because their feature
payload lacks the context tensor.

The maximum later workload is 936 propagations: 36 cases times unrotated, six
joint-rotated, and six fixed-context-rotated trajectories at baseline and
tightened DOP853 settings. This is a ceiling, not execution authorization; a
clean-source compute preflight is still required.

## 5. Defect and target binding

`eps_a` is fixed at `1e-12 km/s^2`, a numerical denominator guard only. It is
not fitted or treated as a physical force magnitude. The primary target remains
`robust_total_correction_delta_v_m_s`; `y_scale=20 m/s`, derived before outcome
inspection from the frozen maximum candidate delta-v and infeasible-regret
penalty. The scale changes neither the target nor any decision threshold.

P018 stops before model design unless, across F1/F2 and all six nonidentity
rotations, at least 75 percent of stable cases have `D_y >= 0.01` (0.2 m/s),
and the absolute Spearman association of `D_break` with `D_y` is at least 0.30
with a two-sided 95 percent cluster-bootstrap interval excluding zero. The
cluster is the unrotated source case. This is a target-mechanism screen, not a
model-performance criterion.

## 6. Outputs and figures

Future immutable audit outputs are bound under
`data/processed/reporting/post_gate5_p018_stage1_audit/`, including the input,
case, generator, basis, closure, spectrum, covariance, breaking, target, and
decision records. D054-A creates none of them.

RFIG-086 is a generated methods-boundary diagram for this freeze. RFIG-087
through RFIG-089 are reserved for a later authorized audit's spectrum,
covariance/breaking, and target-sensitivity evidence. No placeholder result
figure is produced.

## 7. Next decision

The next decision is D055: whether to authorize one clean-source, development-
only numerical audit against this exact binding. It must retain D053-C's direct
SVD, closure, rank-stability, resource, and DOP853 replay stops. It may not
activate SRP, change this representation or input binding, fit a model, read
calibration/final-test data, use hardware/GPU, or open Gate 6.
