"""Twelve figures, one per visualization technique.

Each function reads the CSVs in data/, draws one figure with matplotlib
and writes figures/<name>.pdf (vector, used by the paper) and .png.

Run:  python -m src.figures            (all figures)
      python -m src.figures sankey     (one figure)
"""
import sys

import circlify
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Circle, FancyBboxPatch, PathPatch, Wedge
from matplotlib.path import Path
from scipy.interpolate import BSpline, PchipInterpolator

from . import labels as L
from .analysis import largest_remainder
from .config import DATA, LATEST_YEAR
from .style import (AXIS, DEST_COLORS, FULL, GRID, HALF, INK, MUTED, NODE_GRAY, ORIGIN_COLORS,
                    PERSONA_COLORS, SPEND_COLORS, THAI_COLORS, halo, lighten, save, setup)

TAU = 2 * np.pi
THAI_MARKS = set(range(0x0E31, 0x0E32)) | set(range(0x0E34, 0x0E3B)) | set(range(0x0E47, 0x0E4F))


def load(name: str) -> pd.DataFrame:
    return pd.read_csv(DATA / f"{name}.csv")


def short(name: str) -> str:
    return L.SHORT_NAMES.get(name, name)


def text_width_in(s: str, size_pt: float) -> float:
    """Rough printed width (inches) of a label; Thai combining marks take no space."""
    base = sum(1 for ch in s if ord(ch) not in THAI_MARKS)
    return base * 0.52 * size_pt / 72


def text_inches(ax, s, **kw):
    """Exact printed width of a text string in inches (uses the renderer)."""
    t = ax.text(0, 0, s, **kw)
    fig = ax.figure
    w = t.get_window_extent(renderer=fig.canvas.get_renderer()).width / fig.dpi
    t.remove()
    return w


def data_to_inches(ax, d):
    """Length in inches of a horizontal data distance d (after limits/aspect are final)."""
    ax.figure.canvas.draw()
    (x0, _), (x1, _) = ax.transData.transform([(0, 0), (d, 0)])
    return abs(x1 - x0) / ax.figure.dpi


def repel(ys, gap):
    """Spread sorted label positions so neighbours are at least `gap` apart."""
    ys = np.asarray(ys, dtype=float)
    order = np.argsort(ys)
    out = ys[order].copy()
    for _ in range(200):
        moved = False
        for i in range(1, len(out)):
            d = out[i] - out[i - 1]
            if d < gap:
                shift = (gap - d) / 2
                out[i - 1] -= shift
                out[i] += shift
                moved = True
        if not moved:
            break
    res = np.empty_like(out)
    res[order] = out
    return res


def polar_xy(angle, r):
    """Angle measured clockwise from 12 o'clock."""
    return r * np.sin(angle), r * np.cos(angle)


# ---------------------------------------------------------------------------
# RQ1  Who comes, and when?
# ---------------------------------------------------------------------------
def unit_chart():
    """Unit chart: 100 squares, one per traveller, coloured by origin region."""
    nat = load("arrivals_by_nationality")
    g = (nat[nat.year == LATEST_YEAR].groupby(["region_id", "origin_region"]).arrivals.sum()
         .reset_index().sort_values("region_id"))
    share = g.arrivals / g.arrivals.sum()
    units = largest_remainder(share.values, 100)

    fig, ax = plt.subplots(figsize=(HALF, 3.3))
    dx = 0.85                                     # centre the 10 x 10 grid above the wider legend
    for i, rid in enumerate(np.repeat(g.region_id.values, units)):
        row, col = divmod(i, 10)
        ax.add_patch(FancyBboxPatch((dx + col + .08, -row + .08), .84, .84, lw=0, fc=ORIGIN_COLORS[rid],
                                    boxstyle="round,pad=0,rounding_size=0.14"))
    y = -10.75
    for rid, name, u, s in zip(g.region_id, g.origin_region, units, share):
        ax.add_patch(FancyBboxPatch((.1, y + .2), .6, .6, lw=0, fc=ORIGIN_COLORS[rid],
                                    boxstyle="round,pad=0,rounding_size=0.12"))
        ax.text(0.95, y + .5, name, va="center", fontsize=7.2)
        ax.text(9.35, y + .5, f"{u} visitors", va="center", ha="right", fontsize=7.2, fontweight="semibold")
        ax.text(12.05, y + .5, f"{s:.1%}", va="center", ha="right", fontsize=6.6, color=MUTED)
        y -= 1.0
    ax.set_xlim(0, 12.15)
    ax.set_ylim(y + .75, 1.0)
    ax.set_aspect("equal")
    ax.axis("off")
    save(fig, "fig02_unit_chart")


