"""Generate the ten synthetic datasets used in the study.

Every table is SYNTHETIC. Shapes follow broad, publicly known patterns of
inbound tourism to Thailand (a December-January high season, the collapse
of arrivals in 2020-2021, revenue concentrated in a few destinations), but
no value is an official statistic and none should be cited as one.

Each table is written to data/raw/synthetic_<name>.csv; the loader reads a real
data/raw/<name>.csv instead whenever one is present.

Run:  python -m twelveviews.cli synthetic
"""
import json

import numpy as np
import pandas as pd
from scipy.stats import lognorm
from sklearn.manifold import TSNE
from sklearn.preprocessing import StandardScaler

from . import labels as L
from .config import LATEST_YEAR, RAW, SEED, YEARS


def rng(offset: int) -> np.random.Generator:
    """Independent, reproducible stream for each dataset."""
    return np.random.default_rng(SEED + offset)


# ---------------------------------------------------------------------------
# 1-2. Arrivals by nationality (annual) and total arrivals (monthly)
# ---------------------------------------------------------------------------
# Thousands of arrivals per year, 2010-2025, for ten named markets.
COUNTRY_PATHS = {
    "China":          (0, [1120, 1720, 2790, 4640, 4620, 7930, 8760, 9810, 10540, 11020, 1250, 13, 275, 3520, 6730, 4640]),
    "Malaysia":      (1, [2060, 2510, 2560, 3000, 2610, 3420, 3530, 3360, 4100, 4170, 640, 5, 1960, 4630, 4950, 4430]),
    "Russia":       (2, [1050, 1300, 1320, 1750, 1610, 880, 1090, 1350, 1470, 1480, 430, 30, 400, 1480, 1740, 1880]),
    "South Korea":     (0, [810, 1010, 1170, 1300, 1120, 1370, 1460, 1710, 1800, 1890, 260, 10, 600, 1650, 1870, 1690]),
    "India":       (3, [760, 910, 1010, 1050, 930, 1070, 1190, 1410, 1600, 1990, 200, 6, 980, 1630, 2120, 2310]),
    "Laos":      (1, [720, 890, 980, 980, 1050, 1230, 1390, 1610, 1720, 1850, 200, 1, 750, 1500, 1420, 1310]),
    "Japan":        (0, [990, 1130, 1370, 1540, 1270, 1380, 1440, 1540, 1660, 1810, 330, 10, 270, 980, 1170, 1210]),
    "United States":   (4, [610, 680, 770, 820, 760, 870, 970, 1060, 1120, 1170, 190, 20, 500, 900, 1110, 1150]),
    "United Kingdom": (2, [810, 870, 870, 910, 910, 950, 1000, 990, 990, 1000, 200, 20, 400, 820, 1000, 1010]),
    "Germany":       (2, [610, 620, 680, 740, 720, 760, 830, 850, 870, 880, 240, 20, 400, 720, 880, 900]),
}
# Residual groups: (region_id, thousands in 2010, thousands in 2019)
GROUP_PATHS = {
    "Other East Asia":   (0, 600, 1500),
    "Other ASEAN":          (1, 2200, 5300),
    "Other Europe":            (2, 2600, 3500),
    "Other South Asia":        (3, 200, 330),
    "Other Americas":          (4, 160, 330),
    "Oceania":            (5, 750, 900),
    "Middle East & Africa": (5, 600, 720),
}
PANDEMIC_FACTORS = [0.17, 0.02, 0.33, 0.74, 0.92, 0.93]  # 2020-2025 relative to 2019


def arrivals_by_nationality() -> pd.DataFrame:
    r = rng(1)
    rows = []
    for name, (rid, path) in COUNTRY_PATHS.items():
        for year, k in zip(YEARS, path):
            rows.append((year, name, rid, "country", k * 1000 * (1 + r.normal(0, 0.004))))
    for name, (rid, v2010, v2019) in GROUP_PATHS.items():
        pre = np.linspace(v2010, v2019, 10) * (1 + r.normal(0, 0.02, 10))
        pre[4] *= 0.95                                   # 2014 slowdown
        post = [v2019 * f * (1 + r.normal(0, 0.02)) for f in PANDEMIC_FACTORS]
        for year, k in zip(YEARS, np.r_[pre, post]):
            rows.append((year, name, rid, "group", k * 1000))
    df = pd.DataFrame(rows, columns=["year", "nationality", "region_id", "kind", "arrivals"])
    df["origin_region"] = df.region_id.map(dict(enumerate(L.ORIGIN_REGIONS)))
    df["arrivals"] = df.arrivals.round().astype(int)
    return df[["year", "nationality", "origin_region", "region_id", "kind", "arrivals"]]


