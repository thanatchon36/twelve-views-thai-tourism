"""Compute every number reported in the paper.

Outputs
  data/processed/metrics.json   machine-readable metrics
  paper/tables/numbers.tex      \\newcommand macros used in the text
  paper/tables/tab_*.tex        table bodies included by the paper

Run:  python -m twelveviews.cli analysis
"""
import json

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score, silhouette_score

from . import data_gen as G
from . import labels as L
from .config import LATEST_YEAR, PROCESSED, RAW, SEED, TABLES
from .loaders import load


# ---------------------------------------------------------------------------
# Generic statistics
# ---------------------------------------------------------------------------
def gini(x) -> float:
    """Gini coefficient of non-negative values."""
    x = np.sort(np.asarray(x, dtype=float))
    n = len(x)
    return float((2 * np.arange(1, n + 1) - n - 1) @ x / (n * x.sum()))


def hhi(values) -> float:
    """Herfindahl-Hirschman index on the 0-10,000 scale."""
    s = np.asarray(values, dtype=float)
    s = s / s.sum()
    return float(((100 * s) ** 2).sum())


def largest_remainder(shares, total=100):
    """Integer apportionment of `total` units that preserves the sum exactly."""
    raw = np.asarray(shares, dtype=float) / np.sum(shares) * total
    out = np.floor(raw).astype(int)
    for i in np.argsort(-(raw - out))[: total - out.sum()]:
        out[i] += 1
    return out


def seasonal_index(monthly: pd.DataFrame, last_normal_year: int = 2019) -> pd.Series:
    """S_m: mean ratio of month m to its year's monthly mean, over pre-pandemic years."""
    m = monthly.assign(year=monthly.month.str[:4].astype(int), mon=monthly.month.str[5:].astype(int))
    m = m[m.year <= last_normal_year].copy()
    m["idx"] = m.arrivals / m.groupby("year").arrivals.transform("mean")
    return m.groupby("mon").idx.mean()


def stay_medians(stay: pd.DataFrame) -> dict:
    out = {}
    for market, g in stay.groupby("nationality"):
        g = g.sort_values("nights")
        out[market] = int(g.nights.values[np.searchsorted(g.share.cumsum().values, 0.5)])
    return out


# ---------------------------------------------------------------------------
# Metrics by research question
# ---------------------------------------------------------------------------
def arrivals_metrics(nat, monthly):
    annual = nat.groupby("year").arrivals.sum()
    peak_y, low_y = int(annual.idxmax()), int(annual.idxmin())
    pre = annual.loc[:2019]
    season = seasonal_index(monthly)
    return {
        "first_year": int(annual.index.min()), "first_m": annual.iloc[0] / 1e6,
        "peak_year": peak_y, "peak_m": annual[peak_y] / 1e6,
        "low_year": low_y, "low_m": annual[low_y] / 1e6,
        "latest_year": LATEST_YEAR, "latest_m": annual[LATEST_YEAR] / 1e6,
        "recovery": annual[LATEST_YEAR] / annual[peak_y],
        "drop": 1 - annual[low_y] / annual[peak_y],
        "cagr_pre": (pre.iloc[-1] / pre.iloc[0]) ** (1 / (len(pre) - 1)) - 1,
        "season_peak_month": L.MONTHS_FULL[int(season.idxmax()) - 1], "season_peak": season.max(),
        "season_low_month": L.MONTHS_FULL[int(season.idxmin()) - 1], "season_low": season.min(),
        "season_ratio": season.max() / season.min(),
    }


