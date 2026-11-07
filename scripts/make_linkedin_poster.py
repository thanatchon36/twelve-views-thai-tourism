"""Portrait LinkedIn poster (4:5, 2160 x 2700 px) for the working paper -> docs/assets/linkedin_poster.png.

Night theme of the README banner. The twelve figures are the paper's own PNGs, laid out one row per research
question; the recovery numbers are read from data/processed/metrics.json, so the poster cannot disagree with the
paper. Run ``make all`` first.

Usage: ``python scripts/make_linkedin_poster.py`` (or ``make poster``).
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib import font_manager  # noqa: E402
from matplotlib.collections import LineCollection  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402
from matplotlib.patches import FancyBboxPatch, Rectangle  # noqa: E402
from scipy.interpolate import PchipInterpolator  # noqa: E402

from twelveviews.config import FIGURES, FONTS, PROCESSED, ROOT  # noqa: E402
from twelveviews.loaders import load  # noqa: E402

OUT = ROOT / "docs" / "assets" / "linkedin_poster.png"
W, H, DPI = 2160, 2700, 200                       # pixels; 10.8 x 13.5 in at 200 dpi
PT = 72 / DPI                                      # points per pixel: every size below is in pixels
M = 110                                            # side margin
NIGHT, SKY, AMBER, PALE, EMBER, MUTED, LINE = "#03060d", "#0b1020", "#f5a623", "#ffe8a3", "#b0560f", "#9fb0d0", "#2b3c5c"
INK = "#e8ecf4"
# the paper's RQ colours (Figure 1), lifted for a dark ground
RQ_COLORS = ["#5b9bea", "#3cc4c4", "#e2636c", "#a97dd0"]
CONCEPT_DOI = "10.5281/zenodo.24035604"

ROWS = [
    ("RQ1", "Who visits,\nand when?", [("fig02_unit_chart", "Unit chart"), ("fig03_radial_spiral", "Radial spiral"),
                                       ("fig04_streamgraph", "Streamgraph"), ("fig05_ridgeline", "Ridgeline plot")]),
    ("RQ2", "Where do\nvisitors go?", [("fig06_sankey", "Sankey diagram"), ("fig07_chord", "Chord diagram"),
                                        ("fig08_edge_bundling", "Edge bundling")]),
    ("RQ3", "Where does\nthe money go?", [("fig09_circle_packing", "Circle packing"), ("fig10_sunburst", "Sunburst"),
                                           ("fig11_beeswarm", "Beeswarm")]),
    ("RQ4", "What kinds of\ntravellers?", [("fig12_parallel_coordinates", "Parallel coordinates"),
                                           ("fig13_embedding", "t-SNE embedding map")]),
]


def font() -> str:
    files = sorted(Path(FONTS).glob("IBMPlexSansThai-*.ttf"))
    for f in files:
        font_manager.fontManager.addfont(str(f))
    if not files:
        print("note: IBM Plex fonts not found (make fonts); falling back to DejaVu Sans")
    return "IBM Plex Sans Thai" if files else "DejaVu Sans"


FAMILY = font()


def text(ax, x, y, s, px, color=INK, weight="regular", ha="left", va="baseline", **kw):
    return ax.text(x, y, s, fontsize=px * PT, color=color, family=FAMILY, fontweight=weight, ha=ha, va=va,
                   parse_math=False, **kw)


def spaced(s: str) -> str:
    """Letter-spaced capitals for kickers."""
    return "  ".join(" ".join(w) for w in s.upper().split())


def spiral(fig, rect, alpha):
    """The banner's spiral: monthly arrivals 2010-2025, one turn per year, smoothed without overshoot."""
    m = load("arrivals_monthly")
    year = m.month.str[:4].astype(int).to_numpy()
    month = m.month.str[5:7].astype(int).to_numpy() - 1
    v = m.arrivals.to_numpy(dtype=float)
    r = 0.18 + 0.82 * v / v.max()
    k = np.arange(len(v), dtype=float)
    kk = np.linspace(0, len(v) - 1, 16 * (len(v) - 1) + 1)
    rr = PchipInterpolator(k, r)(kk)
    tt = 2 * np.pi * (kk + 0.5) / 12
    yy = year.min() + (kk + month[0]) / 12
    ax = fig.add_axes(rect, projection="polar", facecolor="none")
    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1)
    for j in range(12):
        ax.plot([2 * np.pi * j / 12] * 2, [0.12, 1.06], color=MUTED, lw=0.5, alpha=0.18 * alpha)
    pts = np.column_stack([tt, rr])
    age = (yy[1:] - yy.min()) / (yy.max() - yy.min())
    cmap = LinearSegmentedColormap.from_list("ember", ["#3a2a12", EMBER, AMBER, PALE])
    ax.add_collection(LineCollection(np.stack([pts[:-1], pts[1:]], axis=1), colors=cmap(age),
                                     linewidths=0.6 + 1.6 * age, alpha=alpha, capstyle="round"))
    ax.set_ylim(0, 1.08)
    ax.axis("off")


