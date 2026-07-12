# Gate 4 Bounded Literature Synthesis

Version: 0.4.0
Search date: 2026-07-12
Search cutoff: 2026-07-10
Status: Accepted for Gate 4 under D002; bounded scoping synthesis, not a complete systematic review

## 1. Decision use

This synthesis supports the Phase 1 prediction-benchmark design before any
research scenario outcome is generated. It determines the registered model
families, fairness controls, metrics, and claim boundaries. It does not provide
evidence that QML improves cislunar guidance, and it is not used to tune a
model to a research result.

The machine-readable audit trail is:

- `literature/search_log.csv`: exact queries, interfaces, dates, counts, and current refresh coverage;
- `literature/screening_log.csv`: deduplicated discovery decisions and open full-text queue;
- `literature/extraction_matrix.csv`: 23 fully extracted evidence records and domain ratings;
- `scripts/run_literature_search.py`: reproducible API search and deduplication;
- `scripts/build_literature_extraction.py`: curated extraction and second-pass closure.

## 2. Search flow and limitation

The accepted Gate 4 snapshot is preserved in commit `61bef3e`. At that
decision, all seven frozen concepts S1-S7 had OpenAlex count results totaling
9,732, but repeated metadata exports received HTTP 429 responses. Complete
supplemental retrieval produced 387 NASA NTRS and 1,043 date-eligible arXiv
records. Deduplication, seed records, and reference-chain checking produced a
closed 1,406-row screening ledger: 1,340 exclusions, 42 Phase 6 deferrals, and
24 included source rows mapping to 23 extracted evidence records. That is the
evidence set that informed the accepted Phase 1 freeze.

A post-acceptance discovery refresh retried the same frozen interfaces without
using research outcomes. The current `search_log.csv` records 4,708 raw API
rows: 3,278 OpenAlex, 387 NASA NTRS, and 1,043 arXiv rows. Two OpenAlex queries
completed metadata pagination; five remain bounded to the first 100
relevance-ranked records after rate limiting. The OpenAlex count snapshots now
total 9,747. One completed query returned six more raw page rows than its count
snapshot, so these values are treated as API audit counts rather than a stable
universe size.

The refreshed discovery ledger contains 4,218 unique canonical keys:

| Current discovery decision | Count | Meaning |
|---|---:|---|
| Title/abstract exclude | 3,288 | Does not pass the current direct task-method conjunction rule |
| Pending full-text screen | 926 | Discovery candidate only; no evidence claim is authorized |
| Provisional include | 4 | Requires authoritative-record reconciliation before extraction |

The refresh does not replace or enlarge the 23-record accepted extraction
matrix and did not change a model, split, threshold, metric, or claim. RFIG-014
records this distinction. The synthesis remains bounded and is not a complete
systematic review: 926 full-text decisions, Crossref, NASA ADS, and a complete
AIAA/publisher search remain open. D002 requires closure before manuscript
submission and prohibits outcome-driven model changes from later literature.

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
- The current search is incomplete because five OpenAlex exports remain bounded, 926 refreshed records await full-text screening, and several planned databases remain for the manuscript update.
- Public human-system standards define a credibility boundary, not project-specific operational values for every Artemis IV constraint.

These gaps limit claims; they do not justify filling missing values with
unlabeled assumptions or treating simulation as telemetry.
