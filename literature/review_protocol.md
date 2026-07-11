# Systematic Scoping Review Protocol

Version: 0.2.0
Search cutoff for initial review: 2026-07-10  
Status: Gate 4 bounded search executed; full systematic update required before manuscript submission

The 2026-07-12 execution is recorded in `search_log.csv`,
`screening_log.csv`, `extraction_matrix.csv`, and
`docs/literature_synthesis.md`. OpenAlex query counts were obtained, but
metadata export was blocked by persistent HTTP 429 responses. Proposed
Deviation D002 requests acceptance of the complete NTRS/arXiv retrieval and
curated primary-source extraction for the Phase 1 freeze only. This execution
must not be described as the complete systematic review defined below.

## Objective

Map the strongest reproducible evidence for robust crewed-spacecraft
trajectory correction, classical ML guidance, QML regression and control,
quantum trajectory optimization, human-spaceflight constraints, and simulation
credibility.

The review will identify:

- what problem formulations are technically defensible;
- what public data and simulators are available;
- which classical baselines are necessary;
- which quantum methods are genuinely QML;
- which claims have hardware evidence;
- which methodological gaps OpenQFuel-Cislunar can address.

## Sources

Search public interfaces and accessible records from:

- NASA Technical Reports Server;
- NASA Standards and NASA mission pages;
- arXiv;
- Crossref;
- OpenAlex;
- NASA ADS;
- AIAA publications;
- Quantum journal;
- publisher and institutional repositories;
- official software repositories connected to included studies.

Search results, dates, query strings, and export files will be versioned. The
review will be updated before manuscript submission.

## Core search strings

S1:

    (spacecraft OR cislunar OR lunar OR Orion)
    AND ("trajectory correction" OR guidance OR "burn placement")
    AND (propellant OR "delta-v" OR fuel)
    AND (robust OR uncertainty OR dispersion)

S2:

    ("machine learning" OR "reinforcement learning" OR surrogate)
    AND (spacecraft OR cislunar OR "low thrust")
    AND (trajectory OR guidance OR control)

S3:

    ("quantum machine learning" OR "quantum kernel"
     OR "variational quantum" OR "quantum neural network")
    AND (regression OR reinforcement OR surrogate OR control)

S4:

    ("quantum annealing" OR QAOA OR QUBO)
    AND (spacecraft OR trajectory OR "space mission")

S5:

    (Artemis OR Orion)
    AND ("trajectory correction" OR navigation OR propulsion
         OR "crew schedule" OR ephemeris)

S6:

    ("human spaceflight" OR astronaut OR crewed)
    AND (acceleration OR sleep OR workload OR radiation)
    AND (standard OR constraint OR spacecraft)

S7:

    ("model credibility" OR "simulation validation"
     OR "verification and validation")
    AND (NASA OR spacecraft OR trajectory)

Exact syntax will be adapted to each database without changing the concepts.

## Date ranges

- QML and modern ML evidence: 2018 through 2026-07-10.
- Trajectory optimization and human-spaceflight standards: no strict lower
  bound when the source is seminal or currently authoritative.
- Mission status and software versions: current at retrieval.

## Inclusion criteria

- Primary research, authoritative technical standard, official mission data,
  or high-quality systematic or technical review.
- Relevant to at least one review cluster.
- Sufficient methodology to identify inputs, outputs, model, evaluation, and
  comparison.
- English full text or enough authoritative technical information to extract
  the required fields.
- Quantum studies must distinguish gate-based QML, annealing, quantum-inspired,
  and classical simulation.

## Exclusion criteria

- Marketing articles used as performance evidence.
- Opinion pieces without technical methods.
- Quantum-inspired classical algorithms described as quantum hardware results.
- Studies with unverifiable headline claims and no usable evaluation details.
- Duplicate reports of the same experiment, retaining the most complete
  version and linking companions.
- Generic optimization work with no transferable connection to the defined
  trajectory or surrogate problem.

## Screening

1. Deduplicate by DOI, title, author, and experiment.
2. Title and abstract screening.
3. Full-text or authoritative-record screening.
4. Record an exclusion reason at full-text stage.
5. Link papers, code, datasets, standards, and mission pages as one evidence
   family where appropriate.

The assistant performs screening and provides uncertain cases to the research
lead only when they alter scope or claims.

## Extraction fields

- evidence ID;
- citation and year;
- evidence type;
- mission and task;
- dynamics fidelity;
- objective and hard constraints;
- uncertainty model;
- input data and availability;
- classical algorithm;
- quantum algorithm class;
- qubits, encoding, ansatz, depth, shots, and backend;
- optimizer and hyperparameter procedure;
- split and leakage controls;
- classical baselines;
- primary metrics;
- uncertainty and statistical testing;
- hardware versus simulation;
- code and data availability;
- reported limitation;
- relevance to this protocol.

## Quality domains

Each source is assessed by domain rather than collapsed into one misleading
total score:

1. Data provenance.
2. Physics and mission fidelity.
3. Baseline fairness.
4. Split and leakage control.
5. Statistical uncertainty.
6. Quantum-resource reporting.
7. Hardware realism.
8. Reproducibility.
9. Claim calibration.

Ratings are strong, partial, weak, not applicable, or unclear, with a note.

## Synthesis

The review will produce:

- evidence map by method and mission task;
- comparison of problem formulations;
- public-data and simulator map;
- required classical baseline set;
- QML benchmark design implications;
- human-rated constraint map;
- identified novelty and non-novelty;
- unresolved evidence gaps.

No meta-analysis will combine incompatible tasks or metrics. Quantitative
synthesis will be used only for sufficiently comparable experiments.

