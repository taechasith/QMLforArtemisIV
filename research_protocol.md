# OpenQFuel-Cislunar Research Protocol

Version: 0.6.20
Status: Gates 1-5 accepted; Gate 5 closed with technical outcome FAIL; D011-R1 development-only campaign complete with valid exploratory negatives; D012 future-protocol discussion opened; D013-C planning accepted; D014-C freeze proposal accepted; Gate 6 unauthorized
Prepared: 2026-07-10  
Updated: 2026-07-14
Recommended next action: Prepare D015 implementation and synthetic-validation authorization only if needed; no experiment, development-data fitting, refit, rerank, calibration/final-test access, hardware/GPU work, Gate 5 reinterpretation, or Gate 6 is authorized by D014-C

## 1. Proposed title

Can Quantum Machine Learning Improve Propellant-Efficient Human-Rated Cislunar
Guidance? An Open, Flight-Ephemeris-Calibrated Benchmark

## 2. Purpose

This study will determine whether a quantum machine-learning surrogate can
improve robust trajectory-correction planning for a crewed cislunar spacecraft
when compared fairly with strong classical machine-learning and numerical
optimization methods.

The long-term invention objective is to use the complete experimental record to
design a new QML method that can beat the strongest documented NASA-relevant
and repository baselines under fair locked-split tests. This objective is
subordinate to scientific correctness: no NASA-used QML method is asserted
unless a cited public source identifies it, and every completed result must
label what evidence is useful for a later invention and what use is prohibited
as post-outcome rescue.

The experiment has two linked parts:

1. Predictive benchmark: compare classical ML and QML performance on robust
   trajectory-cost and feasibility prediction.
2. Mission benchmark: insert selected models into a safety-filtered planning
   loop and evaluate propellant, mission feasibility, crew constraints, tail
   risk, and computation under numerical simulation.

The study is designed so that no quantum improvement is a valid and useful
result.

## 3. Governance and decision authority

The assistant research partner is responsible for literature synthesis, source
provenance, technical design, implementation, execution planning, validation,
statistical analysis, documentation, and recommendations.

The human research lead is the final decision authority. At each gate, the
assistant supplies:

- the decision requested;
- the recommended choice;
- the evidence supporting that choice;
- unresolved risks;
- the consequences of acceptance or rejection.

The human research lead answers accept, reject, or revise. Decisions and
post-freeze deviations are recorded in docs/decision_log.md.

After D013-C, the assistant may choose and commit the recommended planning
path when the human research lead has explicitly delegated that choice, but
the following remain non-delegable without a separate prospective record:
calibration access, final-test access, hardware/GPU execution, Gate 5
reinterpretation, Gate 6, and public claims of superiority or operational
readiness.

## 4. Scope

### 4.1 Included

- Orion post-injection cislunar trajectory-correction planning.
- Artemis II flight-derived ephemeris for simulator calibration.
- An Artemis IV-relevant crewed cislunar reference scenario.
- Robust burn timing, magnitude, direction, and thruster-class decisions.
- Mass depletion, finite burns, navigation uncertainty, execution uncertainty,
  public crew timelines, protected sleep, acceleration, mission duration,
  space-weather exposure proxy, reserve, and abort feasibility.
- Ground-based decision support with a deterministic safety filter and fallback.
- Publicly accessible data, standards, software, and fully documented simulated
  data derived from those sources.

### 4.2 Excluded from the initial study

- SLS ascent optimization.
- Atmospheric entry guidance and landing control.
- SpaceX HLS descent or ascent control without sufficient public parameters.
- Life-support resource optimization as a separate objective.
- Direct autonomous command of a spacecraft.
- Flight certification or claims of operational readiness.
- Unverified proprietary values presented as NASA or SpaceX facts.

### 4.3 Terminology

The engineering term propellant is used instead of generic fuel. Human-rated
means that crew schedules, exposure, workload, contingency, and safety
constraints are represented. It does not mean the research software is
certified for human spaceflight.

## 5. Research questions

RQ1. Under identical data and tuning rules, can a QML surrogate match or exceed
strong classical models in predicting robust trajectory cost and feasibility?

RQ2. Does any predictive improvement translate into lower propellant use
without increasing mission or crew-safety violations?

RQ3. How do the models behave under limited training data, finite-shot noise,
hardware-derived noise, and out-of-distribution mission conditions?

RQ4. If the benchmark reveals a useful quantum residual signal, can a
multi-fidelity physics-constrained quantum residual surrogate improve the
accuracy-safety-propellant Pareto frontier?

RQ5. Are the results credible enough to support future mission-planning
research, and what additional evidence would be required for operational use?

## 6. Hypotheses and claim discipline

Primary null hypothesis:

H0: No evaluated QML method reduces closed-loop robust correction delta-v
regret relative to the best tuned classical method while preserving
non-inferior safety and feasibility.

Primary alternative hypothesis:

H1: At least one QML method produces a practically meaningful reduction in
closed-loop robust correction delta-v regret while meeting every safety gate.

The frozen Gate 2 practical threshold is the larger of 0.25 m/s or 10 percent
of the strongest classical model's mean correction delta-v. The lower bound of
the paired 95 percent confidence interval must exceed that threshold, and the
safety-violation rate must be non-inferior within an absolute margin of 0.001.
Propellant mass is a secondary rocket-equation sensitivity because a complete
flight-specific engine-performance model is not public.

A QML model is not declared better from prediction accuracy alone. Mission
feasibility is a hard gate. Quantum advantage is not claimed from classical
quantum simulation or from an experiment that omits data-loading, shot,
mitigation, queue, or communication costs.

## 7. Decision problem

At a navigation update, define a state-context vector:

    z = [r, v, m, P, mission time, candidate burn plan,
         crew availability, environmental context]

