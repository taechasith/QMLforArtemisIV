# Can Quantum Machine Learning Improve Propellant-Efficient Human-Rated Cislunar Guidance?

Status: D027-C manuscript Results/Discussion draft; not release-ready

## Abstract Draft Boundary

This manuscript reports a governed public-data computational benchmark for
QML-assisted cislunar correction planning. Under the frozen development
benchmark, the tested QML candidates did not outperform strong classical
controls. The result is a valid negative benchmark, not a quantum-advantage or
mission-readiness claim.

## Results

### Gate 5 Preregistered Benchmark

The preregistered Gate 5 algorithm trigger failed under the frozen
development-only benchmark. The Q01 quantum-kernel candidate reached mean
NRMSE 0.6466, while the strongest physics-residual control C06 reached 0.008739.
No residual regime qualified for a QML advance. This is the official Gate 5
technical FAIL.

### Post-Gate-5 Exploratory QML

The post-Gate-5 exploratory QML branches did not produce an advancing signal.
Q01b reached mean NRMSE 0.6612 versus C06 at 0.006833, a 95.77x relative gap.
FQK reached AUROC 0.7436, Brier 0.1561, and recall 0.1089, which was not
adequate for a safety filter. These results are exploratory negatives; they
cannot revise Gate 5 or open Gate 6.

### Recall-First Safety Lesson

The recall-first CSAFE-RF branch produced a future protocol lesson but not an
advancing result. The D023-C audit selected `calibrated_logistic` with recall
0.8043, false-negative rate 0.1957, and Brier 0.1422. D024-C interpreted this
as evidence that future safety filters should prospectively prioritize missed
unsafe cases and calibration constraints. It did not rescue D017 and did not
make a QML candidate eligible.

### Gate 6 Recommendation

No QML candidate is eligible for a Gate 6 mission experiment from P001. If
Gate 6 is opened later, it must be a separate baseline/safety mission protocol
accepted by the human research lead.

## Discussion

The negative result is scientifically useful because it narrows the future QML
invention target. A candidate must beat C06 and the safety-filter controls
under prospectively frozen splits, thresholds, and claim rules before any
mission-loop claim is credible. The tested QML encodings did not do that.

The exploratory QML failures also constrain future design. The Q01b projected
kernel did not encode correction-cost structure well enough, and FQK did not
meet safety-filter recall needs. These failures should be reported rather than
hidden because they prevent selective reporting and identify where future
methods must improve.

The CSAFE-RF branch shows that the safety objective matters. A Brier-first
selection can produce low recall, while a recall-first rule can recover missed
unsafe cases. That lesson must be frozen prospectively in any future protocol;
it cannot be used after observing outcomes to rescue an earlier branch.

## Conclusion

Under the frozen public-data development benchmark, tested QML candidates did
not outperform strong classical controls. The correct conclusion is a valid
negative QML benchmark with useful future-design lessons, not quantum
advantage, not fuel savings, and not mission readiness.

## Claim Boundary

Do not claim quantum advantage, fuel savings, flight readiness, NASA approval,
mission-loop validation, or Gate 6 authorization.

## Source Tables

- `paper/results_tables/gate5_qml_vs_controls.csv`
- `paper/results_tables/claim_boundary_table.csv`
