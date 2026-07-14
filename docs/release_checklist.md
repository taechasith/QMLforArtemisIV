# Release Checklist

Version: 0.2.0
Decision: D033-C
Prepared: 2026-07-14
Status: Release package accepted and published under strict D031-C negative-claim boundary

## Current Release Status

Human research lead accepted the release package with the strict D031-C
negative-claim boundary. D030-C corrected the D029-C byte-provenance blocker
and the corrected clean clone passed pytest, ruff, and compileall. D031-C final
claim review is complete, D032-C hashes the candidate decision packet, and
D033-C authorizes the `v0.3.0` source tag, source archive, citation update,
and publication of the non-draft GitHub Release at
https://github.com/taechasith/QMLforArtemisIV/releases/tag/v0.3.0, only for
the development-only negative benchmark claim. Publication changed no
scientific evidence.

Historical release state remains preserved for audit continuity: D029-C was
Blocked by clean reproducibility audit STOP; Release is eligible for human
claim/release review after D030-C; D031-C final claim review is complete; and
D032-C release-candidate manifest is ready.

Audit phrase: Release is eligible for human claim/release review.

## Required Before Release Decision

- [x] Open and complete a prospective line-ending and byte-provenance correction.
- [x] Rerun clean clone `pytest`, `ruff`, and `compileall`.
- [x] Confirm figure registry generator hashes match in a clean clone.
- [x] Confirm Gate 4 frozen artifact hashes match in a clean clone.
- [x] Confirm no calibration, final-test, mission-loop, or Gate 6 data are read.
- [x] Complete final claim review against D026-C/D027-C boundaries.
- [x] Prepare release-candidate manifest without tag/archive/DOI.
- [x] Human research lead accepts or rejects release.
- [x] Update `CITATION.cff` to accepted version `0.3.0`.
- [x] Prepare accepted release notes under the D031-C boundary.

## Still Prohibited

- No DOI.
- No model release.
- No Gate 6 run.
- No QML invention or quantum-advantage claim.
