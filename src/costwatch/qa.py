"""Grounded plain-English Q&A engine for shipping-cost anomaly results."""

from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pandas as pd
from src.costwatch.llm import LLMClient
from src.costwatch.notes import StructuredNote, load_structured_notes


class GroundedQA:
    """Answers user inquiries strictly grounded in pipeline output and verified notes."""

    def __init__(
        self,
        output_csv_path: str = "outputs/output.csv",
        notes_json_path: str = "data/notes_structured.json",
        llm_client: Optional[LLMClient] = None,
    ):
        self.output_csv_path = Path(output_csv_path)
        self.notes_json_path = Path(notes_json_path)

        if not self.output_csv_path.exists():
            raise FileNotFoundError(f"Pipeline output file not found: {output_csv_path}")

        self.df_output = pd.read_csv(self.output_csv_path)
        self.notes = load_structured_notes(str(self.notes_json_path))
        self.notes_by_id = {n.note_id: n for n in self.notes}

        if llm_client is None:
            self.llm = LLMClient()
        else:
            self.llm = llm_client

    def answer_question(self, question: str) -> Tuple[str, List[str], List[str]]:
        """Answer question using only relevant output rows and cited notes.
        
        Returns:
            (answer_text, cited_rows, cited_note_ids)
        """
        q_lower = question.lower()

        # Identify relevant route-weeks from output.csv
        relevant_rows = []
        for _, row in self.df_output.iterrows():
            route = str(row["route"])
            week = str(row["week_of"])
            nid = str(row["matched_note_id"]) if not pd.isna(row["matched_note_id"]) else ""

            # Check matching keywords in question
            tokens = route.lower().split("-") + [week, nid.lower()]
            if any(t in q_lower for t in tokens if len(t) > 2) or "all" in q_lower or "unexplained" in q_lower:
                relevant_rows.append(row)

        if not relevant_rows:
            relevant_rows = [r for _, r in self.df_output.iterrows()]

        # Collect cited note IDs
        cited_note_ids = set()
        context_lines = ["### Discovered Anomaly Results:"]
        row_identifiers = []

        for r in relevant_rows:
            row_id_str = f"{r['route']} ({r['week_of']})"
            row_identifiers.append(row_id_str)
            nid = str(r["matched_note_id"]).strip() if not pd.isna(r["matched_note_id"]) else ""
            if nid:
                cited_note_ids.add(nid)

            context_lines.append(
                f"- Route: {r['route']} | Week: {r['week_of']} | Rate: ₹{r['cost_per_tonne_km']:.2f}/tonne-km | "
                f"vs Own: {r['vs_own_history']} | vs Peers: {r['vs_similar_routes']} | "
                f"Verdict: {r['flagged']} | Matched Note: {nid or 'None'} | Reason: {r['reason']}"
            )

        context_lines.append("\n### Relevant Context Notes:")
        for nid in sorted(cited_note_ids):
            note = self.notes_by_id.get(nid)
            if note:
                context_lines.append(
                    f"- [{note.note_id}] {note.applies_to} ({note.date}): {note.original_text}"
                )

        context_str = "\n".join(context_lines)

        prompt = f"""You are Routewatch, a shipping-cost assistant.
Answer the user's question using ONLY the provided verified anomaly results and context notes.
If the information is not contained in the provided results, reply exactly: "I couldn't find that in the results."
Never invent reasons or cite notes not provided below.

{context_str}

User Question: {question}

Return a JSON object with:
- "answer": plain-English answer grounded in the data above
- "cited_notes": list of note IDs cited in your answer
"""

        try:
            resp = self.llm.generate_json(prompt)
            answer = resp.get("answer", "I couldn't find that in the results.")
            used_notes = resp.get("cited_notes", [])

            # Guardrail validation: Any note cited in the answer must strictly be in the retrieved set
            for nid in used_notes:
                if nid not in cited_note_ids:
                    return (
                        "I couldn't find that in the results.",
                        row_identifiers[:5],
                        list(cited_note_ids),
                    )

            return answer, row_identifiers[:5], sorted(list(cited_note_ids))
        except Exception:
            # Deterministic fallback when LLM is unavailable
            matched_row = next((r for r in relevant_rows if any(t in q_lower for t in r["route"].lower().split("-"))), relevant_rows[0])
            fallback_ans = f"For {matched_row['route']} ({matched_row['week_of']}): {matched_row['reason']}"
            return fallback_ans, [f"{matched_row['route']} ({matched_row['week_of']})"], list(cited_note_ids)
