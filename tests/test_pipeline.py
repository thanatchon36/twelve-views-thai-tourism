"""Consistency checks for the synthetic data and the planted-structure recovery."""
import json

import numpy as np
import pandas as pd
import pytest

from twelveviews import analysis, data_gen, labels
from twelveviews.config import LATEST_YEAR, PROCESSED
from twelveviews.loaders import load


@pytest.fixture(scope="session", autouse=True)
def generated():
    data_gen.main()
    analysis.main()


def read(name):
    return load(name)


def test_monthly_arrivals_sum_to_annual_totals():
    annual = read("arrivals_by_nationality").groupby("year").arrivals.sum()
    monthly = read("arrivals_monthly")
    by_year = monthly.groupby(monthly.month.str[:4].astype(int)).arrivals.sum()
    assert (annual == by_year).all()


def test_trip_flows_match_latest_year_arrivals():
    total = read("arrivals_by_nationality").query("year == @LATEST_YEAR").arrivals.sum()
    assert abs(read("trip_flows").travelers.sum() / total - 1) < 0.005


def test_stay_distributions_sum_to_one():
    sums = read("stay_length").groupby("nationality").share.sum()
    assert np.allclose(sums, 1, atol=1e-3)


def test_spending_shares_sum_to_one():
    assert abs(read("spending_breakdown").share.sum() - 1) < 1e-3


def test_provinces_complete_and_revenue_identity():
    p = read("provinces")
    assert p.province.nunique() == sum(len(v) for v in labels.PROVINCES.values()) == 77
    assert np.allclose(p.revenue_mb, p.foreign_visitors * p.spend_per_visitor / 1e6, atol=0.06)


def test_covisit_provinces_exist():
    names = set(read("provinces").province)
    cov = read("province_covisits")
    assert set(cov.province_a) | set(cov.province_b) <= names


def test_generation_is_deterministic():
    pd.testing.assert_frame_equal(data_gen.arrivals_by_nationality(), data_gen.arrivals_by_nationality())


def test_largest_remainder_preserves_total():
    assert analysis.largest_remainder([0.333, 0.333, 0.334]).sum() == 100


def test_concentration_measures_are_bounded():
    assert analysis.gini([1, 1, 1, 1]) == pytest.approx(0)
    assert analysis.hhi([1]) == pytest.approx(10_000)


def test_planted_structure_is_recovered():
    m = json.loads((PROCESSED / "metrics.json").read_text())
    assert m["rec_season_r"] > 0.99
    assert m["rec_stay_mae"] < 1.0
    assert m["rec_dest_mae"] < 2.0
    assert abs(m["rec_hub_obs"] - m["rec_hub_planted"]) < 0.02
    assert m["seg_ari"] > 0.7
