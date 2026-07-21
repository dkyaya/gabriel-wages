# Dashboard Data Schema

Date: 2026-07-21  
Schema version: 0.1.0

## General contract

Dashboard JSON is generated, not hand-edited. Every file has a top-level `metadata` object:

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | string | Dashboard contract version |
| `generated_at` | ISO-8601 UTC string | Builder execution time |
| `data_vintage` | ISO date/string | Latest coverage-accounting vintage represented |
| `source_files` | array of strings | Repository-relative inputs actually read |
| `warnings` | array of strings | Missing optional inputs or nonfatal limitations |
| `limitations` | array of strings | Required stage and interpretation caveats |

Numbers are JSON numbers, booleans are JSON booleans, and unavailable future measures are `null`. The frontend must not convert `null` to zero. Empty means “input absent or not yet integrated,” while zero means a present input recorded none.

## `docs/dashboard/data/state_summary.json`

Purpose: national map, state selector, state panel, and printable state report.

Sources:

- `national_scout_coverage_state.csv` for universe, coverage, failure, candidate, likely-triad, calibration, and token-accounting fields;
- `national_scout_candidate_queue_2026-07-20.csv` for state queue buckets and queued municipalities;
- optional `claim_register_2026-07-12.csv` and `state_city_claim_map_2026-07-12.csv` for prior claim context; and
- universe and municipality coverage tables for build-time consistency checks.

Update frequency: after every coordinator queue/coverage rebuild, never independently from worker scouts.

Top-level fields:

- `metric_definition`: UI explanation of the operational readiness score;
- `totals`: national current counts plus null future counts; and
- `states`: one object for each state and DC.

State object:

```json
{
  "state": "CA",
  "state_name": "California",
  "municipality_universe": 483,
  "scout_coverage_count": 21,
  "scout_coverage_rate": 4.3478,
  "candidate_positive_count": 20,
  "no_candidate_count": 1,
  "failed_scout_municipality_count": 4,
  "failed_scout_attempt_count": 4,
  "candidate_rows": 64,
  "high_priority_queue_count": 53,
  "medium_priority_queue_count": 3,
  "low_priority_queue_count": 2,
  "hold_or_rejected_queue_count": 6,
  "queued_municipality_count": 20,
  "likely_matched_set_count": 17,
  "calibration_verified_municipality_count": 0,
  "verified_count": null,
  "ingested_count": null,
  "claim_ids_in_prior_registry": [],
  "claim_mapped_city_count": 0,
  "claim_readiness_level": "matched_set_leads_need_verification",
  "evidence_readiness_score": 89.0,
  "map_color_metric": {
    "field": "evidence_readiness_score",
    "value": 89.0,
    "scale": "0_to_100_operational_triage_only"
  },
  "short_state_narrative": "...",
  "printable_report_data": {
    "route": "#/state/CA",
    "title": "California municipal labor evidence brief",
    "headline_metrics": [],
    "narrative": "...",
    "status_caveat": "..."
  }
}
```

Controlled `claim_readiness_level` values:

- `not_started`;
- `claim_context_without_current_scout_coverage`;
- `scout_coverage_only`;
- `candidate_leads_need_verification`; and
- `matched_set_leads_need_verification`.

None of these values means that a substantive claim is proven. The readiness score is a UI scheduling score, not an empirical estimate.

## `docs/dashboard/data/candidate_queue_summary.json`

Purpose: candidate queue cards, state table, unit composition, and priority explorer.

Source: national candidate queue plus state coverage for likely matched-set counts.

Update frequency: after every coordinator queue rebuild.

Fields:

- `stage`: always identifies the content as an unverified scout candidate queue;
- `totals`: candidate rows, municipalities represented, high/medium/low later-verification rows, later-verification total, and hold/rejected total;
- `by_state`: state candidate rows, municipality counts, controlled triage buckets, and likely matched-set municipality count;
- `by_unit_type`: `police`, `fire`, `non_safety`, and `unclear` counts;
- `by_triage_bucket`: exact durable queue buckets;
- `by_scout_confidence`: model/scout confidence metadata; and
- `by_verification_priority_label`: separate scheduling label retained for transparency.