def market_metrics(nat):
    out = {}
    for tag, year in (("pre", 2019), ("latest", LATEST_YEAR)):
        y = nat[nat.year == year].set_index("nationality")
        share = y.arrivals / y.arrivals.sum()
        countries = share[y.kind == "country"].sort_values(ascending=False)
        out[f"top_{tag}"] = countries.index[0]
        out[f"top_{tag}_share"] = countries.iloc[0]
        out[f"hhi_{tag}"] = hhi(y.arrivals)
    g = nat[nat.year == LATEST_YEAR].groupby(["region_id", "origin_region"]).arrivals.sum().reset_index()
    units = largest_remainder(g.arrivals.values)
    out["units_top_region"] = g.origin_region[int(np.argmax(units))]
    out["units_top"] = int(units.max())
    out["units_asia"] = int(units[[0, 1, 3]].sum())          # East Asia + ASEAN + South Asia
    return out


def stay_metrics(stay):
    s = pd.Series(stay_medians(stay)).sort_values()
    return {"stay_short": s.index[0], "stay_short_n": int(s.iloc[0]),
            "stay_long": s.index[-1], "stay_long_n": int(s.iloc[-1]), "stay_ratio": s.iloc[-1] / s.iloc[0]}


def flow_metrics(trips, flows):
    tot = trips.travelers.sum()
    by_dest = trips.groupby("dest_id").travelers.sum() / tot
    by_style = trips.groupby("style_id").travelers.sum() / tot
    eu, asean = trips[trips.region_id == 2], trips[trips.region_id == 1]
    hub = L.DEST_CLUSTERS[0]
    top = flows.sort_values("travelers", ascending=False).iloc[0]
    pair = flows.set_index(["from", "to"]).travelers
    return {
        "first_bkk": by_dest[0], "style_beach": by_style[0], "style_city": by_style[1],
        "eu_andaman": eu[eu.dest_id == 1].travelers.sum() / eu.travelers.sum(),
        "asean_border": asean[asean.dest_id == 5].travelers.sum() / asean.travelers.sum(),
        "onward_total_m": flows.travelers.sum() / 1e6,
        "onward_bkk": flows[(flows["from"] == hub) | (flows["to"] == hub)].travelers.sum() / flows.travelers.sum(),
        "onward_top_from": top["from"], "onward_top_to": top["to"], "onward_top_m": top.travelers / 1e6,
        "pattaya_bkk": pair[(L.DEST_CLUSTERS[3], hub)] / 1e6,
    }


def network_metrics(cov, prov):
    region = prov.set_index("province").thai_region
    same = cov[cov.province_a.map(region) == cov.province_b.map(region)].trips.sum() / cov.trips.sum()
    deg = pd.concat([cov.set_index("province_a").trips, cov.set_index("province_b").trips]).groupby(level=0).sum()
    no_hub = cov[(cov.province_a != "Bangkok") & (cov.province_b != "Bangkok")]
    top = no_hub.sort_values("trips", ascending=False).iloc[0]
    return {"net_nodes": int(deg.size), "net_edges": len(cov), "net_same_region": same,
            "net_bkk_degree_share": deg["Bangkok"] / deg.sum(),
            "net_bkk_edges": int(((cov.province_a == "Bangkok") | (cov.province_b == "Bangkok")).sum()),
            "net_top_a": top.province_a, "net_top_b": top.province_b, "net_top_k": top.trips / 1e3}


def province_metrics(prov):
    p = prov.sort_values("revenue_mb", ascending=False)
    share = p.revenue_mb / p.revenue_mb.sum()
    hi, lo = prov.loc[prov.spend_per_visitor.idxmax()], prov.loc[prov.spend_per_visitor.idxmin()]
    rho = spearmanr(prov.foreign_visitors, prov.spend_per_visitor)[0]
    return {"rev_total_bn": prov.revenue_mb.sum() / 1e3, "rev_top1": p.province.iloc[0],
            "rev_top1_share": share.iloc[0], "rev_top5_share": share.iloc[:5].sum(),
            "rev_hhi": hhi(p.revenue_mb), "rev_gini": gini(p.revenue_mb),
            "spend_hi": hi.province, "spend_hi_v": hi.spend_per_visitor,
            "spend_lo": lo.province, "spend_lo_v": lo.spend_per_visitor,
            "spend_ratio": hi.spend_per_visitor / lo.spend_per_visitor, "spend_rho": rho}


