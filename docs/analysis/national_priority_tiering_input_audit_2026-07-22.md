# National Municipality Priority Tiering Input Audit

Date: 2026-07-22

Starting commit: `bb0c5eae3411cbe741ee1ea331d91092d8625fa9` (`Run Wave 2 serialized 150-row scout`)

Disposition: **PASS — the authoritative universe contains only the two intended employer classes and has complete unique identity, population, and county linkage. Scoring may proceed offline.**

## Authoritative inputs selected

The dated filenames remain the current canonical discovery-accounting outputs. This is established by `scripts/build_national_scout_candidate_queue.py`, `scripts/build_national_scout_coverage_status.py`, the latest handoff, and the 2026-07-22 `coverage_as_of` / `last_updated` fields—not inferred from the filename alone.

| Role | File | Current rows | Authority used |
|---|---|---:|---|
| Municipality-employer universe | `docs/analysis/national_municipality_universe.csv` | 35,589 | Census-derived identity, type, geography, population, active status, and primary-county count |
| Municipality-county relationships | `docs/analysis/national_municipality_county_crosswalk.csv` | 36,816 associations | County names/GEOIDs, primary relationship, and multi-county context |
| Current municipality scout status | `docs/analysis/national_scout_coverage_municipality_2026-07-20.csv` | 35,589 | Current 2026-07-22 operational coverage, candidate counts, canonical overlap, and failure accounting |
| Candidate queue | `docs/analysis/national_scout_candidate_queue_2026-07-20.csv` | 1,009 | Current unverified candidate and later-verification triage rows |
| State outcomes | `docs/analysis/national_scout_coverage_state.csv` | 51 | Current state/DC successful, empty, failure, candidate, unit-type, and likely-triad totals |
| County outcomes | `docs/analysis/national_scout_coverage_county.csv` | 3,144 | Current municipality-county association coverage; not additive nationally |
| Canonical status | current municipality coverage, sourced from universe/canonical build | 19 municipality rows | Exact existing-corpus flag only; no new canonical inference |

`data/contracts.csv` and `data/city_coverage.csv` were read only as project context and were not changed. The scorer uses the current canonical flag already propagated into municipality coverage rather than constructing fuzzy name matches.

## Universe structure

- Total rows: **35,589**
- Unique municipality IDs: **35,589**
- Unique Census government IDs: **35,589**
- States plus DC: **51**
- Active rows: **35,589 `Y`; zero inactive rows**
- Municipal/place governments: **19,471**
- Township/county-subdivision governments: **16,118**
- Other government/geography pairs: **zero**

The universe therefore contains only its intended municipal and township employer categories. It contains no county, school district, transit authority, port/airport authority, housing authority, industrial district, special district, university, or private-provider row. Some consolidated or legally unusual municipal names contain terms such as “city and county,” but authoritative `government_type` and `geography_type`—not name tokens—control scope.

## Available columns

The universe supplies state/state FIPS, municipality label and two stable IDs, formal government name, government/geography type, political description, local geography FIPS, population and vintage, active status, primary county GEOID, relationship count, multi-county flag, historical project/corpus indicators, a government-website field, source lineage, and notes.

The crosswalk supplies every municipality's associated county GEOID/name, county-equivalent type, primary relationship, relationship source/vintage/basis, and identity fields. Current coverage adds successful/empty/failure status, run/wave/backend/date lineage, candidate and unit-type counts, likely-triad signal, verification-queue counts, calibration/canonical status, and failure-attempt accounting.

## Availability and missingness

### Population

- Present: **35,589 / 35,589**
- Missing: **0**
- Minimum: **0**
- Maximum: **8,258,035**
- Zero values: **8**; retained as observed, not replaced
- Population year: 35,579 rows use 2023; ten rows use other recorded vintages (2006, 2019, 2022, 2024, or 2025)

The score uses the recorded population and never invents a replacement. The builder and tests fail safely to a zero population component and low confidence if a future input is missing.

### County context

- Crosswalk associations: **36,816**
- Unique municipality IDs represented: **35,589 / 35,589**
- Universe rows with relationship count: **35,589 / 35,589**
- Multi-county municipalities: **1,106**
- Single-county municipalities: **34,483**

County coverage counts municipality-county associations, so multi-county governments appear more than once. The scorer uses each municipality's mean associated-county coverage gap and never sums county rows as though they were unique municipalities.

### Current scout and queue status

- Successfully covered with candidates: **391**
- Successfully covered with parseable empty results: **113**
- Successful scout-covered total: **504**
- Failure-only municipalities: **10**
- Ordinary not-scouted status: **35,075**
- Candidate queue rows: **1,009**
- Candidate-positive municipality IDs represented in queue: **391**
- Likely-triad scout labels: **157 municipalities**
- Already canonical: **19 municipalities**

The queue currently contains candidates only from CA, IL, MA, NJ, NY, PA, and TX. These seven states have successful scout evidence; the other 44 states/DC positions have no successful state sample and must not receive an unsmoothed empirical rate.

## State-level yield variables available

For every state/DC the current state output provides universe and covered counts; candidate-positive and parseable-empty outcomes; failure-only municipalities and attempt counts; candidate rows; police, fire, and non-safety candidate presence counts; likely-triad labels; later-verification counts; and current token/cost fields where available. Municipality coverage permits an exact state count of rows with any police/fire candidate.

These are source-discovery outcomes only. Candidate-positive, unit-type, and likely-triad labels remain unverified and are used as operational scheduling signals, never as verified matched sets or substantive evidence.

## Stale or conflicting fields

- The universe's legacy `already_scouted` flag covers only 25 early rows, while current coverage records 504 successful outcomes. Current municipality coverage is authoritative for all operational status.
- The universe's legacy `scout_positive_status` likewise predates the national waves and is not used for current scoring.
- The filenames ending `2026-07-20` are current build targets with 2026-07-22 internal dates. Internal dates and builder paths govern.
- Population vintage is mostly 2023 but mixed for ten rows; no undocumented harmonization is attempted.
- Government website is present for 13,960 rows and blank for 21,629. It is not scored because presence is not portal quality, recency, or verified source availability, and this task forbids opening URLs.

## Variables not available and not inferred

The inputs do not establish municipal workforce size; police or fire department existence; contracted-service arrangements; unionization; bargaining coverage; number of bargaining units; state/local labor-law applicability; verified portal quality; collective-bargaining agreement availability; signed/executed document status; wage schedules; cycle overlap; metropolitan status; fiscal capacity; internet accessibility; verification burden; or wage gaps. No external data, name heuristic, model, URL inspection, or undocumented assumption fills these gaps.

The resulting tiers are therefore a transparent research-operational ordering under observed population, employer type, geographic context, and smoothed scout evidence—not factual classifications of labor institutions or document availability.
