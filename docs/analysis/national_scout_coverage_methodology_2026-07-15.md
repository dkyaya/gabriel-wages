# National Scout Coverage Accounting Methodology (updated 2026-07-16)

## Purpose

This note defines the national municipality-employer universe, the municipality-to-county-equivalent crosswalk, and the scout-coverage accounting vocabulary. It is an accounting layer only. It does not verify sources, ingest documents, run GABRIEL scout calls, or codify text.

## Public source of record

The municipality universe uses the U.S. Census Bureau **2025 Government Units Listing**, published September 24, 2025:

- landing page: `https://www.census.gov/data/datasets/2025/econ/gus/public-use-files.html`
- direct public-use archive: `https://www2.census.gov/programs-surveys/gus/datasets/2025/gov_units_2025.zip`
- source file: `Govt_Units_2025_Final.xlsx`, `General Purpose` tab

The listing is a snapshot of the Census Bureau's Governments Master Address File (GMAF), retrieved August 28, 2025, and covers independent government units active as of the fiscal year ending June 30, 2025. The General Purpose tab contains county, municipal, and township governments. It is a government/employer inventory, not simply a list of named population places.

Jurisdiction state is derived from `FIPS_STATE`, not the workbook's `STATE` field. The latter belongs to the government contact's mailing address and can be out of state. A July 16, 2026 reconciliation found 38 active municipal/township governments where those fields differ, including Auburn Township in Susquehanna County, Pennsylvania, whose contact mailing address is in Oregon. The builder now enforces agreement between each output `state` and `state_fips` so mailing geography cannot alter the employer universe by state.

The source has 38,704 general-purpose rows: 3,031 county, 19,489 municipal, and 16,184 township governments. The `ACTIVE` field distinguishes functionally active (`Y`) from dormant (`N`) units. Dormant units remain legally extant in Census inventory but have no activity, revenue, or current officers.

## Explicit scope decision for labor-contract scouting

The national municipality universe includes:

- `UNIT_TYPE = 2 - MUNICIPAL` and `ACTIVE = Y`;
- `UNIT_TYPE = 3 - TOWNSHIP` and `ACTIVE = Y`;
- the 50 states plus the District of Columbia;
- composite/consolidated municipal-county governments when Census classifies the composite as municipal; and
- independent cities when Census classifies the city as municipal.

The universe excludes:

- ordinary county governments;
- dormant municipal or township governments (`ACTIVE = N`);
- census-designated places (CDPs), which are statistical places rather than independent municipal employers;
- inactive or dissolved incorporated places;
- school districts, special districts, dependent systems, and public pension systems; and
- Puerto Rico and the Island Areas, to retain the existing 50-state-plus-DC project scope.

This produces an employer-oriented scouting frame of **35,589 functionally active subcounty general-purpose governments**: 19,471 municipal and 16,118 township governments. Township governments are included because in New England, New York, New Jersey, Pennsylvania, and other township-government states they often provide the municipal-type services and employ the police, fire, public-works, and clerical units relevant to this project.

The scope is intentionally not “all incorporated places” and not “all county subdivisions.” It is the subset of government units Census classifies as independent municipal or township governments. This avoids treating CDPs, statistical MCDs, and nonfunctioning areas as potential collective-bargaining employers.

## Geography layers

- `county_universe`: the 3,144 counties and county-equivalents in the **2024 Census Gazetteer county file**, filtered to the 50 states plus DC. It includes Alaska boroughs/census areas, Connecticut planning regions, independent cities, and DC.
- `municipality_universe`: the 35,589 in-scope active municipal and township governments from the 2025 Government Units Listing. One row is one government/employer, identified by the Census six-digit government ID.
- `municipality_county_crosswalk`: one row per municipality-to-county-equivalent relationship. A municipality with four county relationships has four crosswalk rows but remains one municipality row.

These layers must not be collapsed. In particular, a county row is not a municipality and county activity does not imply that every municipality in that county has been scouted.

## Municipality-to-county-equivalent crosswalk

The 2025 Government Units Listing provides one `FIPS_COUNTY` value per government. Census documentation states that for a cross-county government this is the county area most served or the headquarters county. It is therefore retained as `government_units_primary_county_geoid`, but it is **not used to collapse multi-county municipalities**.

The full crosswalk is built as follows:

1. For municipal governments (`geography_type=place`), join `FIPS_STATE + FIPS_PLACE` to the official **2020 Census national place-by-county table**: `https://www2.census.gov/geo/docs/reference/codes2020/national_place_by_county2020.txt`. That table has one row for every place-county relationship and preserves all counties for a multi-county place.
2. For township governments (`geography_type=county_subdivision`), join `FIPS_STATE + FIPS_COUNTY + FIPS_PLACE` to the **2024 Census Gazetteer national county-subdivision file**: `https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2024_Gazetteer/2024_Gaz_cousubs_national.zip`. County subdivisions are nested in a county-equivalent, so this produces the current county relationship directly.
3. Retain only county GEOIDs present in the 2024 50-state-plus-DC county universe.
4. If a 2025 government has no current relationship from those two geographic tables, add its 2025 Government Units primary/headquarters county as a clearly labeled supplement instead of dropping the government. This is used for 95 relationships, principally Connecticut's post-2020 planning-region conversion and governments created or recoded after 2020.
5. Mark which crosswalk row equals the 2025 Government Units primary county. This is descriptive provenance only.