where r and v are position and velocity, m is spacecraft mass, P is navigation
uncertainty, and the candidate burn plan contains burn time, magnitude,
direction, duration, and thruster class.

The learned surrogate estimates:

- nominal and robust delta-v;
- propellant consumed as a sensitivity output;
- terminal position and velocity error;
- entry-interface or target-orbit margins;
- probability or calibrated score of plan feasibility;
- uncertainty in each predicted output.

The reference robust objective is:

    minimize J(u) = delta_v_nominal(u) + 3 sigma_delta_v(u)

with a secondary non-Gaussian assessment based on conditional value at risk.
Hard constraints include terminal-state margins, reserve, actuator limits,
protected crew periods, acceleration, computation deadline, and contingency
feasibility.

The ML model evaluates or ranks candidate plans. A deterministic optimizer may
refine a candidate. A physics-based safety filter rejects infeasible commands.
A validated classical fallback is always available.

## 8. Public-source and provenance policy

Every input field is classified as one of:

- observed flight data;
- official public specification;
- derived from a cited source;
- simulated from a documented distribution;
- explicit research assumption.

Each source record includes provider, URL, retrieval date, local filename,
units, transformation, uncertainty statement, and redistribution status.

Unknown parameters are never filled with an unattributed best guess. If a
mission-specific distribution is unavailable, the study uses a transparent
bounded sensitivity range. Results are then described as conditional on that
range.

Simulated samples are not called real telemetry. Numerical optimizer outputs
are reference solutions, not physical ground truth.

## 9. Literature review

A systematic scoping review will cover:

1. robust cislunar trajectory correction;
2. ML surrogate guidance and reinforcement learning;
3. QML regression, quantum kernels, and quantum reinforcement learning;
4. quantum optimization for space trajectories;
5. human-spaceflight operational constraints;
6. model and simulation credibility.

Search strings, inclusion criteria, extraction variables, and quality domains
are defined in literature/review_protocol.md. The search log and evidence
matrix will be versioned. Marketing pages and uncited claims cannot establish
algorithmic performance.

## 10. Simulation architecture

### 10.1 Fidelity levels

F0, analytical check model:

- two-body propagation;
- rocket-equation and dimensional checks;
- simple impulsive maneuvers.

F1, dataset-generation model:

- circular restricted three-body or n-body dynamics;
- impulsive or simplified finite burns;
- mass depletion;
- configurable execution and navigation perturbations.

F2, evaluation model:

- Earth-Moon-Sun and required perturbing bodies;
- finite burn and thruster selection;
- time-varying mass;
- public force and ephemeris models;
- crew and operational constraints;
- high-accuracy integration and event handling.

The Python research engine will support batch generation. NASA GMAT will be
used as an independent verification path where the public model permits.

### 10.2 Artemis II calibration

The flight ephemeris will be divided into calibration and held-out coast arcs
before parameter fitting. Maneuver windows will be taken from public timelines
or inferred only through a documented algorithm.

Validation will compare:

- position and velocity residuals over held-out coast arcs;
- event and maneuver timing;
- trajectory geometry;
- sensitivity to initial-state, force-model, and numerical-integrator choices;
- cross-tool agreement.

The proposed numerical tolerances, five untouched six-hour validation arcs,
release qualification rules, and stop criteria are frozen in
configs/simulator_acceptance.yaml upon Gate 2 acceptance. If F2 fails those
criteria, the study stops at the simulation-validation result.

### 10.3 Credibility

The model record will document intended use, assumptions, calibration domain,
input uncertainty, numerical verification, validation evidence, sensitivity,
failure modes, credibility gaps, and limits of operation following the
principles of NASA-STD-7009B.

## 11. Dataset generation

### 11.1 Experimental design

Initial states, candidate plans, and uncertainties will be sampled using Sobol
sequences or Latin-hypercube sampling. Boundary, tail, and known difficult
conditions receive explicit strata.

Candidate uncertainty variables may include:

- position and velocity estimation error;
- mass and propellant uncertainty;
- thrust magnitude and pointing bias;
- burn start-time and duration error;
- navigation mode;
- missed or delayed maneuver;
- communication delay;
- mission epoch and space-weather stratum.

No distribution will be treated as operationally authentic unless it has a
public mission source. Otherwise it is a sensitivity distribution.

### 11.2 Reference solution

Each training case is solved by a reproducible numerical optimizer. Solutions
are independently repropagated. Nonconvergence and infeasibility are retained
as outcomes rather than removed.

The dataset will contain low-fidelity and high-fidelity pairs where feasible,
enabling multi-fidelity residual learning.

### 11.3 Split policy

The final mission test set is locked before model development. Development
splits are grouped by mission epoch and uncertainty family so correlated
trajectory states cannot appear on both sides of a split.

The intended structure is:

- development pool with grouped cross-validation;
- calibration set for uncertainty calibration;
- untouched in-distribution mission test;
- untouched out-of-distribution stress test.

No result from either final test set may influence feature selection,
hyperparameters, stopping, or algorithm design.

## 12. Experiment 1: ML and QML benchmark

### 12.1 Classical references

- numerical trajectory optimizer;
- mission baseline or published schedule when reconstructable;
- ridge regression;
- Gaussian-process regression;
- gradient-boosted trees;
- parameter-matched multilayer perceptron;
- strong unrestricted multilayer perceptron or deep ensemble.

### 12.2 Quantum candidates

- quantum kernel ridge regression;
- variational quantum regressor with data re-uploading;
- hybrid classical encoder, parameterized quantum circuit, and classical head.

Quantum annealing and QAOA are optimization methods rather than QML models.
They may be reported in a separate exploratory appendix, but they cannot
replace the QML benchmark.

