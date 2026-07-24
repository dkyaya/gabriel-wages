# POST-PI-AGGRESSIVE-ROUND-3X300-2026-07-23 — Lane Live Command Preview

**Preview only. Do not execute without separate live authorization.**

Before launching any lane, run the stronger preflight gate and require a complete
pass, including an explicitly authorized one-row production probe. Quarantine all
probe outputs from official accounting. Generated commands use the requested locked 300-row cap; this nonstandard size requires separate review before live authorization.

Launch lanes in numeric order. Wait exactly 480 seconds
(8 minutes) between starts, confirming the active lanes have not
shown an immediate widespread transport or lifecycle failure before starting the
next lane. Do not run more lanes than the round authorization permits. Stop all
lanes if a widespread transport failure, systematic parser failure, artifact loss,
protected-file mutation, or secret exposure appears.

Each command remains internally serialized with `--n-parallels 1`, uses compact
prompts, exact hints, adaptive pacing, the SDK plus outer 90-second deadline, and a
unique cost log. Timestamped candidate exports are redirected to each lane's
`candidate_exports/` directory; `parsed_candidates.csv` remains at the lane output
root. Lane processes must not rebuild queue/coverage/yield/dashboard, edit final
project docs, or commit. Preserve every artifact.

## Lane 1

Fresh output:
`tmp/parallel_scout_rounds/POST-PI-AGGRESSIVE-ROUND-3X300-2026-07-23/lane_1_live_direct_sdk_attempt1`

```bash
python scripts/gabriel_state_source_scout.py \
  --live \
  --live-backend direct-sdk \
  --state ALL \
  --allow-mixed-states \
  --municipalities-csv docs/analysis/parallel_scout_rounds/POST-PI-AGGRESSIVE-ROUND-3X300-2026-07-23/lane_1_input.csv \
  --output-dir tmp/parallel_scout_rounds/POST-PI-AGGRESSIVE-ROUND-3X300-2026-07-23/lane_1_live_direct_sdk_attempt1 \
  --prompt-mode compact \
  --search-hints-csv docs/analysis/municipality_search_hints_2026-07-22.csv \
  --model gpt-5.4-nano \
  --search-context-size low \
  --max-prompts 300 \
  --live-hard-cap 300 \
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
  --cost-log-path tmp/parallel_scout_rounds/POST-PI-AGGRESSIVE-ROUND-3X300-2026-07-23/lane_1_live_direct_sdk_attempt1/batch_cost_log.csv \
  --candidate-export-dir tmp/parallel_scout_rounds/POST-PI-AGGRESSIVE-ROUND-3X300-2026-07-23/lane_1_live_direct_sdk_attempt1/candidate_exports
```
## Lane 2

Fresh output:
`tmp/parallel_scout_rounds/POST-PI-AGGRESSIVE-ROUND-3X300-2026-07-23/lane_2_live_direct_sdk_attempt1`

```bash
python scripts/gabriel_state_source_scout.py \
  --live \
  --live-backend direct-sdk \
  --state ALL \
  --allow-mixed-states \
  --municipalities-csv docs/analysis/parallel_scout_rounds/POST-PI-AGGRESSIVE-ROUND-3X300-2026-07-23/lane_2_input.csv \
  --output-dir tmp/parallel_scout_rounds/POST-PI-AGGRESSIVE-ROUND-3X300-2026-07-23/lane_2_live_direct_sdk_attempt1 \
  --prompt-mode compact \
  --search-hints-csv docs/analysis/municipality_search_hints_2026-07-22.csv \
  --model gpt-5.4-nano \
  --search-context-size low \
  --max-prompts 300 \
  --live-hard-cap 300 \
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
  --cost-log-path tmp/parallel_scout_rounds/POST-PI-AGGRESSIVE-ROUND-3X300-2026-07-23/lane_2_live_direct_sdk_attempt1/batch_cost_log.csv \
  --candidate-export-dir tmp/parallel_scout_rounds/POST-PI-AGGRESSIVE-ROUND-3X300-2026-07-23/lane_2_live_direct_sdk_attempt1/candidate_exports
```
## Lane 3

Fresh output:
`tmp/parallel_scout_rounds/POST-PI-AGGRESSIVE-ROUND-3X300-2026-07-23/lane_3_live_direct_sdk_attempt1`

```bash
python scripts/gabriel_state_source_scout.py \
  --live \
  --live-backend direct-sdk \
  --state ALL \
  --allow-mixed-states \
  --municipalities-csv docs/analysis/parallel_scout_rounds/POST-PI-AGGRESSIVE-ROUND-3X300-2026-07-23/lane_3_input.csv \
  --output-dir tmp/parallel_scout_rounds/POST-PI-AGGRESSIVE-ROUND-3X300-2026-07-23/lane_3_live_direct_sdk_attempt1 \
  --prompt-mode compact \
  --search-hints-csv docs/analysis/municipality_search_hints_2026-07-22.csv \
  --model gpt-5.4-nano \
  --search-context-size low \
  --max-prompts 300 \
  --live-hard-cap 300 \
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
  --cost-log-path tmp/parallel_scout_rounds/POST-PI-AGGRESSIVE-ROUND-3X300-2026-07-23/lane_3_live_direct_sdk_attempt1/batch_cost_log.csv \
  --candidate-export-dir tmp/parallel_scout_rounds/POST-PI-AGGRESSIVE-ROUND-3X300-2026-07-23/lane_3_live_direct_sdk_attempt1/candidate_exports
```

## After processes terminate

Run the offline lane auditor against `parallel_round_manifest.json`. Do not run any
national builder or merge command from this file.
