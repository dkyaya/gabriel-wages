# Worker 3 TX50 Offline Preparation Prompt

Work only in your persistent Worker 3 worktree, created from the coordinator planning commit that contains this prompt and the locked input. Do not work in the main coordinator repository, inspect or change remotes, or push.

This task is **offline preparation and dry-run review only**. It does not authorize a smoke preflight, live scout, API/model call, hosted search, URL opening, source verification, download, ingestion, codification, national accounting update, or canonical-data change.

## Required inputs

Read `AGENTS.md`, `docs/analysis/three_worker_50row_batch_plan_2026-07-21.md`, `docs/analysis/worker_3_tx50_scout_input_2026-07-21.csv`, `docs/analysis/worker_3_tx50_selection_methodology_2026-07-21.md`, and the parallel-worker template. Apply only its Gate 0 and Gate 1 offline-preparation controls; smoke/live gates are forbidden in this task.

Record the starting local commit. Confirm exactly 50 TX rows, one `worker_3` value, one `COORD-SERIAL150-2026-07-21` future queue ID, 50 unique municipality and Census IDs, only active `municipal` / `place` governments, and only `not_scouted` pre-run coverage. Confirm Dallas, Fort Worth, El Paso, Arlington, and Corpus Christi occupy ranks 1–5; confirm already-covered San Antonio, Austin, and Houston are absent. Reconcile every multi-county summary to its declared relationship count. Do not open a URL.

## Dry run only

Resolve the project Python executable and use a fresh attempt-labeled path:

```bash
<PYTHON> scripts/gabriel_state_source_scout.py \
  --dry-run \
  --state TX \
  --municipalities-csv docs/analysis/worker_3_tx50_scout_input_2026-07-21.csv \
  --output-dir tmp/worker_3_tx50_prep_dry_run_<ATTEMPT_LABEL> \
  --prompt-mode minimal
```

Do not run a smoke preflight, add `--live`, call an API/model, or inspect credentials. Require prompt-preview and dry metadata only with `live_attempted=false`.

Inspect all 50 prompts and create `docs/analysis/worker_3_tx50_filter_contract_dry_run_review_<ATTEMPT_LABEL>.md`. Require 50/50 exact employer/ID checks, every county relationship, prohibited-employer exclusions, ordinary general-municipal civilian scope or exact authoritative civilian wage-setting pathway, safety-not-non-safety, context/insufficient and blocked/dead distinctions, visible year evidence, duplicate controls, matched-cycle purpose, allowed empty results, no public-records request, and unverified-stage quarantine. Do not let a county, transit, port/airport, utility, special district, school, university, or private provider substitute for the municipality. Stop on any failed check without editing the locked batch ad hoc.

## Protected files and relay

Do not update national queue/coverage, global builders/summaries/methodologies, durable cost logs, `PROGRESS.md`, the main handoff, canonical CSVs, or corpus files. Do not verify, download, ingest, or codify.

Create one local worker-prep commit containing only batch-specific prep evidence. Then create a sanitized Worker 3 prep relay ZIP under `tmp/` with the locked input, methodology, prompt, dry artifacts/review, no-network validation outputs, commit/status/diff/changed-file evidence, protected-file comparison, and `next_task.md`. The note must say the relay is prep-only and that the main coordinator later owns the one smoke and one serialized 150-row live queue. Include no `.env`, credentials, source content, or national accounting mutation.