### 12.3 Qubit and noise conditions

Initial circuit sizes are 4, 6, and 8 qubits. Ten or twelve qubits are added
only if memory and execution budgets permit the same evaluation rigor.

Every finalist is evaluated under:

- exact or statevector simulation;
- finite shots at preregistered shot counts;
- a fixed, versioned noise model;
- optional real hardware as secondary external validation.

Hardware results are repeated across sessions when access permits. Hardware
drift is reported rather than averaged away without analysis.

### 12.4 Fairness controls

- identical development and test examples;
- identical outcome transformations;
- a fixed hyperparameter search space per family;
- at most 30 tuning trials per family unless Gate 2 changes the budget;
- capacity-matched classical comparisons;
- strong classical comparisons without artificial parameter restrictions;
- identical compressed inputs for matched models;
- raw-feature classical baselines where appropriate;
- at least 20 independent training seeds for all reported models;
- 30 seeds for finalists;
- training-set learning curves at 128, 256, 512, 1024, and full development
  size when supported by the available data.

### 12.5 Phase 1 outcomes

Primary:

- normalized RMSE for robust delta-v cost;
- feasibility-constrained optimization regret.

Secondary:

- MAE;
- burn-vector magnitude and angular error;
- terminal-margin error;
- feasibility precision, recall, AUROC, and calibration;
- constraint-violation rate after independent propagation;
- learning-curve sample efficiency;
- training and inference wall time;
- memory, parameter count, circuit depth, two-qubit gate count, shots, and
  quantum executions.

Quantum-simulator wall time is reported as simulation cost, not quantum
hardware speed.

## 13. Conditional algorithm-development gate

The proposed new model is a Multi-Fidelity Physics-Constrained Quantum Residual
Surrogate:

    y_high_hat(z) = y_low(z) + Q_theta(E_phi(z))

where y_low is a low-fidelity physics prediction, E_phi is a frozen or trained
classical encoder, and Q_theta is a small quantum residual model. The result is
paired with uncertainty estimation and a deterministic feasibility projection.

Development is authorized only when all of the following hold on development
data:

1. A QML candidate's 20-seed mean primary error is within 5 percent of the
   strongest classical candidate and the upper 95% paired-bootstrap bound of
   its seed-level relative gap is also no greater than 5 percent.
2. A residual regime registered before fitting is reproducibly complementary
   across all five grouped folds and remains favorable after Holm correction.
3. The regime is not explained by different preprocessing, PCA dimension,
   parameter count, tuning effort, A01 random features, or compressed C05, and
   all 20 QML seed runs remain eligible.

The new model must beat:

- its parent QML model;
- the low-fidelity physics model;
- a parameter-matched classical residual model;
- the strongest classical model.

Ablations remove the quantum layer, entanglement, data re-uploading, physics
baseline, uncertainty component, and safety projection. If the trigger fails,
no new algorithm is invented and the negative result is reported.

## 14. Experiment 2: mission simulation

### 14.1 Compared planners

- published or reconstructed mission baseline;
- full numerical optimizer;
- best classical surrogate;
- best QML surrogate;
- new model only if authorized by Gate 5.

### 14.2 Planning loop

At each navigation update:

1. create candidate correction plans;
2. estimate cost and feasibility;
3. refine the selected candidate with a deterministic optimizer if configured;
4. apply the safety filter;
5. execute the accepted plan in the independent simulator;
6. fall back to the validated classical method if confidence or feasibility
   requirements fail.

### 14.3 Scenario strata

A. Artemis II flight replay and held-out coast-arc validation.

B. Nominal Artemis IV-relevant Orion cislunar transfer.

C. Operational dispersions, including state error, thrust bias, timing error,
mass uncertainty, and navigation-mode variation.

D. Off-nominal events, including missed or delayed burn, communication delay,
sensor degradation, reduced reserve, and altered crew availability.

E. OOD environmental stress, including historical space-weather strata. A
space-weather proxy is not described as absorbed astronaut dose.

### 14.4 Human-rated constraints

- protected sleep and scheduled crew activities;
- routine versus emergency maneuver distinction;
- monitoring workload and crew availability;
- body-axis translational acceleration using the NASA-STD-3001 duration
  envelopes;
- mission duration and time outside protective environments;
- space-weather exposure proxy;
- reserve and abort trajectory feasibility.

Human constraints are sourced from NASA standards and public mission
timelines. Unavailable mission-specific thresholds are placed in the assumption
registry and tested by sensitivity analysis.

### 14.5 Monte Carlo plan

Algorithms receive paired scenarios generated with common random numbers.

Run at least 2,000 paired simulations per primary scenario stratum. Continue in
batches of 1,000 until the paired delta-v 95 percent confidence-interval
half-width is both below 0.05 m/s and below 1 percent of the strongest
classical mean, or until 20,000 paired simulations are reached.

Rare violations are reported with exact binomial bounds. Zero observed failures
does not establish flight safety.

### 14.6 Phase 2 outcomes

Hard gates:

- terminal mission constraints;
- entry or target-orbit corridor;
- propellant reserve;
- actuator and acceleration limits;
- protected crew-period compliance;
- computation deadline;
- deterministic fallback availability.

Primary mission outcome:

- paired robust correction delta-v regret among feasible missions.

Secondary:

- correction propellant sensitivity;
- remaining reserve;
- terminal state error;
- mission success probability;
- CVaR and worst observed correction delta-v;
- crew-schedule conflicts;
- body-axis acceleration-envelope margin;
- deadline misses;
- fallback activations;
- sensitivity to assumptions.

## 15. Model selection rule

Selection is lexicographic:

