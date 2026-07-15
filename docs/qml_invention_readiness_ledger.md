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

### D035 result label

**Observed result:** CFQSR-08-N mean pooled OOF NRMSE `0.0134629` versus C06
`0.00683281`, with paired difference `+0.00663006` and 95% interval
`[+0.00662749,+0.00663245]`. A02-STACK-q8 scored `0.00984926`; no endpoint
condition passed.

**Useful invention signal:** cross-fitting prevents in-sample C06 baseline
leakage but did not reveal a residual correction that could compete with C06.
The next candidate should change the coordinate map, not the frozen baseline,
and must use a matched classical control.

**Prohibited use:** do not call D035 a failure of every QML method, rerank its
q values, or claim NASA performance, mission benefit, quantum advantage, or
Gate 6 eligibility.

**Required next control:** D036 TAP-QK uses residual-supervised PLS scores and
TAP-RBF on the same scores to separate a task-alignment effect from a quantum
kernel effect.

## D036 P004: task-aligned projected quantum kernel

D036 is authorized as one new development-only protocol. It fits a fold-local
PLS projection to cross-fitted C06 residuals, standardizes the resulting
scores using training rows only, and applies the existing projected quantum
kernel. The matched TAP-RBF control uses identical scores and solver settings.
The full mathematical contract, claim labels, leakage checks, and falsification
rules are in `docs/post_gate5_d036_tapqk_protocol.md`. No D036 result exists
until its source-bound endpoint completes; no locked data, Gate 6, hardware, or
quantum-advantage claim is authorized.

### D037 result label

**Observed result:** primary TSQR-08-L025 scored NRMSE `0.00684778` versus C06
`0.00683281`, with paired difference `+0.0000149672` and 95% interval
`[+0.0000146573,+0.0000152701]`. TSQR-08-L010 scored `0.00675013`, while the
matched TAP-RBF-SHR-08-L010 scored `0.00675359`; no quantum-specific rule
passed.

**Useful invention signal:** correction shrinkage can reduce harm from an
overactive residual model, but the small gain is reproduced by the classical
control. The next candidate should test a different quantum kernel geometry.

**Prohibited use:** do not rerank D037 or present the lambda=0.10 ablation as
a primary success, and do not claim NASA performance, quantum advantage, or
Gate 6 eligibility.

**Required next control:** D038 tests global state fidelity against the same
task-aligned TAP-RBF control at fixed lambda=0.10.

## D038 P006: global fidelity residual kernel

D038 is authorized as one new development-only protocol. It replaces local
one-RDM projection distance with exact global state fidelity in an entangling
one-layer circuit, while preserving the D036 task-aligned scores and D037
lambda=0.10 stabilization. The result remains unresolved until the
source-bound endpoint completes; no locked data, Gate 6, hardware, or
quantum-advantage claim is authorized.

### D036 result label

**Observed result:** TAPQK-08 mean pooled OOF NRMSE `0.0103815` versus C06
`0.00683281`, with paired difference `+0.00354871` and 95% interval
`[+0.00354672,+0.00355058]`. TAP-RBF-q8 scored `0.00987042`; the candidate
failed every superiority condition.

**Useful invention signal:** residual-supervised PLS coordinates did not expose
a correction that competes with C06. The remaining candidate should test
stability of the correction magnitude rather than add unverified circuit
complexity.

**Prohibited use:** do not rerank D036 q values, claim NASA performance or
quantum advantage, or reinterpret the negative as a Gate 6 qualification.

**Required next control:** D037 applies fixed shrinkage to both the quantum and
matched classical residual corrections, preserving the C06 safety guard.

## D037 P005: trust-region shrunk quantum residual

D037 is authorized as one new development-only protocol. It uses the D036
task-aligned coordinates and tests fixed correction multipliers 0.10, 0.25,
and 0.50 across q=4/6/8. The primary is q=8, lambda=0.25. The matched
TAP-RBF control receives the same multiplier. The result remains unresolved
until the source-bound endpoint completes; no locked data, Gate 6, hardware, or
quantum-advantage claim is authorized.

### D038 result label

**Observed result:** GFRK-08-L010 scored mean pooled OOF NRMSE `0.00664716`
versus C06 `0.00683281`; paired difference `-0.000185652`, with 95% interval
`[-0.000187118,-0.000184266]`. The result improved C06 by about 2.7% but did
not meet the frozen 5% rule or beat the matched TAP-RBF-SHR-q8-L010 control by
5%.

