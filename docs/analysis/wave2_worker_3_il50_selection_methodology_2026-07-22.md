# Wave 2 Worker 3 IL50 Selection Methodology

Date: 2026-07-22

Status: **locked offline-preparation input for a future coordinator-controlled serialized live queue; scout-stage only**

## Result and state rationale

`wave2_worker_3_il50_scout_input_2026-07-22.csv` contains exactly 50 unique active Illinois municipal/place governments. Illinois was chosen over New York because its current evidence is both broader and higher-yield: 68 of 74 successful municipalities are candidate-positive (91.9%), producing 217 rows or 2.932 per covered municipality. New York is 21/25 (84.0%) with 57 rows or 2.280 per covered municipality.

The selected population range is 20,332–81,004 and totals 1,356,772. Eleven rows are multi-county; the batch preserves 63 relationships across ten counties.

## Selection source files

- `docs/analysis/national_municipality_universe.csv`;
- `docs/analysis/national_scout_coverage_municipality_2026-07-20.csv`;
- `docs/analysis/national_scout_candidate_queue_2026-07-20.csv`;
- `docs/analysis/national_municipality_county_crosswalk.csv`;
- `data/contracts.csv` and `data/city_coverage.csv`; and
- current state coverage plus prior IL25/IL25.2/IL25.3 reviews for state-yield context.

No live source or URL was consulted.

## Exclusion and ranking rule

The deterministic builder requires Illinois, `active_status=Y`, `government_type=municipal`, `geography_type=place`, current `not_scouted`, no failed connection, no queue entry by ID or exact state/name, no canonical/corpus overlap, and a complete county join. Bloomington and the other seven named failure rows are excluded. County subdivisions and township governments are excluded by the `municipal/place` gate.

`TOWN OF CICERO` is retained because the authoritative Census files classify it as an incorporated `municipal/place` government; it is not a township/county-subdivision row. The exact ID and county context remain locked so a township or same-name employer cannot substitute.

Eligible rows are sorted by descending 2023 population, then municipality and municipality ID; the first 50 are locked.

## Selection buckets

| Bucket | Ranks | Rows | Purpose |
|---|---:|---:|---|
| `largest_remaining_place_employer` | 1–10 | 10 | Largest clean employers after 74 successful outcomes |
| `high_population_place_expansion` | 11–25 | 15 | Continue the suburban/city municipal tier |
| `regional_municipal_employer_expansion` | 26–40 | 15 | Add geographic and multi-county variation |
| `smaller_place_employer_diversity` | 41–50 | 10 | Preserve smaller-place diversity at the slice boundary |

## Top 10 priorities

| Rank | Municipality | Population | Rationale |
|---:|---|---:|---|
| 1 | Cicero | 81,004 | Largest remaining municipal/place employer |
| 2 | Bartlett | 39,992 | Cook/DuPage/Kane multi-county village |
| 3 | Carol Stream | 38,966 | Large DuPage village employer |
| 4 | Hanover Park | 36,165 | Cook/DuPage multi-county village |
| 5 | Addison | 35,167 | Large DuPage village employer |
| 6 | Woodridge | 33,566 | Three-county municipal comparison |
| 7 | Glendale Heights | 32,409 | DuPage municipal employer expansion |
| 8 | Gurnee | 30,193 | Lake County municipal employer |
| 9 | Algonquin | 30,134 | Kane/McHenry multi-county village |
| 10 | Niles | 29,513 | Cook County municipal employer |

## Duplicate, canonical, coverage, and timeout checks

The file has exactly 50 unique municipality and Census IDs, one `worker_3`, one future queue ID, and all `not_scouted`. Current queue ID/name checks, canonical exact state/name checks, universe/corpus flags, and current canonical-overlap status all pass with zero overlap. County counts and Census IDs reconcile. Bloomington and all other forbidden timeout names are absent.

## Risks and expected source-discovery value

This is the fourth Illinois slice and reaches smaller city/village employers. Source availability may decline from the first 74 successful rows. Suburban fire-protection, park, school, library, and other special districts create a particularly high wrong-employer risk; none may substitute for the exact selected municipality. Multi-county context is descriptive only.

The current state average suggests roughly 46 candidate-positive municipalities and 147 candidate rows for 50 comparable targets, but that likely overstates a smaller-employer tier. A cautious IL planning range is 38–46 positive municipalities and 100–145 candidate rows. All outputs remain unverified scout-stage evidence only.