1. reject any model that fails a hard gate;
2. require safety and feasibility non-inferiority;
3. minimize paired mission correction delta-v regret;
4. minimize tail risk;
5. meet computation deadlines;
6. prefer robustness, calibration, and simpler operational integration.

There may be no overall winner. Pareto-equivalent models will be reported as
such. A model is not promoted because of one favorable metric.

## 16. Statistical analysis

- Use paired analysis because planners share identical scenarios.
- Report confidence intervals and effect sizes for every primary comparison.
- Use bootstrap intervals for paired continuous outcomes and exact intervals
  for violation probabilities.
- Use paired permutation or Wilcoxon tests when distributional assumptions do
  not hold.
- Correct confirmatory multiple comparisons using Holm's procedure.
- Separate confirmatory outcomes from exploratory analyses.
- Report seed-level results, not only the best run.
- Report practical and engineering significance alongside statistical
  significance.
- Preserve the untouched final test set until the analysis code is frozen.

## 17. Real-life interpretation boundary

The maximum justified initial claim is:

    The evaluated method improved or did not improve simulation-based,
    safety-filtered mission-planning performance within the public-data model
    and tested uncertainty domain.

The study cannot independently authorize flight use. Operational translation
would additionally require mission-owned propulsion and GN&C models,
authoritative uncertainty distributions, independent verification and
validation, software and hardware-in-the-loop tests, failure-mode analysis,
formal software assurance, human-factors review, and approval by the responsible
technical authorities.

## 18. Open-science requirements

- Public Git repository.
- Apache-2.0 code license.
- CITATION.cff and contributor guidance.
- Versioned source registry and checksum manifest.
- Download scripts instead of undocumented data copies.
- Environment lock and container definition before final experiments.
- Published computational methodology and reference hardware manifest in
  `docs/computational_methodology.md`.
- Fixed configuration files and seed lists.
- Automated unit, integration, and numerical regression tests.
- Machine-readable results and figure-generation scripts.
- A figure registry linking every material result, failed attempt, repair, and
  claim-bearing methodology change to source data, deterministic PNG/SVG
  generation, captions, checksums, and claim boundaries.
- Data cards, model cards, and simulation-credibility report.
- Tagged releases and an archival DOI at publication.
- Negative and failed experiments retained when scientifically relevant.

## 19. Decision gates

Gate 0, Governance: accepted on 2026-07-10.

Gate 1, Protocol Scope: accepted on 2026-07-10. The NASA-first design is
frozen.

Gate 2, Data and Numeric Freeze: accepted on 2026-07-11. The audited source
set, exact variables, uncertainty ranges, simulator tolerances,
practical-effect threshold, and compute budget are frozen.

Gate 3, Simulator Credibility: accepted by the human research lead on
2026-07-12. Technical validation completed after the logged
Deviation D001 repaired the fixed-column `POTFIELD` serialization supplied to
GMAT R2026a. The repair did not change force-model physics, Python dynamics,
validation windows, integrator settings, or acceptance thresholds. All 67
criteria that could be evaluated pass and no criterion fails.

RTC3 is the one required Gate 3 event check that was not evaluated. Its public
event time is 2026-04-10T18:53:00Z, while the frozen qualified CCSDS OEM was
created at 2026-04-10T03:22:19Z, 15 hours 30 minutes 41 seconds earlier.
Although that OEM contains later trajectory rows, those rows were predictions
made before RTC3, not historical or reconstructed evidence produced after the
event. The separate `2026.04.10 - Post-RTC3 to EI` product was also unavailable
for this check because its mission-relative epoch, M50 frame realization, and
eighth-column meaning were not authoritatively defined and the file was
quarantined under the frozen data rules.

Accordingly, `not_eligible` means **the RTC3 timing check was not performed with
eligible evidence**. It is neither a pass nor a failure. Gate 3 acceptance
explicitly accepts this missing source check as nonblocking; it does not claim
that RTC3 was validated.

All 10 independent GMAT endpoint checks pass. The largest position difference
is 0.046296 km against the 0.100 km limit, and the largest velocity difference
is 0.004266 m/s against the 0.010 m/s limit. The technical run recorded
`pending_external_validation` because the RTC3 check could not be performed,
not because a numeric criterion failed. The human decision accepted this
nonblocking source limitation and the disclosed pre-freeze F2 smoke
computation.

Gate 4 froze 65,000 candidate-plan identities in 13,000 five-plan decision
sets, whole-group splits, schema, seeds, tuning trials, nine candidate
families, one interpretation control, QML resources, and analysis code. Gate 4
and D002 were accepted on 2026-07-12 before any research scenario outcome or
model result was visible. Development generation and registered tuning are
authorized; both final-test splits still require a separate unlock commit.

The first post-acceptance generator produced 7,000 F0 rows that were later
found invalid for schema, uncertainty, epoch, targeting, and effective-input
conformance. Deviation D003 excludes those rows from all research use, retains
their audit and figures, and authorizes a committed repair followed by a
first-group audit before each fidelity scale-up. At D003 authorization, no
F1/F2 payload, valid research payload, fitted model, or benchmark result
existed. Corrected F0, F1, and F2 payloads now pass their required audits.
Registered development-only model fitting is authorized only after the D004
pre-fit literature-hardening controls are preserved in the runner and figures.

Gate 5, Algorithm Trigger: authorize or reject development of the proposed new
model based only on the preregistered trigger. Before the first research model
fit, D004 adds literature-derived diagnostic controls: source-grade discipline,
kernel concentration and bandwidth diagnostics, variational-trainability
failure reporting, random-feature dequantization controls, fixed regime
reporting, and a figure-backed claim boundary. D004 does not add any candidate
family, threshold, split, tuning budget, or final-test access.

