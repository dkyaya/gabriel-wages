# California National Batch 01 CA25 Selection Methodology

Date: 2026-07-20

Stage: municipal selection and scout-input preparation only. This work does not verify a source, open or download a document, submit a public-records request, ingest material, codify text, alter canonical data, or support a claim.

## Purpose and result

CA25 is a locked 25-municipality California source-discovery slice designed to add a large national contrast after successful IL25, NY25, IL25.2, and IL25.3 runs. It includes all five California anchors in the existing national manifest and extends beyond them to large, medium, regional, and cleaner smaller municipal employers. Expected source availability and police/fire/ordinary-civilian comparability are planning hypotheses for the scout and later verification, not established facts.

The selected order is: Los Angeles, Sacramento, San Diego, San Francisco, Fresno, San Jose, Long Beach, Oakland, Bakersfield, Anaheim, Riverside, Stockton, Chula Vista, Fremont, Modesto, Oxnard, Santa Rosa, Salinas, Vallejo, Redding, Chico, Visalia, Santa Barbara, Berkeley, and Palo Alto.

## Authoritative local inputs

- `national_municipality_universe.csv` supplies the authoritative municipality-employer universe, municipality IDs, Census government IDs, government/geography types, formal government names, population, and county-relationship counts.
- `national_scout_coverage_municipality_2026-07-20.csv` supplies current successful, empty-result, and failure-only scout statuses. All 483 California universe rows were `not_scouted` before this batch.
- `national_municipality_county_crosswalk.csv` supplies county context and reconciles every selected relationship.
- `next_wave_municipality_scout_manifest_2026-07-16.csv` supplies priority context. All five California manifest anchors are included: Los Angeles, Sacramento, San Diego, San Francisco, and Fresno.
- `national_scout_candidate_queue_2026-07-20.csv` supplies the exclusion check for municipalities already represented by scout candidates. It contained no California row before CA25.

No live municipal website, candidate source URL, PDF, external labor inventory, or new verification finding was used to select rows.

## Hard exclusion gate

The deterministic builder rejects a proposed row unless all of the following hold:

1. State is California.
2. The authoritative Census classification is `government_type=municipal` and `geography_type=place`.
3. The formal employer begins `CITY OF` or, for California's consolidated municipal structure, `CITY AND COUNTY OF`.
4. Current coverage is `scout_coverage_status=not_scouted`.
5. `failed_connection_attempt_count=0`; failure-only rows are not silently retried.
6. The municipality ID is absent from the national scout queue.
7. `already_in_corpus=no`.
8. Every county relationship reconciles to the authoritative relationship count.
9. All five California manifest anchors remain present.
10. Municipality IDs and Census government IDs are each unique across all 25 rows.

The batch contains no school district, county-only government, transit agency, housing authority, port or airport authority, park/recreation district, fire/water/utility district, other special district, regional body, university, state/federal employer, or private provider. San Francisco is the single California-specific consolidated case: the universe classifies the exact `CITY AND COUNTY OF SAN FRANCISCO` employer as a municipal place. The prompt excludes every other county or special-district substitute.

## Selected municipalities and controlled buckets

