# D025-C Gate 5 Closure And Gate 6 Recommendation

Version: 0.1.0
Decision: D025-C
Protocol: P001
Prepared: 2026-07-14
Accepted: 2026-07-14
Status: Gate 5 closure complete; no QML Gate 6 candidate

## Decision

D025-C closes the current Gate 5 and post-Gate-5 5X evidence chain into a
single Gate 6 recommendation report. It is a reporting and governance step
only. It does not authorize Gate 6, mission-loop execution, calibration or
final-test access, model fitting, reranking, retrying, threshold application,
hardware/GPU execution, QML invention claims, quantum-advantage claims, or
Gate 5 reinterpretation.

## Evidence Summary

The preregistered Gate 5 trigger failed. Q01 reached mean NRMSE 0.6466, while
the strongest physics-residual control C06 reached 0.008739, and there were
zero qualifying residual regimes.

The post-Gate-5 QML explorations were also negative. Q01b remained far worse
than C06, with a 95.77x relative NRMSE gap. FQK did not satisfy safety-filter
conditions, with mean recall 0.1089 and mean Brier 0.1561 against stronger
classical controls.

The recall-first CSAFE-RF branch found a useful future design signal:
`calibrated_logistic` reached mean recall 0.8043. D024-C interpreted that
signal as non-advancing because it is post-D017-informed and calibration/Brier
quality remains unresolved. The A02 exact-RBF feasibility QML-style candidate
did not dominate.

## Gate 6 Recommendation

Do not proceed to a QML Gate 6 mission experiment from P001. No QML candidate
earned locked-data, mission-loop, or quantum-advantage authority.

If the human research lead later wants to open Gate 6, the scientifically safe
scope is a separate baseline/safety mission protocol only. That protocol should
freeze C06 or numerical-reference controls, paired Monte Carlo scenarios,
safety gates, stopping rules, and claim boundaries before any calibration,
final-test, or mission-loop access. It must not be presented as a rescue of
Gate 5 or as QML evidence.

## Manuscript Position

The paper should report Gate 5 as a valid negative QML benchmark, place Q01b
and FQK in the exploratory negative appendix, and discuss recall-first
CSAFE-RF as future protocol design evidence. RFIG-044 records the closure and
Gate 6 recommendation boundary.