def spending_metrics(sp):
    cat = sp.groupby("category").share.sum().sort_values(ascending=False)
    leaf = sp.assign(name=np.where(sp["item"].fillna("") != "", sp["item"], sp["subcategory"]))
    top_leaf = leaf.sort_values("share", ascending=False).iloc[0]
    return {"spend_cat1": cat.index[0], "spend_cat1_share": cat.iloc[0],
            "spend_cat2": cat.index[1], "spend_cat2_share": cat.iloc[1],
            "spend_cat3": cat.index[2], "spend_cat3_share": cat.iloc[2],
            "spend_top3_share": cat.iloc[:3].sum(),
            "spend_top_leaf": top_leaf["name"], "spend_top_leaf_share": top_leaf.share}


def profile_metrics(pr):
    hi, lo = pr.loc[pr.spend_per_day.idxmax()], pr.loc[pr.spend_per_day.idxmin()]
    rep = pr.loc[pr.repeat_share.idxmax()]
    return {"prof_n": len(pr), "prof_r_nights_spend": float(np.corrcoef(pr.avg_nights, pr.spend_per_day)[0, 1]),
            "prof_spend_hi": hi.nationality, "prof_spend_hi_v": hi.spend_per_day,
            "prof_spend_lo": lo.nationality, "prof_spend_lo_v": lo.spend_per_day,
            "prof_repeat_hi": rep.nationality, "prof_repeat_hi_v": rep.repeat_share}


def segment_metrics(seg):
    X = load("traveler_features").values
    km = KMeans(n_clusters=len(L.PERSONAS), n_init=20, random_state=SEED).fit(X)
    vc = seg.segment.value_counts(normalize=True)
    return {"seg_n": len(seg), "seg_k": seg.segment_id.nunique(),
            "seg_sil_embed": silhouette_score(seg[["x", "y"]], seg.segment_id),
            "seg_sil_feat": silhouette_score(X, seg.segment_id),
            "seg_ari": adjusted_rand_score(seg.segment_id, km.labels_),
            "seg_largest": vc.index[0], "seg_largest_share": vc.iloc[0]}


# ---------------------------------------------------------------------------
# Planted-structure recovery (the simulation study's performance measures)
# ---------------------------------------------------------------------------
def recovery_metrics(monthly, stay, trips, flows, M):
    # E1 seasonal profile
    est = seasonal_index(monthly).values
    truth = G.NORMAL_SEASON / G.NORMAL_SEASON.mean()
    # E2 pandemic depth, noise-free planted value
    i19, i21 = G.YEARS.index(2019), G.YEARS.index(2021)
    planted19 = sum(p[i19] for _, p in G.COUNTRY_PATHS.values()) + sum(v19 for _, _, v19 in G.GROUP_PATHS.values())
    planted21 = sum(p[i21] for _, p in G.COUNTRY_PATHS.values()) + \
        sum(v19 * G.PANDEMIC_FACTORS[1] for _, _, v19 in G.GROUP_PATHS.values())
    # E4 length-of-stay medians
    med = stay_medians(stay)
    stay_err = np.array([abs(med[k] - v[1]) for k, v in G.STAY_PARAMS.items()])
    # E5 destination preferences P(d | o)
    obs = trips.groupby(["region_id", "dest_id"]).travelers.sum().unstack(fill_value=0)
    obs = obs.div(obs.sum(axis=1), axis=0).values
    dest_err = 100 * np.abs(obs - G.P_DEST)
    # E6 hub share of onward trips
    R = G.REGION_FLOW
    planted_hub = (R[0].sum() + R[:, 0].sum()) / R.sum()
    return {
        "rec_season_r": float(np.corrcoef(est, truth)[0, 1]), "rec_season_mae": float(np.abs(est - truth).mean()),
        "rec_drop_planted": 1 - planted21 / planted19, "rec_drop_obs": M["drop"],
        "rec_stay_mae": float(stay_err.mean()), "rec_stay_max": float(stay_err.max()),
        "rec_dest_mae": float(dest_err.mean()), "rec_dest_max": float(dest_err.max()),
        "rec_hub_planted": planted_hub, "rec_hub_obs": M["onward_bkk"],
    }


