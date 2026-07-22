# Next Scout Wave Template — Strong Preflight + Adaptive Compact Run

This is a future command template, not authorization. Replace placeholders only after worker evidence, locked-input identity/hash, eligibility, prompt, protected-file, and fresh-directory gates pass.

## 1. Plan and execute the stronger preflight

Plan only (offline):

```bash
python scripts/run_scout_preflight_gate.py \
  --plan-only \
  --output-dir tmp/<RUN_LABEL>_preflight_plan \
  --model gpt-5.4-nano \
  --timeout 30 \
  --search-context-size low \
  --max-calls 4
```

Immediately before an authorized live run, execute the same gate without `--plan-only`. Add `--include-one-row-probe --probe-input-csv <EXACT_ONE_ROW.csv> --probe-output-dir tmp/<FRESH_PROBE_DIR>` only when the one-row probe is explicitly authorized. Stop unless `gate_status=passed`.

## 2. Full coordinator live command

```bash
python scripts/gabriel_state_source_scout.py \
  --live \
  --live-backend direct-sdk \
  --state ALL \
  --allow-mixed-states \
  --municipalities-csv docs/analysis/<LOCKED_INPUT.csv> \
  --output-dir tmp/<FRESH_LIVE_OUTPUT_DIR> \
  --prompt-mode compact \
  --search-hints-csv docs/analysis/municipality_search_hints_2026-07-22.csv \
  --model gpt-5.4-nano \
  --search-context-size low \
  --max-prompts <EXACT_ROW_COUNT> \
  --live-hard-cap <EXACT_ROW_COUNT> \
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
  --cost-log-path tmp/<FRESH_LIVE_OUTPUT_DIR>/batch_cost_log.csv
```

Review prompt length, `row_timing.csv`, planned/actual sleep, adaptive events, token use, failures, rows/hour, candidates/hour, and candidate density. Stop on connection collapse, systematic parser/schema failure, lifecycle loss, protected mutation, or secret exposure. Resume only from a terminal parent into a different fresh output directory after exact input-hash and completed-ID review.

Rebuild queue/coverage exactly once only after a complete merge-eligible lineage, then rebuild yield learning and dashboard JSON. Verification, ingestion, codification, canonical promotion, and claim use remain separate.
