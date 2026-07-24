# Parallel Round 2 3×150 Serial Merge Readiness Audit

Date: 2026-07-23

Round: `POST-PI-PARALLEL-ROUND2-3X150-2026-07-23`

## Disposition

**PASS — the three completed lanes may proceed to one coordinator-controlled
serial accounting rebuild.**

The repository started at
`4f9c865e9f6e1416643c809bcec67623039ee931` on `main`. Required ancestry
`4f9c865`, `d015800`, `c4cf7d0`, `4ee7015`, and `3a7d762` is present. The
tracked worktree was clean; the unrelated untracked root `package-lock.json`
was left untouched.

## Files used

- `AGENTS.md`
- `PROGRESS.md`
- `docs/analysis/chatgpt_handoff_latest.md`
- the five Round 2 collection readiness/result/validation documents
- the locked manifest, combined audit, three lane inputs, and three lane input
  audits under
  `docs/analysis/parallel_scout_rounds/POST-PI-PARALLEL-ROUND2-3X150-2026-07-23/`
- each lane's `run_metadata.json`, `parsed_candidates.csv`,
  `failed_parses.csv`, `row_timing.csv`, `raw_outputs.csv`, and
  `candidate_exports/` directory
- the prior `post_lane_audit_attempt1` artifacts
- current national queue, municipality/state/county coverage, project-phase,
  yield, dashboard, and priority artifacts
- the canonical queue, coverage, yield, dashboard, priority, lane-audit, and
  lane-planning scripts listed in the task

## Fresh auditor

The implemented CLI does not accept `--lane-output-root`; it resolves each
lane output from the locked manifest. The exact command used was:

```text
python scripts/audit_parallel_scout_lanes.py \
  --manifest docs/analysis/parallel_scout_rounds/POST-PI-PARALLEL-ROUND2-3X150-2026-07-23/parallel_round_manifest.json \
  --output-dir tmp/parallel_scout_rounds/POST-PI-PARALLEL-ROUND2-3X150-2026-07-23/lane_audit_for_merge_2026-07-23_attempt1
```

Fresh output:

`tmp/parallel_scout_rounds/POST-PI-PARALLEL-ROUND2-3X150-2026-07-23/lane_audit_for_merge_2026-07-23_attempt1/`

## Lane gates

| Gate | Lane 1 | Lane 2 | Lane 3 |
|---|---:|---:|---:|
| Expected rows | 150 | 150 | 150 |
| Parseable | 148 | 149 | 149 |
| Failure-only | 2 | 1 | 1 |
| Stopped before request | 0 | 0 | 0 |
| Pending timing rows | 0 | 0 | 0 |
| Candidate lead rows | 335 | 343 | 307 |
| Classification | `completed_merge_eligible` | `completed_merge_eligible` | `completed_merge_eligible` |
| Export byte match | yes | yes | yes |

Locked input hashes match:

- Lane 1:
  `320f4915a1aa487e791f67a31826572ac275edf5d4b87ecb99eec4b26279d86a`
- Lane 2:
  `e06f9706d69bce72cabac6f57c8581d16651d0b00ecec5752787edda5fc5500a`
- Lane 3:
  `501e36ff504ec2d5e3a1126eb1315db6fb31bbe5852c2be2590794661dd50665`

Lane-local candidate exports are byte-identical to the corresponding
`parsed_candidates.csv` files:

- Lane 1 pair:
  `081dea566fcae6e3716e11b5b7fd3b258f1d7654d77cdfdc20059434186bc59e`
- Lane 2 pair:
  `411254ec184354e312cd54c7290e440fdfb7075c26a7e21084c32da8d78020fa`
- Lane 3 pair:
  `50f0a26107a08855c64a2ac6f351e9cfca303fdfab9fc63732c4fbf32ee6982c`

Completed municipality-ID overlap is zero. No Round 2 timestamped candidate
export exists in shared `docs/analysis/`; future deterministic rebuilding will
use explicitly named durable copies made during this authorized serial merge.

## Failure boundary

The following rows remain failure-only and outside successful scout coverage:

- Twinsburg, OH (`cog_2025_194843`) —
  `empty_response_no_response_id`
- Oakland Park, FL (`cog_2025_189806`) —
  `empty_response_no_response_id`
- Hollister, CA (`cog_2025_161242`) — `outer_timeout`
- College Place, WA (`cog_2025_176888`) —
  `empty_response_no_response_id`

The Wausau diagnostic probe remains under its quarantine path and is not a
builder input. The stopped `bd5e259` output remains quarantined and is not a
builder input. Before this task, tracked queue, coverage, yield, dashboard, and
priority artifacts matched `4f9c865`, confirming no earlier accounting merge
from these lanes.

## Merge recommendation and boundary

Fresh recommendation: **`merge_all_lanes`**.

The merge may proceed by preserving the three audited candidate exports and
lane state-usage summaries as durable local artifacts, registering the three
successful batches and four terminal failures in the unchanged deterministic
accounting methodology, and invoking the national queue and coverage builder
sequence exactly once. This does not verify, ingest, codify, promote, or use
the candidate rows as claim evidence.
