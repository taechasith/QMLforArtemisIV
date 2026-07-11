# AI code-editor handoff manifest

Prepared: 2026-07-11  
Repository: [QMLforArtemisIV](https://github.com/taechasith/QMLforArtemisIV)  
Local unpushed Gate 3A checkpoint: `432385a` (`Freeze Gate 3 simulator core before formal validation`)  
Local handoff commits: `432385a..7775c9d`

This manifest identifies what is already on GitHub, what must be copied into a
fresh clone, what raw public data must be downloaded locally, and what the next
phase must create.

## A. Already on the remote clone

Do not manually copy these files from the handoff package. They are already on
the remote `main` branch:

```text
.gitignore
CITATION.cff
CONTRIBUTING.md
LICENSE
configs/compute_budget.yaml
configs/constraints.yaml
configs/crew_schedule.yaml
configs/human_acceleration_limits.yaml
configs/simulator_acceptance.yaml
configs/uncertainty_model.yaml
data/artemis2_event_registry.csv
data/processed/artemis2/oem_detected_discontinuities.csv
data/processed/artemis2/oem_inventory.csv
data/processed/artemis2/oem_release_revisions.csv
data/processed/artemis2/two_body_baseline.csv
data/processed/artemis2/validation_windows.csv
data/processed/.gitkeep
data/raw/.gitkeep
docs/gate2_data_numeric_freeze.md
literature/evidence_matrix.csv
literature/review_protocol.md
research_protocol.md
scripts/audit_artemis2_oem.py
scripts/evaluate_two_body_baseline.py
scripts/extract_artemis2_oem.py
scripts/fetch_public_data.py
src/openqfuel/__init__.py
src/openqfuel/oem.py
tests/test_extract_oem.py
tests/test_gate2_config.py
tests/test_oem.py
tests/test_repository.py
```

The remote copies of `README.md`, `data/source_registry.csv`,
`docs/decision_log.md`, `docs/research_execution_map.md`, `pyproject.toml`, and
`uv.lock` are older Gate 2 versions. Replace them with the newer copies listed
below.

## B. Copy these files into the clone

These files are new or modified in the unpushed Gate 3A checkpoint:

```text
README.md
configs/dynamics.yaml
data/public_source_checksums.csv
data/source_registry.csv
docs/ai_editor_handoff_manifest.md
docs/decision_log.md
docs/next_phase_playbook.md
docs/research_execution_map.md
docs/research_record_to_date.md
pyproject.toml
scripts/make_gate2_figures.py
src/openqfuel/constraints.py
src/openqfuel/dynamics.py
src/openqfuel/ephemeris.py
src/openqfuel/propulsion.py
tests/test_constraints.py
tests/test_dynamics.py
uv.lock
artifacts/artemis2_gate2_figures.zip
```

Preserve the relative paths. Do not copy `.git/`, `.venv/`, `__pycache__/`, or
`tmp/`.

The next sections contain the download, verification, and push instructions.

## C. Transfer without manual copying when the original worktree is available

The full Gate 3A implementation is a local Git commit. The safest transfer is:

```bash
git format-patch origin/main..432385a --stdout > gate3a.patch
# In the cloned repository:
git am gate3a.patch
```

If only this handoff package is available, copy the paths in Section B and
commit them together as one phase. Do not duplicate files under alternate names.

## D. Public raw data to download locally (not to commit)

Raw provider files are intentionally excluded from Git. The clone needs these
only to execute the scripts:

| Source | Command | Role |
|---|---|---|
| D001 Artemis II OEM archive | `uv run python scripts/fetch_public_data.py --id D001` then `uv run python scripts/extract_artemis2_oem.py` | OEM audit, baseline, and held-out validation |
| D029 JPL DE440s | `uv run python scripts/fetch_public_data.py --id D029` | Moon/Sun positions for F1/F2 |

Verify D029 exactly:

```bash
sha256sum data/raw/ephemeris/de440s.bsp
# c1c7feeab882263fc493a9d5a5b2ddd71b54826cdf65d8d17a76126b260a49f2
```

The D001 archive is unpacked into `data/raw/artemis2/`; nested manifests and
source manifests are generated locally. Do not use `git add -f` on raw files
unless a later license review explicitly authorizes redistribution.

The independent GMAT R2026a executable/data is a separate public dependency
(D028). It is not included here. Download it from the official release page
when Phase 3B is run and record version, platform, archive checksum, and
executable path in the GMAT comparison output.

## E. Visualization archive

[`artifacts/artemis2_gate2_figures.zip`](../artifacts/artemis2_gate2_figures.zip)
contains:

```text
README.md
earth_only_position_rmse.png
earth_only_velocity_rmse.png
oem_position_revisions.png
oem_velocity_revisions.png
oem_discontinuity_flags.png
frozen_validation_split.png
figure_manifest.csv
```

These are Gate 2 descriptive figures generated from tracked derived CSVs. They
contain no F2, ML, QML, or astronaut-operational results. Regenerate them with:

```bash
uv sync --extra figures
uv run python scripts/make_gate2_figures.py
```

The generator script is included so the archive is reproducible rather than a
hand-edited image bundle.

## F. First commands in the AI code editor

After copying the files and downloading raw data:

```bash
uv sync --extra figures
uv run python scripts/audit_artemis2_oem.py
uv run python scripts/evaluate_two_body_baseline.py
uv run python scripts/make_gate2_figures.py
uv run python -m pytest -q
uv run python -m compileall -q src scripts tests
uv pip check
git diff --check
git status --short
```

Expected test result after Gate 3A files are present:

```text
30 passed, 661 subtests passed
```

Then push the copied Gate 3A checkpoint before implementing formal validation:

```bash
git add -A
git commit -m "Freeze Gate 3 simulator core before formal validation"
git push origin main
```

Record the resulting GitHub commit URL in `docs/decision_log.md`. Only after
that push should the AI editor implement `scripts/validate_simulator.py` and
the Gate 3B report.

## G. Files that the next phase must create

These do not exist yet and should be added in this order:

```text
src/openqfuel/validation.py
tests/test_validation.py
scripts/validate_simulator.py
data/processed/simulator/interpolation_validation.csv
data/processed/simulator/numerical_convergence.csv
data/processed/simulator/f2_flight_validation.csv
data/processed/simulator/event_cross_checks.csv
data/processed/simulator/acceptance_summary.csv
docs/gate3_simulator_credibility.md
```

The complete requirements, thresholds, stop rules, GMAT comparison protocol,
and exact push command are in
[`docs/next_phase_playbook.md`](next_phase_playbook.md), section 4.

## H. Do not download or create yet

Do not begin any of the following until Gate 3 is accepted:

- ML training datasets;
- final-test feature files or labels;
- QML circuit results;
- algorithm-invention variants;
- mission Monte Carlo results;
- astronaut operational claims; or
- a paper conclusion that one model is best.

The current evidence supports only a weak-baseline diagnosis and a frozen
simulator implementation checkpoint.
