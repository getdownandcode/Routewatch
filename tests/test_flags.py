"""Unit tests for baselines calculation and candidate flagging."""

import pandas as pd
import pytest
from src.costwatch.config import Config
from src.costwatch.flags import (
    compute_baselines_and_flags,
    format_percent_own,
    format_percent_similar,
    generate_sensitivity_table,
)
from src.costwatch.metrics import compute_weekly_metrics


@pytest.fixture(scope="module")
def weekly_df() -> pd.DataFrame:
    """Precompute weekly metrics from dataset."""
    return compute_weekly_metrics("data/shipment_records.csv")


def test_golden_check_sample_values(weekly_df: pd.DataFrame):
    """Assert exact match for the three golden sample route-weeks in case study specification."""
    config = Config.load("config.yaml")
    results = compute_baselines_and_flags(weekly_df, config)

    # 1. Delhi-Jaipur 2024-11-11
    dj = results[(results["route"] == "Delhi-Jaipur") & (results["week_of"] == "2024-11-11")].iloc[0]
    assert round(dj["cost_per_tonne_km"], 2) == 4.17
    assert dj["vs_own_history"] == "+35.5% vs this route's past average"
    assert dj["vs_similar_routes"] == "+21.0% vs similar-length routes this week"
    assert bool(dj["is_candidate"]) is True

    # 2. Ahmedabad-Mumbai 2025-01-20
    am = results[(results["route"] == "Ahmedabad-Mumbai") & (results["week_of"] == "2025-01-20")].iloc[0]
    assert round(am["cost_per_tonne_km"], 2) == 3.29
    assert am["vs_own_history"] == "+29.5% vs this route's past average"
    assert am["vs_similar_routes"] == "+22.5% vs similar-length routes this week"
    assert bool(am["is_candidate"]) is True

    # 3. Mumbai-Pune 2025-09-15
    mp = results[(results["route"] == "Mumbai-Pune") & (results["week_of"] == "2025-09-15")].iloc[0]
    assert round(mp["cost_per_tonne_km"], 2) == 3.98
    assert mp["vs_own_history"] == "+9.2% vs this route's past average"
    assert mp["vs_similar_routes"] == "+23.6% vs similar-length routes this week"
    assert bool(mp["is_candidate"]) is True


def test_no_lookahead_guarantee(weekly_df: pd.DataFrame):
    """Verify modifying a future week's data has zero effect on past weeks' baselines."""
    config = Config.load("config.yaml")
    base_res = compute_baselines_and_flags(weekly_df, config)

    # Corrupt future week 2025-12-22
    corrupted_df = weekly_df.copy()
    corrupted_df.loc[corrupted_df["week_of"] == "2025-12-22", "cost_per_tonne_km"] *= 100.0

    new_res = compute_baselines_and_flags(corrupted_df, config)

    # Check that any week prior to 2025-12-22 is 100% identical
    prior_base = base_res[base_res["week_of"] < "2025-12-22"].reset_index(drop=True)
    prior_new = new_res[new_res["week_of"] < "2025-12-22"].reset_index(drop=True)

    pd.testing.assert_series_equal(prior_base["vs_own_pct"], prior_new["vs_own_pct"])
    pd.testing.assert_series_equal(prior_base["vs_similar_pct"], prior_new["vs_similar_pct"])
    pd.testing.assert_series_equal(prior_base["is_candidate"], prior_new["is_candidate"])


def test_week1_has_no_baseline(weekly_df: pd.DataFrame):
    """Verify week 1 of every route has no history and cannot be flagged."""
    config = Config.load("config.yaml")
    results = compute_baselines_and_flags(weekly_df, config)

    week1 = results[results["week_of"] == "2024-01-01"]
    assert len(week1) == 7
    for _, row in week1.iterrows():
        assert row["num_history_weeks"] == 0
        assert pd.isna(row["own_baseline"])
        assert pd.isna(row["vs_own_pct"])
        assert row["vs_own_history"] == "N/A (insufficient history)"
        assert bool(row["is_candidate"]) is False


def test_peer_calculation_excludes_self(weekly_df: pd.DataFrame):
    """Verify peer average calculation strictly excludes the route itself."""
    config = Config.load("config.yaml")
    results = compute_baselines_and_flags(weekly_df, config)

    # For Short routes: only Mumbai-Pune and Delhi-Jaipur exist
    # So Mumbai-Pune's peer average must be Delhi-Jaipur's cost
    short_weeks = results[results["route_type"] == "Short"]
    for week in ["2024-01-01", "2024-06-10", "2025-01-20"]:
        mp = short_weeks[(short_weeks["route"] == "Mumbai-Pune") & (short_weeks["week_of"] == week)].iloc[0]
        dj = short_weeks[(short_weeks["route"] == "Delhi-Jaipur") & (short_weeks["week_of"] == week)].iloc[0]

        assert pytest.approx(mp["peer_baseline"], rel=1e-5) == dj["cost_per_tonne_km"]
        assert pytest.approx(dj["peer_baseline"], rel=1e-5) == mp["cost_per_tonne_km"]


def test_expected_candidate_count_and_routes(weekly_df: pd.DataFrame):
    """Verify candidate count equals exactly 9 matching the route-weeks in case study specification."""
    config = Config.load("config.yaml")
    results = compute_baselines_and_flags(weekly_df, config)

    candidates = results[results["is_candidate"]].reset_index(drop=True)
    assert len(candidates) == 9

    expected_set = {
        ("Delhi-Jaipur", "2024-11-11"),
        ("Delhi-Jaipur", "2024-11-18"),
        ("Ahmedabad-Mumbai", "2025-01-20"),
        ("Chennai-Bangalore", "2025-02-24"),
        ("Chennai-Bangalore", "2025-03-03"),
        ("Chennai-Bangalore", "2025-03-10"),
        ("Chennai-Bangalore", "2025-03-17"),
        ("Mumbai-Pune", "2025-09-15"),
        ("Mumbai-Pune", "2025-11-17"),
    }
    actual_set = set(zip(candidates["route"], candidates["week_of"]))
    assert actual_set == expected_set


def test_sensitivity_table_output(weekly_df: pd.DataFrame):
    """Verify sensitivity table markdown generation."""
    md = generate_sensitivity_table(weekly_df)
    assert "| +8% | +10% | 4 | **9** |" in md
    assert "Candidate Flag Threshold Sensitivity Analysis" in md