# Monthly weights; a "normal" year has a December-January peak and a
# May / September trough. Pandemic years get their own shapes.
NORMAL_SEASON = np.array([1.13, 1.07, 0.99, 0.88, 0.78, 0.82, 0.95, 0.97, 0.78, 0.86, 1.00, 1.17])
SPECIAL_SEASON = {
    2014: NORMAL_SEASON * np.array([1, 1, 1, 1, .82, .85, .90, 1, 1, 1, 1, 1]),
    2020: np.array([.565, .315, .115, .0004, .0004, .0005, .0006, .0008, .0009, .0012, .0015, .002]),
    2021: np.array([.035, .03, .03, .035, .03, .04, .045, .04, .045, .07, .24, .39]),
    2022: np.array([.012, .014, .02, .027, .047, .07, .096, .106, .105, .137, .157, .209]),
    2023: np.array([.077, .078, .078, .072, .067, .074, .09, .09, .074, .083, .095, .122]),
    2025: NORMAL_SEASON * np.array([1, 1, 1, .95, .94, .94, .95, .95, .96, 1, 1, 1]),
}


def arrivals_monthly(nat: pd.DataFrame) -> pd.DataFrame:
    r = rng(2)
    totals = nat.groupby("year").arrivals.sum()
    rows = []
    for year in YEARS:
        w = SPECIAL_SEASON.get(year, NORMAL_SEASON) * (1 + r.normal(0, 0.025, 12))
        w = w / w.sum()
        months = np.floor(totals[year] * w).astype(int)
        months[-1] += totals[year] - months.sum()   # monthly values sum to the annual total
        rows += [(f"{year}-{m + 1:02d}", int(v)) for m, v in enumerate(months)]
    return pd.DataFrame(rows, columns=["month", "arrivals"])


# ---------------------------------------------------------------------------
# 3-4. Length of stay and nationality profiles
# ---------------------------------------------------------------------------
# (region_id, median nights, log-sd) of a log-normal length of stay
STAY_PARAMS = {
    "Malaysia": (1, 3.2, 0.45), "India": (3, 5.0, 0.40), "South Korea": (0, 5.5, 0.35),
    "Japan": (0, 6.5, 0.45), "China": (0, 6.8, 0.35), "United States": (4, 11.0, 0.50),
    "Russia": (2, 12.5, 0.35), "United Kingdom": (2, 14.5, 0.45), "Germany": (2, 16.5, 0.45),
}
MAX_NIGHTS = 30


def stay_distribution(median: float, sigma: float) -> np.ndarray:
    """Share of trips lasting 1..MAX_NIGHTS nights (discretised log-normal)."""
    edges = np.arange(0.5, MAX_NIGHTS + 1.5)
    cdf = lognorm.cdf(edges, s=sigma, scale=median)
    p = np.diff(cdf)
    return p / p.sum()


def stay_length() -> pd.DataFrame:
    rows = []
    for name, (rid, med, sig) in STAY_PARAMS.items():
        for n, p in zip(range(1, MAX_NIGHTS + 1), stay_distribution(med, sig)):
            rows.append((name, L.ORIGIN_REGIONS[rid], rid, n, round(float(p), 5)))
    return pd.DataFrame(rows, columns=["nationality", "origin_region", "region_id", "nights", "share"])


# spend per day (THB), repeat share, independent-travel share, beach share, median age
PROFILE_PARAMS = {
    "China": (0, 6200, .42, .62, .55, 31), "Malaysia": (1, 4300, .78, .75, .25, 38),
    "Russia": (2, 4500, .62, .55, .85, 39), "South Korea": (0, 5600, .55, .70, .45, 36),
    "India": (3, 6300, .40, .55, .48, 32), "Japan": (0, 6000, .68, .78, .30, 42),
    "Laos": (1, 3000, .82, .88, .08, 33), "United States": (4, 5900, .48, .86, .50, 41),
    "United Kingdom": (2, 5300, .58, .88, .70, 43), "Germany": (2, 4800, .55, .87, .72, 45),
    "France": (2, 4900, .50, .86, .66, 40), "Australia": (5, 6100, .60, .85, .68, 42),
    "Singapore": (1, 6500, .80, .84, .30, 39), "Vietnam": (1, 4400, .45, .58, .35, 32),
    "Taiwan": (0, 5700, .52, .72, .40, 37),
}
EXTRA_NIGHTS = {"Laos": 2.5, "France": 15.0, "Australia": 11.5, "Singapore": 3.8,
                "Vietnam": 4.5, "Taiwan": 6.2}


