# Dashboard Data Build Summary

Date: 2026-07-21  
Builder: `scripts/build_dashboard_data.py`

## Result

The static dashboard data build was refreshed after the serialized CA25.2/NJ25 coordinator merge without changing canonical data or contacting any external service. It represents all 50 states plus the District of Columbia and writes four JSON files under `docs/dashboard/data/`.

## Files read

Required:

- `docs/analysis/national_scout_coverage_state.csv`
- `docs/analysis/national_scout_coverage_municipality_2026-07-20.csv`
- `docs/analysis/national_municipality_universe.csv`
- `docs/analysis/national_scout_candidate_queue_2026-07-20.csv`

Optional files present and read:

- `docs/analysis/claim_register_2026-07-12.csv`
- `docs/analysis/state_city_claim_map_2026-07-12.csv`
- `docs/analysis/hypothesis_tracker_2026-07-12.csv`

The municipality universe and coverage tables are used for consistency assertions; the MVP JSON does not expose government websites, source URLs, or municipality row-level details.

## JSON files created

- `docs/dashboard/data/state_summary.json`
- `docs/dashboard/data/candidate_queue_summary.json`
- `docs/dashboard/data/coverage_funnel.json`
- `docs/dashboard/data/analysis_readiness.json`

Each file records schema version, generation timestamp, source files, data vintage, warnings, and limitations.

## Current metrics

| Metric | Value |
| --- | ---: |
| States plus DC represented | 51 |
| States with successful scout coverage | 7 |
| Municipality universe | 35,589 |
| Parseable scout-covered municipalities | 207 |
| Candidate-positive municipalities | 181 |
| Parseable no-candidate municipalities | 26 |
| Current failure-only municipalities | 7 |
| Connection-failed attempts excluded from coverage | 23 |
| Candidate queue rows | 540 |
| Municipalities represented in candidate queue | 181 |
| High-priority later-verification rows | 343 |
| Medium-priority later-verification rows | 59 |
| Low-priority later-verification rows | 31 |
| Hold/rejected rows | 107 |
| Likely matched-set lead groups | 105 |
| Prior claim-register rows | 8 |
| Prior state-city claim-map rows | 26 |
| Hypothesis-tracker rows | 8 |

The 540-row queue consists of 217 police, 159 fire, 155 non-safety, and 9 unclear unit labels. Those are scout metadata, not verified bargaining units.

## Missing and future data

The build deliberately writes null placeholders for project-wide verified-source counts, dashboard-ready ingestion counts, structured wage observations, claim-ready matched sets, and regression estimates. Existing bounded calibration and prior claim/codify context remain labeled separately; they do not promote the national queue.

The MVP also defers municipality-level JSON and a claim-evidence JSON bridge. Those require a payload/performance decision and a dedicated audit of evidence IDs, state scope, and stage semantics.

## Regeneration

Run from the repository root:

```bash
python scripts/build_dashboard_data.py
```

The builder should normally run after a single coordinator has rebuilt the national candidate queue and scout coverage. It fails if required inputs disappear or counts/identifiers are inconsistent. Missing optional claim files produce warnings and empty/null claim context without breaking source-discovery output.

The builder does not require Node or a frontend build. Before committing a refresh, review the JSON diff, the printed totals, and the funnel identities. Do not regenerate from an individual parallel worker’s isolated output; wait for the coordinator merge so the dashboard cannot show half of a parallel wave.
