# Aggressive Parallel Scout Scaling Framework — 2026-07-23

## Current approved position

The 3 × 150 collection and its serial merge have passed. The user has
explicitly selected `aggressive_300` as the next round and accepted the likely
overshoot beyond approximately 2,000 covered municipalities. The prior 3 × 160
checkpoint-targeted package is preserved but superseded. This approval changes
the active planning choice; it does not collapse the live-collection, lane-audit,
and serial-accounting authorization boundaries described below.

## Architecture

Parallelism remains process-level. Each lane invokes the existing scout with
`--n-parallels 1`; the runner’s per-row compact prompt, deterministic hints,
adaptive pacing, SDK/httpx timeout, outer timeout, collapse stop, terminal timing,
and resume contracts are unchanged. Parallel collection ends at isolated lane
artifacts. A combined offline audit then recommends a disposition. National
accounting is a later, single, serial coordinator action.

## Scaling ladder

| Stage | Lanes | Rows/lane | Attempted | Start stagger | Gate |
|---|---:|---:|---:|---:|---|
| Completed baseline | 2 | 150 | 300 | 2–5 minutes planned | Merged successfully |
| `standard_150` | 3 | 150 | 450 | 4 minutes | Completed and merged |
| `aggressive_250` | 3 | 250 | 750 | 7 minutes by default; 6–8 allowed | Only after 3 × 150 collection and merge pass |
| `aggressive_300` | 3 | 300 | 900 | 8 minutes by default; 8–10 configurable | Active user-approved next plan |

Explicit lane, row, or stagger arguments may override a profile, but the planner
records every override in the manifest. More than three lanes fails closed. More
than 300 rows per lane fails unless the conspicuous
`--allow-oversized-lanes` override is supplied; no artifact prepared in this task
uses that override.

## Isolation contract

Every lane has:

- a unique `lane_id`, locked input CSV, SHA-256 hash, and deterministic start offset;
- no municipality-ID or nonblank Census-ID overlap with another lane;
- a fresh lane output directory;
- a unique cost log;
- a lane-local `candidate_exports/` directory supplied through
  `--candidate-export-dir`;
- a lane-specific dry run, live process, result review, and any later resume.

`parsed_candidates.csv` remains at the lane output root. The redundant timestamped
handoff is redirected to `candidate_exports/` and must be byte-identical. Legacy
serial commands that omit `--candidate-export-dir` retain the historical
`docs/analysis/` export behavior.

Lane processes must not rebuild queue/coverage, refresh yield/dashboard, change
final project documentation, commit, inspect remotes, or push.

## Audit and merge rules

The offline auditor supports one to three lanes and arbitrary reviewed lane sizes.
For every lane it checks the input hash/order, terminal timing, parseable/failure/
stopped/pending counts, candidate counts, lane-local export presence and byte
identity, elapsed time, effective rows/hour, outer timeouts, and adaptive backoff/
step-down events. It also checks completed-ID overlap and combined throughput.

- `merge_all_lanes`: every lane is `completed_merge_eligible`, lane-local exports
  match, and no completed ID overlaps.
- `merge_completed_lanes_only_with_user_approval`: at least one lane completed and
  every excluded lane has zero parseable rows. Explicit user approval is mandatory.
- `do_not_merge_until_resume_or_review`: any partial parseable lane, missing or
  ambiguous artifact, export mismatch, duplicate completed ID, or other uncertainty.

No auditor path writes queue, coverage, yield, dashboard, or priority files.

## Failure and preservation policy

- A lane-specific transport collapse stops that lane through existing rules; other
  lanes may continue unless failure is widespread or artifacts are endangered.
- Partial/failing output is preserved. Resume uses a fresh lane-specific directory
  and locked hash/identity lineage.
- Diagnostic and preflight probe outputs are always quarantined.
- Successful lane artifacts remain intact even when a sibling fails.
- Any completed-only merge is a scope change and requires the user’s approval.

## Advancement and checkpoint rules

Run 3 × 150 only because the completed 2 × 150 round and serial merge passed. Advance
to 3 × 250–300 only after the 3 × 150 live collection and its later serial merge
both pass. Those gates are now satisfied. Prefer 3 × 250 if the test shows elevated
timeouts, transport failures, backoff, or uneven lane completion. The user instead
approved 3 × 300 after reviewing the clean three-lane result and intentionally
accepted its expected checkpoint overshoot.

Broad discovery stops after the aggressive round's later serial accounting
reaches or exceeds approximately 2,000 scout-covered municipalities. The
project then pauses for verification, extraction, ingestion, source rating,
descriptive wage-growth-gap analysis, mechanism-correlation documentation, and
planned dashboard filtering. Regressions remain deferred.
