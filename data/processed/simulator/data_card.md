# Phase 1 Scenario Dataset Card

Version: 0.3.0
Prepared: 2026-07-12
Status: Gate 4 accepted; all unlocked D003-v1 F0 qualified; F1/F2 pending

## Intended use

The planned dataset supports a controlled comparison of classical ML and QML
surrogates for simulated, uncertainty-aware cislunar trajectory-correction
cost and feasibility. It is for research benchmarking and advisory
mission-planning studies only. It is not telemetry, a reconstruction of
proprietary Artemis IV operations, a flight-certified dataset, or evidence
that a learned model can command a spacecraft.

## Current contents

Gate 4 defines the accepted identities, groups, counts, schemas, seeds, and
cryptographic commitments. A pre-D003 attempt generated 7,000 F0 rows after
acceptance, but all failed the conformance audit and are prohibited from model
fitting, tuning, calibration, or benchmark claims. They remain only as
failed-attempt evidence. All 14 corrected D003-v1 F0 development/calibration
groups are now admitted: all 7,000 rows pass strict audit. F1 and F2 remain
ungenerated at this checkpoint.
`data/locked/phase1/` is ignored and absent; any file there before an explicit
unlock causes the preparation audit to fail closed.

The compact 60-row `scenario_manifest.csv` deterministically defines 65,000
candidate-plan row identities grouped into 13,000 decision sets of five plans:

| Split | F0 | F1 | F2 | Total | Gate 4 payload state |
|---|---:|---:|---:|---:|---|
| Development | 6,000 | 30,000 | 3,000 | 39,000 | Corrected F0 valid (6,000 rows); F1/F2 pending |
| Uncertainty calibration | 1,000 | 5,000 | 500 | 6,500 | Corrected F0 valid (1,000 rows); F1/F2 pending and calibration-use restricted |
| In-distribution final test | 1,500 | 7,500 | 750 | 9,750 | Locked and not generated |
| Out-of-distribution final test | 1,500 | 7,500 | 750 | 9,750 | Locked and not generated |

The allocation contains 23,571 designated boundary or tail identities
(36.26%), exceeding the frozen 25% minimum. All U5 groups are tail groups. A
deterministic hash order selects the lowest quarter of non-U5 group replicates
as boundary cases. Nonconvergence is retained as an outcome and is never
silently replaced.

## Unit and provenance

One valid D003 row will represent one simulated candidate correction plan under one
fidelity, base trajectory, mission epoch, and uncertainty family. Base windows
come from the Gate 2 qualified Artemis II validation-window registry. F0, F1,
and F2 outcomes will be produced by the Gate 3 accepted simulator and frozen
public-data assumptions. The simulation is calibrated within the documented
Gate 3 domain; it is not a source of flight truth outside that domain.

Scenario IDs follow `F{0|1|2}-G{01..20}-{replicate}`. Consecutive blocks of
five rows map to decision-set IDs
`F{0|1|2}-G{01..20}-D{decision_set_index}` and candidate indices 1-5. These
fields are evaluation metadata and prohibited model inputs. A decision set with
no independently feasible candidate is retained, gives every model the frozen
20 m/s regret penalty, and is reported separately.

The split grouping key is mission epoch plus uncertainty family plus base
trajectory. A key appears in exactly one split, preventing near-duplicate
mission contexts from crossing development and test data.

## Inputs and outcomes

The normative field definition is `scenario_schema.json`. Inputs include
mission time, initial Cartesian state, mass and remaining propellant,
navigation perturbations, candidate burn timing and vector, execution errors,
communication hold, low-fidelity predictions, categorical context, and five
physics-derived quantities.

The primary regression outcome is
`robust_total_correction_delta_v_m_s`. The paired feasibility outcome is
`independently_propagated_feasible`. Secondary outcomes include the burn
vector, terminal errors and margin, propellant use, nonconvergence, and
violation code. D003 also records minimum sampled lunar surface altitude when
the candidate can affect the E006 flyby window; this is a secondary constraint
audit outcome and not a model input.

Identifiers, decision-set metadata, split names, group IDs, and outcome-derived
statistics are prohibited model inputs. Input features are sensitivity
variables generated under the registered uncertainty model, not measured
probabilities or telemetry unless a source explicitly supports that
interpretation.

## Split access and generation order

1. Gate 4 was accepted before any research outcome was visible.
2. D003 requires the repaired generator to be committed, then one corrected F0 group to pass schema, relationship, uncertainty, and checksum audit before scale-up.
3. Development payloads may then be generated in resumable, checksum-verified groups; pre-D003 payloads remain excluded.
4. The calibration split may calibrate uncertainty or probability outputs only after model selection; it cannot fit, tune, or select a model.
5. Final-test payloads require a separate explicit unlock commit after the candidate, preprocessing, tuning outcome, and analysis implementation are fixed.
6. In-distribution and OOD final tests are evaluated once and reported together with all failed and nonconverged rows.

## Preprocessing

Numeric median values, missing indicators, scaling, categorical vocabulary,
target scaling, and PCA are fitted on development data only. QML and matched
classical controls receive the same development-fitted PCA representation and
the same hash-selected samples. No calibration or final-test statistic may
affect preprocessing or feature selection.

## Quality and limitations

- Simulator credibility is bounded by public data and Gate 3 validation; RTC3 was not validated with eligible post-event evidence.
- Artemis IV mission-owned distributions and proprietary spacecraft details are unavailable.
- Boundary and OOD allocations are designed stress conditions, not asserted operational frequencies.
- F0/F1/F2 fidelity differences can create domain shift and must be reported separately.
- A generated label is a numerical-model outcome with uncertainty, not ground truth in the operational sense.
- There are no personal, medical, or directly identifying data in the planned dataset.

## Reproducibility commitments

`configs/phase1_benchmark.yaml` is normative. `seed_manifest.csv` contains 300
registered training/shot seed rows for nine candidates and one interpretation
control. `tuning_manifest.csv` contains 300 frozen, unexecuted trials. Artifact
hashes are recorded in `gate4_freeze_checksums.csv` and can be regenerated with:

```powershell
uv run python scripts/prepare_gate4_freeze.py --check
```

The reference laptop controls chunking and concurrency, not scientific case
counts, split membership, seeds, tolerances, or acceptance rules.
