# Parallel Worker 01 CA25.2 Selection Methodology

Date: 2026-07-21

Worker: `parallel_worker_01`

Stage: `stage_1_two_parallel_25`

Status: locked input preparation only. No dry run, smoke, model/API call, live scout, URL review, source verification, ingestion, codification, queue rebuild, or coverage rebuild occurred in this task.

## Result

Worker 01 contains exactly 25 untouched California municipal/place employers:

1. Irvine
2. Santa Ana
3. Huntington Beach
4. Glendale
5. Ontario
6. Elk Grove
7. Oceanside
8. Garden Grove
9. Corona
10. Roseville
11. Hayward
12. Sunnyvale
13. Escondido
14. Pomona
15. Fullerton
16. Torrance
17. Pasadena
18. Santa Clara
19. Clovis
20. Concord
21. Fairfield
22. Richmond
23. San Luis Obispo
24. Davis
25. Eureka

The rows span 15 counties, populations from 25,734 to 314,621, and a total represented population of 3,791,054. Buckets are eight `large_city_state_anchor`, ten `mid_city_comparison_candidate`, five `regional_diversity_candidate`, and two `clean_municipal_employer_candidate` rows.

## Authoritative inputs and exclusions

`national_municipality_universe.csv` supplied the employer identity, municipality ID, Census government ID, government/geography type, and population. `national_municipality_county_crosswalk.csv` supplied every county association. `national_scout_coverage_municipality_2026-07-20.csv` supplied the locked pre-run discovery status. The national queue and manifest were read as exclusion/priority context.

The builder requires every row to be:

- `government_type=municipal`;
- `geography_type=place`;
- `scout_coverage_status=not_scouted`;
- zero prior failed connection attempts;
- absent from the national scout candidate queue;
- absent from the canonical corpus context flag;
- unique by municipality ID and Census government ID; and
- represented by the exact county relationship count in the authoritative crosswalk.

The batch excludes all 21 successfully covered CA25 municipalities and the four CA25 failure-only rows Oakland, Stockton, Oxnard, and Redding. It also excludes Bloomington, Illinois by the cross-task failure-name guard. All California manifest anchors were already successfully scouted in CA25, so there was no untouched California manifest anchor to carry forward.

No school district, county, township, transit agency, port/airport authority, housing authority, park district, other special district, or private provider is included. Every selected government name is the authoritative `CITY OF ...` municipal/place record.

## Selection logic

CA25.2 is appropriate for one side of the first parallel test because CA25 already established that the direct-SDK path can produce substantial California municipal candidate volume, while its four separated timeouts provide a real concurrency-risk benchmark. The timeout rows are deliberately not retried. Pairing California with a different state prevents both workers from depending on the same source environment.

The first 18 rows emphasize large and medium untouched cities with likely municipal police and ordinary-civilian wage-setting relevance. The remainder broadens the geography across the Central Valley, Contra Costa/Solano, Central Coast, Yolo County, and far northern California. San Luis Obispo, Davis, and Eureka prevent a pure large-metro batch.

Selection did not verify whether each city directly employs both police and fire. The prompt therefore requires exact employer matching: a police or fire unit supplied by a county, authority, district, regional body, or private provider must not be attributed to the city. A city can still yield a useful matched set from one exact municipal safety unit plus one ordinary municipal civilian unit. Parseable empty output is allowed where the exact-employer constraint leaves no qualifying lead.

## Locked identity table

| Rank | Municipality | Municipality ID | Census government ID | Government name | Population | County |
|---:|---|---|---:|---|---:|---|
| 1 | Irvine | `cog_2025_161229` | `161229` | CITY OF IRVINE | 314,621 | Orange |
| 2 | Santa Ana | `cog_2025_100711` | `100711` | CITY OF SANTA ANA | 310,539 | Orange |
| 3 | Huntington Beach | `cog_2025_100709` | `100709` | CITY OF HUNTINGTON BEACH | 192,129 | Orange |
| 4 | Glendale | `cog_2025_161170` | `161170` | CITY OF GLENDALE | 187,050 | Los Angeles |
| 5 | Ontario | `cog_2025_161246` | `161246` | CITY OF ONTARIO | 182,457 | San Bernardino |
| 6 | Elk Grove | `cog_2025_200728` | `200728` | CITY OF ELK GROVE | 178,444 | Sacramento |
| 7 | Oceanside | `cog_2025_161256` | `161256` | CITY OF OCEANSIDE | 170,020 | San Diego |
| 8 | Garden Grove | `cog_2025_193114` | `193114` | CITY OF GARDEN GROVE | 168,234 | Orange |
| 9 | Corona | `cog_2025_207593` | `207593` | CITY OF CORONA | 160,238 | Riverside |
| 10 | Roseville | `cog_2025_123137` | `123137` | CITY OF ROSEVILLE | 159,135 | Placer |
| 11 | Hayward | `cog_2025_161123` | `161123` | CITY OF HAYWARD | 155,675 | Alameda |
| 12 | Sunnyvale | `cog_2025_161281` | `161281` | CITY OF SUNNYVALE | 151,967 | Santa Clara |
| 13 | Escondido | `cog_2025_161255` | `161255` | CITY OF ESCONDIDO | 148,122 | San Diego |
| 14 | Pomona | `cog_2025_161179` | `161179` | CITY OF POMONA | 145,502 | Los Angeles |
| 15 | Fullerton | `cog_2025_161218` | `161218` | CITY OF FULLERTON | 139,250 | Orange |
| 16 | Torrance | `cog_2025_207583` | `207583` | CITY OF TORRANCE | 139,224 | Los Angeles |
| 17 | Pasadena | `cog_2025_207582` | `207582` | CITY OF PASADENA | 133,560 | Los Angeles |
| 18 | Santa Clara | `cog_2025_161280` | `161280` | CITY OF SANTA CLARA | 131,062 | Santa Clara |
| 19 | Clovis | `cog_2025_203966` | `203966` | CITY OF CLOVIS | 125,826 | Fresno |
| 20 | Concord | `cog_2025_161132` | `161132` | CITY OF CONCORD | 122,315 | Contra Costa |
| 21 | Fairfield | `cog_2025_100750` | `100750` | CITY OF FAIRFIELD | 120,768 | Solano |
| 22 | Richmond | `cog_2025_161135` | `161135` | CITY OF RICHMOND | 114,106 | Contra Costa |
| 23 | San Luis Obispo | `cog_2025_161261` | `161261` | CITY OF SAN LUIS OBISPO | 49,244 | San Luis Obispo |
| 24 | Davis | `cog_2025_161303` | `161303` | CITY OF DAVIS | 65,832 | Yolo |
| 25 | Eureka | `cog_2025_161150` | `161150` | CITY OF EUREKA | 25,734 | Humboldt |

## Future execution boundary

Worker 01 must use this CSV without substitution. It must operate in its own worktree/copy, run a prompt-only dry review first, then a separately authorized direct-SDK no-search smoke, and only then the exact CA25.2 live run. Internal `n_parallels` remains one. The worker must not update the national queue or coverage; the later coordinator owns the combined rebuild after both Stage 1 relays are available.
