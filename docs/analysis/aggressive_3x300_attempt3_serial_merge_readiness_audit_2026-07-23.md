# Aggressive 3×300 Attempt 3 Serial Merge Readiness Audit

Date: 2026-07-23/24  
Round: `POST-PI-AGGRESSIVE-ROUND-3X300-2026-07-23`  
Disposition: **PASS — one coordinator-controlled serial accounting rebuild may proceed**

## Repository and accounting boundary

Work began at `27d3cd222517a9c54a7c61d7af3f1d5185d1bd97` on `main`.
The required commits `27d3cd2`, `18c3415`, `dcf3cd5`, `663ffaf`,
`8b653b2`, and `3a7d762` are ancestors of the current HEAD. The tracked
worktree was clean. The unrelated untracked root `package-lock.json` was
reported and left untouched.

Before this merge, canonical accounting was unchanged from the Round 2 merge:

- 3,347 URL-bearing candidate-queue rows;
- 1,537 successfully scout-covered municipalities;
- 1,267 candidate-positive municipalities;
- 270 parseable-empty municipalities; and
- 27 failure-only municipalities.

No Attempt 3 candidate, coverage, yield, dashboard, project-phase, or priority
builder had run. The diagnostic Newport probe is not a registered builder
input. Attempt 1 (`dcf3cd5`) and Attempt 2 (`18c3415`) remain separate,
quarantined, non-mergeable lineages and are not registered builder inputs.

## Files used

- `AGENTS.md`, `PROGRESS.md`, and
  `docs/analysis/chatgpt_handoff_latest.md`
- the five Attempt 3 readiness/preflight/dry-run/result/validation documents
- the Attempt 1 and Attempt 2 result and no-accounting-merge documents
- the locked planning manifest, combined input audit, three lane inputs, and
  three lane input audits under
  `docs/analysis/parallel_scout_rounds/POST-PI-AGGRESSIVE-ROUND-3X300-2026-07-23/`
- the Attempt 3 manifest under
  `tmp/parallel_scout_rounds/POST-PI-AGGRESSIVE-ROUND-3X300-2026-07-23/`
- each Attempt 3 lane's `run_metadata.json`, `parsed_candidates.csv`,
  `failed_parses.csv`, `row_timing.csv`, `raw_outputs.csv`, and
  `candidate_exports/`
- the prior and fresh Attempt 3 lane-audit artifacts
- current national queue, municipality/state/county coverage, yield,
  dashboard/project-phase, and priority artifacts
- the queue, coverage, yield, dashboard, priority, lane-audit, and lane-planning
  builders named in the task
- the Post-PI 2,000-municipality strategy and descriptive-analysis roadmap

## Fresh lane audit

The committed planning manifest points to Attempt 1 roots. The exact
Attempt 3 manifest used by the successful collection audit was therefore
reused:

```text
python scripts/audit_parallel_scout_lanes.py \
  --manifest tmp/parallel_scout_rounds/POST-PI-AGGRESSIVE-ROUND-3X300-2026-07-23/parallel_round_manifest_attempt3.json \
  --output-dir tmp/parallel_scout_rounds/POST-PI-AGGRESSIVE-ROUND-3X300-2026-07-23/lane_audit_for_merge_attempt3_2026-07-23
```

The auditor CLI does not need a separate lane-root override because the
Attempt 3 manifest contains the exact three Attempt 3 roots.

## Lane gates

| Gate | Lane 1 | Lane 2 | Lane 3 |
|---|---:|---:|---:|
| Expected/attempted rows | 300 / 300 | 300 / 300 | 300 / 300 |
| Parseable rows | 299 | 300 | 300 |
| Candidate-positive municipalities | 214 | 200 | 177 |
| Parseable-empty municipalities | 85 | 100 | 123 |
| Failure-only rows | 1 | 0 | 0 |
| Stopped before request | 0 | 0 | 0 |
| Pending timing rows | 0 | 0 | 0 |
| Candidate lead rows | 548 | 456 | 385 |
| Classification | `completed_merge_eligible` | `completed_merge_eligible` | `completed_merge_eligible` |
| Lane-local export byte match | yes | yes | yes |

Locked input hashes match:

- Lane 1:
  `2965bd65a3f5c6fe816f52c3e9f2ce657cd9ff472db6733233bcaa4ad081fee1`
- Lane 2:
  `6057e1c71b74e0342127cad32a183c2b310af704ea5ebab61e5eb7483b3896a7`
- Lane 3:
  `9934026f076a978957de5ae5767eed2ff236646d384285585aeecbddcc50843a`

The lane-local candidate-export pairs are byte-identical:

- Lane 1:
  `78e889b68e12d7645657882b8f59e54ed490fe80fe9bd74aeaed15cbb0272e19`
- Lane 2:
  `ff4c413eeaa2cfac60b5aae18a1b1e0f89eddaf37bf9b2ff5c9d1b36291b83d7`
- Lane 3:
  `f60435fe0254a3bac7cbbf0028b10fe5c41983aff2a5700c45df046f12547254`

No Attempt 3 timestamped candidate export exists under shared
`docs/analysis/`. Completed municipality-ID overlap is zero.

## Failure-only boundary

Shelby, Ohio (`cog_2025_209091`) is the sole Attempt 3 failure-only row.
Its `outer_timeout` has no successful parseable outcome and it must remain
outside successful scout coverage. The other 899 municipalities have terminal
parseable outcomes.

## Decision

Fresh recommendation: **`merge_all_lanes`**.

The merge may preserve the audited candidate exports and state-usage summaries
as durable local artifacts, register only the three Attempt 3 batches in the
unchanged deterministic accounting methodology, and invoke the national queue
and coverage sequence exactly once. This is an accounting promotion of
unverified scout outcomes. It does not verify a URL, ingest or codify a source,
calculate a wage gap, make a causal claim, or authorize another discovery
round.
