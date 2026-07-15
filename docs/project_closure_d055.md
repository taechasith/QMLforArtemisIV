# D055-C Experimental Program Closure and Manuscript Freeze

Version: 0.1.0
Decision: D055-C
Parent: D054-A/P018 and D033-C
Prepared and accepted: 2026-07-16
Status: **Active experiment closed; manuscript package frozen for publication preparation**

## 1. Decision

D055-C closes the active QML experimental program and declines to execute the
prospective D054-A/P018 symmetry audit. P018 remains a clearly labeled
future-only protocol, but it is not part of the completed evidence base and
cannot delay manuscript preparation.

This closes experimentation, not scholarly review. The remaining work is
publication administration and independent scientific review: finalize the
bounded literature statement, add author and journal metadata, select the
submission format, and preserve the reproducibility package.

## 2. Final scientific result

The completed public-data study supports the following bounded result:

- Gate 3 accepted 67 evaluable simulator checks with zero failures; RTC3 was
  not tested with eligible evidence and is neither a pass nor a fail.
- D006 completed 871 of 871 authorized campaign tasks with zero task failures
  and zero calibration/final-test reads.
- The preregistered Q01 benchmark scored mean NRMSE 0.6466 versus 0.008739
  for C06, with no qualifying regime. Gate 5 is a valid technical FAIL.
- Q01b scored 0.661207 versus 0.006833 for C06. FQK reached AUROC 0.7436,
  Brier score 0.1561, and recall 0.1089; neither exploratory track advanced.
- The D034-D049 successor branch contains 16 complete valid development-only
  negatives. Its best apparent C06 comparison did not survive the matched
  classical-control rule, so no QML candidate earned Gate 6 authority.

These results do not prove that QML cannot work. They show that the tested
quantum feature maps and their preregistered successors did not justify their
additional complexity for this frozen task and control set.

## 3. Scientific contribution and claim boundary

The contribution is a source-bound, grouped, matched-control benchmark that
records negative results rather than selecting a favorable QML variant. The
strongest useful conclusion is methodological: apparent gains from a quantum
feature representation must be tested against physics-derived controls,
classical dequantizations, strict thresholds, and explicit eligibility rules.
The branch summary in
`paper/results_tables/post_gate5_invention_branch_summary.csv` makes this
negative evidence auditable.

The project must not claim quantum advantage, a new QML invention, propellant
savings, mission-loop validity, flight readiness, NASA approval, or operational
benefit. The study is public-data and development-only.

## 4. Explicitly closed or prohibited work

D055-C does not authorize:

- the D054-A DOP853/SVD audit or any P018 data read;
- deterministic SRP activation;
- new model fitting, refitting, reranking, retrying, or threshold changes;
- calibration, final-test, mission-loop, hardware, or GPU execution;
- Gate 5 reinterpretation or Gate 6;
- publication of an unsupported QML-advantage or QML-invention claim.

RFIG-086 remains a methods-boundary figure only. RFIG-087 through RFIG-089
remain empty reservations and are not results.

## 5. Publication package

The manuscript and evidence package are:

- `paper/manuscript.md`;
- `paper/results_tables/gate5_qml_vs_controls.csv`;
- `paper/results_tables/post_gate5_invention_branch_summary.csv`;
- `paper/results_tables/claim_boundary_table.csv`;
- the registered Gate 3, Gate 5, exploratory, closure, and reproducibility
  figures;
- `docs/manuscript_submission_readiness.md`;
- the published `v0.3.0` release and its strict negative-claim boundary.

The paper is ready for author/journal metadata and independent review. Those
items are not scientific evidence and cannot be filled with invented details.