def radial_spiral():
    """Radial spiral: one loop per year, radius = monthly arrivals."""
    m = load("arrivals_monthly")
    m["year"] = m.month.str[:4].astype(int)
    m["mon"] = m.month.str[5:].astype(int) - 1
    m["v"] = m.arrivals / 1e6
    years = sorted(m.year.unique())
    annual = m.groupby("year").arrivals.sum()
    peak, low, last = int(annual.idxmax()), int(annual.idxmin()), years[-1]
    cmap = LinearSegmentedColormap.from_list("years", ["#D3DCE8", "#8FA9CC", "#2F5FA3", "#0D2A5C"])
    shade = lambda y: cmap(years.index(y) / (len(years) - 1))

    fig = plt.figure(figsize=(HALF, 3.6))
    ax = fig.add_axes([0.07, 0.2, 0.86, 0.78], projection="polar")
    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1)
    for y in years:
        d = m[m.year == y].sort_values("mon")
        th, r = list(d.mon / 12 * TAU), list(d.v)
        nxt = m[(m.year == y + 1) & (m.mon == 0)]
        if len(nxt):
            th.append(TAU)
            r.append(float(nxt.v.iloc[0]))
        tf = np.linspace(th[0], th[-1], (len(th) - 1) * 10 + 1)   # follow the circle between months
        emph = y in (peak, last)
        ax.plot(tf, np.interp(tf, th, r), color=shade(y), lw=1.6 if emph else 0.75,
                zorder=4 if emph else 2, solid_capstyle="round")
    for y, mon, xt, ha in ((peak, 11, (0.02, 0.985), "left"), (last, 0, (0.98, 0.985), "right")):
        v = float(m[(m.year == y) & (m.mon == mon)].v.iloc[0])
        ax.annotate(f"{y}", xy=(mon / 12 * TAU, v), xytext=xt, textcoords="axes fraction",
                    fontsize=7.2, fontweight="semibold", color=shade(y), ha=ha, va="top",
                    arrowprops=dict(arrowstyle="-", color=shade(y), lw=0.6, shrinkA=1, shrinkB=1), zorder=6)
    lowmax = float(m[m.year == low].v.max())
    ax.annotate("COVID-19: loops collapse\ntowards the centre", xy=(7.5 / 12 * TAU, lowmax + 0.08),
                xytext=(0.03, 0.105), textcoords="figure fraction", fontsize=6.6, ha="left", va="center",
                arrowprops=dict(arrowstyle="-|>", color=INK, lw=0.6, shrinkA=2, shrinkB=1, mutation_scale=6),
                zorder=7)
    vmax = m.v.max()
    ticks = list(range(1, int(np.floor(vmax)) + 1))
    ax.set_ylim(0, vmax * 1.04)
    ax.set_yticks(ticks)
    ax.set_yticklabels([f"{t}M" for t in ticks], fontsize=6.2, color=MUTED)
    for t in ax.get_yticklabels():
        t.set_path_effects(halo(2.0))
    ax.set_rlabel_position(52)
    ax.set_xticks(np.arange(12) / 12 * TAU)
    ax.set_xticklabels(L.MONTHS, fontsize=6.8)
    ax.tick_params(axis="x", pad=-2)
    ax.grid(color=GRID, lw=0.6)
    ax.spines["polar"].set_visible(False)

    cax = fig.add_axes([0.6, 0.075, 0.33, 0.02])
    cax.imshow(np.linspace(0, 1, 256)[None, :], aspect="auto", cmap=cmap)
    cax.axis("off")
    fig.text(0.6, 0.045, str(years[0]), ha="left", va="center", fontsize=6.4, color=MUTED)
    fig.text(0.93, 0.045, str(years[-1]), ha="right", va="center", fontsize=6.4, color=MUTED)
    fig.text(0.765, 0.125, "Line colour = year", ha="center", va="center", fontsize=6.6, color=MUTED)
    save(fig, "fig03_radial_spiral")


def inside_out(Y):
    """d3.stackOrderInsideOut: early-peaking series in the middle, late ones outside."""
    peaks, sums = Y.argmax(axis=1), Y.sum(axis=1)
    top = bottom = 0.0
    tops, bottoms = [], []
    for i in np.argsort(peaks, kind="stable"):
        if top < bottom:
            top += sums[i]
            tops.append(i)
        else:
            bottom += sums[i]
            bottoms.append(i)
    return bottoms[::-1] + tops


