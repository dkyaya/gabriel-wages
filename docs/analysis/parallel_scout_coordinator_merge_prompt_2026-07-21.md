# Stage 1 Parallel Scout Coordinator Merge Prompt

Work in the coordinator repository only after both Stage 1 worker agents have stopped or completed and supplied relay bundles. This is a merge/accounting task, not a scout, verification, ingestion, codification, or claim-analysis task.

## Source inputs

Use the parallel-planning relay/commit as the base, then inspect both completed worker relays:

- Worker 01: CA25.2 relay for `parallel_worker_01`
- Worker 02: NJ25 relay for `parallel_worker_02`

Do not assume a worker succeeded merely because it produced a ZIP or commit. Read each relay's git status/log/diff, locked input, dry review, smoke diagnostics, run metadata, raw/failure artifacts, parsed candidates, normalized candidate handoff, review note, cost summary, validation logs, and credential scan.

Do not inspect/configure/create/validate/modify git remotes and do not push.

## Scope audit before import

For each worker, confirm:

- it ran in a separate worktree or repo copy from the same planning checkpoint;
- it used only its exact locked 25-row input;
- dry-run checklist passed before smoke;
- smoke used exactly `Reply with OK.`, direct SDK, no tools/search, one request, at most 30 seconds, and zero retries;
- live execution, if any, used only `--live-backend direct-sdk`, `--n-parallels 1`, 15-second spacing, zero SDK retries, and the batch-specific cost-log path;
- it did not retry or substitute timeout/failure rows;
- it stopped correctly on any checklist, smoke, or repeated-connection failure;
- all candidate rows remain scout-stage and unverified;
- it did not open/download/verify sources, ingest, codify, make public-records requests, or promote rows;
- it did not edit the national candidate queue, national municipality/state/county coverage, their global summaries/methodologies/builders, the durable global cost log, canonical contracts/city coverage, corpus, codified outputs, claim files, `PROGRESS.md`, or the main handoff; and
- it did not expose credential values.

If a worker violated scope, do not blindly cherry-pick its commit. Preserve the relay, document the violation, and import only independently auditable batch-specific artifacts if doing so is safe and within authorization. Unexpected canonical edits are a stop condition.

## Import rules

Import worker-specific candidate and review files without rewriting the other worker's artifacts. A clean batch-only worker commit may be cherry-picked; otherwise copy the reviewed files from the relay and record their hashes. Do not import a worker's stale copy of any global output.

For each municipality, classify the live outcome from raw metadata and failure artifacts:

- `scouted_with_candidates`: backend response succeeded, parsed, and yielded at least one candidate;
- `scouted_no_candidates`: backend response succeeded and parsed a valid empty candidate list;
- `scout_attempt_failed_connection`: connection/transport/timeout failure with no later valid response;
- stopped-before-request or uncalled: not discovery-covered and recorded separately from a source result.

Never count connection-only, stopped-before-request, malformed-output, or absent responses as source-discovery coverage. Never interpret a parseable empty list as proof that no source exists.

## Single global rebuild

Only after both worker imports are reconciled:

1. Add both normalized candidate files and exact run metadata to `SOURCE_SPECS` in `scripts/build_national_scout_candidate_queue.py`. Preserve every existing PA, TX, MA, NJ, IL, NY, and CA source specification and row.
2. Add each worker's successful municipality outcomes and failure-only outcomes to `scripts/build_national_scout_coverage_status.py`. Preserve all prior successful and failed-run accounting.
3. Merge the two batch-specific cost-log records into the durable global log exactly once if that remains the project's canonical usage procedure. Preserve actual-cost-unavailable versus estimate-only fields.
4. Rebuild the national candidate queue once.
5. Rebuild national municipality/state/county discovery coverage once. Use `scripts/build_scout_coverage.py` only if still required as the canonical orchestrator and local Census caches are present; do not download sources merely for this merge.
6. Update queue/coverage methodology and summary notes to describe both workers, their outcome counts, and the Stage 1 concurrency result.

Do not perform source verification while queueing. Do not inspect returned URLs. Do not ingest, codify, change canonical coverage, or use candidates as claim evidence.

## Required reconciliation metrics

Report for each worker and for the pooled 50-row Stage 1 test:

- smoke pass/fail and latency;
- locked municipalities, requests attempted, stopped-before-request rows, backend successes, nonempty responses, response IDs, parseable outcomes, parseable empty outcomes, candidate-positive municipalities, and candidate rows;
- parseable-outcome rate using 25 as each worker's denominator and 50 as the pooled denominator;
- timeout/connection failure rate and parser-failure rate;
- failures by type, repeated-connection stop activation, missing locators, and duplicate identifiers;
- candidate counts by municipality and unit type;
- visible wrong-employer, wrong-unit, safety-as-non-safety, context, blocked/dead, and duplicate leakage;
- input/reasoning/output/total tokens, actual cost availability, estimate-only cost, and pricing caveats;
- queue rows added by worker/state and resulting national queue total;
- candidate-positive, parseable-empty, and failure-only coverage increments by worker/state and resulting national covered count; and
- confirmation that all prior state rows and statuses were preserved.

## Stage 1 promotion decision

Recommend Stage 2—exactly three parallel 25-row workers—only if:

- both workers passed smoke;
- both live batches completed without connection collapse;
- each worker and the pooled result achieved at least 90% parseable municipality outcomes, meaning at least 23/25 per worker;
- timeout/failure rates were manageable, normally no more than two non-collapse failures per worker;
- parser/schema failures were at most 10% and not systematic;
- candidate volume and provenance were manageable;
- no worker corrupted or edited shared accounting/canonical files;
- the combined queue/coverage rebuild was clean and preserved all earlier states; and
- the full validation suite passed.

If any criterion fails, Stage 1 is not proven. Recommend a bounded diagnostic or another two-worker 25-row test; do not escalate to three workers and do not retry failure-only municipalities without separate authorization.

Even if Stage 1 passes, do not jump to 50-row workers. Stage 2 must first prove three concurrent 25-row workers under the same gates. The current `LIVE_HARD_CAP=25` also requires a separately reviewed code/test change before any future 50-row live task.

## Validation and handoff

Run all required compile, direct-SDK, prompt-contract, schema, ingestion-pipeline, coverage-audit, queue/coverage reconciliation, artifact, and credential checks. Update `PROGRESS.md` and `docs/analysis/chatgpt_handoff_latest.md` with the combined Stage 1 result and promotion decision. Create one clean local coordinator commit and one relay bundle containing all imported worker files, global rebuild outputs, validation evidence, git summaries, and a next-task note.

Do not push and do not inspect remotes.
