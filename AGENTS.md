# AGENTS.md — always-on rules for this repo

You are building the **FreightTiger "Smart Shipping-Cost Assistant"** case study. Read `SPEC.md` (the contract) and `PLAN.md` (the phases) before writing code.

## Hard constraints
- **Total time budget: about 60 minutes.** Choose the simplest option that satisfies SPEC.md. No gold-plating.
- Work **one phase at a time**, in the order in `PLAN.md`. Do not start phase N+1 until phase N's acceptance checks pass.
- **After every phase:** run the tests, then
  `git add -A && git commit -m "<message from PLAN.md>" && git push`.
  If push fails, say so once in your status line, keep committing locally, and continue.
- After every phase, print a 3-line status: what was done, what was tested, what is next.
- If something is ambiguous, pick the simplest reasonable reading, record it in `docs/DECISIONS.md` (one bullet: decision + why), and **keep going**. Do not stop to ask.

## Non-negotiable engineering rules
1. **Determinism.** Same input must give a byte-identical output CSV on every run. Sort everything explicitly, break ties by `note_id` / route name, fix seeds, no timestamps in the output, no unordered set/dict iteration affecting results.
2. **No hallucination.** A "justified" verdict is allowed only if a deterministic gate (route + time window + cost-increase effect) passes for a real note in `context_notes.csv`. Reason text is generated from a **template filled with verified fields**, never free-form LLM text. No supporting note means unexplained. Never guess.
3. **LLM use is minimal and cached.** The LLM may be used only to (a) convert each note into structured JSON once (cached on disk and committed), and (b) answer questions in the optional Q&A feature. Temperature 0. Every call is logged (input tokens, output tokens) to `outputs/llm_calls.jsonl`.
4. **Output contract.** `outputs/output.csv` must have exactly the header and column order of `data/sample_output_format_v2.csv`. A test must assert this.
5. **Secrets.** API keys live in `.env` (gitignored). Never commit them. Provide `.env.example`.
6. **Clean code.** Small modules under `src/costwatch/`, type hints, one-line docstrings, all thresholds in `config.yaml` (no magic numbers in code), pytest tests under `tests/`.
7. Prefer free/open-source: local `sentence-transformers` embeddings, Gemini free tier (or local Ollama) for the few LLM calls.

## Repo layout (create this)
```
.
├── AGENTS.md  SPEC.md  PLAN.md  UI_SPEC.md
├── README.md                 # written in the last phase
├── config.yaml  .env.example  .gitignore  requirements.txt
├── data/                     # shipment_records.csv, context_notes.csv, sample_output_format_v2.csv
├── src/costwatch/            # config.py metrics.py flags.py notes.py retrieval.py verdict.py report.py llm.py qa.py
├── run.py                    # CLI: python run.py  -> outputs/output.csv
├── tests/
├── eval/                     # labeled_cases.csv, run_eval.py
├── outputs/                  # output.csv weekly_metrics.csv llm_calls.jsonl token_log.md repro_check.md eval_report.md
├── docs/DECISIONS.md
└── app/                      # optional UI (see UI_SPEC.md), only in the last phase
```
