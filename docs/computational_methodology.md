# Computational Methodology and Reference Hardware

Version: 0.6.8
Hardware snapshot: 2026-07-11  
Status: published computational-methodology supplement  
Repository: `taechasith/QMLforArtemisIV`

## 1. Purpose

This document defines the reference workstation used for local development and
the hardware-aware execution method for OpenQFuel-Cislunar. It makes compute
constraints visible so runtime, batching, parallelism, and hardware-dependent
results can be interpreted and reproduced.

The workstation profile is an execution boundary, not a scientific tuning
variable. It does not modify any accepted value in `research_protocol.md` or
`configs/`. Dataset totals, splits, seeds, thresholds, exclusions, model
families, qubit requirements, shot counts, and stopping rules remain governed
by the frozen protocol.

If the formal design cannot be completed on the reference workstation after
safe batching and checkpointing, the study must use additional declared
compute or request a documented protocol deviation. The experiment must not be
silently reduced to fit the laptop.

### 1.1 How readers should use this disclosure

The reference workstation is not a minimum specification, recommended build,
or requirement for reproducing or extending this research. Readers should not
copy the CPU, GPU, memory, worker count, or local batch sizes merely because
they appear here.

A reader may use a smaller laptop, a larger workstation, a server, cloud
compute, or a supported quantum backend. What must be reproduced is the
scientific configuration: data eligibility, model definition, numerical
accuracy, splits, seeds, thresholds, budgets, and reporting rules. Worker
count, chunk size, checkpoint frequency, and storage layout may be adapted to
the available machine when those changes do not alter the scientific result.

The transferable contribution of this hardware disclosure is therefore:

- visibility into the limitations under which the results were produced;
- evidence of which bottlenecks and failures occurred in practice;
- reusable strategies for diagnosing and adapting to those constraints; and
- a warning not to generalize this laptop's wall time, energy use, or capacity
  to other hardware.

Readers extending the work should publish their own hardware manifest and
explain how they handled comparable constraints. They should apply the lessons
from this project, not treat this workstation as a template to copy.

## 2. Reference workstation manifest

The primary local research workstation has the following measured profile:

| Component | Reference specification |
|---|---|
| CPU | 13th Gen Intel Core i9-13900HX |
| CPU topology | 24 physical cores, 32 logical processors |
| System memory | 32 GiB DDR5-5600, installed as two 16 GiB modules |
| Discrete GPU | NVIDIA GeForce RTX 4060 Laptop GPU |
| Discrete GPU memory | 8,188 MiB |
| GPU driver at snapshot | NVIDIA 592.27 |
| Integrated GPU | Intel UHD Graphics |
| Primary storage | Samsung MZVL21T0HDLU-00BH1 NVMe SSD, approximately 1 TB |
| Available storage at snapshot | Approximately 53.0 GB decimal, or 49.4 GiB |
| Operating system family | Microsoft Windows |
| Environment manager at snapshot | `uv 0.11.28` |
| Project interpreter at snapshot | Python 3.14.6 in `.venv` |

Available storage, software versions, and driver versions are time-dependent.
Each formal phase must record the values actually used rather than assuming the
snapshot remains current.

This is a high-performance laptop rather than a server. Its practical
bottlenecks are sustained cooling, 32 GiB system memory, 8 GiB VRAM, and local
free storage. Its strengths are independent CPU-case throughput, fast NVMe
checkpointing, and support for compact GPU workloads.

## 3. Relationship to the frozen compute budget

`configs/compute_budget.yaml` defines study-wide ceilings of 10,000 CPU
core-hours, 1,000 GPU-hours, 50 million QPU shots, 250 GB persistent storage,
and 30 wall-clock days. Those are maximum research budgets, not a statement
that the reference workstation has 250 GB of free local space or can sustain
all CPU and GPU work concurrently.

The more restrictive limit applies during local execution:

1. the frozen study-wide ceiling limits scientific resource use;
2. the measured workstation envelope limits safe local scheduling; and
3. a run proceeds only when it satisfies both.

Exceeding a frozen study ceiling requires the protocol-deviation process.
Moving a conforming workload to declared external compute does not itself
change the scientific design, but the external hardware and software manifest
must be reported.

## 4. Local execution envelope

The following defaults are used to avoid oversubscription and preserve enough
capacity for Windows, the editor, monitoring, and checkpoint writes.

### 4.1 CPU scheduling

- Eight process workers are the default for independent simulations, seeds, or
  scenario chunks.
- Twelve workers are the normal local high-throughput ceiling after a
  representative benchmark confirms memory and thermal stability.
- Sixteen workers may be used for a monitored overnight run only after a
  sustained thermal test.
- Thirty-two CPU-heavy processes are prohibited as a default. Logical
  processors are not equivalent to 32 full-performance independent cores, and
  process plus BLAS oversubscription can reduce throughput.
- Independent windows, seeds, scenarios, or data chunks may run in parallel.
  Tasks that mutate a shared result file must remain serialized or use separate
  atomic chunk files.
- Numerical libraries use one thread per process during process-parallel work.

The standard thread environment is:

```powershell
$env:OMP_NUM_THREADS = "1"
$env:MKL_NUM_THREADS = "1"
$env:OPENBLAS_NUM_THREADS = "1"
$env:NUMEXPR_NUM_THREADS = "1"
$env:OPENQFUEL_MAX_WORKERS = "8"
```

Formal run manifests record the actual worker count and thread variables.

### 4.2 System-memory scheduling

- At least 8 GiB is reserved for the operating system and supporting tools.
- The normal aggregate project working-set target is 22-24 GiB.
- Concurrency is reduced if committed memory approaches 26 GiB.
- New work is not launched at 28 GiB or during sustained paging.
- Available memory is checked immediately before a formal run because other
  applications may already consume a substantial fraction of the 32 GiB.
