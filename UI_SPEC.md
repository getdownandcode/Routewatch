# UI_SPEC.md — optional review dashboard (Phase 7 only)

**Is a UI required?** No. The brief grades the CSV, the guardrails, reproducibility, cost, code quality and your explanation. A UI helps only as a demo aid for the 10-minute walkthrough and for the stretch goal (plain-English Q&A). Build it last, time-boxed to about 12 minutes, using **Streamlit** (fastest in Python). A broken UI costs more than no UI, so it must never block the CLI.

## Audience and job
An operations analyst reviewing which route-weeks need human attention. Primary job: in under 10 seconds, see which routes are flagged, why, and whether the explanation is backed by a real note.

## Screens (one page, two tabs)

### Tab 1: Review
- **Summary strip** at the top: count of `Yes` (needs review) first and largest, then count of `No (justified)`, then routes covered. Plain sentence above it, e.g. "9 route-weeks looked unusually expensive. 5 need a human look."
- **Flag table** (from `outputs/output.csv`): columns route, week, cost per tonne-km, vs own history, vs similar routes, status. Sort: unexplained first. Status shown as a text label with an icon and colour (never colour alone). Filters: route, status.
- **Detail panel** on row selection:
  - Line chart of that route's weekly cost per tonne-km across 104 weeks, with the flagged week marked and the trailing 8-week baseline drawn as a faint band. Peer-average line optional and muted.
  - **Evidence card**: the cited note's id, date, applies-to and full original text, with the matched dates in the note visibly tied to the flagged week. For unexplained rows show "No supporting note found" and, if any, the closest rejected note with the specific reason it was rejected.
  - The plain-English reason, exactly as in the CSV.

### Tab 2: Ask
- One text box, "Ask about a flagged route or week". Example chips: "Why did Chennai-Bangalore get pricier in March 2025?", "Which flags have no explanation?".
- Answers come from `qa.py`: retrieve relevant rows of `output.csv` and the cited notes, pass only those to the LLM (temperature 0) with an instruction to answer **only** from the provided rows and notes and to say "I couldn't find that in the results" otherwise. Show a "Based on" line listing the rows and note ids used. Validate: any note id in the answer must exist in the retrieved set, otherwise replace the answer with the fallback message.

## Visual direction (make deliberate choices, avoid generic dashboard defaults)
The subject is Indian road freight: trucks, highways, waybills, route signage. Take the look from highway signage and printed consignment notes, not from a generic SaaS template.
- **Palette (6 named values):** Highway-sign green `#0B5D3B` (primary, used sparingly), Paper `#FAF8F3` (background), Ink `#1B1F23` (text), Hazard amber `#F2A900` (needs-review emphasis only), Verified teal `#0F7A8A` (justified status), Quiet grey `#6B7280` (secondary text, baselines).
- **Type:** one sturdy grotesque for UI and headings (for example *IBM Plex Sans* or *Public Sans*) plus *IBM Plex Mono* only for note ids and numbers in tables so digits align. Sentence case everywhere. Do not use all-caps eyebrow labels.
- **Layout:** left-aligned, a wide table with a detail panel beneath it on narrow screens and beside it (60/40) on wide ones. Rows are generous (44px) with a thin bottom rule. The one memorable element is the **evidence card**, styled like a stamped waybill slip (hairline border, mono note id in a small tag); everything else stays quiet.
- Single border radius (4px). No gradients, no per-card drop shadows, no decorative animation. Motion only in response to a click (detail panel opens, chart marker moves).

## Copy rules
Write for the analyst, not the engineer. "Needs review" and "Explained by a note", not "flagged=Yes". Empty state: "No unusual cost rises found for these filters." Error state: say what failed and what to do, e.g. "Couldn't read outputs/output.csv. Run `python run.py` first." Buttons are verbs: "Ask", "Clear filters".

## Quality floor
Responsive to mobile width, visible keyboard focus, text contrast at least 4.5:1 (check amber on paper: use ink text on amber backgrounds, never amber text), status never conveyed by colour alone, charts have a text summary ("Chennai-Bangalore: 4.9 in the flagged week vs 3.1 average over the previous 8 weeks"). Cache data loading with `st.cache_data` so the app opens fast.

## Acceptance
`streamlit run app/app.py` opens, the table matches `outputs/output.csv` row for row, selecting a justified row shows its note text, selecting an unexplained row shows "No supporting note found", the Ask tab refuses to answer outside the results. Take a screenshot to check layout before committing.