def nationality_profiles() -> pd.DataFrame:
    rows = []
    for name, (rid, spend, rep, ind, beach, age) in PROFILE_PARAMS.items():
        if name in STAY_PARAMS:   # mean nights consistent with the stay distribution
            _, med, sig = STAY_PARAMS[name]
            nights = float(np.arange(1, MAX_NIGHTS + 1) @ stay_distribution(med, sig))
        else:
            nights = EXTRA_NIGHTS[name]
        rows.append((name, L.ORIGIN_REGIONS[rid], rid, spend, round(nights, 1), rep, ind, beach, age))
    return pd.DataFrame(rows, columns=["nationality", "origin_region", "region_id", "spend_per_day",
                                       "avg_nights", "repeat_share", "independent_share",
                                       "beach_share", "median_age"])


# ---------------------------------------------------------------------------
# 5-6. Trip flows (origin -> destination -> style) and inter-destination flows
# ---------------------------------------------------------------------------
P_DEST = np.array([          # rows: origin regions, cols: DEST_CLUSTERS
    [.50, .18, .06, .12, .08, .06],
    [.38, .05, .03, .06, .04, .44],
    [.25, .30, .15, .15, .10, .05],
    [.50, .15, .03, .25, .03, .04],
    [.40, .18, .12, .08, .17, .05],
    [.35, .30, .12, .10, .08, .05],
])
P_STYLE = np.array([         # rows: DEST_CLUSTERS, cols: TRIP_STYLES
    [.05, .62, .18, .15],
    [.85, .05, .08, .02],
    [.88, .02, .08, .02],
    [.62, .20, .08, .10],
    [.02, .18, .75, .05],
    [.08, .45, .32, .15],
])
STYLE_TILT = np.array([      # origin-specific tilt of the style mix
    [0.8, 1.3, 1.0, 1.0],
    [0.9, 1.2, 1.0, 1.1],
    [1.3, 0.7, 1.1, 0.8],
    [0.9, 1.0, 0.8, 1.6],
    [1.0, 0.9, 1.3, 1.0],
    [1.2, 0.9, 1.0, 0.9],
])


def trip_flows(nat: pd.DataFrame) -> pd.DataFrame:
    r = rng(5)
    origin_tot = nat[nat.year == LATEST_YEAR].groupby("region_id").arrivals.sum()
    rows = []
    for o, total in origin_tot.items():
        pd_ = P_DEST[o] * (1 + r.normal(0, .04, 6)); pd_ /= pd_.sum()
        for d in range(6):
            ps = P_STYLE[d] * STYLE_TILT[o]; ps /= ps.sum()
            for s in range(4):
                v = int(round(total * pd_[d] * ps[s], -2))
                if v > 0:
                    rows.append((L.ORIGIN_REGIONS[o], o, L.DEST_CLUSTERS[d], d, L.TRIP_STYLES[s], s, v))
    return pd.DataFrame(rows, columns=["origin_region", "region_id", "destination", "dest_id",
                                       "style", "style_id", "travelers"])


REGION_FLOW = np.array([     # thousands of onward trips, row = from, col = to
    [0, 2400, 900, 2600, 1500, 900],
    [1900, 0, 500, 150, 250, 120],
    [700, 450, 0, 80, 120, 60],
    [2100, 120, 60, 0, 90, 150],
    [1300, 300, 150, 80, 0, 220],
    [800, 100, 50, 120, 180, 0],
])


def region_flows() -> pd.DataFrame:
    r = rng(6)
    rows = []
    for i in range(6):
        for j in range(6):
            if i != j:
                v = int(round(REGION_FLOW[i, j] * 1000 * (1 + r.normal(0, .05)), -2))
                rows.append((L.DEST_CLUSTERS[i], i, L.DEST_CLUSTERS[j], j, v))
    return pd.DataFrame(rows, columns=["from", "from_id", "to", "to_id", "travelers"])


