# Worker 2 NJ50 Offline Preparation Prompt

Work only in your persistent Worker 2 worktree, created from the coordinator planning commit that contains this prompt and the locked input. Do not work in the main coordinator repository, inspect or change remotes, or push.

This task is **offline preparation and dry-run review only**. It does not authorize a smoke preflight, live scout, API/model call, hosted search, URL opening, source verification, download, ingestion, codification, national accounting update, or canonical-data change.

## Required inputs

Read `AGENTS.md`, `docs/analysis/three_worker_50row_batch_plan_2026-07-21.md`, `docs/analysis/worker_2_nj50_scout_input_2026-07-21.csv`, `docs/analysis/worker_2_nj50_selection_methodology_2026-07-21.md`, and the parallel-worker template. Use only the template's Gate 0 and Gate 1 offline-preparation controls; smoke/live gates are out of scope.

Record the starting local commit. Confirm exactly 50 NJ rows, one `worker_2` value, one `COORD-SERIAL150-2026-07-21` future queue ID, 50 distinct municipality and Census IDs, only active `municipal` / `place` governments, and only `not_scouted` pre-run coverage. Confirm no township government, current queue/canonical/covered row, or timeout-only name appears—especially Princeton. Do not open any URL.

## Dry run only

Resolve the project Python executable and use a fresh attempt-labeled output directory:

```bash
<PYTHON> scripts/gabriel_state_source_scout.py \
  --dry-run \
  --state NJ \
  --municipalities-csv docs/analysis/worker_2_nj50_scout_input_2026-07-21.csv \
  --output-dir tmp/worker_2_nj50_prep_dry_run_<ATTEMPT_LABEL> \
  --prompt-mode minimal
```

Do not run the smoke helper, do not add `--live`, do not call an API/model, and do not inspect credential values or presence. Require prompt-preview plus dry metadata only and `live_attempted=false`.

Inspect all 50 prompts and create `docs/analysis/worker_2_nj50_filter_contract_dry_run_review_<ATTEMPT_LABEL>.md`. Require 50/50 exact employer and Census-ID checks; categorical exclusion of counties, schools, authorities, districts, townships, and private providers; ordinary civilian non-safety scope; safety-not-non-safety; context/insufficient and blocked/dead distinctions; visible years; duplicate controls; matched-cycle purpose; allowed empty output; no public-records request; and unverified-stage quarantine. Pay special attention to same-name municipality, township, county, school, and authority leakage. On any failure, stop and document it without changing the locked input.

## Protected files and relay

Do not update national queue/coverage or global summaries/builders/cost logs. Do not touch `PROGRESS.md`, the main handoff, canonical contracts/city coverage, or corpus files. Do not verify or ingest.

Create one local worker-prep commit limited to batch-specific prep evidence, then create a sanitized Worker 2 prep relay ZIP under `tmp/`. Include the locked input, methodology, prompt, dry-run artifacts/review, no-network validation evidence, starting/latest commit, `git_status`, diff summary, changed-files list, protected-file comparison, and `next_task.md`. State clearly that the relay is prep-only and that the future main coordinator—not this worker—owns the single smoke and 150-row serialized live run. Include no secret, `.env`, source content, or stale/global accounting output.
