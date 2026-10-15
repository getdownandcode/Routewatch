# SPEC.md — the contract (derived from the FreightTiger brief + the actual data)

## 1. Goal
Detect routes whose freight cost per tonne-km is rising abnormally, check a small notes file for a **real, applicable** reason, and output flagged rows with honest verdicts. Trust beats cleverness: a confident wrong reason scores worse than "couldn't find one".

## 2. Input facts (already verified, use as tests)
- `data/shipment_records.csv`: 2,940 rows, no nulls, no duplicate ids. Columns: shipment_id, origin, destination, route_type, material, quantity_tonnes, distance_km, freight_cost_inr, shipment_date, transporter.
- Date range 2024-01-01 (Monday) to 2025-12-28 (Sunday) = **104 full weeks**. Every route has data in every week.
- **7 routes**; the route key is `"{origin}-{destination}"` (matches `applies_to` in the notes). `route_type` is constant per route:
  - Short: Mumbai-Pune, Delhi-Jaipur (each has exactly **1** peer, so peer comparison is noisy)
  - Medium: Ahmedabad-Mumbai, Chennai-Bangalore, Kolkata-Bhubaneswar
  - Long: Delhi-Chennai, Mumbai-Delhi
- `data/context_notes.csv`: 10 notes (N001–N010), columns note_id, date, applies_to, note.
- `data/sample_output_format_v2.csv` is the output contract (the brief calls it `sample_output_format.csv`; use the v2 file that was provided).

## 3. Metrics (use exactly these definitions)
- **week_of** = the Monday of the Mon–Sun week containing `shipment_date`. Group into weeks first.
- **cost_per_tonne_km (per route-week)** = `sum(freight_cost_inr) / sum(quantity_tonnes * distance_km)` over that route's shipments that week. Output rounded to 2 dp; compute everything on unrounded values.
- **vs own history** = route's trailing rolling mean of its weekly cost_per_tonne_km over the **previous up-to-8 weeks, strictly before the current week** (no look-ahead; if fewer than 8 prior weeks exist, use all available, no padding). Percent = `(current / baseline - 1) * 100`. Week 1 of a route has no history, so it has no value and cannot be flagged. Document this in README.
- **vs similar routes** = in that same week, the mean of weekly cost_per_tonne_km across **all other routes with the same route_type** (route itself excluded). Same percent formula.
- Formatting of the percent strings (exact, with explicit sign, 1 dp):
  - `vs_own_history`: `+35.5% vs this route's past average` (use `-` for negatives)
  - `vs_similar_routes`: `+21.0% vs similar-length routes this week`

### Golden check (must pass in Phase 2)
These values from the sample file reproduce with the definitions above; your code must produce them:

| route | week_of | cost_per_tonne_km | vs_own | vs_similar |
|---|---|---|---|---|
| Delhi-Jaipur | 2024-11-11 | 4.17 | +35.5% | +21.0% |
| Ahmedabad-Mumbai | 2025-01-20 | 3.29 | +29.5% | +22.5% |
| Mumbai-Pune | 2025-09-15 | 3.98 | +9.2% | +23.6% |

## 4. Flag rule
The brief does not give a threshold, so make it configurable in `config.yaml` and document it.
- Candidate if `vs_own >= +8%` **and** `vs_similar >= +10%` and at least `min_history_weeks: 4` prior weeks exist.
- With these defaults the data yields about **9 candidate route-weeks** (Delhi-Jaipur 2024-11-11 and 11-18; Ahmedabad-Mumbai 2025-01-20; Chennai-Bangalore 2025-02-24, 03-03, 03-10, 03-17; Mumbai-Pune 2025-09-15 and 2025-11-17). If your count is far from this, investigate before moving on. Weekly own-history noise is about ±4% (std), so 8% is roughly 2 sigma.
- Phase 2 must also print a small sensitivity table (thresholds 8/10, 10/10, 15/10) so the choice can be defended in the walkthrough.

## 5. Output CSV (`outputs/output.csv`)
Header and order exactly:
`route,week_of,cost_per_tonne_km,vs_own_history,vs_similar_routes,flagged,matched_note_id,reason`
- One row per **candidate** route-week (see sample: it contains both `Yes` and `No (justified)` rows). Sort by `week_of`, then `route`.
- `flagged`: `Yes` (unexplained, needs human review) or `No (justified)`.
- `matched_note_id`: the note id if justified, **blank** if unexplained. Never fill it for an unexplained row.
- `reason`: plain English from a template (see section 7).
- Also write `outputs/weekly_metrics.csv` with all 728 route-weeks and the raw numbers (supporting analytics, not part of the contract).

## 6. Notes: what each note can and cannot justify
Convert each note once into structured JSON (`data/notes_structured.json`, committed, hand-verified). Fields: `note_id, effect` (`cost_increase | no_cost_effect | cost_decrease | recovery_to_normal`), `routes` (list or `"ALL"`), `affects_dataset` (bool), `start_date`, `end_date` (nullable), `window_kind` (`explicit_range | single_week | open_ended`), `stated_magnitude_pct` (nullable `[lo, hi]`).

