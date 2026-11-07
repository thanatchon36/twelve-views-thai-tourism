# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- Zenodo concept DOI [10.5281/zenodo.24035604](https://doi.org/10.5281/zenodo.24035604) in `CITATION.cff`, the README badge, the web
  reader and the Hugging Face dataset card.

## [0.1.0] - 2026-11-07

### Added
- Ten synthetic datasets with planted structure (`data/raw/synthetic_*.csv`, `make synthetic`): annual and
  monthly arrivals by market, length of stay, market profiles, origin-destination-style flows, onward travel,
  77 provinces, co-visitation, a three-level spending hierarchy and a 1,200-respondent persona survey.
- Loader that reads a real `data/raw/<name>.csv` when present and falls back to the synthetic file with a
  warning; `docs/data_sources.md` lists the columns and candidate real sources for each dataset.
- Analysis of every reported number and of planted-structure recovery (E1-E8), written as LaTeX macros and table
  bodies to `paper/tables/` and as `data/processed/metrics.json`.
- The twelve figures (`make figures`): unit chart, radial spiral, streamgraph, ridgeline plot, Sankey diagram,
  chord diagram, hierarchical edge bundling, circle packing, sunburst, beeswarm, parallel coordinates and a
  t-SNE embedding map.
- The working paper `paper/paper.pdf`, typeset from `paper/paper.tex` with tectonic (XeLaTeX, 11pt A4,
  Libertinus), and its web reader `docs/paper/`, built with pandoc and served on GitHub Pages at
  <https://thanatchon36.github.io/twelve-views-thai-tourism/paper/>.
- `make arxiv`: self-contained arXiv source bundle `paper/arxiv.tar.gz` (XeLaTeX, with `paper.bbl`), checked to
  compile on its own, plus the title, abstract and comments for the submission form.
- Dataset on Hugging Face,
  [`thanatchon36/twelve-views-thai-tourism`](https://huggingface.co/datasets/thanatchon36/twelve-views-thai-tourism):
  the eleven synthetic tables, the manifest and the computed metrics.
- README banner and preview (`make assets`), CI on GitHub Actions, `CITATION.cff` and Zenodo metadata.