# ---------------------------------------------------------------------------
# 7-8. Provinces and province co-visits
# ---------------------------------------------------------------------------
# foreign visitors (thousands), spend per visitor per trip (THB)
NOTABLE_PROVINCES = {
    "Bangkok": (21800, 33500), "Phuket": (9600, 51500), "Chonburi": (7700, 30500),
    "Krabi": (3500, 38500), "Surat Thani": (3200, 46500), "Chiang Mai": (2900, 26500),
    "Phang Nga": (2050, 40500), "Songkhla": (2100, 9800), "Phra Nakhon Si Ayutthaya": (1650, 4800),
    "Prachuap Khiri Khan": (1180, 29500), "Nong Khai": (980, 4300), "Kanchanaburi": (860, 12800),
    "Chiang Rai": (790, 15200), "Samut Prakan": (720, 8800), "Sa Kaeo": (690, 2700),
    "Rayong": (640, 21500), "Tak": (560, 3100), "Trat": (520, 26500), "Mukdahan": (480, 3500),
    "Udon Thani": (430, 9200), "Narathiwat": (390, 3000), "Phetchaburi": (340, 11200),
    "Satun": (320, 16500), "Ranong": (310, 9300), "Nakhon Phanom": (300, 3900),
    "Nakhon Ratchasima": (270, 8600), "Samut Songkhram": (270, 3700), "Trang": (250, 14200),
    "Khon Kaen": (240, 9600), "Sukhothai": (210, 7100), "Yala": (210, 3200),
    "Mae Hong Son": (190, 14300), "Chanthaburi": (190, 11400), "Nakhon Pathom": (180, 4600),
    "Ubon Ratchathani": (170, 6600), "Nakhon Si Thammarat": (160, 8200), "Chumphon": (150, 9000),
    "Phitsanulok": (125, 7200), "Lampang": (115, 8100), "Buriram": (115, 9100),
    "Lopburi": (110, 4300), "Loei": (95, 7600), "Nan": (92, 9600), "Lamphun": (82, 5100),
}


def provinces() -> pd.DataFrame:
    r = rng(7)
    rows = []
    for rid, names in L.PROVINCES.items():
        for name in names:
            if name in NOTABLE_PROVINCES:
                k, spend = NOTABLE_PROVINCES[name]
                visitors = k * 1000 * (1 + r.normal(0, .02))
                spend = spend * (1 + r.normal(0, .02))
            else:
                visitors = r.uniform(15, 90) * 1000
                spend = r.uniform(2800, 8500)
            rows.append((name, L.THAI_REGIONS[rid], rid, int(round(visitors, -2)), int(round(spend, -1))))
    df = pd.DataFrame(rows, columns=["province", "thai_region", "thai_region_id",
                                     "foreign_visitors", "spend_per_visitor"])
    df["revenue_mb"] = (df.foreign_visitors * df.spend_per_visitor / 1e6).round(1)
    return df


