# Post-Gate-5 Clean-Source Compute Preflight

Version: 0.1.1
Decision: D009
Protocol: P001
Prepared: 2026-07-13
Accepted: 2026-07-13
Status: Terminal technical STOP; resource admission unavailable; research-data execution unauthorized

## Decision

D009 authorizes one clean-source, deterministic synthetic benchmark for the
accepted D008 implementation. It does not authorize a development-row fit,
calibration or final-test access, model selection, hardware or GPU execution,
Gate 5 reinterpretation, or Gate 6.

The machine-readable authority is `configs/post_gate5_preflight.yaml`. The
benchmark must stop if the Git worktree is dirty, the active branch is not
`main`, or this document and the machine-readable contract disagree.

## Question

Can the complete frozen P001 workload be executed on the recorded reference
laptop without changing rows, folds, rungs, controls, diagnostics, or claim
boundaries?

This is a compute-admission question, not a QML-performance question.

## Frozen synthetic workload

The benchmark uses deterministic synthetic arrays only. It contains 1,024
training rows, 256 validation rows, 64 primary-control features, and eight
compressed circuit features. The quantum workload is the D008 worst admitted
size: eight qubits, two data-reupload layers, entanglement enabled, one exact
statevector task at a time, and 256 deterministic Nystrom landmarks.

One shared quantum projection must feed both the Q01b cost head and FQK
feasibility head. The same benchmark also executes all unique D008 matched
controls using the frozen Gate 5 model parameters: C01 through C06 where
applicable, A01-T04, the A02 classical RBF kernel, and compressed C05-T17.
Synthetic outputs must be finite, and the synthetic feasibility target must
contain both classes.

No statevector or full kernel matrix is persisted. The benchmark output is a
compact JSON audit containing source hashes, timings, resource observations,
admission checks, and zero research-row read counters.

## Conservative campaign projection

The preflight charges the complete measured benchmark to every equivalent
1,024-row unit, even where the later runner could safely reuse projections or
avoid repeating controls. This prevents a favorable admission decision from
depending on unimplemented cache savings.

The tuning rungs contribute 77.5 equivalent units. Five folds and 20 selected
seeds contribute 100 exact units. Three report-only sensitivity conditions
contribute another 300 units. The frozen total is therefore 477.5 units. Every
time and artifact projection receives a further 25% margin.

## Admission limits

PASS requires all of the following:

- no more than 250 projected CPU-core-hours;
- no more than five projected sequential wall-clock days;
- no more than 20 GiB of projected new artifacts;
- no more than 24 GiB observed peak process working set;
- at least 20 GiB free disk after projected artifacts;
- zero GPU hours, zero research rows, and zero calibration/final-test reads.

If any check fails, the result is `STOP`. The active design is not reduced and
the benchmark is not silently retried. The observed stop, bounded
interpretation, and evidence-based future improvement must be committed under
the D008 future-research firewall.

## Reporting

The source-bound JSON is the sole quantitative source for RFIG-030. The figure
shows normalized utilization against each accepted resource limit with exact
observed and allowed values. It is methods and compute evidence only; it cannot
support a model-performance, quantum-advantage, mission, or Gate 6 claim.

## Consequence

A PASS permits preparation of a separate D010 development-only execution
decision. It does not itself unlock research-data fitting. A STOP leaves P001
execution locked pending a new prospective compute protocol.

## Recorded outcome

The single authorized run started from clean `main` commit
`7aade60d61897781076730676aafca000ca52ad0`. It completed the shared 1,024-row
synthetic training projection, then the Windows peak-working-set probe raised
`OSError: Unable to read Windows process memory counters`.

The validation projection, projected-kernel geometry, Q01b/FQK heads, all
matched controls, and the admission calculation were not reached. Development,
calibration, and final-test row reads remained zero. The result is therefore
`STOP`, not PASS or resource-limit FAIL. It says nothing about QML performance
and does not establish whether the frozen campaign fits the laptop ceilings.

P001-FR001 records one future-only improvement: validate a correctly typed
Windows memory adapter against an independent OS reading before a later full
preflight. The improvement requires a new prospective protocol and cannot
alter or retry the active P001 pipeline. RFIG-029 records the stop; RFIG-030 is
not generated because no resource-admission values exist.
