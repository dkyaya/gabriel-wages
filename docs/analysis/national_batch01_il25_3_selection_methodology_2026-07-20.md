# Illinois National Batch 01 IL25.3 Selection Methodology

Date: 2026-07-20

Stage: municipal selection and scout-input preparation only. This task did not run a model/API call, open a source URL, verify or download a document, ingest a source, codify text, edit canonical data, or create claim evidence.

## Purpose

IL25.3 is the third 25-municipality Illinois state-scale discovery slice. IL25 successfully covered 24 municipalities, with Bloomington retained as a failure-only timeout. IL25.2 successfully covered all 25 municipalities. Together, those runs leave Illinois with 49 successfully source-discovery-covered municipalities, 45 candidate-positive municipalities, four parseable-empty municipalities, and Bloomington as the sole failure-only row.

The third batch expands beyond those 50 prior input rows into a smaller municipal-employer tier while preserving population, employer-scale, and geographic variation. It is a scout-planning input. Likely source availability and matched-cycle value are hypotheses for a later live scout and later verification, not established facts.

## Authoritative local inputs

- `national_municipality_universe.csv`: authoritative employer name, municipality ID, Census government ID, government/geography type, population, and county-relationship count.
- `national_scout_coverage_municipality_2026-07-20.csv`: current successful, empty-result, and failure-only scout statuses.
- `national_municipality_county_crosswalk.csv`: all municipality-county relationships and primary-county context.
- `national_batch01_il25_scout_input_2026-07-20.csv`: all 25 first-batch IDs, including Bloomington, to exclude.
- `national_batch01_il25_2_scout_input_2026-07-20.csv`: all 25 second-batch IDs to exclude.
- `national_scout_candidate_queue_2026-07-20.csv`: exclusion check for municipalities already represented by scout candidates.
- `next_wave_municipality_scout_manifest_2026-07-16.csv`: priority context. Its five Illinois rows were all included in IL25 and are already successfully covered.

No live website, source URL, PDF, external dataset, or new verification finding was consulted.

## Hard exclusion gate

The reproducible builder rejects a proposed row unless all of the following hold:

1. State is Illinois.
2. Census classification is `government_type=municipal` and `geography_type=place`.
3. Formal government name begins `CITY OF` or `VILLAGE OF`.
4. Current status is `scout_coverage_status=not_scouted`.
5. `failed_connection_attempt_count=0`.
6. Municipality ID is absent from all 25 IL25 rows.
7. Municipality ID is absent from all 25 IL25.2 rows.
8. Municipality ID is absent from the national scout candidate queue.
9. `already_in_corpus=no`.
10. Every county-crosswalk relationship reconciles to the authoritative relationship count.

The builder separately asserts the prior status distributions. IL25 must remain 23 candidate-positive, one parseable empty (Champaign), and one failure-only row (Bloomington). IL25.2 must remain 22 candidate-positive and three parseable empty. Bloomington must remain the failure-only municipality and cannot enter IL25.3.

## Selected municipalities and controlled buckets

