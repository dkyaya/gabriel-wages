# Safe Parallel State-Scout Workflow

Date: 2026-07-21

Status: operating design and locked Stage 1 preparation only. This task made no model/API call, ran no scout, opened no source URL, and changed no queue, discovery-coverage, canonical, ingestion, codified, or claim-stage record.

## Plain-English design

Parallel scouting is now justified because five recent 25-row direct-SDK state batches—IL25, NY25, IL25.2, IL25.3, and CA25—completed the same gated workflow and preserved auditable prompt, response, parse, usage, and failure artifacts. Four of those batches had at least 96% parseable outcomes and three were 25/25; CA25 showed the remaining risk clearly, with four separated timeouts and 21/25 parseable outcomes. That history is enough to test two concurrent workers, but not enough to jump directly to many workers or 50-row runs.

Concurrency must happen across isolated worker repositories, not inside one scout process. Each worker receives one exact 25-row CSV, runs with `--n-parallels 1`, and owns a separate git worktree or separate repository copy. This avoids multiplying concurrency: Stage 1 should create at most two live research calls at once, not two workers times several in-process calls. Serial execution within each worker also preserves municipality-level timing and failure attribution and lets the existing consecutive-connection-error stop guard work predictably.

Workers must not rebuild or edit the national candidate queue or national scout coverage. Those outputs are whole-project snapshots with deterministic expected totals and source specifications. If two workers rebuild them independently from the same base, each output will contain only its own new batch, and the last commit merged can silently erase the other worker's contribution. Concurrent writes would also create unnecessary conflicts in the queue, municipality/state/county coverage tables, methodologies, summaries, and global cost log.

Each worker therefore writes only batch-specific prompt reviews, staged and normalized candidates, run reviews, raw/sanitized artifacts, failure ledgers, token/cost summaries, a local worker commit, and a relay bundle. The scout command must route cost logging to a batch-specific path with `--cost-log-path`; the historical global cost log must not be edited in a worker branch. After both workers finish, one coordinator audits both relays, imports both result sets, updates the queue builder and coverage builder once, rebuilds all national outputs once, reconciles totals, validates, and creates one clean coordinator commit.

## Repository isolation and launch order

1. Commit the locked inputs, worker prompts, and this workflow in the coordinator repository.
2. Create exactly two worktrees or full repo copies from that same planning commit. Do not let both agents write in the original working directory.
3. Assign Worker 01 only `parallel_worker_01_ca25_scout_input_2026-07-21.csv` and Worker 02 only `parallel_worker_02_nj25_scout_input_2026-07-21.csv`.
4. Start exactly two agents concurrently. Each agent performs its own dry-run review and, only if authorized and passed, its own no-search smoke. A smoke call is live infrastructure use and requires explicit live authorization at execution time.
5. Each worker runs at most its exact locked 25-row state batch through `--live-backend direct-sdk`, `--n-parallels 1`, and zero SDK retries. No row substitution and no timeout retry are allowed inside Stage 1.
6. Each worker commits only batch-specific tracked outputs. Raw run directories and validation evidence go into that worker's relay whether or not `tmp/` is git-ignored.
7. Do not launch the coordinator merge until both workers have either completed or stopped and produced sanitized relays explaining their dispositions.
8. The coordinator audits scope first. It imports only valid worker outputs, then updates the global queue/coverage builders and rebuilds national accounting once.

Separate worktrees are preferable when both workers run on one machine because their git indexes and tracked files are isolated while they share the same base history. Separate full repo copies are acceptable when process isolation or filesystem contention is a concern. Merely using two output directories inside one working tree is not sufficient: the live scout also stages a run-specific candidate CSV under `docs/analysis`, and an incorrect command could touch a global log.

## Stage 1: exactly two parallel 25-row workers

Stage 1 consists of:

- Worker 01: CA25.2, 25 locked California municipal/place employers;
- Worker 02: NJ25, 25 locked New Jersey municipal/place employers.

Both must keep in-process concurrency at one. Stage 1 is a test of two-worker service concurrency, output isolation, relay quality, and coordinator merge behavior—not a test of maximum throughput.

Move to Stage 2 only if all of the following hold:

- both workers pass their independent synthetic direct-SDK smoke preflight;
- both live processes finish without connection collapse or the consecutive-connection-error stop guard truncating a batch;
- each worker and the pooled Stage 1 total have a parseable municipality-outcome rate of at least 90%; for a 25-row worker this means at least 23 parseable outcomes;
- parser/schema failures are at most 10% and do not reveal a systematic prompt or candidate-schema defect;
- no major normalized-candidate or queue-schema failure occurs;
- timeout/failure rates are manageable—normally no more than two non-collapse failures per worker, with no repeated proxy/API instability pattern;
- candidate volume can be normalized, reviewed, and merged without row explosion, duplicate-ID failure, or loss of municipality/run provenance;
- neither worker edits global queue/coverage/canonical files;
- the coordinator can import both relays and rebuild the queue and coverage exactly once without losing prior PA/TX/MA/NJ/IL/NY/CA rows; and
- the full validation suite passes after the coordinator merge.

