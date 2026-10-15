"""Deterministic verdict gate and template-based justification generator."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from src.costwatch.config import Config
from src.costwatch.notes import StructuredNote
from src.costwatch.retrieval import NoteRetriever


@dataclass(frozen=True)
class VerdictResult:
    """Final grounded verdict for a candidate route-week."""
    route: str
    week_of: str
    cost_per_tonne_km: float
    vs_own_history: str
    vs_similar_routes: str
    flagged: str  # "Yes" or "No (justified)"
    matched_note_id: str  # Note ID if justified, else ""
    reason: str


def date_range_overlaps(
    start_a: datetime.date,
    end_a: datetime.date,
    start_b: datetime.date,
    end_b: datetime.date,
) -> bool:
    """Check if two inclusive date ranges overlap."""
    return start_a <= end_b and end_a >= start_b


def check_note_applicability(
    note: StructuredNote,
    route: str,
    week_start: datetime.date,
    vs_own_pct: Optional[float],
    config: Config,
) -> Tuple[bool, str]:
    """Evaluate whether a note deterministically applies to a candidate route-week.
    
    Returns:
        (is_applicable, rejection_detail)
    """
    week_end = week_start + timedelta(days=6)

    # 1. Route check
    if note.routes != "ALL" and route not in note.routes:
        return False, f"applies only to {note.routes}, not {route}"

    if not note.affects_dataset:
        return False, note.rejection_reason or "does not affect routes in this dataset"

    # 2. Time window check
    note_start = datetime.strptime(note.start_date, "%Y-%m-%d").date()
    if note.window_kind == "explicit_range" and note.end_date:
        note_end = datetime.strptime(note.end_date, "%Y-%m-%d").date()
    elif note.window_kind == "single_week":
        note_end = note_start + timedelta(days=6)
    else:  # open_ended
        max_days = config.open_ended_max_weeks * 7
        note_end = note_start + timedelta(days=max_days)

    if not date_range_overlaps(week_start, week_end, note_start, note_end):
        if week_start > note_end:
            return False, f"ended on {note_end.strftime('%Y-%m-%d')} before this week"
        else:
            return False, f"starts on {note_start.strftime('%Y-%m-%d')} after this week"

    # 3. Effect check (must be cost_increase)
    if note.effect != "cost_increase":
        return False, note.rejection_reason or f"has effect '{note.effect}' which does not justify a cost rise"

    # 4. Magnitude check
    if config.magnitude_check and note.stated_magnitude_pct and vs_own_pct is not None:
        upper_bound = max(note.stated_magnitude_pct)
        max_allowed = upper_bound + config.magnitude_tolerance_pp
        if vs_own_pct > max_allowed:
            return False, (
                f"stated a magnitude of {note.stated_magnitude_pct[0]:.0f}-{note.stated_magnitude_pct[1]:.0f}%, "
                f"but observed increase was {vs_own_pct:+.1f}%"
            )

    return True, ""


def evaluate_candidate(
    route: str,
    week_of: str,
    cost_per_tonne_km: float,
    vs_own_pct: Optional[float],
    vs_own_history: str,
    vs_similar_routes: str,
    retriever: NoteRetriever,
    config: Config,
) -> VerdictResult:
    """Evaluate candidate route-week against retrieved notes using deterministic gates."""
    week_start = datetime.strptime(week_of, "%Y-%m-%d").date()
    retrieved = retriever.retrieve(route=route, week_of=week_of, top_k=config.top_k)

    passing_note: Optional[StructuredNote] = None

    # Step 1: Check retrieved notes for justification
    for note, _ in retrieved:
        applicable, _ = check_note_applicability(
            note=note,
            route=route,
            week_start=week_start,
            vs_own_pct=vs_own_pct,
            config=config,
        )
        if applicable:
            passing_note = note
            break

    if passing_note:
        # Justified Verdict
        flagged = "No (justified)"
        matched_note_id = passing_note.note_id
        reason = (
            f"Matches note {passing_note.note_id} dated {passing_note.date}: "
            f"{passing_note.paraphrase}. The cost rise has a clear explanation."
        )
        return VerdictResult(
            route=route,
            week_of=week_of,
            cost_per_tonne_km=cost_per_tonne_km,
            vs_own_history=vs_own_history,
            vs_similar_routes=vs_similar_routes,
            flagged=flagged,
            matched_note_id=matched_note_id,
            reason=reason,
        )

    # Step 2: Unexplained Verdict - Identify closest note in temporal proximity
    flagged = "Yes"
    matched_note_id = ""

    # Search among route-relevant notes that affect dataset for closest in time
    route_notes = [
        n for n in retriever.notes
        if (n.routes == "ALL" or route in n.routes) and n.affects_dataset
    ]

    closest_note: Optional[StructuredNote] = None
    min_days: float = float("inf")

    for n in route_notes:
        n_date = datetime.strptime(n.date, "%Y-%m-%d").date()
        diff = abs((n_date - week_start).days)
        if diff < min_days:
            min_days = diff
            closest_note = n

    # If closest note is within temporal proximity threshold (<= 45 days)
    if closest_note is not None and min_days <= 45:
        n_start = datetime.strptime(closest_note.start_date, "%Y-%m-%d").date()
        if closest_note.end_date:
            n_end = datetime.strptime(closest_note.end_date, "%Y-%m-%d").date()
        else:
            n_end = n_start + timedelta(days=6)

        if week_start > n_end and closest_note.effect == "cost_increase":
            reason = (
                f"The closest note ({closest_note.note_id}, {closest_note.date}) "
                f"ended on {closest_note.end_date} before this week -- it does not describe a reason for a cost rise in this period. "
                f"No genuine justification found; flagged for review."
            )
        else:
            reason = (
                f"The closest note ({closest_note.note_id}, {closest_note.date}) "
                f"{closest_note.paraphrase} -- it does not describe a reason for a cost rise on this route. "
                f"No genuine justification found; flagged for review."
            )
    else:
        reason = (
            "No matching note found for this route or date range. "
            "Cost rise looks unexplained and worth a human review."
        )

    return VerdictResult(
        route=route,
        week_of=week_of,
        cost_per_tonne_km=cost_per_tonne_km,
        vs_own_history=vs_own_history,
        vs_similar_routes=vs_similar_routes,
        flagged=flagged,
        matched_note_id=matched_note_id,
        reason=reason,
    )