def streamgraph():
    """Streamgraph: arrivals by market, wiggle baseline (Byron & Wattenberg 2008).

    Layers are grouped by origin region so each colour family stays together;
    small residual groups are merged into a single grey layer.
    """
    nat = load("arrivals_by_nationality")
    other = "Other"
    keep_groups = {"Other East Asia", "Other ASEAN", "Other Europe"}
    nat["layer"] = np.where((nat.kind == "country") | nat.nationality.isin(keep_groups), nat.nationality, other)
    info = nat.groupby("layer").agg(rid=("region_id", "first"), kind=("kind", "first"), tot=("arrivals", "sum"))
    stack_regions = [1, 0, 3, 2, 4]            # bottom -> top; grey "other" layer last
    order = []
    for r in stack_regions:
        sub = info[(info.rid == r) & (info.index != other)]
        order += list(sub.assign(g=sub.kind == "group").sort_values(["g", "tot"], ascending=[True, False]).index)
    order.append(other)
    piv = nat.pivot_table(index="year", columns="layer", values="arrivals", aggfunc="sum")[order] / 1e6
    years = piv.index.values
    xf = np.linspace(years[0], years[-1], 600)
    Y = np.array([np.clip(PchipInterpolator(years, piv[c].values)(xf), 0, None) for c in order])
    colors, seen = [], {}
    for name in order:
        if name == other:
            colors.append("#C9C7C0")
            continue
        r = int(info.loc[name, "rid"])
        k = seen.get(r, 0)
        seen[r] = k + 1
        colors.append(lighten(ORIGIN_COLORS[r], min(0.62, 0.24 * k)))
    n = len(Y)
    base = -(Y * (n - 0.5 - np.arange(n))[:, None]).sum(0) / n      # matplotlib's "wiggle" baseline
    tops = base + np.cumsum(Y, axis=0)
    bottoms = np.vstack([base, tops[:-1]])

    fig = plt.figure(figsize=(FULL, 3.0))
    ax = fig.add_axes([0.0, 0.1, 0.77, 0.86])
    ax.axvspan(2019.75, 2022.4, color="#F1EFEA", lw=0, zorder=0)
    ax.text(2021.08, tops.max() * 1.03, "COVID-19", ha="center", va="bottom", fontsize=6.8, color=MUTED)
    for i in range(n):
        ax.fill_between(xf, bottoms[i], tops[i], color=colors[i], lw=0.45, edgecolor="white", zorder=2)
    placed = []
    for i in np.argsort(-(tops - bottoms).max(axis=1)):
        th = tops[i] - bottoms[i]
        j = int(np.argmax(th[40:-40])) + 40
        x, y = xf[j], (tops[i][j] + bottoms[i][j]) / 2
        if th[j] < 1.8 or any(abs(x - px) < 2.8 and abs(y - py) < 1.5 for px, py in placed):
            continue
        placed.append((x, y))
        ax.text(x, y, order[i], ha="center", va="center", fontsize=7, color=INK,
                path_effects=halo(2.0), zorder=5)
    y0 = bottoms.min() + 0.5
    ax.plot([2025.6, 2025.6], [y0, y0 + 5], color=INK, lw=1.0, solid_capstyle="butt")
    ax.text(2025.8, y0 + 2.5, "5 million", rotation=90, va="center", ha="left", fontsize=6.6, color=MUTED)
    ax.set_xlim(years[0] - 0.1, 2026.3)
    ax.set_ylim(bottoms.min() - 0.3, tops.max() * 1.12)
    ax.set_xticks(range(years[0], years[-1] + 1, 3))
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_bounds(years[0], years[-1])
    ax.set_yticks([])

    lg = fig.add_axes([0.79, 0.1, 0.21, 0.86])
    lg.axis("off")
    for k, i in enumerate(range(n - 1, -1, -1)):
        yy = 1 - k / (n + 0.5)
        lg.add_patch(FancyBboxPatch((0.0, yy - 0.022), 0.07, 0.044, boxstyle="round,pad=0,rounding_size=0.01",
                                    fc=colors[i], lw=0, transform=lg.transAxes))
        lg.text(0.11, yy, order[i], va="center", fontsize=6.8, transform=lg.transAxes)
    save(fig, "fig04_streamgraph")


def ridgeline():
    """Ridgeline plot: distribution of nights per trip, one ridge per nationality."""
    st = load("stay_length")
    groups = []
    for name, g in st.groupby("nationality"):
        g = g.sort_values("nights")
        med = int(g.nights.values[np.searchsorted(g.share.cumsum().values, 0.5)])
        groups.append((med, name, int(g.region_id.iloc[0]), g.nights.values, g.share.values))
    groups.sort()
    scale = 2.4 / max(s.max() for *_, s in groups)
    xf = np.linspace(1, 30, 500)

    fig, ax = plt.subplots(figsize=(FULL, 3.15))
    for i, (med, name, rid, nights, share) in enumerate(groups):
        base = -i
        f = PchipInterpolator(nights, share)
        yf = np.clip(f(xf), 0, None) * scale
        col = ORIGIN_COLORS[rid]
        z = 10 + 2 * i
        ax.fill_between(xf, base, base + yf, color=lighten(col, 0.18), lw=0, zorder=z)
        ax.plot(xf, base + yf, color="white", lw=1.1, zorder=z + 1)
        ax.plot([1, 30], [base, base], color=col, lw=0.6, zorder=z + 1)
        ax.plot([med, med], [base, base + float(f(med)) * scale], color="white", lw=0.9,
                ls=(0, (2, 1.4)), zorder=z + 1)
        ax.text(0.3, base + 0.1, name, ha="right", va="bottom", fontsize=7.2)
        ax.text(31.0, base + 0.1, f"median {med} nights", ha="left", va="bottom", fontsize=6.7, color=MUTED)
    ax.set_xlim(-5.2, 36.5)
    ax.set_ylim(-len(groups) + 0.6, 2.6)
    ax.set_xticks([1, 7, 14, 21, 28])
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_bounds(1, 30)
    ax.set_yticks([])
    ax.set_xlabel("Nights per trip", fontsize=7.2, color=MUTED, labelpad=3)
    ax.xaxis.set_label_coords(15.5 / 41.7 + 5.2 / 41.7, -0.09)
    save(fig, "fig05_ridgeline")


# ---------------------------------------------------------------------------
# RQ2  Where do they go?
# ---------------------------------------------------------------------------
def band(xa, ya1, ya0, xb, yb1, yb0):
    """Closed Bezier band between a source slot (ya1..ya0) and a target slot."""
    xm = (xa + xb) / 2
    verts = [(xa, ya1), (xm, ya1), (xm, yb1), (xb, yb1), (xb, yb0), (xm, yb0), (xm, ya0), (xa, ya0), (xa, ya1)]
    codes = [Path.MOVETO, Path.CURVE4, Path.CURVE4, Path.CURVE4, Path.LINETO,
             Path.CURVE4, Path.CURVE4, Path.CURVE4, Path.CLOSEPOLY]
    return Path(verts, codes)


