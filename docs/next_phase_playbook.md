# OpenQFuel-Cislunar: next-phase research playbook

This is the execution manual for continuing the project in an AI-enabled code
editor. It assumes a fresh clone of
[`taechasith/QMLforArtemisIV`](https://github.com/taechasith/QMLforArtemisIV),
the Gate 2 files already on `main`, and a researcher who accepts or rejects the
explicit decision gates.

The governing rule is:

> Every completed phase must be committed, tested, documented, and pushed to
> GitHub before the next phase opens. Never run the next phase on an unrecorded
> working tree.

The current unpushed Gate 3A checkpoint is local commit `432385a` in the
original worktree. If your clone does not contain the files listed in
[`ai_editor_handoff_manifest.md`](ai_editor_handoff_manifest.md), copy them
first or reimplement them using the exact specification below, then commit and
push that checkpoint before formal validation.

## 1. Non-negotiable scientific rules

1. Do not call simulated samples telemetry or ground truth.
2. Do not train or tune any ML model until Gate 3 simulator credibility is
   accepted.
3. Do not inspect the locked final-test labels while selecting features,
   architectures, hyperparameters, seeds, or preprocessing.
4. Use the same data groups, uncertainty draws, random seeds, safety filter,
   wall-clock budget, and reporting rules for classical and quantum models.
5. A negative QML result is valid and publishable. Do not invent an algorithm
   merely because a quantum model is behind.
6. Do not use the phrase quantum advantage for classical simulation results.
7. Any change to an accepted outcome, split, threshold, source role, exclusion,
   compute ceiling, or uncertainty range requires a dated deviation entry and
   human approval.
8. Preserve failed optimizer cases and unsafe candidates in machine-readable
   audit outputs; do not remove them to improve averages.
9. Every result must identify source release, kernel checksum, software lock,
   configuration, frame, time system, seed, and hardware.
10. The final claim can only be about simulation-based, safety-filtered
    performance within the tested public-data uncertainty domain.

## 2. Phase 0: clone and verify the starting point

Run this in the cloned repository:

```bash
git clone https://github.com/taechasith/QMLforArtemisIV.git
cd QMLforArtemisIV
git switch main
git pull --ff-only origin main
git status --short --branch
```

Install the reproducible environment:

```bash
uv sync --extra figures
uv run python -m pytest -q
uv run python -m compileall -q src scripts tests
uv pip check
```

If the GitHub remote does not yet contain Gate 3A, copy the files in the
handoff manifest before running the tests. The repository should then show a
clean working tree before any new edit.

## 3. Phase 3A: publish the simulator-core freeze

### Objective

Make the F0/F1/F2 implementation visible and reproducible before producing
formal held-out validation metrics.

### Files required

- [`configs/dynamics.yaml`](../configs/dynamics.yaml): frozen constants, force
  terms, frames, time conversion, fidelity levels, tolerances, and deferred
  boundaries;
- [`src/openqfuel/ephemeris.py`](../src/openqfuel/ephemeris.py): JPL DE440s
  adapter and checksum check;
- [`src/openqfuel/dynamics.py`](../src/openqfuel/dynamics.py): point-mass,
  third-body, J2, impulses, finite burns, mass depletion, and DOP853;
- [`src/openqfuel/propulsion.py`](../src/openqfuel/propulsion.py): public
  thrust catalog and propellant equations;
- [`src/openqfuel/constraints.py`](../src/openqfuel/constraints.py): crew
  protected intervals, blackout buffers, emergency reason codes, and body-axis
  acceleration limits;
- [`data/public_source_checksums.csv`](../data/public_source_checksums.csv):
  DE440s SHA-256 and size;
- [`tests/test_dynamics.py`](../tests/test_dynamics.py) and
  [`tests/test_constraints.py`](../tests/test_constraints.py): executable
  physical and human-constraint checks;
- `pyproject.toml` and `uv.lock`: locked runtime and optional figure extra.

### Public data setup

The DE440s binary is not committed. Use the registry and fetcher:

```bash
uv run python scripts/fetch_public_data.py --id D029
sha256sum data/raw/ephemeris/de440s.bsp
```

The digest must equal:

```text
c1c7feeab882263fc493a9d5a5b2ddd71b54826cdf65d8d17a76126b260a49f2
```

If the provider changes the file, stop and create a protocol deviation. Do not
silently update the checksum.

### Acceptance checklist

- [ ] `uv run python -m pytest -q` passes.
- [ ] F0 circular-orbit closure passes.
- [ ] SI impulse units are tested.
- [ ] Finite-burn mass flow matches thrust/(Isp·g0).
- [ ] F2 requires the checked DE440s kernel.
- [ ] Sleep blackout and acceleration constraints reject unsafe candidates.
- [ ] `git diff --check` is clean.
- [ ] The dynamic model has been committed before formal validation is run.

### Required push

```bash
git add configs/dynamics.yaml data/public_source_checksums.csv data/source_registry.csv \
  docs/decision_log.md docs/research_execution_map.md pyproject.toml uv.lock \
  src/openqfuel/constraints.py src/openqfuel/dynamics.py src/openqfuel/ephemeris.py \
  src/openqfuel/propulsion.py tests/test_constraints.py tests/test_dynamics.py
git commit -m "Freeze Gate 3 simulator core before formal validation"
git push origin main
```

After the push, verify the commit on GitHub before proceeding. Record the commit
URL in `docs/decision_log.md` if the project convention requires a checkpoint
link.

## 4. Phase 3B: formal simulator credibility validation

### Objective

Run the frozen simulator against parser, convergence, cross-tool, event, and
held-out Artemis II criteria. This phase must produce a pass/fail result for
every requirement, not only a mean score.

### Files to implement

Create or complete:

- `scripts/validate_simulator.py`: one deterministic entry point;
- `src/openqfuel/validation.py`: reusable metric and acceptance functions;
- `data/processed/simulator/interpolation_validation.csv`;
- `data/processed/simulator/numerical_convergence.csv`;
- `data/processed/simulator/f2_flight_validation.csv`;
- `data/processed/simulator/event_cross_checks.csv`;
- `data/processed/simulator/acceptance_summary.csv`;
- `docs/gate3_simulator_credibility.md`;
- `tests/test_validation.py`.

### Required analyses

#### 4.1 Parser and interpolation

Use leave-one-out Hermite interpolation on eligible OEM points. Exclude the
detected state-transition intervals in
`data/processed/artemis2/oem_detected_discontinuities.csv`. Report p95 position
and velocity errors and the sample count. Both must remain no worse than 0.005
km and 0.005 m/s respectively.

#### 4.2 Numerical convergence

For each of V01–V05, propagate with the nominal F2 settings and with
`ForceModelSettings.tightened()`. Compare six-hour endpoint position and
velocity. Every arc must meet 0.01 km and 0.001 m/s. Save both endpoint states,
absolute differences, and solver settings; do not report only a pass flag.

#### 4.3 Flight-ephemeris validation

Use the exact frozen validation windows and the April 10 eligible reference
release. Start from the OEM state at the window start and compare the propagated
F2 trajectory at every reference epoch. Report position/velocity RMSE and
endpoint errors.

Every validation arc must satisfy:

| Arc class | Position RMSE | Position endpoint | Velocity RMSE | Velocity endpoint |
|---|---:|---:|---:|---:|
| Non-lunar V01, V02, V04, V05 | ≤10 km | ≤20 km | ≤1 m/s | ≤2 m/s |
| Lunar V03 | ≤25 km | ≤50 km | ≤2 m/s | ≤5 m/s |

Also calculate error reduction relative to the tracked Earth-only baseline.
Every validation arc must achieve at least the frozen 80% improvement rule.

#### 4.4 Event cross-checks

Check TLI, OTC3, RTC1, RTC2, RTC3, and lunar closest approach. Use the event
registry for public timing and clearly label rounded times. Do not turn a rounded
event article into state truth. If the eligible historical OEM cannot validate
an event because it is beyond its creation time, record `not_eligible` with the
reason rather than fabricating a pass. In every report, define `not_eligible` as
**not tested with eligible evidence; neither pass nor fail**. State explicitly
that no validation claim is made for that event. The acceptance report must say
whether the missing check blocks Gate 3.

#### 4.5 Independent GMAT comparison

Use NASA GMAT R2026a (D028) as an independent tool. Do not compare against a
different force model and call it same-model agreement. The GMAT script must
state:

- UTCGregorian epoch and Earth-centered J2000-compatible state;
- Earth, Moon, and Sun point masses;
- whether Earth J2 is enabled and which coefficient file is used;
- no drag and no solar-radiation pressure unless the Python model also includes
  them;
- integrator, error control, step settings, and constants;
- executable version and checksum; and
- output endpoint states for each validation arc.

For the same force model, every endpoint must meet 0.10 km and 0.01 m/s.
If GMAT cannot run in the editor environment, publish the exact script,
required download, environment limitation, and `pending` status. Do not replace
independent comparison with a second Python implementation.

### Formal stop rule

If any required criterion fails, set the Gate 3 status to `failed_repair_required`,
publish the failure, and stop before ML training. Repair only through a logged
deviation. A failure is a legitimate research result.

### Required push

```bash
uv run python scripts/validate_simulator.py
uv run python -m pytest -q
git add scripts/validate_simulator.py src/openqfuel/validation.py \
  data/processed/simulator docs/gate3_simulator_credibility.md tests/test_validation.py
git commit -m "Run Gate 3 simulator credibility validation"
git push origin main
```

Then ask the human research lead to accept or reject Gate 3. Do not begin Phase
4 until the decision is explicit in `docs/decision_log.md`.

## 5. Phase 4: literature synthesis and Phase 1 prediction benchmark freeze

### Gate condition

Gate 3 must be accepted. If it is rejected, remain in simulator repair.

### Objective

Create a fair prediction benchmark that estimates correction outcomes from
simulated scenarios without opening the locked final test set.

### Required literature work

1. Execute each search string in `literature/review_protocol.md`.
2. Save query date, database, exact string, filters, and result count.
3. Deduplicate by DOI, NASA report number, arXiv ID, and title.
4. Screen title/abstract and record exclusion reason.
5. Extract model family, state/action representation, fidelity, data source,
   split, metric, uncertainty treatment, compute, and failure reporting.
6. Score quality domains and separate evidence from author claims.
7. Write a synthesis that explicitly includes negative and inconclusive results.

### Required data work

Create:

- `literature/search_log.csv`;
- `literature/screening_log.csv`;
- `literature/extraction_matrix.csv`;
- `docs/literature_synthesis.md`;
- `data/processed/simulator/data_card.md`;
- `data/processed/simulator/scenario_schema.json`;
- `data/processed/simulator/seed_manifest.csv`.

Generate F0/F1/F2 scenarios only after the accepted simulator report. The frozen
dataset allocation is 10,000 F0 cases, 50,000 F1 cases, and an initial 5,000 F2
cases, with up to 5,000 active-learning additions. Retain at least 25% boundary
or tail conditions and all nonconvergence cases.

Group splits by mission epoch, uncertainty family, and base trajectory. Use 60%
development, 10% uncertainty calibration, 15% in-distribution final test, and
15% out-of-distribution final test. Lock the final-test manifest before any
feature engineering or model selection.

### Candidate models

The preregistered comparison should include strong classical models before QML:

- regularized linear/elastic-net baseline;
- random forest or extra trees;
- gradient-boosted trees;
- Gaussian process or sparse GP where the data size permits;
- multilayer perceptron;
- physics-informed residual or low-fidelity-correction model.

The QML set should be resource-matched and include at least:

- quantum kernel regression/classification;
- variational quantum regressor;
- hybrid physics-feature quantum residual model.

Report qubit counts 4, 6, and 8; 10 and 12 only if the compute budget permits.
Include encoding, circuit depth, shots, optimizer, initialization, simulator
backend, and classical overhead. A quantum circuit simulated on a CPU is not a
hardware speedup.

### Required push

```bash
uv run python -m pytest -q
git add literature docs data/processed configs scripts tests
git commit -m "Freeze Phase 1 prediction benchmark without opening final tests"
git push origin main
```

Request Gate 4 approval before reading final-test labels.

## 6. Phase 5: preregistered algorithm trigger

### Objective

Decide whether a new physics-constrained quantum residual algorithm is
justified. It is not a default deliverable.

The trigger requires all of the following:

1. A QML model is within 5% of the strongest classical primary prediction
   error.
2. A residual regime remains after matched preprocessing and parameter counts.
3. The regime survives grouped validation and at least 20 independent seeds.

If any condition fails, do not invent a new algorithm. Publish the negative
QML result and analyze where classical methods dominate.

If all conditions pass, implement only one candidate variant and compare it
against:

- the parent QML model;
- the low-fidelity physics model;
- a parameter-matched classical residual model; and
- the strongest unrestricted classical model.

Create:

- `experiments/phase1_model_registry.yaml`;
- `experiments/phase1_seed_results.csv`;
- `experiments/algorithm_trigger_report.md`;
- `src/openqfuel/models/`;
- `tests/test_models.py`.

Push the trigger report and all seed-level machine-readable results before
asking for authorization to open the mission experiment.

## 7. Phase 6: mission experiment

### Gate condition

Gate 4 benchmark approval and Gate 5 trigger decision must both be recorded.

### Objective

Test whether predictive differences survive the actual safety-filtered mission
loop and improve robust correction delta-v.

Freeze before opening final results:

- scenario manifest and common-random-number seeds;
- burn action space and timing constraints;
- crew/safety/reserve/deadline filter;
- deterministic fallback policy;
- optimizer termination and compute budget;
- paired Monte Carlo estimator;
- sequential precision stopping rule; and
- result-file schema.

Each model must face identical scenarios and the same unsafe-candidate policy.
Report success, fallback, infeasible, nonconverged, and unsafe-candidate counts,
not only successful cases.

Required primary outputs:

- total correction delta-v;
- 95% CVaR;
- propellant consumed and reserve remaining;
- safety-filter violation rate;
- crew acceleration margin;
- deadline/fallback rate;
- lunar altitude and entry-interface constraint margins;
- planner wall-clock time; and
- paired bootstrap or paired confidence intervals.

Stress strata must include communication holds, burn delays, mass error,
main-engine thrust sensitivity, and propulsion-model error. Use common random
numbers so model comparisons are paired.

Create `experiments/phase2_scenario_card.md`,
`experiments/phase2_results.csv`, `experiments/phase2_paired_statistics.csv`,
`docs/mission_experiment_report.md`, and safety-filter tests. Push before
opening final interpretation.

## 8. Phase 7: results, discussion, and release

The final paper must answer five separate questions:

1. Did prediction improve under a fair budget?
2. Did prediction improve robust mission correction delta-v?
3. Did safety, crew, reserve, and deadline gates remain non-inferior?
4. Do results survive noise, OOD stress, data revisions, and seed variation?
5. What mission-owned evidence is still required before operational use?

Required artifacts:

- `paper/manuscript.md` or source LaTeX;
- `paper/results_tables/`;
- `paper/figures/` generated from scripts, never hand-edited;
- model card for every released model;
- simulation credibility report;
- data card and provenance manifest;
- limitations and negative-results appendix;
- `CITATION.cff` update only after a release decision;
- tagged Git release and archival DOI plan;
- final reproducibility audit from a clean clone.

The final wording must remain conditional: “within the public-data model and
tested uncertainty domain.” It must not imply NASA, SpaceX, Orion, or any
mission authority has approved the method.

### Required release push

```bash
git clone https://github.com/taechasith/QMLforArtemisIV.git clean-release-check
cd clean-release-check
git switch main
uv sync --extra figures
uv run python -m pytest -q
uv run python scripts/reproduce_all.py
git tag -a vX.Y.Z -m "OpenQFuel-Cislunar research release"
git push origin main --follow-tags
```

The tag and archive are created only after the human research lead accepts each
main claim and the release checklist.

## 9. Required GitHub checkpoint convention

Use one focused commit per phase. Recommended messages:

| Phase | Commit message |
|---|---|
| Gate 3A | `Freeze Gate 3 simulator core before formal validation` |
| Gate 3B | `Run Gate 3 simulator credibility validation` |
| Gate 4 | `Freeze Phase 1 prediction benchmark without opening final tests` |
| Gate 5 | `Record preregistered algorithm trigger decision` |
| Gate 6 | `Run paired safety-filtered mission experiment` |
| Gate 7 | `Publish audited results and discussion` |

For every push, record in `docs/decision_log.md`:

- date and commit URL;
- tests and commands run;
- files and data added;
- whether final labels were visible;
- any failed or nonconverged cases;
- any protocol deviation; and
- the exact human decision requested.

## 10. AI code-editor operating prompt

Paste this at the start of each phase:

```text
You are working on OpenQFuel-Cislunar. Read research_protocol.md,
docs/gate2_data_numeric_freeze.md, docs/decision_log.md, and
docs/next_phase_playbook.md before editing. Work only on the named phase.
Preserve all frozen values, source IDs, splits, thresholds, and seeds. Do not
train ML before Gate 3 acceptance. Do not inspect locked final-test labels.
Add tests and machine-readable outputs. Keep raw public downloads out of Git
unless redistribution is explicitly permitted. Run the complete test suite and
diff checks. Update the decision log. Stop if a required criterion fails or a
protocol deviation is needed. Commit the phase with the prescribed message and
push to origin main. Report the commit URL, tests, results, failures, and the
human accept/reject decision required before the next phase.
```

## 11. Current next action

The immediate next action is not ML. It is:

1. copy or recreate the unpushed Gate 3A files from the handoff manifest;
2. download and checksum D029 DE440s;
3. run the 30-test suite;
4. commit and push Gate 3A;
5. implement `scripts/validate_simulator.py` and its report;
6. run numerical, event, flight-arc, and GMAT checks;
7. push the Gate 3B evidence; and
8. ask the human lead to accept or reject Gate 3.

Do not proceed to Phase 4 until that decision is written down.
