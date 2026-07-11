# OpenQFuel-Cislunar Research Protocol

Version: 0.3.0
Status: Gates 1, 2, 3, and 4 accepted; Gate 5 development-scenario generation and tuning in progress
Prepared: 2026-07-10  
Updated: 2026-07-12
Recommended next decision: Accept Gate 5 trigger after reviewing the development-split analysis report

## 1. Proposed title

Can Quantum Machine Learning Improve Propellant-Efficient Human-Rated Cislunar
Guidance? An Open, Flight-Ephemeris-Calibrated Benchmark

## 2. Purpose

This study will determine whether a quantum machine-learning surrogate can
improve robust trajectory-correction planning for a crewed cislunar spacecraft
when compared fairly with strong classical machine-learning and numerical
optimization methods.

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

1. A QML candidate is within 5 percent of the best classical primary error, or
   is statistically non-inferior under the Gate 2 margin.
2. It shows a preregistered advantage in limited-data, noise, or OOD testing,
   or its residual errors are demonstrably complementary.
3. The opportunity is not explained solely by different preprocessing,
   parameter count, or tuning effort.

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

The Gate 4 candidate now freezes 65,000 manifest-only candidate-plan identities
in 13,000 five-plan decision sets, whole-group splits, schema, seeds, tuning
trials, nine candidate families, one interpretation control, QML resources,
and analysis code. No feature payload, label, fitted research model, or
benchmark outcome has been generated. Gate 4 remains pending the human
research lead's accept, reject, or revise decision. Both final-test splits also
require a separate post-approval unlock commit.

Gate 4, Phase 1 Freeze: pending human approval. The recommendation is to accept
the benchmark with proposed Deviation D002, which records the bounded
literature-search coverage and requires the full systematic update before
manuscript submission. Acceptance authorizes development generation and
tuning, not immediate final-test access.

Gate 5, Algorithm Trigger: authorize or reject development of the proposed new
model based only on the preregistered trigger.

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

Proposed Deviation D002, dated 2026-07-12, would allow the Gate 4 freeze to use
complete NTRS/arXiv retrieval plus 23 extracted primary or authoritative
records after OpenAlex metadata export was blocked by HTTP 429 responses. The
search is labeled a bounded scoping synthesis, not a complete systematic
review. No research outcome was visible. If accepted, a broader database
update remains mandatory before manuscript submission and cannot be used to
change a model after final-test access without a new deviation.

After Gate 2, every change affecting data, outcomes, models, comparison budget,
thresholds, or exclusions requires a dated deviation entry containing:

- original rule;
- revised rule;
- reason;
- whether results were visible;
- likely bias;
- approving decision.
