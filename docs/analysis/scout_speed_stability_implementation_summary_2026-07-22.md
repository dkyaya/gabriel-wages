# Scout Speed/Stability Implementation Summary — 2026-07-22

## Implemented

- Added a composite fail-closed preflight gate with no-search, hosted-search trivial, hosted-search municipality-style, and optional explicit one-row production probe stages.
- Added opt-in direct-SDK adaptive sleep with min/base/max/backoff/stability/failure controls while retaining fixed five-second behavior by default.
- Extended `row_timing.csv` and `run_metadata.json` with planned/actual pacing evidence.
- Added `--prompt-mode compact`, preserving the minimal prompt’s locked identity, controls, and exact output schema with 36.09% fewer representative characters.
- Generated 35,589 deterministic five-phrase municipality hint rows and added exact-ID `--search-hints-csv` support.
- Added deterministic state/wave yield learning outputs and three dashboard operations JSON files.
- Added no-network regression coverage for fixed/adaptive pacing, compact contract, deterministic hints, hint attachment, and plan-only preflight artifacts.

## Strong preflight use

First run the gate in `--plan-only` mode and inspect `preflight_plan.json`, `preflight_gate_report.md`, and `sanitized_command_preview.txt`. Under a separately authorized live task, execute the gate immediately before the full run. A 150-row coordinator run must not proceed unless the executed gate passes. The optional probe requires an explicit one-row CSV, a fresh probe directory, and a four-call cap; its candidate handoff is quarantined.

## Adaptive pacing use

Pass `--adaptive-sleep` with the reviewed defaults:

```text
--adaptive-sleep
--adaptive-sleep-min 3
--adaptive-sleep-base 5
--adaptive-sleep-max 15
--adaptive-sleep-backoff 10
--adaptive-sleep-stability-window 25
--adaptive-sleep-failure-window 2
```

The controller begins at five seconds, steps down by one second after each 25-row stable window, backs off to at least 10 seconds on the first transport failure, and reaches 15 seconds at the failure window. The existing connection-collapse stop remains authoritative. Without `--adaptive-sleep`, `--sleep-between-prompts` behaves exactly as before.

## Compact prompts and search hints

Use `--prompt-mode compact --search-hints-csv docs/analysis/municipality_search_hints_2026-07-22.csv`. Hints match exact municipality IDs and are described in-prompt as starting phrases only. Missing row-aware IDs fail closed. Regenerate hints offline with `python scripts/build_municipality_search_hints.py` whenever the authoritative universe identity fields change.

The representative test estimates 1,483 minimal versus 948 compact tokens using a simple characters/4 proxy. This 535-token/36.09% reduction is directional, not an SDK usage measurement. Review actual input tokens after the next authorized run.

## Yield learning and dashboard data

Run `python scripts/build_scout_yield_learning_report.py` after accounting is rebuilt for a successful wave, then `python scripts/build_dashboard_data.py`. Current reviewed wave densities are 1.651, 1.507, and 1.887 candidates per parseable municipality. Current 10+ sample leaders by density are PA, FL, MA, CA, IL, NY, NJ, AZ, and TX; confidence and sample size must accompany the metric.

## Recommended next-run pattern

Use one coordinator-controlled direct-SDK lane, an exact locked input/cap, immediate executed composite preflight, compact prompts, deterministic hints, adaptive pacing, zero SDK retries, and a fresh output directory. Preserve resume lineage and stop on transport collapse. This package does not authorize a live run or concurrent workers.

## Boundary

No live/API/model call, source opening, verification, ingestion, codification, queue/coverage rebuild, priority-tier rebuild/methodology change, canonical/corpus edit, dashboard frontend edit, remote action, or push occurred.