Expected result of structuring (verify against this table; fix the JSON if the LLM disagrees):

| id | route(s) | effect | window |
|---|---|---|---|
| N001 | Chennai-Bangalore | cost_increase | 2025-02-24 to 2025-03-08 (explicit) |
| N002 | Ahmedabad-Mumbai | cost_increase | single week starting 2025-01-20 |
| N003 | ALL | cost_increase (5–7%) | open-ended from 2025-05-05 (cap at `open_ended_max_weeks: 8` in config) |
| N004 | ALL | no_cost_effect, `affects_dataset=false` | n/a |
| N005 | Mumbai-Delhi | no_cost_effect | ~1 week from 2024-07-29 |
| N006 | ALL | no_cost_effect | quarter from 2025-09-22 |
| N007 | Delhi-Jaipur | cost_decrease (roads improved) | from 2024-05-20 |
| N008 | Kolkata-Bhubaneswar | no_cost_effect | quarter from 2025-06-09 |
| N009 | Chennai-Bangalore | recovery_to_normal | from 2025-03-17 |
| N010 | ALL | no_cost_effect | from 2025-10-27 |

**Only N001, N002 and N003 may ever justify a cost rise.** All others are traps (wrong effect, wrong route, no effect, or dated after the week). A test must assert this.

### Applicability gate (deterministic, in `verdict.py`)
A note justifies a flagged `(route, week_of)` only if **all** pass:
1. Route: `route in note.routes` or `routes == "ALL"`, and `affects_dataset` is true.
2. Time: the week `[week_of, week_of+6]` overlaps the note's effective window (explicit range, the single week, or open-ended start plus `open_ended_max_weeks`).
3. Effect: `effect == "cost_increase"`.
4. (Optional, config `magnitude_check: true`) If the note states a magnitude and the observed `vs_own` exceeds its upper bound by more than `magnitude_tolerance_pp: 10`, treat as **not fully explained** and leave it unexplained, saying so in the reason. Record how many rows this affects in `docs/DECISIONS.md`.

Pick the passing note with the highest retrieval similarity (tie: lowest `note_id`). If none passes, the verdict is `Yes` with blank `matched_note_id`.

Expected outcome on the default candidates (sanity check, not hard-coded): Ahmedabad-Mumbai 2025-01-20 is justified by N002; Chennai-Bangalore 2025-02-24 and 03-03 are justified by N001; 03-10 starts after N001 ended, so it is unexplained; 03-17 is unexplained (N009 says conditions were normal); the Delhi-Jaipur and Mumbai-Pune rows are unexplained.

## 7. Reason templates (no free-form LLM text)
- Justified: `Matches note {id} dated {date}: {paraphrase from notes_structured.json}. The cost rise has a clear explanation.`
- Unexplained, nothing relevant: `No matching note found for this route or date range. Cost rise looks unexplained and worth a human review.`
- Unexplained, closest note rejected: `The closest note ({id}, {date}) {why it does not apply, e.g. mentions stable demand with no major disruptions} -- it does not describe a reason for a cost rise on this route. No genuine justification found; flagged for review.` Only name a rejected note when it is route-relevant or all-routes and you state the true rejection reason (wrong window, no effect, recovery).
- Reasons must contain no commas that break the CSV: always write with Python's `csv` module (proper quoting).

## 8. Retrieval (the "AI" part)
- Local embeddings with `sentence-transformers` (`all-MiniLM-L6-v2`), embeddings of the 10 notes cached to `data/note_embeddings.npy`. Cosine similarity with numpy is fine (brief allows "vector database and retrieval"; with 10 notes a numpy store is the honest trade-off, and say Chroma/FAISS would replace it at scale).
- Query per candidate: a short text such as `freight cost increase on {route} in week of {date}`. Pre-filter by route metadata (route or ALL), rank by similarity, then apply the gate in section 6 to each ranked note. Retrieval proposes; the gate decides.

## 9. Evaluation and reproducibility (graded)
- `eval/labeled_cases.csv`: at least 25 hand-labeled `(route, week_of, expected_verdict, expected_note_id)` cases including every trap (wrong route, N004/N005/N006/N008/N010 no-effect notes, N009 recovery, week just after N001, N003 weeks before and after its start). `eval/run_eval.py` scores verdict accuracy, note-id accuracy, and a **fabrication audit**: every non-blank `matched_note_id` in the output must pass the gate. Target 100% on the audit.
- Reproducibility: `scripts/repro.sh` (or `python run.py --repro`) runs the pipeline 3 times, compares SHA-256 of `outputs/output.csv`, writes `outputs/repro_check.md`.
- Cost log: `outputs/token_log.md` with total input tokens, total output tokens, number of LLM calls, model, temperature, and rough cost at the model's published rate, for one **cold** run (cache empty) and one **warm** run (0 calls). Free tier means 0 INR actual; also state the paid-rate equivalent.

## 10. Deliverables
Code, `outputs/output.csv`, README (how it works, how it was built, how it was checked, assumptions, trade-offs), repro check, token log, eval report, and a 10-minute walkthrough outline in README.