def sankey():
    """Three-stage Sankey: origin region -> main destination -> trip style.

    Second-stage links are split by origin so each colour runs through the diagram.
    """
    tf = load("trip_flows")
    cols = [("region_id", L.ORIGIN_REGIONS), ("dest_id", L.DEST_CLUSTERS), ("style_id", L.TRIP_STYLES)]
    xs, nw, gap = [0.215, 0.545, 0.855], 0.011, 0.02
    k = (1 - 5 * gap) / tf.travelers.sum()
    nodes = {}
    for ci, (idcol, names) in enumerate(cols):
        sums = tf.groupby(idcol).travelers.sum().sort_index()
        y = 1 - (1 - (sums.sum() * k + (len(sums) - 1) * gap)) / 2
        for i, v in sums.items():
            nodes[(ci, i)] = dict(y1=y, y0=y - v * k, out=y, inn=y, v=v, name=names[i])
            y -= v * k + gap

    def place(links, sc, tc, skey, tkey):
        for l in sorted(links, key=skey):
            n = nodes[(sc, l["s"])]
            l["sy1"], n["out"] = n["out"], n["out"] - l["v"] * k
            l["sy0"] = n["out"]
        for l in sorted(links, key=tkey):
            n = nodes[(tc, l["t"])]
            l["ty1"], n["inn"] = n["inn"], n["inn"] - l["v"] * k
            l["ty0"] = n["inn"]

    l1 = [dict(o=o, s=o, t=d, v=v) for (o, d), v in tf.groupby(["region_id", "dest_id"]).travelers.sum().items()]
    l2 = [dict(o=o, s=d, t=s, v=v) for (d, s, o), v in
          tf.groupby(["dest_id", "style_id", "region_id"]).travelers.sum().items()]
    place(l1, 0, 1, lambda l: (l["s"], l["t"]), lambda l: (l["t"], l["s"]))
    place(l2, 1, 2, lambda l: (l["s"], l["t"], l["o"]), lambda l: (l["t"], l["s"], l["o"]))

    fig, ax = plt.subplots(figsize=(FULL, 3.7))
    for links, sc, tc in ((l1, 0, 1), (l2, 1, 2)):
        for l in links:
            p = band(xs[sc] + nw, l["sy1"], l["sy0"], xs[tc], l["ty1"], l["ty0"])
            ax.add_patch(PathPatch(p, fc=ORIGIN_COLORS[l["o"]], alpha=0.42, lw=0))
    for (ci, i), n in nodes.items():
        fc = ORIGIN_COLORS[i] if ci == 0 else NODE_GRAY
        ax.add_patch(plt.Rectangle((xs[ci], n["y0"]), nw, n["y1"] - n["y0"], fc=fc, lw=0))
        ym = (n["y0"] + n["y1"]) / 2
        label = f"{n['name']}  {n['v'] / 1e6:.1f}M"
        if ci == 0:
            ax.text(xs[0] - 0.008, ym, label, ha="right", va="center", fontsize=7)
        else:
            ax.text(xs[ci] + nw + 0.007, ym, label, ha="left", va="center", fontsize=7,
                    path_effects=halo(2.2) if ci == 1 else None)
    for x, t, ha in ((xs[0] + nw, "Origin region", "right"), (xs[1], "Main destination", "left"),
                     (xs[2], "Trip style", "left")):
        ax.text(x, 1.045, t, ha=ha, va="bottom", fontsize=7.4, fontweight="semibold", color=INK)
    ax.set_xlim(0, 1)
    ax.set_ylim(-0.01, 1.09)
    ax.axis("off")
    save(fig, "fig06_sankey")


def chord_layout(M, pad):
    """Port of d3.chord(): returns group arcs, subgroup arcs and chord pairs."""
    n = len(M)
    k = (TAU - pad * n) / M.sum()
    groups, sub, a = [], {}, 0.0
    for i in range(n):
        start = a
        for j in sorted(range(n), key=lambda j: -M[i, j]):
            sub[(i, j)] = (a, a + M[i, j] * k)
            a += M[i, j] * k
        groups.append((start, a))
        a += pad
    pairs = [(i, j) for i in range(n) for j in range(i + 1, n) if M[i, j] + M[j, i] > 0]
    return groups, sub, pairs


def arc_points(a0, a1, r, n=40):
    t = np.linspace(a0, a1, max(2, int(n * abs(a1 - a0) / TAU * 4) + 2))
    return np.c_[r * np.sin(t), r * np.cos(t)]


def chord():
    """Chord diagram of onward trips between destination clusters.

    A ribbon's two ends show the flow in each direction; its colour is the
    smaller cluster of the pair, so the hub's ribbons show who it links to.
    """
    rf = load("region_flows")
    n = len(L.DEST_CLUSTERS)
    M = np.zeros((n, n))
    for r in rf.itertuples():
        M[r.from_id, r.to_id] = r.travelers / 1e6
    groups, sub, pairs = chord_layout(M, pad=0.05)
    R, w = 1.0, 0.075
    rin = R - w - 0.012
    size = M.sum(1) + M.sum(0)

    fig, ax = plt.subplots(figsize=(FULL, 3.4))
    for i, j in sorted(pairs, key=lambda p: -(M[p] + M[p[::-1]])):
        a0, a1 = sub[(i, j)]
        b0, b1 = sub[(j, i)]
        src, tgt = arc_points(a0, a1, rin), arc_points(b0, b1, rin)
        verts = list(src) + [(0, 0), tuple(tgt[0])] + list(tgt[1:]) + [(0, 0), tuple(src[0])]
        codes = [Path.MOVETO] + [Path.LINETO] * (len(src) - 1) + [Path.CURVE3, Path.CURVE3] \
            + [Path.LINETO] * (len(tgt) - 1) + [Path.CURVE3, Path.CURVE3]
        spoke = i if size[i] < size[j] else j
        ax.add_patch(PathPatch(Path(verts, codes), fc=DEST_COLORS[spoke], alpha=0.6, ec="white", lw=0.35))
    for i, (g0, g1) in enumerate(groups):
        ax.add_patch(Wedge((0, 0), R, 90 - np.degrees(g1), 90 - np.degrees(g0), width=w,
                           fc=DEST_COLORS[i], ec="white", lw=0.6))
        mid = (g0 + g1) / 2
        x, y = polar_xy(mid, R + 0.08)
        sx, cy = np.sin(mid), np.cos(mid)
        ha = "left" if sx > 0.15 else ("right" if sx < -0.15 else "center")
        va = "bottom" if cy > 0.85 else ("top" if cy < -0.85 else "center")
        ax.text(x, y, f"{L.DEST_CLUSTERS[i]}\nout {M[i].sum():.1f}M / in {M[:, i].sum():.1f}M trips",
                ha=ha, va=va, fontsize=6.8, linespacing=1.05)
    ax.set_xlim(-2.1, 2.1)
    ax.set_ylim(-1.32, 1.32)
    ax.set_aspect("equal")
    ax.axis("off")
    save(fig, "fig07_chord")


