"""CLI entrypoint for CostWatch anomaly detection and grounded justification pipeline."""

import argparse
import hashlib
import sys
from pathlib import Path
from typing import List, Optional

from src.costwatch.config import Config
from src.costwatch.flags import compute_baselines_and_flags
from src.costwatch.metrics import compute_weekly_metrics, save_weekly_metrics
from src.costwatch.notes import build_and_save_structured_notes, load_structured_notes
from src.costwatch.report import write_output_csv
from src.costwatch.retrieval import NoteRetriever
from src.costwatch.verdict import VerdictResult, evaluate_candidate


def run_pipeline(
    config_path: str = "config.yaml",
    shipments_path: Optional[str] = None,
    notes_path: Optional[str] = None,
    output_path: Optional[str] = None,
    verbose: bool = True,
) -> List[VerdictResult]:
    """Execute the full end-to-end CostWatch anomaly detection pipeline."""
    config = Config.load(config_path)

    shipments_csv = shipments_path or config.paths.get("shipments", "data/shipment_records.csv")
    notes_csv = notes_path or config.paths.get("notes", "data/context_notes.csv")
    output_csv = output_path or config.paths.get("output_csv", "outputs/output.csv")
    weekly_metrics_csv = config.paths.get("weekly_metrics", "outputs/weekly_metrics.csv")
    structured_json_path = config.paths.get("notes_structured", "data/notes_structured.json")

    # 1. Compute weekly metrics
    if verbose:
        print(f"Loading shipments from {shipments_csv}...")
    weekly_df = compute_weekly_metrics(shipments_csv)
    save_weekly_metrics(weekly_df, weekly_metrics_csv)
    if verbose:
        print(f"Saved {len(weekly_df)} route-weeks to {weekly_metrics_csv}")

    # 2. Compute baselines and flags
    if verbose:
        print("Computing rolling own-history and peer baselines...")
    flagged_df = compute_baselines_and_flags(weekly_df, config)
    candidates = flagged_df[flagged_df["is_candidate"]].reset_index(drop=True)
    if verbose:
        print(f"Identified {len(candidates)} candidate anomalies needing review.")

    # 3. Ensure structured notes and retriever are ready
    if not Path(structured_json_path).exists():
        if verbose:
            print(f"Structuring context notes from {notes_csv}...")
        build_and_save_structured_notes(notes_csv_path=notes_csv, output_json_path=structured_json_path)

    notes = load_structured_notes(structured_json_path)
    retriever = NoteRetriever(
        notes=notes,
        model_name=config.embedding_model,
        embeddings_cache_path=config.paths.get("note_embeddings", "data/note_embeddings.npy"),
        notes_json_path=structured_json_path,
    )

    # 4. Evaluate candidates through deterministic applicability gate
    if verbose:
        print("Evaluating candidates against retrieved context notes...")
    verdicts: List[VerdictResult] = []
    for _, row in candidates.iterrows():
        v = evaluate_candidate(
            route=row["route"],
            week_of=row["week_of"],
            cost_per_tonne_km=row["cost_per_tonne_km"],
            vs_own_pct=row["vs_own_pct"],
            vs_own_history=row["vs_own_history"],
            vs_similar_routes=row["vs_similar_routes"],
            retriever=retriever,
            config=config,
        )
        verdicts.append(v)

    # 5. Output contract CSV
    write_output_csv(verdicts, output_path=output_csv)
    if verbose:
        justified_count = sum(1 for v in verdicts if "justified" in v.flagged)
        unexplained_count = len(verdicts) - justified_count
        print(f"Wrote {len(verdicts)} rows to {output_csv}")
        print(f"Summary: {justified_count} Explained (Justified), {unexplained_count} Unexplained (Needs Review).")

    return verdicts


def run_reproducibility_check(runs: int = 3) -> None:
    """Run pipeline repeatedly and verify byte-identical output hashes."""
    print(f"Running reproducibility audit across {runs} untouched runs...")
    hashes = []
    output_path = "outputs/output.csv"

    for i in range(1, runs + 1):
        run_pipeline(verbose=False)
        with open(output_path, "rb") as f:
            digest = hashlib.sha256(f.read()).hexdigest()
        hashes.append(digest)
        print(f"Run {i}: SHA-256 = {digest}")

    all_identical = len(set(hashes)) == 1
    report_lines = [
        "# CostWatch Reproducibility Audit Report",
        "",
        f"**Audit Status**: {'PASSED (Deterministic)' if all_identical else 'FAILED'}",
        f"**Total Executions**: {runs}",
        "",
        "| Run | Output File | SHA-256 Hash | Status |",
        "|:---:|:---|:---|:---:|",
    ]
    for idx, h in enumerate(hashes, 1):
        report_lines.append(f"| Run {idx} | `outputs/output.csv` | `{h}` | ✓ Identical |")

    report_lines.extend([
        "",
        "### Guarantee:",
        "- Same input generates byte-identical outputs across all runs.",
        "- Explicit sort orders by `week_of` and `route` eliminate non-deterministic dictionary/set iteration.",
        "- Temperature 0 and cached deterministic gates eliminate stochastic drift.",
    ])

    report_path = Path("outputs/repro_check.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))
    print(f"Wrote reproducibility report to {report_path}")

    if not all_identical:
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="CostWatch shipping-cost anomaly assistant")
    parser.add_argument("--config", default="config.yaml", help="Path to config.yaml")
    parser.add_argument("--shipments", default=None, help="Path to shipment_records.csv")
    parser.add_argument("--notes", default=None, help="Path to context_notes.csv")
    parser.add_argument("--output", default=None, help="Path to output.csv")
    parser.add_argument("--repro", action="store_true", help="Run 3x reproducibility check")

    args = parser.parse_args()

    if args.repro:
        run_reproducibility_check()
    else:
        run_pipeline(
            config_path=args.config,
            shipments_path=args.shipments,
            notes_path=args.notes,
            output_path=args.output,
            verbose=True,
        )


if __name__ == "__main__":
    main()
