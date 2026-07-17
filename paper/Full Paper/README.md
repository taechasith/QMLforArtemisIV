# QMLforArtemisIV Camera-Ready and Review Papers

This directory is a self-contained Springer LNCS/Proceedings manuscript package.
It uses the supplied `llncs.cls` and `splncs04.bst` files from
`paper/LaTeX2e+Proceedings+Template`, so it can be uploaded directly to a new
Overleaf project without an external template dependency.

## Abstract

This paper evaluates whether simulated quantum machine-learning (QML) kernels
add predictive value to a public-data benchmark for crewed Earth-Moon
trajectory-correction planning. The target is robust total correction delta-v
under uncertainty. The protocol froze data transformations, grouped development
folds, decision thresholds, and the calibration/final-test boundary before
outcomes. A physics-residual classical control and matched alternatives were
evaluated under the same development-only conditions. The physics-residual
control consistently outperformed the tested QML paths: Q01's mean normalized
root-mean-square error (NRMSE) was 0.6466 versus 0.0087 for C06 (lower is
better). The projected-kernel, feasibility-screening, and bounded successor
studies also did not satisfy their prespecified advancement criteria. This is a
valid, task-specific negative result, not evidence that QML cannot be useful
elsewhere. For human-AI decision support in space, the contribution is an
evidence design that makes model scope, null results, uncertainty, and human
authorization visible rather than converting a model score into an automation
recommendation. The study claims no quantum advantage, propellant saving,
flight readiness, hardware performance, or QML invention.

## Contents

- `main.tex`: final named camera-ready manuscript source, including author,
  institution, acknowledgements, and camera-ready PDF metadata.
- `submission.tex`: anonymous SpaceCHI double-blind submission wrapper. It uses
  the concise `sections/spacechi_front.tex` and `sections/spacechi_back.tex` so
  the review manuscript is 15 pages before references, while sharing the full
  methods, results, tables, and evidence figures with the named manuscript.
- `references.bib`: bibliography used by the manuscript.
- `tables/`: source tables retained with the package; the manuscript typesets
  its non-duplicative result table while the remaining tables support review.
- `figures/`: the exact registered PNG figures used by `main.tex`.
- `results_tables/`: copied frozen CSV evidence and the full figure registry.
- `REVIEWER_RESPONSE_DRAFT.md`: a scoped draft response to the structural
  revision comments; update its page and line references after a final
  submission build.
- `sections/A_reproducibility.tex` and `sections/B_literature_audit.tex`:
  supplementary reviewer notes retained outside the 20-page proceedings
  manuscript; their essential scope statements are reflected in the main text.
- `QMLforArtemisIV_full_paper.pdf`: locally compiled camera-ready manuscript
  PDF. This is the full-paper version for publication after acceptance.
- `QMLforArtemisIV_spacechi_submission.pdf`: locally compiled anonymous
  submission PDF.
- `llncs.cls` and `splncs04.bst`: Springer proceedings style files.

## Build in Overleaf

1. Create a blank project and upload the complete contents of this directory.
2. Set `submission.tex` as the main document for the double-blind SpaceCHI
   review submission, or `main.tex` for the named/camera-ready manuscript.
3. Use pdfLaTeX and compile twice after BibTeX runs. Overleaf normally handles
   this sequence automatically.

For a local manual build, run:

```text
pdflatex main
bibtex main
pdflatex main
pdflatex main
```

## Evidence boundary

The manuscript reports a closed public-data, development-only benchmark. It
does not claim quantum advantage, mission-loop validity, flight readiness,
propellant savings, NASA approval, hardware performance, a final-test result,
or a new QML invention. Gate 6 remains unauthorized.

`main.tex` identifies Taechasith Kangkhuntod of the University of the Thai
Chamber of Commerce and includes the personal acknowledgements. The
double-blind `submission.tex` build replaces author and institution metadata
with anonymous placeholders and suppresses acknowledgements.
