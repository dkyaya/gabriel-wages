# Stage 1 Parallel Worker 02 Prompt — New Jersey NJ25

Work only in a dedicated git worktree or complete repo copy created from the coordinator's parallel-planning commit. Do not work in the coordinator's original writable repository and do not share a worktree with Worker 01.

This is Stage 1 of the parallel ladder. Exactly two worker agents are expected to run concurrently: Worker 01 CA25.2 and Worker 02 NJ25. Keep the scout serial inside this worker. The coordinator will inspect and merge both relays later.

## Source of truth and required reading

Treat `tmp/national_batch01_ca25_live_direct_sdk_2026-07-21_relay_d4ca8d0.zip` as the historical national-scout source of truth, with the coordinator's parallel-planning commit adding only the locked Stage 1 materials. Inspect the ZIP and reconcile shared files before acting. Read:

- `AGENTS.md`
- the newest `PROGRESS.md` and `docs/analysis/chatgpt_handoff_latest.md` entries
- `docs/analysis/parallel_scout_workflow_2026-07-21.md`
- `docs/analysis/parallel_worker_02_nj25_scout_input_2026-07-21.csv`
- `docs/analysis/parallel_worker_02_nj25_selection_methodology_2026-07-21.md`
- `docs/analysis/national_batch01_ca25_live_direct_sdk_scout_review_2026-07-20.md`
- `docs/analysis/national_scout_candidate_queue_summary_2026-07-20.md`
- `docs/analysis/national_scout_candidate_queue_methodology_2026-07-20.md`
- `docs/analysis/national_scout_coverage_status_methodology_2026-07-20.md`
- `docs/analysis/direct_sdk_scout_backend_2026-07-20.md`
- `scripts/gabriel_state_source_scout.py`
- `scripts/diagnose_direct_sdk_scout_backend_smoke_test.py`
- `scripts/test_gabriel_state_source_scout_direct_sdk.py`
- `scripts/test_gabriel_state_source_scout_prompt.py`

Record the starting commit. Never inspect or modify remotes and never push.

## Hard scope

- Use only the exact locked NJ25 input. No substitutions, additions, timeout retries, or other state.
- Use `--live-backend direct-sdk`, `--n-parallels 1`, 15-second spacing, and zero SDK retries.
- Do not rebuild or edit the national queue/coverage files, their builders, national summaries/methodologies, `PROGRESS.md`, or the main handoff.
- Use the batch-specific `--cost-log-path`; do not touch the global cost log.
- Do not verify/open/download sources, ingest, codify, alter canonical data/corpus, promote rows, make public-records requests, or use output as claim evidence.
- Do not inspect/configure/create/validate/modify remotes, push, or print/package secrets.

## Stage 1 retry Gate 0: readiness and unique attempt paths

This locked prompt is now for a hardened same-stage retry. Set one unique `{{ATTEMPT_LABEL}}` containing a retry label or timestamp and use it in every dry, smoke, live, command-log, review, and relay path below. The prior smoke/live directories—including the prompt-preview-only live directory—are evidence; never reuse, delete, clear, resume, or overwrite them.

Before the dry run, create a credential-free readiness note confirming:

- the preparation relay exists locally;
- the worker-local `.env` exists;
- `HARVARD_SUBSCRIPTION_KEY` is present after `.env` load, recording only presence and never value/length/prefix/suffix/hash;
- the exact Python executable path/version that will run every command;
- successful imports and package versions for `openai`, `httpx`, and `pandas`;
- writable parents for the unique dry, smoke, live, command-log, cost-log, and relay paths;
- none of those attempt paths already exists;
- a protected-file hash/diff baseline for national queue/coverage/builders/summaries/global cost log, `PROGRESS.md`, main handoff, canonical data, and corpus; and
- this worktree is not shared with Worker 01.

Any failure is a Gate 0 stop. Do not smoke or live-scout. The two Stage 1 worker starts must be staggered by 5–10 minutes; in-process concurrency remains one.

## Gate 1: input and dry run

Verify exactly 25 distinct NJ municipal/place rows with distinct IDs, `worker_id=parallel_worker_02`, Stage 1 status, untouched coverage, zero failure attempts, no queue/canonical overlap, no overlap with Worker 01, and no prohibited government type. The accepted `CITY`, `TOWN`, `BOROUGH`, or `MUNICIPALITY` name does not override the authoritative `municipal` / `place` requirement.

Run only this dry command first:

