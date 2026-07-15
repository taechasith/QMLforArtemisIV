# A Governed Public-Data Benchmark of Quantum Machine Learning for Human-Rated Cislunar Trajectory-Correction Planning

Status: Final experimental manuscript package draft; scientific evidence is
closed. Author metadata, target-journal formatting, and independent review
remain before submission.

Release basis: `v0.3.0`, published under the strict D031-C negative-claim
boundary. This manuscript does not authorize Gate 6, calibration or final-test
access, new model fitting, or a new QML method.

<!-- Status: D031-C claim-reviewed draft -->
<!-- Status: D027-C manuscript Results/Discussion draft; not release-ready -->
<!-- Status: D026-C manuscript synthesis ready -->

## Abstract

Quantum machine learning (QML) is often proposed as a route to faster or more
efficient aerospace decision support, but application claims require controls
that are at least as strong as the proposed quantum model. We report a
governed, public-data, development-only benchmark for QML-assisted cislunar
trajectory-correction planning under crew and feasibility constraints. The
pipeline froze grouped data splits, fold-local preprocessing, matched
classical controls, seed accounting, eligibility rules, and a preregistered
algorithm trigger before research-data fitting. The simulator passed 67
evaluable credibility checks with no failed check; one required source event,
RTC3, remained outside the claim because eligible trajectory evidence was not
available under the frozen rule. In the preregistered Gate 5 benchmark, the
Q01 quantum-kernel candidate reached mean NRMSE 0.6466, compared with 0.008739
for the strongest physics-residual control C06, and no regime qualified for a
QML advance. Two prospective post-Gate-5 exploratory tracks were also
negative: Q01b reached mean NRMSE 0.6612 versus 0.006833 for C06, while the
feasibility-only quantum kernel reached AUROC 0.7436, Brier score 0.1561, and
recall 0.1089. A recall-first classical safety analysis produced a future
protocol signal but not an advancing model result. Sixteen subsequent
development-only successor protocols (D034-D049) also produced no candidate
that satisfied the strict matched-control rule. These findings support a
benchmark-specific negative conclusion: the tested QML candidates did not
outperform strong classical controls and no candidate qualified for a QML
Gate 6 mission experiment from P001. They do not establish that all QML
methods fail, quantum advantage is impossible, or the simulator is flight
ready.

Keywords: quantum machine learning; cislunar guidance; trajectory correction;
human-rated spaceflight; quantum kernels; reproducible benchmarking; negative
results; uncertainty-aware simulation

## 1. Introduction

Cislunar trajectory-correction planning combines constrained dynamics,
uncertain navigation and actuation, feasibility screening, correction cost,
and human-system requirements. In this setting, a predictive model cannot be
assessed only by an aggregate regression score. A useful model must preserve
the grouping structure of the mission design, remain valid under the relevant
uncertainty strata, compare fairly with physics-derived and classical machine
learning controls, and avoid unsafe promotion when the numerical reference is
infeasible or the model is poorly calibrated.

Quantum machine learning is a plausible research direction for structured
surrogates and feasibility classification, but the existence of a quantum
feature map does not establish application benefit. Classical approximations,
data encoding, kernel geometry, sample size, optimizer behavior, and control
quality can dominate the comparison. This is especially important for
statevector experiments, where computational simulation is not evidence of
hardware speedup or quantum advantage.

This work asks four bounded questions:

1. Can the preregistered Q01 quantum-kernel surrogate outperform strong
   classical and physics-residual controls under frozen development rules?
2. If Q01 fails, does a projected quantum-kernel representation improve the
   same cost-prediction task without changing the pipeline?
3. Can a feasibility-only quantum kernel provide a useful safety-filter signal
   under fixed threshold and recall requirements?
4. What conclusions remain justified when calibration, final-test, hardware,
   and mission-loop evidence are not available?

