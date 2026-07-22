# Future Coordinator 150-Row Serialized Live Prompt With Fast Sleep and Resume

This supersedes `coordinator_150row_serial_live_prompt_after_runner_fix_2026-07-21.md` for future runs using the pace/resume runner. Use it only in the main coordinator repository under separate explicit smoke/live authorization. Reading this prompt does not authorize an API call. Do not inspect or modify remotes and do not push.

## 1. Evidence, code, and input gate

Read `AGENTS.md`, current `PROGRESS.md` and handoff, the worker-prep evidence, the prior coordinator result review, `scout_runtime_pace_analysis_2026-07-21.md`, and `scout_pace_settings_recommendation_2026-07-21.md`. Record the starting commit and require a clean tracked worktree.

Require the runner tests proving: exact mixed-state loading; explicit hard cap; default/override pace; `row_timing.csv`; timing metadata; immutable output directories; completed-ID skipping; failure-only selection; resume planning without backend use; and hash mismatch blocking/override recording.

Build or reuse one locked 150-row CSV in approved order. Assert exactly 150 rows, unique municipality and Census government IDs, approved states/workers, complete context, and current eligibility. Record its SHA-256. Stop rather than substitute if any row is no longer eligible.

## 2. Corrected-code dry run

Use a fresh output directory:

```bash
python scripts/gabriel_state_source_scout.py \
  --dry-run \
  --state ALL \
  --allow-mixed-states \
  --municipalities-csv <LOCKED_150_ROW_CSV> \
  --output-dir <FRESH_150_DRY_RUN_DIR> \
  --prompt-mode minimal \
  --live-hard-cap 150 \
  --sleep-between-prompts 5
```

Require 150 prompts in exact file order, 150 dry-planned rows in `row_timing.csv`, the exact input hash in metadata, no live attempt, no backend return, and all row-identity/filter-contract checks. A non-empty output directory is a hard stop.

## 3. One smoke preflight

Only after offline gates pass and API use is explicitly authorized, run exactly one fresh direct-SDK no-search smoke using the canonical helper. Require exact `Reply with OK.`, no tools/search, timeout no higher than 30 seconds, zero retries, success, `OK`/`OK.`, a response ID when exposed, and positive output tokens. If it fails, stop without live scouting.

## 4. One coordinator-controlled serialized live queue

After smoke success, run exactly one live process. No worker may run live and no second live process may overlap it.

```bash
python scripts/gabriel_state_source_scout.py \
  --live \
  --live-backend direct-sdk \
  --state ALL \
  --allow-mixed-states \
  --municipalities-csv <LOCKED_150_ROW_CSV> \
  --output-dir <FRESH_150_LIVE_DIR> \
  --prompt-mode minimal \
  --model gpt-5.4-nano \
  --search-context-size low \
  --max-prompts 150 \
  --live-hard-cap 150 \
  --n-parallels 1 \
  --sleep-between-prompts 5 \
  --timeout 90 \
  --direct-sdk-max-retries 0 \
  --cost-log-path <FRESH_150_LIVE_DIR>/batch_cost_log.csv
```

The two 150 values remain separate exact authorizations. Five-second spacing is explicit for auditability. It does not permit concurrent workers or `n_parallels>1`.

Preserve the locked input/hash, command/exit/timestamps, preview, metadata checkpoints, `row_timing.csv`, raw responses, candidates, failures, sanitized log, and usage/cost summaries. Review total/average/median elapsed time, total sleep, effective rows/hour, failure counts, and each row's identity, timestamps, sleep, parse status, response-ID presence, and tokens.

Stop on two consecutive no-ID/no-text/no-token connection/timeout failures, repeated transport collapse, systematic malformed/parser failure, lifecycle/timing/artifact loss, protected-file mutation, or secret exposure. A graceful collapse stop must preserve stopped-before-request rows. Do not rebuild accounting after a stopped/incomplete run.

