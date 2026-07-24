# Aggressive 3×300 Attempt 2 Readiness Audit

Date: 2026-07-23/24  
Round: `POST-PI-AGGRESSIVE-ROUND-3X300-2026-07-23`

## Repository and lineage gate

- Starting commit: `dcf3cd5f0ff77c746bf6b27c6e7561d9b8ccb1f8`.
- Branch: `main`.
- Required ancestry confirmed locally: `dcf3cd5`, `663ffaf`, `8b653b2`, `d015800`, and `3a7d762`.
- The tracked worktree was clean. The unrelated untracked root `package-lock.json` was reported and left untouched.
- No remote was inspected or changed.

## Files used

- `AGENTS.md`
- `PROGRESS.md`
- `docs/analysis/chatgpt_handoff_latest.md`
- aggressive preparation, dashboard-status, supersession, live-prompt, and serial-merge-prompt documents dated 2026-07-23
- the manifest, combined audit, three locked inputs/audits, live commands, and merge handoff under `docs/analysis/parallel_scout_rounds/POST-PI-AGGRESSIVE-ROUND-3X300-2026-07-23/`
- `docs/analysis/aggressive_3x300_live_collection_result_review_2026-07-23.md`
- `docs/analysis/aggressive_3x300_no_accounting_merge_note_2026-07-23.md`
- `docs/analysis/aggressive_3x300_preflight_gate_review_2026-07-23.md`
- Attempt 1 Lane 1 `run_metadata.json`, `row_timing.csv`, and `failed_parses.csv`
- Attempt 1 `post_lane_audit_attempt1/parallel_lane_audit_summary.json` and `merge_recommendation.md`
- current national priority, coverage, canonical, failure/retry, and deterministic-hint artifacts referenced by the committed planner
- `scripts/prepare_parallel_scout_lanes.py`
- `scripts/audit_parallel_scout_lanes.py`
- `scripts/gabriel_state_source_scout.py`
- `scripts/run_scout_preflight_gate.py`
- `docs/analysis/direct_sdk_outer_timeout_fix_summary_2026-07-23.md`
- `docs/analysis/scout_speed_stability_implementation_summary_2026-07-22.md`
- Post-PI strategy and current project/parallel dashboard JSON.

## Attempt 1 quarantine

Attempt 1 is non-mergeable:

- Lane 1 made two requests, both terminal no-ID/no-text/no-token connection failures.
- Lane 1 produced zero parseable outcomes and zero candidate rows.
- Its remaining 298 rows are `stopped_before_request`.
- Lane 2 and Lane 3 were never launched.
- The offline recommendation is `do_not_merge_until_resume_or_review`.
- No national queue, coverage, yield, dashboard, project-phase, or priority builder ran.

Attempt 1 and its diagnostic Newport probe remain quarantined and are not official municipality source outcomes. A fresh attempt is appropriate because there is no parseable Lane 1 completion to resume.

## Locked inputs and current eligibility

| Lane | Rows | SHA-256 | Current eligibility |
|---|---:|---|---|
| 1 | 300 | `2965bd65a3f5c6fe816f52c3e9f2ce657cd9ff472db6733233bcaa4ad081fee1` | passed |
| 2 | 300 | `6057e1c71b74e0342127cad32a183c2b310af704ea5ebab61e5eb7483b3896a7` | passed |
| 3 | 300 | `9934026f076a978957de5ae5767eed2ff236646d384285585aeecbddcc50843a` | passed |

Current reconciliation confirms:

- 900 rows and exactly 300 rows per lane;
- 900 unique municipality IDs and 900 unique Census government IDs;
- zero cross-lane municipality or Census overlap;
- zero covered, canonical, retry, or failure-only rows;
- exact five-hint coverage for 900/900 rows;
- Tier 1: 606; Tier 2: 294;
- lane-local candidate export support; and
- direct-SDK outer per-row timeout support.

No row was substituted.

## Fresh attempt 2 roots

- `tmp/parallel_scout_rounds/POST-PI-AGGRESSIVE-ROUND-3X300-2026-07-23/lane_1_live_direct_sdk_attempt2`
- `tmp/parallel_scout_rounds/POST-PI-AGGRESSIVE-ROUND-3X300-2026-07-23/lane_2_live_direct_sdk_attempt2`
- `tmp/parallel_scout_rounds/POST-PI-AGGRESSIVE-ROUND-3X300-2026-07-23/lane_3_live_direct_sdk_attempt2`

All preflight, probe, dry-run, live, and post-lane-audit Attempt 2 paths were absent before work.

## Staged health gate

The coordinator will poll each active lane’s checkpointed `row_timing.csv` every 30–60 seconds. A later lane is authorized only after the preceding lane has at least ten terminal rows with `parse_status=parseable`, has not terminated, and does not show an active two-consecutive no-response transport-collapse pattern. If Lane 1 stops before ten parseable rows, Lanes 2–3 remain suppressed. If Lane 2 stops before ten, Lane 3 remains suppressed while a healthy Lane 1 may continue.

No more than three lanes may launch. No resume and no serial accounting merge are authorized in this task.