**Useful invention signal:** global state fidelity preserved predictive
structure not retained by the local one-RDM projection. The next test should
make the residual representation explicitly conditional on the honest C06
prediction rather than changing the kernel again.

**Prohibited use:** do not call D038 scientifically superior, claim NASA
performance or quantum advantage, revise Gate 5, or authorize Gate 6.

**Required next control:** D039 adds the outer-fold C06 prediction as a
fold-local PLS input feature and applies the same error-conditioned coordinates
to the matched classical RBF.

## D039 P007: error-conditioned global fidelity residual kernel

D039 is authorized as one new development-only protocol. It tests whether the
first clean GFRK signal is strengthened when the learned coordinates explicitly
identify where the C06 baseline is likely to err. The C06 prediction is
cross-fitted for the training projection and generated without validation
outcomes for the outer validation projection. All other kernel, shrinkage,
split, seed, safety, threshold, and resource rules remain frozen.

### D039 result label

**Observed result:** EC-GFRK-08-L010 scored mean pooled OOF NRMSE `0.00646644`
versus C06 `0.00683281`, an approximately 5.36% improvement, with paired
difference `-0.000366372` and 95% interval `[-0.000367832,-0.000365004]`.
The matched EC-TAP-RBF-SHR-q8 control scored `0.00675401`, so the quantum
candidate did not pass the 5% classical-control rule.

**Useful invention signal:** conditioning the residual representation on the
honest C06 prediction produced a stronger signal than D038, but most of the
gain was available to the identical classical kernel. The next test should
remove dominant common-similarity structure with training-only kernel
centering, without changing the error-conditioned input or control.

**Prohibited use:** do not call D039 scientifically superior, claim NASA
performance or quantum advantage, revise Gate 5, or authorize Gate 6.

**Required next control:** D040 applies the same training-only centered feature
map to CE-GFRK and its matched classical RBF.

## D040 P008: centered error-conditioned global fidelity residual kernel

D040 is authorized as one new development-only protocol. It retains the D039
error-conditioned feature and global fidelity geometry, then centers the
whitened landmark feature map using training rows only. The identical centered
feature construction is applied to the matched classical RBF, preserving fair
comparison and all frozen split, seed, safety, threshold, and resource rules.

### D040 result label

**Observed result:** CE-GFRK-08-L010 scored mean pooled OOF NRMSE `0.00650367`
versus C06 `0.00683281`, with paired difference `-0.000329145` and 95%
interval `[-0.000330332,-0.000327932]`. The improvement was about 4.82%, below
the 5% rule, and the centered classical control scored `0.00677146`.

**Useful invention signal:** centering the error-conditioned feature map was
numerically valid but slightly weakened the D039 endpoint. The next candidate
should test complementary residual channels rather than further centering.

**Prohibited use:** do not call D040 scientifically superior, claim NASA
performance or quantum advantage, revise Gate 5, or authorize Gate 6.

**Required next control:** D041 mixes the D039 fidelity correction with an RBF
correction and compares it against an identically weighted two-bandwidth RBF.

## D041 P009: hybrid error-conditioned fidelity-RBF residual kernel

D041 is authorized as one new development-only protocol. It uses fixed mixture
weights `eta=0.25, 0.50, 0.75` between the D039 global-fidelity correction and
an RBF correction. The primary is q=8, eta=0.50. The matched classical control
uses the same weights between RBF corrections at gamma multipliers 0.25 and
0.50. All splits, seeds, residual targets, safety metrics, thresholds, and
data boundaries remain frozen.

## D041 P009 technical stop

The first D041 launcher attempt timed out at the local one-hour execution
limit before an atomic endpoint was written. It is a technical failure, not a
scientific negative or positive, and its partial computation must not be
reported. The useful implementation lesson is to cache shared RBF distance and
landmark calculations without changing the declared hybrid workload.

**Required next control:** D041-C1 permits one unchanged D041 attempt with that
execution-only cache correction. The timeout record remains immutable.

## D041 P009 result label

**Observed result:** HEFRK-08-E050 scored mean pooled OOF NRMSE `0.00659197`
versus C06 `0.00683281`, with paired difference `-0.000240838` and 95%
interval `[-0.000241783,-0.000239875]`. The improvement was about 3.52%, below
the frozen 5% rule. HEFRK-08-E075 scored `0.00652507`, while the matched
TWO-RBF-08-E050 control scored `0.00672438`.

