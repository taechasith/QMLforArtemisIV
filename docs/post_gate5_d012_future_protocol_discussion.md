# D012 Future Protocol Discussion

Version: 0.1.0
Decision: D012
Protocol: P001
Prepared: 2026-07-14
Accepted: 2026-07-14
Status: Discussion-only opened; Gate 6 unauthorized; D013-C selected as planning-only successor

## Authority Boundary

D012 opens a future-protocol discussion from the completed D011-R1
development-only negative results. It does not authorize a new experiment,
refit, rerank, retry, calibration access, final-test access, hardware/GPU
execution, Gate 5 reinterpretation, quantum-advantage claim, or Gate 6 work.

Any executable successor requires a separate prospective decision, currently
reserved as D013. D013 would need to freeze the scientific question, controls,
thresholds, splits, compute admission, stop rules, figures, and claim boundary
before any new development payload or implementation work begins.

## Evidence Being Discussed

D011-R1 completed one frozen development-only campaign from source commit
`083d777`. It read 39,000 development rows and zero calibration or final-test
rows. Hardware/GPU and Gate 6 runs remained zero.

Q01b selected PX-03 and completed all five folds and 20 selected seeds, but it
was not promising. Mean pooled OOF NRMSE was 0.6612 versus C06 at 0.0068328,
the relative gap was 95.769x, and no preregistered dequantization regime
qualified.

FQK selected PX-03 and completed all five folds and 20 selected seeds, but it
was not promising. Mean AUROC/Brier/recall were 0.7436/0.1561/0.1089 versus
strongest comparator C02-T02 at 0.9134/0.1062/0.3233.

RFIG-026 through RFIG-028 show the reached development evidence. RFIG-029
records the firewall between observed failures/negative results and future-only
ideas. RFIG-031 remains corrected synthetic compute-admission evidence only.

## Discussion Questions

1. Did D011 fail mainly because the one-RDM projected representation was too
   weak for the cost target and feasibility boundary?
2. Which future QML variant can be specified prospectively without tuning from
   the D011 outcome?
3. Which stronger classical controls must accompany any future QML attempt?
4. What minimum development-only evidence would be required before requesting
   calibration, final-test, hardware, or Gate 6 authority?

## Candidate Future Protocols

### D012-A: Task-Informed Local-Observable Projected Kernel

This is the most direct QML successor if the project continues QML work. The
D011 Q01b result suggests the frozen one-RDM Pauli projection did not encode the
robust correction cost well enough. A future protocol could prospectively
define richer local observable projections or task-informed encodings before
seeing any new outcomes.

This candidate must keep strong controls: A02 exact classical RBF on identical
fold-local PCA rows, random-feature RBF, compressed MLP, physics-residual
controls, and C06. It is discussion-only under D012.

### D012-B: Class-Sensitive Feasibility Quantum Kernel

This is the second QML candidate. D011 FQK underperformed C02-T02 on AUROC,
Brier, and recall, and the frozen 0.5 threshold produced high false-negative
rate. A future protocol could prospectively specify class-sensitive kernel
training and a separately frozen safety-threshold selection rule.

This candidate must keep C02-T02, calibrated logistic, class-weighted tree
ensemble, A02, and C06 controls. It is discussion-only under D012.

### D012-C: Classical-First Residual and Safety-Filter Hardening

This is the recommended non-QML discussion path before any new experiment. Both
near-term QML tracks were weaker than classical controls, so the research may
gain more scientific value by first hardening physics-residual controls,
calibration, and safety-filter design under the same grouped split discipline.

This path would not be a QML rescue. It would establish a stronger future
baseline that any later QML protocol must beat. It is discussion-only under
D012.

## Current Recommendation

Do not open Gate 6. Do not run another QML experiment immediately.

D013-C has been selected as the planning-only successor. It prepares
classical-first residual and safety-filter hardening before any new QML
invention process. D012-A remains the main QML invention candidate for a later
prospective protocol, and D012-B remains secondary unless feasibility recall
becomes the dominant scientific question.

The current paper can already report a high-value negative result: under a
source-bound laptop-feasible campaign with strong controls and locked splits,
the tested QML projected-kernel variants did not produce a promising
development-only signal.
