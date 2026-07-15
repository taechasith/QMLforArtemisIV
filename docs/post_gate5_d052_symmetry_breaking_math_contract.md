# D052-C Stage 1 Mathematical Contract: Learnable Symmetry Breaking

Version: 0.3.0
Decision: D052-C
Parent discussion: D051-C
Prospective protocol: P018
Prepared: 2026-07-15
Status: **Theory-only contract; D053-C numerical architecture and D054-A inputs frozen; no audit execution, data generation, model fit, or Gate 6 authority**

## 1. Research question

Can a variational quantum model with an exactly symmetric base circuit and a
bounded, context-conditioned set of symmetry-breaking generators learn the
departure from a central-gravity symmetry more efficiently than strong
classical strict-equivariant, approximately equivariant, and non-equivariant
controls on the existing cislunar surrogate task?

This is an empirical hypothesis. It is not a planned discovery, a world-first
claim, a sample-complexity theorem, or evidence of quantum advantage.

## Literature boundary

Classical models already provide relaxed and explicit symmetry-breaking
mechanisms. Wang, Walters, and Yu study approximately equivariant networks for
imperfectly symmetric dynamics:
https://proceedings.mlr.press/v162/wang22aa.html. Xie and Smidt construct
equivariant symmetry-breaking sets:
https://arxiv.org/abs/2402.02681. These methods are mandatory comparators and
invalidate any assumption that broken symmetry is intrinsically a classical
blind spot.

Dynamical Lie algebras can characterize reachable directions, information
matrix rank, and overparameterization behavior in QNNs, but that does not imply
a predictive or sample-complexity advantage on this task. See Larocca et al.,
"Theory of overparametrization in quantum neural networks",
https://www.nature.com/articles/s43588-023-00467-6. The DLA in P018 must be
computed for the concrete circuit rather than invoked as a qualitative label.

These sources orient a future protocol; they are not additions to or
reinterpretations of the closed Gate 4 review.

## 2. Repository-grounded physical scope

The current simulator implements:

- F0: Earth point-mass gravity and impulsive maneuvers;
- F1: F0 plus Moon and Sun point-mass third-body gravity, fixed-direction
  finite burns, and mass depletion;
- F2: F1 plus Earth J2 and tighter numerical integration.

The implementation is in `src/openqfuel/dynamics.py`. Deterministic solar
radiation pressure is disabled. `configs/uncertainty_model.yaml` contains an
SRP process-noise source, but `configs/scenario_generation.yaml` selects a
different scalar process-noise source and does not implement a directional SRP
acceleration. SRP is therefore outside this contract unless a later protocol
adds and validates it prospectively.

The current feature payload contains spacecraft position/velocity, candidate
burn vector, navigation perturbations, scalar timing/resource quantities,
categorical context, and five Earth-centered derived invariants. It does not
contain explicit Moon/Sun ephemeris vectors, the Earth J2 axis, or the target
state/frame. Existing D006-D049 rows therefore cannot support a fair
context-conditioned symmetry-breaking comparison without a new, separately
authorized development schema.

The primary target, robust total correction delta-v, is defined mainly from
planned burn magnitude and execution uncertainty. Its dependence on broken
gravitational symmetry is indirect through candidate construction. Stage 1
must quantify target sensitivity before this target can support the proposed
mechanism. Feasibility, terminal margin, and terminal errors are more directly
dynamics-dependent, but changing the primary target requires a separate
prospective decision.

## 3. State, context, and group action

Let the dynamic state be

`z(t) = (r(t), v(t), m(t)) in R^3 x R^3 x R_+`.

Let the candidate-control input contain burn start and duration plus the
inertial burn direction `u in S^2`. Let scalar mission and uncertainty features
be collected in `q`.

Let the environment context be

`b(t) = (r_M(t), r_S(t), e_J2, r_T, v_T, c)`

where `r_M` and `r_S` are geocentric Moon and Sun vectors, `e_J2` is the Earth
J2 symmetry axis, `(r_T,v_T)` defines the fixed terminal state/frame, and `c`
contains scalar or discrete mission constraints.

The base coordinate group is `G = SO(3)`. For `R in SO(3)`, define the joint
action

`R . (r,v,u,r_M,r_S,e_J2,r_T,v_T) =`
`(Rr,Rv,Ru,Rr_M,Rr_S,Re_J2,Rr_T,Rv_T)`.

Mass, time, thrust magnitude, uncertainty magnitudes, and categorical labels
are invariant scalars unless Stage 1 proves a different representation.

Translations are not included: the Earth-centered potential and fixed Earth
origin are not translation invariant. A generic `E(3)` claim is therefore too
broad for this pipeline. Reflections or parity may be audited separately, but
the contract assumes only proper rotations until every orientation-sensitive
constraint is checked.

