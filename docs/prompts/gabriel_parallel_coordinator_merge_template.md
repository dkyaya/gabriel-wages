# Gabriel Parallel Scout Coordinator Merge Template

Use this template only in the main repository after every assigned worker lane has supplied a sanitized relay. First determine whether every relay is complete and merge-eligible. A stopped or incomplete relay may be diagnosed, but it does not authorize a partial accounting rebuild. This is a local accounting merge, not a scout or source-research task.

Use Routine / GPT-5.6 Terra for relay packaging and deterministic queue/coverage rebuilds. Use Heavy / GPT-5.6 Sol for scope disputes, debugging, schema changes, selection/methodology decisions, or prompt/filter-contract changes. Use Low / GPT-5.4 only for tiny doc cleanup.

## Inputs and boundary

| Parameter | Value |
| --- | --- |
| Planning commit | `{{PLANNING_COMMIT}}` |
| Stage | `{{PARALLEL_STAGE}}` |
| Worker relays | `{{WORKER_RELAY_PATHS}}` |
| Candidate queue builder | `{{QUEUE_BUILDER}}` |
| Coverage builder | `{{COVERAGE_BUILDER}}` |

Read project instructions and the relevant workflow before acting. Record the initial local commit. Do not inspect, configure, create, validate, or modify remotes; do not push. Work in the main repository only.

## Audit every relay before importing

For each worker relay, inspect its status/log/diff summaries, locked input, dry review, smoke record, run metadata, failures, candidates, review, cost data, validation output, and credential scan. Confirm that the worker:

- used a separate worktree/repo copy and only its locked input;
- ran and passed dry review before smoke, and used the exact one-request smoke contract;
- used direct SDK, `--live-backend direct-sdk`, `--n-parallels 1`, 15-second spacing, zero retries, and a batch-specific cost log for any live run;
- made no substitutions or failure retries and stopped safely when required;
- kept all candidates unverified and did not open/download/verify sources;
- did not ingest, codify, issue public-records requests, promote claim evidence, or edit canonical data/corpus; and
- did not alter global queue/coverage, global builders/summaries, durable cost log, progress/handoff, or expose credentials.

Also require a unique attempt label and fresh output paths, a Gate 0 readiness note, the exact interpreter/package record, command launch/exit evidence, and a protected-file before/after comparison.

While parallel live use is paused, also require evidence that workers obeyed the serialized recovery protocol: Gate 0/dry runs may overlap, but smoke/live intervals may not; each worker must record its coordinator live-lane grant; and the next smoke must begin at least five minutes after the prior worker's lane was released. Overlapping smoke/live timestamps are a hard scope rejection, not a reason to reinterpret failures.

## Hard relay rejection rules

Reject the relay as a Stage outcome and do not start the global rebuild if any of the following is true:

- it is a preflight-stop relay because dry review or smoke failed;
- the live output directory contains only `prompt_preview.md`;
- `run_metadata.json` is absent, invalid, or remains at `execution_status=live_started` without completion evidence;
- `raw_outputs.csv` is absent;
- `parsed_candidates.csv` or equivalent parsed-output evidence is absent;
- the failure ledger is absent when failures or incomplete parsing are claimed;
- sanitized command stdout/stderr and exit-code disposition are both absent;
- no parseable model output exists for any municipality; or
- the review cannot reconcile artifact-supported attempted, response, parseable, empty, candidate, and failure counts.
- `execution_status=completed_no_parseable_outcome`, or the process exits zero despite zero parseable research outcomes under a pre-hardening runner;
- the relay lacks live-lane grant/release evidence or shows overlapping API intervals while serialized recovery is required.

A header-only `parsed_candidates.csv` may be valid only when `raw_outputs.csv` contains one or more successful, parseable `candidates=[]` model outputs. Zero candidate rows are not by themselves a rejection; zero parseable model outputs are. Synthetic smoke artifacts never substitute for research-batch raw/parsed evidence.

If any assigned worker is rejected under these rules, Stage 1/2/3 is not complete. Preserve and diagnose all relays, leave national queue/coverage unchanged, and recommend a hardened same-stage retry under separate authorization. Do not merge the other worker merely because its relay is complete.

If scope was violated, do not blindly cherry-pick. Preserve the relay and document the exception. An unexpected canonical edit is a stop condition. Any proposal to import independently auditable partial data after another worker failed requires separate explicit authorization; the default parallel-stage rule is no partial merge.

## Import and classify outcomes

Import URL-bearing, normalized, unverified candidates and batch review files without overwriting other workers' artifacts. Record hashes if copying from a relay. Never import a worker's stale global output.

Only after every assigned relay passes the hard eligibility audit, classify each municipality from raw evidence:

- `scouted_with_candidates`: successful parsed result with one or more candidates;
- `scouted_no_candidates`: successful parsed empty candidate list;
- `scout_attempt_failed_connection`: connection/transport/timeout with no later valid response;
- stopped-before-request or uncalled: separately logged, not discovery-covered.

Do not count connection-only, malformed, absent, prompt-only, or stopped outcomes as coverage. A parseable empty result is coverage, not proof that no source exists. Never infer 25 connection failures from a prompt-only directory; without row-level evidence the batch is simply incomplete and unclassifiable.

## One global rebuild, after all imports

The steps below are forbidden until all relays pass the eligibility audit.

1. Add each valid normalized candidate file and exact run metadata to the queue builder's source specifications, preserving all prior rows.
2. Add successful and failure-only outcomes to the coverage builder, preserving all historical status and attempt accounting.
3. Merge batch-specific cost records into the durable log once only if that log remains canonical; retain estimate-only/actual-cost caveats.
4. Rebuild the national candidate queue once.
5. Rebuild national municipality/state/county scout coverage once, without source downloads.
6. Update queue/coverage methodology and summaries with worker and pooled results.

No verification, ingestion, codify, canonical coverage edit, or candidate claim use occurs in this merge.

## Report and validation

Report per worker and pooled: live-lane grant/release and non-overlap; smoke result/latency; locked, attempted, stopped, successful, nonempty, response-ID, parseable, parseable-empty, candidate-positive, and candidate-row counts; parseable and failure rates; parser failures; leakage; missing locators/duplicates; tokens/cost caveats; queue/coverage increments; and confirmation that all prior rows remain. A clean serialized recovery merge does not by itself prove parallel-live stability or authorize Stage 2.

Run at least:

```bash
python scripts/validate.py
python ingest/test_pipeline.py
python ingest/audit_coverage.py
```

Run available project-specific queue/coverage reconciliation checks too. Update `PROGRESS.md` and the main handoff with the combined result and scaling decision. Create one clean local coordinator commit, then package a sanitized relay ZIP with imported artifacts, rebuilt outputs, validation evidence, git summaries, changed-file list, and a next-task note. Do not push.
