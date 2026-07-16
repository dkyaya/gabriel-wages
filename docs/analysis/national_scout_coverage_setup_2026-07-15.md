# National Scout Coverage Setup (updated 2026-07-16)

## Outcome

The former 65-row project-known municipality placeholder has been replaced by an authoritative, employer-oriented national universe and a separate full municipality-to-county-equivalent crosswalk.

- Starting local commit: `b516140f30c84029ac5845acbb86b2d601624d3d` (`Add national scout coverage accounting`)
- County/county-equivalent universe: **3,144**
- Active municipal governments: **19,471**
- Active township governments: **16,118**
- Total in-scope municipality employers: **35,589**
- Municipality-county relationship rows: **36,816**
- Multi-county municipalities: **1,106**
- Prior project-known municipalities preserved: **65 of 65**
- Municipalities scouted: **25**
- Scout-positive municipalities: **23**

No GABRIEL scout call, `gabriel.codify` call, model/API call, source ingestion, or source verification was performed. `data/contracts.csv`, `data/city_coverage.csv`, and `corpus/` were not changed.

## Source of record and scope

The municipality source of record is the Census Bureau's **2025 Government Units Listing**, a Governments Master Address File snapshot of independent government units active as of the fiscal year ending June 30, 2025:

- `https://www.census.gov/data/datasets/2025/econ/gus/public-use-files.html`
- `https://www2.census.gov/programs-surveys/gus/datasets/2025/gov_units_2025.zip`

The scouting universe includes functionally active municipal and township governments in the 50 states plus DC. It excludes ordinary county governments, dormant governments, CDPs, school districts, special districts, territories, and pension systems. This is a government/employer frame, not a generic list of populated places or all Census county subdivisions.

Township governments are included because New England towns and many municipal-type employers elsewhere are classified by Census as township rather than municipal governments. Only Census-classified independent township governments are included; statistical or inactive MCDs are not.

## Counts by state

| State | Municipal governments | Township governments | Total in scope |
|---|---:|---:|---:|
| AL | 463 | 1 | 464 |
| AK | 149 | 0 | 149 |
| AZ | 91 | 0 | 91 |
| AR | 500 | 0 | 500 |
| CA | 483 | 0 | 483 |
| CO | 271 | 0 | 271 |
| CT | 30 | 148 | 178 |
| DE | 57 | 0 | 57 |
| DC | 1 | 0 | 1 |
| FL | 411 | 0 | 411 |
| GA | 537 | 0 | 537 |
| HI | 1 | 0 | 1 |
| ID | 198 | 0 | 198 |
| IL | 1,294 | 1,425 | 2,719 |
| IN | 566 | 1,003 | 1,569 |
| IA | 940 | 2 | 942 |
| KS | 623 | 1,209 | 1,832 |
| KY | 411 | 0 | 411 |
| LA | 304 | 0 | 304 |
| ME | 23 | 458 | 481 |
| MD | 157 | 0 | 157 |
| MA | 58 | 294 | 352 |
| MI | 533 | 1,240 | 1,773 |
| MN | 856 | 1,777 | 2,633 |
| MS | 299 | 0 | 299 |
| MO | 934 | 283 | 1,217 |
| MT | 127 | 2 | 129 |
| NE | 528 | 333 | 861 |
| NV | 19 | 0 | 19 |
| NH | 13 | 223 | 236 |
| NJ | 323 | 241 | 564 |
| NM | 105 | 0 | 105 |
| NY | 594 | 929 | 1,523 |
| NC | 550 | 0 | 550 |
| ND | 355 | 1,301 | 1,656 |
| OH | 925 | 1,308 | 2,233 |
| OK | 591 | 0 | 591 |
| OR | 240 | 1 | 241 |
| PA | 1,014 | 1,542 | 2,556 |
| RI | 8 | 31 | 39 |
| SC | 271 | 0 | 271 |
| SD | 310 | 891 | 1,201 |
| TN | 345 | 0 | 345 |
| TX | 1,224 | 0 | 1,224 |
| UT | 255 | 0 | 255 |
| VT | 39 | 235 | 274 |
| VA | 227 | 0 | 227 |
| WA | 281 | 1 | 282 |
| WV | 230 | 0 | 230 |
| WI | 608 | 1,240 | 1,848 |
| WY | 99 | 0 | 99 |
| **National** | **19,471** | **16,118** | **35,589** |

