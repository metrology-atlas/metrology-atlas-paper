# The Metrology Atlas: paper

LaTeX source of the paper "The Metrology Atlas: describing recorded physiological data as a measurement system", which accompanies the atlas (vitaldb.metrology-atlas.org). Published as [arXiv:2610.29001](https://arxiv.org/abs/2610.29001).

Build: `latexmk -pdf main.tex` (pdflatex + BibTeX).

Numbers: every number in the paper that describes the dataset is a `\fact{id}`, defined in `facts/facts.tex`.
`python facts/make_facts.py --resolution ../vitaldb/vitaldb-resolution` regenerates `facts/facts.tex` and
`facts/facts.yaml` from the atlas file (built from `../metrology-atlas`, or pass the file's path); the YAML records
each fact's value, the atlas item it comes from, and the atlas commit and file hash. An undefined fact prints a red
?? in the PDF, and `make_arxiv.py` refuses it.

arXiv: `python make_arxiv.py` writes `arxiv/arxiv.tar.gz` (main.tex, main.bbl and the figures), checks that it
compiles on its own as arXiv compiles it, and writes the plain-text abstract and the comments line for the form.
It refuses while `\todo` notes or unresolved references remain (`--draft` builds anyway). `arxiv/` is git-ignored.

## Figures

| File | Made by |
|---|---|
| fig0-uncertainty.pdf | `figures/src/fig_uncertainty_concept.py figures/fig0-uncertainty.pdf` (illustrative widths) |
| fig1-sitemap.pdf, fig2-invertibility.pdf | `figures/src/*.jsx`, rendered with `figures/src/render.js` (React to SVG), then cairosvg to PDF |
| fig3-accuracy.pdf | vitaldb-bench `tools/time_source_accuracy_figure.py --paper out.png out.pdf` (landscape print layout) |
| fig4-timing-network.pdf | metrology-atlas `datasets/vitaldb/figures/timing-graph.svg`, cairosvg to PDF |
| fig5-sync-demo-1216.pdf | vitaldb-bench `tools/sync_demo.py --case 1216` |
| fig6-census.pdf | vitaldb-bench `tools/sync_error_census.py` |

Numbers in the text match the atlas at the archived snapshot cited in Section 9.

## Licence

Text and figures: CC BY 4.0. Figure scripts in `figures/src`: MIT. See `LICENSE`.
