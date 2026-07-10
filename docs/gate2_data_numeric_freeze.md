# Gate 2: Data and Numeric Freeze

Version: 0.2.0  
Prepared: 2026-07-10  
Decision status: Accepted by human research lead on 2026-07-11  
Recommendation: Accept

## Decision requested

Approve the public-source audit, exact variable roles, Artemis II calibration
split, uncertainty strata, simulator acceptance tests, human constraints,
engineering effect threshold, and compute ceiling before simulator fitting or
ML training begins.

Accepting Gate 2 authorizes implementation and validation of the simulator. It
does not authorize opening an ML final test, claiming quantum advantage, or
claiming flight readiness.

## The most important methodological decisions

1. Correction delta-v, not kilograms of propellant, is the primary mission
   endpoint. Public mission records constrain delta-v directly, while a complete
   flight-specific Isp and mixture-state model is not public. Propellant mass is
   reported as a transparent rocket-equation sensitivity.
2. NASA's Artemis II OEM archive is an operational ephemeris product, not raw
   telemetry. States at or before each file's `CREATION_DATE` are classified by
   this study as historical/reconstructed; later states are classified as
   predictions. This is an audit convention, not a NASA label.
3. Only the latest-release states through 2026-04-10 03:22:19 UTC are eligible
   as retrospective validation references. Later states may be used only for
   forecast-consistency analysis.
4. The one-second M50/PROP_MAN entry product is quarantined. Its epoch,
   reference-frame realization, and eighth column are not used until an
   authoritative definition is found.
5. Five held-out validation arcs are frozen before force-model fitting. The
   study stops before ML training if the mission simulator fails any required
   acceptance test.

## Public-source audit

The immutable download manifest contains six locally preserved primary files:

| ID | Source | Size | SHA-256 status | Use |
|---|---|---:|---|---|
| D001 | Artemis II OEM archive | 1,584,030 bytes | Recorded | Flight-ephemeris calibration and release-revision experiment |
| D003 | January 2026 public timeline | 248,301 bytes | Recorded | Planned events and crew schedule comparison |
| D004 | Orion Reference Guide | 62,224,406 bytes | Recorded | Public mass, propellant, thrust, and crew bounds |
| D006 | NASA Artemis II burn-placement paper | 4,755,585 bytes | Recorded | Objective, EI corridor, timing, uncertainty, and engineering benchmark |
| D010 | NASA-STD-3001 Vol. 2 Rev. E | 5,796,486 bytes | Recorded | Human acceleration envelopes |
| D011 | NASA-STD-7009B | 1,417,365 bytes | Recorded | Model and simulation credibility process |

All URLs, retrieval dates, local paths, limitations, and source roles are in
`data/source_registry.csv`; file hashes are produced by the downloader in the
raw-source manifest.

### OEM archive result

- 9 CCSDS OEM 2.0 releases parsed successfully.
- 26,309 state rows were audited across those releases.
- All nine use object EM2, Earth center, EME2000, UTC, kilometres, and
  kilometres per second.
- Median cadence is 240 seconds, with denser and irregular samples around
  state transitions and mission events.
- One file contains 108 wrapper lines before its valid OEM message; the parser
  locates the CCSDS header rather than assuming line 1.
- One separate PROP_MAN 11.0/M50 product contains 820 one-second rows and is
  quarantined.

Thirty conservative discontinuity intervals were flagged by leave-one-out
Hermite inconsistency. These flags are used only to exclude clean coast arcs.
They are not described as maneuvers unless an independent public event source
supports that label.

### Operational release revisions

Adjacent OEM releases were compared at 0, 6, 24, and 48 hours from each newer
release's creation time. These are solution revisions, not errors against
truth.

