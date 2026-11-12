# The Metrology Atlas: paper

LaTeX source of the paper "The Metrology Atlas: describing clinical time-series data as a measurement system", which accompanies the atlas (vitaldb.metrology-atlas.org). Published as [arXiv:2610.29001](https://arxiv.org/abs/2610.29001).

Build: `latexmk -pdf main.tex` (pdflatex + BibTeX).

Review copy (a red note under the date; the normal build has none):
`latexmk -pdf -jobname=review -pdflatex="pdflatex %O '\def\draftnote{Draft for co-authors, DATE. Not for circulation.}\input{%S}'" main.tex`
writes `review.pdf`; keep shared copies in `review/` (git-ignored).

Numbers: every number in the paper that describes the dataset is a `\fact{id}`, defined in `facts/facts.tex`.
`python facts/make_facts.py --resolution ../vitaldb/vitaldb-resolution` regenerates `facts/facts.tex` and
`facts/facts.yaml` from the atlas file (built from `../metrology-atlas`, or pass the file's path); the YAML records
each fact's value, the atlas item it comes from, and the atlas commit and file hash. An undefined fact prints a red
?? in the PDF, and `make_arxiv.py` refuses it.

arXiv: `python make_arxiv.py` writes `arxiv/arxiv.tar.gz` (main.tex, main.bbl and the figures), checks that it
compiles on its own as arXiv compiles it, and writes the plain-text abstract and the comments line for the form.
It refuses while `\todo` notes or unresolved references remain (`--draft` builds anyway). `arxiv/` is git-ignored.

## Figures

| Figure | File | Made by |
|---|---|---|
| 1 | fig1-concept-hr.pdf | metrology-atlas `tools/fig_concept_hr.py ATLAS_REPO OUT` (worked example: heart rate) |
| 2 | fig2-invertibility.pdf | `figures/src/fig2-invertibility.jsx`, rendered with `figures/src/render.js` (React to SVG), then cairosvg to PDF |
| 3 | fig3-urine-heaping.pdf | metrology-atlas `tools/fig_urine_heaping.py RESOLUTION_REPO RELEASE --summary SUMMARY.json OUT` (worked example: urine output) |
| 4 | fig4-bias-uncertainty.pdf | `figures/src/fig_bias_uncertainty.py ATLAS_REPO figures/fig4-bias-uncertainty.pdf figures/fig6-corrected-uncertainty.pdf` |
| 5 | fig5-timing-network.pdf | metrology-atlas `python -m metrology_atlas graph datasets/vitaldb --out fig5.svg --print` (the site's timing graph in its print layout), then cairosvg to PDF with the Inter font installed |
| 6 | fig7-ppg-correction-steps.pdf | vitaldb-bench `tools/ppg_correction_steps_figure.py --scan check_rebuilt6.jsonl --beats scan_full --fit fit.jsonl --chain-delay pleth-chain-delay.yaml --case 5328 --out OUT` (physiosync on the path) (saved outputs of the PLETH correction's checks) |
| 7 | fig6-corrected-uncertainty.pdf | as Figure 4 |

Numbers in the text match the atlas at the archived snapshot cited in Section 7.

## Licence

Text and figures: CC BY 4.0. Figure scripts in `figures/src`: MIT. See `LICENSE`.
