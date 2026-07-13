# D011-C2 Raw-Blob Hash Correction Freeze

Version: 0.1.0
Decision: D011-C2
Protocol: P001
Prepared: 2026-07-14
Accepted: 2026-07-14
Status: Accepted; hash smoke test and one unchanged preflight attempt pending

## Decision

After reviewing the D011-C1 stop evidence, the assistant determined that the
failure was limited to governance metadata: the C1 freeze pinned dependency
hashes computed outside the raw Git-blob byte path, while the actual raw Git
blobs are stable and independently verifiable.

D011-C2 corrects only those pinned dependency hashes and requires a
hash-consistency smoke test before the one unchanged preflight attempt. It does
not change the D011 scientific workload, rows, folds, models, controls,
thresholds, seeds, resource ceilings, or claim boundaries.

The machine-readable authority is
`configs/post_gate5_d011_c2_hash_correction.yaml`.

## Frozen Attempt

The preflight remains the D011 largest-fold synthetic benchmark:

- 1,024 synthetic training rows and 9,750 synthetic validation rows.
- Eight qubits, two data-reupload layers, both projected heads, A02, and every
  matched classical control.
- 1,220 worst-fold bundle units with a 25% margin.
- The same CPU, wall-clock, artifact, process-memory, free-disk, and zero-GPU
  ceilings.

D011 and D011-C1 STOP evidence remain immutable. D011-C2 writes its own
evidence file at
`data/processed/reporting/post_gate5_d011_c2_fold_shape_preflight.json`.

## Consequence

A D011-C2 `PASS` records corrected synthetic compute admission only and asks
for a human decision on whether to resume the D011 development-only campaign
authority. It does not itself authorize campaign execution.

A D011-C2 `STOP` is terminal for this correction attempt. It must update the
future-research register and paper figures, and it cannot be retried or rescued
by reducing the active design.