Gate 6, Mission Experiment: approve Phase 2 scenario set and safety filter
before opening final mission results.

Gate 7, Claims and Release: approve paper claims, limitations, repository
release, and archival package.

## 20. Protocol deviations

Deviation D001, dated 2026-07-11, corrected the fixed-column formatting of the
GMAT Earth-J2 COF `POTFIELD` record after an incremental Earth-only diagnostic
campaign isolated the original cross-tool discrepancy. The failed comparison,
diagnostic chain, corrected file checksum, and passing rerun remain preserved
in repository history and `docs/decision_log.md`. D001 changed serialization
only; no scientific constant, threshold, split, window, exclusion, or force
term changed.

Deviation D002, accepted on 2026-07-12, allows the Gate 4 freeze to use
complete NTRS/arXiv retrieval plus 23 extracted primary or authoritative
records after OpenAlex metadata export was blocked by HTTP 429 responses. The
search is labeled a bounded scoping synthesis, not a complete systematic
review. No research outcome was visible at acceptance. A broader database
update remains mandatory before manuscript submission and cannot be used to
change a model after final-test access without a new deviation.

A same-day post-acceptance discovery refresh expanded the current ledger to
4,218 unique canonical keys. It leaves 926 full-text screens open and does not
change the accepted 23-record extraction matrix or any Gate 4 scientific
choice. RFIG-014 preserves the updated coverage and incomplete-screening
boundary.

Deviation D003, authorized on 2026-07-12 before any model fit or final-test
access, repairs the Gate 5 scenario generator after the invalid F0 run. The
repair is limited to frozen-config conformance, source-derived epochs,
deterministic Sobol sampling, numerical targeting, effective timing/execution
inputs, lunar-flyby exclusion, explicit crew-axis mapping, complete metadata,
schema and checksum validation, and append-only provenance. Pre-D003 outputs
are audit-only. Because their diagnostic outcomes
were visible, no repair choice may be tuned to produce a preferred feasibility
rate, and pre/post repair figures are mandatory.

The corrected F0 campaign contains 7,000 rows in 14 unlocked groups. All
rows pass schema, relationship, finite-value, checksum, and frozen uncertainty
audits, with no nonconvergence. Of 1,400 decision sets, 319 have no feasible
reference; they remain included under the preregistered penalty/reporting rule
and cannot motivate post-result candidate retuning.

The serial F1 G01 checkpoint added 2,500 valid U0 rows with no nonconvergence
or no-reference decision set. Its 1,268.159-second wall time authorized
controlled four-process F1 group execution with locked ledger appends. The
completed F1 campaign contains 35,000 valid rows in 14 unlocked groups, with
6,436 feasible candidates and 4,215 of 7,000 decision sets lacking a feasible
numerical reference. The latter are retained as a development limitation and
cannot motivate post-result candidate or uncertainty retuning. Total F1 group
work was 64,907.601 seconds; the separate 13-group scale-up required
18,148.400 seconds of wall time at effective concurrency 3.51. No final-test
payload was generated or read. F2 required its own full-fidelity audit before
model fitting and later completed that audit.

The serial F2 G01 checkpoint contains 250 valid nominal-U0 rows with no
nonconvergence or no-reference decision set. It required 450.835 seconds,
3.555 times the F1 G01 per-row cost, and authorized at most two process workers
for scale-up. The completed F2 campaign contains 3,500 valid rows in 14
unlocked groups, with 642 feasible candidates and 423 of 700 decision sets
lacking a feasible numerical reference. The latter remain included under the
frozen penalty/reporting rule. Total F2 group work was 16,054.965 seconds;
the separate two-worker scale-up required 7,978.900 seconds of wall time at
effective concurrency 1.956. All 45,500 unlocked F0/F1/F2 rows now pass their
full audits, so registered development-only model fitting may begin. The
calibration split remains prohibited for fitting or selection, and final-test
payloads remain absent and locked.

Deviation D004, authorized on 2026-07-12 before any research model fit,
hardens Gate 5 using an additional local literature review and primary-source
checks. The revision adds source-vetting rules, quantum-kernel concentration
and bandwidth diagnostics, variational-trainability failure reporting,
random-feature and compressed-classical dequantization controls, fixed regime
reports, and RFIG-019. It does not add a model family, threshold, split,
tuning budget, scenario outcome, or final-test access. Scenario feasibility and
no-reference rates were visible, so the D004 controls are restricted to
diagnosis, reporting, interpretation, and claim discipline. They cannot be used
to redesign candidate plans, retune uncertainty distributions, change ranking
thresholds, or promote QRL, dynamic circuits, quantum annealing, or QAOA into
the Phase 1 candidate set.

Deviation D005 was opened on 2026-07-12 before any research model fit to close
four execution ambiguities left by the Gate 4 freeze: exact group-to-fold
assignment, nested row hashing, fold-local learned transforms, and matched
control/residual handling. The proposed runner balances frozen uncertainty and
trajectory-family design strata with SHA-256 tie breaks and no outcomes, then
fits every imputer/scaler/PCA and target standardizer inside each
training fold, scores pooled out-of-fold error while retaining fold summaries,
and gives C06/Q03 an explicit low-fidelity baseline in target-standardized
units. Q03 removes that appended baseline from circuit encoding before adding
the predicted residual. A01 and compressed C05 use the same row IDs, fold,
rung, PCA dimension, and seed index as their QML view. QML halving retains at
least one eligible trial per required qubit count at each rung. The human
research lead accepted D005 on 2026-07-12 after publication of the candidate
at commit `80ae35d`. No calibration or final-test row was read while preparing,
auditing, or accepting this candidate.