## 5. Resume planning after a graceful partial stop

Resume is permitted only under separate authorization and only when the parent is a post-patch terminal live directory with `input_csv_sha256` and `row_timing.csv`. OS-killed, `live_started`, prompt-only, corrupt, or old pre-instrumentation directories are not resumable.

Never reuse the parent directory. First run a no-backend plan in a fresh directory:

```bash
python scripts/gabriel_state_source_scout.py \
  --dry-run \
  --state ALL \
  --allow-mixed-states \
  --municipalities-csv <SAME_LOCKED_150_ROW_CSV> \
  --resume-from-output-dir <PARENT_LIVE_DIR> \
  --output-dir <FRESH_RESUME_DRY_RUN_DIR> \
  --retry-failures-only \
  --failure-retry-types timeout,connection_error,parse_error,malformed_output \
  --resume-lineage-note "<SANITIZED_LINEAGE_NOTE>" \
  --prompt-mode minimal \
  --live-hard-cap 150 \
  --sleep-between-prompts 5
```

`--retry-failures-only` skips prior parseable rows and selects authorized failures/stopped-before-request rows. Use `--skip-completed-municipality-ids` instead when the reviewed recovery scope is all noncompleted identities, including rows with no terminal attempt. Inspect `resume_plan.csv`, `resume_summary.json`, preview, timing ledger, counts, identities, and hash evidence. Skipped rows are prior outcomes; they are not newly scouted.

An input hash mismatch is a default hard stop. Use `--allow-resume-input-hash-mismatch` only after a separate explicit row-identity/order audit, and require the mismatch and reason to remain prominent in metadata and review.

Let `R` be the exact reviewed selected-row count. After a newly authorized smoke and only if the dry resume plan passes, run one fresh sequential resume process:

```bash
python scripts/gabriel_state_source_scout.py \
  --live \
  --live-backend direct-sdk \
  --state ALL \
  --allow-mixed-states \
  --municipalities-csv <SAME_LOCKED_150_ROW_CSV> \
  --resume-from-output-dir <PARENT_LIVE_DIR> \
  --output-dir <FRESH_RESUME_LIVE_DIR> \
  --retry-failures-only \
  --failure-retry-types timeout,connection_error,parse_error,malformed_output \
  --resume-lineage-note "<SANITIZED_LINEAGE_NOTE>" \
  --prompt-mode minimal \
  --model gpt-5.4-nano \
  --search-context-size low \
  --max-prompts <R> \
  --live-hard-cap 150 \
  --n-parallels 1 \
  --sleep-between-prompts <5_OR_APPROVED_8_TO_15_SECOND_FALLBACK> \
  --timeout 90 \
  --direct-sdk-max-retries 0 \
  --cost-log-path <FRESH_RESUME_LIVE_DIR>/batch_cost_log.csv
```

If five-second pacing contributed to transport instability, use an explicitly reviewed 8–10-second fallback, then 15 seconds if needed. Never add concurrency. Never recursively resume without first reconciling the full parent→child lineage and obtaining separate authorization.

## 6. Accounting boundary

For an uninterrupted complete run, use its 150 final outcomes. For a completed resume, reconcile parent and child by exact row identity: child outcomes replace only selected prior failed/stopped outcomes; prior parseable outcomes remain prior evidence and must not be presented as newly attempted. Require one final outcome per locked input row and preserve both directories plus the resume plan.

Only after the complete lineage is merge-eligible may the coordinator rebuild candidate queue and municipality/state/county coverage once. Connection-only, malformed, absent, and stopped-before-request outcomes are excluded from successful coverage. Do not rebuild after an incomplete or nonterminal lineage.

All candidates remain unverified scout-stage leads. No source opening/downloading, verification, public-records action, ingestion, `gabriel.codify`, canonical contract/city-coverage/corpus edit, candidate promotion, or claim use is authorized. Finish with validation, one local commit for an eligible result, and a sanitized relay. Do not push.