| Horizon | Comparisons | Median position revision | Position 95th percentile | Median velocity revision | Velocity 95th percentile |
|---:|---:|---:|---:|---:|---:|
| 0 h | 8 | 11.115 km | 104.945 km | 0.314 m/s | 1.288 m/s |
| 6 h | 8 | 9.395 km | 104.694 km | 0.238 m/s | 1.618 m/s |
| 24 h | 7 | 17.048 km | 95.460 km | 0.129 m/s | 0.386 m/s |
| 48 h | 7 | 13.739 km | 75.863 km | 0.066 m/s | 0.309 m/s |

This supports a separate operational-replay question: whether a planner remains
robust as the public flight solution changes during a mission.

## Planned-versus-flown event audit

The event registry separates the January public plan from flown public mission
updates.

| Event | Public mission outcome | Quantitative value used |
|---|---|---:|
| TLI | Executed 2026-04-02 23:49 UTC for 350 s | Pre-burn public delta-v 388.3152 m/s is a planning cross-check only |
| OTC1 | Cancelled | No burn and no invented counterfactual delta-v |
| OTC2 | Cancelled | No burn and no invented counterfactual delta-v |
| OTC3 | Executed 2026-04-06 03:03 UTC for 17.5 s | Delta-v not public |
| Lunar closest approach | Executed about 2026-04-06 23:00 UTC | About 4,067 miles altitude, rounded event check |
| RTC1 | Executed for 15 s | 0.48768 m/s, converted from rounded 1.6 ft/s |
| RTC2 | Executed for 9 s | 1.61544 m/s, converted from rounded 5.3 ft/s |
| RTC3 | Executed for 8 s | 1.28016 m/s, converted from rounded 4.2 ft/s |

The known RTC1-to-RTC3 sum is 3.38328 m/s. Because NASA did not publish OTC3
delta-v, this is a lower bound, not the mission's total correction delta-v.

## Vehicle and human-data qualification

The Orion reference values frozen for sensitivity modeling are 58,000 lb at
TLI, 57,000 lb post-TLI, 19,000 lb usable propellant, and 34,400 lb service
module mass. Public thrust values are 6,000 lbf for the main engine, eight
110-lbf auxiliary engines, and twenty-four 50-lbf RCS thrusters.

Two inconsistencies are explicit:

- The reference guide shows a 58,000-lb mass value under an Artemis II
  total-change-in-velocity heading. It is excluded rather than silently
  reinterpreted.
- A flown-mission update says the main engine provides up to 6,700 lbf, while
  the reference guide and another NASA update say 6,000 lbf. The model uses
  6,000 lbf nominally and 6,700 lbf only as a sensitivity bound.

Protected sleep windows are encoded from public mission schedules with a
30-minute planning buffer. Routine corrections cannot be placed in those
windows; a documented emergency override is allowed. These schedules are
operational records, not astronaut health telemetry.

NASA-STD-3001 Rev. E does not provide one universal maximum g value. The model
therefore checks acceleration by crew-body axis, duration, posture, and
conditioning. The conservative deconditioned envelope is used. The standard's
jerk limits for extraterrestrial surface vehicles are not applied to Orion.

## Frozen simulator split

The retrospective reference is the latest April 10 CCSDS OEM, restricted to
epochs no later than its creation time. Windows are mutually disjoint and at
least 30 minutes from a public burn or a conservatively detected state
transition.

| Role | Count | Duration each | Purpose |
|---|---:|---:|---|
| Calibration | 8 | 6 h | Fit allowed public force and nuisance parameters |
| Tuning | 4 | 6 h | Select integrator and model options without touching validation |
| Validation | 5 | 6 h | Final simulator credibility decision |

The five validation arcs cover outbound-mid, outbound-late, lunar flyby,
return-mid, and return-late phases. Their exact UTC boundaries are fixed in
`data/processed/artemis2/validation_windows.csv`.

### Weak baseline

An Earth point-mass model was run before fitting the mission simulator. It is a
deliberately weak analytical check, not the proposed simulator.

