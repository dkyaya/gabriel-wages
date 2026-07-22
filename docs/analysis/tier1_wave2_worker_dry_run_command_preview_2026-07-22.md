# Tier 1 Wave 2 Worker Dry-Run Command Preview

Date: 2026-07-22

Command previews only; the coordinator did not execute worker dry-runs.

## Worker 1

```bash
python scripts/gabriel_state_source_scout.py \
  --dry-run \
  --state ALL \
  --allow-mixed-states \
  --municipalities-csv docs/analysis/tier1_wave2_worker_1_scout_input_2026-07-22.csv \
  --output-dir tmp/tier1_wave2_worker_1_prep_dry_run_20260722_attempt1 \
  --prompt-mode compact \
  --search-hints-csv docs/analysis/municipality_search_hints_2026-07-22.csv \
  --live-hard-cap 50 \
  --sleep-between-prompts 5 \
  --adaptive-sleep \
  --adaptive-sleep-min 3 \
  --adaptive-sleep-base 5 \
  --adaptive-sleep-max 15 \
  --adaptive-sleep-backoff 10 \
  --adaptive-sleep-stability-window 25 \
  --adaptive-sleep-failure-window 2
```

## Worker 2

```bash
python scripts/gabriel_state_source_scout.py \
  --dry-run \
  --state ALL \
  --allow-mixed-states \
  --municipalities-csv docs/analysis/tier1_wave2_worker_2_scout_input_2026-07-22.csv \
  --output-dir tmp/tier1_wave2_worker_2_prep_dry_run_20260722_attempt1 \
  --prompt-mode compact \
  --search-hints-csv docs/analysis/municipality_search_hints_2026-07-22.csv \
  --live-hard-cap 50 \
  --sleep-between-prompts 5 \
  --adaptive-sleep \
  --adaptive-sleep-min 3 \
  --adaptive-sleep-base 5 \
  --adaptive-sleep-max 15 \
  --adaptive-sleep-backoff 10 \
  --adaptive-sleep-stability-window 25 \
  --adaptive-sleep-failure-window 2
```

## Worker 3

```bash
python scripts/gabriel_state_source_scout.py \
  --dry-run \
  --state ALL \
  --allow-mixed-states \
  --municipalities-csv docs/analysis/tier1_wave2_worker_3_scout_input_2026-07-22.csv \
  --output-dir tmp/tier1_wave2_worker_3_prep_dry_run_20260722_attempt1 \
  --prompt-mode compact \
  --search-hints-csv docs/analysis/municipality_search_hints_2026-07-22.csv \
  --live-hard-cap 50 \
  --sleep-between-prompts 5 \
  --adaptive-sleep \
  --adaptive-sleep-min 3 \
  --adaptive-sleep-base 5 \
  --adaptive-sleep-max 15 \
  --adaptive-sleep-backoff 10 \
  --adaptive-sleep-stability-window 25 \
  --adaptive-sleep-failure-window 2
```

No smoke, hosted-search diagnostic, live/API/model call, URL access, verification, ingestion, codification, or queue/coverage rebuild is authorized.
