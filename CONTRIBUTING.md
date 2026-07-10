# Contributing

OpenQFuel-Cislunar welcomes reproducibility fixes, source corrections,
astrodynamics validation, fair classical baselines, quantum-model
implementations, uncertainty analysis, human-factors review, and negative
results.

## Principles

1. Do not introduce a mission parameter without a source or explicit
   assumption label.
2. Do not tune on the locked mission test set.
3. Do not remove failed optimizer cases merely to improve model metrics.
4. Do not describe quantum simulation as hardware advantage.
5. Preserve units, frames, time systems, source versions, seeds, and checksums.
6. Add a test for every fixed scientific or software defect where practical.
7. Record protocol-affecting changes in docs/decision_log.md.

## Proposed workflow

1. Open an issue describing the scientific question or defect.
2. Identify affected protocol, source, configuration, or result.
3. Add or update tests.
4. Run the repository test suite.
5. Submit a focused pull request with provenance and expected impact.

Research claims require review of the underlying result files and cannot be
approved from a figure screenshot alone.

