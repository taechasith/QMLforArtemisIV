# QMLforArtemisIV Full Paper

This directory is a self-contained Springer LNCS/Proceedings manuscript package.
It uses the supplied `llncs.cls` and `splncs04.bst` files from
`paper/LaTeX2e+Proceedings+Template`, so it can be uploaded directly to a new
Overleaf project without an external template dependency.

## Contents

- `main.tex`: complete manuscript source.
- `references.bib`: bibliography used by the manuscript.
- `tables/`: LaTeX tables included by `main.tex`.
- `figures/`: the exact registered PNG figures used by `main.tex`.
- `results_tables/`: copied frozen CSV evidence and the full figure registry.
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