The contributions are methodological as well as empirical. First, we provide
an open, source-bound benchmark with explicit governance, simulator checks,
grouped splits, fold-local preprocessing, matched dequantization controls,
and retained failure records. Second, we report a complete negative QML
benchmark rather than selecting only favorable regimes. Third, we separate
valid development evidence from exploratory follow-up, future protocol
lessons, and locked mission evidence. The paper's conclusion is therefore
deliberately narrower than a claim that QML is universally ineffective.

## 2. Related Work and Positioning

The benchmark is motivated by public Artemis trajectory-correction design
research, which treats correction-burn placement, uncertainty, crew timeline,
and robust delta-v as coupled mission-design concerns [1]. Cislunar and
low-thrust learning studies provide useful classical precedents, but their
missions, dynamics, objectives, and validation splits are not interchangeable
with a human-rated cislunar correction benchmark [4].

Quantum feature-space methods frame a quantum circuit as an encoding or kernel
construction for supervised learning [5,6]. Quantum-kernel regression and
projected-kernel studies show that performance depends on the data geometry,
encoding, kernel bandwidth, and the availability of strong classical
approximations [7,8,9]. Broad QML benchmarking has also shown that classical
models frequently match or exceed QML models on ordinary supervised tasks,
making unrestricted classical baselines and negative-result reporting
essential [10]. These results motivate the present use of exact matched
classical controls, random-feature comparisons, compressed-input controls,
and a physics-residual baseline.

The work also follows model-and-simulation credibility principles from NASA's
modeling and simulation standard [2] and keeps human-system constraints
separate from predictive performance [3]. The benchmark is not a replacement
for mission-owned data, certification, or operational validation. It is a
public, development-only test of whether the registered QML candidates earned
further authority.

The paper uses a bounded evidence review rather than claiming an exhaustive
systematic review. The repository contains 23 accepted extracted literature
records; a post-acceptance discovery refresh remains archival, was not used to
change the experiment, and does not alter the reported outcomes.

## 3. Materials and Methods

### 3.1 Governance and evidence boundaries

The experiment was organized as prospective decisions D001-D033. Gates 1-5
were accepted, with Gate 5 closed as a technical `FAIL`. D006 completed 871 of
871 authorized campaign tasks with zero task failures and zero calibration or
final-test reads. Q02 and Q03 stopped because they did not satisfy the frozen
eligibility rule for later stages; they are reported as
`not_reached_under_frozen_eligibility`, not as failed experiments.

The current paper reports only public-data development evidence. Calibration
and final-test rows, mission-loop scenarios, hardware or GPU quantum runs,
threshold application to real data, model release, and Gate 6 remain locked.
Any result from the local simulator is a classical simulation result and is
not evidence of quantum advantage.

The D034-D049 successor branch is included as a closed development-only
negative synthesis. It did not revise Gate 5, add a new selection rule, or
open any locked evidence pathway.

### 3.2 Simulator and scenario construction

The pipeline generated trajectory-correction scenarios across the frozen F0,
F1, and F2 fidelity levels. The simulator included mass depletion, event
handling, crew-related constraints, uncertainty variables, and numerical
feasibility checks. Gate 3 compared eligible Python results with GMAT
endpoints and accepted 67 evaluable checks with zero failures. Ten repaired
GMAT endpoints passed unchanged position and velocity limits.

RTC3 is not included in the simulator validation claim. The qualified public
trajectory source predates the RTC3 event under the frozen evidence rule, and
no later source was substituted. This is a source-eligibility limitation, not
a hidden validation pass or failure.

### 3.3 Frozen data, splits, and preprocessing

The Gate 4 freeze committed manifest identities, feature definitions, grouped
development folds, target definitions, controls, tuning budgets, seeds, and
analysis rules before research outcomes. Records from the same mission-design
group were kept in the same validation fold. Imputation, categorical encoding,
feature scaling, target scaling, and PCA were fitted inside each training fold.

The development campaign used nested hash-selected sample rungs of 128, 256,
512, and 1,024 rows, followed by 20 registered seed indices for selected
configurations. The primary regression summary used pooled out-of-fold error;
unweighted fold summaries and seed-level diagnostics were retained. The
preregistered trigger required complete eligible folds and seeds, comparison
against the strongest classical finalist and matched dequantization controls,
paired uncertainty checks, and no qualifying regime defined after seeing the
outcome.