Deviation D006 was opened before the first research fit after a final
execution audit found that D005's independently cycled control dimensions did
not match every QML trial at the same seed index. D006 repeats each of the 30
frozen A01 and compressed-C05 hyperparameter trials at all 4/6/8 dimensions,
giving 180 non-winning control views and 450 first-stage tasks. Controls
advance independently within dimension and exact same-index views also follow
QML survivors. It adds no hyperparameter trial, candidate family, fold, row,
seed, threshold, or final-test access.

D006 was explicitly accepted by the human research lead on 2026-07-12 from
candidate commit `3ac9403`. It freezes immutable rung/selection authorizations, exact 20-seed
selected-configuration reruns, terminal-failure preservation, task locks, and
a mathematically equivalent vectorized statevector batch. Recorded
state/feature/kernel differences are at most `2.67e-15`; circuits, objectives,
optimizers, and seeds are unchanged. Before scale-up, frozen C04-T02 runs at
its full-data subset and Q01-T04/Q02-T07/Q03-T14 plus their matched controls
run at the 1,024-row rung; a 25%-margin projection must remain inside every
Gate 2 ceiling. Checkpoint scores remain outside ranking unless the identical
task later advances under the frozen halving rule, and the projection uses
end-to-end task time. Source-bound, failure-free evidence is required for a
technical trigger pass. D004 claim-boundary diagnostics are mandatory
report-only checks pending human interpretation, so a technical pass does not
itself authorize algorithm development. The maximum formal task count remains
1,275; resource projections conservatively add all ten qualification tasks
without overlap credit, for at most 1,285 executions inside those ceilings.
Invalid or incomplete evidence yields `UNAVAILABLE` and repair, not a negative
scientific result.

The D006 campaign completed on 2026-07-13 from source commit `6e5a620`: 671
tuning tasks and 200 exact seed reruns completed with zero task failures and
zero calibration/final-test reads. Q01 advanced through all four rungs. Q02
and Q03 stopped at rung 128 because only 8/30 and 4/30 tasks were eligible,
below the frozen retain count of 15. The first report is preserved as an
`UNAVAILABLE` historical artifact because the original reporting contract
incorrectly described those registered early stops as terminal failures and
required diagnostics from later stages that were never authorized.

Deviation D007 was opened after outcomes became visible and accepted by the
human research lead on 2026-07-13 from candidate commit
`7a726c8917a85f24313208eb18c33e1ccb5f703e`. It authorizes a reporting-only,
fail-closed recognition of the exact source-bound
terminal-nonadvancement case. Every task, fold, digest, eligibility value, and
ranking must remain unchanged; later rungs or seed results are explicitly not
imputed. Under D007, Q02/Q03 trainability is reported from their 150
completed tuning folds per family, Q01 retains its four-rung/20-seed evidence,
and the unchanged trigger is evaluated only over eligible finalists. This
acceptance authorizes only report and figure regeneration, which both entry
points verify before writing. Regenerated evidence must keep the D006
campaign source distinct from the accepted D007 candidate, clean reporting
commit, and reporter/generator hashes. The accepted Git snapshot byte-anchors
both the reporting implementation and every immutable D006 campaign evidence
file; a complete derived-package digest manifest is written last and verified
before figures. Reporting from clean source commit
`7b7db694cd7911a2643950c4c57f993046271a95` validated the unchanged evidence
and produced an official technical trigger `FAIL`: Q01 mean NRMSE
`0.6466136067` versus C06 `0.0087390408`, relative gap `72.9913708168`, and
zero qualifying regimes. RFIG-021 through RFIG-023 preserve the reached-rung,
20-seed, and regime-trigger evidence. This is not a claim that QML can never
work; it is a negative result for this preregistered development benchmark.
The human research lead accepted this unchanged technical `FAIL` as the
official Gate 5 result on 2026-07-13. This closes Gate 5 and rejects development
of the proposed new model under the frozen trigger. Acceptance does not
authorize refitting, reranking, new algorithm work, calibration or final-test
access, or Gate 6. Any later experiment requires a new, prospectively approved
protocol decision; the accepted result cannot be reinterpreted as a universal
claim that QML cannot work.

Post-Gate-5 exploratory protocol P001 was opened by the human research lead on
2026-07-13. It creates a narrow prospective branch, not a rescue analysis.
Only two near-term QML tests may be designed under that branch:

- `Q01b`, a projected quantum-kernel supervised surrogate using the original
  grouped-development pipeline, matched controls, and robust-cost/regret
  endpoints.
- `FQK`, a feasibility-only quantum-kernel classifier for
  `independently_propagated_feasible`, using development-fold feasibility and
  safety-filter diagnostics rather than cost-regression claims.

Quantum reinforcement learning, dynamic circuits, quantum annealing, QAOA, new
variational QML architectures, larger-qubit circuits, and hardware execution
are appendix or future-work topics only unless a later prospective protocol
opens them. P001 does not authorize any fit, refit, calibration read, final-test
read, Gate 6 run, or reinterpretation of Gate 5. The protocol document is
`docs/post_gate5_exploratory_protocol.md`; RFIG-024 records its paper-ready
decision boundary.

D008 is the accepted implementation freeze for P001. It fixes the
projected one-qubit-density-matrix feature map, 30 balanced paired projection
configurations, Q01b and FQK endpoint orderings, exact classical and frozen
model controls, successive-halving rungs, 20 selected-configuration seeds,
local compute ceilings, and RFIG-025 through RFIG-029 reporting obligations.
It also requires every failure or stopped step to commit an evidence-based
future-research improvement while marking that improvement as prohibited from
changing or retrying the active pipeline. The accepted D008 scope authorizes
implementation and synthetic validation only; a separate execution decision is
still required before fitting development rows.

