# Research Execution Map

Version: 0.6.40
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
| 5X. Exploratory protocol | Execute the accepted post-Gate-5 Q01b projected quantum kernel and FQK feasibility-only quantum kernel protocol under corrected fold-shape admission | D033-C release package ACCEPTED; no QML Gate 6 candidate | D009 remains an immutable telemetry STOP, D010 attempt 2 remains a closed synthetic PASS, D011 remains a terminal pre-launch STOP, D011-C1 remains a terminal authority-hash STOP, and D011-C2 remains corrected synthetic compute admission. D011-R1 completed one frozen development-only campaign with 39,000 development rows and zero calibration/final-test rows. Q01b and FQK are valid exploratory negatives. D017-C completed; D018-C records CRES as baseline-only and CSAFE as failed safety utility. D019-C records the Brier-vs-recall lesson. D020-C freezes recall-first CSAFE-RF. D021-C implements and validates CSAFE-RF guards/metrics on synthetic arrays only. D022-C passed clean-source synthetic compute admission. D023-C audits committed D017 CSAFE metrics and selects calibrated logistic by recall-first rule without refit. D024-C interprets that signal as future-useful but non-advancing because calibration remains unresolved and QML does not dominate. D025-C recommends no QML Gate 6 mission experiment from P001. D026-C converts the closed evidence into allowed/prohibited manuscript claims. D027-C drafts source-backed Results and Discussion sections. D028-C creates model/simulator/data/limitation cards. D029-C stops release readiness on clean-clone byte-provenance failures. D030-C fixes checkout byte policy and passes the clean clone audit. D031-C completes final claim/release review preparation. D032-C release-candidate manifest READY hashes the release-candidate decision packet. D033-C accepts the release package under the strict negative-claim boundary. RFIG-037 through RFIG-052 record boundaries. Calibration/final-test, Gate 5 reinterpretation, threshold application to real data, new development-data fitting, hardware/GPU, mission-loop work, DOI minting, and Gate 6 remain locked |
| 6. Mission experiment | Not authorized by current evidence. If opened later, freeze a separate baseline/safety mission protocol with C06 or numerical-reference controls, paired Monte Carlo scenarios, safety gates, stopping rules, and claim boundaries | Human lead must approve a new baseline/safety-only Gate 6 protocol before any calibration, final-test, or mission-loop work | D025-C recommendation: no QML Gate 6 candidate; no Gate 6 run authorized |
| 7. Claims and release | Finish manuscript, perform robustness and negative-result analysis, audit reproducibility, prepare archive, and publish only after human approval | Release package accepted and published under D033-C; structural manuscript draft complete | D033-C release package ACCEPTED and PUBLISHED at https://github.com/taechasith/QMLforArtemisIV/releases/tag/v0.3.0. `paper/manuscript.md` now contains the full structural draft and `docs/manuscript_submission_readiness.md` records the remaining literature, metadata, journal, independent-review, and DOI tasks. RFIG-052 remains the accepted release boundary; no scientific evidence changed. DOI minting, Gate 6, locked data, mission loop, model release, QML invention claims, and quantum-advantage claims remain unauthorized |

## Discussion structure reserved in advance

The final discussion will distinguish five questions:

1. Did predictive performance improve under a fair budget?
2. Did that improvement reduce robust correction delta-v in the mission loop?
3. Did every safety, crew, reserve, and deadline gate remain non-inferior?
4. Which findings survive noise, limited data, operational revisions, and OOD stress?
5. What additional mission-owned evidence would be required before any operational consideration?

No positive quantum conclusion is required. A strong negative result, including
the regimes and reasons for failure, is a publishable target.

After D013-C, all completed results should also be labeled for future QML
invention readiness: useful design signal, required future control, prohibited
post-outcome use, and claim boundary.
