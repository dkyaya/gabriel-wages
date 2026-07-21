# Worker 1 CA50 Offline Preparation Prompt

Work only in your persistent Worker 1 worktree, created from the coordinator planning commit that contains this prompt and the locked input. Do not work in the main coordinator repository, inspect or change remotes, or push.

This task is **offline preparation and dry-run review only**. It does not authorize a smoke preflight, live scout, API/model call, hosted search, URL opening, source verification, download, ingestion, codification, national accounting update, or canonical-data change.

## Required inputs

Read, in order:

1. `AGENTS.md`.
2. `docs/analysis/three_worker_50row_batch_plan_2026-07-21.md`.
3. `docs/analysis/worker_1_ca50_scout_input_2026-07-21.csv`.
4. `docs/analysis/worker_1_ca50_selection_methodology_2026-07-21.md`.
5. `docs/prompts/gabriel_parallel_worker_template.md`, using only its Gate 0 and Gate 1 offline-preparation controls. Its smoke/live gates are out of scope.

Record your starting local commit and confirm the input has exactly 50 CA rows, one `worker_1` value, one `COORD-SERIAL150-2026-07-21` future queue ID, 50 distinct municipality IDs, 50 distinct Census government IDs, only `municipal` / `place` employers, and only `coverage_status_before_run=not_scouted`. Confirm none of Bloomington, Oakland, Stockton, Oxnard, Redding, Fairfield, or Princeton appears. Do not open any returned or embedded URL.

## Dry run only

Resolve the worktree's project Python executable without printing secrets. Use a fresh attempt-labeled output path, then run exactly:

```bash
<PYTHON> scripts/gabriel_state_source_scout.py \
  --dry-run \
  --state CA \
  --municipalities-csv docs/analysis/worker_1_ca50_scout_input_2026-07-21.csv \
  --output-dir tmp/worker_1_ca50_prep_dry_run_<ATTEMPT_LABEL> \
  --prompt-mode minimal
```

Do not add `--live`, do not run `diagnose_direct_sdk_scout_backend_smoke_test.py`, and do not test credential presence. A dry run should create only prompt-preview and dry-run metadata artifacts and should record `live_attempted=false`.

Inspect all 50 prompts. Write `docs/analysis/worker_1_ca50_filter_contract_dry_run_review_<ATTEMPT_LABEL>.md` and require 50/50 checks for exact municipality/government ID, exact employer, prohibited employer types, ordinary municipal civilian scope, safety-not-non-safety, context/insufficient separation, blocked/dead separation, visible-year evidence, duplicate controls, matched-cycle purpose, allowed empty output, public-records prohibition, and unverified scout-stage handling. Stop and document the discrepancy if any check fails; do not edit the locked input ad hoc.

## Protected files and relay

Do not update the national candidate queue, municipality/state/county scout coverage, their builders/methodologies/summaries, the durable cost log, `PROGRESS.md`, the main handoff, `data/contracts.csv`, `data/city_coverage.csv`, or `corpus/`. Do not verify or ingest anything.

Create a local worker-prep commit containing only the batch-specific dry-run review and any intentionally tracked batch-prep evidence. Create a sanitized Worker 1 prep relay ZIP under `tmp/` containing the locked input, methodology, this prompt, dry-run artifacts, dry-run review, relevant no-network validation output, starting/latest commit records, `git_status`, diff summary, changed-files list, protected-file comparison, and `next_task.md`. The next-task note must state that Worker 1 is prep-complete only; all smoke/live work belongs to the future main-coordinator task. Include no `.env`, credential value, raw secret-bearing log, global queue/coverage rebuild, or source content.
