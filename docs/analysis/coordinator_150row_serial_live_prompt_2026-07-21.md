# Future Coordinator 150-Row Serialized Live Prompt

Use this prompt only in the main coordinator repository and only after all three persistent workers return sanitized offline-preparation relays. This is a future task requiring separate API/live authorization. Do not inspect or modify remotes, and do not push.

## Inputs and required relay audit

Read `AGENTS.md`, `three_worker_50row_batch_plan_2026-07-21.md`, all three worker methodologies/prompts/inputs, the parallel coordinator template, the direct-SDK backend note, and the serialized recovery review. Record the starting local commit.

Inspect all three worker prep relays. Each must contain its exact locked 50-row input, dry-run prompt preview and metadata, a 50/50 filter-contract review, protected-file comparison, validation evidence, local commit/status/diff records, and a prep-only next-task note. Confirm that workers used their persistent worktrees; ran dry-run only; did not run a smoke, live scout, API/model, hosted search, verification, ingestion, codify, or national rebuild; and did not alter global/canonical files or expose a secret.

Reject the wave before any API action if any relay or dry review is incomplete. Do not repair a failed worker review silently in the coordinator task.

## Reconcile and lock one 150-row input

Reconcile every row against the then-current authoritative universe, municipality coverage, candidate queue, canonical overlap, crosswalk, and timeout exclusion list. If a row has since become covered, queued, canonical, failure-only, duplicated, or prohibited, stop and prepare a separately reviewed replacement plan; do not substitute ad hoc.

Combine the three CSVs into one new locked input in this exact order:

1. Worker 1 CA priority ranks 1–50;
2. Worker 2 NJ priority ranks 1–50;
3. Worker 3 TX priority ranks 1–50.

Preserve every original column and add no inferred source fact. Assert 150 rows, 150 unique municipality IDs, 150 unique Census government IDs, one future queue ID, worker counts 50/50/50, state counts 50/50/50, exact within-worker ordering, valid county relationship counts, `municipal` / `place` only, and `not_scouted` eligibility. Hash and lock the combined input before any smoke/live action.

## Mandatory runner-capability gate

The current 2026-07-21 scout is not yet capable of this exact run: `load_municipalities()` filters to one `--state`, and live execution clips at `LIVE_HARD_CAP=25`. Before smoke, implement a small reviewed runner enhancement that explicitly supports a locked mixed-state input and a live cap of at least 150. Add no-network regression tests proving:

- all 150 mixed-state rows load once in file order;
- each prompt and identifier uses that row's own state and municipality ID;
- `--max-prompts 150` is not clipped;
- dry-run behavior stays no-network;
- direct-SDK execution remains `n_parallels=1`, zero retries, and ordered;
- lifecycle, stop-guard, raw/failure/cost, and sanitized-log artifacts remain complete; and
- existing direct-SDK and prompt-contract tests still pass.

Review and commit that enhancement separately before API use. If the runner still reports a hard cap below 150, requires one state filter, loads fewer/more than 150 rows, or changes order, stop. Do not split the batch into worker-owned live runs under this prompt.

## One smoke, then one sequential live process

After all offline gates pass and separate live authorization is explicit, use one fresh coordinator-owned output family and run exactly one direct-SDK synthetic smoke preflight. It must send `Reply with OK.`, use no tools/search, one request, a timeout no higher than 30 seconds, and zero retries. Require `OK`/`OK.`, a response ID when exposed, positive output tokens, and explicit success. If it fails, stop without launching research prompts.

After the successful smoke, retain exclusive control of the API lane and run exactly one live process over the locked 150-row file with:

- direct SDK and `gpt-5.4-nano`;
- mixed-state mode explicitly enabled;
- `--max-prompts 150` and an effective live cap at least 150;
- `--n-parallels 1`;
- `--sleep-between-prompts 15`;
- low search context;
- 90-second request timeout unless a separately reviewed change says otherwise;
- `--direct-sdk-max-retries 0`; and
- a queue-specific cost-log path inside the coordinator run artifact directory.

Capture launch/stop timestamps, exact sanitized command, exit code, sanitized console output, prompt preview, lifecycle metadata, all raw responses, parsed candidates, failure ledger, usage/cost summaries, and stopped-before-request evidence. Preserve the locked input and its hash with the run.

Stop on connection collapse, defined conservatively as two consecutive no-ID/no-text/no-token connection or timeout failures, or an equivalent repeated transport pattern. Also stop on systematic parser/schema failure, lifecycle/artifact loss, unexpected protected-file mutation, or secret exposure. Do not retry a failed municipality, substitute a row, or resume into the same output directory. Preserve partial artifacts and classify only outcomes supported by parseable model evidence.

## One post-run accounting rebuild

Audit the complete live artifact set before accounting. Confirm locked/attempted/stopped/response-ID/token/parseable/empty/candidate/failure counts and reconcile each of 150 municipality IDs. Parseable candidate and parseable-empty outcomes are discovery-covered; connection-only, malformed, absent, and stopped-before-request outcomes are not.

Only if the run is merge-eligible, normalize every candidate as `unverified_scout_candidate`, add the exact source/run specifications to the candidate-queue and coverage builders, preserve all prior rows, merge the queue-specific cost record, and rebuild in this order exactly once:

1. national candidate queue;
2. national municipality/state/county scout coverage; and
3. dependent summaries/dashboard accounting when required by the established workflow.

If connection collapse stops the process or the artifact set is not merge-eligible, do not rebuild national queue/coverage under this prompt. Preserve the relay and request a separately authorized recovery/accounting decision.

No source verification, URL opening/downloading, public-records activity, ingestion, codify, canonical contract/city-coverage/corpus edit, or claim use is authorized. Finish with the full validation/reconciliation suite, one local coordinator commit for the eligible live/accounting result, and a sanitized relay. Do not push.
