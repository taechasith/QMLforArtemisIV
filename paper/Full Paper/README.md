# QMLforArtemisIV Full Paper

This directory is a self-contained Springer LNCS/Proceedings manuscript package.
It uses the supplied `llncs.cls` and `splncs04.bst` files from
`paper/LaTeX2e+Proceedings+Template`, so it can be uploaded directly to a new
Overleaf project without an external template dependency.

## Contents

- `main.tex`: complete manuscript source.
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
- `QMLforArtemisIV_full_paper.pdf`: locally compiled final PDF.
- `llncs.cls` and `splncs04.bst`: Springer proceedings style files.

## Build in Overleaf

1. Create a blank project and upload the complete contents of this directory.
2. Set `main.tex` as the main document.
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

The author metadata identifies Taechasith Kangkhuntod of the University of the
Thai Chamber of Commerce. The acknowledgement remains a deliberate placeholder
for advisor review and contribution wording before submission.