```bash
{{PYTHON_EXECUTABLE}} scripts/gabriel_state_source_scout.py \
  --dry-run \
  --state NJ \
  --municipalities-csv docs/analysis/parallel_worker_02_nj25_scout_input_2026-07-21.csv \
  --output-dir tmp/gabriel_state_source_scout/NJ/parallel_worker_02_nj25_{{ATTEMPT_LABEL}}_filter_contract_dry_run_2026-07-21 \
  --prompt-mode minimal
```

Review all 25 prompts and create an attempt-labeled `docs/analysis/parallel_worker_02_nj25_{{ATTEMPT_LABEL}}_filter_contract_dry_run_review_2026-07-21.md`. Require exact employer/Census ID, wrong-employer exclusions, ordinary civilian comparator rules, safety-not-non-safety, context separation, blocked-versus-dead, visible years, duplicate risk, empty output, public-records prohibition, and unverified-stage language. Stop if any check fails.

## Gate 2: synthetic direct-SDK smoke

Only after dry approval and explicit authorization for live API use:

```bash
{{PYTHON_EXECUTABLE}} scripts/diagnose_direct_sdk_scout_backend_smoke_test.py \
  --output-dir tmp/direct_sdk_scout_backend_preflight/NJ/parallel_worker_02_nj25_{{ATTEMPT_LABEL}}_2026-07-21
```

The prompt must be exactly `Reply with OK.` with `gpt-5.4-nano`, the HUIT `/v2` base, no search/tools, one prompt, at most 30 seconds, and zero retries. Require nonempty text, response ID when exposed, positive output tokens, success metadata, and no connection error. Stop on failure.

## Gate 3: exact live run

Only after smoke success and explicit live authorization, run exactly once. Capture the exact command, start/stop time, exit code, and sanitized stdout/stderr in the attempt-specific command-log directory. Explicitly record if stdout/stderr is empty.

```bash
{{PYTHON_EXECUTABLE}} scripts/gabriel_state_source_scout.py \
  --state NJ \
  --municipalities-csv docs/analysis/parallel_worker_02_nj25_scout_input_2026-07-21.csv \
  --output-dir tmp/gabriel_state_source_scout/NJ/parallel_worker_02_nj25_{{ATTEMPT_LABEL}}_live_direct_sdk_2026-07-21 \
  --prompt-mode minimal \
  --max-prompts 25 \
  --n-parallels 1 \
  --sleep-between-prompts 15 \
  --search-context-size low \
  --live \
  --live-backend direct-sdk \
  --direct-sdk-max-retries 0 \
  --cost-log-path tmp/gabriel_state_source_scout/NJ/parallel_worker_02_nj25_{{ATTEMPT_LABEL}}_live_direct_sdk_2026-07-21/batch_cost_log.csv
```

Stop on repeated no-ID/no-token connection failures. Preserve partial artifacts, do not retry, and do not substitute municipalities.

The scout must create `run_metadata.json` with `execution_status=live_started` before backend setup and finalize it on handled completion/failure. If it remains `live_started`, exits nonzero, returns zero rows, or lacks required artifacts, create an attempt-specific stop note listing the launched command, exit code or unavailable reason, sanitized stdout/stderr or explicit absence, artifacts present/missing, supported outcome counts, and why the relay is non-mergeable. Do not retry.

## Batch-specific outputs

Preserve every readiness, lifecycle, command-exit, run, failure, usage, and sanitized-log artifact. A complete live relay requires `run_metadata.json`, `raw_outputs.csv`, `parsed_candidates.csv`, `failed_parses.csv` or equivalent ledger, sanitized command/live log, cost/usage evidence, and worker review. A prompt-preview-only directory is non-mergeable. If candidates parse, create attempt-labeled candidate/review files derived from:

- `docs/analysis/parallel_worker_02_nj25_{{ATTEMPT_LABEL}}_live_direct_sdk_scout_candidates_2026-07-21.csv`
- `docs/analysis/parallel_worker_02_nj25_{{ATTEMPT_LABEL}}_live_direct_sdk_scout_review_2026-07-21.md`

All normalized candidates remain `unverified_scout_candidate`. Report municipality/unit counts, valid empty results, parse/transport failures, leakage, tokens, and estimate-only cost. Never update shared queue/coverage.

## Validation, commit, and relay

Run the full local compile/test/validation suite and batch artifact assertions. Verify that national queue/coverage, global cost log, canonical data/corpus, progress, handoff, and unrelated tracked files remain unchanged.

Create one local commit with only batch-specific tracked outputs and one uniquely labeled sanitized worker relay ZIP containing the readiness note, locked input/methodology, dry review/artifacts, smoke/live artifacts if run, command exit/log evidence, stop note if applicable, protected-file comparison, validation logs, git summaries, changed-file list, and next-task note. Do not push. The coordinator will not merge unless both Stage 1 workers produce complete merge-eligible relays.
