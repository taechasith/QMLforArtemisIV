# D026-C Manuscript Results Synthesis

Version: 0.1.0
Decision: D026-C
Protocol: P001
Prepared: 2026-07-14
Accepted: 2026-07-14
Status: Manuscript synthesis ready

## Purpose

D026-C converts the closed Gate 5 and 5X evidence into manuscript-ready claim
language. It is not an experiment and does not authorize Gate 6, calibration,
final-test access, mission-loop execution, model fitting, reranking, retrying,
hardware/GPU work, QML invention claims, quantum-advantage claims, or Gate 5
reinterpretation.

## Allowed Claims

The main result is a valid negative benchmark: under the frozen public-data
development benchmark, the tested QML candidates did not outperform strong
classical controls. Q01 reached mean NRMSE 0.6466 versus C06 at 0.008739, and
there were zero qualifying residual regimes.

The post-Gate-5 QML tests are exploratory negatives. Q01b remained far worse
than C06, and FQK did not satisfy safety-filter conditions.

The recall-first CSAFE-RF branch is a future protocol lesson only. It shows
that missed-unsafe-case priority can select a higher-recall candidate, but it
does not solve calibration quality and does not make a QML candidate eligible.

## Prohibited Claims

The manuscript must not claim quantum advantage, flight readiness, NASA
approval, Artemis operational readiness, QML mission benefit, Gate 6
authorization, or a rescue of Gate 5.

## Writing Plan

The next writing step is to draft Results and Discussion around negative
evidence, failed and stopped branches, reference-laptop limits, simulator
credibility, limitations, and future protocol design. RFIG-045 records the
allowed/prohibited claim boundary.
