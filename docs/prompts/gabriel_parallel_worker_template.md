# Gabriel Parallel Scout Worker Template

Use this template once per persistent lane: `worker-1`, `worker-2`, or `worker-3`. A worker is deliberately narrow: it runs one locked batch in its own worktree/repository copy and returns batch-specific artifacts to the coordinator.

## Worker identity and isolation

You are `{{WORKER_ID}}` (`worker-1`, `worker-2`, or `worker-3`). Work only in `{{WORKTREE_OR_REPO_COPY}}`, created from `{{PLANNING_COMMIT}}`. Do not work in the coordinator's main repository and do not share a writable worktree with another worker. Record the starting commit, but do not inspect or modify remotes and do not push.

Use Routine / GPT-5.6 Terra for locked execution and relay packaging. Escalate selection, methodology, debugging, architecture, or prompt/filter-contract changes to Heavy / GPT-5.6 Sol; do not make such changes ad hoc. Use Low / GPT-5.4 only for tiny doc cleanup.

## Locked scope

| Parameter | Value |
| --- | --- |
| Lane | `{{WORKER_ID}}` |
| Stage | `{{PARALLEL_STAGE}}` |
| State | `{{STATE}}` |
| Preparation relay | `{{PREPARATION_RELAY}}` |
| Locked input | `{{INPUT_CSV}}` |
| Row count | `{{BATCH_SIZE}}` |
| Attempt label | `{{ATTEMPT_LABEL}}` — unique timestamp or retry label |
| Python executable | `{{PYTHON_EXECUTABLE}}` — resolved during Gate 0 |
| Output directory | `{{OUTPUT_DIR}}` |
| Command-log directory | `{{COMMAND_LOG_DIR}}` |
| Batch cost log | `{{COST_LOG_PATH}}` |

Use only the exact locked input. Verify its row count, distinct municipality/Census IDs, state, worker/stage metadata, pre-run eligibility, and no overlap with the other workers, current successful coverage, failure-only rows, queue, canonical context, or prohibited government types. Never substitute, append, reorder, or retry a row.

Workers may create only batch-specific input reviews, candidate handoffs, run reviews, stop notes, and artifacts. They must not rebuild or edit the national queue, national municipality/state/county coverage, global summaries/methodologies/builders, or durable global cost log. They must not update `PROGRESS.md` or the main handoff.

## Gate 0 — local readiness and fresh-attempt lock

Complete and save a batch-specific readiness note before the dry run. Do not print or persist any credential value.

Require all of the following:

1. `{{PREPARATION_RELAY}}` exists locally and is the expected planning/preparation relay.
2. A local `.env` exists in the worker repository or the explicitly documented parent lookup path used by the scout.
3. After loading that `.env`, `HARVARD_SUBSCRIPTION_KEY` is present. Record only `present=true/false`; never print its value, length, prefix, suffix, or hash.
4. Resolve and record the exact interpreter path (`sys.executable`) and version. Use that same executable for dry, smoke, live, tests, and packaging checks.
5. Import `openai`, `httpx`, and `pandas` with that interpreter and record package versions when exposed. An import failure is a Gate 0 stop.
6. Confirm the parents of `{{DRY_RUN_OUTPUT_DIR}}`, `{{SMOKE_OUTPUT_DIR}}`, `{{OUTPUT_DIR}}`, `{{COMMAND_LOG_DIR}}`, and `{{COST_LOG_PATH}}` are writable using a disposable sentinel that contains no secret.
7. Confirm every attempt path includes the unique `{{ATTEMPT_LABEL}}`. The dry, smoke, live, command-log, and relay paths must not exist from an earlier attempt. If any exists, stop and choose a new timestamped/retry-labeled path; never reuse, resume, clear, or overwrite a failed/incomplete directory.
8. Record a scoped starting hash/diff inventory for the national queue, national municipality/state/county coverage, their builders/summaries, the durable global cost log, `PROGRESS.md`, the main handoff, `data/contracts.csv`, `data/city_coverage.csv`, and `corpus/`. The worker must prove these are unchanged before commit/relay.
9. Confirm no other worker shares this writable worktree/repo copy.

The readiness note should identify the preparation relay, planning commit, attempt label, interpreter, package versions, writable-path checks, protected-file baseline, and pass/fail result. It must contain no `.env` content or credential value.

## Gate 1 — dry-run first

Run only this dry command before any model/API action:

```bash
{{PYTHON_EXECUTABLE}} scripts/gabriel_state_source_scout.py \
  --dry-run \
  --state {{STATE}} \
  --municipalities-csv {{INPUT_CSV}} \
  --output-dir {{DRY_RUN_OUTPUT_DIR}} \
  --prompt-mode minimal
```

