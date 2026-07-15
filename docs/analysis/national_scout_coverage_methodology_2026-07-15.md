# National Scout Coverage Accounting Methodology (2026-07-15)

## Purpose

This note defines the accounting vocabulary for national scout coverage before additional GABRIEL scout batches expand beyond the current Pennsylvania work. It is an accounting/setup layer only. It does not verify sources, ingest documents, or alter the claim/evidence pipeline.

## Geography layers

- `county_universe`: the national set of counties and county-equivalents used to define broad geographic coverage. In this setup, that universe is the **2024 Census Gazetteer county file filtered to the 50 states plus DC**. It includes county-equivalents such as Alaska boroughs/census areas, Connecticut planning regions, independent cities, and DC.
- `municipality_universe`: the set of municipalities/employers that may become scout targets. This is a different layer from the county universe. A county can contain zero, one, or many municipalities that matter for labor-source scouting.

## Workflow-status vocabulary

- `scout_coverage`: municipalities already queried by the GABRIEL source scout. This is only a record of which municipalities have been asked, not a statement that the county is finished.
- `scout_positive`: a municipality where the scout returned one or more unverified candidate leads.
- `verified`: a source URL/document has passed reachability/provenance review under the project's verification rules.
- `ingested`: a source has been promoted into `data/contracts.csv` and the document has entered `corpus/`.
- `codified`: a source has downstream evidence-layer rows produced by the GABRIEL/codify workflow.

## Critical distinction

These statuses are sequential and must not be collapsed:

1. `scout_coverage` asks: did we query this municipality?
2. `scout_positive` asks: did the scout return any leads?
3. `verified` asks: did a human or an authorized verification session confirm the lead?
4. `ingested` asks: did the source enter the causal corpus?
5. `codified` asks: did the source enter the evidence layer?

A scout-positive municipality is **not** verified, ingested, or codified.

## County coverage is not municipality completion

County-level accounting exists to answer "which county-equivalents contain any municipalities currently known to the project, and where has scout work already happened?" It does **not** mean:

- that every municipality in that county has been identified,
- that every municipality in that county has been scouted,
- that any source in that county has been verified, or
- that the county is analytically complete for cross-occupation comparison.

For this reason, the national county coverage files should always be read together with the municipality-universe placeholder notes. A county with `municipalities_scouted > 0` only means "some known municipalities in this county have been queried."

## Current file roles

- `national_county_universe.csv`: authoritative county/county-equivalent backbone.
- `national_county_state_summary.csv`: state-level count of county-equivalents.
- `national_municipality_universe.csv`: current known-municipality placeholder only, intentionally incomplete.
- `national_scout_coverage_state.csv`: state rollup of known municipalities plus current scout activity.
- `national_scout_coverage_county.csv`: county-equivalent rollup of known municipalities plus current scout activity.

## Scope limits of this setup

- No GABRIEL scout calls were run to create these files.
- No candidate URL was verified.
- No contract row, corpus file, claim file, or evidence-layer file was changed.
- The municipality universe is presently a **project-known placeholder**, populated only from:
  - existing corpus cities in `data/contracts.csv`,
  - existing planning targets in `docs/analysis/national_source_targets_2026-07-12.csv`,
  - the Pennsylvania 25-municipality scout batch list and resulting coverage files.

## Multi-county municipalities

Some municipalities span multiple counties/county-equivalents. The placeholder municipality universe assigns a primary county for accounting and flags that choice in the row-level `notes`. This is acceptable for setup/accounting, but a future full municipality universe should replace those primary assignments with an authoritative crosswalk.
