# Research Execution Map

Version: 0.2.0  
Prepared: 2026-07-10

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
| 3. Simulator credibility | Implement F0/F1/F2 dynamics, mass depletion, events, crew constraints, numerical verification, GMAT comparison, and held-out validation | Approve the simulator for dataset generation or stop/repair | GMAT R2026a comparison completed 2026-07-11; all 10 independent endpoint thresholds failed (position 1.699–14.094 km vs 0.100 km limit; velocity 0.141–1.402 m/s vs 0.010 m/s limit). Status: `failed_repair_required`. Pending human decision. ML/QML training prohibited. |
| 4. Phase 1 freeze | Complete systematic review; generate locked datasets; implement classical and QML models; freeze features, tuning spaces, and analysis code without opening final tests | Approve the prediction benchmark | Review synthesis, data card, model registry, locked analysis |
| 5. Algorithm trigger | Run only the preregistered development analysis; test whether the residual-QML trigger passes | Authorize one new-model variant or reject algorithm invention | Trigger report with seed-level evidence |
| 6. Mission experiment | Freeze safety filter and mission scenarios; run paired Monte Carlo with common random numbers and sequential precision stopping | Approve the final mission experiment and interpretation boundary | Scenario card, safety-filter tests, paired results |
| 7. Claims and release | Draft results and discussion, perform robustness and negative-result analysis, audit reproducibility, prepare paper, archive, and GitHub release | Accept or reject each main claim and public release | Manuscript, result tables, model/simulation cards, tagged archive |

## Discussion structure reserved in advance

The final discussion will distinguish five questions:

1. Did predictive performance improve under a fair budget?
2. Did that improvement reduce robust correction delta-v in the mission loop?
3. Did every safety, crew, reserve, and deadline gate remain non-inferior?
4. Which findings survive noise, limited data, operational revisions, and OOD
   stress?
5. What additional mission-owned evidence would be required before any
   operational consideration?

No positive quantum conclusion is required. A strong negative result, including
the regimes and reasons for failure, is a publishable target.