| Arc | Phase | Position RMSE | Velocity RMSE |
|---|---|---:|---:|
| V01 | Outbound mid | 13.146 km | 1.589 m/s |
| V02 | Outbound late | 348.967 km | 47.041 m/s |
| V03 | Lunar flyby | 3,268.162 km | 453.667 m/s |
| V04 | Return mid | 21.792 km | 2.500 m/s |
| V05 | Return late | 8.466 km | 0.974 m/s |

The lunar failure confirms that a two-body benchmark cannot answer the mission
question and that the held-out set tests genuinely cislunar dynamics.

## Frozen simulator acceptance

The complete machine-readable tests are in
`configs/simulator_acceptance.yaml`. The key gates are:

- parser/interpolation p95 no worse than 5 m position and 5 mm/s velocity on
  qualified points;
- numerical convergence no worse than 10 m and 1 mm/s at six-hour endpoints;
- independent GMAT same-force-model agreement no worse than 100 m and
  0.01 m/s at every endpoint;
- at least 80 percent error reduction against the Earth-only baseline on every
  validation arc;
- on non-lunar validation arcs, position RMSE at most 10 km and velocity RMSE
  at most 1 m/s, with 20 km and 2 m/s endpoint ceilings;
- on the lunar validation arc, position RMSE at most 25 km and velocity RMSE at
  most 2 m/s, with 50 km and 5 m/s endpoint ceilings.

Every requirement must pass. Failure stops the project before ML training and
is itself published as a simulation-validation result.

## Frozen uncertainty experiment

The public NASA study supplies 3-sigma initial-state, navigation, DSN, IMU,
star-tracker, thruster, and process-noise values. The exact table is transcribed
with original and SI units in `configs/uncertainty_model.yaml`.

Six primary strata separate deterministic, navigation-only, execution-only,
coupled Gaussian-replication, bounded, and heavy-tail sensitivity cases.
Gaussian and Student-t choices are labeled modeling choices rather than
mission-owned distributions. Stress cases add communication holds, burn delay,
mass error, and propulsion-model error. A two-hour communications scenario is
motivated by the public RTC2 mission update but is not treated as a probability
distribution.

## Frozen effect and safety rule

A QML result can advance to a mission claim only when:

1. its predictive error is within 5 percent of the strongest tuned classical
   model and any special regime is stable;
2. the paired 95 percent confidence-interval lower bound for mission delta-v
   improvement exceeds the larger of 0.25 m/s or 10 percent of the strongest
   classical mean;
3. every hard constraint passes and violation probability is non-inferior
   within 0.001 absolute;
4. latency, encoding, shots, mitigation, communication, and classical
   post-processing costs are included.

The 0.25 m/s and 10 percent rule is intentionally below the approximately
1.5 m/s improvement reported as possible for the NASA DSN study, yet large
enough to reject cosmetic gains. If the residual-QML trigger fails, no new
algorithm is created.

## Frozen compute ceiling

The package caps the study at 10,000 CPU core-hours, 1,000 GPU-hours, 50 million
QPU shots, 250 GB persistent storage, and 30 wall-clock days. It fixes 30 tuning
trials per family, 20 development seeds, 30 finalist seeds, required 4/6/8
qubit experiments, and 2,000 to 20,000 paired mission runs per uncertainty
stratum. Exceeding a ceiling requires a documented protocol deviation before
final-test inspection.

## Known limitations accepted at this gate

- The OEM is a public operational trajectory solution, not raw tracking or
  spacecraft telemetry.
- A complete mission-owned force, navigation, covariance, propulsion, and
  reserve model is unavailable.
- The public sleep schedule is not a fatigue or biomedical model.
- The Artemis IV scenario will be a source-qualified reference scenario, not a
  reconstruction of proprietary future operations.
- Space-weather data can support environmental stress labels but not absorbed
  astronaut dose claims.
- Passing this research protocol cannot establish flight certification or
  operational safety.

These limitations narrow the claim; they do not invalidate a simulation-based,
open benchmark.

## Consequence of the decision

Gate 2 was accepted on 2026-07-11. All numeric choices above are frozen and
work proceeds to Gate 3 simulator implementation and credibility testing.