No raw URL, document text, or secret-bearing run metadata appears in this summary.

## `docs/dashboard/data/coverage_funnel.json`

Purpose: national source-discovery funnel and explicit future-stage placeholders.

Source: national state coverage.

Update frequency: after every coordinator coverage rebuild.

`current_funnel` stages are ordered and non-increasing:

1. `municipality_universe`;
2. `scout_covered`;
3. `candidate_positive`;
4. `queued_for_later_verification`; and
5. `likely_matched_set_leads`.

`future_funnel` holds nullable `verified_sources`, `ingested_contracts`, `extracted_wage_observations`, `codified_mechanism_evidence`, and `claim_ready_matched_sets`. `separate_failure_accounting` records failure-only municipalities and all excluded connection attempts outside the funnel.

## `docs/dashboard/data/analysis_readiness.json`

Purpose: show which analyses are supported, blocked, or require new inputs.

Sources: queue/coverage plus optional claim register, state-city claim map, and hypothesis tracker.

Update frequency: after queue/coverage rebuilds and after coordinated claim-register updates.

Fields:

- `overall_status`;
- `current_inputs` with file-availability booleans;
- `source_discovery_readiness` counts and assessment;
- `claim_inventory_context` counts and a non-promotion caveat;
- `stage_availability` with distinct scout, verification, ingestion, codified, wage, and regression objects;
- `analyses_available_now`;
- `analyses_not_yet_supported`; and
- `promotion_gate`.

## Planned `docs/dashboard/data/state_claims.json`

Purpose: claim/evidence/reasoning cards after a dedicated builder is reviewed.

Sources: claim register, claim evidence bridge, evidence/codify outputs, and state-city claim map. National scout candidates may be linked only as source needs.

Update frequency: only after a coordinated claim-register/evidence update.

Proposed fields per claim:

- `claim_id`, `claim_text`, `scope`, `claim_status`, `evidence_strength`;
- `states`, `cities`, `occupations`, `mechanism_attributes`;
- `supporting_evidence_ids` and counts;
- `reasoning_summary`, `counterevidence_summary`, `key_limitations`;
- `what_would_change_our_mind`, `additional_sources_needed`;
- `report_ready`; and
- `unverified_scout_source_needs`, separately labeled.

The first builder does not emit this file because the evidence bridge and national state mapping require a dedicated schema audit.

## Planned `docs/dashboard/data/municipality_summary.json`

Purpose: municipality explorer and later city matched-set table.

Sources: municipality universe, municipality coverage, county crosswalk, queue, and future verification/extraction ledgers.

Update frequency: after coordinated queue/coverage rebuilds; later after verification/extraction rebuilds.

Proposed current fields:

- `state`, `municipality`, `municipality_id`, `census_gov_id`;
- `government_type`, `geography_type`, `population`;
- `county_context` and `multi_county_flag`;
- exact `scout_coverage_status` and failure accounting;
- candidate row/unit counts, queue bucket counts, and likely-triad flag; and
- nullable project-wide `verified_source_count`, `ingested_contract_count`, `wage_observation_count`, and `matched_cycle_count`.

This file is deferred because 35,589 row-level objects would materially increase the MVP payload; the state and queue summaries answer the first PI-facing questions more efficiently.

## Planned future analysis outputs

`verified_source_summary.json`, `wage_summary.json`, and `regression_results.json` should be introduced only with dedicated validated source tables. Regression records should include a specification ID, frozen input hash, sample definition, outcome, treatment/exposure variables, fixed effects, clustering, estimate, standard error, confidence interval, observation/matched-set counts, exclusions, caveats, and artifact path.

## Build behavior and compatibility

`scripts/build_dashboard_data.py`:

- fails on missing required queue/coverage/universe files;
- warns and writes empty/null claim context when optional claim files are absent;
- verifies all 51 state/DC rows, municipality/universe count agreement, unique municipality and queue IDs, and allowed scout/calibration status labels;
- writes formatted UTF-8 JSON with a trailing newline; and
- does not modify any source file.

Schema changes that rename/remove fields require a version increment. Additive fields may remain within 0.1.x if the frontend tolerates unknown properties.
