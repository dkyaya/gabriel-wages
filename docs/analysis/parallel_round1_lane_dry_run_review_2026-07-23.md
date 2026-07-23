# Parallel Round 1 Lane Dry-Run Review — 2026-07-23

Disposition: **PASS — both locked lanes are eligible for isolated live
collection because the readiness audit, stronger preflight, and both fresh
dry-runs passed.**

## Shared controls

Both dry-runs used:

- `--dry-run`
- `--state ALL`
- `--allow-mixed-states`
- `--prompt-mode compact`
- the committed deterministic search-hint file
- `--live-hard-cap 150`
- fixed fallback sleep 5 seconds
- adaptive sleep min/base/max/backoff 3/5/15/10 seconds
- adaptive stability/failure windows 25/2

Neither dry-run made an API, model, backend, hosted-search, or source-URL call.

## Lane 1

- Input rows: 150
- Prompts generated: 150
- Prompt mode: compact
- Search hints matched: 150/150
- Mixed states allowed: true
- Live hard cap: 150
- Adaptive sleep: true
- `row_timing.csv`: present with 150 rows
- Timing disposition: 150 `dry_run_planned` / `not_attempted`
- `live_attempted`: false
- `backend_call_returned`: false
- Execution status: `dry_run_completed`

## Lane 2

- Input rows: 150
- Prompts generated: 150
- Prompt mode: compact
- Search hints matched: 150/150
- Mixed states allowed: true
- Live hard cap: 150
- Adaptive sleep: true
- `row_timing.csv`: present with 150 rows
- Timing disposition: 150 `dry_run_planned` / `not_attempted`
- `live_attempted`: false
- `backend_call_returned`: false
- Execution status: `dry_run_completed`

## Prompt-level audit

The preview was split into 150 prompt blocks per lane and matched in locked
input order. All 300 blocks contain:

- municipality and state;
- locked internal municipality ID;
- exact government name and Census government ID;
- county geography context;
- expected units/source targets;
- the five row-specific deterministic query hints;
- row-specific verification cautions;
- exact-employer and no-substitution controls;
- strict safety versus ordinary non-safety unit controls;
- no-candidate guidance;
- duplicate suppression;
- blocked-versus-dead separation;
- unverified scout-stage handling; and
- prohibition on public-records requests.

Prompt identity/control failures: 0 for Lane 1 and 0 for Lane 2.

The diagnostic preflight probe remains quarantined. No national accounting,
verification, ingestion, codification, dashboard, yield, wage-gap, or causal
analysis action occurred during either dry-run.