Joint rotation of state and all context vectors is coordinate covariance, not
a physical symmetry advantage. The physical environment holds `b=b_0` fixed.
Its residual symmetry group is the stabilizer

`H_b = {R in SO(3) : R . b_0 = b_0}`.

For central Earth gravity alone, `H_b = SO(3)`. For isolated J2 with a fixed
axis, the connected stabilizer is rotation about `e_J2`, isomorphic to
`SO(2)`. Fixed non-collinear Moon/Sun/target vectors may reduce the common
stabilizer to a discrete subgroup or the identity. This must be computed from
the actual context; it is not assumed.

## 4. Project force decomposition

The controlled dynamics are

`dot(r) = v`

`dot(v) = a_E(r) + lambda_M a_M(r,r_M)`
`         + lambda_S a_S(r,r_S)`
`         + lambda_J2 a_J2(r;e_J2) + a_T(u,m,t)`

with the existing mass-depletion equation during finite burns.

The central term is

`a_E(r) = -mu_E r / ||r||^3`.

For body `B` in `{M,S}`,

`a_B(r,r_B) = mu_B [(r_B-r)/||r_B-r||^3 - r_B/||r_B||^3]`.

Writing `s=e_J2 . r`, the J2 term implemented by the repository is

`a_J2(r;e_J2) = k(r) [(5s^2/||r||^2 - 1)r - 2s e_J2]`,

`k(r) = 3 J2 mu_E R_E^2 / (2 ||r||^5)`.

During a finite burn,

`a_T(u,m,t) = I_burn(t) T u / (1000 m)`.

The vector `lambda=(lambda_M,lambda_S,lambda_J2)` is a diagnostic interpolation
parameter, not an operational claim. Physical endpoints already exist at F0,
F1, and F2, but those fidelities also change maneuver and integration settings
and are not a clean one-dimensional symmetry-breaking experiment. Any
continuous lambda campaign requires a new controlled generator and separate
authorization.

## 5. Covariance and symmetry-breaking defects

### Proposition 1 - joint coordinate covariance

For every `R in SO(3)`, if state, ephemerides, J2 axis, target frame, and burn
direction are all rotated jointly, each acceleration term satisfies

`a(Rr; Rb, Ru) = R a(r; b, u)`.

**Status:** new project-specific derivation from established vector identities;
analytically supported, not yet numerically verified by P018.

**Proof strategy:** rotations preserve norms and inner products. Substitute
`Rr`, `Rr_B`, `Re_J2`, and `Ru` into each term, factor out `R`, and use
`R^T R = I`. Target-frame constraints built only from norms, dot products, and
cross products are also jointly covariant when the target state is rotated.

### Proposition 2 - fixed-context residual symmetry

With `b=b_0` fixed, exact equivariance is guaranteed only for `R in H_b`.
For general `R notin H_b`,

`a(Rr; b_0, Ru) != R a(r; b_0, u)`.

**Status:** direct consequence of Proposition 1 and the stabilizer definition,
conditional on the complete context inventory.

### Numerical defects

The joint-covariance defect is

`D_cov(R,r,b,u) = ||a(Rr;Rb,Ru)-R a(r;b,u)||`
`                 / (||a(r;b,u)|| + eps_a)`.

The fixed-environment breaking defect is

`D_break(R,r,b_0,u) = ||a(Rr;b_0,Ru)-R a(r;b_0,u)||`
`                     / (||a(r;b_0,u)|| + eps_a)`.

The repropagated scalar-label defect is

`D_y(R,x,b_0) = |y(T_R x;b_0)-y(x;b_0)| / y_scale`.

`y(T_R x;b_0)` must be regenerated by the simulator in the fixed environment;
it cannot be created by rotating or copying an existing label.

A trajectory-level dynamic breaking severity is

`S_dyn = RMS_t ||a_M+a_S+a_J2|| / (||a_E|| + eps_a)`.

Stage 1 must also report term-wise severities and maximum values. A single
aggregate cannot hide cancellation between Moon, Sun, and J2 terms.
`eps_a` must be a frozen positive acceleration scale with units of km/s^2;
it cannot be selected from observed model performance.

## 6. Target-mechanism admission test

Before model design, Stage 1 must test whether the frozen target responds to
the measured breaking severity. The audit must report, by grouped development
stratum:

- the distribution of `S_dyn`, `D_break`, and `D_y`;
- association between each severity and robust cost, feasibility, terminal
  margin, and terminal errors;
