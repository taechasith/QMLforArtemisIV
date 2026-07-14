# Can Quantum Machine Learning Improve Propellant-Efficient Human-Rated Cislunar Guidance?

Status: D026-C manuscript scaffold; not release-ready

## Abstract Draft Boundary

This manuscript reports a governed public-data computational benchmark for
QML-assisted cislunar correction planning. Under the frozen development
benchmark, the tested QML candidates did not outperform strong classical
controls. The result is a valid negative benchmark, not a quantum-advantage or
mission-readiness claim.

## Results Skeleton

### Gate 5 Preregistered Benchmark

Report Q01 as the official technical FAIL: mean NRMSE 0.6466 versus C06 at
0.008739, with zero qualifying residual regimes.

### Post-Gate-5 Exploratory QML

Report Q01b and FQK as exploratory negatives. These results can inform future
encoding and safety-filter design but cannot revise Gate 5 or open Gate 6.

### Recall-First Safety Lesson

Report CSAFE-RF as future protocol design evidence. The recall-first audit
selected `calibrated_logistic` with recall 0.8043, but calibration/Brier
quality remains unresolved and QML did not dominate.

### Gate 6 Recommendation

State that no QML candidate is eligible for a Gate 6 mission experiment from
P001. If Gate 6 is opened later, it must be a separate baseline/safety mission
protocol accepted by the human research lead.

## Discussion Skeleton

The discussion should explain why negative results are scientifically useful:
they constrain future QML invention targets, identify failed encodings, expose
safety-objective tradeoffs, and prevent overclaiming from public-data
development evidence.

## Claim Boundary

Do not claim quantum advantage, fuel savings, flight readiness, NASA approval,
mission-loop validation, or Gate 6 authorization.