- Large scenario, prediction, and seed outputs are streamed in chunks rather
  than held together in memory.

### 4.3 GPU scheduling

- One GPU training or quantum-simulation process runs at a time.
- The normal allocation target is at most 6.5 GiB VRAM.
- Usage from 6.5 to 7.2 GiB triggers batch-size reduction or gradient
  accumulation before continuing.
- Jobs are not designed to consume the full reported 8,188 MiB because the
  driver, display, framework context, and temporary tensors require headroom.
- Mixed precision may be used only where it preserves the registered metric
  and numerical method. Final metrics retain their required precision.
- A backend is counted as GPU work only when execution logs verify that it used
  CUDA. CPU quantum simulation is reported as simulation cost, not quantum or
  GPU hardware advantage.

### 4.4 Storage scheduling

- At least 20 GiB remains free on the system drive after projected outputs.
- Given approximately 53 GB free at the hardware snapshot, no more than about
  25 GB of new project data is scheduled before storage is reassessed.
- Storage estimates include raw inputs, environment growth, temporary chunks,
  checkpoints, failed cases, result tables, logs, and figures.
- Large numeric outputs use compressed typed formats where permitted by the
  registered schema.
- Raw sources, formal evidence, nonconvergence records, and scientifically
  relevant failures are not deleted automatically to recover space.
- When the projected free-space floor cannot be met, verified external storage
  or another declared compute environment is required.

### 4.5 Thermal and power controls

Formal multi-hour runs use AC power and the workstation's performance cooling
profile. Worker count is reduced when sustained CPU temperature approaches
95 C, sustained GPU temperature approaches 85 C, or clock collapse indicates
thermal throttling. These are local operational safeguards, not experiment
outcomes.

## 5. Hardware-aware execution procedure

Every formal computational phase follows this sequence:

1. Verify that the governing decision gate authorizes the phase.
2. Synchronize the locked environment and record software and driver versions.
3. Run unit, integration, compilation, and dependency checks.
4. Execute a correctness smoke test on development-only data.
5. Benchmark a representative unlocked workload without reading final-test
   labels.
6. Record seconds per case, peak RAM, peak VRAM, output bytes per case, worker
   count, and thermal behavior.
7. Estimate formal runtime and storage with at least 25% scheduling and thermal
   overhead.
8. Select chunk size and concurrency within the local envelope.
9. Test interruption and checkpoint resume before an overnight or multi-hour
   run.
10. Execute the exact frozen configuration and retain failures.
11. Validate row counts, schemas, checksums, and acceptance results before
   merging chunks or publishing conclusions.

The reference runtime estimate is:

```text
estimated wall time = measured seconds per case * formal cases
                      / effective workers * 1.25
```

The factor is increased when throughput or temperature is unstable. Runtime
estimation changes scheduling only; it does not authorize early termination of
a frozen experiment.

## 6. Phase-specific implementation method

### 6.1 Simulator verification and validation

NASA GMAT executes serially as the independent comparison tool. Independent
Python validation windows may run in separate processes only when ephemeris
access is process-safe and each process writes an isolated result. Nominal and
tightened integrations remain separately identifiable in evidence tables.
Integrator tolerances, OEM samples, validation windows, and acceptance limits
are never loosened to reduce runtime.

Gate 3 was accepted on 2026-07-12 after the D001 repair and independent rerun.
Gate 4 and D002 were accepted on 2026-07-12. Development generation is
authorized. Corrected F0, F1, and F2 payloads pass their full D003 conformance
audits. D005 and D006 were accepted on 2026-07-12. The D006 development-only
campaign completed on 2026-07-13 from source commit `6e5a620`: 871/871 tasks
are complete and none failed. The human research lead accepted D007 on
2026-07-13 from candidate commit `7a726c8917a85f24313208eb18c33e1ccb5f703e`,
authorizing only the reporting correction for the registered Q02/Q03
terminal-nonadvancement outcome. No model execution or locked-split access is
authorized by that decision. Reporting from clean source commit `7b7db69`
validated the unchanged package and returned a technical trigger `FAIL` with
zero calibration/final-test reads. Q02/Q03 later stages are recorded as
`not_reached_under_frozen_eligibility`, not execution failures. RFIG-021 through
RFIG-023 preserve the reached-rung, 20-seed, and regime evidence.
The human research lead accepted the unchanged technical `FAIL` on 2026-07-13,
closing Gate 5 without authorizing the proposed new algorithm. RFIG-001 records
the gate decision. No experiment, model fit, or locked-split read was performed
for acceptance, and Gate 6 remains unauthorized.
Calibration remains restricted to post-selection calibration, and final tests
remain separately locked.

### 6.2 F0/F1/F2 dataset generation

The accepted totals remain 10,000 F0 cases, 50,000 F1 cases, and an initial
5,000 F2 cases. Local batching changes only how those totals are executed.

| Fidelity | Initial local chunk | Initial workers | Execution method |
|---|---:|---:|---|
| F0 | One 500-row group | 1 for repaired first group; up to 4 groups after audit | Atomic group checkpoint and deterministic equivalence check before parallel scale-up |
| F1 | One 2,500-row group | 1 for first group; up to 4 groups after audit | Process-isolated groups with one numerical-library thread per worker |
| F2 | One 250-row group | 1 for first group; up to 2 groups after audit | Profile ephemeris, memory, and thermal behavior before increasing concurrency |

