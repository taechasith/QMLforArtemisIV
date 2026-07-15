# D053-C Stage 1 Numerical-Audit Freeze

Version: 0.1.0
Decision: D053-C
Parent contract: D052-C
Prospective protocol: P018
Prepared and accepted: 2026-07-16
Status: **Numerical architecture frozen; no numerical audit, dataset read, model fit, figure, or Gate 6 authority**

## 1. Purpose and boundary

D053-C records the human research lead's locked numerical architecture for the
future Stage 1 audit in `docs/post_gate5_d052_symmetry_breaking_math_contract.md`.
It freezes how a concrete DLA centralizer and trajectory-covariance audit must
be calculated. It does not choose the concrete representation, circuit,
generators, DLA basis, rotations, trajectory cases, target scale, or model.
Those objects are not yet scientifically identified, so selecting them after
an audit result would be post-outcome design.

No DLA has been constructed, no SVD has been run, no trajectory has been
propagated for P018, no development row has been read, and no figure has been
rendered under D053-C. Gate 6 remains unauthorized.

The machine-readable freeze is
`configs/post_gate5_d053_symmetry_audit_freeze.yaml`.

## 2. DLA coefficient-space contract

For an audited q-qubit representation, let `L` be the real DLA of
skew-Hermitian operators. Its frozen basis is `B_1, ..., B_p`, orthonormal
under

`<A,B> = Re Tr(A^dagger B) / 2^q`.

This normalization makes Pauli-derived skew-Hermitian basis elements
unit-norm. The representation generators `J_k` are archived in their raw form
and then normalized to unit Hilbert-Schmidt norm before numerical assembly.
The normalization changes singular values but not the exact centralizer.

For every connected audited generator and every basis element, construct the
stacked real coefficient matrix

`C_((k,b),a) = <B_b, [J_k, B_a]>`.

Columns index the candidate DLA element and the stacked rows index `(k,b)`.
The audit uses direct Pauli/DLA coefficient arithmetic. It must not construct
a dense `4^q` by `4^q` operator-space supermatrix. This avoids treating the
full q=8 operator space as a local-memory problem when only a bounded,
audited DLA is relevant.

Before extracting a nullspace, the audit must record the basis-closure leakage

`L_(k,a) = ||[J_k,B_a] - sum_b C_((k,b),a) B_b||_HS`.

It stops if any leakage exceeds

`100 * eps_float64 * max(1, sigma_max)`.

A projected coefficient matrix cannot certify a centralizer when the frozen
basis is not closed under the audited commutator. The failure must be reported
as `dla_basis_not_closed`; it may not be hidden by truncating the leakage.

## 3. Direct SVD rank and centralizer rule

The only permitted rank/nullspace calculation is

```python
U, singular_values, Vh = numpy.linalg.svd(C, full_matrices=False)
```

For a nonempty generator set, the matrix must have at least as many rows as
columns, so economy SVD returns every right-singular vector. Define

`tau = max(C.shape) * eps_float64 * sigma_max`.

At each threshold, `rank(tau)` is the number of singular values strictly
larger than `tau`; the remaining rows of `Vh` span the numerical centralizer.
The full spectrum, shape, dtype, `sigma_max`, threshold, rank, nullity,
generator provenance, basis hash, and every closure-leakage value are required
raw audit outputs.

The centralizer dimension must be identical at `0.1*tau`, `tau`, and
`10*tau`. A change at any of those preregistered thresholds is a hard numerical
stability failure, not a license to choose the favorable threshold. If
`sigma_max` is zero, the audit records `zero_commutator_map` and the full
frozen basis is the centralizer; it must not divide by zero.

`eigh(C^H C)` and any normal-equation eigensolve are prohibited because they
square the condition number. QR rank heuristics, iterative/sparse solver
substitutions, and silent fallback solvers are also prohibited without a new
prospective decision.

For an identity connected residual stabilizer, there are no infinitesimal
constraints: the audit sets `c_H = L` directly rather than passing an empty
matrix to a numerical solver.

## 4. Local resource boundary

The future audit is bounded to q=4, q=6, and q=8 with at most 1,024 frozen DLA
basis elements and at most three connected rotation generators per centralizer
calculation. The largest permitted direct coefficient matrix is therefore
`3,072 x 1,024`; its float64 entries alone occupy about 24 MiB. This is a
bounded coefficient calculation, not evidence that a larger DLA is easy to
simulate classically.

Only one DLA audit may run at a time on the project reference CPU-only laptop.
If DLA closure exceeds 1,024 basis elements, the audit stops as
`dla_basis_over_ceiling`. It must not truncate the basis, switch solvers, use
the GPU, or infer a complexity advantage from the stop.

## 5. Decoupled trajectory-covariance replay

The orbital check is mathematically and operationally separate from the DLA
SVD. It uses the repository's `scipy.integrate.solve_ivp(method="DOP853")`
path in `src/openqfuel/dynamics.py`.

Each future audit case is propagated twice:

1. With `ForceModelSettings.for_fidelity(fidelity)`: F0/F1 use `rtol=1e-10`,
   `atol=1e-12`, and a 600 s maximum step; F2 uses `rtol=1e-11`,
   `atol=1e-13`, and a 300 s maximum step.
2. With the existing `ForceModelSettings.tightened()` replay: `rtol` and
   `atol` are divided by 100 and the maximum step is halved.

The initial state, epoch, force flags, ephemeris, time conversion, maneuvers,
constraints, frame, rotation, duration, and evaluation epochs are identical
between replays. Changing any physical setting would confound numerical error
with a physical fixed-context effect.

At the common replay epochs, the audit evaluates D052-C's force-level
`D_cov` and `D_break`. A nonzero `D_break` can be called physical only when it
exceeds ten times the larger default/tightened `D_cov`, and its replay change

`abs(D_break_tightened - D_break_default) / max(D_break_tightened, 1e-15)`

is at most 1 percent. A violation stops the affected effect as
`integrator_sensitive_or_numerical_artifact`; it cannot be used to motivate a
PQC. The floor and replay checks apply to every frozen case and evaluation
epoch before an aggregate is reported; an average cannot hide an unstable
case. If a later authorized audit computes `D_y`, it must regenerate both
labels and apply the same 1 percent replay rule with a separately frozen,
positive label scale.

## 6. Required future inputs and outputs

Before any execution decision, a separate manifest must freeze the group
representation, raw/normalized generators, DLA basis and its provenance hash,
complete context inventory, stabilizer case, rotations, development-only
strata, common evaluation epochs, positive `eps_a`, target scale, output paths,
and paper-figure registry entries. D053-C does not supply those inputs.

An authorized audit must preserve an input manifest, basis/generator records,
the full singular-spectrum table, centralizer summary, closure table, default-
versus-tightened covariance table, and any separately authorized term-wise
breaking/target-sensitivity records. It must then create paper-ready figures
from immutable raw evidence. D053-C creates no placeholder and reserves no
figure ID.

## 7. Claim boundary and next decision

D053-C is a numerical-method freeze. It establishes no actual symmetry,
centralizer, physical breaking, target response, predictive improvement,
sample-complexity result, QML invention, quantum advantage, or Gate 6 result.

The next eligible action is not an experiment: it is a separate prospective
decision that binds the remaining mathematical inputs and explicitly authorizes
one bounded Stage 1 audit. Model fitting remains prohibited until the Stage 1
completion criteria in D052-C pass.
