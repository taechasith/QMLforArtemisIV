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

## Current Invention Readiness Assessment

The project is not ready to invent and test a new QML architecture yet. The
next scientifically correct step is D013-C: harden residual and safety-filter
classical baselines, then decide whether a future QML invention has a fair and
non-rescue target.