Each completed group ledger records payload version, configuration hash,
source commit, requested/completed cases, validation state, runtime, and output
checksum. All nonconvergence cases remain represented. The first corrected
group is deliberately serial so validity is established before throughput is
optimized for the reference laptop.

After full F0 qualification, a deterministic within-group cache was enabled
for zero-burn candidates with byte-identical true states. This removes repeated
integration of the same trajectory in nominal groups while retaining each
candidate's timing metadata. It does not cache nonzero burns or distinct
uncertainty states and therefore changes scheduling cost, not scientific rows.

The first F1 group required 1,268.159 seconds for 2,500 U0 rows, 22.7 times the
F0 G01 wall time despite the cache. Its strict audit passed. A duration- and
trajectory-count projection estimated 13.8 worker-hours for the remaining
groups and 3.5 wall-hours at four ideally balanced workers. The controlled
G02-G14 scale-up instead required 63,639.442 seconds (17.678 worker-hours) of
summed group work in 18,148.400 seconds (5.041 wall-hours), for effective
concurrency 3.51. Including the earlier serial checkpoint, all F1 work totals
64,907.601 seconds (18.030 worker-hours) and 19,416.559 seconds (5.393 hours)
of active wall time, excluding the idle interval between stages.

All 35,000 F1 rows pass strict schema, relationship, uncertainty, finite-value,
checksum, and decision-set audits with no nonconvergence. The run used four
workers rather than the eight-worker ceiling to limit sustained laptop heat;
CPU, not RAM or VRAM, was limiting. RFIG-011 and RFIG-012 preserve F1 group
coverage and runtime; the interim F0/F1-only summary was superseded by the
full F0/F1/F2 campaign summary in RFIG-018. The optimistic estimate is retained
as scheduling evidence rather than rewritten after the result.

The serial F2 G01 checkpoint generated 250 rows in 450.835 seconds and passed
every strict audit. Its 1.803 seconds per row is 3.555 times the F1 G01
per-row cost. Applying that measured ratio to F1 G02-G14 work and the
one-tenth F2 row count projects 22,624.046 seconds (6.285 worker-hours) for the
remaining 3,250 rows. The frozen two-worker ceiling gives 3.142 ideal
wall-hours; the local planning estimate is 3.928 hours after the required 25%
margin. This estimate authorizes scheduling only after the checkpoint commit;
actual F2 ledgers and the full audit remain authoritative.

The measured G02-G14 scale-up required 15,604.130 seconds (4.334
worker-hours) of summed group work in 7,978.900 seconds (2.216 wall-hours), for
effective concurrency 1.956. This was 68.97% of projected group work and
56.43% of the conservative planning wall time. Including G01, F2 totals
16,054.965 seconds (4.460 worker-hours) and 8,429.735 seconds (2.342 hours) of
active wall time. All 3,500 F2 rows pass strict audit with no nonconvergence;
RFIG-016 through RFIG-018 preserve coverage, runtime, and the full campaign
summary. The faster-than-planned result does not retroactively alter the
projection method or authorize more workers for later phases.

### 6.3 Classical model experiments

Trial-level and model-internal parallelism are not both run at full width.
Tree-model parallelism starts at eight workers, and at most one or two tuning
trials run concurrently. Memory mapping or streamed arrays are used when
dataset and model copies would exceed the aggregate memory target.

Hardware scheduling does not alter model families, tuning trials, development
seeds, finalist seeds, or locked comparison data.

### 6.4 QML experiments

Required 4-, 6-, and 8-qubit experiments remain mandatory after their
governing gate opens. Ten and twelve qubits remain conditional exactly as
specified in `configs/compute_budget.yaml`.

The local QML schedule does not execute 30 trials multiplied by every seed as
one Cartesian grid. All 30 frozen trials begin on 128 identical development
rows; 15, 8, and 4 survive deterministic grouped-CV rungs at 256, 512, and
1,024 rows. Only the selected configuration is rerun on 20 development seeds.
The random-Fourier ridge and other matched views use the same samples. This
staging is frozen before outcomes and reduces laptop wall time without changing
the model families, maximum trials, required qubits, or finalist seeds.

Circuit families and seeds are queued through one GPU-backed process at a
time. Statevector, finite-shot, gradient, and noise-model memory are benchmarked
separately because temporary tapes and noisy simulation can dominate raw
statevector storage. Shot batches and seed outputs are checkpointed before any
request to change a registered shot or seed count.

No result produced by classical simulation on the RTX 4060 is described as a
quantum hardware speedup or quantum advantage.

### 6.5 Mission Monte Carlo

The minimum 2,000 paired simulations per stratum and frozen 1,000-run
sequential decision batch remain unchanged. A 1,000-run decision batch may be
computed as smaller 250-500-case storage chunks, but stopping is evaluated only
after the complete registered batch. Common random numbers and paired outcomes
are preserved.

## 7. Required compute reporting

Every published formal result must identify:

- CPU and GPU model;
- physical and logical CPU count;
- installed RAM and GPU memory;
- operating system;
- GPU driver and relevant runtime/backend;
- Python version, `uv.lock` identity, and package environment;
- worker count and numerical-library thread settings;
- model, circuit, qubit, shot, seed, and batch configuration as applicable;
- wall-clock time and failed/nonconverged workload counts;
- peak RAM and VRAM when measurable;
- hardware queue, communication, encoding, mitigation, and classical
  post-processing time where applicable; and
- energy or carbon measurement method on a best-effort basis.

Timing comparisons are interpreted only after confirming equivalent workload,
precision, preprocessing, and output requirements. Laptop wall time is not
generalized to server, cloud, QPU, or flight-computer performance.