def bspline_curve(ctrl, k=3, n=60):
    ctrl = np.asarray(ctrl, dtype=float)
    k = min(k, len(ctrl) - 1)
    t = np.r_[np.zeros(k), np.linspace(0, 1, len(ctrl) - k + 1), np.ones(k)]
    return BSpline(t, ctrl, k)(np.linspace(0, 1, n))


def edge_bundling(beta=0.85):
    """Hierarchical edge bundling (Holten 2006): provinces -> regions -> root."""
    cov = load("province_covisits")
    prov = load("provinces").set_index("province")
    deg = pd.concat([cov.set_index("province_a").trips, cov.set_index("province_b").trips]).groupby(level=0).sum()
    nodes = sorted(deg.index, key=lambda p: (prov.loc[p, "thai_region_id"], -deg[p]))
    rid = {p: int(prov.loc[p, "thai_region_id"]) for p in nodes}
    pos, t = [], 0.0
    for i, p in enumerate(nodes):
        if i and rid[p] != rid[nodes[i - 1]]:
            t += 1.6
        pos.append(t)
        t += 1
    span = pos[-1] + 1.6
    ang = {p: TAU * pos[i] / span for i, p in enumerate(nodes)}
    R = 1.32
    centre = {r: np.mean([ang[p] for p in nodes if rid[p] == r]) for r in set(rid.values())}

    fig, ax = plt.subplots(figsize=(FULL, 4.3))
    wmax = cov.trips.max()
    for e in cov.sort_values("trips").itertuples():
        a, b = e.province_a, e.province_b
        pa, pb = np.array(polar_xy(ang[a], R)), np.array(polar_xy(ang[b], R))
        ca, cb = np.array(polar_xy(centre[rid[a]], R * 0.48)), np.array(polar_xy(centre[rid[b]], R * 0.48))
        ctrl = [pa, ca, pb] if rid[a] == rid[b] else [pa, ca, np.zeros(2), cb, pb]
        ctrl = np.array(ctrl)
        straight = ctrl[0] + np.linspace(0, 1, len(ctrl))[:, None] * (ctrl[-1] - ctrl[0])
        curve = bspline_curve(beta * ctrl + (1 - beta) * straight)
        spoke = a if deg[a] < deg[b] else b
        ax.plot(curve[:, 0], curve[:, 1], color=THAI_COLORS[rid[spoke]], alpha=0.55,
                lw=0.35 + 2.4 * np.sqrt(e.trips / wmax), solid_capstyle="round", zorder=2)
    for p in nodes:
        x, y = polar_xy(ang[p], R)
        ax.add_patch(Circle((x, y), 0.022, fc=THAI_COLORS[rid[p]], lw=0, zorder=4))
        lx, ly = polar_xy(ang[p], R + 0.06)
        deg_std = 90 - np.degrees(ang[p])
        right = np.sin(ang[p]) >= 0
        ax.text(lx, ly, short(p), rotation=deg_std if right else deg_std + 180, rotation_mode="anchor",
                ha="left" if right else "right", va="center", fontsize=6.6, zorder=5)
    for r in range(len(L.THAI_REGIONS)):
        ax.add_patch(Circle((-2.95, 1.95 - r * 0.2), 0.045, fc=THAI_COLORS[r], lw=0))
        ax.text(-2.85, 1.95 - r * 0.2, L.THAI_REGIONS[r], va="center", fontsize=6.8)
    ax.set_xlim(-3.05, 3.05)
    ax.set_ylim(-2.08, 2.08)
    ax.set_aspect("equal")
    ax.axis("off")
    save(fig, "fig08_edge_bundling")


