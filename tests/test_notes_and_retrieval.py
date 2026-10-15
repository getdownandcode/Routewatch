"""Unit tests for notes structuring and local retrieval."""

from pathlib import Path
import pytest
from src.costwatch.notes import load_structured_notes
from src.costwatch.retrieval import NoteRetriever


def test_structured_notes_schema_and_integrity():
    """Verify all 10 notes adhere to schema and match canonical classification."""
    notes = load_structured_notes("data/notes_structured.json")
    assert len(notes) == 10

    note_ids = [n.note_id for n in notes]
    assert note_ids == [f"N{i:03d}" for i in range(1, 11)]

    # SPEC rule: ONLY N001, N002, and N003 may ever justify a cost rise
    cost_increase_ids = [n.note_id for n in notes if n.effect == "cost_increase"]
    assert sorted(cost_increase_ids) == ["N001", "N002", "N003"]

    # SPEC rule: N004 is outside dataset
    n004 = next(n for n in notes if n.note_id == "N004")
    assert n004.affects_dataset is False

    # SPEC rule: N009 is recovery to normal
    n009 = next(n for n in notes if n.note_id == "N009")
    assert n009.effect == "recovery_to_normal"

    # SPEC rule: N007 is cost decrease
    n007 = next(n for n in notes if n.note_id == "N007")
    assert n007.effect == "cost_decrease"

    # Verify windows and dates
    n001 = next(n for n in notes if n.note_id == "N001")
    assert n001.start_date == "2025-02-24"
    assert n001.end_date == "2025-03-08"
    assert n001.window_kind == "explicit_range"
    assert n001.routes == ["Chennai-Bangalore"]

    n002 = next(n for n in notes if n.note_id == "N002")
    assert n002.start_date == "2025-01-20"
    assert n002.window_kind == "single_week"
    assert n002.routes == ["Ahmedabad-Mumbai"]

    n003 = next(n for n in notes if n.note_id == "N003")
    assert n003.routes == "ALL"
    assert n003.start_date == "2025-05-05"
    assert n003.stated_magnitude_pct == [5.0, 7.0]
    assert n003.window_kind == "open_ended"


def test_retriever_chennai_bangalore_flood():
    """Verify retrieval returns N001 as top ranked note for Chennai-Bangalore in flood window."""
    retriever = NoteRetriever()
    results = retriever.retrieve("Chennai-Bangalore", "2025-02-24")
    assert len(results) > 0
    top_note, score = results[0]
    assert top_note.note_id == "N001"
    assert score > 0.4


def test_retriever_ahmedabad_mumbai_festival():
    """Verify retrieval returns N002 as top note for Ahmedabad-Mumbai festival week."""
    retriever = NoteRetriever()
    results = retriever.retrieve("Ahmedabad-Mumbai", "2025-01-20")
    assert len(results) > 0
    top_note, score = results[0]
    assert top_note.note_id == "N002"
    assert score > 0.3


def test_retriever_prefilter_routes():
    """Verify retrieval only returns notes that match route or applies to ALL."""
    retriever = NoteRetriever()
    results = retriever.retrieve("Mumbai-Pune", "2025-09-15")

    for note, _ in results:
        assert note.routes == "ALL" or "Mumbai-Pune" in note.routes
        # Must not contain notes specifically for other routes (e.g. N001 Chennai-Bangalore)
        assert note.note_id not in ["N001", "N002", "N005", "N007", "N008", "N009"]
