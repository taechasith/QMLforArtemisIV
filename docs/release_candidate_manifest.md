# D032-C Release-Candidate Manifest

Version: 0.1.0
Decision: D032-C
Protocol: P001
Prepared: 2026-07-14
Status: Release-candidate manifest ready; release unauthorized

## Scope

D032-C records the candidate base commit, release-candidate file manifest, and
post-acceptance actions. It does not publish the repository, create a tag,
create an archive, mint a DOI, update citation metadata, open locked data, run
Gate 6, or authorize any new scientific claim.

## Candidate Base

- Candidate base commit:
  `64296def4d6e1b86e13fee8d839e0445378d0ae1`
- Candidate label: P001 negative-QML benchmark release candidate.
- Version candidate: `0.3.0`.
- Current citation metadata version: `0.2.0`.

## Release-Candidate Contents

The manifest hashes the README, protocol, claim-reviewed manuscript, release
cards, final claim/release review, reproducibility record, figure registry, and
D031-C decision evidence. The generated file list is
`data/processed/reporting/post_gate5_d032_release_candidate_files.csv`.

## Required After Human Acceptance

- Create a release tag from the accepted release commit.
- Prepare archive/DOI metadata only after tag acceptance.
- Update `CITATION.cff` release metadata only after release acceptance.
- Preserve the D031-C claim boundary in release notes.

## Boundary

D032-C authorizes no release, tag, archive, DOI, `CITATION.cff` update,
locked-data access, mission-loop execution, Gate 6 run, model fitting, QML
invention claim, or quantum-advantage claim. RFIG-051 records this state.