# Pairs of provinces visited on the same trip (thousands of trips)
COVISITS = """
Phuket,Krabi,820;Phuket,Phang Nga,760;Krabi,Phang Nga,420;Krabi,Trang,160;Trang,Satun,120;
Krabi,Surat Thani,380;Phuket,Surat Thani,330;Songkhla,Satun,90;Songkhla,Trang,70;
Bangkok,Phuket,1150;Bangkok,Chonburi,1400;Bangkok,Chiang Mai,880;
Bangkok,Surat Thani,560;Bangkok,Krabi,510;Bangkok,Phra Nakhon Si Ayutthaya,900;
Bangkok,Kanchanaburi,420;Bangkok,Prachuap Khiri Khan,380;Bangkok,Samut Songkhram,300;
Bangkok,Nakhon Pathom,160;Bangkok,Rayong,210;Bangkok,Chiang Rai,190;
Bangkok,Trat,150;Bangkok,Songkhla,140;Bangkok,Phang Nga,160;
Bangkok,Udon Thani,90;Bangkok,Khon Kaen,85;Bangkok,Nakhon Ratchasima,110;
Bangkok,Sukhothai,70;Bangkok,Lopburi,60;Bangkok,Phetchaburi,120;
Bangkok,Nong Khai,75;Bangkok,Buriram,50;Bangkok,Ubon Ratchathani,45;
Bangkok,Tak,25;Bangkok,Chanthaburi,70;Bangkok,Mae Hong Son,30;
Bangkok,Phitsanulok,40;Bangkok,Trang,40;
Chiang Mai,Chiang Rai,420;Chiang Mai,Mae Hong Son,170;Chiang Mai,Lamphun,150;Chiang Mai,Lampang,110;
Chiang Rai,Nan,50;Chiang Mai,Nan,45;Lampang,Lamphun,30;Chiang Mai,Sukhothai,85;Sukhothai,Phitsanulok,60;
Chiang Mai,Tak,30;Phra Nakhon Si Ayutthaya,Lopburi,70;Phra Nakhon Si Ayutthaya,Sukhothai,50;
Nakhon Pathom,Samut Songkhram,90;Nakhon Pathom,Kanchanaburi,140;Samut Songkhram,Phetchaburi,80;
Chonburi,Rayong,420;Rayong,Chanthaburi,120;Chanthaburi,Trat,160;Chonburi,Trat,110;
Chonburi,Phra Nakhon Si Ayutthaya,140;Prachuap Khiri Khan,Phetchaburi,230;
Udon Thani,Nong Khai,280;Khon Kaen,Udon Thani,90;Nakhon Ratchasima,Buriram,80;Udon Thani,Loei,60;
Khon Kaen,Nakhon Ratchasima,70;Nong Khai,Loei,40;Nakhon Ratchasima,Ubon Ratchathani,25;
Chiang Mai,Phuket,220;Chiang Mai,Krabi,120;Chiang Mai,Surat Thani,90;Chonburi,Phuket,180;
Chonburi,Chiang Mai,120;Phuket,Prachuap Khiri Khan,60;Krabi,Chonburi,70;Songkhla,Phuket,60;
Chiang Rai,Phuket,40;Udon Thani,Chiang Mai,35
"""


def province_covisits() -> pd.DataFrame:
    r = rng(8)
    rows = []
    for item in COVISITS.replace("\n", "").split(";"):
        if item.strip():
            a, b, k = item.split(",")
            rows.append((a.strip(), b.strip(), int(round(float(k) * 1000 * (1 + r.normal(0, .05)), -2))))
    return pd.DataFrame(rows, columns=["province_a", "province_b", "trips"])


# ---------------------------------------------------------------------------
# 9. Spending structure (three-level hierarchy, shares of total spending)
# ---------------------------------------------------------------------------
SPENDING = [
    ("Accommodation", 0, "Hotels", "Five-star hotels", 9.0), ("Accommodation", 0, "Hotels", "Three- and four-star hotels", 12.5),
    ("Accommodation", 0, "Guesthouses & hostels", "", 3.5), ("Accommodation", 0, "Short-term rentals", "", 3.5),
    ("Shopping", 1, "Department stores", "Fashion", 6.5), ("Shopping", 1, "Department stores", "Cosmetics", 5.0),
    ("Shopping", 1, "Department stores", "Electronics", 2.0), ("Shopping", 1, "Markets & souvenirs", "", 6.0),
    ("Shopping", 1, "Duty-free", "", 4.5),
    ("Food & drink", 2, "Restaurants", "Thai cuisine", 7.5),
    ("Food & drink", 2, "Restaurants", "International cuisine", 4.5),
    ("Food & drink", 2, "Street food", "", 4.0), ("Food & drink", 2, "Bars & cafés", "", 5.0),
    ("Entertainment & activities", 3, "Spa & massage", "", 3.5),
    ("Entertainment & activities", 3, "Tours & activities", "Island & diving tours", 3.5),
    ("Entertainment & activities", 3, "Tours & activities", "Cultural tours", 2.0),
    ("Entertainment & activities", 3, "Shows & nightlife", "", 4.0),
    ("Domestic transport", 4, "Domestic flights", "", 4.0),
    ("Domestic transport", 4, "Car hire & taxis", "", 4.5),
    ("Domestic transport", 4, "Boats & ferries", "", 2.0),
    ("Other", 5, "Other services", "", 3.0),
]


def spending_breakdown() -> pd.DataFrame:
    df = pd.DataFrame(SPENDING, columns=["category", "cat_id", "subcategory", "item", "share_pct"])
    df["share"] = (df.share_pct / df.share_pct.sum()).round(4)
    return df.drop(columns="share_pct")


