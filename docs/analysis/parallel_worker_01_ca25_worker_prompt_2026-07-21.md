# Stage 1 Parallel Worker 01 Prompt — California CA25.2

Work only in a dedicated git worktree or complete repo copy created from the coordinator's parallel-planning commit. Do not work in the coordinator's original writable repository and do not share a worktree with Worker 02.

This is Stage 1 of the parallel ladder. Exactly two worker agents are expected to run concurrently: Worker 01 CA25.2 and Worker 02 NJ25. Your in-process scout concurrency must remain one. The coordinator will inspect and merge both worker relays later.

## Source of truth and required reading

Treat this historical relay as the source of truth for completed national-scout state before the parallel planning commit:

`tmp/national_batch01_ca25_live_direct_sdk_2026-07-21_relay_d4ca8d0.zip`

Inspect the ZIP before acting. Reconcile shared relay/repository files and prefer the relay unless the planning commit clearly adds the parallel-workflow files. Read at minimum:

- `AGENTS.md`
- `PROGRESS.md` newest entry
- `docs/analysis/chatgpt_handoff_latest.md` newest entry
- `docs/analysis/parallel_scout_workflow_2026-07-21.md`
- `docs/analysis/parallel_worker_01_ca25_scout_input_2026-07-21.csv`
- `docs/analysis/parallel_worker_01_ca25_selection_methodology_2026-07-21.md`
- `docs/analysis/national_batch01_ca25_live_direct_sdk_scout_review_2026-07-20.md`
- `docs/analysis/national_scout_candidate_queue_summary_2026-07-20.md`
- `docs/analysis/national_scout_candidate_queue_methodology_2026-07-20.md`
- `docs/analysis/national_scout_coverage_status_methodology_2026-07-20.md`
- `docs/analysis/direct_sdk_scout_backend_2026-07-20.md`
- `scripts/gabriel_state_source_scout.py`
- `scripts/diagnose_direct_sdk_scout_backend_smoke_test.py`
- `scripts/test_gabriel_state_source_scout_direct_sdk.py`
- `scripts/test_gabriel_state_source_scout_prompt.py`

Record the starting commit. Do not inspect, configure, create, validate, or modify git remotes, and do not push.

## Hard scope

- Use only the exact locked 25 rows in `parallel_worker_01_ca25_scout_input_2026-07-21.csv`; do not substitute or append a municipality.
- Do not retry Oakland, Stockton, Oxnard, Redding, Bloomington, or any new timeout-only row.
- Use the direct-SDK backend only for live scouting.
- Keep `--n-parallels 1`, `--direct-sdk-max-retries 0`, and the 15-second prompt spacing.
- Do not run another state or a second batch.
- Do not rebuild or edit `national_scout_candidate_queue_2026-07-20.csv`, any national scout coverage CSV, their builders, their summaries/methodologies, `PROGRESS.md`, or the main handoff.
- Route cost logging to the batch-specific output path shown below. Do not edit the global `gabriel_state_source_scout_cost_log.csv`.
- Do not open or download source URLs, verify sources, ingest, run `gabriel.codify`, edit `data/contracts.csv`, edit `data/city_coverage.csv`, edit `corpus/`, promote candidates, or use scout output as claim evidence.
- Do not make or recommend a CPRA/PRA or any other public-records request.
- Do not print or package secrets.

## Gate 1: input and dry run

Before any live action, verify programmatically that the CSV has exactly 25 distinct CA municipal/place rows; distinct municipality/Census IDs; `worker_id=parallel_worker_01`; `parallel_stage=stage_1_two_parallel_25`; `coverage_status_before_run=not_scouted`; zero overlap with current successful coverage, failure-only rows, queue municipalities, canonical corpus context, Worker 02, or prohibited government types.

Run only this dry command first:

