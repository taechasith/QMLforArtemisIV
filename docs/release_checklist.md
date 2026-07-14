# Release Checklist

Version: 0.1.0
Decision: D030-C
Prepared: 2026-07-14
Status: Eligible for human claim/release review

## Current Release Status

Release is not authorized. D030-C corrected the D029-C byte-provenance blocker
and the corrected clean clone passed pytest, ruff, and compileall. Release is
eligible for human claim/release review, but still requires explicit human
acceptance. Release is eligible for human claim/release review after D030-C.
D029-C remains recorded as: Blocked by clean reproducibility audit STOP.

## Required Before Release Decision

- [x] Open and complete a prospective line-ending and byte-provenance correction.
- [x] Rerun clean clone `pytest`, `ruff`, and `compileall`.
- [x] Confirm figure registry generator hashes match in a clean clone.
- [x] Confirm Gate 4 frozen artifact hashes match in a clean clone.
- [x] Confirm no calibration, final-test, mission-loop, or Gate 6 data are read.
- [ ] Complete final claim review against D026-C/D027-C boundaries.
- [ ] Human research lead accepts or rejects release.

## Prohibited Until Complete

- No public release.
- No tagged archive.
- No DOI.
- No model release.
- No Gate 6 run.
- No QML invention or quantum-advantage claim.
