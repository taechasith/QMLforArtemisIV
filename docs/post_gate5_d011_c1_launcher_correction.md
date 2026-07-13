# D011-C1 Launcher Correction Freeze

Version: 0.1.0
Decision: D011-C1
Protocol: P001
Prepared: 2026-07-14
Accepted: 2026-07-14
Status: Terminal authority-hash technical STOP; corrected fold-shaped workload not reached

## Decision

The human research lead accepted D011-C1 to correct only the direct-file
launcher/import failure that stopped D011 before governed execution. D011-C1
does not change the D011 scientific workload, rows, folds, controls, models,
thresholds, seeds, resource ceilings, or reporting boundaries.

The machine-readable authority is
`configs/post_gate5_d011_c1_launcher_correction.yaml`.

## Correction

D011 stopped because `python scripts/run_post_gate5_fold_shape_preflight.py`
could not resolve `scripts.run_post_gate5_compute_preflight` during import.
That happened before the D011 authority check, source-hash verification,
synthetic arrays, resource admission, development rows, calibration rows,
final-test rows, hardware/GPU work, or Gate 6.

D011-C1 permits the shared synthetic-preflight helper functions to be imported
from the package namespace instead of from another script file. The correction
requires a clean-source import-only smoke test before the one allowed unchanged
preflight attempt.

## Frozen Attempt

The preflight remains the D011 largest-fold synthetic benchmark:

- 1,024 synthetic training rows and 9,750 synthetic validation rows.
- Eight qubits, two data-reupload layers, both projected heads, A02, and every
  matched classical control.
- 1,220 worst-fold bundle units with a 25% margin.
- The same CPU, wall-clock, artifact, process-memory, free-disk, and zero-GPU
  ceilings.

The D011 terminal STOP evidence remains immutable. D011-C1 writes its own
evidence file at
`data/processed/reporting/post_gate5_d011_c1_fold_shape_preflight.json`.

## Consequence

## Outcome

The import-only smoke test passed from clean source. The formal preflight
command then stopped during D011-C1 authority verification because the pinned
raw Git-blob hash for `configs/post_gate5_development_execution.yaml` did not
match the actual raw Git blob. The mismatch came from freeze metadata, not from
the scientific workload.

Synthetic arrays, source-hash verification of the workload, resource admission,
development rows, calibration rows, final-test rows, hardware/GPU work, and
Gate 6 were not reached. D011-C1 is therefore a terminal technical `STOP`, not
QML evidence and not a laptop-capacity result.

P001-FR003 records the future-only recommendation: any successor correction
should compute and independently verify every pinned dependency hash from raw
Git blob bytes before acceptance, then keep the D011 scientific workload,
rows, models, controls, thresholds, folds, seeds, margins, and ceilings
unchanged. D011-C1 cannot be retried or rescued by reducing the active design.