## Crosswalk representation

`national_municipality_county_crosswalk.csv` has one row per government-county relationship. The 2025 Government Units primary/headquarters county is retained as a flag, but it is not used as a one-county collapse.

- Municipal governments are expanded with the official 2020 Census national place-by-county table.
- Township governments use the 2024 Census Gazetteer county-subdivision GEOID.
- A labeled 2025 primary-county supplement is used for 95 relationships where the older place table or 2024 county-subdivision table does not provide a current match, chiefly Connecticut planning-region conversions and post-2020 governments/recodes.
- 1,106 municipalities have more than one crosswalk row; the largest has five.

Examples from existing project targets now retain every relationship:

- Aurora, IL: DuPage, Kane, Kendall, and Will Counties.
- Columbus, OH: Delaware, Fairfield, and Franklin Counties.
- Austin, TX: Bastrop, Hays, Travis, and Williamson Counties.
- Houston, TX: Fort Bend, Harris, Montgomery, and Waller Counties.
- Portland, OR: Clackamas, Multnomah, and Washington Counties.
- Bethlehem, PA: Lehigh and Northampton Counties.

County coverage rows therefore count municipality-county associations and are not additive nationally.

## Special geography handling

- **Independent cities:** represented as municipal employers mapped to their own county-equivalent GEOID. Baltimore, St. Louis, Carson City, and Virginia independent cities are not assigned to adjacent counties.
- **Consolidated city-counties:** retained as one Census municipal government/employer, with the exact government name preserved (for example, `CITY AND COUNTY OF DENVER`) and one or more county-equivalent crosswalk rows. An ordinary county-government duplicate is not added.
- **New England municipalities:** Census township governments are included directly and mapped through county subdivisions. Connecticut uses its nine current planning regions as county equivalents.
- **DC:** represented explicitly as one municipal government (`CITY OF WASHINGTON DC`) and the single DC county-equivalent (`11001`).

## Status separation

The municipality universe has separate fields for:

- `already_scouted`
- `scout_positive_status`
- `verified_status`
- `ingested_status`
- `codified_status`

Scout output never populates verified, ingested, or codified status. Verification and codification remain `not_accounted` until authoritative source-level ledgers are joined. Ingestion is independently derived from the canonical contract corpus. A scout-positive row is still an unverified lead.

## PA carry-forward preserved

The national state rollup reconciles directly to `gabriel_state_source_scout_state_coverage.csv`. The PA scout results remain:

- municipalities in national universe: **2,556**
- municipalities scouted: **25**
- scout-positive municipalities: **23**
- police candidate municipalities: **20**
- fire candidate municipalities: **16**
- non-safety candidate municipalities: **14**
- likely-triad municipalities: **10**
- candidate rows total: **75**
- official-or-union candidate rows: **65**
- high-priority candidate rows: **3**
- scout total cost: **$0.2687877**
- input / reasoning / output tokens: **814,151 / 36,975 / 47,791**

These are scout-stage accounting values only. No PA lead was reclassified as verified, ingested, or codified.

## Files and rebuild

The deterministic builder is `scripts/build_scout_coverage.py`. Run:

```bash
python scripts/build_scout_coverage.py
```

It rebuilds the county universe/state summary, municipality universe, municipality-county crosswalk, and national state/county scout rollups. It also enforces unique Census government IDs, one crosswalk relationship per municipality-county pair, exact preservation of all 65 earlier project-known municipalities, inclusion of every scouted municipality, and reconciliation to the existing scout state rollup.

## Known limitations

- The source vintages are not identical: 2025 government units, 2024 counties/county subdivisions, and a 2020 national place-by-county table.
- The 95 explicit primary-county supplements prevent omissions but do not provide a full post-2020 boundary-history reconstruction.
- Inclusion does not prove that a government has police/fire employees, collective bargaining, a public CBA portal, or any in-window contract.
- County government employers are outside this municipality-specific frame.
- County association counts must not be summed to obtain national municipality counts.

## Recommended next move

Use this universe to design the next scout wave by explicit sampling or prioritization rules—population, state labor-law regime, existing safety/non-safety coverage gaps, and source-verification capacity—rather than trying to scout all 35,589 governments indiscriminately. Before any scout call, generate a bounded batch manifest from `national_municipality_universe.csv`, preserve the current one-request-at-a-time configuration, and keep all returned leads in scout-stage files until independently verified.