| Rank | Municipality | Bucket | Selection role |
|---:|---|---|---|
| 1 | Los Angeles | `claim_register_anchor` | Highest-priority California manifest anchor and largest municipal employer |
| 2 | Sacramento | `claim_register_anchor` | State-capital city employer and manifest anchor |
| 3 | San Diego | `claim_register_anchor` | Major southern full-service city and manifest anchor |
| 4 | San Francisco | `claim_register_anchor` | Consolidated city-and-county municipal structure and manifest anchor |
| 5 | Fresno | `claim_register_anchor` | Large Central Valley regional center and manifest anchor |
| 6 | San Jose | `large_city_state_anchor` | Major Bay Area municipal employer |
| 7 | Long Beach | `large_city_state_anchor` | Independent large Los Angeles County city employer |
| 8 | Oakland | `large_city_state_anchor` | Large East Bay safety/civilian comparison |
| 9 | Bakersfield | `large_city_state_anchor` | Large inland Kern County contrast |
| 10 | Anaheim | `large_city_state_anchor` | Large Orange County exact city-employer target |
| 11 | Riverside | `large_city_state_anchor` | Inland Empire city and county-seat setting |
| 12 | Stockton | `large_city_state_anchor` | Large Delta/San Joaquin Valley city employer |
| 13 | Chula Vista | `mid_city_comparison_candidate` | Independent San Diego County city comparison |
| 14 | Fremont | `mid_city_comparison_candidate` | East Bay high-income labor-market contrast |
| 15 | Modesto | `mid_city_comparison_candidate` | Stanislaus regional city employer |
| 16 | Oxnard | `mid_city_comparison_candidate` | Ventura coastal/industrial comparison |
| 17 | Santa Rosa | `mid_city_comparison_candidate` | North Bay regional center |
| 18 | Salinas | `mid_city_comparison_candidate` | Monterey agricultural-region city employer |
| 19 | Vallejo | `mid_city_comparison_candidate` | Solano fiscal and safety-labor setting |
| 20 | Redding | `regional_diversity_candidate` | Far northern regional center |
| 21 | Chico | `regional_diversity_candidate` | Northern Sacramento Valley comparison |
| 22 | Visalia | `regional_diversity_candidate` | Southern Central Valley comparison |
| 23 | Santa Barbara | `regional_diversity_candidate` | Central Coast comparison |
| 24 | Berkeley | `clean_municipal_employer_candidate` | Smaller organized East Bay city employer |
| 25 | Palo Alto | `clean_municipal_employer_candidate` | Smaller high-wage Santa Clara city employer |

Bucket totals are five `claim_register_anchor`, seven `large_city_state_anchor`, seven `mid_city_comparison_candidate`, four `regional_diversity_candidate`, and two `clean_municipal_employer_candidate` rows.

## Geographic and scale profile

The authoritative populations range from 65,882 in Palo Alto to 3,820,914 in Los Angeles and sum to 12,324,714. The 25 rows span 20 counties: Alameda, Butte, Fresno, Kern, Los Angeles, Monterey, Orange, Riverside, Sacramento, San Diego, San Francisco, San Joaquin, Santa Barbara, Santa Clara, Shasta, Solano, Sonoma, Stanislaus, Tulare, and Ventura. Each selected government has one county relationship in the current crosswalk.

The mix deliberately covers coastal and inland California, northern and southern regions, the Central Valley, the Bay Area, and multiple employer scales. County names are context only and cannot substitute for the exact municipal employer.

## Prompt and stage boundaries

Each row requests a police CBA, fire CBA, one ordinary general-municipal civilian CBA, and relevant public wage-setting mechanism material when available. Ordinary non-safety means clerical, public works, library, citywide civilian, or comparable municipal material; police, fire, EMS, corrections, dispatch, or another safety agreement cannot satisfy it. The prompt requires visible 2014-2024 cycle-year support, separates context-only from qualifying documents, separates blocked/unreadable from observed dead/unreachable, and permits a valid empty candidate list.

The row context also forbids making or recommending a CPRA/PRA or similar public-records request. Scout output remains `unverified` / `raw_model_output`; it does not become verification-stage, ingestion-stage, canonical, codified, or claim-stage evidence.

## Reproducibility

Run:

```bash
.venv/bin/python scripts/build_national_batch01_ca25_scout_input.py
```

The builder asserts exact order, 25 unique municipality and Census IDs, controlled bucket totals, all manifest anchors, permitted government/geography types, untouched coverage, zero failure history, no queue or canonical overlap, complete county joins, and CSV parse-back schema/order. Every row is `recommended_scout_status=ready_for_scout`, `already_scouted_status=no`, and `coverage_status_before_run=not_scouted` before the live gate.
