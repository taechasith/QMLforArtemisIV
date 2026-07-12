# OpenQFuel-Cislunar: research record to date

Historical note, 2026-07-12: this is an archival Gate 2/Gate 3 handoff record.
It is superseded for current status by `README.md`, `research_protocol.md`,
`docs/decision_log.md`, and `docs/research_execution_map.md`.

Status date: 2026-07-11  
Repository: [taechasith/QMLforArtemisIV](https://github.com/taechasith/QMLforArtemisIV)  
Current remote status: Gate 2 package published; Gate 3A simulator-core
checkpoint is prepared locally but is not yet on the remote repository.

This document is a factual handoff record. It distinguishes completed methods,
descriptive results, frozen assumptions, and work that has not yet been done.
It is not a claim that a quantum model has been shown to improve spacecraft
operations.

## 1. Research question and operational boundary

The study asks:

> Under a fixed public-data model, common random scenarios, equal computation
> budgets, crew and safety constraints, and reproducible numerical simulation,
> which classical or quantum machine-learning method best predicts or selects
> propellant-efficient cislunar trajectory corrections?

The planned optimization boundary is post-translunar-injection trajectory
correction planning through the return correction sequence. The intended use is
ground-planning decision support. The study does not authorize flight control,
does not replace mission-owned guidance and navigation models, and does not
claim that simulated data are telemetry.

The primary mission objective is robust total correction delta-v, expressed as
nominal correction delta-v plus a 3-sigma contribution from OTC2 through RTC3.
CVaR is the non-Gaussian tail metric. Propellant mass is a secondary
Tsiolkovsky sensitivity because public flight-specific mixture-state and Isp
data are incomplete.

## 2. Governance and decision gates completed

| Gate | Meaning | Status | Evidence |
|---|---|---|---|
| Gate 0 | Governance and human decision authority | Accepted 2026-07-10 | [`research_protocol.md`](../research_protocol.md), [`docs/decision_log.md`](decision_log.md) |
| Gate 1 | NASA-first scope and mission boundary | Accepted 2026-07-10 | [`research_protocol.md`](../research_protocol.md) |
| Gate 2 | Public data, numeric assumptions, uncertainty, splits, thresholds, compute ceiling | Accepted 2026-07-11 | [`docs/gate2_data_numeric_freeze.md`](gate2_data_numeric_freeze.md) |
| Gate 3A | F0/F1/F2 simulator core frozen before formal validation | Implemented locally; pending GitHub publication | [`configs/dynamics.yaml`](../configs/dynamics.yaml), `src/openqfuel/dynamics.py` |
| Gate 3 | Simulator credibility and independent validation | In progress | [`configs/simulator_acceptance.yaml`](../configs/simulator_acceptance.yaml) |

The human research lead remains the final authority. No ML training or final
test opening is authorized until Gate 3 is accepted.

## 3. Literature and evidence work completed

The review protocol is versioned in
[`literature/review_protocol.md`](../literature/review_protocol.md). It defines
search strings, inclusion/exclusion criteria, evidence extraction fields,
quality domains, and the rule that marketing pages or uncited claims cannot
establish algorithmic performance.

The initial evidence matrix is in
[`literature/evidence_matrix.csv`](../literature/evidence_matrix.csv). It
contains the seed evidence map spanning:

- robust cislunar trajectory correction;
- classical ML surrogate guidance and reinforcement learning;
- QML regression, kernels, and quantum reinforcement learning;
- quantum optimization for space trajectories;
- human-spaceflight standards and crew constraints; and
- model and simulation credibility.

This is a prepared scoping-review foundation, not the final systematic-review
synthesis. Full paper retrieval, duplicate screening, quality scoring, and
claim-level extraction remain Gate 4 work.

## 4. Public-data method completed

All source records are in [`data/source_registry.csv`](../data/source_registry.csv).
The public-data policy is:

1. preserve raw downloads without silent edits;
2. record URL, source ID, retrieval date, local path, size, and SHA-256;
3. classify historical/reconstructed versus predicted ephemeris rows using the
   source creation time;
4. never call simulated or predicted rows raw telemetry; and
5. keep the raw provider files out of Git when redistribution terms are not
   established, while providing a reproducible download script.

The main flight reference is the NASA Artemis II CCSDS OEM collection (D001).
The audit found nine qualified OEM releases and one quarantined non-OEM product.
The latest April 10 release is the frozen reference for the coast-arc split.
The parser accepts the observed HTML-wrapped OEM prefix but does not interpret
the separate PROP_MAN/M50 product as a CCSDS OEM.

The Gate 3 simulator adds JPL DE440s (D029) for public Earth-relative Moon and
Sun positions. Its checksum is recorded in
[`data/public_source_checksums.csv`](../data/public_source_checksums.csv):

```text
c1c7feeab882263fc493a9d5a5b2ddd71b54826cdf65d8d17a76126b260a49f2
```

Download it with the existing fetcher after the D029 registry row is present:

```bash
python scripts/fetch_public_data.py --id D029
sha256sum data/raw/ephemeris/de440s.bsp
```

The JPL source is linked from the registry and is not copied into the Git
repository. The fixed UTC-to-TT offset of 69.184 s is scoped to the 2026
Artemis II interval; a future mission epoch must use a maintained time-scale
conversion.

## 5. Frozen numerical design

### 5.1 Coast-arc split

The exact UTC windows are in
[`data/processed/artemis2/validation_windows.csv`](../data/processed/artemis2/validation_windows.csv):

| Role | Number | Duration | Purpose |
|---|---:|---:|---|
| Calibration | 8 | 6 h each | Allowed force/nuisance calibration domain |
| Tuning | 4 | 6 h each | Integrator and model-option selection |
| Validation | 5 | 6 h each | Untouched simulator-credibility decision |

The validation arcs cover outbound-mid (V01), outbound-late (V02), lunar-flyby
(V03), return-mid (V04), and return-late (V05). They are disjoint and are
buffered from public burns and detected local state transitions.

### 5.2 Fidelity levels

The Gate 3 model is frozen in [`configs/dynamics.yaml`](../configs/dynamics.yaml):

| Level | Forces | Burn/mass model | Intended role |
|---|---|---|---|
| F0 | Earth point mass | Impulsive checks | Analytical and dimensional sanity tests |
| F1 | Earth, Moon, Sun point masses | Impulsive and fixed-direction finite burns with mass depletion | Dataset-generation development model |
| F2 | F1 plus Earth J2 | High-accuracy DOP853, finite burns, time-varying mass, crew checks | Evaluation model candidate |

State units are km, km/s, and optional kg in Earth-centered J2000/ICRF-
compatible axes. F2 uses DOP853 with `rtol=1e-11`, `atol=1e-13`, and a 300 s
maximum step. Numerical verification tightens tolerances by 100x and halves the
maximum step, exactly as required by the frozen acceptance configuration.

Implemented modules:

- [`src/openqfuel/ephemeris.py`](../src/openqfuel/ephemeris.py): DE440s access,
  checksum verification, UTC-to-TDB argument conversion, and geocentric Moon/Sun
  vectors;
- [`src/openqfuel/dynamics.py`](../src/openqfuel/dynamics.py): F0/F1/F2 forces,
  J2, impulses, finite burns, mass flow, and DOP853 propagation;
- [`src/openqfuel/propulsion.py`](../src/openqfuel/propulsion.py): public Orion
  thrust classes, ideal rocket equation, and constant-thrust propellant flow;
- [`src/openqfuel/constraints.py`](../src/openqfuel/constraints.py): protected
  crew intervals, blackout buffers, emergency reason codes, and conservative
  body-axis acceleration envelopes.

### 5.3 Frozen uncertainty and safety rules

The exact public 3-sigma inputs and declared sensitivities remain in
[`configs/uncertainty_model.yaml`](../configs/uncertainty_model.yaml). The six
primary strata are deterministic, navigation-only, execution-only, coupled
Gaussian replication, bounded coupled, and heavy-tail coupled sensitivity.

The hard study constraints include:

- total correction delta-v no more than 20 m/s including dispersions;
- lunar surface altitude at least 100 km including dispersion;
- entry-interface ellipse limits and correlations;
- burn timing, lunar-flyby exclusion, and crew protected periods;
- conservative body-axis acceleration envelopes;
- 10% nominal usable-propellant reserve as an explicit research assumption;
- 900 s planner and 1 s safety-filter wall-clock ceilings; and
- deterministic fallback with no unsafe-candidate execution.

The practical mission-stage effect threshold is at least 0.25 m/s and at least
10% relative delta-v improvement, with the paired 95% confidence lower bound
required to exceed the larger threshold. Classical simulation alone cannot be
described as quantum advantage.

## 6. Results completed before Gate 3 validation

### 6.1 Parser and OEM audit

The parser and audit outputs are tracked in
[`data/processed/artemis2/`](../data/processed/artemis2/):

- nine qualified OEM releases plus one quarantined product;
- 30 conservative local discontinuity intervals;
- 30 adjacent-release revision comparisons across 0, 6, 24, and 48 h horizons;
- 17 six-hour arc evaluations (8 calibration, 4 tuning, 5 validation); and
- 5 frozen validation windows.

The detected discontinuities are exclusion evidence, not maneuver labels. The
largest recorded local leave-one-out flag is 69.9876 km position and 321.3773
m/s velocity. It is retained as a reason to exclude difficult state-transition
regions from clean coast validation, not deleted as an outlier.

### 6.2 Earth-only analytical baseline

The baseline is deliberately weak: Earth point mass only, SciPy DOP853, and
the initial OEM state at each arc. It establishes why a cislunar simulator is
needed; it is not a mission simulator and not an ML comparison.

The exact machine-readable output is
[`two_body_baseline.csv`](../data/processed/artemis2/two_body_baseline.csv).
Selected validation results are:

| Arc | Phase | Position RMSE (km) | Velocity RMSE (m/s) | Interpretation |
|---|---|---:|---:|---|
| V01 | Outbound mid | 13.1457 | 1.5890 | Earth-only error already exceeds the non-lunar target |
| V02 | Outbound late | 348.9666 | 47.0406 | Strong cislunar/force-model mismatch |
| V03 | Lunar flyby | 3268.1621 | 453.6668 | Confirms Earth-only propagation cannot answer the mission question |
| V04 | Return mid | 21.7923 | 2.4999 | Return geometry remains outside the weak-model target |
| V05 | Return late | 8.4655 | 0.9741 | Smallest validation error, still only a weak baseline |

The full result table includes calibration and tuning arcs. No F2 result is
being reported here because the formal Gate 3 validation pipeline has not yet
been completed and independently checked.

### 6.3 Public-release revision audit

Adjacent public release revisions are an operational robustness signal. Median
position revision magnitudes are approximately 11.11 km at 0 h, 9.39 km at 6 h,
17.05 km at 24 h, and 13.74 km at 48 h in the current audit. The maximum
position revision is 147.52 km at the 6 h horizon. These numbers are not
measurement error, truth residuals, or mission covariance estimates.

### 6.4 Event geometry cross-check already possible

Using the public event registry and DE440s geometry, the OEM-derived closest
approach search places the lunar-flyby minimum at approximately 2026-04-06
23:00:46 UTC, about 46 s from the rounded public event time. This is a temporal
alignment sanity check, not state-vector truth. Full event qualification for
all required events remains in the Gate 3 validation script.

## 7. Verification completed

The local test suite currently reports:

```text
30 passed, 661 subtests passed
```

The tests cover OEM parsing, source-registry integrity, frozen windows, Gate 2
configuration values, F0 circular-orbit closure, impulse units, finite-burn
mass flow, rocket-equation edge cases, tightened numerical settings, crew
sleep/blackout rules, emergency override reason codes, and acceleration limits.

The project environment also passes compilation and dependency checks when run
through the locked `uv` environment. The project defines an optional
`figures` extra for the matplotlib-based figure generator.

## 8. Research maturity assessment

This work is currently at **computational research protocol / pre-ML simulator
credibility level**, not at flight-readiness, operational validation, or final
publication level.

| Dimension | Current level | What is still missing |
|---|---|---|
| Research question | Strongly scoped | None for Gate 2 scope; future mission scenario still conditional |
| Literature | Protocol and seed matrix | Full systematic search, screening, extraction, and synthesis |
| Public data | Audited and provenance-controlled | Additional source re-download verification in the target editor |
| Numerical model | F0/F1/F2 core implemented locally | Formal held-out metrics, independent GMAT comparison, event report |
| Uncertainty | Frozen public inputs and sensitivities | Propagated uncertainty dataset and sensitivity results |
| ML | Not started by design | Classical baselines, QML models, learning curves, seeds, locked test |
| Mission simulation | Not started | Safety filter, paired Monte Carlo, operational stress scenarios |
| Claims | No positive claim made | Claim audit, negative-result analysis, paper and archive |

The strongest defensible current conclusion is:

> An Earth-only analytical model is inadequate for the frozen cislunar
> validation problem, which justifies implementing and independently checking a
> public-data Earth–Moon–Sun simulator before any ML comparison.

It is not defensible to conclude that QML is better, that fuel savings are
flight-realistic, or that any method is ready for astronauts.

## 9. Procedural limitation disclosed

During local prototyping, a one-off F2 smoke computation was run on the frozen
windows before the Gate 3A code freeze was committed. No constants, force terms,
thresholds, windows, exclusions, or model parameters were fitted or changed
after seeing that smoke output, and the exploratory output was not retained as
research evidence. This weakens ideal blinding and is recorded in
[`docs/decision_log.md`](decision_log.md). The human lead must explicitly accept
or reject this handling at Gate 3.

## 10. Reproduce the completed descriptive outputs

From the repository root:

```bash
uv sync --extra figures
uv run python scripts/audit_artemis2_oem.py
uv run python scripts/evaluate_two_body_baseline.py
uv run python scripts/make_gate2_figures.py
```

The prebuilt visualization archive is
[`artifacts/artemis2_gate2_figures.zip`](../artifacts/artemis2_gate2_figures.zip).
It contains six PNG figures, a figure manifest, and a short interpretation
README. The archive is descriptive Gate 2 evidence only; it contains no F2 or
ML performance claim.

## 11. Files already on GitHub versus files still local

### Already on the remote repository

The remote `main` branch already contains the Gate 0–2 foundation, including
the protocol, literature-review seed, source registry, Artemis II event registry,
OEM audit outputs, weak baseline, frozen configurations, tests, Apache license,
and project metadata. A fresh clone does not need those files copied manually.

### Required from the unpushed local checkpoint

The following files are new or modified since the remote commit and must be
copied into the cloned repository or pushed from the local checkpoint:

```text
configs/dynamics.yaml
data/public_source_checksums.csv
data/source_registry.csv
docs/decision_log.md
docs/research_execution_map.md
pyproject.toml
uv.lock
src/openqfuel/constraints.py
src/openqfuel/dynamics.py
src/openqfuel/ephemeris.py
src/openqfuel/propulsion.py
tests/test_constraints.py
tests/test_dynamics.py
README.md
scripts/make_gate2_figures.py
docs/research_record_to_date.md
docs/next_phase_playbook.md
docs/ai_editor_handoff_manifest.md
artifacts/artemis2_gate2_figures.zip
```

The public DE440s kernel itself is intentionally not a Git file. Download it
with D029 and verify its checksum as described above.