**Useful invention signal:** fixed fidelity/RBF fusion reduced error relative
to C06, but the gain did not meet the preregistered threshold and was not a
5%-specific gain over the matched classical fusion. This supports testing a
predeclared, outcome-blind regime gate rather than post-outcome eta selection.

**Integrity label:** 39,000 development rows, 900 channel audits, 900
projection audits, and 400 inner-fold audits completed. Validation outcomes
were not used by the feature or gate construction; group overlap, locked-data
reads, hardware/GPU, mission-loop, and Gate 6 counters were zero. RFIG-068 and
RFIG-069 are the reporting figures.

**Prohibited use:** do not call D041 scientifically superior, claim NASA
performance or quantum advantage, revise Gate 5, or authorize Gate 6.

## D042 P010: adaptive-gated error-conditioned fidelity-RBF kernel

D042 is authorized as one new development-only protocol. AGEFRK uses the
predeclared gate `eta(x) = 0.25 + 0.50 * (1-p_C06(x))`, where the probability
comes from the unchanged outer-fold C06 feasibility head. The candidate mixes
the D041 fidelity and RBF-0.25 residual channels; its matched control mixes
RBF-0.25 and RBF-0.50 with the identical per-row eta. The gate is outcome-blind
and is not tuned after validation outcomes. All frozen thresholds, safety
metrics, grouped splits, seeds, development-only data scope, and CPU-only
resource limits remain unchanged.

## D042 P010 result label

**Observed result:** AGEFRK-08-ADAPT scored mean pooled OOF NRMSE `0.006523834`
versus C06 `0.006832811`, with paired difference `-0.000308977` and 95%
interval `[-0.000310404,-0.000307594]`. The improvement was about 4.52%, below
the frozen 5% rule. TWO-RBF-08-ADAPT scored `0.006738683`; safety and regret
conditions were preserved.

**Useful invention signal:** outcome-blind C06 feasibility gating slightly
improved fixed D041 fusion but did not reach the threshold or establish a
classical-specific gain. The next test should learn a mixture only from
training-only cross-fitted residual evidence, rather than use a feasibility
proxy.

**Integrity label:** 39,000 development rows, 300 channel audits, 300
projection audits, and 100 gate audits completed. Validation outcomes were not
used in gate construction; group overlap, locked-data reads, hardware/GPU,
mission-loop, and Gate 6 counters were zero. RFIG-070 and RFIG-071 are the
reporting figures.

**Prohibited use:** do not call D042 scientifically superior, claim NASA
performance or quantum advantage, revise Gate 5, or authorize Gate 6.

## D043 P011: cross-fitted residual stacking

D043 is authorized as one new development-only protocol. It obtains inner
grouped out-of-fold predictions for each residual channel on outer-training
rows, fits a convex weight from those training-only predictions, and applies
that fold/seed/q weight to outer validation predictions. The candidate stacks
fidelity with RBF-0.25; the matched control stacks RBF-0.25 with RBF-0.50 using
the same procedure. Outer validation outcomes cannot influence the weight.
This is a test of train-only expert specialization, not a quantum advantage
claim.

## D043 P011 result label

**Observed result:** SFRK-08-CV scored mean pooled OOF NRMSE `0.006445379`
versus C06 `0.006832811`, with paired difference `-0.000387432` and 95%
interval `[-0.000388651,-0.000386026]`. The C06 improvement was about 5.67%,
but TWO-RBF-08-CV scored `0.006710554`, so the candidate-over-classical gain
was only about 3.95%.

**Useful invention signal:** training-only cross-fitted stacking is the first
post-Gate-5 candidate to clear the C06 threshold, but the matched classical
stack explains enough of the gain that the strict invention criterion fails.
The next test should examine nonlinear interaction between experts under the
same control and leakage boundary.

**Integrity label:** 39,000 development rows, 300 channel audits, 1,500 stack
audits, and zero validation-outcome use in weight construction were recorded.
Group overlap, locked-data reads, hardware/GPU, mission-loop, and Gate 6
counters were zero. RFIG-072 and RFIG-073 are the reporting figures.

**Prohibited use:** do not call D043 scientifically superior, claim NASA
performance or quantum advantage, revise Gate 5, or authorize Gate 6.

## D044 P012: nonlinear interaction residual stack

D044 is authorized as one new development-only protocol. It fits the fixed
quadratic map `[1,u,v,u*v,u^2,v^2]` on inner grouped out-of-fold residual
experts. The candidate uses fidelity/RBF-0.25 and the matched control uses
RBF-0.25/RBF-0.50 with the identical map, ridge penalty, and cross-fitting.
Outer validation outcomes cannot influence the stack.

