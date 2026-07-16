# Draft Response to Structural Review Comments

This draft responds only to the structural and clarification points supplied
with the manuscript revision. It does not imply that a particular venue or
reviewer has accepted the paper. Update page and line references after the
final submission build.

## Manuscript position

The manuscript is a negative-results and governance-benchmark paper. It does
not propose a new QML algorithm, claim quantum advantage, or recommend a model
for flight use. Its contribution is a source-bound, frozen public-data
evaluation that makes both positive and negative model evidence auditable for
a high-consequence decision-support context.

## Response to the organization and research-question comments

We reorganized the Introduction into distinct **Problem statement**,
**Research objective**, and **Central research question** subsections. The
revision now presents one central question: whether simulated quantum-kernel
representations add empirical predictive value to the cislunar
trajectory-correction benchmark when fairly compared with physics-based
controls. The former four questions are retained as narrow operational
sub-questions that resolve this central question; they are no longer presented
as four independent study aims.

## Response to the trajectory-correction context comment

The opening of the Introduction explicitly defines the trajectory as a crewed
spacecraft path in the Earth--Moon system and a trajectory-correction maneuver
as an intentional change in velocity, summarized as correction delta-v in
m/s. It also explains why correction planning is a coupled decision problem:
burn timing and delta-v interact with navigation uncertainty, crew timelines,
entry conditions, and reserve constraints. The target is therefore a
benchmark-defined robust correction cost under uncertainty, not a generic
curve-fitting target.

## Response to the quantum-method formulation comment

The Methods section now includes an explicit mathematical contract for Q01.
It defines the $2^q$-dimensional complex Hilbert space, all-zero initial state,
input-dependent unitary feature map, pure-state density-operator notation, and
fidelity-style kernel. The revision also states that Q01 was evaluated through
exact classical statevector simulation for $q\in\{4,6,8\}$, with no hardware
shots, quantum-device noise, or quantum-hardware performance claim. Matched
classical controls remain part of the protocol so that a distinct quantum
representation is not confused with demonstrated empirical value.

## Bound of the revision

These revisions improve conceptual clarity and mathematical reproducibility.
They do not alter the frozen data boundary, model configurations, thresholds,
seeds, results, or the paper's negative conclusion.
