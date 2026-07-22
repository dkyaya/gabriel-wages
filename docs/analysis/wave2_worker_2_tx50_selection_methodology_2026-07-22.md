# Wave 2 Worker 2 TX50 Selection Methodology

Date: 2026-07-22

Status: **locked offline-preparation input for a future coordinator-controlled serialized live queue; scout-stage only**

## Result and state rationale

`wave2_worker_2_tx50_scout_input_2026-07-22.csv` contains exactly 50 unique active Texas municipal/place governments. Texas remains valuable despite a 69.8% current candidate-positive rate because only 53 of 1,224 municipalities are covered and the state directly probes the project’s institutional safety-versus-ordinary-civilian source gap. The batch continues beyond the first major-city wave into sizeable independent municipal employers.

The population range is 35,741–77,516; the selected places represent 2,470,505 residents. Eighteen are multi-county, producing 73 municipality-county relationships across 31 counties.

## Selection source files

- `docs/analysis/national_municipality_universe.csv`;
- `docs/analysis/national_scout_coverage_municipality_2026-07-20.csv`;
- `docs/analysis/national_scout_candidate_queue_2026-07-20.csv`;
- `docs/analysis/national_municipality_county_crosswalk.csv`;
- `data/contracts.csv` and `data/city_coverage.csv`; and
- `docs/analysis/national_scout_coverage_state.csv`, the claim register, and prior coordinator reviews for state rationale only.

These local files supply identity, eligibility, canonical context, and current yield. No URL, source, or external site was opened.

## Exclusion and ranking rule

The deterministic builder requires Texas, `active_status=Y`, `government_type=municipal`, `geography_type=place`, current `not_scouted`, zero failed-connection attempts, no queue or canonical/corpus overlap, and complete county reconciliation. The eight named timeout/failure rows are prohibited globally. Texas places sharing names such as Oakland, Princeton, or Redding are excluded too; the batch does not rely on same-name inference.

The target must be the exact city/town employer. Counties, school districts, transit agencies, housing authorities, port/airport authorities, park districts, township governments, industrial districts, fire/water/utility districts, other special districts, regional bodies, universities, state/federal employers, advisory bodies, and private providers cannot substitute. Eligible rows are sorted by population, then exact name and ID; the first 50 are locked.

## Selection buckets

| Bucket | Ranks | Rows | Purpose |
|---|---:|---:|---|
| `largest_remaining_place_employer` | 1–10 | 10 | Largest remaining exact municipal employers |
| `high_population_place_expansion` | 11–25 | 15 | Upper-tier independent city/town employers |
| `regional_municipal_employer_expansion` | 26–40 | 15 | Regional and suburban institutional contrasts |
| `smaller_place_employer_diversity` | 41–50 | 10 | Lower edge of the current sizeable-employer tier |

## Top 10 priorities

| Rank | Municipality | Population | Rationale |
|---:|---|---:|---|
| 1 | Cedar Park | 77,516 | Largest remaining clean TX place; two-county context |
| 2 | Missouri City | 76,773 | Large Fort Bend/Harris municipal employer |
| 3 | San Marcos | 71,569 | Three-county regional municipal employer |
| 4 | Harlingen | 71,510 | Cameron County regional center |
| 5 | North Richland Hills | 70,658 | Large Tarrant County employer |
| 6 | Rowlett | 66,813 | Dallas/Rockwall multi-county employer |
| 7 | Victoria | 65,800 | Independent regional center |
| 8 | Pflugerville | 65,301 | Travis/Williamson employer expansion |
| 9 | Kyle | 62,548 | Fast-growing Hays County employer |
| 10 | Wylie | 61,078 | Three-county suburban employer |

## Duplicate, canonical, coverage, and timeout checks

The file has 50 unique municipality IDs and Census IDs, one `worker_2`, one future queue ID, and all 50 are `not_scouted`. ID and exact state/name checks find zero queue overlap; exact state/name and corpus flags find zero canonical overlap. County contexts reconcile. None of Bloomington, Oakland, Stockton, Oxnard, Redding, Fairfield, Princeton, or Moreno Valley appears.

## Risks and expected source-discovery value

Texas’s collective-bargaining structure makes ordinary non-safety CBAs less common and increases the risk of parseable-empty outcomes, context-only pay-plan material, or wrong-employer district/provider substitution. The scout must not reinterpret institutional absence as permission to return schools, counties, advisory bodies, districts, or private providers. If no qualifying municipal bargaining source exists, an empty candidate list is correct.

At the current state average, 50 comparable municipalities imply roughly 35 candidate-positive outcomes and 80 candidate rows. This is an empirical planning reference only. Results remain unverified scout leads and cannot be ingested, codified, or used for claims without later exact-source verification.