Published compute figures follow `docs/research_figure_policy.md`. Small
factor comparisons are reported as exact tables; dense evidence with more than
100 plotted points is summarized with heat maps, ordered matrices, linear
clusters, density views, or aggregated trends rather than row-per-record bar
charts; and methods, timelines, and decision gates are represented as diagrams
rather than statistical graphs.

## 8. Portability and reproducibility boundary

Another machine may reproduce the study with different worker counts, batch
sizes, or checkpoint intervals when the scientific configuration and numerical
acceptance criteria are unchanged. Hardware-dependent runtime and energy
results must be reported separately for each environment.

If a different environment changes numerical outputs beyond frozen convergence
or acceptance limits, that discrepancy is a validation result requiring
investigation. It must not be hidden as a harmless performance difference.

The detailed personal scheduling log remains in the ignored
`docs/local_compute_guide.md`. This published document contains the stable
hardware context and methodological rules required to interpret formal results.

## 9. Living record of computational struggles and adaptations

Computational methodology is updated throughout the project, not reconstructed
only after successful results are known. Each material bottleneck, failed
approach, diagnostic campaign, and adaptation is retained below. The record
distinguishes hardware limitations from software defects, source limitations,
and scientific failures because they require different responses.

| Date | Phase | Struggle observed | Impact | Adaptation and evidence | Status and transferable lesson |
|---|---|---|---|---|---|
| 2026-07-11 | Environment bootstrap | `uv` was not initially available on `PATH`, and a registered Python 3.12 launcher entry was stale | The prescribed extraction and verification commands could not start on a fresh local environment | Installed `uv` through the valid local Python installation, synchronized the locked environment, and reran tests and dependency checks | Resolved. Verify executable paths and the actual interpreter before attributing a failure to project code |
| 2026-07-11 | Local storage planning | The study permits up to 250 GB persistent storage, but only about 53 GB was free on the reference system drive | The global protocol ceiling could not be treated as locally available capacity | Established a 20 GiB free-space floor, a roughly 25 GB reassessment point for new data, compressed chunk outputs, and checksum-verified external storage when needed | Ongoing constraint. Separate study-wide ceilings from measured local capacity |
| 2026-07-11 | Gate 3 F2 validation | High-accuracy nominal and tightened propagations dominated local wall time | Repeated full validation runs were expensive even though the laptop has many logical processors | Preserved every frozen tolerance and sample, benchmarked the complete path, and limited proposed acceleration to independent-window parallelism, caching, and resumable outputs | Ongoing optimization. Reduce scheduling overhead, never numerical credibility |
| 2026-07-11 | GMAT integration | GMAT resolved support files from its execution environment rather than the repository-relative location initially assumed | The independent tool could not load DE440s or the custom gravity file from the first generated script | Staged checksum-verified support files in the external GMAT distribution and kept the tracked script portable | Resolved. Cross-tool validation must test path resolution and provenance, not only equations |
| 2026-07-11 | Gate 3 GMAT comparison | The first independent comparison failed all ten endpoint thresholds by large margins | The simulator gate correctly entered repair analysis instead of allowing ML work to start | Incremental Earth-only, J2-only, and full-force diagnostics isolated the discrepancy to the custom COF `POTFIELD` fixed-column format; Deviation D001 records the repair | Resolved. The fixed COF passes all ten frozen GMAT thresholds without changing physics, windows, or acceptance limits; preserve failed evidence because it shows how the defect was found |
| 2026-07-11 | Gate 3 event evidence | RTC3 occurred at 18:53:00Z, after the qualified OEM was created at 03:22:19Z | Later rows in that OEM are pre-event predictions, not post-event evidence; more compute cannot turn them into historical/reconstructed evidence | Computed no RTC3 timing error and retained `not_eligible`, meaning not tested with eligible evidence, neither pass nor fail | Open source limitation. Gate 3 acceptance does not claim RTC3 validation, and hardware adaptation cannot repair missing evidence |
| 2026-07-12 | Gate 4 literature retrieval | OpenAlex returned all seven query counts but persistently rate-limited metadata export with HTTP 429 | A complete multi-database systematic review could not be claimed from this run | Preserved count-only OpenAlex logs, completed NTRS/arXiv API retrieval, extracted 23 primary or authoritative records, labeled the synthesis bounded, and accepted D002 with a mandatory pre-manuscript update | Open coverage limitation. API throttling must reduce claim scope, not be hidden as successful screening |
| 2026-07-12 | Gate 4 literature refresh | Retrying the frozen searches recovered 3,278 OpenAlex metadata rows, but five searches remain first-100 partial and 926 of 4,218 unique discovery rows await full-text screening | The larger discovery ledger cannot be described as a closed evidence synthesis or used to revise an accepted model after outcomes become visible | Preserved the 23-record accepted extraction matrix, labeled refreshed includes provisional, and added RFIG-014 as the source-flow record | Open screening limitation. More retrieved metadata is not the same as completed evidence appraisal |
| 2026-07-12 | Gate 4 QML scheduling | A full trial-by-seed-by-fold Cartesian run would spend substantial laptop time on configurations that are clearly uncompetitive at small samples | The accepted 30-trial and seed ceilings could be misread as requiring every combination | Froze grouped successive-halving rungs for QML and matched controls, 20 seeds only for selected development configurations, one statevector/GPU job, and resumable checkpoints | Preventive adaptation. Preserve comparisons and randomness while pruning only by a rule registered before outcomes |
| 2026-07-12 | Gate 5 scenario generation | The first generator produced 7,000 F0 rows before a schema/uncertainty audit and an F1 run stopped on an incorrect DE440s path | Every pre-D003 F0 row is invalid for research use, and 1,020 of 1,400 decision sets lack a feasible reference | Stopped progression, preserved RFIG-002 through RFIG-004, froze D003 in `72f99c4`, qualified G01 with RFIG-005/RFIG-006, then audited all F0 with RFIG-007 through RFIG-009 | F0 resolved: 14/14 groups and 7,000/7,000 rows valid in 542.060 s group work; 319/1,400 no-reference sets are retained limitations. F1 and F2 were later resolved separately under D003 |
| 2026-07-12 | Gate 5 F1 preparation | Nominal decision sets contain multiple zero-delta-v candidates that would repeat the same multi-day propagation thousands of times | The scientifically identical work would waste CPU time before any higher-fidelity evidence was produced | Added a true-state-keyed zero-burn cache after F0 qualification; candidate timing metadata remains distinct and nonzero/distinct-state propagations are never cached | Execution-only adaptation. Unit tests enforce cache identity and timing retention; F1 runtime figures must disclose the optimization |
| 2026-07-12 | Gate 5 F1 checkpoint | Valid F1 G01 required 1,268.159 s, 22.7 times F0 G01, while using one core and roughly 115 MB RAM | Serial completion of the remaining 32,500 unlocked F1 rows would be unnecessarily slow on the 24-core/32-thread reference laptop | Qualified G01 first, projected aggregate work, and added a four-process group scheduler with per-worker thread limits, atomic files, and a locked shared ledger | Resolved checkpoint. CPU, not RAM/VRAM, was limiting; four workers preserved cases and tolerances |
| 2026-07-12 | Gate 5 F1 scale-up | The 13-group scale-up exceeded its 13.8 worker-hour and 3.5 ideal wall-hour projection | The laptop required 17.678 worker-hours and 5.041 wall-hours despite effective concurrency 3.51; four-group load was uneven because trajectory and uncertainty families have different cost | Completed every group without increasing workers or relaxing the scientific configuration; retained per-group ledgers, strict audit, RFIG-011/RFIG-012, and the later full-campaign summary in RFIG-018 | F1 resolved: 14/14 groups and 35,000/35,000 rows valid. Runtime projections need measured family-specific costs plus thermal/imbalance margin; 4,215/7,000 no-reference sets remain a scientific coverage limitation, not a compute failure |
| 2026-07-12 | Gate 5 F2 checkpoint | F2 G01 required 450.835 s for only 250 rows, 3.555 times F1 G01 per-row cost | The tighter F2 model makes even the reduced row groups expensive, while only 11.49 GiB RAM and 47.74 GiB disk were free before launch | Kept the checkpoint serial, audited all 250 rows, projected G02-G14 from measured fidelity-normalized work, capped scale-up at two workers, and recorded RFIG-015 | Qualified checkpoint. Plan about 3.93 wall-hours with 25% margin, but retain measured ledgers and reduce concurrency rather than scientific work if thermal or memory pressure appears |
| 2026-07-12 | Gate 5 F2 scale-up | Family-normalized projection overstated F2 G02-G14 work because the tighter-model cost ratio from nominal G01 did not transfer uniformly across uncertainty families | Actual scale-up consumed 4.334 worker-hours and 2.216 wall-hours, 68.97% and 56.43% of the corresponding projected work and planning wall time | Completed every group at two workers, retained the original projection, audited all 3,500 rows, and added RFIG-016 through RFIG-018 | F2 resolved: 14/14 groups valid with zero nonconvergence. Use family-specific pilot costs for future estimates, but preserve conservative margin and never use an overestimate to expand scientific scope after outcomes are visible |
| 2026-07-12 | Gate 5 literature hardening | The local QML space-fuel note contained useful leads but mixed primary literature, arXiv, vendor material, RequestPDF pages, and broad claims | Without source-grade controls, Gate 5 could overstate QML readiness or import adjacent QRL/annealing ideas into a supervised benchmark | Opened D004 before any research model fit, added source-vetting rules, kernel concentration/bandwidth diagnostics, trainability failure reporting, matched dequantization controls, fixed regime reports, and RFIG-019 | Preventive adaptation. Model families, thresholds, splits, tuning budgets, and final-test locks do not change; D004 strengthens interpretation and required graphing only |
| 2026-07-12 | Gate 5 runner scientific audit | The freeze left exact folds, row hashes, fold-local transforms, and residual baseline indexing implicit; the implementation's default last-column baseline could select a one-hot or PCA component | Silent choices could leak validation statistics, distort unequal-fold weighting, or invalidate C06/Q03 physically | Opened D005 before model fitting; froze label-agnostic hashes, per-fold transforms, pooled OOF scoring, explicit target-scaled low-fidelity baselines, Q03 baseline exclusion from circuit angles, preflight tests, and RFIG-020 | Accepted by the human research lead from candidate commit `80ae35d`; 39,000 development rows passed preflight with zero calibration/final reads |
| 2026-07-12 | Gate 5 matched-control campaign audit | D005's 330-task plan cycled control dimensions independently, so equal trial/seed indices did not always share a PCA dimension; it also lacked immutable multi-rung and 20-seed orchestration | Executing the plan could call unmatched or weak controls “matched,” permit incomplete-stage selection, under-project end-to-end runtime, or make the multi-day CPU run irreproducible | D006 repeats the same 30 A01/C05 trials at all three dimensions, advances controls independently while carrying exact QML-index views, freezes signed authorizations and terminal failures, benchmarks frozen 1,024-row worst-shape views with end-to-end timing, validates output containment and source-bound reports, and vectorizes identical state batches | Accepted by the human research lead from candidate commit `3ac9403`. The first stage has 450 tasks; no model family/trial/split/threshold changes, recorded state/feature/kernel differences are at most `2.67e-15`, and calibration/final reads remain prohibited |
| 2026-07-13 | Gate 5 terminal-nonadvancement reporting audit | The completed campaign has 871 complete tasks and zero failures, but only 8/30 Q02 and 4/30 Q03 tasks were eligible at rung 128 versus retain=15 | The scheduler correctly stopped both families, while the reporter mislabeled their absent later authorization as terminal failure and demanded nonexistent later-rung/seed diagnostics | Opened D007 to verify the exact signed ranking/task/fold/digest chain, report trainability over authorized/reached stages, and keep stopped families excluded from selection and trigger evidence | Accepted by the human research lead from candidate commit `7a726c8`; reporting-only regeneration is authorized. No refit, rerank, threshold change, or locked read; the technical Gate 5 decision remains separate |
| 2026-07-13 | D007 Windows publication checkout | Git for Windows with `core.autocrlf=true` materialized the accepted LF reporting code and campaign CSV/JSON evidence as CRLF | Raw-byte candidate checks and campaign SHA-256 validation rejected all eleven anchored files even though their normalized Git content was unchanged | Added explicit `eol=lf` attributes for the accepted reporting and immutable evidence paths, set this checkout to `core.autocrlf=false`, and rematerialized the exact Git blobs before publication | Resolved portability issue only. The anchored-path diff against `7a726c8` is empty and the acceptance guard passes; no task, score, ranking, digest source, threshold, or split changed |
| 2026-07-13 | D007 official report regeneration | The accepted reporting correction had to distinguish valid scientific elimination from missing or failed evidence without changing post-outcome scores | A permissive report could promote stopped families, while an overstrict report would keep a complete negative result unavailable | Ran only the source-bound report and RFIG-021 through RFIG-023 generators from clean commit `7b7db69`, then verified package provenance, artifact hashes, and rendered figures | Technical trigger `FAIL`: Q01 mean NRMSE `0.6466136067` versus C06 `0.0087390408`, relative gap `72.9913708168`, zero qualifying regimes, and zero calibration/final reads |
| 2026-07-13 | Gate 5 human decision | The complete D007 package met its evidence contract but every preregistered trigger path failed | Reopening or retuning after seeing the result would invalidate the benchmark and turn a valid negative result into post-outcome model search | Accepted the unchanged technical `FAIL`, rejected development of the proposed new algorithm under the frozen trigger, and updated the governance record and RFIG-001 only | Gate 5 closed as a benchmark-specific negative result. No refit, calibration/final-test read, new algorithm, or Gate 6 run was authorized; RFIG-021 through RFIG-023 remain unchanged |
| 2026-07-13 | Post-Gate-5 exploratory protocol P001 | The accepted Gate 5 negative result does not prove all QML directions impossible, but post-outcome redesign risks bias | Any new branch must remain prospective, pipeline-bound, and visibly separated from the closed Gate 5 result | Opened a planning-only protocol for Q01b projected quantum kernel and FQK feasibility-only quantum kernel, recorded the scope matrix, and generated RFIG-024 | No new compute workload, model fit, calibration/final-test read, or Gate 6 run was authorized. QRL, dynamic circuits, annealing, QAOA, variational redesigns, larger-qubit circuits, and hardware runs remain appendix/future-only |
| 2026-07-13 | D008 exploratory implementation freeze accepted | P001 required exact methods and a way to learn from future failures without post-outcome rescue testing | An underspecified projected kernel or informal failure suggestion could silently change bandwidth, controls, retries, compute scope, or paper interpretation after results | Accepted a 30-pair balanced Q01b/FQK manifest, one-RDM projected-kernel formula, endpoint-specific controls and stop rules, laptop-bounded compute admission, future-research register, and RFIG-025 | Implementation and synthetic validation are authorized. Every failure/stop must be committed with an evidence-based future improvement, but that improvement cannot change or retry the active pipeline. Research-data fitting still requires a separate clean-source execution decision |
| 2026-07-13 | D008 implementation and synthetic validation | The accepted freeze needed executable projected-kernel math before any source-bound preflight could be proposed | Jumping directly to development rows would mix implementation debugging with research outcomes | Implemented Pauli X/Y/Z one-RDM projection, median-distance projected kernels, deterministic Nystrom landmarks, PSD clipping diagnostics, projected-kernel regressors/classifiers, D008 scope guards, and synthetic validation tests | Synthetic-only validation passed. No development-row fit, calibration/final-test read, hardware run, or Gate 6 execution occurred; the next process requires a separate clean-source compute preflight and execution decision |
| 2026-07-13 | D009 synthetic compute preflight | The clean-source run completed its first shared 1,024-row projection, then the Windows peak-working-set probe returned no valid process counters | Validation projection, both projected heads, all matched controls, and resource admission were not reached, so no laptop-fit conclusion can be made | Stopped without retry, preserved zero research/calibration/final reads, recorded P001-FR001 as a future-only typed-adapter validation, and generated RFIG-029 | Terminal technical STOP. This is a telemetry-interface failure, not QML performance or a resource-ceiling result; any correction and rerun require a new prospective human decision |
| 2026-07-13 | D010 telemetry correction and compute admission | A standalone diagnosis showed that D009 used untyped 64-bit Windows process handles and pointers; an explicitly typed adapter returned valid counters close to PowerShell | Retrying without a prospective correction would be undocumented, while changing the workload would confound telemetry repair with scientific redesign | Froze explicit PSAPI and `GlobalMemoryStatusEx` types, an independent `WorkingSet64` tolerance check, committed-Git-blob hashing, and exactly one unchanged synthetic attempt-2 rerun; the formal check differed by 49,152 bytes | PASS. The 25%-margin projection used 1.7849/250 core-hours, 0.0758/5 days, 1.1658/20 GiB artifacts, 0.2014/24 GiB peak RSS, and retained 53.7426 GiB versus a 20 GiB disk minimum. RFIG-030 records compute admission only; D009 is immutable and D011 remains required before research fitting |
| 2026-07-13 | D011 pre-execution fold-shape audit and conditional authority | D010's valid frozen bundle predicted 256 validation rows, but the real grouped folds contain 6,500 or 9,750 held-out rows and every complete task predicts 39,000 rows | Using the D010 projection as final campaign admission could understate validation projection/inference time even though its original PASS remains valid | Froze a q=8, two-layer, 1,024-training/9,750-validation synthetic bundle, charged 1,220 worst-fold units with 25% margin and no sharing/cache/smaller-shape credit, and retained unchanged methods, controls, guards, and reporting boundaries | The formal direct-file command failed at `scripts` namespace import before authority verification or synthetic work. D011 is a terminal pre-launch technical `STOP`; zero development/calibration/final rows were read, P001-FR002 is future-only, RFIG-029 is updated, and RFIG-031/RFIG-026-RFIG-028 remain absent. This is not QML or resource-admission evidence |
| 2026-07-14 | D011-C1 launcher correction | D011 failed before governed execution because the direct-file launcher imported helpers from the `scripts` namespace, which was not resolvable in that execution mode | Treating that import failure as QML or resource evidence would be scientifically wrong, but silently retrying would violate the no-rescue rule | Froze a launcher-only correction that imports shared synthetic-preflight helpers from `openqfuel`, requires a clean-source import smoke test, preserves the D011 STOP evidence, writes separate D011-C1 evidence, and permits exactly one unchanged fold-shaped synthetic preflight attempt | The smoke test passed, but the formal preflight stopped during C1 authority verification because a pinned raw Git-blob hash for the D011 config was wrong. Synthetic workload, resource admission, development/calibration/final rows, hardware, and Gate 6 were not reached. P001-FR003 records raw-blob hash prevalidation as future-only work; D011-C1 is terminal and RFIG-029 is updated |
| 2026-07-14 | D011-C2 raw-blob hash correction and compute admission | Review of D011-C1 showed stable raw Git blobs but C1-pinned dependency hashes produced through a non-raw text path | Correcting metadata is justified because the stop occurred before synthetic work, but the correction still needs prospective authority to avoid silent retry | Froze independently verified raw Git-blob dependency hashes, added a hash-consistency smoke test before the import smoke test, preserved D011/D011-C1 STOP evidence, and retained the unchanged D011 largest-fold synthetic preflight workload | PASS. The smoke tests passed, and the 25%-margin projection used 4.7259/250 core-hours, 0.2002/5 days, 2.9785/20 GiB artifacts, 0.6339/24 GiB peak RSS, and retained 45.3606 GiB versus a 20 GiB disk minimum. This is corrected synthetic compute admission only; development execution still requires a later human decision |
| 2026-07-14 | D011-R1 development-only campaign execution | D011-C2 established that the corrected largest-fold synthetic workload fits the reference laptop limits | The next scientific question required development-only Q01b/FQK execution, but locked splits and Gate 6 had to remain protected | Recorded D011-R1 as a one-campaign authority using the frozen D011 protocol, then completed the source-bound campaign and generated RFIG-026 through RFIG-029 | Valid exploratory negatives. The campaign read 39,000 development rows and zero calibration/final-test rows. Q01b had mean NRMSE 0.6612 versus C06 at 0.0068328 with zero qualifying regimes; FQK had AUROC/Brier/recall 0.7436/0.1561/0.1089 versus C02-T02 at 0.9134/0.1062/0.3233. Hardware/GPU, Gate 5 reinterpretation, and Gate 6 remain unauthorized |
| 2026-07-14 | D012 future-protocol discussion opened | D011-R1 produced valid negative QML evidence, but those negatives can still inform a future research discussion | Treating future ideas as active pipeline changes would become post-outcome rescue; treating the negatives as universal QML impossibility would overclaim | Opened a discussion-only D012 record with three candidates: task-informed local-observable projected kernels, class-sensitive feasibility kernels, and classical-first residual plus safety-filter hardening | No implementation, new experiment, refit, rerank, calibration/final-test read, hardware/GPU run, Gate 5 reinterpretation, or Gate 6 work is authorized. D013 is required before any successor protocol |
| 2026-07-14 | D013-C classical-first planning accepted | The project needs a future QML invention target, but D011-R1 showed the tested QML tracks were weaker than strong controls | Inventing a new QML method immediately would risk post-outcome architecture search; claiming NASA used a specific QML method would be unsupported without a cited source | Selected D012-C as the assistant-recommended planning path, added an invention-readiness ledger, and required every result to label useful invention signal versus prohibited rescue use | Planning-only. No implementation, experiment, refit, rerank, calibration/final-test read, hardware/GPU run, Gate 5 reinterpretation, or Gate 6 work is authorized. D014 is required for any executable successor |
| 2026-07-14 | D014-C classical-first freeze proposal accepted | D013-C selected the right direction, but implementation still needed a locked method and compute-admission boundary | Running code before freezing controls, metrics, and resource accounting would repeat the same post-outcome-search risk the project is avoiding | Locked CRES residual-cost hardening, CSAFE safety-filter hardening, required controls, metrics, conservative compute-admission requirement, and RFIG-032 through RFIG-035 planning | Freeze proposal only. No implementation, synthetic validation, development-data fitting, calibration/final-test read, hardware/GPU run, Gate 5 reinterpretation, QML invention claim, or Gate 6 work is authorized. D015 is required before implementation or synthetic validation |
| 2026-07-14 | D015-C implementation and synthetic validation accepted | D014-C froze the tracks and required RFIG-032 before executable work | Jumping to development rows would bypass compute admission and risk post-outcome rescue; implementing against synthetic arrays is the narrow next step | Added a source-bound RFIG-032 freeze map and authorized CRES/CSAFE implementation scaffolds plus synthetic-array validation only | No development-data fitting, calibration/final-test read, refit, rerank, hardware/GPU run, Gate 5 reinterpretation, QML invention claim, or Gate 6 work is authorized. D016 is required before clean-source compute admission |
| 2026-07-14 | D015-C synthetic-only scaffolds implemented | D015-C authorized only implementation and synthetic validation, so the first code had to be array-only and guard-checked | Letting helpers read project payloads or silently select thresholds on held-out rows would violate the D015 boundary | Added CRES/CSAFE synthetic utilities for residual targets, residual-cost metrics, training-only safety-threshold selection, held-out safety metrics, D015 scope guards, and invention-readiness labels | Synthetic validation only. No development-data fitting, calibration/final-test read, hardware/GPU run, Gate 5 reinterpretation, QML invention claim, or Gate 6 work is authorized |
| 2026-07-14 | D016-C clean-source synthetic compute preflight | D015-C completed the synthetic scaffolds, but development-data fitting still needed a resource and source-integrity boundary | Running CRES/CSAFE on development rows before compute admission would bypass the frozen laptop limits and make any stop ambiguous | Added a D016-C authority record, clean-source synthetic preflight runner, RFIG-033 generator, tests, and terminal evidence | PASS. The synthetic preflight projected 0.0179/250 CPU-core-hours, 0.000788/5 wall-days, 1.2207/20 GiB artifacts, 0.1713/24 GiB peak memory, 46.5275 GiB free disk after artifacts, and zero GPU-hours. RFIG-033 records the margins. No development-data fitting, calibration/final-test read, refit, retry, hardware/GPU run, Gate 5 reinterpretation, QML invention claim, quantum-advantage claim, or Gate 6 work is authorized; D017 is required before fitting |
| 2026-07-14 | D016-C1 A02 exact-RBF preflight correction | A pre-D017 audit found that D016-C did not include the D014-C required A02 exact classical RBF control in its synthetic workload | Opening development rows with an unbenchmarked required control would make the compute-admission claim incomplete | Added a D016-C1 authority record, A02 exact-RBF synthetic preflight runner, RFIG-036 generator, tests, and terminal evidence | PASS. The synthetic A02 preflight projected 0.0109/250 CPU-core-hours, 0.000438/5 wall-days, 1.2207/20 GiB artifacts, 0.2679/24 GiB peak memory, 46.5217 GiB free disk after artifacts, and zero GPU-hours. RFIG-036 records the correction. No development-data fitting, calibration/final-test read, refit, retry, hardware/GPU run, Gate 5 reinterpretation, QML invention claim, quantum-advantage claim, or Gate 6 work is authorized; D017 is required before fitting |
| 2026-07-14 | D017-C development-only classical-first campaign accepted | D016-C and D016-C1 both passed source-bound compute admission, so the next scientific step is development-only CRES/CSAFE evidence | Opening calibration/final-test or mission-loop work would overclaim beyond development evidence | Added D017-C authority, a source-bound development-only campaign runner, compact result outputs, and RFIG-034/RFIG-035 generators | One development-only campaign is authorized. Calibration/final-test reads, refit, rerank, retry, hardware/GPU run, Gate 5 reinterpretation, QML invention claim, quantum-advantage claim, mission-loop work, and Gate 6 remain unauthorized |