- counterexamples with high dynamic breaking but negligible target change;
- whether time or trajectory identity alone explains the association;
- whether the existing feature payload contains the context needed to predict
  the observed change.

If robust cost has negligible preregistered sensitivity, P018 must stop before
model fitting. It may recommend a new target in future work, but it cannot
promote a secondary target after seeing model outcomes.

## 7. Quantum model contract

Let `V(R)` be the selected q-qubit representation of the audited group and let
`L = Lie_R{i H_j}` be the skew-Hermitian dynamical Lie algebra generated by the
candidate Hermitian Hamiltonians `H_j`. Define the centralizers

`c_G = {X in L : [X,V(R)] = 0 for every R in G}`

and

`c_H = {X in L : [X,V(R)] = 0 for every R in H_b}`.

`c_G` contains base-symmetry-preserving directions. Directions that break `G`
but preserve the audited residual symmetry must lie in

`m = c_H intersect c_G^perp`,

where orthogonality uses the real Hilbert-Schmidt inner product
`<X,Y> = Re Tr(X^dagger Y)`. If `m` is empty, the proposed mechanism has no
admissible breaking direction and is rejected.

The term *horizontal generator* is permitted only if the implementation proves
the reductive condition `[c_G,m] subseteq m` and records the connection or
orthogonal projection defining horizontality. Otherwise the operators are
called **symmetry-breaking complement generators**.

With `A_j in c_G`, `B_k in m`, and audited breaking descriptors `s(x,b)`, the
candidate ansatz is

`U_(theta,beta)(x,b) = product_l exp([`
`  sum_j theta_(l,j) A_j + sum_k beta_(l,k)(s(x,b)) B_k]) E(x,b)`.

The coefficient map must satisfy `beta(0)=0`, for example

`beta_(l,k)(s) = s_k * beta_tilde_(l,k)`.

This makes the perfect-base limit an explicit ablation. The number of
complement generators, coefficient parameters, layers, measurements, and
classical preprocessing operations must be frozen. The model is rejected if
the complement spans an effectively unrestricted circuit without a bounded
symmetry-breaking mechanism.

For scalar prediction,

`f_(theta,beta)(x,b) = Tr[O U_(theta,beta)(x,b) rho_0`
`                           U_(theta,beta)(x,b)^dagger]`.

The empirical loss remains

`L(theta,beta) = (1/N) sum_i ell(f_(theta,beta)(x_i,b_i), y_i)`.

The exact encoding, initial state, observables, qubits, depth, gates, shots,
noise channels, connectivity, state-preparation cost, and decoding cost remain
undefined until the Stage 1 audit identifies a nontrivial admissible group and
context representation. They cannot be selected from model outcomes.

## 8. Required classical and quantum controls

Every model receives the same context vectors, scalar features, grouped rows,
parameter-search budget, and outcome access.

Required classical controls are:

1. C06 on the frozen original feature contract;
2. a strict equivariant model with explicit context/spurion vectors;
3. an approximately equivariant or relaxed-equivariance model;
4. a non-equivariant geometric model with matched capacity;
5. a parameter- and compute-matched classical model using the same breaking
   descriptors as the PQC.

Required quantum controls are:

1. the symmetry-preserving PQC with `beta=0`;
2. the symmetry-breaking PQC with bounded complement generators;
3. the same PQC with context descriptors permuted or removed;
4. the same PQC without the symmetric base constraint;
5. the frozen initialization and optimizer ablations from D051-C.

Classical tensor growth, sample-efficiency collapse, and a quantum-specific
inductive bias are empirical hypotheses. They are not assumptions in the
baseline design.

## 9. Falsifiable hypotheses

### H1 - physical decomposition

The audited base dynamics pass joint covariance within a solver-derived frozen
tolerance, while fixed-context rotations produce a reproducible nonzero
breaking defect explained by identified physical terms.

**Reject if:** joint covariance fails, the context inventory is incomplete, or
the defect is a numerical/frame artifact.

### H2 - bounded adaptation

At preregistered breaking severities, the bounded symmetry-breaking PQC
improves over its `beta=0` ablation without losing the perfect-base limit.

**Reject if:** the improvement is absent, unstable across seeds, or requires an
unbounded complement-generator family.

### H3 - classical-specific predictive result

The candidate must beat both C06 and the strongest matched approximately
equivariant classical control by the frozen 5% development criterion, with the
paired uncertainty bound and no safety regression.

**Reject if:** either threshold fails or the effect disappears under identical
features, tuning, and compute accounting.

### H4 - sample-efficiency hypothesis

For breaking severity `s`, define

`N_m(epsilon,delta;s) = min n such that`
`Pr[R_s(f_hat_(m,n)) - R_s^* <= epsilon] >= 1-delta`.

