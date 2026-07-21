# Parallel Worker 02 NJ25 Selection Methodology

Date: 2026-07-21

Worker: `parallel_worker_02`

Stage: `stage_1_two_parallel_25`

Status: locked input preparation only. No dry run, smoke, model/API call, live scout, URL review, source verification, ingestion, codification, queue rebuild, or coverage rebuild occurred in this task.

## Result

Worker 02 contains exactly 25 untouched New Jersey municipal/place employers:

1. Paterson
2. Elizabeth
3. Princeton
4. Clifton
5. Bayonne
6. East Orange
7. Passaic
8. Union City
9. Vineland
10. Hoboken
11. New Brunswick
12. Perth Amboy
13. Plainfield
14. West New York
15. Hackensack
16. Sayreville
17. Linden
18. Fort Lee
19. Kearny
20. Atlantic City
21. Fair Lawn
22. Long Branch
23. Garfield
24. Rahway
25. Morristown

The rows span 11 counties, populations from 20,571 to 156,452, and a total represented population of 1,422,443. Buckets are two `national_manifest_anchor`, seven `large_city_state_anchor`, eight `mid_city_comparison_candidate`, six `regional_diversity_candidate`, and two `clean_municipal_employer_candidate` rows.

## Authoritative inputs and exclusions

The municipality universe supplied exact employer identity and IDs; the current municipality coverage table supplied the pre-run scout state; the county crosswalk supplied all county context; and the national manifest and queue supplied priority and exclusion context.

Every row is asserted to be `municipal` / `place`, `not_scouted`, zero-failure, absent from the current queue, absent from the canonical corpus context flag, and unique by municipality and Census government ID. All county relationship counts reconcile to the crosswalk.

Newark, Jersey City, and Camden are excluded because they were already successfully scout-covered. No recent timeout-only municipality is included. Trenton is untouched by the scout, but it is excluded from this new-discovery batch because it already has canonical corpus context; Princeton preserves Mercer County diversity without creating an avoidable canonical-overlap burden.

The national manifest's untouched New Jersey rows include Edison, Woodbridge, Lakewood, Hoboken, and Atlantic City. Edison, Woodbridge, and Lakewood are authoritative township-government rows and are prohibited by this task. Hoboken and Atlantic City are municipal/place employers and are included as the two eligible untouched manifest anchors.

No school district, county, township government, transit agency, port/airport authority, housing authority, park district, other special district, or private provider is included. New Jersey's city, town, borough, village, and municipality labels are accepted only where the authoritative universe records `government_type=municipal` and `geography_type=place`.

## Selection logic

NJ25 provides an East Coast and institutionally distinct complement to CA25.2. The earlier three-city NJ direct-SDK run completed 3/3 and produced eight unverified leads, showing that the transport and prompt can operate in this state without claiming that the new municipalities will have the same source quality. New Jersey also offers state labor-board/PERC context, dense municipal government, and city/town/borough variation. That contrasts with California's larger geographic and portal heterogeneity and reduces correlated source-quality risk across the two workers.

The batch begins with the largest untouched cities, retains the two eligible national-manifest anchors, and then adds medium and smaller employers across Passaic, Union, Mercer, Hudson, Essex, Cumberland, Middlesex, Bergen, Atlantic, Monmouth, and Morris counties. University, port, casino/private, county, transit, and authority substitutions are called out where locally salient, but no source was opened and no source/employment structure was verified during selection.

## Locked identity table

| Rank | Municipality | Municipality ID | Census government ID | Government name | Population | County |
|---:|---|---|---:|---|---:|---|
| 1 | Paterson | `nj_paterson` | `184046` | CITY OF PATERSON | 156,452 | Passaic |
| 2 | Elizabeth | `cog_2025_204933` | `204933` | CITY OF ELIZABETH | 135,829 | Union |
| 3 | Princeton | `cog_2025_170189` | `170189` | MUNICIPALITY OF PRINCETON | 30,289 | Mercer |
| 4 | Clifton | `cog_2025_225827` | `225827` | CITY OF CLIFTON | 88,461 | Passaic |
| 5 | Bayonne | `cog_2025_208765` | `208765` | CITY OF BAYONNE | 70,300 | Hudson |
| 6 | East Orange | `cog_2025_170167` | `170167` | CITY OF EAST ORANGE | 69,556 | Essex |
| 7 | Passaic | `cog_2025_130867` | `130867` | CITY OF PASSAIC | 68,903 | Passaic |
| 8 | Union City | `cog_2025_109091` | `109091` | CITY OF UNION CITY | 64,462 | Hudson |
| 9 | Vineland | `cog_2025_170164` | `170164` | CITY OF VINELAND | 60,797 | Cumberland |
| 10 | Hoboken | `cog_2025_130839` | `130839` | CITY OF HOBOKEN | 57,010 | Hudson |
| 11 | New Brunswick | `cog_2025_193736` | `193736` | CITY OF NEW BRUNSWICK | 55,846 | Middlesex |
| 12 | Perth Amboy | `cog_2025_170194` | `170194` | CITY OF PERTH AMBOY | 55,249 | Middlesex |
| 13 | Plainfield | `cog_2025_130872` | `130872` | CITY OF PLAINFIELD | 54,670 | Union |
| 14 | West New York | `cog_2025_170180` | `170180` | TOWN OF WEST NEW YORK | 50,754 | Hudson |
| 15 | Hackensack | `cog_2025_184024` | `184024` | CITY OF HACKENSACK | 45,736 | Bergen |
| 16 | Sayreville | `cog_2025_186549` | `186549` | BOROUGH OF SAYREVILLE | 45,496 | Middlesex |
| 17 | Linden | `cog_2025_190901` | `190901` | CITY OF LINDEN | 43,950 | Union |
| 18 | Fort Lee | `cog_2025_211389` | `211389` | BOROUGH OF FORT LEE | 39,700 | Bergen |
| 19 | Kearny | `cog_2025_170179` | `170179` | TOWN OF KEARNY | 39,370 | Hudson |
| 20 | Atlantic City | `cog_2025_130810` | `130810` | CITY OF ATLANTIC CITY | 38,464 | Atlantic |
| 21 | Fair Lawn | `cog_2025_170118` | `170118` | BOROUGH OF FAIR LAWN | 35,564 | Bergen |
| 22 | Long Branch | `cog_2025_130855` | `130855` | CITY OF LONG BRANCH | 32,745 | Monmouth |
| 23 | Garfield | `cog_2025_170120` | `170120` | CITY OF GARFIELD | 32,456 | Bergen |
| 24 | Rahway | `cog_2025_109127` | `109127` | CITY OF RAHWAY | 29,813 | Union |
| 25 | Morristown | `cog_2025_170213` | `170213` | TOWN OF MORRISTOWN | 20,571 | Morris |

## Future execution boundary

Worker 02 must use this exact input without substitution in its own worktree/copy. It must pass a prompt-only dry review and a separately authorized direct-SDK no-search smoke before any live call. The future live run stays serial within the worker, and the worker may write only NJ25 batch artifacts. It must not rebuild national queue/coverage; the coordinator imports both Stage 1 relays and rebuilds once.
