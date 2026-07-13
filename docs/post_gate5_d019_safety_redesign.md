# D019-C Safety-Objective Redesign Discussion

Version: 0.1.0
Decision: D019-C
Protocol: P001
Prepared: 2026-07-14
Accepted: 2026-07-14
Status: Discussion-only opened; no experiment authorized

## Decision

D019-C opens a future-only safety-objective redesign discussion after D018-C
closed D017-C as `NO_ADVANCE`.

This is not a retry and not a model-selection correction. It does not replace
the D017 frozen selector, does not change the CSAFE result, and does not
authorize implementation, development fitting, calibration, final-test,
hardware/GPU, mission-loop, QML invention, quantum-advantage, Gate 5
reinterpretation, or Gate 6 work.

## Evidence Being Discussed

D017-C selected `class_weighted_tree` under the frozen mean-Brier objective.
That model had mean Brier 0.1311 but mean recall only 0.0139. D018-C therefore
classified CSAFE as failed safety utility.

The `calibrated_logistic` head had worse mean Brier, 0.1422, but much higher
mean recall, 0.8043. This is useful only as a future signal. Selecting it now
would be post-outcome rescue because the D017 objective had already been
frozen.

## Future Protocol Requirements

Any executable successor must first freeze a safety objective that treats
missed unsafe cases as primary evidence. At minimum, a future D020 proposal
must prospectively define:

- the primary recall or false-negative-cost objective;
- secondary Brier/calibration diagnostics;
- the threshold-selection rule using only authorized development training
  folds;
- matched classical and QML controls;
- minimum safety-utility criteria before calibration, final-test,
  mission-loop, hardware/GPU, or Gate 6 authority can be requested;
- compute preflight and stop rules.

## Claim Boundary

RFIG-038 records the boundary. D019-C is future-only discussion evidence. It
does not improve, rescue, or reinterpret the D017/CSAFE result.