### 3.4 Models and controls

Q01 was the preregistered fidelity-style quantum-kernel candidate for robust
correction-cost prediction. Its comparison set included the C06
physics-residual control, the A01 random-Fourier feature control, compressed
classical views, and other registered classical families. C06 was the key
physics-derived comparator because it expresses a low-fidelity physical
residual rather than only a generic statistical baseline.

P001 opened two prospective exploratory tracks after Gate 5. Q01b replaced the
Q01 overlap readout with one-qubit reduced-density-matrix projections and a
median-distance projected kernel. FQK used a quantum kernel only for the
`independently_propagated_feasible` classification task. Both retained the
same grouped development discipline, fold-local preprocessing, nested rungs,
matched controls, and 20 selected seed indices. They could not revise Gate 5.

The later D034-D049 branch tested sixteen prospectively bounded successor
variants. Each used the same development-only scope and the accepted C06
comparison, while the branch-specific protocol froze its candidate, matched
classical control, threshold, and stopping rule before fitting. The complete
summary is in `paper/results_tables/post_gate5_invention_branch_summary.csv`.

The recall-first CSAFE-RF analysis is reported as a future protocol lesson.
It was not used to rescue a prior QML result, change a threshold, or authorize
mission use.

### 3.5 Metrics and statistical interpretation

The cost-prediction endpoint was pooled out-of-fold NRMSE, with robust
correction cost and feasibility-constrained regret retained as interpretation
metrics. The feasibility endpoint used Brier score, AUROC, recall, precision,
false-negative rate, and calibration diagnostics at the frozen 0.5 threshold.

The preregistered trigger included paired bootstrap uncertainty, fold-level
sign checks, and a sign-permutation test with multiplicity control. All
reported intervals and diagnostics are taken from the committed evidence
files. No post-outcome statistic, threshold, split, seed, or model family was
added to improve a result.

### 3.6 Computational environment and reproducibility

Compute admission was designed for the reference Windows laptop: a 13th Gen
Intel Core i9-13900HX with 32 GB RAM and an NVIDIA GeForce RTX 4060 Laptop
GPU. The project used a bounded RAM budget and serialized expensive statevector
work; GPU and hardware quantum execution were not authorized. The local
hardware specification is a reproducibility limitation and a scheduling
record, not a requirement that future researchers use identical equipment.

The accepted source package is released as `v0.3.0`. The repository's clean
source audit passed pytest, Ruff, and compilation checks. The release includes
machine-readable reporting outputs, figure registry entries, source-bound
scripts, data cards, and the complete decision log.

## 4. Results

### 4.1 Simulator credibility

All 67 eligible Gate 3 checks passed, including the repaired GMAT endpoint
comparisons. RTC3 remained outside the claim because its qualified source was
not temporally eligible. The simulator result therefore supports benchmark
credibility within the accepted public-data scope, not flight readiness or
mission-owned validation.

### 4.2 Preregistered Gate 5 benchmark

Q01 reached mean NRMSE 0.646614, while C06 reached 0.008739. No preregistered
residual regime qualified for a QML advance. Gate 5 is therefore a valid
technical `FAIL` for this frozen benchmark. The result does not imply that
every QML representation or every cislunar task will fail.

Q02 and Q03 completed all authorized tasks and were stopped before later
rungs and seed reruns under the frozen retention rule. Their later-stage
absence is an eligibility outcome, not a task failure or missing-data claim.

### 4.3 Exploratory Q01b and FQK results

Q01b reached mean NRMSE 0.661207 compared with 0.006833 for C06, a 95.77-fold
relative gap. No projected-kernel regime qualified for a new-protocol signal.
FQK reached AUROC 0.7436, Brier score 0.1561, and recall 0.1089; its recall
was inadequate for the frozen safety-filter interpretation and its controls
were stronger. These are valid exploratory negatives for the exact P001
feature map and benchmark, not universal QML impossibility results.

