"""Unit tests for weekly metrics aggregation."""

from pathlib import Path
import pandas as pd
import pytest
from src.costwatch.metrics import compute_weekly_metrics, get_week_monday, save_weekly_metrics


def test_get_week_monday():
    """Verify Sunday maps to prior Monday, Monday maps to itself, and midweek maps correctly."""
    assert get_week_monday("2024-01-01") == "2024-01-01"  # Monday
    assert get_week_monday("2024-01-03") == "2024-01-01"  # Wednesday
    assert get_week_monday("2024-01-07") == "2024-01-01"  # Sunday
    assert get_week_monday("2024-01-08") == "2024-01-08"  # Next Monday
    assert get_week_monday("2025-12-28") == "2025-12-22"  # Sunday to Monday


def test_compute_weekly_metrics_full_dataset():
    """Verify aggregation across 104 weeks and 7 routes produces exactly 728 non-null rows."""
    shipments_path = "data/shipment_records.csv"
    weekly = compute_weekly_metrics(shipments_path)

    # Must be 7 routes * 104 weeks = 728 rows
    assert len(weekly) == 728
    assert weekly["route"].nunique() == 7
    assert weekly["week_of"].nunique() == 104

    # No NaN values anywhere
    assert not weekly.isnull().values.any()

    # Route types must be constant per route
    route_types = weekly.groupby("route")["route_type"].nunique()
    assert (route_types == 1).all()


def test_hand_computed_route_week():
    """Verify aggregation matches manual arithmetic for Mumbai-Pune in week 2024-01-01."""
    raw = pd.read_csv("data/shipment_records.csv")
    raw["route"] = raw["origin"].str.strip() + "-" + raw["destination"].str.strip()
    raw["week_of"] = raw["shipment_date"].apply(get_week_monday)

    subset = raw[(raw["route"] == "Mumbai-Pune") & (raw["week_of"] == "2024-01-01")]
    expected_cost = subset["freight_cost_inr"].sum()
    expected_tkm = (subset["quantity_tonnes"] * subset["distance_km"]).sum()
    expected_rate = expected_cost / expected_tkm

    weekly = compute_weekly_metrics("data/shipment_records.csv")
    actual = weekly[(weekly["route"] == "Mumbai-Pune") & (weekly["week_of"] == "2024-01-01")].iloc[0]

    assert pytest.approx(actual["total_cost"], rel=1e-5) == expected_cost
    assert pytest.approx(actual["total_tonne_km"], rel=1e-5) == expected_tkm
    assert pytest.approx(actual["cost_per_tonne_km"], rel=1e-5) == expected_rate


def test_save_weekly_metrics(tmp_path: Path):
    """Verify writing metrics to CSV creates a valid, readable file."""
    weekly = compute_weekly_metrics("data/shipment_records.csv")
    out_file = tmp_path / "weekly_metrics.csv"
    save_weekly_metrics(weekly, str(out_file))

    loaded = pd.read_csv(out_file)
    assert len(loaded) == 728
    assert list(loaded.columns) == ["route", "route_type", "week_of", "total_cost", "total_tonne_km", "cost_per_tonne_km"]
