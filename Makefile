PY ?= .venv/bin/python

.PHONY: setup fonts synthetic analysis figures paper web arxiv assets poster test all clean

setup:          ## create venv and install the package (needs uv)
	uv venv .venv --python 3.12
	uv pip install --python .venv/bin/python -e ".[dev]"

fonts:          ## IBM Plex Sans Thai for the figures (SIL OFL); without it they fall back to DejaVu Sans
	bash scripts/get_fonts.sh

synthetic:      ## (re)generate the ten synthetic datasets. NEVER a substitute for real data
	$(PY) -m twelveviews.cli synthetic

analysis:       ## metrics, planted-structure recovery, LaTeX macros and tables
	$(PY) -m twelveviews.cli analysis

figures:        ## the twelve figures -> paper/figures/ (PDF for the paper, PNG for the web)
	$(PY) -m twelveviews.cli figures

paper:          ## build paper/paper.pdf (tectonic) and the web reader docs/paper/ (pandoc)
	$(PY) -m twelveviews.cli paper
	$(PY) -m twelveviews.cli web

web:            ## web reader only -> docs/paper/index.html (pandoc; copies the current paper.pdf)
	$(PY) -m twelveviews.cli web

arxiv: paper    ## arXiv source bundle -> paper/arxiv.tar.gz
	$(PY) scripts/arxiv_bundle.py

assets:         ## README banner and preview -> docs/assets/
	$(PY) scripts/make_assets.py

poster:         ## LinkedIn poster (4:5, 2160 x 2700) -> docs/assets/linkedin_poster.png; post text in docs/linkedin_post.md
	$(PY) scripts/make_linkedin_poster.py

test:
	$(PY) -m pytest -q

all: analysis figures paper

clean:
	rm -rf data/processed/* paper/paper.pdf paper/paper.aux paper/paper.bbl paper/paper.blg paper/paper.log paper/paper.out paper/arxiv paper/arxiv.tar.gz
