# POST-PI-CHECKPOINT-ROUND-3X160-2026-07-23 — Lane Dry-Run Command Preview

**Offline previews only. These commands make no backend call.**

Run and audit every lane dry-run before any separately authorized live collection.
Require exact row counts, compact prompts, complete hints, adaptive metadata, and
locked identities. Candidate-export routing applies only to completed live runs.

## Lane 1

```bash
python scripts/gabriel_state_source_scout.py \
  --dry-run \
  --state ALL \
  --allow-mixed-states \
  --municipalities-csv docs/analysis/parallel_scout_rounds/POST-PI-CHECKPOINT-ROUND-3X160-2026-07-23/lane_1_input.csv \
  --output-dir tmp/parallel_scout_rounds/POST-PI-CHECKPOINT-ROUND-3X160-2026-07-23/lane_1_dry_run_attempt1 \
  --prompt-mode compact \
  --search-hints-csv docs/analysis/municipality_search_hints_2026-07-22.csv \
  --live-hard-cap 160 \
  --sleep-between-prompts 5 \
  --adaptive-sleep \
  --adaptive-sleep-min 3 \
  --adaptive-sleep-base 5 \
  --adaptive-sleep-max 15 \
  --adaptive-sleep-backoff 10 \
  --adaptive-sleep-stability-window 25 \
  --adaptive-sleep-failure-window 2
```
## Lane 2

```bash
python scripts/gabriel_state_source_scout.py \
  --dry-run \
  --state ALL \
  --allow-mixed-states \
  --municipalities-csv docs/analysis/parallel_scout_rounds/POST-PI-CHECKPOINT-ROUND-3X160-2026-07-23/lane_2_input.csv \
  --output-dir tmp/parallel_scout_rounds/POST-PI-CHECKPOINT-ROUND-3X160-2026-07-23/lane_2_dry_run_attempt1 \
  --prompt-mode compact \
  --search-hints-csv docs/analysis/municipality_search_hints_2026-07-22.csv \
  --live-hard-cap 160 \
  --sleep-between-prompts 5 \
  --adaptive-sleep \
  --adaptive-sleep-min 3 \
  --adaptive-sleep-base 5 \
  --adaptive-sleep-max 15 \
  --adaptive-sleep-backoff 10 \
  --adaptive-sleep-stability-window 25 \
  --adaptive-sleep-failure-window 2
```
## Lane 3

```bash
python scripts/gabriel_state_source_scout.py \
  --dry-run \
  --state ALL \
  --allow-mixed-states \
  --municipalities-csv docs/analysis/parallel_scout_rounds/POST-PI-CHECKPOINT-ROUND-3X160-2026-07-23/lane_3_input.csv \
  --output-dir tmp/parallel_scout_rounds/POST-PI-CHECKPOINT-ROUND-3X160-2026-07-23/lane_3_dry_run_attempt1 \
  --prompt-mode compact \
  --search-hints-csv docs/analysis/municipality_search_hints_2026-07-22.csv \
  --live-hard-cap 160 \
  --sleep-between-prompts 5 \
  --adaptive-sleep \
  --adaptive-sleep-min 3 \
  --adaptive-sleep-base 5 \
  --adaptive-sleep-max 15 \
  --adaptive-sleep-backoff 10 \
  --adaptive-sleep-stability-window 25 \
  --adaptive-sleep-failure-window 2
```