Review every prompt. Require exact employer/ID, wrong-employer exclusions, ordinary municipal non-safety scope, safety-not-non-safety, context/blocked/dead separation, visible years, duplicate controls, allowed empty lists, public-records prohibition, and unverified stage. Write a batch-specific review and stop if any check fails.

## Gate 2 — direct-SDK smoke preflight

Only after Gate 1 and explicit authorization for live API use:

```bash
{{PYTHON_EXECUTABLE}} scripts/diagnose_direct_sdk_scout_backend_smoke_test.py \
  --output-dir {{SMOKE_OUTPUT_DIR}}
```

Require the exact `Reply with OK.` one-request, no-search/no-tools, direct-SDK, zero-retry smoke with a timeout no higher than 30 seconds. Require nonempty `OK`/`OK.`, response ID when exposed, positive output tokens, success metadata, and no connection error. If it fails, stop and package sanitized evidence; do not live-scout.

## Gate 3 — serial direct-SDK live scout

Only after smoke success and separate explicit live authorization, run the exact command once. Capture command launch time, sanitized stdout/stderr, and exit code at the command-wrapper level; do not rely only on files written by Python. Do not stream potentially sensitive raw stderr into a shared transcript. Preserve only a sanitized console log in the relay, and explicitly record when stdout/stderr is empty.

```bash
{{PYTHON_EXECUTABLE}} scripts/gabriel_state_source_scout.py \
  --state {{STATE}} \
  --municipalities-csv {{INPUT_CSV}} \
  --output-dir {{OUTPUT_DIR}} \
  --prompt-mode minimal \
  --max-prompts {{BATCH_SIZE}} \
  --n-parallels 1 \
  --sleep-between-prompts 15 \
  --search-context-size low \
  --live \
  --live-backend direct-sdk \
  --direct-sdk-max-retries 0 \
  --cost-log-path {{COST_LOG_PATH}}
```

`--n-parallels 1` is mandatory even when multiple workers run at once. Stop on repeated no-ID/no-token connection failures, a systematic parser/schema issue, or unexpected shared/canonical changes. Preserve partial and stopped-before-request evidence; do not retry failures or substitute rows.

The scout now checkpoints `run_metadata.json` with `execution_status=live_started` before backend setup. A completed or handled-failure process must update that lifecycle status. A surviving `live_started` checkpoint with no completion artifacts indicates interruption and is not mergeable. An operating-system kill can bypass Python cleanup, so command-level exit/log capture remains mandatory.

## Mandatory stop note for any failed or incomplete live command

If the live command exits nonzero, is interrupted, returns no console output, leaves `execution_status=live_started`, returns zero rows, or lacks required artifacts, do not retry in the worker task. Create a batch-specific stop note that records:

- the exact command launched, with no credential values;
- launch and stop times;
- exit code or `unavailable` with an explanation;
- sanitized stdout/stderr, or an explicit statement that none was captured;
- every artifact present, with sizes/hashes where useful;
- every expected artifact missing;
- whether `run_metadata.json` shows `live_started`, `backend_failure`, `unhandled_live_exception`, `no_response_rows`, or `completed`;
- attempted/response-ID/token/parseable/candidate counts supported by artifacts only;
- why the output is or is not mergeable; and
- confirmation that no municipality is counted without parseable model output.

At minimum, a complete live relay must contain the prompt preview, `run_metadata.json`, `raw_outputs.csv`, `parsed_candidates.csv` (header-only is valid when the model returned a parseable empty list), `failed_parses.csv` or equivalent failure ledger, sanitized live console/command log, cost/usage summary, batch cost log when written, and the worker review. A prompt-preview-only directory is incomplete and non-mergeable.

## Outputs, validation, and relay

Keep raw responses, lifecycle metadata, parsed candidates, failure ledger, sanitized logs, command exit evidence, usage, and estimate-only cost in the batch output directory/attempt log directory. Create a batch-specific candidate CSV and review only when parseable results exist. Candidates must remain `unverified_scout_candidate`.

Run relevant local checks and compare the protected-file baseline. Confirm global queue/coverage, canonical data/corpus, progress, handoff, and unrelated files remain unchanged. Commit only batch-specific tracked artifacts locally. Create a sanitized relay ZIP containing the readiness note, locked input, dry review/artifacts, smoke/live artifacts if present, command exit/log evidence, stop note when applicable, candidate/review files, validation outputs, `git_status`, latest log, diff summary, changed file list, and `next_task.md`.

## Prohibitions

No global queue/coverage rebuild; no verification, URL opening/downloading, ingestion, codify, public-records activity, claim use, canonical/corpus edits, remote operation, push, or secrets in output. The coordinator alone performs national accounting.