For RTC3 specifically, the qualified OEM predates the event by 15 hours 30
minutes 41 seconds. A separate post-RTC3 trajectory product was not substituted
because its mission-relative epoch, M50 frame realization, and eighth-column
semantics lack authoritative definitions and it remains quarantined under the
frozen data rules. This is a source-qualification limit, not a workstation
performance limit. Faster hardware or a longer run would not resolve it.

The Gate 3 COF episode is especially important for interpretation. The initial
cross-tool failure was real evidence under the then-executed configuration, but
its cause was an interface-format defect rather than insufficient CPU/GPU
capacity or a need to relax thresholds. The repair changed how the same frozen
constants were transmitted to GMAT. It did not change the Python dynamics,
force-model physics, validation windows, or acceptance limits. Both the failed
result and the repaired result remain part of the audit trail.

## 10. Ongoing update rule

After every computational phase, this methodology must be updated when any of
the following occurs:

1. measured hardware, driver, interpreter, or backend changes materially;
2. a formal job exceeds its predicted runtime, RAM, VRAM, thermal, or storage
   envelope;
3. a run crashes, stalls, pages, throttles, exhausts storage, or cannot resume;
4. a cross-tool, precision, serialization, path, or file-format defect changes
   the interpretation of a result;
5. work moves to external compute or a quantum backend;
6. an execution adaptation is introduced to finish a frozen experiment; or
7. a limitation remains unresolved and could affect what readers conclude.
8. a material experimental or methodological change requires a corresponding
   registry entry and reproducible visual under `artifacts/research_figures/`.

Each update records the observed problem, affected phase, measured impact,
attempted response, final status, evidence location, and whether any scientific
quantity changed. Resolved problems are not deleted. Unresolved problems remain
visible beside the results they qualify.

The public record should teach readers how the project behaved under real
constraints. It should not imply that the work proceeded without failed
attempts, and it should not imply that duplicating the reference laptop is the
correct way to continue the research.