# ---------------------------------------------------------------------------
# LaTeX output
# ---------------------------------------------------------------------------
def fmt_int(x) -> str:
    return f"{int(round(x)):,}"


def tex(s) -> str:
    return (str(s).replace("\\", r"\textbackslash{}").replace("&", r"\&").replace("%", r"\%")
            .replace("_", r"\_").replace("#", r"\#"))


def pct(v, d=1) -> str:
    return f"{100 * v:.{d}f}"


def write_macros(M: dict) -> None:
    macros = {
        "FirstYear": M["first_year"], "FirstM": f"{M['first_m']:.1f}",
        "PeakYear": M["peak_year"], "PeakM": f"{M['peak_m']:.1f}",
        "LowYear": M["low_year"], "LowM": f"{M['low_m']:.2f}",
        "LatestYear": M["latest_year"], "LatestM": f"{M['latest_m']:.1f}",
        "RecoveryPct": pct(M["recovery"]), "DropPct": pct(M["drop"]), "CagrPct": pct(M["cagr_pre"]),
        "SeasonPeakMonth": M["season_peak_month"], "SeasonPeak": f"{M['season_peak']:.2f}",
        "SeasonLowMonth": M["season_low_month"], "SeasonLow": f"{M['season_low']:.2f}",
        "SeasonRatio": f"{M['season_ratio']:.2f}",
        "TopPre": M["top_pre"], "TopPreShare": pct(M["top_pre_share"]),
        "TopLatest": M["top_latest"], "TopLatestShare": pct(M["top_latest_share"]),
        "HhiPre": fmt_int(M["hhi_pre"]), "HhiLatest": fmt_int(M["hhi_latest"]),
        "UnitsTopRegion": M["units_top_region"], "UnitsTop": M["units_top"], "UnitsAsia": M["units_asia"],
        "StayShort": M["stay_short"], "StayShortN": M["stay_short_n"],
        "StayLong": M["stay_long"], "StayLongN": M["stay_long_n"], "StayRatio": f"{M['stay_ratio']:.1f}",
        "FirstBkkPct": pct(M["first_bkk"]), "StyleBeachPct": pct(M["style_beach"]),
        "StyleCityPct": pct(M["style_city"]), "EuAndamanPct": pct(M["eu_andaman"]),
        "AseanBorderPct": pct(M["asean_border"]), "OnwardTotalM": f"{M['onward_total_m']:.1f}",
        "OnwardBkkPct": pct(M["onward_bkk"]), "OnwardTopFrom": M["onward_top_from"],
        "OnwardTopTo": M["onward_top_to"], "OnwardTopM": f"{M['onward_top_m']:.2f}",
        "PattayaBkkM": f"{M['pattaya_bkk']:.2f}",
        "NetNodes": M["net_nodes"], "NetEdges": M["net_edges"], "NetBkkEdges": M["net_bkk_edges"],
        "NetSameRegionPct": pct(M["net_same_region"]), "NetBkkDegreePct": pct(M["net_bkk_degree_share"]),
        "NetTopA": M["net_top_a"], "NetTopB": M["net_top_b"], "NetTopK": fmt_int(M["net_top_k"]),
        "RevTotalBn": fmt_int(M["rev_total_bn"]), "RevTopOne": M["rev_top1"],
        "RevTopOnePct": pct(M["rev_top1_share"]), "RevTopFivePct": pct(M["rev_top5_share"]),
        "RevHhi": fmt_int(M["rev_hhi"]), "RevGini": f"{M['rev_gini']:.2f}",
        "SpendHi": M["spend_hi"], "SpendHiV": fmt_int(M["spend_hi_v"]),
        "SpendLo": M["spend_lo"], "SpendLoV": fmt_int(M["spend_lo_v"]),
        "SpendRatio": f"{M['spend_ratio']:.0f}", "SpendRho": f"{M['spend_rho']:.2f}",
        "SpendCatOne": M["spend_cat1"], "SpendCatOnePct": pct(M["spend_cat1_share"]),
        "SpendCatTwo": M["spend_cat2"], "SpendCatTwoPct": pct(M["spend_cat2_share"]),
        "SpendCatThree": M["spend_cat3"], "SpendCatThreePct": pct(M["spend_cat3_share"]),
        "SpendTopThreePct": pct(M["spend_top3_share"]),
        "SpendTopLeaf": M["spend_top_leaf"], "SpendTopLeafPct": pct(M["spend_top_leaf_share"]),
        "ProfN": M["prof_n"], "ProfR": f"{M['prof_r_nights_spend']:.2f}",
        "ProfSpendHi": M["prof_spend_hi"], "ProfSpendHiV": fmt_int(M["prof_spend_hi_v"]),
        "ProfSpendLo": M["prof_spend_lo"], "ProfSpendLoV": fmt_int(M["prof_spend_lo_v"]),
        "ProfRepeatHi": M["prof_repeat_hi"], "ProfRepeatHiPct": pct(M["prof_repeat_hi_v"], 0),
        "SegN": fmt_int(M["seg_n"]), "SegK": M["seg_k"],
        "SegSilEmbed": f"{M['seg_sil_embed']:.2f}", "SegSilFeat": f"{M['seg_sil_feat']:.2f}",
        "SegAri": f"{M['seg_ari']:.2f}", "SegLargest": M["seg_largest"],
        "SegLargestPct": pct(M["seg_largest_share"]),
        "RecSeasonR": f"{M['rec_season_r']:.3f}", "RecSeasonMae": f"{M['rec_season_mae']:.3f}",
        "RecDropPlanted": pct(M["rec_drop_planted"]), "RecDropObs": pct(M["rec_drop_obs"]),
        "RecStayMae": f"{M['rec_stay_mae']:.2f}", "RecStayMax": f"{M['rec_stay_max']:.1f}",
        "RecDestMae": f"{M['rec_dest_mae']:.2f}", "RecDestMax": f"{M['rec_dest_max']:.2f}",
        "RecHubPlanted": pct(M["rec_hub_planted"]), "RecHubObs": pct(M["rec_hub_obs"]),
    }
    lines = ["% Generated by twelveviews.analysis -- do not edit by hand"]
    lines += [f"\\newcommand{{\\{k}}}{{{tex(v)}}}" for k, v in macros.items()]
    (TABLES / "numbers.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_tables(prov, seg, meta, M) -> None:
    w = lambda name, rows: (TABLES / f"{name}.tex").write_text("\n".join(rows) + "\n", encoding="utf-8")

    w("tab_datasets", [f"\\texttt{{{tex(k)}}} & {tex(v['description'])} & {fmt_int(v['rows'])} & "
                       f"{len(v['columns'])} \\\\" for k, v in meta.items()])

    p = prov.sort_values("revenue_mb", ascending=False).head(8)
    tot = prov.revenue_mb.sum()
    w("tab_provinces", [f"{tex(r.province)} & {tex(r.thai_region)} & {r.foreign_visitors / 1e6:.2f} & "
                        f"{fmt_int(r.spend_per_visitor)} & {r.revenue_mb / 1e3:,.1f} & "
                        f"{100 * r.revenue_mb / tot:.1f} \\\\" for r in p.itertuples()])

    rows = []
    for (_, name), d in seg.groupby(["segment_id", "segment"]):
        rows.append(f"{tex(name)} & {len(d)} & {100 * len(d) / len(seg):.1f} & "
                    f"{fmt_int(d.spend_per_day.median())} & {d.nights.median():.1f} & {int(d.age.median())} & "
                    f"{tex(d.origin_region.value_counts().index[0])} \\\\")
    w("tab_segments", rows)

    w("tab_recovery", [
        f"E1 & Seasonal profile (12 monthly indices) & Radial spiral & "
        f"$r = {M['rec_season_r']:.3f}$; MAE $= {M['rec_season_mae']:.3f}$ \\\\",
        f"E2 & Depth of the pandemic shock, 2019--2021 & Radial spiral; streamgraph & "
        f"planted {pct(M['rec_drop_planted'])}\\%; recovered {pct(M['rec_drop_obs'])}\\% \\\\",
        f"E4 & Length-of-stay medians (9 markets) & Ridgeline plot & "
        f"MAE $= {M['rec_stay_mae']:.2f}$ nights (max.\\ {M['rec_stay_max']:.1f}) \\\\",
        f"E5 & Destination preferences (36 shares) & Sankey diagram & "
        f"MAE $= {M['rec_dest_mae']:.2f}$ pp (max.\\ {M['rec_dest_max']:.2f}) \\\\",
        f"E6 & Hub share of onward trips & Chord diagram & "
        f"planted {pct(M['rec_hub_planted'])}\\%; recovered {pct(M['rec_hub_obs'])}\\% \\\\",
        f"E8 & Persona membership ({fmt_int(M['seg_n'])} respondents) & Embedding map + $k$-means & "
        f"ARI $= {M['seg_ari']:.2f}$ \\\\",
    ])

    # Appendix: generating parameters
    season = G.NORMAL_SEASON / G.NORMAL_SEASON.mean()
    w("tab_params_season", [" & ".join(L.MONTHS) + " \\\\", "\\midrule",
                            " & ".join(f"{v:.2f}" for v in season) + " \\\\"])
    w("tab_params_stay", [f"{tex(k)} & {tex(L.ORIGIN_REGIONS[rid])} & {med:.1f} & {sig:.2f} \\\\"
                          for k, (rid, med, sig) in G.STAY_PARAMS.items()])
    w("tab_params_personas", [f"{tex(L.PERSONAS[i])} & {p[0]:.2f} & {fmt_int(p[1])} & {p[2]:.1f} & {p[3]} & "
                              f"{p[4]:.1f} & {p[5]:.2f} & {p[6]:.2f} & {p[7]:.2f} & {p[8]:.2f} \\\\"
                              for i, p in enumerate(G.PERSONA_PARAMS)])


def main() -> None:
    nat, monthly = load("arrivals_by_nationality"), load("arrivals_monthly")
    stay, trips, flows = load("stay_length"), load("trip_flows"), load("region_flows")
    prov, seg = load("provinces"), load("traveler_segments")
    M = {}
    M.update(arrivals_metrics(nat, monthly))
    M.update(market_metrics(nat))
    M.update(stay_metrics(stay))
    M.update(flow_metrics(trips, flows))
    M.update(network_metrics(load("province_covisits"), prov))
    M.update(province_metrics(prov))
    M.update(spending_metrics(load("spending_breakdown")))
    M.update(profile_metrics(load("nationality_profiles")))
    M.update(segment_metrics(seg))
    M.update(recovery_metrics(monthly, stay, trips, flows, M))
    clean = {k: (v.item() if isinstance(v, np.generic) else v) for k, v in M.items()}
    (PROCESSED / "metrics.json").write_text(json.dumps(clean, indent=2), encoding="utf-8")
    write_macros(M)
    write_tables(prov, seg, json.loads((RAW / "synthetic_manifest.json").read_text(encoding="utf-8")), M)
    for k in ("peak_m", "low_m", "drop", "recovery", "hhi_pre", "hhi_latest", "rev_top5_share", "seg_ari",
              "rec_season_r", "rec_season_mae", "rec_drop_planted", "rec_stay_mae", "rec_dest_mae",
              "rec_hub_planted", "rec_hub_obs"):
        print(f"{k:18s} {clean[k]}")


if __name__ == "__main__":
    main()
