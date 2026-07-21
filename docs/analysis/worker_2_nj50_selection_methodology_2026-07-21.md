# Worker 2 NJ50 Selection Methodology

Date: 2026-07-21

Status: locked offline-preparation input for a future coordinator-controlled serialized live queue. No live scout, API/model call, source opening, verification, ingestion, codification, or national queue/coverage rebuild occurred.

## Result

`worker_2_nj50_scout_input_2026-07-21.csv` contains exactly 50 unique New Jersey municipal/place governments. They are the 50 highest-population eligible city, borough, town, or village place governments after excluding current scout coverage, current queue municipalities, canonical municipalities, township governments, and timeout-only rows.

The ordered batch is: Westfield; Englewood; Bergenfield; Millville; Bridgeton; Paramus; Ridgewood; Lodi; Cliffside Park; Carteret; South Plainfield; Glassboro; North Plainfield; Summit; Roselle; Lindenwold; Elmwood Park; Secaucus; Pleasantville; Harrison; Palisades Park; Hawthorne; Point Pleasant; Tinton Falls; Rutherford; Dover; Dumont; New Milford; Madison; North Arlington; South River; Asbury Park; Phillipsburg; Tenafly; Metuchen; Highland Park; Fairview; Hammonton; Ramsey; Edgewater; Hopatcong; Middlesex; Collingswood; Somerville; Florham Park; Roselle Park; Eatontown; New Providence; Woodland Park; and Ridgefield Park.

## Authoritative inputs and manifest treatment

The selection uses the authoritative municipality universe, current municipality coverage, current candidate queue, next-wave manifest, and municipality-county crosswalk named in the task. The serialized recovery relay supplies the current operating and timeout boundary.

Every New Jersey manifest row was considered. Newark, Jersey City, Camden, Hoboken, and Atlantic City are already successfully covered. Edison, Woodbridge, and Lakewood remain unscouted but are Census township governments; the task expressly excludes township governments, so none can enter this batch. Princeton is a recent failure-only timeout and is also excluded. The result is therefore a new population-ranked place-government expansion rather than a manifest-only batch.

## Deterministic selection rule

Rows must be active Census `municipal` / `place` governments, `not_scouted`, have zero failed attempts, have no candidate-queue row, have no canonical overlap, and not be a prohibited timeout name. This automatically excludes New Jersey township governments represented as county subdivisions while retaining eligible incorporated place governments.

Eligible rows are sorted by descending 2023 population and municipality name, then the first 50 are locked. Ranks 1–15 are `largest_uncovered_place_employer`, ranks 16–35 are `mid_size_borough_city_expansion`, and ranks 36–50 are `regional_place_employer_expansion`.

The batch responds to the sparse serialized NJ25 result—12 candidate-positive, 12 parseable-empty, and one timeout—by expanding across additional exact municipal employers without retrying or treating an empty scout result as proof of source nonexistence. It remains a discovery-preparation batch, not source verification.

## Exact-employer and county controls

Each row carries the exact government name and Census ID. Future prompts must exclude counties, schools, authorities, districts, private providers, and any same-name township or statistical geography. A safety agreement cannot satisfy the ordinary non-safety request, and a county or regional safety unit cannot be attributed to the municipality.

Every crosswalk relationship is preserved in `county_context_summary`; relationship counts and Census IDs are asserted against the universe. The builder also asserts 50 unique rows, no overlap with Workers 1 or 3, no queue/canonical/coverage overlap, no failure-only row, and the exact locked order.

All rows remain `locked_for_worker_prep_dry_run_only`. Dry-run output is prompt-contract evidence only and does not confer discovery coverage.
