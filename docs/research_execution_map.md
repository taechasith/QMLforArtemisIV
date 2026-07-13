# Research Execution Map

Version: 0.6.11
Prepared: 2026-07-10
Updated: 2026-07-14

## Working agreement

The assistant research partner performs the literature work, data engineering,
simulation, model implementation, experiments, statistical analysis,
documentation, repository maintenance, and recommendations. The human research
lead does not need to perform those technical tasks. The human research lead
accepts, rejects, or requests revision at explicit decision gates and remains
the final authority for scope, methodological deviations, claims, and release.

## Work from now to publication

| Gate | Assistant work | Decision for human research lead | Completion evidence |
|---|---|---|---|
| 2. Data and numeric freeze | Audit public files; freeze variables, uncertainty, splits, tolerances, practical effect, and compute budget | Accepted 2026-07-11 | Frozen Gate 2 package |
| 3. Simulator credibility | Implement F0/F1/F2 dynamics, mass depletion, events, crew constraints, numerical verification, GMAT comparison, and held-out validation | Accepted 2026-07-12 with RTC3 explicitly outside the validation claim | 67 evaluable checks passed, 0 failed; all 10 repaired GMAT endpoints passed unchanged limits; RTC3 was not tested with eligible evidence |
| 4. Phase 1 freeze | Execute bounded literature synthesis; freeze manifest-only identities, grouped splits, features, models, controls, tuning, seeds, and analysis without research outcomes | Accepted with D002 on 2026-07-12 | 65,000 identities committed, final payloads absent, 23 evidence records frozen; post-acceptance refresh has 4,218 unique discovery rows and 926 open full-text screens without changing the freeze |
| 5. Development and algorithm trigger | Generate and validate unlocked payloads, run only preregistered development analysis, and test whether the residual-QML trigger passes | Accepted as technical `FAIL` on 2026-07-13; the proposed new algorithm is not authorized | D007 package valid; Q01 mean NRMSE 0.6466 versus C06 0.00874; zero qualifying regimes; Q02/Q03 are `not_reached_under_frozen_eligibility`; all 871 tasks remain complete with zero failures and zero calibration/final reads; RFIG-001 and RFIG-021 through RFIG-023 record the decision and evidence; Gate 6 remains unauthorized |
| 5X. Exploratory protocol | Execute the accepted post-Gate-5 Q01b projected quantum kernel and FQK feasibility-only quantum kernel protocol under corrected fold-shape admission | D011-C1 ended in an authority-hash technical `STOP`; corrected admission and development campaign not reached | D009 remains an immutable telemetry STOP, D010 attempt 2 remains a closed synthetic PASS under its own frozen shape, and D011 remains a terminal pre-launch STOP from the `scripts` namespace import failure. D011-C1 corrected the launcher import and passed its import smoke test, but the formal command stopped during correction-authority hash validation before synthetic workload or resource admission. P001-FR003 is future-only. RFIG-029 is cumulative; RFIG-031 and RFIG-026 through RFIG-028 remain absent. Calibration/final-test, hardware/GPU, Gate 5 reinterpretation, and Gate 6 remain locked |
| 6. Mission experiment | Freeze safety filter and mission scenarios; run paired Monte Carlo with common random numbers and sequential precision stopping | Approve the final mission experiment and interpretation boundary | Scenario card, safety-filter tests, paired results |
| 7. Claims and release | Draft results and discussion, perform robustness and negative-result analysis, audit reproducibility, prepare paper, archive, and GitHub release | Accept or reject each main claim and public release | Manuscript, result tables, model/simulation cards, tagged archive |

## Discussion structure reserved in advance

The final discussion will distinguish five questions:

1. Did predictive performance improve under a fair budget?
2. Did that improvement reduce robust correction delta-v in the mission loop?
3. Did every safety, crew, reserve, and deadline gate remain non-inferior?
4. Which findings survive noise, limited data, operational revisions, and OOD stress?
5. What additional mission-owned evidence would be required before any operational consideration?

No positive quantum conclusion is required. A strong negative result, including
the regimes and reasons for failure, is a publishable target.