def main() -> None:
    mt = json.loads((PROCESSED / "metrics.json").read_text(encoding="utf-8"))
    fig = plt.figure(figsize=(W / DPI, H / DPI), dpi=DPI, facecolor=NIGHT)

    # night sky
    bg = fig.add_axes([0, 0, 1, 1])
    bg.axis("off")
    bg.imshow(np.linspace(0, 1, 256)[:, None], extent=[0, 1, 0, 1], aspect="auto", transform=bg.transAxes,
              cmap=LinearSegmentedColormap.from_list("sky", [SKY, NIGHT, NIGHT, SKY]))
    rng = np.random.default_rng(12)
    bg.scatter(rng.uniform(0, 1, 220), rng.uniform(0, 1, 220), s=rng.uniform(0.2, 2.0, 220), color=PALE,
               alpha=0.28, linewidths=0, transform=bg.transAxes)

    spiral(fig, [0.61, 0.758, 0.40, 0.235], alpha=0.95)   # upper right, clear of the gallery

    ax = fig.add_axes([0, 0, 1, 1], facecolor="none")     # pixel canvas: x right, y down
    ax.set_xlim(0, W)
    ax.set_ylim(H, 0)
    ax.axis("off")

    def width(t) -> float:
        fig.canvas.draw()
        return t.get_window_extent().transformed(ax.transData.inverted()).width

    # ---------------------------------------------------------------- header
    text(ax, M, 100, spaced("Working paper · November 2026"), 25, AMBER, "medium")
    ax.plot([M, 1250], [128, 128], color=AMBER, lw=1.2, alpha=0.55)
    text(ax, M, 228, "TWELVE VIEWS OF", 46, MUTED, "medium")
    text(ax, M - 6, 390, "Thai Tourism", 172, PALE, "bold")
    for j, line in enumerate([
        "Bar and line charts flatten everything tourism data can be: cycles, flows,",
        "hierarchies, networks and traveller profiles. This framework picks a view",
        "for the shape of each question, then tests whether it shows what it claims.",
    ]):
        text(ax, M, 470 + j * 46, line, 33, INK)
    x = M
    for i, c in enumerate(["4 questions", "10 datasets", "12 views", "1 command"]):
        x += width(text(ax, x, 630, c, 31, AMBER if i % 2 == 0 else PALE, "semibold")) + 24
        if i < 3:
            text(ax, x, 630, "·", 31, MUTED)
            x += 38

    # ---------------------------------------------------------------- layout budget (bottom up)
    author_y = H - 52
    box_h = 196
    box_y = author_y - 50 - box_h
    strip_h = 292
    strip_y = box_y - 44 - strip_h
    g0, g1 = 680, strip_y - 26                         # the gallery lives between these

    # ---------------------------------------------------------------- gallery: one row per research question
    label_w, gap, pad, row_gap = 300, 20, 8, 26
    x0 = M + label_w
    avail = W - M - x0
    rows = []
    for rq, question, views in ROWS:
        imgs = [plt.imread(FIGURES / f"{name}.png") for name, _ in views]
        ars = [im.shape[1] / im.shape[0] for im in imgs]
        inner = avail - (len(views) - 1) * gap - 2 * pad * len(views)
        rows.append((rq, question, views, imgs, ars, min(inner / sum(ars), 420)))
    budget = g1 - g0 - len(rows) * (2 * pad + row_gap) + row_gap
    natural = sum(r[-1] for r in rows)
    scale = min(1.0, budget / natural)
    y = g0
    for (rq, question, views, imgs, ars, h), color in zip(rows, RQ_COLORS):
        h *= scale
        ax.add_patch(Rectangle((M, y), 7, h + 2 * pad, color=color, lw=0))
        text(ax, M + 30, y + 50, rq, 48, color, "bold")
        for j, line in enumerate(question.split("\n")):
            text(ax, M + 30, y + 98 + j * 36, line, 29, INK)
        for j, (_, label) in enumerate(views):          # the idioms, in the order they appear
            text(ax, M + 30, y + 98 + 2 * 36 + 14 + j * 30, label, 22, MUTED, "medium")
        x = x0
        for im, ar in zip(imgs, ars):
            w = h * ar
            ax.add_patch(FancyBboxPatch((x, y), w + 2 * pad, h + 2 * pad,
                                        boxstyle="round,pad=0,rounding_size=12", fc="white", ec=LINE, lw=1))
            ax.imshow(im, extent=[x + pad, x + pad + w, y + pad + h, y + pad], interpolation="lanczos", zorder=3)
            x += w + 2 * pad + gap
        y += h + 2 * pad + row_gap
    ax.set_xlim(0, W)
    ax.set_ylim(H, 0)

    # ---------------------------------------------------------------- recovery strip
    y = strip_y
    text(ax, M, y + 20, spaced("Planted in the data → recovered by the views"), 25, AMBER, "medium")
    ax.plot([M, W - M], [y + 44, y + 44], color=LINE, lw=1.2)
    tiles = [
        (f"r = {mt['rec_season_r']:.3f}", "seasonal profile", "radial spiral"),
        (f"{mt['rec_stay_mae']:.2f} nights", "error in median\nlength of stay", "ridgeline plot"),
        (f"{mt['rec_dest_mae']:.2f} pp", "error in destination\npreferences", "Sankey diagram"),
        (f"ARI {mt['seg_ari']:.2f}", "six traveller personas\nfound again", "embedding map"),
    ]
    tw = (W - 2 * M) / 4
    for i, (big, what, view) in enumerate(tiles):
        tx = M + i * tw
        text(ax, tx, y + 138, big, 76, AMBER, "bold")
        for j, line in enumerate(what.split("\n")):
            text(ax, tx, y + 190 + j * 36, line, 28, INK)
        text(ax, tx, y + 190 + 2 * 36 + 4, view, 23, MUTED, "medium")

    # ---------------------------------------------------------------- footer
    ax.add_patch(FancyBboxPatch((M - 22, box_y), W - 2 * M + 44, box_h, boxstyle="round,pad=0,rounding_size=22",
                                fc="#0a1222", ec=LINE, lw=1.5))
    links = [
        ("READ", "thanatchon36.github.io/twelve-views-thai-tourism"),
        ("DOI", CONCEPT_DOI),
        ("CODE", "github.com/thanatchon36/twelve-views-thai-tourism"),
        ("DATA", "hf.co/datasets/thanatchon36/twelve-views-thai-tourism"),
    ]
    for j, (k, v) in enumerate(links):
        lx = M + 10 + (j % 2) * 1010
        ly = box_y + 62 + (j // 2) * 50
        text(ax, lx, ly, spaced(k), 22, AMBER, "semibold")
        text(ax, lx + 120, ly, v, 28, INK)
    text(ax, M + 10, box_y + box_h - 34,
         "All data are synthetic, with known structure planted in them: a test of the method, not findings about Thai tourism.",
         23, MUTED)
    text(ax, M, author_y, "Thanatchon Chongmankhong", 31, PALE, "semibold")
    text(ax, W - M, author_y, "Personal research; views are my own  ·  19-page working paper, open code and data",
         23, MUTED, ha="right")
    print(f"gallery scale {scale:.2f}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=DPI, facecolor=NIGHT)
    plt.close(fig)
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
