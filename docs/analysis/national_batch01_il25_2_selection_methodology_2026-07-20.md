# Illinois National Batch 01 IL25.2 Selection Methodology

Date: 2026-07-20

Stage: municipal selection and scout-input preparation only. This task did not run a model/API call, open source URLs, verify or download documents, ingest sources, codify text, edit canonical data, or create claim evidence.

## Purpose

IL25.2 is the second 25-municipality Illinois state-scale discovery slice. The first IL25 run covered the state's largest anchors and produced 76 unverified candidates from 24 successful responses. Bloomington timed out without a model response and remains a failure-only attempt. This second batch expands Illinois breadth without repeating any IL25 row or treating Bloomington as ready for immediate retry.

The selection favors the next tier of medium and smaller municipal employers, balanced across metropolitan, outer-suburban, central, western, eastern, and Metro East settings. It remains a discovery input: source availability and matched-cycle quality are hypotheses to test later, not verified facts.

## Authoritative inputs

- `national_municipality_universe.csv`: authoritative employer identity, municipality ID, Census government ID, government type, geography type, population, and county-relationship count.
- `national_scout_coverage_municipality_2026-07-20.csv`: current successful, empty-result, and failure-only scout statuses.
- `national_municipality_county_crosswalk.csv`: every municipality-county relationship and primary-county marker.
- `national_batch01_il25_scout_input_2026-07-20.csv`: all 25 first-batch IDs to exclude.
- `national_batch01_il25_live_direct_sdk_scout_review_2026-07-20.md`: confirmation that 23 IL25 municipalities returned candidates, Champaign returned a parseable empty list, and Bloomington was failure-only.
- `next_wave_municipality_scout_manifest_2026-07-16.csv`: priority context. Its five Illinois rows—Chicago, Aurora, Rockford, Springfield, and Naperville—were all already in IL25 and successfully covered, so IL25.2 deliberately continues beyond the manifest.
- `national_scout_candidate_queue_2026-07-20.csv`: exclusion check for municipalities with an existing scout candidate row.

No live website, source URL, PDF, or external dataset was consulted.

## Hard exclusion gate

The reproducible builder rejects a proposed row unless all of the following are true:

1. State is Illinois.
2. Census classification is `government_type=municipal` and `geography_type=place`.
3. Government name begins `CITY OF` or `VILLAGE OF`; towns and township governments are not selected.
4. `scout_coverage_status=not_scouted`.
5. `failed_connection_attempt_count=0`.
6. Municipality ID is absent from all 25 prior IL25 rows.
7. Municipality ID is absent from the national candidate queue.
8. `already_in_corpus=no`.
9. Every county-crosswalk relationship reconciles to the authoritative relationship count.

The builder separately asserts the prior IL25 status distribution: 23 `scouted_with_candidates`, one `scouted_no_candidates` municipality (Champaign), and one `scout_attempt_failed_connection` municipality (Bloomington). Bloomington must remain the failure-only row and cannot enter IL25.2.

## Selection logic

The first 12 rows retain the largest eligible municipal employers after excluding IL25, Bloomington, and Cicero. Cicero is Census-classified as a municipal place but has the formal name `TOWN OF CICERO`; it was not selected because this batch deliberately uses unambiguous city/village employers and avoids township-boundary confusion.

The remaining rows broaden the batch beyond Cook and DuPage counties. Seven regional-diversity rows cover McHenry, DeKalb, Kane, Kendall/Will, Peoria/Tazewell, Vermilion, and Madison settings. Four continuity rows provide distinct employers near earlier IL25 targets without repeating them:

- Urbana alongside Champaign, whose completed prompt returned no candidates;
- Rock Island alongside Moline;
- O'Fallon alongside Belleville;
- Loves Park alongside Rockford.

Continuity means a nearby independent employer useful for later comparison. It does not transfer any source, cycle, or verification status from the IL25 municipality.

The final two rows, Galesburg and Freeport, preserve smaller clean city-employer contrasts in western and northwest Illinois.

## Controlled bucket counts

| Selection bucket | Rows | Role |
|---|---:|---|
| `large_city_state_anchor` | 5 | Largest eligible second-tier Illinois city/village employers |
| `mid_city_comparison_candidate` | 7 | Medium-large independent municipal-employer comparisons |
| `regional_diversity_candidate` | 7 | Outer-metropolitan and non-Chicago regional coverage |
| `continuity_with_il25_candidate` | 4 | Independent employers linked geographically to IL25 settings |
| `clean_municipal_employer_candidate` | 2 | Smaller city-employer and scale contrasts |
| **Total** | **25** | |

Fourteen rows are cities and 11 are villages. None is a county, township government, school district, transit agency, housing authority, park district, fire/water district, other special district, university, regional body, or private employer.

## Geographic and scale balance

Population ranges from 23,136 in Freeport to 74,495 in Arlington Heights; the 25 rows sum to 1,047,857 residents in the authoritative universe. The batch contains 31 municipality-county relationships across 18 counties:

Boone, Champaign, Cook, DeKalb, DuPage, Kane, Kendall, Knox, Madison, McHenry, Peoria, Rock Island, St. Clair, Stephenson, Tazewell, Vermilion, Will, and Winnebago.

Hoffman Estates, Plainfield, Elmhurst, Oswego, Pekin, and Loves Park have two county relationships. Every relationship is retained in `county_context_summary`; county geography is context only and cannot substitute for the target municipal employer.

## Reproducibility and stage boundary

Run:

```bash
.venv/bin/python scripts/build_national_batch01_il25_2_scout_input.py
```

The builder asserts the exact municipality order, 25 unique IDs, controlled bucket counts, city/village identity, untouched coverage, zero failure history, no IL25 overlap, no queue/canonical overlap, complete county joins, and CSV parse-back schema. It writes `national_batch01_il25_2_scout_input_2026-07-20.csv`.

Every row remains `recommended_scout_status=ready_for_scout`, `already_scouted_status=no`, and `coverage_status_before_run=not_scouted`. Those are scout-planning fields, not verification or ingestion decisions. A future live run requires separate authorization and a fresh successful direct-SDK synthetic smoke preflight. Returned rows must remain unverified until a later coordinated verification wave.
