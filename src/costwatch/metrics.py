"""Weekly freight metrics aggregation and calculations."""

from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Tuple
import pandas as pd


def get_week_monday(date_str: str) -> str:
    """Return the Monday date string (YYYY-MM-DD) for the given YYYY-MM-DD date."""
    d = datetime.strptime(date_str, "%Y-%m-%d").date()
    monday = d - timedelta(days=d.weekday())
    return monday.strftime("%Y-%m-%d")


def compute_weekly_metrics(shipment_csv_path: str) -> pd.DataFrame:
    """Load shipment records and aggregate metrics per route-week.
    
    Formula:
        cost_per_tonne_km = sum(freight_cost_inr) / sum(quantity_tonnes * distance_km)
    Returns:
        DataFrame sorted deterministically by route and week_of.
    """
    path = Path(shipment_csv_path)
    if not path.exists():
        raise FileNotFoundError(f"Shipments file not found: {shipment_csv_path}")

    df = pd.read_csv(path)
    required_cols = [
        "shipment_id", "origin", "destination", "route_type",
        "quantity_tonnes", "distance_km", "freight_cost_inr", "shipment_date"
    ]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Shipment records missing required columns: {missing}")

    # Build route key and calculate shipment-level tonne-km
    df["route"] = df["origin"].str.strip() + "-" + df["destination"].str.strip()
    df["week_of"] = df["shipment_date"].apply(get_week_monday)
    df["tonne_km"] = df["quantity_tonnes"] * df["distance_km"]

    # Aggregate by route, route_type, and week_of
    weekly = df.groupby(["route", "route_type", "week_of"], as_index=False).agg(
        total_cost=("freight_cost_inr", "sum"),
        total_tonne_km=("tonne_km", "sum")
    )

    weekly["cost_per_tonne_km"] = weekly["total_cost"] / weekly["total_tonne_km"]

    # Deterministic sort: route alphabetically, then week_of chronologically
    weekly = weekly.sort_values(by=["route", "week_of"]).reset_index(drop=True)
    return weekly


def save_weekly_metrics(weekly_df: pd.DataFrame, output_path: str) -> None:
    """Save weekly metrics to CSV deterministically."""
    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    weekly_df.to_csv(out_file, index=False, float_format="%.6f")
