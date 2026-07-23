# POST-PI-PARALLEL-ROUND1-2026-07-23 — Lane Live Command Preview

**Preview only. Do not execute without separate live authorization.**

Before launching either lane, run the stronger preflight gate and require a complete
pass, including an explicitly authorized one-row production probe. Quarantine all
probe outputs from official accounting. Generated commands use the exact locked 150-row cap.

Launch Lane 1 first. Wait 2–5 minutes, confirm it has not shown an immediate
widespread transport or lifecycle failure, then launch Lane 2. Do not run more lanes
than the round authorization permits. Stop all lanes if a widespread transport
failure, systematic parser failure, artifact loss, protected-file mutation, or
secret exposure appears.

Each command remains internally serialized with `--n-parallels 1`, uses compact
prompts, exact hints, adaptive pacing, the SDK plus outer 90-second deadline, and a
unique cost log. Lane processes must not rebuild queue/coverage/yield/dashboard,
edit final project docs, or commit. Preserve every artifact.

## Lane 1

Fresh output:
`tmp/parallel_scout_rounds/POST-PI-PARALLEL-ROUND1-2026-07-23/lane_1_live_direct_sdk_attempt1`

```bash
python scripts/gabriel_state_source_scout.py \
  --live \
  --live-backend direct-sdk \
  --state ALL \
  --allow-mixed-states \
  --municipalities-csv docs/analysis/parallel_scout_rounds/POST-PI-PARALLEL-ROUND1-2026-07-23/lane_1_input.csv \
  --output-dir tmp/parallel_scout_rounds/POST-PI-PARALLEL-ROUND1-2026-07-23/lane_1_live_direct_sdk_attempt1 \
  --prompt-mode compact \
  --search-hints-csv docs/analysis/municipality_search_hints_2026-07-22.csv \
  --model gpt-5.4-nano \
  --search-context-size low \
  --max-prompts 150 \
  --live-hard-cap 150 \
  --n-parallels 1 \
  --sleep-between-prompts 5 \
  --adaptive-sleep \
  --adaptive-sleep-min 3 \
  --adaptive-sleep-base 5 \
  --adaptive-sleep-max 15 \
  --adaptive-sleep-backoff 10 \
  --adaptive-sleep-stability-window 25 \
  --adaptive-sleep-failure-window 2 \
  --timeout 90 \
  --direct-sdk-max-retries 0 \
  --cost-log-path tmp/parallel_scout_rounds/POST-PI-PARALLEL-ROUND1-2026-07-23/lane_1_live_direct_sdk_attempt1/batch_cost_log.csv
```
## Lane 2

Fresh output:
`tmp/parallel_scout_rounds/POST-PI-PARALLEL-ROUND1-2026-07-23/lane_2_live_direct_sdk_attempt1`

```bash
python scripts/gabriel_state_source_scout.py \
  --live \
  --live-backend direct-sdk \
  --state ALL \
  --allow-mixed-states \
  --municipalities-csv docs/analysis/parallel_scout_rounds/POST-PI-PARALLEL-ROUND1-2026-07-23/lane_2_input.csv \
  --output-dir tmp/parallel_scout_rounds/POST-PI-PARALLEL-ROUND1-2026-07-23/lane_2_live_direct_sdk_attempt1 \
  --prompt-mode compact \
  --search-hints-csv docs/analysis/municipality_search_hints_2026-07-22.csv \
  --model gpt-5.4-nano \
  --search-context-size low \
  --max-prompts 150 \
  --live-hard-cap 150 \
  --n-parallels 1 \
  --sleep-between-prompts 5 \
  --adaptive-sleep \
  --adaptive-sleep-min 3 \
  --adaptive-sleep-base 5 \
  --adaptive-sleep-max 15 \
  --adaptive-sleep-backoff 10 \
  --adaptive-sleep-stability-window 25 \
  --adaptive-sleep-failure-window 2 \
  --timeout 90 \
  --direct-sdk-max-retries 0 \
  --cost-log-path tmp/parallel_scout_rounds/POST-PI-PARALLEL-ROUND1-2026-07-23/lane_2_live_direct_sdk_attempt1/batch_cost_log.csv
```

## After processes terminate

Run the offline lane auditor against `parallel_round_manifest.json`. Do not run any
national builder or merge command from this file.
