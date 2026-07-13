# D013-C Classical-First Protocol Planning

Version: 0.1.0
Decision: D013-C
Protocol: P001
Prepared: 2026-07-14
Accepted: 2026-07-14
Status: Planning-only accepted; no experiment authorized

## Decision

The assistant selected D012-C as the recommended next decision under the human
research lead's instruction to proceed by choosing the scientifically strongest
path and committing it. D013-C opens planning for classical-first residual and
safety-filter hardening before any new QML invention phase.

D013-C does not authorize implementation, refit, rerank, retry, calibration
access, final-test access, hardware/GPU execution, Gate 5 reinterpretation,
quantum-advantage claims, or Gate 6. D014 is required before any executable
successor work.

## Long-Term QML Invention Goal

The long-term goal remains to invent a new QML method that works better than
the QML variants tested here and can beat the strongest documented
NASA-relevant and repository classical baselines under fair locked-split tests.
Scientific correctness has priority over invention speed.

The repository must not claim that NASA used a specific QML method unless a
cited public source identifies that method. Until such evidence exists,
comparisons are to NASA-relevant mission-design baselines, public NASA-derived
constraints, and the strongest classical controls in this repository.

Every result must now label what it teaches for the future invention process:
which signal is useful, which failure mode it exposes, which control must be
beaten, and which use is prohibited as post-outcome rescue.

## Why Classical-First Comes Before Inventing New QML

D011-R1 found that both near-term QML tracks were weaker than strong classical
controls. Q01b missed C06 by a wide NRMSE gap and had zero qualifying
dequantization regimes. FQK underperformed C02-T02 on AUROC, Brier, and recall.

Inventing a new QML method immediately from those outcomes would risk
post-outcome architecture search. D013-C instead hardens the classical residual
and safety-filter baselines first. That gives the later invented QML model a
clearer and stronger target.

## Planning Scope

Allowed under D013-C:

- Define protocol requirements for stronger residual-cost controls.
- Define protocol requirements for stronger feasibility and safety-filter
  controls.
- Map existing results into invention-readiness labels.
- Identify the controls and diagnostics that any later QML invention must beat.

Prohibited under D013-C:

- New model implementation.
- Development-data fitting.
- Calibration or final-test reads.
- Hardware or GPU execution.
- Gate 5 reinterpretation.
- Gate 6 work.

## Baseline Hardening Targets

For residual cost prediction, D014 should consider physics-residual controls,
C06-T17, A02 exact classical RBF, random-feature RBF, and compressed MLP. It
must freeze fold-local preprocessing, compute budget, residual definitions, and
regime diagnostics before fitting anything.

For feasibility and safety filtering, D014 should consider C02-T02, calibrated
logistic safety heads, class-weighted tree ensembles, and conformal or quantile
safety thresholds. It must freeze threshold selection, false-negative priority,
calibration diagnostics, and mission-safety non-inferiority boundaries before
fitting anything.

## Next Decision

D014-C has been accepted as a freeze proposal for CRES residual-cost hardening
and CSAFE safety-filter hardening. It remains non-executable. D015 is required
before implementation or synthetic validation, and Gate 6 remains unauthorized.
