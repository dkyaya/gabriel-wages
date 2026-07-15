# National Scout Coverage Setup (2026-07-15)

## What this setup adds

This session established a national accounting backbone for future scout work:

- `national_county_universe.csv`
- `national_county_state_summary.csv`
- `national_municipality_universe.csv`
- `national_scout_coverage_state.csv`
- `national_scout_coverage_county.csv`
- `scripts/build_scout_coverage.py`

The accounting vocabulary is defined in `docs/analysis/national_scout_coverage_methodology_2026-07-15.md`.

## National county-equivalent count

- Total county/county-equivalent universe: **3,144**
- Geography source: **2024 Census Gazetteer counties national file**
- Scope rule: **50 states plus DC only; territories excluded**

Full state-by-state county-equivalent counts are in `docs/analysis/national_county_state_summary.csv` (51 rows, one per state or DC).

## Current known municipality count

- Municipalities currently known in project accounting: **65**
- Source basis:
  - `data/contracts.csv`
  - `docs/analysis/national_source_targets_2026-07-12.csv`
  - `docs/analysis/gabriel_state_source_scout_pa_batch25_municipalities_2026-07-15.csv`
- Important limit: this is a **placeholder municipality universe**, not a national municipality list.

Known municipalities by state currently on file:

| State | Known municipalities |
|---|---:|
| PA | 25 |
| MA | 9 |
| NJ | 5 |
| IL | 5 |
| NY | 5 |
| OH | 4 |
| TX | 3 |
| CA | 2 |
| CO | 1 |
| CT | 1 |
| MD | 1 |
| MN | 1 |
| OR | 1 |
| WA | 1 |
| WI | 1 |

## Current scouted municipality count

- Municipalities already scouted: **25**
- States with any scout coverage so far: **PA only**
- National scout-positive municipalities currently on file: **23**

## PA scout snapshot carried into the national accounting

The national setup preserves the existing PA 25-municipality coverage results:

- municipalities known: **25**
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

This remains scout-stage accounting only. None of those PA leads are reclassified here as verified, ingested, or codified.

## What remains unknown

- The municipality universe is incomplete nationwide; current counts reflect only municipalities already visible in existing corpus, source-target, and PA scout files.
- County coverage does **not** mean all municipalities in a county have been identified or scouted.
- Some municipalities span multiple counties. The placeholder municipality universe uses a primary-county assignment and flags those cases in `notes`.
- No state outside Pennsylvania currently has scout-coverage rows in the national accounting, even when the project already knows target municipalities there.

## Recommended next step

Build a **full municipality universe/county crosswalk** from an authoritative public place/employer geography source before running broader multi-state scout batches. The practical next move is:

1. Choose a national municipality source of record (for example, Census place geography plus a documented employer-target filter).
2. Generate a municipality-to-county-equivalent crosswalk from that source rather than relying on curated primary-county assignments.
3. Rebuild `national_municipality_universe.csv` from that source, then rerun `python scripts/build_scout_coverage.py`.

Until that happens, the national files are reliable for **project-known coverage accounting**, not for claims about full county-by-county municipal completion.