# ---------------------------------------------------------------------------
# 10. Traveller survey -> t-SNE embedding
# ---------------------------------------------------------------------------
# share, spend/day, nights, age, group size, beach, shopping, culture, nightlife
PERSONA_PARAMS = [
    (.22, 4800, 13.0, 41, 2.1, .85, .25, .25, .45),
    (.24, 6500, 4.5, 33, 2.5, .15, .90, .30, .50),
    (.16, 3800, 8.0, 38, 2.0, .20, .30, .90, .20),
    (.10, 1800, 21.0, 25, 1.4, .60, .15, .60, .70),
    (.10, 9500, 3.2, 42, 1.2, .10, .40, .10, .40),
    (.18, 5200, 6.0, 37, 4.0, .70, .55, .35, .10),
]
PERSONA_ORIGINS = np.array([      # P(origin region | persona)
    [.13, .05, .55, .05, .10, .12],
    [.55, .25, .05, .08, .04, .03],
    [.30, .10, .35, .05, .15, .05],
    [.10, .04, .50, .04, .20, .12],
    [.35, .20, .15, .20, .07, .03],
    [.35, .25, .10, .20, .05, .05],
])
N_TRAVELLERS = 1200


def traveler_segments() -> pd.DataFrame:
    r = rng(10)
    shares = np.array([p[0] for p in PERSONA_PARAMS])
    seg = r.choice(len(PERSONA_PARAMS), size=N_TRAVELLERS, p=shares / shares.sum())
    feats, rows = [], []
    for s in seg:
        _, spend, nights, age, group, beach, shop, culture, night = PERSONA_PARAMS[s]
        x = [
            np.log(spend) + r.normal(0, .32),
            max(1.0, nights * np.exp(r.normal(0, .42))),
            float(np.clip(age + r.normal(0, 9), 18, 80)),
            max(1.0, group + r.normal(0, 1.0)),
            *np.clip(np.array([beach, shop, culture, night]) + r.normal(0, .2, 4), 0, 1),
        ]
        feats.append(x)
        o = r.choice(6, p=PERSONA_ORIGINS[s])
        rows.append((L.PERSONAS[s], int(s), L.ORIGIN_REGIONS[o], int(o),
                     int(round(np.exp(x[0]), -1)), round(x[1], 1), int(round(x[2])), round(x[3], 1)))
    X = StandardScaler().fit_transform(np.array(feats))
    xy = TSNE(n_components=2, perplexity=40, init="pca", random_state=SEED).fit_transform(X)
    df = pd.DataFrame(rows, columns=["segment", "segment_id", "origin_region", "region_id",
                                     "spend_per_day", "nights", "age", "group_size"])
    df.insert(0, "y", xy[:, 1].round(3))
    df.insert(0, "x", xy[:, 0].round(3))
    pd.DataFrame(X, columns=["log_spend", "nights", "age", "group", "beach", "shopping",
                             "culture", "nightlife"]).round(4).to_csv(RAW / "synthetic_traveler_features.csv", index=False)
    return df


# ---------------------------------------------------------------------------
DESCRIPTIONS = {
    "arrivals_by_nationality": "Annual international arrivals by market",
    "arrivals_monthly": "Monthly international arrivals, all markets",
    "stay_length": "Distribution of nights per trip by market",
    "nationality_profiles": "Behavioural profiles of fifteen markets",
    "trip_flows": "Origin region, main destination and trip style, latest year",
    "region_flows": "Onward trips between destination clusters",
    "provinces": "Foreign visitors, spend per visitor and revenue by province",
    "province_covisits": "Pairs of provinces visited on the same trip",
    "spending_breakdown": "Three-level structure of visitor spending",
    "traveler_segments": "Individual survey responses with t-SNE coordinates",
}


def main() -> None:
    nat = arrivals_by_nationality()
    tables = {
        "arrivals_by_nationality": nat,
        "arrivals_monthly": arrivals_monthly(nat),
        "stay_length": stay_length(),
        "nationality_profiles": nationality_profiles(),
        "trip_flows": trip_flows(nat),
        "region_flows": region_flows(),
        "provinces": provinces(),
        "province_covisits": province_covisits(),
        "spending_breakdown": spending_breakdown(),
        "traveler_segments": traveler_segments(),
    }
    meta = {}
    for name, df in tables.items():
        df.to_csv(RAW / f"synthetic_{name}.csv", index=False)
        meta[name] = {"rows": len(df), "columns": list(df.columns), "description": DESCRIPTIONS[name]}
        print(f"{name:26s} {len(df):5d} rows")
    (RAW / "synthetic_manifest.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
