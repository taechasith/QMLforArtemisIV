# Release Reproducibility Audit

Version: 0.2.0
Decision: D029-C / D030-C
Protocol: P001
Prepared: 2026-07-14
Accepted: 2026-07-14
Status: D030-C clean reproducibility correction PASS

## Scope

Historical D029-C status: Clean reproducibility audit STOP.

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

## D030-C Correction

D030-C corrected the byte-provenance blocker by adding explicit LF checkout
rules in `.gitattributes` for repository text files used as source, evidence,
configuration, documentation, and figure-registry provenance. The corrected
source commit was `90f45d356faa480998573cbc3b25b6e819b95ae8`.

The clean clone of that correction passed:

- `uv run --directory <clean_clone> --frozen pytest -q`: 252 passed and
  667 subtests passed.
- `uv run --directory <clean_clone> --frozen ruff check .`: passed.
- `uv run --directory <clean_clone> --frozen python -m compileall -q src scripts tests`: passed.

RFIG-049 records the D030-C PASS. This makes the release package eligible for
human claim/release review. It does not authorize release, tagging, archiving,
Gate 6, locked-data access, mission-loop execution, QML invention claims, or
quantum-advantage claims.
