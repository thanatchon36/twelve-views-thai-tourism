"""Project-wide configuration: paths, random seed and study period."""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"              # real <name>.csv, or the synthetic_<name>.csv fallback
PROCESSED = ROOT / "data" / "processed"  # metrics.json (generated, not committed)
PAPER = ROOT / "paper"
FIGURES = PAPER / "figures"              # generated figures (PDF for the paper, PNG for the web)
TABLES = PAPER / "tables"                # numbers.tex and table bodies written by analysis.py
DOCS = ROOT / "docs"
FONTS = Path(os.environ.get("THAI_FONT_DIR", ROOT / "fonts"))

REPO_URL = "https://github.com/thanatchon36/twelve-views-thai-tourism"
PAPER_URL = "https://thanatchon36.github.io/twelve-views-thai-tourism/paper/"
DATA_URL = "https://huggingface.co/datasets/thanatchon36/twelve-views-thai-tourism"

SEED = 2026                      # every random draw derives from this seed
YEARS = list(range(2010, 2026))  # study period, Gregorian calendar
LATEST_YEAR = YEARS[-1]

for _p in (RAW, PROCESSED, FIGURES, TABLES):
    _p.mkdir(parents=True, exist_ok=True)