```bash
.venv/bin/python scripts/gabriel_state_source_scout.py \
  --dry-run \
  --state CA \
  --municipalities-csv docs/analysis/parallel_worker_01_ca25_scout_input_2026-07-21.csv \
  --output-dir tmp/gabriel_state_source_scout/CA/parallel_worker_01_ca25_filter_contract_dry_run_2026-07-21 \
  --prompt-mode minimal
```

Inspect every rendered prompt and create `docs/analysis/parallel_worker_01_ca25_filter_contract_dry_run_review_2026-07-21.md`. Confirm exact employer/ID, wrong-employer exclusions, ordinary municipal non-safety meaning, safety-not-non-safety, context separation, blocked-versus-dead, visible years, duplicates, empty-list permission, public-records prohibition, and unverified stage. If any item fails, stop; do not smoke or live-scout.

## Gate 2: synthetic direct-SDK smoke

Only after the dry review passes and live API use is explicitly authorized, run:

```bash
.venv/bin/python scripts/diagnose_direct_sdk_scout_backend_smoke_test.py \
  --output-dir tmp/direct_sdk_scout_backend_preflight/CA/parallel_worker_01_ca25_2026-07-21
```

The helper must send exactly `Reply with OK.`, use `gpt-5.4-nano`, the Harvard HUIT `/v2` base, no search/tools, one prompt, timeout no higher than 30 seconds, direct SDK, and zero retries. Require nonempty `OK`/`OK.`, response ID when exposed, positive output tokens, success metadata, and no connection error. If smoke fails, stop and create a sanitized stop relay; do not live-scout.

## Gate 3: exact live run

Only after smoke success and explicit live authorization, run exactly:

```bash
.venv/bin/python scripts/gabriel_state_source_scout.py \
  --state CA \
  --municipalities-csv docs/analysis/parallel_worker_01_ca25_scout_input_2026-07-21.csv \
  --output-dir tmp/gabriel_state_source_scout/CA/parallel_worker_01_ca25_live_direct_sdk_2026-07-21 \
  --prompt-mode minimal \
  --max-prompts 25 \
  --n-parallels 1 \
  --sleep-between-prompts 15 \
  --search-context-size low \
  --live \
  --live-backend direct-sdk \
  --direct-sdk-max-retries 0 \
  --cost-log-path tmp/gabriel_state_source_scout/CA/parallel_worker_01_ca25_live_direct_sdk_2026-07-21/batch_cost_log.csv
```

Stop immediately if repeated connection errors occur without response IDs or output tokens. Preserve stopped-before-request rows and all sanitized evidence. Do not retry or substitute rows.

## Batch-specific outputs

Preserve all prompt, metadata, raw response, parsed candidate, failure, sanitized log, usage, and estimate-only cost artifacts in the worker output directory. If candidates parse, create:

- `docs/analysis/parallel_worker_01_ca25_live_direct_sdk_scout_candidates_2026-07-21.csv`
- `docs/analysis/parallel_worker_01_ca25_live_direct_sdk_scout_review_2026-07-21.md`

Every normalized row must have `scout_stage_status=unverified_scout_candidate`. The review must report municipality/unit counts, parseable-empty outcomes, connection/timeouts, parser failures, stopped rows, leakage, token usage, estimate-only cost, and exact scope boundaries. Do not update national queue or coverage.

## Validation, commit, and relay

Run the repository compile/tests/validation suite, plus batch-specific schema and artifact checks. Confirm that global queue/coverage, canonical data, corpus, `PROGRESS.md`, and the main handoff are unchanged from the worker's starting commit.

Create one local worker commit containing only batch-specific tracked review/candidate outputs. Do not push. Create a worker relay ZIP under `tmp/` containing the commit diff, locked input and methodology, dry artifacts/review, smoke artifacts if run, live artifacts if run, validation logs, git status/log/diff summaries, a next-task note, and a credential scan. The coordinator will audit both Stage 1 relays and perform the only global queue/coverage merge.