# ---------------------------------------------------------------------------
# RQ3  Where does the money go?
# ---------------------------------------------------------------------------
def circle_packing():
    """Circle packing: region -> province, area = tourism revenue."""
    prov = load("provinces")
    data = [{"id": int(r), "datum": float(g.revenue_mb.sum()),
             "children": [{"id": p.province, "datum": float(p.revenue_mb)} for p in g.itertuples()]}
            for r, g in prov.groupby("thai_region_id")]
    circles = circlify.circlify(data, show_enclosure=False, target_enclosure=circlify.Circle(x=0, y=0, r=1))
    region_of = prov.set_index("province").thai_region_id
    revenue = prov.set_index("province").revenue_mb
    tops = [c for c in circles if c.level == 1]
    x0 = min(c.x - c.r for c in tops) - 0.02
    x1 = max(c.x + c.r for c in tops) + 0.02
    y0 = min(c.y - c.r for c in tops) - 0.02
    y1 = max(c.y + c.r for c in tops) + 0.02

    fig, ax = plt.subplots(figsize=(FULL, 3.5))
    for c in tops:
        col = THAI_COLORS[c.ex["id"]]
        ax.add_patch(Circle((c.x, c.y), c.r, fc=lighten(col, 0.88), ec=lighten(col, 0.35), lw=0.7))
    leaves = [c for c in circles if c.level == 2]
    for c in leaves:
        col = THAI_COLORS[int(region_of[c.ex["id"]])]
        ax.add_patch(Circle((c.x, c.y), c.r * 0.97, fc=lighten(col, 0.12), lw=0))
    legend_x = x1 + 0.12
    ax.set_xlim(x0, legend_x + 1.05)
    ax.set_ylim(y0, y1)
    ax.set_aspect("equal")
    ax.axis("off")
    unit = data_to_inches(ax, 1.0)
    for c in leaves:
        name = c.ex["id"]
        diam = 2 * c.r * 0.97 * unit
        label, value = short(name), f"THB {revenue[name] / 1e3:,.0f}bn"
        w_name = text_inches(ax, label, fontsize=7.2, fontweight="semibold")
        w_val = text_inches(ax, value, fontsize=6.4)
        if diam > max(w_name, w_val) + 0.1 and diam > 0.42:
            ax.text(c.x, c.y + 0.11 * c.r, label, ha="center", va="center", fontsize=7.2,
                    color="white", fontweight="semibold")
            ax.text(c.x, c.y - 0.2 * c.r, value, ha="center", va="center", fontsize=6.4, color="white")
        elif diam > text_inches(ax, label, fontsize=6.2) + 0.06:
            ax.text(c.x, c.y, label, ha="center", va="center", fontsize=6.2, color="white")
    ytop = y1 - 0.18
    ax.text(legend_x, ytop, "Revenue share by region", fontsize=7.2, fontweight="semibold", va="center")
    for r in range(len(L.THAI_REGIONS)):
        y = ytop - 0.2 - r * 0.17
        ax.add_patch(Circle((legend_x + 0.04, y), 0.04, fc=THAI_COLORS[r], lw=0))
        tot = prov[prov.thai_region_id == r].revenue_mb.sum() / prov.revenue_mb.sum()
        ax.text(legend_x + 0.12, y, L.THAI_REGIONS[r], va="center", fontsize=7)
        ax.text(legend_x + 1.02, y, f"{tot:.1%}", va="center", ha="right", fontsize=7, color=MUTED)
    save(fig, "fig09_circle_packing")


