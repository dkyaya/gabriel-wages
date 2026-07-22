# Tier 1 Worker Dry-Run Command Preview

Date: 2026-07-22

These are previews only. The coordinator did not execute them. Each worker must run its command in its assigned persistent worktree after switching to its fresh local prep branch.

## Worker 1

```bash
python scripts/gabriel_state_source_scout.py \
  --dry-run \
  --state ALL \
  --allow-mixed-states \
  --municipalities-csv docs/analysis/tier1_worker_1_scout_input_2026-07-22.csv \
  --output-dir tmp/tier1_worker_1_prep_dry_run_20260722_attempt1 \
  --prompt-mode minimal \
  --live-hard-cap 50 \
  --sleep-between-prompts 5
```

## Worker 2

```bash
python scripts/gabriel_state_source_scout.py \
  --dry-run \
  --state ALL \
  --allow-mixed-states \
  --municipalities-csv docs/analysis/tier1_worker_2_scout_input_2026-07-22.csv \
  --output-dir tmp/tier1_worker_2_prep_dry_run_20260722_attempt1 \
  --prompt-mode minimal \
  --live-hard-cap 50 \
  --sleep-between-prompts 5
```

## Worker 3

```bash
python scripts/gabriel_state_source_scout.py \
  --dry-run \
  --state ALL \
  --allow-mixed-states \
  --municipalities-csv docs/analysis/tier1_worker_3_scout_input_2026-07-22.csv \
  --output-dir tmp/tier1_worker_3_prep_dry_run_20260722_attempt1 \
  --prompt-mode minimal \
  --live-hard-cap 50 \
  --sleep-between-prompts 5
```

No smoke, live scout, API/model call, URL access, verification, ingestion, codification, or queue/coverage rebuild is authorized by these commands.
