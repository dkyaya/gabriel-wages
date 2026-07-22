# Wave 2 Worker 1 CA50 Selection Methodology

Date: 2026-07-22

Status: **locked offline-preparation input for a future coordinator-controlled serialized live queue; scout-stage only**

## Result and state rationale

`wave2_worker_1_ca50_scout_input_2026-07-22.csv` contains exactly 50 unique active California municipal/place governments. California is retained because its current scaled yield is the strongest: 90 of 94 successful municipalities are candidate-positive (95.7%), producing 234 candidate rows. The batch continues down the population-ranked employer distribution without repeating any of the 94 covered or six failure-only municipalities.

The population range is 60,015–84,782; the selected places represent 3,605,758 residents in the authoritative 2023 population field. All 50 are single-county places spanning 20 counties.

## Selection source files

- `docs/analysis/national_municipality_universe.csv` — authoritative municipality/employer identity, IDs, classifications, population, and relationship counts.
- `docs/analysis/national_scout_coverage_municipality_2026-07-20.csv` — current successful, empty, and failed scout outcomes through the coordinator 150-row merge.
- `docs/analysis/national_scout_candidate_queue_2026-07-20.csv` — current 786-row candidate queue.
- `docs/analysis/national_municipality_county_crosswalk.csv` — all county relationships.
- `data/contracts.csv` and `data/city_coverage.csv` — canonical exact state/municipality exclusions.
- `docs/analysis/national_scout_coverage_state.csv` and the prior coordinator reviews — state-yield and operating context.

No website, source URL, PDF, external lookup, or model output was consulted.

## Exclusion and ranking rule

The deterministic builder requires California, `active_status=Y`, `government_type=municipal`, `geography_type=place`, current `not_scouted`, zero failed-connection attempts, no queue entry by ID or exact state/name, no canonical/corpus overlap, and a complete county join. It excludes Bloomington, Oakland, Stockton, Oxnard, Redding, Fairfield, Princeton, and Moreno Valley by name. Counties, schools, township governments, transit, housing, port/airport, park, fire/water/utility, industrial and other special districts, regional bodies, universities, state/federal employers, and private providers are prohibited.

Eligible rows are sorted by descending 2023 population, then exact municipality name and municipality ID. The first 50 are locked; there is no discretionary substitution.

## Selection buckets

| Bucket | Ranks | Rows | Purpose |
|---|---:|---:|---|
| `largest_remaining_place_employer` | 1–10 | 10 | Largest clean employers after the first 94 covered municipalities |
| `high_population_place_expansion` | 11–25 | 15 | Continue the upper municipal-employer tier |
| `regional_municipal_employer_expansion` | 26–40 | 15 | Extend geographic and labor-market variation |
| `smaller_place_employer_diversity` | 41–50 | 10 | Preserve diversity at the lower edge of this 50-row slice |

## Top 10 priorities

| Rank | Municipality | Population | Rationale |
|---:|---|---:|---|
| 1 | Folsom | 84,782 | Largest remaining clean CA place employer |
| 2 | Whittier | 84,143 | Large Los Angeles County municipal employer |
| 3 | Hawthorne | 83,364 | Large Los Angeles County municipal employer |
| 4 | Livermore | 82,908 | Alameda County employer-scale expansion |
| 5 | Newport Beach | 82,637 | Orange County municipal contrast |
| 6 | Rancho Cordova | 82,605 | Sacramento County employer expansion |
| 7 | Buena Park | 81,958 | Orange County municipal contrast |
| 8 | Mountain View | 81,785 | Santa Clara County employer comparison |
| 9 | Redwood City | 80,996 | San Mateo County employer comparison |
| 10 | Perris | 80,603 | Riverside County regional expansion |

## Duplicate, canonical, coverage, and timeout checks

The file has 50 unique municipality IDs and 50 unique Census government IDs, one `worker_1`, one `COORD-SERIAL150-WAVE2-2026-07-22`, and only `coverage_status_before_run=not_scouted`. All municipality IDs and exact CA/name keys are absent from the current queue. Exact CA/name keys are absent from canonical contracts and city coverage. Universe and current coverage both report no corpus overlap. Crosswalk relationship count and Census ID reconcile for every row.

Oakland, Stockton, Oxnard, Redding, Fairfield, and Moreno Valley are known California failure-only rows and are excluded. The other globally named failure rows are also absent. No retry is embedded in this fresh-discovery batch.

## Risks and expected source-discovery value

The batch moves below the prior large-city tier. Some places may contract police or fire services or have only external district sources; those cannot be attributed to the selected city. Wrong-employer and context-only returns are therefore material risks. The prompt must allow an empty list and must preserve exact employer, ordinary non-safety, duplicate, source-stage, and public-records prohibitions.

At the current CA average, 50 comparable municipalities would imply about 48 candidate-positive outcomes and 124 candidate rows. That is a planning reference, not a guarantee; smaller-employer source availability may be lower. No selected source is verified, downloaded, ingested, codified, canonical, or claim-supporting.
