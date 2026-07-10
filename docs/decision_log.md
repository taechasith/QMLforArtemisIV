# Decision and Deviation Log

## Decision Gate 0: Research governance

Date: 2026-07-10  
Status: Accepted  
Decision authority: Human research lead  
Recommendation: Accept

Decision:

The assistant research partner will perform the research operations,
implementation, validation, documentation, and recommendations. The human
research lead will make the final accept, reject, or revise decision at
explicit gates.

Consequence:

Routine technical choices within the accepted protocol do not require repeated
permission. Scope changes, claim changes, post-freeze methodological changes,
and release decisions return to the human research lead.

## Decision Gate 1: Protocol scope

Date opened: 2026-07-10  
Date decided: 2026-07-10  
Status: Accepted  
Recommendation: Accept

Decision requested:

Accept the NASA-first scope using Artemis II flight ephemeris for calibration
and an Artemis IV-relevant Orion trajectory-correction scenario for the future
application.

Evidence package:

- research_protocol.md
- literature/review_protocol.md
- literature/evidence_matrix.csv
- data/source_registry.csv
- configs/constraints.yaml

Risk if accepted:

The work will be relevant to Artemis-class cislunar planning but cannot claim
to reconstruct proprietary Artemis IV or SpaceX HLS operations.

Consequence if rejected:

The project requires a new mission boundary and source audit before simulator
development.

Human decision: Accepted

Consequence:

The NASA-first mission scope is frozen. Gate 2 may define numeric values and
source-qualified assumptions but may not replace the Artemis II calibration
case, Artemis IV-relevant Orion application boundary, post-injection correction
segment, or ground-planning advisory use without a protocol deviation.

## Decision Gate 2: Data and numeric freeze

Date opened: 2026-07-10  
Date package completed: 2026-07-10  
Date decided: 2026-07-11  
Status: Accepted  
Recommendation: Accept

Decision requested:

Approve or reject the audited source set, exact modeling variables, data
splits, uncertainty strata, simulator acceptance tolerances, practical-effect
threshold, and compute budget before simulator calibration and model training.

Evidence package:

- docs/gate2_data_numeric_freeze.md
- data/source_registry.csv
- data/artemis2_event_registry.csv
- data/processed/artemis2/oem_inventory.csv
- data/processed/artemis2/oem_release_revisions.csv
- data/processed/artemis2/oem_detected_discontinuities.csv
- data/processed/artemis2/validation_windows.csv
- data/processed/artemis2/two_body_baseline.csv
- configs/constraints.yaml
- configs/uncertainty_model.yaml
- configs/crew_schedule.yaml
- configs/human_acceleration_limits.yaml
- configs/simulator_acceptance.yaml
- configs/compute_budget.yaml

Recommended decision:

Accept. The package prevents forecast-as-truth leakage, quarantines the
unqualified entry product, uses correction delta-v as the primary endpoint,
and freezes meaningful validation and QML comparison rules before any model
result is visible.

Human decision: Accepted

Consequence:

The public source set, variable roles, Artemis II simulator split, uncertainty
strata, human constraints, simulator tolerances, engineering effect threshold,
algorithm trigger, and compute ceiling are frozen. Any change affecting these
items requires a dated protocol deviation. Gate 3 simulator credibility work
is authorized; ML training remains prohibited until Gate 3 is accepted.

## Decision Gate 3: Simulator credibility

Date opened: 2026-07-11  
Status: In progress  
Recommendation: Pending implementation and held-out validation

Decision requested when complete:

Approve or reject the F0/F1/F2 simulator, numerical convergence evidence,
independent GMAT comparison, Artemis II held-out arc performance, mass and burn
model, and credibility report before synthetic dataset generation.

## Protocol deviations

No deviations recorded.
