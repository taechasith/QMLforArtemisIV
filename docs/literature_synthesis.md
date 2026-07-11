# Gate 4 Bounded Literature Synthesis

Version: 0.3.0
Search date: 2026-07-12
Search cutoff: 2026-07-10
Status: Gate 4 freeze candidate; bounded scoping synthesis, not a complete systematic review

## 1. Decision use

This synthesis supports the Phase 1 prediction-benchmark design before any
research scenario outcome is generated. It determines the registered model
families, fairness controls, metrics, and claim boundaries. It does not provide
evidence that QML improves cislunar guidance, and it is not used to tune a
model to a research result.

The machine-readable audit trail is:

- `literature/search_log.csv`: exact queries, interfaces, dates, counts, and coverage;
- `literature/screening_log.csv`: deduplication and screening decisions;
- `literature/extraction_matrix.csv`: 23 fully extracted evidence records and domain ratings;
- `scripts/run_literature_search.py`: reproducible API search and deduplication;
- `scripts/build_literature_extraction.py`: curated extraction and second-pass closure.

## 2. Search flow and limitation

All seven frozen concepts S1-S7 were executed on OpenAlex. The seven count
queries returned 9,732 results in aggregate, but repeated metadata export
requests received HTTP 429 responses. Those records were not treated as
retrieved, screened, or included evidence.

Complete supplemental API retrieval produced 387 NASA NTRS records for S1,
S5, S6, and S7 and 1,043 date-eligible arXiv records for S2, S3, and S4. After
deduplication with 13 seed records, there were 1,404 records. Reference-chain
checking added two unique records, producing the final 1,406-row screening
ledger.

| Final source-row decision | Count | Meaning |
|---|---:|---|
| Included | 24 | Fully assessed source rows; two rows represent the same Artemis II evidence family |
| Deferred to Phase 6 | 42 | Control or mission-design evidence not required to freeze Phase 1 prediction models |
| Excluded | 1,340 | Did not directly inform the registered Phase 1 task, fairness controls, or statistics |

The 24 included source rows map to 23 unique extracted evidence records. This
is a bounded, reproducible scoping synthesis, not the complete systematic
review anticipated by the original review protocol. Crossref, NASA ADS, and a
complete AIAA/publisher search were not exported in this pass. Proposed
Deviation D002 in `docs/decision_log.md` asks the human research lead to accept
this limitation for the Gate 4 freeze while requiring a broader update before
manuscript submission.

## 3. Findings that control Phase 1

### 3.1 Mission task and labels

The Artemis II burn-placement study treats correction planning as constrained,
uncertainty-aware trajectory design rather than unconstrained delta-v
regression. That supports a paired cost-and-feasibility surrogate, independent
repropagation of selected plans, and a numerical trajectory method as the
reference rather than a learned label as truth. See the [NASA Artemis II
trajectory-design paper](https://ntrs.nasa.gov/api/citations/20230000223/downloads/Artemis2OptTrajDesignFinal.pdf).

Classical low-thrust surrogate studies support separate reachability or
feasibility outputs, learning curves, physics scaling, and validation by a
propagator. They do not establish transfer to Orion or Artemis IV. Their role
is methodological: require a feasibility head, retain nonconvergence, and
compare MLP and physics-residual models against numerical references. Relevant
records include [feasible-trajectory classification](https://arxiv.org/abs/2202.04962)
and [real-time neural guidance](https://arc.aiaa.org/doi/10.2514/1.G005254).

### 3.2 QML evidence is mixed or negative

A broad QML benchmark found no consistent superiority over tuned classical
models and found that removing entanglement was often not harmful. The freeze
therefore includes six strong classical families, a required no-entanglement
ablation, and negative-result reporting. See [Bowles, Ahmed, and Schuld](https://arxiv.org/abs/2403.07059).

Data re-uploading is a valid variational design, but its original small-circuit
demonstration is classically simulable and is not evidence of practical
advantage. It justifies an auditable candidate family, not an advantage claim.
See [Perez-Salinas et al.](https://quantum-journal.org/papers/q-2020-02-06-226/).

Quantum-kernel evidence shows that encoding scale and bandwidth can dominate
performance, while classical approximations can remove an apparent quantum
benefit. The freeze therefore tunes a registered feature scale and adds a
random-Fourier ridge control on identical PCA inputs and samples. See
[Shaydulin and Wild](https://arxiv.org/abs/2111.05451), [Sweke et al.](https://arxiv.org/abs/2309.11647),
and [Huang et al.](https://www.nature.com/articles/s41467-021-22539-9).

Quantum annealing for trajectory transcription is quantum optimization, not
QML. It is retained in the evidence map but excluded from the three Phase 1
QML model families. See [De Grossi et al.](https://link.springer.com/article/10.1007/s42064-024-0216-6).

No included source demonstrates an end-to-end practical quantum advantage for
Artemis trajectory correction. No result from the in-repository statevector
simulator can establish hardware speedup.

### 3.3 Statistics and failure reporting

Non-normal benchmark errors can change model ranking, so the analysis cannot
rely on one average score. Phase 1 retains seed-level rows and reports RMSE,
MAE, tails, bootstrap intervals, paired permutation tests, and Holm-adjusted
comparisons. See [Pernot, Huang, and Savin](https://arxiv.org/abs/2004.02524).

Optimization failures and nonconverged trajectory cases are outcomes, not
records to resample away. Variational initialization remains fixed to a small
seeded interval, every failed seed is retained, and training fit is not used
as proof of generalization. See [Grant et al.](https://quantum-journal.org/papers/q-2019-12-09-214/)
and [Peters and Schuld](https://arxiv.org/abs/2209.05523).

### 3.4 Credibility and human-rated boundaries

[NASA-STD-7009B](https://standards.nasa.gov/sites/default/files/standards/NASA/B/1/NASA-STD-7009B-Final-3-5-2024.pdf)
supports explicit intended use, input pedigree, validation evidence,
uncertainty, and limitations. [NASA-STD-3001 Volume 2](https://standards.nasa.gov/standard/NASA/NASA-STD-3001_VOL_2)
supports treating crew constraints as separate hard requirements rather than
folding them into a prediction score. Public standards do not make this
software flight-qualified.

## 4. Frozen implications

The evidence directly produced these Gate 4 controls:

1. Cost regression and independently propagated feasibility are co-primary model outputs.
2. Six classical candidates precede three QML candidates.
3. QML uses identical grouped splits, preprocessing, PCA dimensions, sample IDs, and budgets as its matched controls.
4. Quantum feature scale and entanglement are explicit registered variables.
5. Random-Fourier ridge is an interpretation control and cannot be hidden if it matches a quantum kernel.
6. Four, six, and eight qubits are required; ten and twelve remain unauthorized.
7. Exact statevector, finite-shot, and fixed hardware-agnostic noise sensitivities are reported separately.
8. All failed optimizer seeds, infeasible selections, and nonconverged scenarios remain in the result record.
9. Quantum advantage language is prohibited for classical simulation.

## 5. Evidence gaps

- There is no public Artemis IV mission-owned dispersion, propulsion, or guidance dataset sufficient to reproduce operational planning.
- There is no included head-to-head QML benchmark for crewed cislunar correction planning.
- Hardware QML evidence does not establish useful scale, latency, or reliability for this task.
- The current search is incomplete because OpenAlex metadata export was throttled and several planned databases remain for the manuscript update.
- Public human-system standards define a credibility boundary, not project-specific operational values for every Artemis IV constraint.

These gaps limit claims; they do not justify filling missing values with
unlabeled assumptions or treating simulation as telemetry.