D008 implementation and synthetic validation are now complete. The implemented
code covers Pauli X/Y/Z one-RDM projection, projected-kernel distances and
bandwidths, deterministic SHA-256 Nystrom landmark selection, projected-kernel
regression and feasibility classification, PSD clipping diagnostics, and
Post-Gate-5 scope guards. Validation used synthetic arrays only and did not
read development payloads for fitting, calibration rows, final-test rows,
hardware devices, or Gate 6 scenarios.

D009 is accepted for one clean-source synthetic compute preflight. The frozen
benchmark uses 1,024 synthetic training rows, 256 synthetic validation rows,
eight qubits, two layers, shared Q01b/FQK projected features, and every D008
matched control. It projects 477.5 conservative equivalent work units with a
25% margin against 250 CPU-core-hours, five wall-clock days, 20 GiB new
artifacts, a 24 GiB process working set, and a 20 GiB post-projection free-disk
floor. A PASS permits preparation of D010 only; it does not authorize any
development-row fit. A STOP invokes the frozen future-research firewall and
cannot be rescued by reducing the active design.

The single D009 attempt ended in `STOP` after the first shared synthetic
training projection. The Windows peak-working-set probe raised `OSError`
before validation projection, either projected head, any matched control, or
the admission calculation completed. All research-row read counters remained
zero. The outcome is a telemetry-interface failure: it provides no QML result
and no evidence that the workload fits or exceeds the laptop. P001 execution
remains locked. P001-FR001 records a future-only telemetry-adapter validation;
it does not authorize a correction or retry. RFIG-029 records this boundary,
while RFIG-030 remains absent because no resource-margin result exists.

D010 is accepted prospectively to correct only that telemetry interface and
to run one unchanged synthetic preflight as attempt 2. The correction declares
the Windows `GetProcessMemoryInfo` and `GlobalMemoryStatusEx` argument and
return types explicitly, validates the adapter against PowerShell
`WorkingSet64` within the larger of 64 MiB or 25%, and hashes committed Git
blobs so checkout line endings cannot alter provenance. The D009 benchmark,
477.5-work-unit projection, 25% margin, controls, seed, rows, circuits, and all
resource ceilings remain unchanged. The required order is a telemetry-only
check followed by at most one full synthetic rerun. D009 evidence remains
immutable. A D010 PASS may support preparation of D011 only; no development,
calibration, final-test, hardware/GPU, Gate 5 reinterpretation, or Gate 6 work
is authorized.

The D010 telemetry-only check passed: the typed adapter reported 127,705,088
bytes and PowerShell reported 127,754,240 bytes, a 49,152-byte difference
against the frozen 67,108,864-byte allowance. The single unchanged attempt 2
then completed both projected heads and every matched control. All five
admission checks passed: 1.7849 of 250 CPU-core-hours, 0.0758 of five
wall-days, 1.1658 of 20 GiB new artifacts, 0.2014 of 24 GiB peak process
memory, and 53.7426 GiB free disk after artifacts against a 20 GiB minimum.
The run used 1,280 synthetic rows and read zero development, calibration, or
final-test rows; it submitted no hardware/GPU or Gate 6 job. RFIG-030 records
the margins. D010 is now closed to rerun. This PASS establishes laptop compute
admission only and permits preparation of D011; it is not QML performance,
Gate 5 reinterpretation, or research-data execution authority.

D011 is accepted prospectively by the human research lead. The pre-execution
runner audit identified an accounting-shape gap rather than a change to D010:
D010 validly benchmarked its frozen 256-row validation bundle, while D011 must
predict 6,500 or 9,750 held-out rows per grouped fold and 39,000 rows per
complete five-fold task. D011 therefore requires a new largest-fold synthetic
preflight with 1,024 training rows, 9,750 validation rows, q=8, two layers,
both projected heads, A02, and every matched control. The projection charges
1,220 worst-fold bundles with a 25% margin and takes no credit for smaller
folds, smaller qubit maps, shared controls, shared projections, or cached
states. The D008 ceilings remain unchanged.

Only a source-bound `PASS` on every D011 preflight check authorizes the first
development payload read. A `STOP` is terminal under this decision and must be
committed with a future-only improvement. After a PASS, exactly one resumable
development-only P001 campaign may run. Q01b and FQK advance independently
through the frozen 128/256/512/1,024-row rungs, one selected configuration per
reached track runs seeds 1-20, and 1,024-shot, 4,096-shot, and fixed Gate 4
noise conditions remain report-only sensitivities. The fixed Q01b regime
analysis uses fidelity, uncertainty family, base-trajectory family,
boundary/tail status, and reference-feasibility status; a cell must cover all
five folds and all 20 seeds, and its paired-bootstrap upper bound must be below
zero versus A01, A02, and compressed C05. No sensitivity may rerank or rescue a
track.

D011 checkpoints and compact reports bind the clean source commit and preserve
zero calibration/final-test reads. Governed undefined folds are recorded as
ineligible; technical integrity failures stop the campaign and cannot be
silently retried. RFIG-031 was reserved for reached corrected resource
admission, RFIG-026 through RFIG-028 for reached development evidence, and
RFIG-029 remains the cumulative failure/future-research firewall. D011 cannot revise Gate 5,
authorize hardware/GPU work, make a quantum-advantage claim, or open Gate 6.

The first formal D011 command stopped before governed execution. Direct-file
Python execution could not resolve the repository `scripts` namespace while
importing `scripts.run_post_gate5_compute_preflight`, raising
`ModuleNotFoundError` before `verify_d011_authority` ran. Consequently, source
hash verification, synthetic array creation, corrected fold-shape admission,
and the development campaign were not reached. Development, calibration, and
final-test reads are all zero; no hardware/GPU or Gate 6 job ran.

