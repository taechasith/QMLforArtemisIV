# Gate 3 simulator credibility validation

Status: `failed_repair_required`  
Generated: 2026-07-11  
Decision authority: Human research lead

## Technical summary

Gate 3 failed its frozen acceptance criteria and is in `failed_repair_required` status. ML and QML work remains prohibited.

The run evaluated 67 numeric acceptance checks: 10 failed and 1 required checks are pending or not eligible. The public OEM is an operational trajectory solution, not raw telemetry, and all conclusions are limited to the frozen public-data model.

## Frozen criteria produced a gate decision

| Category | Passed | Failed | Pending/not eligible |
|---|---|---|---|
| parser_and_interpolation | 2 | 0 | 0 |
| numerical_convergence | 10 | 0 | 0 |
| flight_ephemeris_validation | 20 | 0 | 0 |
| weak_baseline_improvement | 20 | 0 | 0 |
| event_cross_checks | 5 | 0 | 1 |
| independent_gmat | 0 | 10 | 0 |

Every failed criterion is retained in `data/processed/simulator/acceptance_summary.csv`; thresholds, windows, exclusions, and source roles were not changed after viewing results.

## Interpolation met its parser-quality thresholds

Leave-one-out cubic Hermite interpolation used 2369 eligible clean-coast points. Segments touching any frozen 30-minute discontinuity buffer were excluded.

| Metric | Observed | Upper bound | Status |
|---|---|---|---|
| Position p95 (km) | 0.000220474363 | 0.005000000000 | pass |
| Velocity p95 (m/s) | 0.000013083564 | 0.005000000000 | pass |

## Numerical convergence was checked on every frozen window

Nominal F2 propagation was compared with tolerances tightened by 100x and maximum step halved. The table reports six-hour endpoint differences; full endpoint states and solver settings are in the CSV.

| Window | Position difference (km) | Velocity difference (m/s) | Status |
|---|---|---|---|
| V01 | 0.000000001094 | 0.000000000023 | pass |
| V02 | 0.000000029641 | 0.000000015136 | pass |
| V03 | 0.000011128549 | 0.000001105634 | pass |
| V04 | 0.000000003543 | 0.000000000055 | pass |
| V05 | 0.000000002378 | 0.000000000198 | pass |

## Flight-ephemeris validation exposed the F2 result

Each window starts from its OEM state and is compared at every public reference epoch. The 80% weak-baseline improvement rule is applied conservatively to all four error metrics.

| Window | Position RMSE (km) | Velocity RMSE (m/s) | Overall |
|---|---|---|---|
| V01 | 0.001952941411 | 0.000230488149 | pass |
| V02 | 0.001971668943 | 0.000235902254 | pass |
| V03 | 0.033012822821 | 0.006199496894 | pass |
| V04 | 0.001960330658 | 0.000231514343 | pass |
| V05 | 0.001963869243 | 0.000231917681 | pass |

This is a descriptive validation against a public operational ephemeris. It does not establish flight truth, causal model adequacy, or operational certification.

## Event checks preserve source eligibility

Burn timing uses the nearest eligible OEM epoch adjacent to a non-nominal cadence interval. Lunar closest approach is the OEM-to-DE440s distance minimum inside V03. Rounded public event times are used only for temporal alignment.

| Event | Estimated UTC | Error (s) | Status |
|---|---|---|---|
| TLI | 2026-04-02T23:48:30.934000Z | 29.066 | pass |
| OTC3 | 2026-04-06T03:03:17.084000Z | 17.084 | pass |
| lunar closest approach | 2026-04-06T23:00:46.159111Z | 46.159 | pass |
| RTC1 | 2026-04-08T00:03:17.084000Z | 17.084 | pass |
| RTC2 | 2026-04-10T02:53:28.122000Z | 28.122 | pass |
| RTC3 | not eligible | n/a | not_eligible |

## GMAT provides the independent same-force comparison

NASA GMAT R2026a console completed the generated same-force script.

The generated `scripts/gmat/gate3_same_force_model.script` uses DE440s through SPICE, Earth point mass and J2, Luna and Sun point masses, no drag or SRP, and a tight RungeKutta89 propagation. Executable and archive hashes are retained in the comparison CSV.

| Window | Position difference (km) | Velocity difference (m/s) | Status |
|---|---|---|---|
| V01 | 11.276084294437 | 0.986380952903 | fail |
| V02 | 2.189901878445 | 0.197074914230 | fail |
| V03 | 1.698661383349 | 0.141042055373 | fail |
| V04 | 5.167709057523 | 0.497374536822 | fail |
| V05 | 14.093528854239 | 1.401584593293 | fail |

## Scope, data, and metric definitions

- Reference release: `Artemis_II_OEM_2026_04_10_Post-ICPS-Sep-to-EI.asc`.
- Eligible reference cutoff: `2026-04-10T03:22:19Z`.
- Validation cohort: V01-V05, five frozen six-hour coast windows in UTC.
- Position errors: Euclidean EME2000/EarthMJ2000Eq differences in kilometres.
- Velocity errors: Euclidean inertial differences converted to metres per second.
- Weak baseline: tracked Earth-only DOP853 results in `two_body_baseline.csv`.
- No calibration, threshold changes, window changes, or post-result exclusions were performed.

Exact audit tables are used instead of charts because each validation family has only five frozen windows and the gate decision depends on per-window thresholds, not a visual trend.

## Limitations and robustness boundaries

- The OEM is not raw tracking or spacecraft telemetry.
- The fixed 2026 UTC-to-TT conversion omits a sub-2 ms periodic TDB term.
- F2 omits solar-radiation pressure, attitude, and mission-owned force and navigation details.
- RTC3 cannot be checked against eligible historical/reconstructed rows when it occurs after the OEM creation cutoff.
- Passing numerical or cross-tool checks would not establish flight readiness.

## Required next step

Publish and review the failed criteria. Any repair requires a dated protocol deviation; do not change thresholds, windows, splits, or exclusions, and do not begin ML or QML training.

Decision requested from the human research lead: reject Gate 3 as currently implemented or authorize a documented simulator-repair protocol deviation.
