# Post–Full Text/Table Detection Next-Phase Plan

## Current state

The full text/table-detection run is durably merged:

- parse-text detection universe: 1,828 PDFs
- terminal heuristic results: 1,828
- likely wage-table candidates: 1,067
- possible wage-table candidates: 749
- unlikely wage-table candidates: 12
- candidate wage-page hints: 7,649
- pages scanned / with text: 17,861 / 17,369
- OCR-later PDFs outside this run: 296
- final wage values extracted: 0
- ingestion / codification: 0 / 0

## Why calibration precedes extraction

The detector marked 1,816 of 1,828 PDFs likely or possible, a 99.3435% rate.
That high rate is consistent with a useful sensitive screen, but it also makes
false-positive measurement essential. Page hints are not wage observations;
some will identify prose about compensation, non-wage numeric tables, benefit
schedules, indexes, or other structurally dense pages.

A bulk wage extraction run now would turn unmeasured detector error into
structured-data error. Manual calibration should determine which signals and
page layouts are precise enough to support an extraction schema.

## Recommended calibration subset

Review 100–150 PDFs or candidate pages, sampled reproducibly across:

- wage-table signal: likely, possible, and the small unlikely group
- content-review priority: p1 and p2
- unit type: police, fire, and non-safety
- source type: CBA, wage schedule/compensation plan, memorandum, ordinance,
  arbitration award, and factfinding where available
- officialness: municipal, state repository, union, uncertain, and unknown
- page-count bins: 1–10, 11–25, 26–50, 51–100, and over 100
- states and source-review batches

Oversample possible and unlikely signals enough to characterize the decision
boundary. Preserve exact PDF-readiness/source-review identities.

## Calibration goals

1. Estimate precision of candidate wage-table page hints.
2. Test whether contract-period hints identify genuine agreement terms or
   effective periods.
3. Catalogue common table layouts: steps, grades, ranks, classifications,
   hourly schedules, annual schedules, percentage schedules, and appendices.
4. Identify false-positive families and define deterministic exclusion rules.
5. Decide a bounded wage-table extraction schema and row-level QA protocol.
6. Decide whether any of the 296 OCR-later PDFs merit a separate, explicitly
   authorized OCR pilot.

## Boundaries after calibration

- Design a small wage-table extraction pilot only after calibration results
  and schema are reviewed.
- Do not launch full wage extraction until field definitions, source identity
  joins, unit/cycle controls, and manual QA are stable.
- Do not ingest or codify extracted fields until validation demonstrates that
  page hints and extracted values remain traceable to exact source spans.
- Do not calculate wage gaps or make causal claims at this stage.
- Do not automatically OCR all 296 absent-text PDFs; first establish their
  likely incremental analytic value and an OCR QA protocol.
- Do not resume broad scouting or bulk downloading yet. The retained corpus is
  large enough that extraction calibration, not discovery volume, is the
  immediate bottleneck.
