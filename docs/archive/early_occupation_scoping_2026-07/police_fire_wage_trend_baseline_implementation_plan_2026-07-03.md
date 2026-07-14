# Descriptive OEWS/ASPEP Wage-Trend Baseline Implementation Plan

**Date:** 2026-07-03  
**Scope:** descriptive baseline planning only; no GABRIEL run, no ingestion, no causal claim

## 1. Purpose

This note operationalizes the next empirical step after the PI-facing mechanism synthesis: a descriptive wage-trend baseline using public federal sources. The baseline is meant to answer a limited question:

What do broad occupation-level wage trends look like for police, fire, and selected comparison occupations at national, Massachusetts, and Boston-metro scales?

It is **not** a bargaining-unit wage dataset. It is **not** a contract schedule dataset. It is **not** a causal identification design.

## 2. Core source families

### BLS OEWS

The Bureau of Labor Statistics states that the Occupational Employment and Wage Statistics program produces annual employment and wage estimates for approximately 830 occupations and makes them available for the nation, states, and metropolitan/nonmetropolitan areas ([OEWS home](https://www.bls.gov/oes/home.htm); [OEWS tables](https://www.bls.gov/oes/tables.htm)).

The key OEWS tables page explicitly lists separate national, state, metro/nonmetro, national industry-specific/by-ownership, and all-data files for May 2025, and analogous annual files for earlier years including May 2024, 2023, 2022, and earlier ([OEWS tables](https://www.bls.gov/oes/tables.htm)).

### Census ASPEP

The Census Bureau's 2025 ASPEP tables page provides separate table entry points for:

- state government by function;
- local government by function;
- combined state and local government by function;
- individual unit files.

The page also notes that years not ending in `2` or `7` are survey years rather than census years and do not include all governments ([2025 ASPEP tables](https://www.census.gov/data/tables/2025/econ/apes/annual-apes.html); [2025 ASPEP datasets](https://www.census.gov/data/datasets/2025/econ/apes/annual-apes.html)).

## 3. Exact OEWS files/tables to use

### Primary OEWS entry page

- `https://www.bls.gov/oes/tables.htm`

This is the central index for annual OEWS files. It is the cleanest official landing page for a repeatable annual pull.

### May 2025 files to use first

From the OEWS tables page:

- National occupation profile file: May 2025 National (`HTML` / `XLSX`)
- State occupation profile file: May 2025 State (`HTML` / `XLSX`)
- Metropolitan and nonmetropolitan area file: May 2025 Metropolitan and nonmetropolitan area (`HTML` / `XLSX`)
- National industry-specific and by ownership file: May 2025 National industry-specific and by ownership (`HTML` / `XLSX`)
- All-data file: May 2025 All data (`XLSX` / `TXT`)

Official source page: [OEWS tables](https://www.bls.gov/oes/tables.htm)

The direct linked file targets on that page resolve to BLS-hosted zip/text artifacts with the following file names for May 2025:

- `oesm25nat.zip`
- `oesm25st.zip`
- `oesm25ma.zip`
- `oesm25in4.zip`
- `oesm25all.zip`
- `oesm25all.txt`

These direct file targets are linked from the official tables page, even though the browser tool does not render the zip contents directly.

### Historical OEWS years to use

For the first baseline, use the annual May OEWS files for:

- `2014` through `2025` if the full sequence is practical in one pull
- minimum fallback window: `2019` through `2025`

Reason:

- `2014-2025` lines up reasonably well with the project's bargaining-era window while preserving a pre-2020 comparison period.
- `2019-2025` is the lighter-weight fallback if the first implementation needs to stay compact.

The annual table index confirms annual files for May 2025, 2024, 2023, 2022, 2021, 2020, 2019, 2018, 2017, 2016, 2015, and 2014 on the same page ([OEWS tables](https://www.bls.gov/oes/tables.htm)).

### Exact OEWS geography pages

- National and state reference page for May 2024 state estimates:
  `https://www.bls.gov/oes/current/oessrcst.htm`

This page links directly to Massachusetts and also to national and metropolitan pages ([May 2024 state estimates](https://www.bls.gov/oes/current/oessrcst.htm)).

- Metropolitan/nonmetropolitan listing page for May 2025:
  `https://www.bls.gov/oes/current/oessrcma.htm`

This page explicitly lists `Boston-Cambridge-Newton, MA-NH` among Massachusetts metro areas ([May 2025 metro/nonmetro estimates](https://www.bls.gov/oes/current/oessrcma.htm)).

### OEWS ownership/public-sector sensitivity check

Use the national industry-specific and by ownership file as a sensitivity check on public/private sector mix where feasible. This will not solve the state/metro public-sector mix problem, but it provides one official BLS route to inspect ownership structure at the national level.

## 4. Exact ASPEP tables/files to use

### Primary ASPEP table page

- `https://www.census.gov/data/tables/2025/econ/apes/annual-apes.html`

This page is the cleanest public landing page for the current ASPEP tables.

### Table IDs to use

The 2025 ASPEP table page links to three data.census.gov table families:

- `GOVSEMPTIMESERIES.GS00EMP01`
  State and Local Government Employment & Payroll Data
  Example table URL:
  `https://data.census.gov/table/GOVSEMPTIMESERIES.GS00EMP01`

- `GOVSEMPTIMESERIES.GS00EMP02`
  State Government Employment & Payroll Data
  Example table URL:
  `https://data.census.gov/table/GOVSEMPTIMESERIES.GS00EMP02`

- `GOVSEMPTIMESERIES.GS00EMP03`
  Local Government Employment & Payroll Data
  Example table URL:
  `https://data.census.gov/table/GOVSEMPTIMESERIES.GS00EMP03`

These table IDs are the most useful function-based entry points for police protection, fire protection, education, transit, sanitation-like public services where available by function code, and broad state/local payroll context.

### Dataset page and individual-unit files

- `https://www.census.gov/data/datasets/2025/econ/apes/annual-apes.html`

This page links to:

- State Government Employment & Payroll Data
- Local Government Employment & Payroll Data
- State and Local Government Employment & Payroll Data
- Individual Unit Files

The 2025 dataset page also states:

- years not ending in `2` or `7` are survey years rather than census years;
- these years include sampled governments rather than the universe of all governments.

For individual-unit work, the page links to:

- `https://www2.census.gov/programs-surveys/apes/datasets/2025/2025_individual_unit_files.zip`

This should be treated as a secondary ASPEP lane, useful if the first descriptive baseline later needs individual-government function records rather than only table summaries.

### ASPEP methodology page

- `https://www.census.gov/programs-surveys/apes/technical-documentation/methodology/annual/2025.html`

Use this page when documenting what March payroll means, what governments are included, and the survey-versus-census distinction.

## 5. Proposed geographies

### Required first-pass geographies

1. National
2. Massachusetts
3. Boston-Cambridge-Newton, MA-NH metro if available

These are all supported directly in OEWS:

- nation;
- state;
- metro/nonmetro areas.

The metro page explicitly lists `Boston-Cambridge-Newton, MA-NH` as an available OEWS geography ([May 2025 metro/nonmetro estimates](https://www.bls.gov/oes/current/oessrcma.htm)).

### Optional later geography

- broader-state comparison set, selected only after the first Massachusetts/Boston baseline is stable.

Possible later comparison states:

- Connecticut
- New York
- New Jersey
- Pennsylvania
- Rhode Island

This should stay optional for the first baseline so the first pull remains manageable.

## 6. Proposed years

### Preferred

- `2014-2025` annual May OEWS files
- latest ASPEP table year, plus historical ASPEP tables back through at least `2014` if the extraction path is straightforward

### Practical fallback

- `2019-2025`

Rationale:

- keeps a pre-2020 baseline;
- spans the post-2020 period emphasized in the mechanism memo;
- aligns reasonably well with the project's municipal bargaining window.

## 7. Occupation mappings for the first baseline

The crosswalk CSV created alongside this memo gives the row-level mapping details. The short version is:

### Core occupations to include in the first baseline

- `police` -> `33-3051` Police and Sheriff's Patrol Officers
- `fire` -> `33-2011` Firefighters
- `teacher` -> `25-2021` Elementary School Teachers, Except Special Education
- `teacher` -> `25-2031` Secondary School Teachers, Except Special and Career/Technical Education
- `clerical_admin` -> `43-9061` Office Clerks, General
- `public_works` -> `49-9071` Maintenance and Repair Workers, General
- `sanitation` -> `53-7081` Refuse and Recyclable Material Collectors
- `transit` -> `53-3052` Bus Drivers, Transit and Intercity

### Candidate secondary or sensitivity occupations

- `clerical_admin` -> `43-6014` Secretaries and Administrative Assistants, Except Legal, Medical, and Executive
- `public_works` -> `47-2061` Construction Laborers
- `office_admin_broad` -> `43-0000` Office and Administrative Support Occupations

The main logic is to start with occupations that have relatively clear SOC identities, while being honest that `public_works` and `clerical_admin` are only approximated by national occupation categories.

## 8. Recommended first-pass build

### OEWS

Build a tidy panel with:

- year
- geography type
- geography
- SOC code
- occupation title
- employment
- annual mean wage
- annual median wage
- hourly mean wage if available

Minimum geography set:

- United States
- Massachusetts
- Boston-Cambridge-Newton, MA-NH

### ASPEP

Build a function-based context panel with:

- year
- government level (`state`, `local`, `state_local_combined`)
- function
- full-time equivalent employment if available
- full-time payroll if available
- part-time payroll if available
- total March payroll if available

Priority functions:

- police protection
- fire protection
- education
- transit or transit-related function if present
- sanitation / solid waste / sewerage / highways or other public-works-adjacent functions where the ASPEP item codes support them

## 9. What this baseline can answer

- whether police and firefighter occupational wages move differently from selected comparison occupations at broad geographic scales;
- whether Massachusetts roughly follows national patterns;
- whether the Boston metro pattern looks unusual or ordinary relative to the state/national baseline;
- whether government-function payroll context moves in ways that are consistent with broader public-safety wage pressure.

## 10. What this baseline cannot answer

- bargaining-unit contract wages;
- municipal-unit-specific negotiated wage schedules;
- wage growth within a specific CBA unit such as `Franklin police sergeants`;
- whether a mechanism caused wage growth;
- whether police/fire wage differences remain after perfect within-city contract matching.

## 11. Main limitations

- not bargaining-unit-level;
- not contract wage schedules;
- occupational categories do not perfectly match municipal bargaining units;
- public/private sector mix may remain imperfect outside the national ownership-sensitive table;
- metro is not municipality;
- county-level coverage is not the core OEWS design for this use case;
- ASPEP payroll is function-based March payroll, not annual negotiated base wage;
- ASPEP years not ending in `2` or `7` are survey years rather than full census years.

## 12. Recommendation

Start with a compact descriptive panel:

1. OEWS national/state/metro for `2019-2025` or `2014-2025`
2. ASPEP function-based context for the same years where feasible
3. occupation set centered on police, firefighters, teachers, clerical/admin, public-works proxy, sanitation, and transit

That gives the project a disciplined descriptive wage baseline without pretending to observe bargaining-unit contract wages.