This is a terminal pre-launch technical `STOP`, not resource-admission or QML
evidence. P001-FR002 proposes a package-safe invocation/import plus a
clean-source import-only smoke test for a later prospective decision, while
freezing all D011 scientific rows, methods, folds, controls, thresholds,
seeds, and ceilings. It does not authorize a correction or retry. RFIG-029 is
updated cumulatively; RFIG-031 and RFIG-026 through RFIG-028 remain absent
because their evidence was not reached. A new prospective human decision is
required before any corrected preflight attempt.

D011-C1 was accepted prospectively by the human research lead on 2026-07-14.
It corrected only the launcher/import path by moving shared synthetic-preflight
helpers into an importable `openqfuel` module and requiring an import-only
smoke test before one unchanged corrected fold-shape preflight attempt. The
smoke test passed, but the formal preflight stopped during D011-C1 authority
verification because the pinned raw Git-blob hash for
`configs/post_gate5_development_execution.yaml` did not match the actual raw
Git blob. The original D011 STOP file remains immutable; D011-C1 writes
separate STOP evidence at
`data/processed/reporting/post_gate5_d011_c1_fold_shape_preflight.json`.
Synthetic arrays, resource admission, development rows, calibration rows,
final-test rows, hardware/GPU work, and Gate 6 were not reached. P001-FR003
records a future-only recommendation to validate raw dependency hashes before
any successor correction. D011-C1 is terminal and cannot be retried without a
new prospective human decision.

D011-C2 was accepted prospectively on 2026-07-14 after reviewing the D011-C1
hash mismatch, docs, and evidence. It corrects only the dependency hashes by
using independently verified raw Git-blob SHA-256 values, requires a
hash-consistency smoke test plus the package import smoke test, and permits one
unchanged corrected fold-shape preflight attempt. D011-C2 writes separate
evidence at
`data/processed/reporting/post_gate5_d011_c2_fold_shape_preflight.json`.
D011 and D011-C1 STOP evidence remain immutable. D011-C2 does not authorize any
development payload, calibration/final-test access, hardware/GPU work, Gate 5
reinterpretation, or Gate 6 work.

The D011-C2 hash-consistency smoke test and import smoke test passed from clean
source commit `06381d1`. The one unchanged corrected fold-shape synthetic
preflight also passed every unchanged laptop boundary: 4.7259 CPU-core-hours of
250, 0.2002 wall-days of five, 2.9785 GiB artifacts of 20, 0.6339 GiB peak
working set of 24, and 45.3606 GiB projected free disk against the 20 GiB
minimum. Development, calibration, and final-test reads remained zero; hardware,
GPU, and Gate 6 runs remained zero. RFIG-031 records this corrected admission.
The PASS is synthetic compute-admission evidence only and requires a human
decision before the D011 development campaign can resume.

D011-R1 was accepted by the human research lead on 2026-07-14 to resume exactly
one source-bound D011 development-only campaign after the D011-C2 PASS. It
opens development rows only under the frozen D011 Q01b/FQK campaign contract.
Calibration, final-test, hardware/GPU, Gate 5 reinterpretation, and Gate 6
remain locked. Any technical failure, governed stop, terminal nonadvancement,
or scientific negative must be recorded with future-only discussion and the
required paper figures.

The D011-R1 campaign completed from source commit `083d777` under that frozen
contract. It read 39,000 development rows and zero calibration/final-test rows;
hardware/GPU and Gate 6 runs remained zero. Q01b and FQK both completed all
five folds and 20 selected seeds but did not meet their promising rules. Q01b
had mean pooled OOF NRMSE 0.6612 versus C06 at 0.0068328, a 95.769x relative
gap, and zero qualifying dequantization regimes. FQK had mean AUROC 0.7436,
Brier 0.1561, and recall at 0.5 of 0.1089 versus strongest comparator C02-T02
at 0.9134, 0.1062, and 0.3233. These are valid development-only exploratory
negative results; they do not revise Gate 5 and do not authorize Gate 6.

D012 was opened by the human research lead on 2026-07-14 as a discussion-only
future-protocol interpretation of those negative results. D012 records three
candidate future directions: task-informed local-observable projected kernels,
class-sensitive feasibility quantum kernels, and classical-first residual plus
safety-filter hardening. None is authorized for implementation or execution.
Any successor requires a separate prospective D013 decision, and Gate 6 remains
unauthorized.

D013-C was then accepted as the assistant-recommended planning path. It chooses
classical-first residual and safety-filter hardening before inventing a new QML
method, because D011-R1 showed both tested QML tracks were weaker than strong
classical controls. D013-C creates `docs/qml_invention_readiness_ledger.md` so
each result labels the useful signal for later QML invention and the prohibited
post-outcome use. D013-C authorizes no implementation, experiment, refit,
rerank, calibration/final-test access, hardware/GPU execution, Gate 5
reinterpretation, quantum-advantage claim, or Gate 6.

D014-C was accepted as the next assistant-selected freeze proposal. It locks
the classical-first residual-cost track (`CRES`) and safety-filter track
(`CSAFE`), their required controls, metrics, compute-admission requirement, and
planned figures RFIG-032 through RFIG-035. D014-C is not execution authority:
implementation, synthetic validation, development-data fitting,
calibration/final-test access, hardware/GPU execution, Gate 5 reinterpretation,
QML invention claims, and Gate 6 remain unauthorized. D015 is required before
any implementation or synthetic validation, and a later clean-source compute
admission is required before any development-data fitting.

After Gate 2, every change affecting data, outcomes, models, comparison budget,
thresholds, or exclusions requires a dated deviation entry containing:

- original rule;
- revised rule;
- reason;
- whether results were visible;
- likely bias;
- approving decision.
