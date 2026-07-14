# QML Invention Readiness Ledger

Version: 0.1.0
Updated: 2026-07-14
Status: Evidence-label ledger for future QML invention; not an experiment

## Purpose

After the current experimental program is complete, the project may try to
invent a new QML method that beats the strongest documented NASA-relevant and
repository baselines under fair locked-split tests. This ledger records what
each result teaches for that future invention process.

This file does not authorize implementation, refit, rerank, calibration or
final-test access, hardware/GPU execution, Gate 5 reinterpretation, or Gate 6.

## Claim Discipline

Do not claim NASA used a specific QML method unless a cited public source
identifies that method. Until then, the comparison target is NASA-relevant
mission-design evidence plus the strongest controls in this repository.

Useful invention signals may guide a future prospectively frozen protocol.
They cannot alter, rescue, rerank, or reinterpret the completed P001 results.

## Result Labels

| Result ID | Observed Result | Useful Signal For Invention | Prohibited Use | Required Future Control | Claim Boundary |
|---|---|---|---|---|---|
| Gate 5 / D007 Q01 | Official technical FAIL: Q01 mean NRMSE 0.6466 versus C06 at 0.00874; zero qualifying regimes | The original QML residual trigger was too weak under the frozen development benchmark; future QML must show regime-specific residual value before any mission claim | Do not retune Q01, reopen Q02/Q03, or reinterpret Gate 5 | C06, A01/A02, compressed C05, physics-residual controls | Benchmark-specific negative only |
| D011-R1 Q01b | Valid exploratory negative: mean NRMSE 0.6612 versus C06 at 0.0068328; zero qualifying dequantization regimes | One-RDM Pauli projected kernels did not encode robust correction cost well enough; future QML needs richer task-informed observables or encodings | Do not tune a new feature map from D011 outcomes without a new prospective protocol | C06, A02, random-feature RBF, compressed MLP, physics-residual control | Development-only exploratory negative |
| D011-R1 FQK | Valid exploratory negative: AUROC/Brier/recall 0.7436/0.1561/0.1089 versus C02-T02 at 0.9134/0.1062/0.3233 | Feasibility QML needs class-sensitive training and a safety-threshold design if pursued later | Do not change the threshold or relabel FQK as useful after seeing the result | C02-T02, calibrated logistic, class-weighted tree ensemble, A02, C06 | Development-only exploratory negative |
| D009 telemetry STOP | Technical stop from invalid Windows working-set telemetry | Future long runs need typed resource telemetry before admission | Do not treat as QML failure or laptop-capacity evidence | Independent OS telemetry validation | Technical infrastructure evidence only |
| D011 / D011-C1 STOPs | Import and raw-hash authority stops before synthetic workload or research rows | Future source-bound protocols need package-safe launchers and raw Git-blob hash prevalidation | Do not treat as model-performance evidence | Import smoke test and hash-consistency smoke test | Technical provenance evidence only |
| D010 / D011-C2 compute PASS | Synthetic compute admissions passed within laptop limits | The reference laptop can run bounded source-bound synthetic checks when shape and telemetry are correct | Do not treat as model-performance or Gate 6 evidence | Full campaign-shape admission before data fitting | Synthetic compute evidence only |
| D024-C CSAFE-RF interpretation | Recall-first `calibrated_logistic` reached recall 0.8043 but remained post-D017-informed and calibration-limited; A02 exact-RBF did not dominate | Future QML or hybrid safety filters must freeze missed-unsafe-case priority and calibration constraints prospectively | Do not use recall-first audit to rescue D017, open locked data, or claim QML progress | Prospective recall/calibration/false-negative-cost protocol with classical and dequantized controls | Future design signal only |
| D025-C Gate 5 closure | Gate 5 and 5X closed with no QML candidate eligible for Gate 6 | The invention target is now clear: beat C06 and safety-filter controls before mission-loop claims | Do not proceed to QML Gate 6 from P001 | New prospective protocol before any QML invention or Gate 6 mission work | Closure recommendation only |

## Current Invention Readiness Assessment

The project is not ready to invent and test a new QML architecture inside
P001. D025-C closes Gate 5/5X with no QML Gate 6 candidate. The next
scientifically correct use of this ledger is manuscript discussion or a new
prospective future protocol whose QML target must beat C06 and safety-filter
controls before any mission-loop claim.

## D034 P002: PRQK campaign

Date: 2026-07-15
Status: **Authorized as one bounded development-only invention campaign**

D034 opens a new protocol rather than modifying P001. It tests the
Physics-Anchored Residual Projected Quantum Kernel (PRQK): the low-fidelity
physics cost is excluded from the quantum encoding, the kernel learns only the
standardized residual, and the physics baseline is added back analytically.
Six fixed q=4/6/8, entanglement-off/on configurations are ablations, not
post-outcome tuning. C06, BASELINE, and identical-input A02-R are required
controls. Calibration, final-test, hardware/GPU, mission-loop, Gate 5, Gate 6,
NASA-performance, and quantum-advantage claims remain prohibited.

The complete mathematical contract, claim labels, derivation checks,
falsification rule, resource limits, and reporting obligations are in
`docs/post_gate5_d034_prqk_protocol.md` and
`configs/post_gate5_d034_prqk.yaml`. The result is unresolved until the
source-bound run completes. If PRQK is negative, the failure must be graphed,
committed as future-only improvement, and tested only under a new protocol.

### D034 result label

**Observed result:** PRQK-08-N mean pooled OOF NRMSE `0.0293259` versus C06
`0.00683281`, with paired difference `+0.0224931` and 95% interval
`[+0.0224857, +0.0225005]`; regret, infeasible selection, and safety rules
also failed. A02-R-q8 scored `0.0265477`, better than PRQK.

**Useful invention signal:** adding the low-fidelity physics baseline back
after a local projected kernel is mathematically valid but not sufficient;
the local projection or residual target does not retain the structure needed to
compete with the boosted physics residual. The next candidate should learn a
quantum correction to cross-fitted C06 errors rather than to the raw
low-fidelity error.

**Prohibited use:** do not call D034 a failure of every QML method, do not
rerank its six configurations, and do not claim NASA performance, mission
benefit, quantum advantage, or Gate 6 eligibility.

**Required next control:** a new P003 protocol must compare the proposed
cross-fitted C06-stacked quantum correction against C06 and an identical-input
classical stacked RBF, with the same grouped split, seed discipline, and
development-only claim boundary.

## D035 P003: cross-fitted C06-stacked quantum residual

D035 is the next prospective protocol after the D034 negative. It tests whether
the quantum model can learn honest, cross-fitted errors of C06 rather than the
raw low-fidelity error. A02-STACK uses the same residual targets and inputs;
the C06 safety guard is held fixed. The protocol, controls, inner-fold audit,
and negative-result firewall are in
`docs/post_gate5_d035_cfqsr_protocol.md`. No D035 result exists until the
source-bound endpoint completes.
