# Future Coordinator 150-Row Serialized Live Prompt After Runner Fix

Use this prompt only in the main coordinator repository. It describes a future task that requires separate smoke/live authorization. It does not authorize any API call now. Do not inspect or modify remotes, and do not push.

## 1. Re-establish the evidence gate

Read `AGENTS.md`, the three locked worker inputs and methodologies, `three_worker_50row_batch_plan_2026-07-21.md`, `three_worker_50row_prep_relay_assessment_2026-07-21.md`, `worker_2_nj50_prompt_contract_rereview_after_municipality_id_fix_2026-07-21.md`, the parallel coordinator template, the serialized recovery review, and the direct-SDK backend note. Record the starting commit and require a clean tracked worktree.

Inspect all three worker prep relays. Worker 1 CA50 and Worker 3 TX50 must retain their offline PASS evidence. Worker 2's original FAIL is not waived: require the coordinator-regenerated NJ50 prompt preview and the 50/50 corrected rereview as the controlling remediation evidence. Confirm that all inputs remain byte-identical to the locked coordinator CSVs and that no worker ran smoke, live, API/model, verification, ingestion, codify, or national accounting.

Stop before any API action if evidence is missing, an input changed, a row is no longer eligible, or the corrected prompt contract is absent.

## 2. Build and lock one mixed-state 150-row input

Reconcile the three inputs against then-current scout coverage, candidate queue, canonical overlap, the authoritative municipality universe/crosswalk, and the timeout-only exclusions. If a row is newly covered, queued, canonical, failure-only, duplicated, or prohibited, stop and prepare a separately reviewed replacement plan. Do not substitute ad hoc.

Combine without reordering:

1. Worker 1 CA ranks 1–50;
2. Worker 2 NJ ranks 1–50; and
3. Worker 3 TX ranks 1–50.

Preserve all original columns. Assert exactly 150 rows, worker counts 50/50/50, state counts CA=50/NJ=50/TX=50, 150 unique municipality IDs, 150 unique Census government IDs, one future queue ID, exact within-worker ordering, and valid county context. Write and record a SHA-256 hash for the locked combined CSV.

Before smoke, run the corrected runner once in dry-run mode over that exact combined file:

```bash
python scripts/gabriel_state_source_scout.py \
  --dry-run \
  --state ALL \
  --allow-mixed-states \
  --municipalities-csv <LOCKED_150_ROW_CSV> \
  --output-dir <FRESH_COORDINATOR_150_DRY_RUN_DIR> \
  --prompt-mode minimal \
  --live-hard-cap 150
```

Require 150 prompts in file order, `input_states=[CA,NJ,TX]`, `allow_mixed_states=true`, `live_hard_cap=150`, and `live_attempted=false`. Audit every prompt for municipality name, state, locked internal municipality ID, government name, Census government ID, county context, expected units, verification notes, strict employer/unit/source controls, empty-candidate guidance, access-state separation, and unverified-stage handling.

## 3. One smoke preflight

Only after the offline gates pass and separate API authorization is explicit, run exactly one fresh direct-SDK no-search smoke:

```bash
python scripts/diagnose_direct_sdk_scout_backend_smoke_test.py \
  --output-dir <FRESH_COORDINATOR_SMOKE_DIR>
```

Require one `Reply with OK.` request, no tools/search, zero retries, timeout no higher than 30 seconds, `success=true`, response text `OK` or `OK.`, a response ID when exposed, and positive output tokens. If any condition fails, stop. Preserve the smoke artifacts; do not reinterpret a connection failure as source evidence.

## 4. One coordinator-controlled sequential live queue

After the successful smoke, run exactly one live process. No worker may run live and no second live process may overlap it.

```bash
python scripts/gabriel_state_source_scout.py \
  --live \
  --live-backend direct-sdk \
  --state ALL \
  --allow-mixed-states \
  --municipalities-csv <LOCKED_150_ROW_CSV> \
  --output-dir <FRESH_COORDINATOR_150_LIVE_DIR> \
  --prompt-mode minimal \
  --model gpt-5.4-nano \
  --search-context-size low \
  --max-prompts 150 \
  --live-hard-cap 150 \
  --n-parallels 1 \
  --sleep-between-prompts 15 \
  --timeout 90 \
  --direct-sdk-max-retries 0 \
  --cost-log-path <FRESH_COORDINATOR_150_LIVE_DIR>/batch_cost_log.csv
```

The two `150` values are separate authorizations: `--max-prompts 150` requests exactly 150 rows and `--live-hard-cap 150` permits no more than 150. The runner must fail rather than truncate if they disagree or if the loaded mixed-state file does not contain exactly 150 rows. Require direct SDK, `n_parallels=1`, zero retries, no `--limit`, and no retry-file mode.

Preserve the locked input/hash, sanitized command and console output, timestamps, exit code, prompt preview, lifecycle metadata, raw outputs, parsed candidates, failure ledger, usage/cost summaries, and stopped-before-request evidence.

Stop on connection collapse: two consecutive no-ID/no-text/no-token connection or timeout failures, or an equivalent repeated transport pattern. Also stop on systematic parser/schema failure, lifecycle/artifact loss, unexpected protected-file mutation, or any secret exposure. Do not restart into the same directory, retry a failed municipality, or substitute a row. Preserve partial artifacts and leave accounting unchanged pending a separately authorized recovery decision.

## 5. One post-run accounting boundary

After a fully completed, merge-eligible run, reconcile all 150 IDs and classify only parseable candidate or parseable-empty outcomes as discovery-covered. Connection-only, malformed, absent, and stopped-before-request rows do not count.

Then add only unverified scout candidates/outcome metadata to the existing builders and rebuild the national candidate queue and municipality/state/county coverage once. Preserve earlier rows and reconcile the one queue-specific usage/cost family. If the live process stopped on collapse or the artifact set is incomplete, do not rebuild.

No URL opening/downloading, source verification, public-records activity, ingestion, `gabriel.codify`, canonical contracts/city-coverage/corpus edit, candidate promotion, or claim use is authorized. Finish with the established validation suite, one local coordinator commit for an eligible result, and a sanitized relay. Do not push.
