"""README assets in the night theme of the thainowcast repository -> docs/assets/.

banner.png   1680 x 624: the radial spiral of monthly arrivals (one turn per year, 2010-2025) in amber on
             a night sky, with the title. Drawn from the same data as Figure 3.
preview.png  the twelve views as a contact sheet, from the PNGs in paper/figures/.

Usage: ``python scripts/make_assets.py`` (or ``make assets``), after ``make figures``.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib import font_manager  # noqa: E402
from matplotlib.collections import LineCollection  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402
from scipy.interpolate import PchipInterpolator  # noqa: E402

from twelveviews.config import FIGURES, FONTS, ROOT  # noqa: E402
from twelveviews.loaders import load  # noqa: E402

OUT = ROOT / "docs" / "assets"
NIGHT, SKY, AMBER, PALE, EMBER, MUTED = "#03060d", "#0b1020", "#f5a623", "#ffe8a3", "#b0560f", "#9fb0d0"
VIEWS = [
    ("fig02_unit_chart", "Unit chart"), ("fig03_radial_spiral", "Radial spiral"),
    ("fig04_streamgraph", "Streamgraph"), ("fig05_ridgeline", "Ridgeline plot"),
    ("fig06_sankey", "Sankey diagram"), ("fig07_chord", "Chord diagram"),
    ("fig08_edge_bundling", "Edge bundling"), ("fig09_circle_packing", "Circle packing"),
    ("fig10_sunburst", "Sunburst"), ("fig11_beeswarm", "Beeswarm"),
    ("fig12_parallel_coordinates", "Parallel coordinates"), ("fig13_embedding", "Embedding map"),
]


def _font() -> str:
    files = sorted(Path(FONTS).glob("IBMPlexSansThai-*.ttf"))
    for f in files:
        font_manager.fontManager.addfont(str(f))
    return "IBM Plex Sans Thai" if files else "DejaVu Sans"


def banner(family: str) -> Path:
    m = load("arrivals_monthly")
    year = m.month.str[:4].astype(int).to_numpy()
    month = m.month.str[5:7].astype(int).to_numpy() - 1
    v = m.arrivals.to_numpy(dtype=float)
    r = 0.18 + 0.82 * v / v.max()
    # smooth the spiral: monotone cubic through every monthly point (no overshoot), 16 steps per month
    k = np.arange(len(v), dtype=float)
    kk = np.linspace(0, len(v) - 1, 16 * (len(v) - 1) + 1)
    rr = PchipInterpolator(k, r)(kk)
    tt = 2 * np.pi * (kk + 0.5) / 12
    yy = year.min() + (kk + month[0]) / 12

    fig = plt.figure(figsize=(16.8, 6.24), dpi=100, facecolor=NIGHT)
    bg = fig.add_axes([0, 0, 1, 1])
    bg.axis("off")
    bg.imshow(np.linspace(0, 1, 256)[None, :], extent=[0, 1, 0, 1], aspect="auto",
              cmap=LinearSegmentedColormap.from_list("sky", [NIGHT, SKY]), transform=bg.transAxes)
    rng = np.random.default_rng(12)                                 # a few faint stars
    bg.scatter(rng.uniform(0, 1, 140), rng.uniform(0, 1, 140), s=rng.uniform(0.2, 2.2, 140),
               color=PALE, alpha=0.35, linewidths=0, transform=bg.transAxes)

    ax = fig.add_axes([0.575, 0.03, 0.40, 0.94], projection="polar", facecolor="none")
    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1)
    for j in range(12):                                              # twelve month spokes, twelve views
        ax.plot([2 * np.pi * j / 12] * 2, [0.12, 1.06], color=MUTED, lw=0.5, alpha=0.25)
    pts = np.column_stack([tt, rr])
    segs = np.stack([pts[:-1], pts[1:]], axis=1)
    age = (yy[1:] - yy.min()) / (yy.max() - yy.min())
    cmap = LinearSegmentedColormap.from_list("ember", ["#3a2a12", EMBER, AMBER, PALE])
    ax.add_collection(LineCollection(segs, colors=cmap(age), linewidths=0.8 + 1.8 * age, capstyle="round"))
    peak = np.floor(yy) == 2019
    ax.plot(tt[peak], rr[peak], color=PALE, lw=2.8, solid_capstyle="round")
    ax.set_ylim(0, 1.08)
    ax.axis("off")

    fig.text(0.055, 0.70, "TWELVE VIEWS OF", color=MUTED, family=family, fontsize=19, fontweight="medium")
    fig.text(0.052, 0.50, "Thai Tourism", color=PALE, family=family, fontsize=66, fontweight="bold")
    fig.text(0.056, 0.38, "A data-shape-driven framework for visual analysis,", color=MUTED,
             family=family, fontsize=19)
    fig.text(0.056, 0.31, "evaluated by planted-structure recovery", color=MUTED, family=family, fontsize=19)
    fig.text(0.056, 0.13, "Monthly arrivals 2010–2025, one turn per year  ·  synthetic data",
             color=AMBER, family=family, fontsize=13, alpha=0.9)
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / "banner.png", facecolor=NIGHT)
    plt.close(fig)
    return OUT / "banner.png"


def preview(family: str) -> Path:
    cols, rows = 4, 3
    fig = plt.figure(figsize=(16, 9.6), dpi=100, facecolor=NIGHT)
    for i, (name, label) in enumerate(VIEWS):
        c, rr = i % cols, i // cols
        x0, y0, w, h = 0.02 + c * 0.245, 0.68 - rr * 0.325, 0.225, 0.27
        plate = fig.add_axes([x0, y0, w, h])
        plate.set_facecolor("white")
        img = plt.imread(FIGURES / f"{name}.png")
        plate.imshow(img, interpolation="lanczos")
        plate.set_xticks([])
        plate.set_yticks([])
        for s in plate.spines.values():
            s.set_color("#2b3c5c")
        plate.set_aspect("equal", adjustable="datalim")
        fig.text(x0, y0 + h + 0.008, f"Figure {i + 2}  \u00b7  {label}", color=PALE, family=family, fontsize=12,
                 fontweight="medium")
    fig.savefig(OUT / "preview.png", facecolor=NIGHT)
    plt.close(fig)
    return OUT / "preview.png"


def main() -> None:
    family = _font()
    for p in (banner(family), preview(family)):
        print(f"wrote {p.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
