# D011-C2 Raw-Blob Hash Correction Freeze

Version: 0.1.0
Decision: D011-C2
Protocol: P001
Prepared: 2026-07-14
Accepted: 2026-07-14
Status: Completed with synthetic corrected fold-shape admission PASS; development campaign still requires separate human decision

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

## Outcome

The hash-consistency smoke test and direct-file import smoke test both passed
from clean source commit `06381d1`. The single unchanged D011-C2 preflight then
passed all five unchanged laptop boundaries:

- 4.7259 CPU-core-hours against a 250 core-hour maximum.
- 0.2002 sequential wall-days against a five-day maximum.
- 2.9785 GiB new artifacts against a 20 GiB maximum.
- 0.6339 GiB peak process memory against a 24 GiB maximum.
- 45.3606 GiB projected free disk after artifacts against a 20 GiB minimum.

The result used synthetic rows only. Development, calibration, and final-test
reads remained zero; hardware, GPU, and Gate 6 runs remained zero. RFIG-031
records corrected fold-shape compute admission.

D011-C2 is closed to rerun. Its PASS is synthetic compute-admission evidence
only and asks for a human decision on whether to resume the D011
development-only campaign authority. It does not itself authorize campaign
execution.