## D044 P012 result label

**Observed result:** NIFRK-08-NL scored mean pooled OOF NRMSE `0.006751395`
versus C06 `0.006832811`, with paired difference `-0.000081416` and 95%
interval `[-0.0000840,-0.0000787]`. The improvement was only about 1.19%,
and TWO-RBF-08-NL scored `0.006765864`.

**Useful invention signal:** the fixed quadratic interaction stack weakened the
D043 linear stack and did not establish a classical-specific gain. Further
nonlinear expansion is not justified. The next test returns to a linear model
and tests whether fidelity information is complementary across q=4/6/8.

**Integrity label:** 39,000 development rows, 300 channel audits, 1,500
interaction audits, and zero construction-time validation-outcome use were
recorded. Group overlap, locked-data reads, hardware/GPU, mission-loop, and
Gate 6 counters were zero. RFIG-074 and RFIG-075 are the reporting figures.

**Prohibited use:** do not call D044 scientifically superior, claim NASA
performance or quantum advantage, revise Gate 5, or authorize Gate 6.

## D045 P013: multi-scale fidelity residual stack

D045 is authorized as one new development-only protocol. It fits a fixed
six-channel linear ridge stack from q=4/6/8 fidelity and RBF-0.25 experts. The
matched control uses q=4/6/8 RBF-0.25 and RBF-0.50 experts with the same six
channels, inner cross-fitting, ridge penalty, and data boundary. This tests
cross-q complementarity without expanding the nonlinear branch.

## D045 P013 result label

**Observed result:** MSFRK-ALL scored mean pooled OOF NRMSE `0.006731045`
versus C06 `0.006832811`, with paired difference `-0.000101766` and 95%
interval `[-0.000103313,-0.000100332]`. The improvement was about 1.49%, and
MS-TWO-RBF scored `0.006869509`.

**Useful invention signal:** adding q=4 and q=6 fidelity channels did not
establish the frozen C06 or classical-specific 5% thresholds. The next test
must remove the shared RBF contribution before measuring any fidelity-specific
residual information.

**Integrity label:** 39,000 development rows, 300 channel audits, 1,300
multi-scale audits, and zero construction-time validation-outcome use were
recorded. Group overlap, locked-data reads, hardware/GPU, mission-loop, and
Gate 6 counters were zero. RFIG-076 and RFIG-077 are the reporting figures.

**Prohibited use:** do not call D045 scientifically superior, claim NASA
performance or quantum advantage, revise Gate 5, or authorize Gate 6.

## D046 P014: orthogonalized residual fidelity-RBF kernel

D046 is authorized as one new development-only protocol. A shared RBF-0.25
first-stage correction is fitted to the C06 residual. Inner grouped OOF
RBF-0.25 predictions define a second-stage residual target. The candidate uses
a fidelity second stage; the matched control uses RBF-0.50. This isolates
fidelity information not already explained by the common RBF correction.

## D046 P014 result label

**Observed result:** ORFRK-08-R2 scored mean pooled OOF NRMSE `0.006436255`
versus C06 `0.006832811`, with paired difference `-0.000396556` and 95%
interval `[-0.000398722,-0.000394287]`. The C06 improvement was about 5.80%.
The matched TWO-RBF-08-R2 control scored `0.006750081`, leaving about 4.65%
candidate-over-control improvement.

**Useful invention signal:** orthogonalizing against the shared RBF-0.25
correction strengthened the fidelity residual, but the strict classical-
specific 5% threshold still failed. The next test therefore keeps one shared
q=8 first stage and tests fixed q=4/6/8 second-stage complementarity.

**Integrity label:** 39,000 development rows, 300 channel audits, 1,200
orthogonalized inner audits, and zero validation-outcome use were recorded.
Group overlap, locked-data reads, hardware/GPU, mission-loop, and Gate 6
counters were zero. RFIG-078 and RFIG-079 are the reporting figures.

**Prohibited use:** do not call D046 scientifically superior, claim NASA
performance or quantum advantage, revise Gate 5, or authorize Gate 6.

## D047 P015: orthogonalized multi-scale fidelity stack

D047 is authorized as one new development-only protocol. A shared q=8
RBF-0.25 first stage defines one common residual target. The candidate stacks
q=4/6/8 second-stage fidelity predictions; the matched control stacks q=4/6/8
RBF-0.50 predictions with identical fitting, cross-fitting, ridge, and data
access. This tests cross-q complementarity without post-outcome q selection.
