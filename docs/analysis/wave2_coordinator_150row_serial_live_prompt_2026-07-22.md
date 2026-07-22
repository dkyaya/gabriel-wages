# Wave 2 Future Coordinator 150-Row Serialized Live Prompt

Use this prompt only in the main coordinator repository under a new explicit smoke/live authorization. The current planning task does not authorize an API call. Never inspect or modify remotes, and never push.

## 1. Worker relay and current-eligibility gate

Read `AGENTS.md`, current `PROGRESS.md`/handoff, `next_3x50_batch_selection_audit_2026-07-22.md`, `wave2_3x50_batch_plan_2026-07-22.md`, the pace/resume recommendation, and all three worker prep relays.

For Worker 1 CA50, Worker 2 TX50, and Worker 3 IL50, require:

- the relay comes from the assigned persistent worktree and expected branch;
- the locked input/methodology/prompt match the planning commit;
- structural checks pass at exactly 50 rows, one state/worker/future queue ID, and 50 unique municipality/Census IDs;
- dry metadata reports 50 prompts, five-second pace metadata, no backend/live attempt, and terminal dry completion;
- `row_timing.csv` has 50 dry-planned, not-attempted rows;
- the review passes every row-aware/filter-contract item 50/50;
- no smoke, API/model, hosted search, live scout, URL access, verification, ingestion, codify, queue/coverage rebuild, canonical mutation, or secret exposure occurred; and
- no protected/global file differs from the planning baseline.

Reconcile all 150 rows to current coverage, queue, canonical context, employer type, and failure status immediately before combination. If any row is newly covered/queued/canonical/ineligible, stop rather than substitute ad hoc. Require the same eight timeout names to remain absent.

## 2. Combine and lock the input

Combine CSVs in exact worker order:

1. Worker 1 CA ranks 1–50;
2. Worker 2 TX ranks 1–50; and
3. Worker 3 IL ranks 1–50.

Preserve the shared schema and write a new coordinator input. Assert exactly 150 rows; CA/TX/IL=50 each; worker_1/2/3=50 each; one `COORD-SERIAL150-WAVE2-2026-07-22`; 150 unique municipality IDs; 150 unique Census IDs; all `municipal/place`; all currently `not_scouted`; no queue/canonical/failure/prohibited-name overlap; and exact file order. Record SHA-256 in an audit before any API-bearing step.

## 3. Corrected-code 150-row dry run

Use a fresh directory:

```bash
python scripts/gabriel_state_source_scout.py \
  --dry-run \
  --state ALL \
  --allow-mixed-states \
  --municipalities-csv <LOCKED_WAVE2_150_INPUT.csv> \
  --output-dir <FRESH_WAVE2_150_DRY_RUN_DIR> \
  --prompt-mode minimal \
  --live-hard-cap 150 \
  --sleep-between-prompts 5
```

Require exact hash, 150 ordered prompts and timing rows, `input_states=[CA, IL, TX]` in metadata order as serialized by the runner, `allow_mixed_states=true`, `live_hard_cap=150`, sleep 5.0, `live_attempted=false`, and `backend_call_returned=false`. Audit all 150 prompts for municipality/state/internal ID/government/Census/county/expected-unit/verification context and the complete employer/unit/source, empty-result, blocked/dead, duplicate, public-records, and unverified-stage contract. Stop if any check fails.

## 4. One direct-SDK no-search smoke

Only with explicit API authorization and after every offline gate passes, run exactly one canonical direct-SDK smoke in a fresh directory. Require one request; exact `Reply with OK.`; no tools/search; timeout no higher than 30 seconds; zero retries; `OK`/`OK.`; response ID when exposed; positive output tokens; and explicit success. If it fails, stop. Do not run live.

```bash
python scripts/diagnose_direct_sdk_scout_backend_smoke_test.py \
  --output-dir <FRESH_WAVE2_DIRECT_SDK_SMOKE_DIR>
```

## 5. One coordinator-controlled live queue

Only after smoke success and explicit live authorization, run exactly one process:

```bash
python scripts/gabriel_state_source_scout.py \
  --live \
  --live-backend direct-sdk \
  --state ALL \
  --allow-mixed-states \
  --municipalities-csv <LOCKED_WAVE2_150_INPUT.csv> \
  --output-dir <FRESH_WAVE2_150_LIVE_DIR> \
  --prompt-mode minimal \
  --model gpt-5.4-nano \
  --search-context-size low \
  --max-prompts 150 \
  --live-hard-cap 150 \
  --n-parallels 1 \
  --sleep-between-prompts 5 \
  --timeout 90 \
  --direct-sdk-max-retries 0 \
  --cost-log-path <FRESH_WAVE2_150_LIVE_DIR>/batch_cost_log.csv
```

No concurrent worker or second coordinator live process is allowed. Preserve the command/exit/timestamps, locked hash, preview, lifecycle metadata, `row_timing.csv`, raw outputs, candidates, failures, sanitized log, and usage/cost summaries. Review total/average/median elapsed time, actual sleep, effective rows/hour, failures by type, response IDs, and tokens.

Stop on two consecutive no-ID/no-text/no-token connection/timeout failures, repeated transport collapse, systematic parser/schema failure, lifecycle/timing/artifact loss, protected mutation, or secret exposure. Do not retry inside the same process or directory.

## 6. Resume after a graceful stop

If the run stops with terminal post-patch metadata, exact input hash, and a complete timing ledger, preserve the parent directory unchanged. Under separate authorization, first make a dry resume plan in a different fresh directory using the same locked CSV and either `--retry-failures-only` or `--skip-completed-municipality-ids`, never both. Inspect `resume_plan.csv`, `resume_summary.json`, skipped prior IDs, selected failures, hash, and lineage note. Hash mismatch is a hard stop unless separately audited and explicitly overridden.

Only after review may one new direct-SDK smoke and one fresh sequential child process be considered. Use exact selected count `R` as `--max-prompts R`, retain `--live-hard-cap 150`, `n_parallels=1`, zero retries, and five seconds unless reviewed instability requires 8–10 or 15 seconds. Never resume into the parent or count skipped parent rows as newly scouted.

## 7. One accounting merge and dashboard refresh

Reconcile one final outcome per locked municipality across parent/child lineage. Only if the run or complete lineage is merge-eligible, add normalized unverified candidates/outcomes to the canonical builders and run the candidate queue, current national coverage, and top-level coverage rebuild once in canonical order. Then refresh dashboard JSON once. Do not copy stale outputs from a worker relay.

Connection-only, malformed, missing, and stopped-before-request rows are not successful coverage. Parseable empty output is coverage but not proof of source absence. No URL opening, verification, source download, ingestion, `gabriel.codify`, canonical contract/city-coverage/corpus edit, candidate promotion, or claim use is authorized. Finish with validation, one local commit, and a sanitized relay; do not push.