def sunburst():
    """Sunburst: category -> subcategory -> item, angle = share of spending."""
    sp = load("spending_breakdown")
    rings = {1: (0.40, 0.66), 2: (0.675, 0.84), 3: (0.85, 1.0)}
    fig, ax = plt.subplots(figsize=(FULL, 3.9))
    leaves = []
    a = 0.0
    for cid, cat in sp.groupby("cat_id", sort=True):
        col = SPEND_COLORS[cid]
        c0 = a
        for sub_name, sub in cat.groupby("subcategory", sort=False):
            s0 = a
            items = sub[sub["item"].notna() & (sub["item"] != "")]
            if len(items):
                for it in items.itertuples():
                    i0, a = a, a + it.share * TAU
                    ax.add_patch(Wedge((0, 0), rings[3][1], 90 - np.degrees(a), 90 - np.degrees(i0),
                                       width=rings[3][1] - rings[3][0], fc=lighten(col, 0.55), ec="white", lw=0.7))
                    leaves.append(((i0 + a) / 2, it.item, it.share, rings[3][1]))
            else:
                a += sub.share.sum() * TAU
                leaves.append(((s0 + a) / 2, sub_name, sub.share.sum(), rings[2][1]))
            ax.add_patch(Wedge((0, 0), rings[2][1], 90 - np.degrees(a), 90 - np.degrees(s0),
                               width=rings[2][1] - rings[2][0], fc=lighten(col, 0.3), ec="white", lw=0.7))
        ax.add_patch(Wedge((0, 0), rings[1][1], 90 - np.degrees(a), 90 - np.degrees(c0),
                           width=rings[1][1] - rings[1][0], fc=col, ec="white", lw=0.9))
        mid, span = (c0 + a) / 2, a - c0
        if span > 0.6:
            x, y = polar_xy(mid, sum(rings[1]) / 2)
            ax.text(x, y, f"{cat.share.sum():.0%}", ha="center", va="center", fontsize=6.8,
                    color="white", fontweight="semibold")
    ax.text(0, 0.06, "Total", ha="center", va="center", fontsize=7.4, fontweight="semibold")
    ax.text(0, -0.08, "spending", ha="center", va="center", fontsize=7.4, fontweight="semibold")
    # Leader-line labels for every leaf, spread on the two sides
    for side in (1, -1):
        L_ = [lf for lf in leaves if np.sign(np.sin(lf[0]) or 1) == side]
        if not L_:
            continue
        ys = repel([np.cos(lf[0]) * 1.12 for lf in L_], 0.115)
        for (ang_, name, share, r0), ly in zip(L_, ys):
            x0, y0 = polar_xy(ang_, r0 + 0.01)
            x1, y1 = polar_xy(ang_, r0 + 0.08)
            xt = side * 1.42
            ax.plot([x0, x1, xt - side * 0.04], [y0, y1, ly], color=AXIS, lw=0.45)
            ax.text(xt, ly, f"{name}  {share:.1%}", ha="left" if side > 0 else "right", va="center", fontsize=6.6)
    cats = sp.groupby(["cat_id", "category"]).share.sum().reset_index()
    for k, r in enumerate(cats.itertuples()):
        x = -2.72 + (k % 3) * 1.98
        y = -1.5 - (k // 3) * 0.17
        ax.add_patch(FancyBboxPatch((x, y - 0.045), 0.09, 0.09, boxstyle="round,pad=0,rounding_size=0.015",
                                    fc=SPEND_COLORS[r.cat_id], lw=0))
        ax.text(x + 0.14, y, f"{r.category}  {r.share:.1%}", va="center", fontsize=6.8)
    ax.set_xlim(-2.75, 2.75)
    ax.set_ylim(-1.72, 1.32)
    ax.set_aspect("equal")
    ax.axis("off")
    save(fig, "fig10_sunburst")


def beeswarm():
    """Beeswarm of 77 provinces: x = spend per visitor (log), area = foreign visitors."""
    prov = load("provinces")
    W = FULL
    left, right = 0.2, W - 0.2
    lo, hi = np.log(prov.spend_per_visitor.min() * 0.86), np.log(prov.spend_per_visitor.max() * 1.1)
    X = lambda v: left + (np.log(v) - lo) / (hi - lo) * (right - left)
    vmax = prov.foreign_visitors.max()
    radius = lambda v: 0.042 + 0.21 * np.sqrt(v / vmax)
    pts = [dict(name=r.province, rid=r.thai_region_id, x=X(r.spend_per_visitor), r=radius(r.foreign_visitors),
                v=r.spend_per_visitor) for r in prov.itertuples()]
    placed = []
    for p in sorted(pts, key=lambda d: -d["r"]):
        blocked, cands = [], [0.0]
        for q in placed:
            dx, need = abs(p["x"] - q["x"]), p["r"] + q["r"] + 0.012
            if dx < need:
                dy = np.sqrt(need ** 2 - dx ** 2)
                blocked.append((q["y"] - dy, q["y"] + dy))
                cands += [q["y"] - dy, q["y"] + dy]
        ok = [c for c in cands if all(not (b0 + 1e-9 < c < b1 - 1e-9) for b0, b1 in blocked)]
        p["y"] = min(ok, key=abs)
        placed.append(p)
    top = max(p["y"] + p["r"] for p in placed)
    bot = min(p["y"] - p["r"] for p in placed)
    lab_up, lab_dn = top + 0.2, bot - 0.2
    axis_y = lab_dn - 0.3
    legend_y = lab_up + 0.32
    y_min, y_max = axis_y - 0.45, legend_y + radius(1e7) + 0.06
    fig = plt.figure(figsize=(W, y_max - y_min))
    ax = fig.add_axes([0, 0, 1, 1])          # 1 data unit = 1 inch, so text widths are comparable
    ax.set_xlim(0, W)
    ax.set_ylim(y_min, y_max)
    ax.set_aspect("equal")
    ax.axis("off")
    for p in placed:
        ax.add_patch(Circle((p["x"], p["y"]), p["r"], fc=THAI_COLORS[p["rid"]], ec="white", lw=0.4, zorder=3))
    ranked = sorted(placed, key=lambda d: d["v"])
    chosen = ranked[:2] + ranked[-2:] + sorted(placed, key=lambda d: -d["r"])[:3]
    chosen = list({id(p): p for p in chosen}.values())
    for group, ly, va in (([p for p in chosen if p["y"] >= 0], lab_up, "bottom"),
                          ([p for p in chosen if p["y"] < 0], lab_dn, "top")):
        group.sort(key=lambda d: d["x"])
        widths = [text_inches(ax, short(p["name"]), fontsize=6.8) for p in group]
        xs = [p["x"] for p in group]
        for _ in range(100):
            for i in range(1, len(xs)):
                need = (widths[i] + widths[i - 1]) / 2 + 0.08
                if xs[i] - xs[i - 1] < need:
                    d = (need - (xs[i] - xs[i - 1])) / 2
                    xs[i - 1] -= d
                    xs[i] += d
        for p, x in zip(group, xs):
            edge = p["y"] + (p["r"] if va == "bottom" else -p["r"])
            ax.plot([p["x"], x], [edge, ly + (-0.03 if va == "bottom" else 0.03)], color=AXIS, lw=0.5, zorder=2)
            ax.text(x, ly, short(p["name"]), ha="center", va=va, fontsize=6.8, zorder=6)
    ax.plot([left, right], [axis_y, axis_y], color=AXIS, lw=0.6)
    for t in (2000, 3000, 5000, 10000, 20000, 30000, 50000):
        if np.exp(lo) <= t <= np.exp(hi):
            ax.plot([X(t)] * 2, [axis_y, axis_y - 0.04], color=AXIS, lw=0.6)
            ax.text(X(t), axis_y - 0.07, f"{t:,}", ha="center", va="top", fontsize=6.8, color=MUTED)
    ax.text((left + right) / 2, axis_y - 0.3, "Average spend per foreign visitor per trip (THB, log scale)",
            ha="center", va="center", fontsize=7, color=MUTED)
    x = left
    for r in range(len(L.THAI_REGIONS)):
        ax.add_patch(Circle((x + 0.04, legend_y), 0.04, fc=THAI_COLORS[r], lw=0))
        ax.text(x + 0.11, legend_y, L.THAI_REGIONS[r], va="center", fontsize=6.8)
        x += 0.24 + text_inches(ax, L.THAI_REGIONS[r], fontsize=6.8)
    for v, lab in ((1e6, "1M visitors"), (1e7, "10M visitors")):
        rr = radius(v)
        cx = right - (0.25 if v == 1e7 else 1.05)
        ax.add_patch(Circle((cx, legend_y), rr, fc="none", ec=MUTED, lw=0.6))
        ax.text(cx - rr - 0.05, legend_y, lab, ha="right", va="center", fontsize=6.6, color=MUTED)
    save(fig, "fig11_beeswarm")


# ---------------------------------------------------------------------------
# RQ4  What kinds of travellers are there?
# ---------------------------------------------------------------------------
def parallel_coordinates():
    """Parallel coordinates of fifteen nationality profiles."""
    pr = load("nationality_profiles")
    pct = lambda v: f"{v:.0%}"
    axes = [("spend_per_day", "Spend/day (THB)", lambda v: f"{v:,.0f}"),
            ("avg_nights", "Mean nights", lambda v: f"{v:.0f}"),
            ("repeat_share", "Repeat visitors", pct),
            ("independent_share", "Independent", pct),
            ("beach_share", "Beach trips", pct),
            ("median_age", "Median age", lambda v: f"{v:.0f}")]
    norm = {}
    for col, *_ in axes:
        lo, hi = pr[col].min(), pr[col].max()
        pad = (hi - lo) * 0.06
        norm[col] = (lo - pad, hi + pad)
    xs = np.arange(len(axes))

    fig, ax = plt.subplots(figsize=(FULL, 3.25))
    ends = []
    for r in pr.sort_values("region_id", ascending=False).itertuples():
        ys = [(getattr(r, c) - norm[c][0]) / (norm[c][1] - norm[c][0]) for c, *_ in axes]
        ax.plot(xs, ys, color=ORIGIN_COLORS[r.region_id], lw=1.15, alpha=0.85, solid_joinstyle="round", zorder=3)
        ax.scatter(xs, ys, s=5, color=ORIGIN_COLORS[r.region_id], zorder=4, lw=0)
        ends.append((ys[-1], r.nationality, r.region_id))
    for x, (col, title, fmt) in zip(xs, axes):
        ax.plot([x, x], [0, 1], color=AXIS, lw=0.8, zorder=2)
        lo, hi = norm[col]
        for q in (0.0, 0.5, 1.0):
            v = lo + q * (hi - lo)
            ax.text(x - 0.05, q, fmt(v), ha="right", va="center", fontsize=6, color=MUTED, zorder=5,
                    path_effects=halo(1.8))
        ax.text(x, 1.06, title, ha="center", va="bottom", fontsize=7, fontweight="semibold")
    ly = repel([e[0] for e in ends], 0.062)
    for (y, name, rid), yy in zip(ends, ly):
        ax.plot([xs[-1] + 0.03, xs[-1] + 0.16], [y, yy], color=lighten(ORIGIN_COLORS[rid], 0.3), lw=0.5)
        ax.text(xs[-1] + 0.19, yy, name, va="center", fontsize=6.5, color=INK)
    for r_, name in enumerate(L.ORIGIN_REGIONS):
        x = -0.3 + r_ * 1.02
        ax.plot([x, x + 0.12], [-0.13, -0.13], color=ORIGIN_COLORS[r_], lw=2.2, solid_capstyle="round")
        ax.text(x + 0.17, -0.13, name, va="center", fontsize=6.8)
    ax.set_xlim(-0.4, len(axes) - 1 + 0.95)
    ax.set_ylim(-0.19, 1.16)
    ax.axis("off")
    save(fig, "fig12_parallel_coordinates")


def embedding():
    """t-SNE map of 1,200 synthetic survey respondents coloured by persona."""
    seg = load("traveler_segments")
    fig, ax = plt.subplots(figsize=(FULL, 3.45))
    for sid, g in seg.groupby("segment_id"):
        ax.scatter(g.x, g.y, s=6.5, color=PERSONA_COLORS[sid], alpha=0.78, lw=0, zorder=2)
    for sid, g in seg.groupby("segment_id"):
        cx, cy = g.x.median(), g.y.median()
        ax.text(cx, cy, f"{L.PERSONAS[sid]}\nn = {len(g):,}", ha="center", va="center", fontsize=7.2,
                fontweight="semibold", color=INK, path_effects=halo(2.6), zorder=5, linespacing=1.25)
    pad = 3
    ax.set_xlim(seg.x.min() - pad, seg.x.max() + pad)
    ax.set_ylim(seg.y.min() - pad, seg.y.max() + pad)
    ax.set_aspect("equal")
    ax.axis("off")
    save(fig, "fig13_embedding")


FIGURES = {
    "unit_chart": unit_chart, "radial_spiral": radial_spiral, "streamgraph": streamgraph,
    "ridgeline": ridgeline, "sankey": sankey, "chord": chord, "edge_bundling": edge_bundling,
    "circle_packing": circle_packing, "sunburst": sunburst, "beeswarm": beeswarm,
    "parallel_coordinates": parallel_coordinates, "embedding": embedding,
}


def main(names=None) -> None:
    setup()
    for name in names or FIGURES:
        FIGURES[name]()
        print("drew", name)


if __name__ == "__main__":
    main(sys.argv[1:])
