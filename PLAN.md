# PLAN.md — phases (do strictly one by one)

Rules for every phase: implement, run tests, verify the acceptance checks, commit and push with the given message, print the 3-line status, then move on. Time boxes add up to about 60 minutes; if a phase overruns, simplify rather than skip the commit.

---
## Phase 0: Setup (3 min)
- Create the layout from `AGENTS.md`. Copy the three CSVs into `data/`. `git init` (if needed), add the remote the user provides, `.gitignore` (`.env`, `__pycache__`, `.venv`, `*.pyc`, `.pytest_cache`).
- `requirements.txt`: pandas, numpy, pyyaml, pytest, sentence-transformers, python-dotenv, google-genai (or the user's chosen LLM SDK), streamlit (only needed for Phase 7).
- `config.yaml` with every threshold from SPEC.md (rolling_weeks 8, min_history_weeks 4, own_threshold_pct 8, peer_threshold_pct 10, open_ended_max_weeks 8, magnitude_check true, magnitude_tolerance_pp 10, top_k 5, model name, temperature 0).
- **Accept:** `pytest` runs (even with 0 tests), `python -c "import pandas"` works.
- **Commit:** `chore: project scaffold, config, data`

## Phase 1: Weekly metrics (8 min)
- `metrics.py`: load shipments, build route key, compute `week_of` (Monday), aggregate per route-week with `sum(cost)/sum(qty*dist)`, write `outputs/weekly_metrics.csv` (728 rows).
- Tests: week assignment (a Sunday maps to the previous Monday; a Monday maps to itself); 7 routes x 104 weeks = 728 rows; one hand-computed route-week.
- **Accept:** tests pass; 728 rows; no NaN.
- **Commit:** `feat: weekly cost per tonne-km by route`

## Phase 2: Baselines and flags (8 min)
- `flags.py`: vs-own-history (trailing 8 strictly prior, fewer if unavailable), vs-similar (same route_type, same week, exclude self), percent strings, candidate rule from config.
- Tests: the **golden check** in SPEC.md section 3 (all three rows must match exactly); no look-ahead (changing a future week's data must not change the baseline); self excluded from peers; week 1 has no baseline.
- Print the sensitivity table (8/10, 10/10, 15/10) into `outputs/flag_sensitivity.md` and report the candidate count (expect about 9).
- **Accept:** golden check passes; candidate list resembles SPEC.md section 4.
- **Commit:** `feat: own-history and peer baselines, flag rule, golden tests`

## Phase 3: Notes structuring and retrieval (10 min)
- `llm.py`: thin client, temperature 0, JSON-only output, **disk cache** keyed by hash of (model, prompt), appends every call to `outputs/llm_calls.jsonl` with input and output token counts.
- `notes.py`: for each note, call the LLM once to produce the structured JSON in SPEC.md section 6; write `data/notes_structured.json`. Then **compare with the expected table in SPEC.md** and correct the JSON by hand where it differs (record corrections in `docs/DECISIONS.md`). Commit the JSON so later runs make 0 LLM calls.
- `retrieval.py`: embed the 10 notes with sentence-transformers, cache to `data/note_embeddings.npy`, cosine search with metadata pre-filter, deterministic tie-breaking.
- If the LLM is unavailable or rate-limited, hand-write the JSON from the SPEC table and note that in DECISIONS.md (it is only 10 notes).
- Tests: retrieval for `Chennai-Bangalore` flood query returns N001 first among its candidates; JSON schema valid for all 10.
- **Accept:** `notes_structured.json` matches the SPEC table; retrieval test passes.
- **Commit:** `feat: structured notes (cached LLM) and local retrieval`

## Phase 4: Verdict gate and output CSV (8 min)
- `verdict.py`: the applicability gate (route, time overlap, effect, optional magnitude check) and the reason templates. `report.py`: write `outputs/output.csv` with the `csv` module in the exact header order, sorted by `week_of`, `route`. `run.py`: end-to-end CLI.
- Tests: output header equals the sample header exactly; only N001/N002/N003 can ever appear in `matched_note_id`; a justified row always has a non-blank note id and an unexplained row always a blank one; each of the 7 trap notes (N004–N010) is rejected for the right reason.
- **Accept:** `python run.py` produces the CSV; the three rows from the sample file appear with the expected verdicts (Ahmedabad-Mumbai 2025-01-20 is justified by N002; Delhi-Jaipur 2024-11-11 and Mumbai-Pune 2025-09-15 are unexplained).
- **Commit:** `feat: grounded verdict gate and contract-compliant output CSV`

## Phase 5: Evaluation harness, reproducibility, cost log (8 min)
- `eval/labeled_cases.csv` (25+ cases) and `eval/run_eval.py` with the fabrication audit, writing `outputs/eval_report.md`.
- `scripts/repro.sh`: 3 clean runs, SHA-256 compare, write `outputs/repro_check.md`. Run once with a **cold** cache to produce `outputs/token_log.md` (calls, input tokens, output tokens, cost), then a warm run (0 calls).
- **Accept:** eval is all-pass (or failures are explained in the report); 3 hashes identical; token log exists.
- **Commit:** `test: eval harness, 3-run reproducibility check, token and cost log`

## Phase 6: README and walkthrough notes (5 min)
- `README.md`: problem in 3 lines; architecture diagram (ASCII is fine); how to run (3 commands); metric definitions and the fewer-than-8-weeks rule; flag thresholds and why (sensitivity table); how notes are structured, retrieved and gated (retrieval proposes, gate decides, templates write the text); where the LLM is used and why so little; reproducibility result; cost log; eval results; limitations (small peer groups for Short routes, open-ended N003 cap, 10-note corpus); what you would do next.
- Add a **10-minute walkthrough outline** at the bottom (1 min problem, 2 min data and metrics, 3 min grounding and guardrails, 2 min eval and repro, 1 min cost, 1 min trade-offs).
- **Accept:** a stranger can run it from the README.
- **Commit:** `docs: README, assumptions, walkthrough outline`

---
## Phase 7: OPTIONAL UI (only if at least 12 minutes remain; Phases 0–6 must already be pushed)
Follow `UI_SPEC.md`. Do not touch the pipeline outputs; the UI only reads `outputs/*.csv` and `data/*.json`.
- **Commit:** `feat(ui): review dashboard and grounded Q&A`

## Final step
Run `pytest`, `python eval/run_eval.py`, `scripts/repro.sh`, confirm `git status` is clean and `git push` succeeded. Print the repo URL and a checklist of the deliverables from SPEC.md section 10.
