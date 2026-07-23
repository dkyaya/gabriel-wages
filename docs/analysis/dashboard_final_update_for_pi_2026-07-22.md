# Dashboard final update for PI — 2026-07-22

## Status

PASS. The deterministic yield-learning and dashboard builders were rerun from the committed post–Tier 1 Wave 2 queue, coverage, priority, and wave-summary files. All ten JSON files parsed successfully and reproduce the frozen national totals.

The documented GitHub Pages project URL is:

`https://dkyaya.github.io/gabriel-wages/`

The repository documents this as the configured project-site URL. Availability still depends on GitHub Pages being enabled and the committed deployment workflow having completed successfully.

## Refreshed JSON

- `docs/dashboard/data/state_summary.json`
- `docs/dashboard/data/candidate_queue_summary.json`
- `docs/dashboard/data/coverage_funnel.json`
- `docs/dashboard/data/analysis_readiness.json`
- `docs/dashboard/data/priority_summary.json`
- `docs/dashboard/data/state_priority_summary.json`
- `docs/dashboard/data/top_priority_targets.json`
- `docs/dashboard/data/scout_operations_summary.json`
- `docs/dashboard/data/scout_yield_by_state.json`
- `docs/dashboard/data/scout_runtime_trends.json`

The build also regenerated the local deterministic learning outputs:

- `docs/analysis/scout_yield_learning_report_2026-07-22.md`
- `docs/analysis/scout_yield_learning_by_state_2026-07-22.csv`
- `docs/analysis/scout_yield_learning_by_wave_2026-07-22.csv`

## Metrics reflected

- 35,589 municipality/township governments in the authoritative universe;
- 794 successfully scout-covered municipalities;
- 612 candidate-positive municipalities;
- 182 parseable-empty municipalities;
- 20 failure-only municipalities held outside successful coverage;
- 1,602 URL-bearing candidate queue rows;
- 34,789 future-scout-eligible municipalities;
- 1,227 eligible Tier 1 and 3,478 eligible Tier 2 municipalities;
- latest-wave runtime 5,738.638 seconds and throughput 94.099 attempted rows/hour;
- latest-wave candidate production 205.136 parsed candidate records/hour and density 2.209 records per parseable municipality.

The state-yield layer contains all 51 state/DC rows. Among states with at least ten successful scouts, the leading observed candidate densities are Washington, Massachusetts, Pennsylvania, Florida, Michigan, California, Illinois, and New York. These rankings retain explicit sample-confidence labels and are operational learning signals, not substantive state comparisons.

## What the dashboard means

The main dashboard presents source-discovery coverage, queue volume and triage, a geographic state map, a source-discovery funnel, and readiness limitations. The additional operations JSON records runtime/yield trends and state-yield learning, while the priority JSON records deterministic scout-scheduling tiers. Candidate rows are unverified leads; priority and readiness measures are operational, not evidence strength.

The frontend was not changed. This task refreshed and documented the static data layer only. The operations files are available for a later low-risk UI panel, but the PI report does not imply that every JSON field is already rendered visibly by the current frontend.

## Interpretation boundary

The dashboard does not report verified-source totals, ingested wage observations, safety/non-safety wage gaps, mechanism estimates, or causal results. It must not be used to infer that a candidate URL is official, complete, current, matched by city-cycle, or suitable for wage extraction.

No scout, live/API/model call, hosted-search diagnostic, URL verification, ingestion, codification, queue/coverage rebuild, priority-methodology change, or dashboard frontend change occurred in this update.