Because `R_s^*` is unknown, the executable protocol must freeze an operational
estimator, confidence method, and learning-curve rungs before fitting. The
existing `[128,256,512,1024]` rungs may support a bounded empirical comparison;
they cannot establish an asymptotic `O(sqrt(N))` law.

**Reject if:** the confidence interval for the candidate's required sample
count overlaps or exceeds the strongest classical control, or if the result is
sensitive to the estimator or rung selection.

## 10. Counterexample search

Stage 1 must actively test these failure modes:

- rotating all context vectors removes the apparent breaking, showing only
  coordinate covariance;
- Moon/Sun/target vectors reduce the stabilizer to identity, leaving no useful
  nontrivial group bias;
- a classical relaxed-equivariance model learns the same breaking with lower
  cost;
- robust cost is insensitive to the physical breaking terms;
- time or trajectory identity acts as a shortcut for ephemeris context;
- the PQC complement generators make the circuit effectively generic;
- gradient concentration or shot noise erases the proposed adaptation;
- F0/F1/F2 differences are caused by maneuver/integrator changes rather than
  symmetry-breaking physics;
- fixed-frame preprocessing creates an artificial defect;
- a laptop simulation timeout is mistaken for a complexity lower bound.

## 11. Scientific status of claims

- Central-force `SO(3)` covariance: **established mathematical result**.
- Project force decomposition: **direct consequence of repository code**.
- Joint covariance proposition: **new project-specific derivation**, pending
  numerical verification.
- Fixed-context stabilizer formulation: **direct consequence of group action**,
  pending complete context audit.
- Horizontal/complement generator construction: **design hypothesis**, pending
  an explicit DLA and reductive-decomposition proof.
- Better trainability or prediction: **empirical hypothesis**.
- Lower sample complexity: **empirical hypothesis**, not a scaling theorem.
- Classical tensor explosion: **speculation until measured or proven**.
- Quantum advantage or world-first discovery: **unsupported and prohibited**.

## 12. Resource and data-access boundary

Stage 1 may use source code, equations, configs, and a separately authorized
small development-only numerical audit. It may not read calibration or
final-test rows, fit a model, submit hardware/GPU jobs, run a mission loop, or
open Gate 6. The reference envelope remains CPU-only q=4/6/8, 32 GiB RAM, and
one expensive simulator process at a time until a new compute preflight passes.

No experiment figure is generated by this theory contract. A later authorized
Stage 1 audit must create paper-ready figures for term-wise breaking severity,
joint-covariance residuals, fixed-context defects, target sensitivity, and
counterexamples, each backed by immutable raw evidence and a figure-registry
entry.

## 13. Stage 1 completion rule

Stage 1 is complete only when all of the following are available:

1. complete context/spurion inventory and group representations;
2. symbolic or algebraic verification of each force and constraint term;
3. solver-tolerance-derived numerical audit plan;
4. target-mechanism admission threshold frozen before labels are inspected;
5. classical approximately equivariant controls specified;
6. explicit DLA, centralizer, complement, and any horizontality proof;
7. data schema, resource ceiling, stop rules, and required figures frozen;
8. a separate prospective decision authorizing the bounded audit.

Until then, P018 remains discussion-only and Gate 6 remains unauthorized.

## 14. D053-C numerical-method amendment

D053-C freezes the numerical method for any future Stage 1 execution in
`docs/post_gate5_d053_symmetry_audit_freeze.md`. It requires direct SVD of the
closed Pauli/DLA coefficient commutator matrix, complete singular-spectrum and
rank-stability records, and a DOP853 default-versus-tightened replay. D054-A
subsequently binds the representation, DLA basis/generators, rotations,
development-only cases, target scale, output paths, and figure registry in
`docs/post_gate5_d054a_p018_binding_freeze.md`; it still authorizes no audit
execution.

## 15. D054-A input-binding amendment

D054-A fixes the pending Stage 1 inputs prospectively: deterministic SRP is
excluded; the audit uses the q=4 collective-spin `SO(3)` representation and a
255-element skew-Hermitian Pauli basis; the prescribed local `X/Z` and
nearest-neighbor `ZZ` generators must close exactly to that basis; and the
rotation suite, development-only identity rule, `eps_a`, target normalization,
future output paths, and figure registry are fixed. It also binds separate
dynamical and task-context stabilizer records so a later model mechanism cannot
ignore label or target-frame constraints.

This amendment creates no numerical result. RFIG-086 is a methods-boundary
figure made only from the accepted freeze. RFIG-087 through RFIG-089 are empty
reservations for a later authorized audit. D055 must authorize one bounded audit
before the source manifest or any development identity is read.
