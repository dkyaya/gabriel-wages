# PI report input audit — 2026-07-22

## Decision

PASS. The committed post–Tier 1 Wave 2 state is internally consistent and suitable for a frozen PI-facing source-discovery report. Work began at `3f2f815f4ca4b4e90f6ca1bff769bd300843d703` (`Run Tier 1 Wave 2 compact adaptive scout`), with no tracked worktree changes. The unrelated untracked root `package-lock.json` was reported and left untouched.

Exact ancestry checks passed for `3f2f815`, `bef5077`, `b6bd6b3`, and `bbb4dfa`. No requested filename required substitution: the canonical current files retain their historical date-stamped names even though their contents include the latest accepted waves.

## Files used

Project context:

- `AGENTS.md`
- `PROGRESS.md`
- `docs/analysis/chatgpt_handoff_latest.md`

Current queue and coverage authority:

- `docs/analysis/national_municipality_universe.csv` — 35,589 authoritative municipal/township rows
- `docs/analysis/national_scout_candidate_queue_2026-07-20.csv` — 1,602 unique URL-bearing queue rows
- `docs/analysis/national_scout_coverage_municipality_2026-07-20.csv` — 35,589 municipality status rows
- `docs/analysis/national_scout_coverage_state.csv` — 51 state/DC summaries
- `docs/analysis/national_scout_coverage_county.csv` — 3,144 county-equivalent summaries

Wave evidence and comparisons:

- `docs/analysis/coordinator_150row_serial_live_result_review_2026-07-21.md`
- `docs/analysis/coordinator_150row_serial_live_queue_coverage_update_2026-07-21.md`
- `docs/analysis/wave2_coordinator_150row_serial_live_result_review_2026-07-22.md`
- `docs/analysis/wave2_coordinator_150row_serial_live_queue_coverage_update_2026-07-22.md`
- `docs/analysis/tier1_coordinator_150row_serial_live_after_diag_result_review_2026-07-22.md`
- `docs/analysis/tier1_coordinator_150row_serial_live_after_diag_queue_coverage_update_2026-07-22.md`
- `docs/analysis/tier1_wave2_coordinator_150row_serial_live_result_review_2026-07-22.md`
- `docs/analysis/tier1_wave2_coordinator_150row_serial_live_queue_coverage_update_2026-07-22.md`
- `docs/analysis/tier1_wave2_dashboard_yield_refresh_2026-07-22.md`
- `docs/analysis/tier1_wave2_priority_refresh_decision_2026-07-22.md`

Operational learning inputs:

- `docs/analysis/scout_speed_stability_implementation_summary_2026-07-22.md`
- `docs/analysis/scout_speed_stability_design_2026-07-22.md`
- `docs/analysis/scout_speed_stability_next_wave_template_2026-07-22.md`
- `docs/analysis/scout_yield_learning_report_2026-07-22.md`
- `docs/analysis/scout_yield_learning_by_state_2026-07-22.csv`
- `docs/analysis/scout_yield_learning_by_wave_2026-07-22.csv`

Priority authority:

- `docs/analysis/national_municipality_priority_tiers_2026-07-22.csv`
- `docs/analysis/national_priority_tier_top_targets_2026-07-22.csv`
- `docs/analysis/state_priority_summary_2026-07-22.csv`
- `docs/analysis/national_failure_retry_priority_2026-07-22.csv`
- `docs/analysis/national_municipality_priority_tiering_methodology_2026-07-22.md`
- `docs/analysis/national_priority_tier_build_summary_2026-07-22.md`
- `docs/analysis/national_priority_tiering_validation_2026-07-22.md`
- `docs/analysis/tier_based_scouting_strategy_2026-07-22.md`
- `docs/analysis/recommended_post_tiering_wave_2026-07-22.md`

Dashboard inputs and builders:

- `scripts/build_scout_yield_learning_report.py`
- `scripts/build_dashboard_data.py`
- `scripts/build_national_municipality_priority_tiers.py` (read/compiled only; tiers were not rebuilt)
- all ten JSON files under `docs/dashboard/data/`

## Frozen national accounting

| Measure | Current value |
|---|---:|
| Authoritative municipality/township universe | 35,589 |
| Successfully scout-covered municipalities | 794 |
| Candidate-positive municipalities | 612 |
| Parseable-empty municipalities | 182 |
| Failure-only municipalities | 20 |
| Not-yet-scouted municipalities | 34,775 |
| URL-bearing candidate queue rows | 1,602 |

The identity `612 + 182 = 794` holds. Failure-only municipalities are kept outside successful coverage. A candidate-positive municipality has at least one unverified scout lead; it is not a verified source or a matched comparison.

## Frozen priority accounting

| Measure | Current value |
|---|---:|
| Universe rows scored | 35,589 |
| Future-scout eligible | 34,789 |
| Tier 1 eligible | 1,227 |
| Tier 2 eligible | 3,478 |
| Tier 3 eligible | 7,008 |
| Tier 4 eligible | 10,620 |
| Tier 5 eligible | 12,456 |
| Separate failure-retry targets | 20 |

The priority builder was previously refreshed after Tier 1 Wave 2 using the unchanged deterministic methodology. Priority tiers are research-operational scheduling heuristics, not facts about unionization, departments, source quality, wage gaps, or causal effects.

## Latest-wave checkpoint

Tier 1 Wave 2 attempted 150 municipalities and returned 148 parseable results: 122 candidate-positive, 26 parseable-empty, and two isolated failure-only outcomes. It produced 327 parsed candidate records, of which 325 had locators and entered the queue. Runtime was 5,738.638 seconds (95m38.638s), or 94.099 attempted rows/hour. Joplin, Missouri and Framingham, Massachusetts remain retry-only failures; neither is evidence that a source does not exist.

## Stage and interpretation limits

The frozen report distinguishes five stages:

1. **Municipality searched:** the scout returned a parseable candidate list or a parseable empty list.
2. **Candidate source row:** a possible document or URL was identified and queued; it remains unverified.
3. **Verified source:** employer, unit, provenance, source type, dates, access, and relevance have been checked.
4. **Ingested/codified contract:** a complete document passed provenance/schema gates and text measurement.
5. **Analysis-ready evidence:** matched safety and non-safety city-cycle observations have usable wage/mechanism fields.

This task reaches only the first two stages. It does not establish a wage gap, a safety/non-safety comparison, a bargaining-mechanism effect, or a causal result.

## Task boundary confirmation

Only deterministic local yield and dashboard summaries were rebuilt from existing committed artifacts. No scout, smoke test, hosted-search diagnostic, API/model call, URL opening, source verification, contract ingestion, codification, queue/coverage rebuild, priority rebuild or methodology change, canonical promotion, or claim use occurred.
