# Research Execution Map

Version: 0.6.2
Prepared: 2026-07-10
Updated: 2026-07-12

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
| 5. Development and algorithm trigger | Generate and validate unlocked payloads, run only preregistered development analysis, and test whether the residual-QML trigger passes | In progress: D005 accepted; D006 exact-control campaign candidate awaits explicit acceptance before fitting | Pre-D003 F0 excluded; RFIG-002 through RFIG-020 retained; 39,000 development rows pass preflight and the proposed 450-task first stage is blocked; source-bound reporting, worst-shape scale gating, final-root containment, and mandatory D004 diagnostic reporting are frozen; calibration/final reads remain zero; trigger report pending |
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
