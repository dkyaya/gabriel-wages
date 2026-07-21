# Worker 1 CA50 Selection Methodology

Date: 2026-07-21

Status: locked offline-preparation input for a future coordinator-controlled serialized live queue. No live scout, API/model call, source opening, verification, ingestion, codification, or national queue/coverage rebuild occurred.

## Result

`worker_1_ca50_scout_input_2026-07-21.csv` contains exactly 50 unique California municipal/place governments. They are the 50 highest-population eligible California city governments after the current successful-coverage, queue, canonical, government-type, and timeout-only exclusions were applied.

The ordered batch is: Santa Clarita; San Bernardino; Fontana; Moreno Valley; Rancho Cucamonga; Lancaster; Palmdale; Victorville; Orange; Simi Valley; Thousand Oaks; Antioch; Carlsbad; Menifee; Murrieta; Temecula; Santa Maria; San Buenaventura (Ventura); Downey; Costa Mesa; Jurupa Valley; West Covina; El Monte; Rialto; El Cajon; Inglewood; Burbank; Vacaville; San Mateo; Hesperia; Daly City; Vista; Norwalk; Tracy; San Marcos; Merced; Chino; Indio; Hemet; Carson; Manteca; Compton; Mission Viejo; South Gate; Santa Monica; Westminster; Citrus Heights; Lake Forest; San Leandro; and San Ramon.

## Authoritative inputs

- Municipality/employer identity, IDs, type, and population: `national_municipality_universe.csv`.
- Successful and failed scout status: `national_scout_coverage_municipality_2026-07-20.csv`, current through 2026-07-21.
- Existing queued municipality IDs: `national_scout_candidate_queue_2026-07-20.csv`, current through 2026-07-21.
- Strategic context: `next_wave_municipality_scout_manifest_2026-07-16.csv`.
- All county relationships: `national_municipality_county_crosswalk.csv`.
- Operating boundary and failure exclusions: the serialized recovery relay and `serialized_parallel_stage1_recovery_review_2026-07-21.md`.

The manifest's five California anchors—Los Angeles, Sacramento, San Diego, San Francisco, and Fresno—are already successfully scout-covered. The batch therefore expands beyond the manifest rather than re-scouting those anchors.

## Deterministic selection rule

The builder selects California rows only when all of the following hold:

1. `government_type=municipal`, `geography_type=place`, and `active_status=Y` in the authoritative universe.
2. `scout_coverage_status=not_scouted` and `failed_connection_attempt_count=0` in current municipality coverage.
3. No candidate-queue row has the municipality ID.
4. The municipality is not already in the canonical corpus.
5. The target is not Oakland, Stockton, Oxnard, Redding, Fairfield, Bloomington, or Princeton.
6. The target is a city/place employer, not a county, school district, transit or port/airport authority, housing authority, park district, township government, special district, or private provider.

Eligible rows are sorted by descending 2023 population, with municipality name as the deterministic tie-breaker, and the first 50 are locked. Ranks 1–10 are `largest_uncovered_city_anchor`, ranks 11–30 are `high_population_city_expansion`, and ranks 31–50 are `regional_city_employer_expansion`.

This is an employer-priority rule, not a finding that every target directly employs both police and fire. The future scout must return an empty list rather than attribute a county, district, or contracted safety unit to the city. That is why the row-level verification note names the exact Census employer and preserves categorical exclusions.

## County and ID preservation

Every row preserves the authoritative `municipality_id`, `census_gov_id`, government name/type, population, relationship count, multi-county flag, and a summary of every crosswalk relationship. The builder asserts that each row's crosswalk count equals `county_relationship_count` and that all crosswalk rows share the selected Census government ID.

## Eligibility assertions

The reproducible builder asserts 50 rows, 50 distinct municipality IDs, 50 distinct Census government IDs, no cross-worker overlap, no current queue overlap, no canonical overlap, no successful or failure-only coverage, and no prohibited timeout municipality. It also asserts the exact ordered name list so future source-file changes cannot silently alter the locked batch.

All rows remain `locked_for_worker_prep_dry_run_only`. Dry-run output is prompt-contract evidence only and does not confer discovery coverage.
