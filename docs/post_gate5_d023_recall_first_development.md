# D023-C Recall-First Development Audit

Version: 0.1.0
Decision: D023-C
Protocol: P001
Prepared: 2026-07-14
Accepted: 2026-07-14
Status: Development-only reporting audit complete

## Decision

D023-C applies the frozen CSAFE-RF recall-first selection rule to the already
committed D017-C CSAFE development metrics. It does not refit models, rerun
threshold selection, open raw development payloads, or touch calibration,
final-test, hardware/GPU, mission-loop, or Gate 6 scopes.

This is intentionally labeled post-D017-informed. It is useful for future
method design and manuscript discussion, but it is not independent confirmation
and cannot rescue D017 or reopen Gate 5.

## Audit Rule

Eligible models are `calibrated_logistic`, `class_weighted_tree`, and
`a02_exact_rbf_feasibility`. Selection order is:

- higher mean recall;
- lower mean false-negative rate;
- lower mean Brier score;
- simpler model family.

## Boundary

## Outcome

D023-C selected `calibrated_logistic` under the recall-first rule. Mean recall
was 0.8043, mean false-negative rate was 0.1957, and mean Brier score was
0.1422. The lower-Brier `class_weighted_tree` was not selected because its mean
recall was only 0.0139.

No model was refit, no threshold was newly applied to real data, and
calibration/final-test/Gate 6 counters remained zero. RFIG-042 records the
development-only audit. D024 interpretation is required before another
successor decision.