### 4.4 Successor QML branch D034-D049

All sixteen D034-D049 campaigns completed as valid development-only negatives.
The strongest raw C06 comparison was ORFRK-08-R2 (D046), with mean NRMSE
0.0064363 versus 0.0068328 for C06, an apparent 5.80% improvement. Its
matched TWO-RBF control reached 0.0067501, leaving only about 4.65% improvement
over the matched classical alternative, below the preregistered 5% rule.
Therefore the apparent gain did not establish a quantum-specific advantage.
The full paired intervals, source evidence paths, and all sixteen outcomes are
provided in the supplementary result table.

### 4.5 Future safety-objective signal

The recall-first CSAFE-RF audit selected `calibrated_logistic` with mean recall
0.804253, false-negative rate 0.195747, and Brier score 0.142231. This is a
future protocol-design signal: a safety filter should prospectively prioritize
missed unsafe cases while retaining calibration constraints. It is not an
advancing QML result, not a mission filter, and not a post-outcome rescue of
D017 or Gate 5.

### 4.6 Evidence accounting

The D006 campaign completed 871 of 871 authorized tasks with zero failures.
The D011-R1 exploratory campaign read 39,000 development rows and zero
calibration or final-test rows. No hardware quantum job, mission-loop run,
Gate 6 run, or locked-data read occurred. The evidence accounting is part of
the result because it determines which claims the benchmark can support.

## 5. Discussion

The main result is a controlled negative benchmark. Q01 did not approach the
physics-residual control, and Q01b did not recover the gap after changing the
quantum readout while preserving the pipeline. FQK also failed to meet the
safety-filter recall requirement. The D034-D049 branch shows that even a
stronger apparent residual improvement can disappear under a matched classical
control and a candidate-specific threshold. The results therefore narrow the
space of credible next methods: a future candidate must be prospectively selected,
beat the strongest controls, preserve grouped leakage protection, and satisfy
the safety objective before mission-level claims are considered.

The result also illustrates why a QML application paper should report
dequantization and capacity controls. A quantum circuit can produce a useful
feature map without producing an application advantage. The exact classical
RBF, random-feature, compressed-input, and physics-residual comparisons make
it harder to attribute an apparent improvement to the quantum component alone.

The recall-first safety analysis provides a separate methodological lesson.
Optimizing Brier score alone can select a model with unacceptable unsafe-case
recall. That observation is useful for a future prospective protocol, but
using it to retune the completed benchmark would invalidate the negative
result. The paper therefore separates future design evidence from active
pipeline evidence.

### 5.1 Gate 6 implication

No QML candidate from P001 earned authority for a Gate 6 mission experiment.
If a future human decision opens Gate 6, it must first freeze a separate
baseline and safety protocol with C06 or numerical-reference controls, paired
Monte Carlo scenarios, safety gates, stopping rules, and claim boundaries.
Such a protocol would be a new experiment, not a rescue of Gate 5.

## 6. Limitations

This is a public-data, development-only benchmark. Calibration and final-test
data were not read, and the simulator was not evaluated in a mission loop.
The study therefore cannot establish operational performance, propellant
savings, flight readiness, NASA approval, or quantum advantage.

The simulator credibility claim is bounded by the eligible evidence set;
RTC3 was not evaluated. Scenario-generation audits also retain decision sets
without an independently feasible numerical reference. These cases are
visible limitations and were not removed after observing model results.

The quantum results are classical statevector simulations in a small-qubit,
laptop-bounded resource envelope. They do not establish hardware behavior,
quantum speedup, noise robustness, or a scalable quantum resource advantage.

The literature package is a bounded evidence review with 23 accepted extracted
records, not an exhaustive systematic review. A post-acceptance discovery
refresh is preserved as archival coverage information and did not alter the
frozen experiment or outcomes. This limits claims about literature
completeness, not the benchmark results.

## 7. Data, Code, and Evidence Availability

