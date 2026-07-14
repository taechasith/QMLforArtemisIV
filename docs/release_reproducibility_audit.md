# D029-C Release Reproducibility Audit

Version: 0.1.0
Decision: D029-C
Protocol: P001
Prepared: 2026-07-14
Accepted: 2026-07-14
Status: Clean reproducibility audit STOP

## Scope

D029-C audited a clean local clone of D028-C commit
`0521fee3343b7484a5b70cf3a8dea250b88d0e51`. This is a release
infrastructure audit only. It is unrelated to the public-source identifier
D029 for JPL DE440s.

## Audit Result

The clean clone is not release-ready.

- `uv run --directory <clean_clone> --frozen pytest -q`: failed with
  3 failed, 246 passed, and 667 subtests passed.
- `uv run --directory <clean_clone> --frozen ruff check .`: passed.
- `uv run --directory <clean_clone> --frozen python -m compileall -q src scripts tests`: passed.

## Failure Interpretation

The failures are byte-provenance and line-ending portability failures:

- `scenario_manifest.csv` did not match the frozen Gate 4 checksum record in
  the clean clone.
- Gate 5 preflight failed closed because the Gate 4 frozen artifact hash did
  not match.
- RFIG-030 generator hash did not match the registry hash in the clean clone.

This does not change the scientific result. It blocks release readiness until
a prospective correction freezes checkout byte behavior and reruns the clean
audit.

## Boundary

D029-C authorizes no release, correction, Gate 6 run, locked-data access,
mission-loop execution, model fitting, QML invention claim, quantum-advantage
claim, or Gate 5 reinterpretation. RFIG-048 records the STOP.
