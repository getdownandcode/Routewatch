# Paste this into Antigravity goal mode

Put `AGENTS.md`, `SPEC.md`, `PLAN.md`, `UI_SPEC.md` in the repo root and the three CSVs (`shipment_records.csv`, `context_notes.csv`, `sample_output_format_v2.csv`) in `data/`. Create an empty GitHub repo first and set it as `origin` (or give the agent the URL).

---

**Goal:** Build the FreightTiger shipping-cost assistant exactly as specified in `SPEC.md`, following `AGENTS.md` rules and executing `PLAN.md` phases 0 to 6 strictly in order, one phase at a time.

For each phase: implement it, run its tests and acceptance checks, fix any failure, then `git add -A`, commit with the exact message given in `PLAN.md`, `git push`, and print a 3-line status (done, tested, next). Do not begin the next phase until the current one passes. Do not ask me questions; if something is ambiguous, choose the simplest reading that satisfies `SPEC.md` and log it in `docs/DECISIONS.md`.

Hard requirements to never violate: output CSV header and column order identical to `data/sample_output_format_v2.csv`; byte-identical output across runs; a justified verdict only when the deterministic gate passes for a real note; reason text from templates; LLM at temperature 0 with every call logged and cached; no secrets in git.

After Phase 6 is pushed, if more than 12 minutes of my hour remain, do Phase 7 using `UI_SPEC.md`; otherwise stop and print the final checklist. I have about 60 minutes in total, so prefer simple, working, tested code over extra features.
