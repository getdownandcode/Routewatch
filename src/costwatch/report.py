"""CSV report generation conforming strictly to sample_output_format_v2.csv."""

import csv
from pathlib import Path
from typing import List
from src.costwatch.verdict import VerdictResult

CONTRACT_COLUMNS = [
    "route",
    "week_of",
    "cost_per_tonne_km",
    "vs_own_history",
    "vs_similar_routes",
    "flagged",
    "matched_note_id",
    "reason",
]


def write_output_csv(
    verdicts: List[VerdictResult],
    output_path: str = "outputs/output.csv"
) -> None:
    """Write verdicts to CSV adhering strictly to the contract format.
    
    Sorting: deterministically sorted by week_of, then route.
    """
    sorted_verdicts = sorted(verdicts, key=lambda v: (v.week_of, v.route))

    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    with open(out_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
        # Write exact contract header
        writer.writerow(CONTRACT_COLUMNS)

        for v in sorted_verdicts:
            writer.writerow([
                v.route,
                v.week_of,
                f"{v.cost_per_tonne_km:.2f}",
                v.vs_own_history,
                v.vs_similar_routes,
                v.flagged,
                v.matched_note_id,
                v.reason,
            ])
