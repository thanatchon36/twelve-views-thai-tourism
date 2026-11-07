"""Project-wide configuration: paths, random seed and study period."""
from pathlib import Path
import os

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
FIGURES = ROOT / "figures"
RESULTS = ROOT / "results"
PAPER = ROOT / "paper"
GENERATED = PAPER / "generated"
FONTS = Path(os.environ.get("THAI_FONT_DIR", ROOT / "fonts"))

SEED = 2026                      # every random draw derives from this seed
YEARS = list(range(2010, 2026))  # study period, Gregorian calendar
LATEST_YEAR = YEARS[-1]

for _p in (DATA, FIGURES, RESULTS, GENERATED):
    _p.mkdir(parents=True, exist_ok=True)