The parseable-outcome denominator is the full locked batch, not merely the requests that returned before a stop. A stopped-before-request row therefore cannot make the success rate look better. Parseable empty `candidates=[]` output is a valid parseable discovery outcome; a connection-only response is not.

## Stage 2: three parallel 25-row workers

Stage 2 may begin only after the Stage 1 coordinator documents that every promotion condition passed. It uses exactly three isolated worker worktrees/copies, three disjoint locked 25-row batches, direct SDK, an independent smoke per worker, `--n-parallels 1`, batch-specific cost logs, zero uncontrolled retries, worker relays, and one later coordinator merge.

Move to Stage 3 only if:

- all three workers pass smoke and complete cleanly;
- each worker and the pooled 75-row stage retain at least a 90% parseable-outcome rate;
- no repeated API/proxy instability, connection-collapse pattern, or systemic malformed-output pattern appears;
- timeout and parser failures remain isolated and manageable;
- candidate volume remains operationally reviewable and all candidates retain unique batch/run/municipality provenance;
- no worker mutates shared global accounting or canonical data;
- the coordinator imports all three relays, preserves every previous state, and rebuilds queue/coverage once without conflict; and
- the full post-merge validation suite passes.

Any worker producing unexpectedly extreme candidate volume should be reviewed before promotion. Historical 25-row runs produced roughly 57-76 parsed rows; volume far outside that range is not automatically wrong, but more than about 150 rows from one worker is a practical trigger to inspect output shape and repeated-locator behavior before scaling.

## Stage 3: parallel 50-row workers

Stage 3 is permitted only after Stage 2 is proven. It must retain the direct-SDK backend, one synthetic no-search smoke per worker, `--n-parallels 1`, batch-specific output and cost logging, no source verification, no ingestion, no codification, worker relays, and one coordinator queue/coverage rebuild.

The current scout has `LIVE_HARD_CAP=25`; passing `--max-prompts 50` would be clipped to 25. Before Stage 3, a separately reviewed and committed code change must raise the hard cap to 50, update tests and documentation, and preserve all stop guards. That change must not be made merely by a worker prompt or silently during a live task.

A 50-row worker should still be one serial stream. The wall-clock gain comes from multiple isolated workers, not from setting a worker's internal concurrency above one.

## Stability metrics recorded by every worker and coordinator

Every worker relay must expose:

- smoke response text, response ID availability, success flag, token counts, elapsed time, and absence/presence of a connection error;
- locked municipality count and exact input SHA-256;
- requests attempted, calls stopped before request, backend-successful responses, nonempty responses, response IDs, parseable outcomes, valid empty outcomes, candidate-positive outcomes, and candidate rows;
- input, reasoning, output, and total tokens plus estimate-only cost status;
- timeout/connection failures, parser failures by failure type, missing locators, duplicate identifiers, and repeated-connection stop status;
- candidate counts by municipality and unit type;
- visible wrong-employer, wrong-unit, safety-as-non-safety, context, blocked, dead, and duplicate-risk leakage;
- all tracked files changed in the worker branch; and
- validation results.

The coordinator calculates per-worker and pooled parse rates, timeout rates, parser-failure rates, candidate counts, successful discovery-coverage increments, and queue increments. It also verifies that parseable empty results count as scout coverage while connection-only failures do not.

## Immediate stop conditions

A worker must stop and preserve sanitized evidence if any of these occurs:

- the dry-run checklist fails for any locked row;
- the synthetic no-search smoke fails, lacks response text/ID/output tokens, or reports a connection error;
- repeated connection errors arrive with no response IDs and no output tokens, including activation of the existing consecutive-error stop guard;
- parser failures exceed 10% of the locked batch or show a systematic schema/prompt defect;
- the input is not exactly the locked 25 rows or includes a covered, failure-only, prohibited-government, or wrong-state row;
- the worker command would edit/rebuild the national queue, national municipality/state/county coverage, or global cost log;
- the worker begins source verification, ingestion, `gabriel.codify`, public-records activity, URL opening/downloading, or claim-stage promotion;
- `data/contracts.csv`, `data/city_coverage.csv`, `corpus/`, another canonical file, or an unrelated tracked file changes unexpectedly;
- secrets or credential values would be printed or packaged; or
- the worker discovers it is sharing a writable repo/worktree with the other worker.

On a stop, do not substitute municipalities, retry timeout-only rows, or repair global accounting in the worker. Preserve the prompt preview, metadata, sanitized log, raw/failure artifacts already created, validation results that remain safe to run, and a relay explaining the stop. The coordinator decides later whether any parseable partial outcomes can be imported; failure-only municipalities never count as discovery coverage.

## Coordinator ownership boundary

Only the coordinator may:

- add the two completed worker candidate files to `SOURCE_SPECS`;
- add successful and failure-only municipality outcomes to the national coverage builder;
- merge batch-specific cost-log rows into the durable global cost log if desired;
- rebuild the national candidate queue and municipality/state/county discovery coverage;
- update national queue/coverage summaries and methodologies;
- update `PROGRESS.md` and the main handoff for the combined stage; and
- decide, from the documented metrics, whether Stage 1 qualifies for Stage 2.

This coordinator work remains scout-stage accounting. It must not open sources, verify candidates, ingest documents, alter canonical contract coverage, codify, or use worker leads as claim evidence.
