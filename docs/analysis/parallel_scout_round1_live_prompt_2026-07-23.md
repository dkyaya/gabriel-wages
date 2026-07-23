# Future Coordinator Prompt — First Two-Lane Parallel Scout Round

Use only under a separately authorized live task. This document does not authorize a live call now.

---

Work only in the main coordinator repository:

`/Users/joachimjohnson/Documents/RA_2026/Pol_Fire/gabriel-wages`

Run the first coordinator-controlled parallel scout round as two isolated, internally serialized 150-row direct-SDK lane processes. Do not inspect remotes, push, fetch, pull, verify URLs, ingest, codify, calculate wage gaps, make causal claims, or run regressions.

## Locked round

Round manifest:

`docs/analysis/parallel_scout_rounds/POST-PI-PARALLEL-ROUND1-2026-07-23/parallel_round_manifest.json`

Lane 1:

- Input: `docs/analysis/parallel_scout_rounds/POST-PI-PARALLEL-ROUND1-2026-07-23/lane_1_input.csv`
- Rows: 150
- SHA-256: `56e592291f1dbac83836acddcf0065df40141b51f9e93bfb548a040f52b8e700`
- Lineage: byte-identical to the uncompleted Post-PI Wave 1 locked input.

Lane 2:

- Input: `docs/analysis/parallel_scout_rounds/POST-PI-PARALLEL-ROUND1-2026-07-23/lane_2_input.csv`
- Rows: 150
- SHA-256: `f381ce60c362a78561250b08b66ba32822fc583b86892b04fbb24b3a6a7b998d`

Require the exact hashes, 300 unique municipality IDs, 300 unique Census IDs, zero cross-lane overlap, current ordinary eligibility, no retries/failure-only/covered/canonical rows, and 300/300 exact hint sets. If any row is ineligible, stop without substitution and regenerate the offline plan.

Preserve the stopped `bd5e259` output as quarantined non-evidence. Do not resume from or write into it.

## Offline gates

1. Require clean tracked state and record unrelated untracked files.
2. Compile and run the parallel-lane, direct-SDK, and prompt test suites.
3. Run one fresh 150-row dry run per lane into distinct dry-run directories. Require exact identity/order, compact prompts, five hints, strict employer/unit/source/stage controls, adaptive metadata, 150 dry timing rows, and no backend call.
4. Run the stronger preflight plan in a fresh directory:

   ```bash
   python scripts/run_scout_preflight_gate.py \
     --plan-only \
     --output-dir tmp/parallel_scout_rounds/POST-PI-PARALLEL-ROUND1-2026-07-23/preflight_plan_attempt1 \
     --model gpt-5.4-nano \
     --timeout 30 \
     --search-context-size low \
     --max-calls 4
   ```

5. Create `tmp/parallel_scout_rounds/POST-PI-PARALLEL-ROUND1-2026-07-23/preflight_one_row_probe_input_attempt1.csv` as an exact header plus first data row from Lane 1. Under this separate live authorization, run exactly one stronger executed preflight:

   ```bash
   python scripts/run_scout_preflight_gate.py \
     --output-dir tmp/parallel_scout_rounds/POST-PI-PARALLEL-ROUND1-2026-07-23/preflight_live_attempt1 \
     --model gpt-5.4-nano \
     --timeout 30 \
     --search-context-size low \
     --max-calls 4 \
     --include-one-row-probe \
     --probe-input-csv tmp/parallel_scout_rounds/POST-PI-PARALLEL-ROUND1-2026-07-23/preflight_one_row_probe_input_attempt1.csv \
     --probe-output-dir tmp/parallel_scout_rounds/POST-PI-PARALLEL-ROUND1-2026-07-23/preflight_one_row_probe_output_attempt1
   ```

   Require no-search, both hosted-search controls, and the one-row production probe to pass. Quarantine every probe artifact from official accounting.

6. Stop before lane launch unless every gate passes with no secret exposure or widespread transport instability.

## Lane collection controls

Use the exact lane commands in:

`docs/analysis/parallel_scout_rounds/POST-PI-PARALLEL-ROUND1-2026-07-23/lane_live_commands.md`

Both lanes must use:

- `--live --live-backend direct-sdk`;
- state `ALL` with mixed-state authorization;
- exact max/cap 150;
- `--n-parallels 1` inside each lane;
- compact prompts;
- deterministic hints;
- adaptive min/base/max/backoff `3/5/15/10`;
- stability/failure windows `25/2`;
- 90-second SDK plus runner-level outer timeout;
- zero SDK retries;
- unique output and cost-log paths.

Create a lane-specific lineage note before each run. Launch Lane 1 first. Wait 2–5 minutes and confirm no immediate widespread transport/lifecycle failure before launching Lane 2. Do not launch more than two lanes.

Lane processes must write only to their own output directories. During collection they must not:

- rebuild queue or coverage;
- refresh yield or dashboard JSON;
- refresh priority tiers;
- update final project documentation;
- commit;
- promote candidates;
- verify, ingest, or codify.

Stop all lanes if a widespread transport pattern, systematic parser failure, lifecycle/artifact loss, protected-file mutation, or secret exposure appears. Preserve partial artifacts. Never rerun into an existing directory.

## Post-lane audit

After both processes terminate, run only:

```bash
python scripts/audit_parallel_scout_lanes.py \
  --manifest docs/analysis/parallel_scout_rounds/POST-PI-PARALLEL-ROUND1-2026-07-23/parallel_round_manifest.json \
  --output-dir tmp/parallel_scout_rounds/POST-PI-PARALLEL-ROUND1-2026-07-23/post_lane_audit
```

Review each classification, hash, parseable/failure/stopped/pending/candidate count, and completed-ID overlap. Preserve the three audit outputs.

## Stop before shared accounting

Do not rebuild queue, coverage, yield, dashboard, project phase, or priority files in this task unless the user has explicitly extended authorization to the separate serial-merge phase.

- If `merge_all_lanes`, report readiness for the serial merge and stop.
- If `merge_completed_lanes_only_with_user_approval`, request explicit approval and stop.
- If `do_not_merge_until_resume_or_review`, preserve all artifacts and report the required lane-specific next action.

Do not push or inspect remotes.

---
