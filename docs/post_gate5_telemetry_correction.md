# Post-Gate-5 Telemetry Correction and Preflight Rerun

Version: 0.1.1
Decision: D010
Protocol: P001
Prepared: 2026-07-13
Accepted: 2026-07-13
Status: Completed with synthetic compute admission PASS; D010 grants no research-data authority; D011 conditional authority is recorded separately

## Decision

D010 prospectively authorizes a narrow correction to the process-memory
telemetry that stopped D009. It also authorizes one telemetry-only validation
and, if that validation passes, one rerun of the unchanged synthetic compute
preflight as attempt 2.

D010 does not authorize research-data fitting, calibration/final-test access,
model selection, hardware/GPU work, Gate 5 reinterpretation, or Gate 6.

## Root cause and correction

The D009 runner called `GetProcessMemoryInfo` through untyped `ctypes`
defaults. On 64-bit Windows, the native handle and pointer arguments were not
declared, and the function returned no valid process counters.

D010 permits only these implementation changes:

- declare `HANDLE`, `DWORD`, `BOOL`, pointer, and structure types explicitly;
- type `GlobalMemoryStatusEx` in the same way;
- compare the adapter's current working set with an independent PowerShell
  `Get-Process ... WorkingSet64` reading before the benchmark;
- require positive current memory, peak memory at least as large as current,
  and agreement within the larger of 64 MiB or 25%; and
- bind source hashes to committed Git blobs rather than checkout-dependent
  line endings.

The standalone diagnostic preceding this freeze returned a 72-byte process
counter structure and adapter-versus-PowerShell difference of 147,456 bytes.
That diagnostic established the proposed correction but is not the formal
accepted validation or a resource-admission result.

## Unchanged D009 contract

The benchmark inherits `benchmark`, `campaign_projection`, and `ceilings`
directly from `configs/post_gate5_preflight.yaml`, whose accepted Git-blob
SHA-256 is pinned in the D010 config. The following remain unchanged:

- deterministic synthetic seed and 1,024 training plus 256 validation rows;
- 64 primary-control and eight compressed features;
- eight qubits, two layers, entanglement, feature scale, bandwidth,
  regularization, and 256 landmarks;
- one shared Q01b/FQK projection, both heads, and every matched control;
- 477.5 equivalent work units and 25% projection margin; and
- all CPU, wall-time, artifact, memory, disk, GPU, and concurrency limits.

## Execution order

1. Commit D010 source and validation tests before execution.
2. From that clean commit, run the telemetry-only check.
3. Continue only if the telemetry check returns `PASS`.
4. Run the full synthetic preflight once as attempt 2.
5. Record PASS or STOP without changing or retrying the workload.

A PASS generates RFIG-030 from the source-bound result JSON. A STOP updates
RFIG-029 and the future-research register. Missing values are never plotted as
zero.

## Outcome

The telemetry-only check passed with a 49,152-byte difference between the
typed adapter and PowerShell, below the frozen 64 MiB allowance. The one
authorized full rerun then completed once from clean source commit `882bfd5`.
Every projected head and matched control finished with finite outputs, and all
five admission checks passed under the unchanged 477.5-work-unit projection
and 25% margin:

- 1.7849 CPU-core-hours against a 250 core-hour maximum;
- 0.0758 sequential wall-days against a five-day maximum;
- 1.1658 GiB new artifacts against a 20 GiB maximum;
- 0.2014 GiB peak process memory against a 24 GiB maximum; and
- 53.7426 GiB projected free disk against a 20 GiB minimum.

The result used synthetic rows only. Development, calibration, and final-test
reads were zero; hardware, GPU, and Gate 6 runs were zero. RFIG-030 records the
resource margins. The authority is exhausted and no additional preflight rerun
is permitted.

## Consequence

A PASS authorizes preparation of D011 only. It does not unlock development
rows. A STOP leaves P001 locked and no further preflight retry is authorized
without another prospective human decision.