Source code, governance records, machine-readable reporting outputs, result
tables, figure registry, and release-support cards are available in the
repository and in the non-draft `v0.3.0` GitHub Release:

https://github.com/taechasith/QMLforArtemisIV/releases/tag/v0.3.0

The release does not include calibration or final-test data, mission-owned
evidence, trained model weights, or a Gate 6 experiment. An archival DOI is
not yet minted and requires a separate human decision.

## 8. Conclusion

Under the frozen public-data development benchmark, the tested QML candidates
did not outperform strong classical controls, and no QML candidate from the
Gate 5 or D034-D049 branches qualified for a Gate 6 mission experiment. The
result is a valid negative benchmark with useful future-design lessons,
including evidence that matched classical residual controls explain the
strongest apparent successor gain. It is not evidence of quantum advantage,
fuel savings, flight readiness, NASA approval, or a proven new QML invention.

## 9. Submission Readiness Checklist

- [x] Gate 5 technical result accepted as a benchmark-specific `FAIL`.
- [x] Q01b and FQK exploratory negatives reported separately.
- [x] Q02/Q03 labeled `not_reached_under_frozen_eligibility`.
- [x] Simulator, data, model, limitation, and reproducibility records released.
- [x] Source tag `v0.3.0` and non-draft GitHub Release published.
- [x] Paper result tables and claim-boundary table committed.
- [x] Formally close the bounded literature scope without claiming an exhaustive systematic review.
- [x] Select final main-text and supplementary figure families from the registry.
- [x] Freeze the D034-D049 successor branch as development-only negative evidence.
- [ ] Add author names, affiliations, funding, conflicts, and contribution statements.
- [ ] Select a target journal and apply its format, word, figure, and data rules.
- [ ] Complete independent internal scientific and reproducibility review.
- [ ] Decide whether to mint an archival DOI before submission.

## Source Tables and Figure Evidence

- `paper/results_tables/gate5_qml_vs_controls.csv`
- `paper/results_tables/post_gate5_invention_branch_summary.csv`
- `paper/results_tables/claim_boundary_table.csv`
- `artifacts/research_figures/figure_registry.csv`
- RFIG-001, RFIG-014, RFIG-021 through RFIG-023, RFIG-026 through RFIG-029,
  RFIG-044 through RFIG-052, and RFIG-062 through RFIG-085

## Selected References

Reference records and screening provenance are maintained in
`literature/extraction_matrix.csv`. The following sources are the core
positioning set and must be formatted in the final target-journal style:

1. Woffinden, Eckman, and Robinson, "Optimized Trajectory Correction Burn
   Placement for the NASA Artemis II Mission," NASA technical report, 2023.
2. NASA, `NASA-STD-7009B Standard for Models and Simulations`, 2024.
3. NASA, `NASA-STD-3001 Volume 2 Revision E`, 2025.
4. Sullivan et al., "Multi-Objective Reinforcement Learning for Low-Thrust
   Transfer Design Between Libration Point Orbits," 2021.
5. Schuld and Killoran, "Quantum Machine Learning in Feature Hilbert Spaces,"
   Physical Review Letters, 2019, doi:10.1103/PhysRevLett.122.040504.
6. Havlicek et al., "Supervised Learning with Quantum-Enhanced Feature
   Spaces," Nature, 2019, doi:10.1038/s41586-019-0980-2.
7. Huang et al., "Power of Data in Quantum Machine Learning," Nature
   Communications, 2021, doi:10.1038/s41467-021-22539-9.
8. Otten et al., "Quantum Machine Learning Using Gaussian Processes with
   Performant Quantum Kernels," 2020, arXiv:2004.11280.
9. Schnabel and Roth, "Quantum Kernel Methods under Scrutiny: A Benchmarking
   Study," 2024, arXiv:2409.04406.
10. Bowles, Ahmed, and Schuld, "Better than Classical? The Subtle Art of
    Benchmarking Quantum Machine Learning Models," 2024, arXiv:2403.07059.
