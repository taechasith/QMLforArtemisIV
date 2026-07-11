# Research Figure and Change-Evidence Policy

Version: 0.1.0
Effective: 2026-07-12
Authority: Human research lead
Status: Active for all work after Gate 4 acceptance

## Purpose

Every material experimental result, failed attempt, protocol repair,
performance bottleneck, model comparison, and claim-bearing methodological
change must leave a reproducible visual record suitable for the research paper
or its supplementary material. Figures supplement, but never replace, the
machine-readable data and written audit trail.

Routine code formatting and non-scientific text edits do not require a graph.
They remain visible in Git. A change requires a figure when it alters or
reveals data coverage, validity, uncertainty, numerical behavior, compute cost,
model behavior, statistical conclusions, or the interpretation boundary.

## Required workflow

1. Write machine-readable source data before plotting.
2. Assign a stable figure ID in `artifacts/research_figures/figure_registry.csv`.
3. Generate PNG and SVG from a versioned script; do not edit either image manually.
4. Record source paths, generator path, caption, intended paper section, and claim boundary.
5. Record SHA-256 and byte size for every generated image.
6. Label exploratory, failed, invalid, calibration-only, and final evidence distinctly.
7. Preserve superseded figures and their source data when they explain a research decision.
8. Regenerate the complete registry before each research commit and manuscript release.

## Visual standards

- Use explicit units, sample counts, uncertainty intervals, and split/fidelity labels.
- Use colorblind-safe colors plus shape, hatching, or direct labels where practical.
- Avoid truncated axes unless the truncation is essential and visibly disclosed.
- Show distributions or uncertainty, not only favorable point estimates.
- Keep ID and OOD results separate.
- Keep development, calibration, and final-test evidence visually distinct.
- Mark invalid or pre-repair evidence in the title and caption.
- Export at least 300 DPI PNG plus vector SVG.
- Never plot a locked final-test value before its authorized one-time evaluation.

## Minimum paper figure set

The registry must eventually cover:

- gate and protocol timeline;
- source/data coverage and exclusion flow;
- simulator verification, convergence, and independent-tool agreement;
- scenario coverage, uncertainty strata, feasibility, and nonconvergence;
- generator runtime, memory, and throughput on the reference laptop;
- pre/post repair comparisons for every result-changing defect;
- classical and QML learning curves;
- seed distributions and paired model differences;
- calibration, ID/OOD, finite-shot, noise, and ablation results;
- mission regret, safety gates, tail risk, fallback, and compute deadline;
- negative and inconclusive findings needed to prevent selective reporting.

## Claim boundary

A graph is not automatically valid research evidence. Its registry status and
caption determine whether it is a diagnostic, failed-attempt record,
development result, calibration result, or final result. Pre-D003 scenario
figures are retained only to document why the generator was repaired and must
not appear as model-performance evidence.
