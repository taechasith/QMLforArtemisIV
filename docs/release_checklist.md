# Release Checklist

Version: 0.1.0
Decision: D029-C
Prepared: 2026-07-14
Status: Blocked by clean reproducibility audit STOP

## Current Release Status

Release is not authorized. D029-C found clean-clone reproducibility failures.

## Required Before Release Decision

- [ ] Open and complete a prospective line-ending and byte-provenance correction.
- [ ] Rerun clean clone `pytest`, `ruff`, and `compileall`.
- [ ] Confirm figure registry generator hashes match in a clean clone.
- [ ] Confirm Gate 4 frozen artifact hashes match in a clean clone.
- [ ] Confirm no calibration, final-test, mission-loop, or Gate 6 data are read.
- [ ] Complete final claim review against D026-C/D027-C boundaries.
- [ ] Human research lead accepts or rejects release.

## Prohibited Until Complete

- No public release.
- No tagged archive.
- No DOI.
- No model release.
- No Gate 6 run.
- No QML invention or quantum-advantage claim.