| Rank | Municipality | Bucket | Selection role |
|---:|---|---|---|
| 1 | Lombard | `large_city_state_anchor` | Largest untouched city/village municipal employer after IL25.2; DuPage third-tier anchor |
| 2 | Buffalo Grove | `large_city_state_anchor` | Large Cook/Lake multi-county municipal comparison |
| 3 | Park Ridge | `large_city_state_anchor` | Large independent Cook County city employer |
| 4 | Streamwood | `large_city_state_anchor` | Large northwest Cook village comparison |
| 5 | Wheeling | `large_city_state_anchor` | Large Cook/Lake multi-county comparison |
| 6 | Calumet City | `mid_city_comparison_candidate` | South Cook industrial-border municipal comparison |
| 7 | Northbrook | `mid_city_comparison_candidate` | North Cook independent municipal employer |
| 8 | St. Charles | `mid_city_comparison_candidate` | Fox River Kane/DuPage municipal comparison |
| 9 | Mundelein | `mid_city_comparison_candidate` | Northern Lake County comparison |
| 10 | Elk Grove Village | `mid_city_comparison_candidate` | Cook/DuPage employment-center comparison |
| 11 | North Chicago | `mid_city_comparison_candidate` | Lake County city near a federal installation, with federal substitution explicitly excluded |
| 12 | Highland Park | `mid_city_comparison_candidate` | North-shore municipal-employer contrast |
| 13 | Batavia | `regional_diversity_candidate` | Kane/DuPage Fox River continuity with a distinct employer |
| 14 | Edwardsville | `regional_diversity_candidate` | Madison County and Metro East administrative setting |
| 15 | Belvidere | `regional_diversity_candidate` | Boone County northwest industrial setting |
| 16 | Kankakee | `regional_diversity_candidate` | Kankakee County regional center |
| 17 | Ottawa | `regional_diversity_candidate` | LaSalle County north-central regional center |
| 18 | Jacksonville | `regional_diversity_candidate` | Morgan County west-central comparison |
| 19 | Marion | `regional_diversity_candidate` | Williamson County southern Illinois comparison |
| 20 | East Peoria | `continuity_with_il25_candidate` | Independent counterpart to IL25 Peoria |
| 21 | East Moline | `continuity_with_il25_candidate` | Independent counterpart to IL25 Moline and IL25.2 Rock Island |
| 22 | Sycamore | `continuity_with_il25_2_candidate` | Independent counterpart to IL25.2 DeKalb |
| 23 | Alton | `continuity_with_il25_2_candidate` | Independent Madison County counterpart to IL25.2 Granite City |
| 24 | Rolling Meadows | `clean_municipal_employer_candidate` | Smaller northwest Cook city-employer contrast |
| 25 | Mattoon | `clean_municipal_employer_candidate` | Smaller Coles County east-central contrast |

Bucket totals are:

| Selection bucket | Rows |
|---|---:|
| `large_city_state_anchor` | 5 |
| `mid_city_comparison_candidate` | 7 |
| `regional_diversity_candidate` | 7 |
| `continuity_with_il25_candidate` | 2 |
| `continuity_with_il25_2_candidate` | 2 |
| `clean_municipal_employer_candidate` | 2 |
| **Total** | **25** |

Continuity identifies a nearby independent municipal employer that may be useful for later comparison. It does not transfer source, cycle, candidate, verification, ingestion, canonical, codified, or claim status from the earlier municipality.

## Geographic and scale profile

The batch contains 18 cities and seven villages. Population ranges from 16,560 in Mattoon to 43,779 in Lombard; the 25 rows sum to 705,449 residents in the authoritative universe. Five municipalities are multi-county. The batch preserves 30 municipality-county relationships across 14 counties:

Boone, Coles, Cook, DeKalb, DuPage, Kane, Kankakee, LaSalle, Lake, Madison, Morgan, Rock Island, Tazewell, and Williamson.

County names are prompt context only and cannot substitute for the selected municipal employer. No county, school district, township, park district, transit agency, housing authority, fire/water district, other special district, university, federal installation, regional body, or private provider is selected as the target employer.

## Reproducibility and stage boundary

Run:

```bash
.venv/bin/python scripts/build_national_batch01_il25_3_scout_input.py
```

The builder asserts the exact order, 25 unique municipality and Census IDs, controlled bucket counts, city/village identity, untouched status, zero failure history, no overlap with IL25 or IL25.2, Bloomington exclusion, no queue/canonical overlap, complete county joins, and CSV parse-back schema.

Every row is `recommended_scout_status=ready_for_scout`, `already_scouted_status=no`, and `coverage_status_before_run=not_scouted`. These are scout-planning statuses only. A future live run requires separate authorization and a new successful direct-SDK synthetic smoke preflight. Any returned rows must remain unverified until a later coordinated verification wave.