The resulting crosswalk has **36,816 relationship rows** for 35,589 governments. **1,106 municipalities are multi-county** and retain every relationship available from the source crosswalk; the maximum observed relationship count is five.

## Special geographies

### Multi-county municipalities

Multi-county municipalities have one universe row and multiple crosswalk rows. There is no “primary county only” analytical collapse. County rollups count the municipality in each associated county and therefore are not additive across counties.

### Independent cities

Independent cities are municipal-government rows and map to their own county-equivalent GEOID. The county universe explicitly classifies Baltimore, St. Louis, Carson City, and Virginia independent-city county equivalents as `independent_city`. They are not assigned to an adjacent county.

### Consolidated city-counties and composite governments

Census classifies consolidated or substantially merged municipal-county composites as municipal governments. They therefore remain one municipality/employer row. The exact source name is preserved in `government_name` (for example, `CITY AND COUNTY OF DENVER`), and the crosswalk links the unit to the corresponding county-equivalent. The universe does not add a duplicate ordinary county-government row.

### New England-style towns and county subdivisions

New England towns that Census classifies as township governments are included from the Government Units Listing, not inferred from every Census MCD. They use `geography_type=county_subdivision` and are mapped through the 2024 county-subdivision GEOID. Connecticut uses the current nine planning regions as county equivalents. A small number of Connecticut units require the labeled 2025 primary-county supplement because the national place-by-county reference is 2020 vintage.

### District of Columbia

DC is represented explicitly as one municipal government (`CITY OF WASHINGTON DC`, Census government ID `124214`) and one county-equivalent (`11001`, District of Columbia). It is not omitted merely because DC has no ordinary county government.

## Workflow-status vocabulary

The statuses remain sequential and separate:

1. `already_scouted` asks whether the municipality was queried by the GABRIEL source scout.
2. `scout_positive_status` asks whether that scout query returned any unverified candidate leads.
3. `verified_status` asks whether a candidate source passed the project's verification standard.
4. `ingested_status` asks whether a source from the municipality is present in `data/contracts.csv` / `corpus/`.
5. `codified_status` asks whether a source has downstream GABRIEL evidence-layer rows.

The national builder does not infer verification or codification from scout output. `verified_status` and `codified_status` are therefore `not_accounted` until authoritative source-level ledgers are joined. `ingested_status` is independently derived from the canonical contract corpus. A scout-positive municipality is not treated as verified, ingested, or codified.

## County coverage is not municipality completion

`national_scout_coverage_county.csv` reports municipality-county **associations**, not a completion flag. A county with `municipality_associations_scouted > 0` only means at least one in-scope associated municipality has been queried. It does not mean:

- every municipality in the county was scouted;
- a source was verified;
- a contract was ingested;
- the county has a matched safety/non-safety comparison; or
- the county is analytically complete.

Because multi-county municipalities appear in every associated county, summing municipality association counts across counties will exceed the national municipality total.

## Rebuild procedure

Run:

```bash
python scripts/build_scout_coverage.py
```

The script downloads these public sources into `tmp/` only when their cache is absent:

- `tmp/gov_units_2025.zip`
- `tmp/2024_Gaz_counties_national.zip`
- `tmp/2024_Gaz_cousubs_national.zip`
- `tmp/national_place_by_county2020.txt`

It then rebuilds:

- `national_county_universe.csv`
- `national_county_state_summary.csv`
- `national_municipality_universe.csv`
- `national_municipality_county_crosswalk.csv`
- `national_scout_coverage_state.csv`
- `national_scout_coverage_county.csv`

The builder parse-validates every output, requires jurisdiction state to agree with `state_fips`, requires all 65 prior project-known municipalities to match exactly one appropriate Census government (preferring the unique municipal row when a same-name township also exists), requires every scout municipality to remain in the universe, and reconciles scout metrics to the existing state scout-coverage file. These gates preserve the PA scout-result carry-forward rather than recomputing it under new semantics.

## Known limitations

- Universe and crosswalk vintages differ: the government inventory is 2025, county/county-subdivision geography is 2024, and the national place-by-county table is 2020. The 95 labeled current-primary supplements prevent silent loss, but they do not reconstruct every post-2020 boundary change for a place.
- `FIPS_COUNTY` in the Government Units Listing is only a primary/headquarters county for cross-county governments; consumers must use the full crosswalk.
- Some very small active governments may have no police/fire bargaining units or no collective bargaining. Inclusion means “potential municipal employer,” not “known contract source.”
- Ordinary county governments are outside this municipality scope even where a county is the relevant public-safety employer. A later county-employer wave would require a separate scope and must not be silently merged into this municipality universe.
- The Census government classification reflects institutional structure, not bargaining-unit availability or source verification.
