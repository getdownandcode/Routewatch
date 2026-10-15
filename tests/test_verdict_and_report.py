"""Unit tests for verdict gates, output CSV contract compliance, and trap rejection."""

import csv
from pathlib import Path
import pandas as pd
import pytest
from src.costwatch.config import Config
from src.costwatch.notes import load_structured_notes
from src.costwatch.report import CONTRACT_COLUMNS
from src.costwatch.retrieval import NoteRetriever
from src.costwatch.verdict import check_note_applicability, evaluate_candidate
from run import run_pipeline


@pytest.fixture(scope="module")
def config() -> Config:
    return Config.load("config.yaml")


@pytest.fixture(scope="module")
def retriever() -> NoteRetriever:
    return NoteRetriever()


def test_output_csv_contract_schema_and_order():
    """Assert output CSV has identical header, column order, and structure to sample contract."""
    with open("data/sample_output_format_v2.csv", "r", encoding="utf-8") as f:
        sample_header = f.readline().strip().split(",")

    output_df = pd.read_csv("outputs/output.csv")
    assert list(output_df.columns) == sample_header
    assert list(output_df.columns) == CONTRACT_COLUMNS


def test_guardrail_only_permitted_notes_justify():
    """Assert non-negotiable guardrail: ONLY N001, N002, N003 may ever justify an anomaly."""
    output_df = pd.read_csv("outputs/output.csv")
    justified = output_df[output_df["flagged"] == "No (justified)"]

    allowed_ids = {"N001", "N002", "N003"}
    for _, row in justified.iterrows():
        nid = str(row["matched_note_id"]).strip()
        assert nid in allowed_ids, f"Illegal note ID {nid} found in justified row!"


def test_guardrail_matched_note_id_blank_for_unexplained():
    """Assert unexplained rows MUST have blank matched_note_id, justified rows MUST have note ID."""
    output_df = pd.read_csv("outputs/output.csv")
    for _, row in output_df.iterrows():
        flag = str(row["flagged"]).strip()
        nid = "" if pd.isna(row["matched_note_id"]) else str(row["matched_note_id"]).strip()
        if flag == "No (justified)":
            assert len(nid) > 0, "Justified row missing matched_note_id"
        elif flag == "Yes":
            assert len(nid) == 0, f"Unexplained row has non-blank matched_note_id: {nid}"
        else:
            pytest.fail(f"Unexpected flagged status: {flag}")


def test_deterministic_trap_notes_rejection(config: Config, retriever: NoteRetriever):
    """Verify each of the 7 trap notes (N004-N010) is deterministically rejected by the gate."""
    notes_by_id = {n.note_id: n for n in retriever.notes}

    # N004: Not in dataset
    n004 = notes_by_id["N004"]
    ok, rej = check_note_applicability(n004, "Delhi-Jaipur", pd.to_datetime("2024-03-11").date(), 10.0, config)
    assert not ok
    assert "not part of this dataset" in rej

    # N005: No cost effect (maintenance delays only)
    n005 = notes_by_id["N005"]
    ok, rej = check_note_applicability(n005, "Mumbai-Delhi", pd.to_datetime("2024-07-29").date(), 10.0, config)
    assert not ok
    assert "not significantly affected" in rej

    # N006: Stable demand, no disruptions (check in its active week)
    n006 = notes_by_id["N006"]
    ok, rej = check_note_applicability(n006, "Mumbai-Pune", pd.to_datetime("2025-09-22").date(), 10.0, config)
    assert not ok
    assert "no major disruptions" in rej

    # N007: Cost decrease (resurfacing)
    n007 = notes_by_id["N007"]
    ok, rej = check_note_applicability(n007, "Delhi-Jaipur", pd.to_datetime("2024-05-20").date(), 10.0, config)
    assert not ok
    assert "cost_decrease" in rej or "improved conditions" in rej

    # N008: No disruption
    n008 = notes_by_id["N008"]
    ok, rej = check_note_applicability(n008, "Kolkata-Bhubaneswar", pd.to_datetime("2025-06-09").date(), 10.0, config)
    assert not ok
    assert "no disruptions" in rej or "no_cost_effect" in rej

    # N009: Recovery to normal
    n009 = notes_by_id["N009"]
    ok, rej = check_note_applicability(n009, "Chennai-Bangalore", pd.to_datetime("2025-03-17").date(), 10.0, config)
    assert not ok
    assert "normal conditions" in rej or "recovery_to_normal" in rej

    # N010: Costs absorbed without rate change
    n010 = notes_by_id["N010"]
    ok, rej = check_note_applicability(n010, "Mumbai-Pune", pd.to_datetime("2025-10-27").date(), 10.0, config)
    assert not ok
    assert "without a rate change" in rej or "no_cost_effect" in rej


def test_golden_sample_rows_present_in_output():
    """Verify the 3 sample rows from sample_output_format_v2 appear in output with identical verdicts."""
    output_df = pd.read_csv("outputs/output.csv")

    # 1. Delhi-Jaipur 2024-11-11
    dj = output_df[(output_df["route"] == "Delhi-Jaipur") & (output_df["week_of"] == "2024-11-11")].iloc[0]
    assert dj["flagged"] == "Yes"
    assert pd.isna(dj["matched_note_id"]) or dj["matched_note_id"] == ""
    assert "No matching note found" in dj["reason"]

    # 2. Ahmedabad-Mumbai 2025-01-20
    am = output_df[(output_df["route"] == "Ahmedabad-Mumbai") & (output_df["week_of"] == "2025-01-20")].iloc[0]
    assert am["flagged"] == "No (justified)"
    assert am["matched_note_id"] == "N002"
    assert "regional festival week" in am["reason"]

    # 3. Mumbai-Pune 2025-09-15
    mp = output_df[(output_df["route"] == "Mumbai-Pune") & (output_df["week_of"] == "2025-09-15")].iloc[0]
    assert mp["flagged"] == "Yes"
    assert pd.isna(mp["matched_note_id"]) or mp["matched_note_id"] == ""
    assert "N006" in mp["reason"]
    assert "stable demand" in mp["reason"]
