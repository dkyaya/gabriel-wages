# Post-Calibration Extraction Scale Plan

## Gate

Calibration status is **fail for extraction authorization**. The 150-row
Codex-assisted local review reports 76 apparent immediate pilot candidates
and 36 schema-update candidates, but it is not independent human ground
truth: 55 rows need second review and 59 are structurally hard. More
importantly, a five-row rendered-page challenge found material disagreement
in every case, including wage-related prose classified as table layouts and a
contents page pointing to a salary table after an assisted
`no_wage_table` result.

Do not proceed to 500 documents. Refine the page-hint/table classifier and
calibration schema, then run an independently adjudicated calibration subset.

## Future 500-document criteria

The following criteria are retained for a future run only after a revised
calibration passes:

Select from the durable text/table-detection layer using these gates:

- frozen `wage_table_signal=likely` as the primary pool;
- prioritize reviewed lessons associated with
  `include_in_wage_extraction_pilot`;
- preserve police, fire, and non-safety representation;
- include p1 and a controlled p2 share;
- include CBAs and wage schedules/compensation plans, plus smaller
  memorandum, ordinance, arbitration, and factfinding strata;
- include multiple states, officialness groups, page-count bins, and
  step-grade/rank-step/hourly/annual layouts;
- avoid or explicitly flag benefit tables, non-wage schedules,
  classification-without-pay pages, numeric appendices, and prose-only
  schedules;
- avoid known hard/partial-text cases in the main stratum, while retaining a
  small QA challenge sample;
- use local retained artifacts and candidate pages only;
- keep lanes balanced, resumable, and output-isolated.

## Extraction boundaries

The 500-run output must be a provisional extraction ledger, not a final
analysis dataset. It should preserve:

- detection, PDF-readiness, source-review, triage, verification, and
  candidate identities;
- document and candidate-page identity;
- table layout and effective-date/rate-basis provenance;
- field-level extraction status and validation errors;
- source relevance and officialness caveats.

It must not:

- open URLs or download documents;
- run OCR;
- write complete page/document text or copied PDFs;
- ingest or codify;
- create final wage observations;
- calculate wage gaps or run regressions;
- mutate current durable ledgers.

## QA gates after a future 500

Require:

1. terminal row and page coverage;
2. artifact hash equality;
3. schema-complete identity/provenance;
4. human spot checks stratified by layout, unit, source type, and confidence;
5. false-positive and wrong-page rates;
6. agreement between extracted table headers, effective dates, and rate
   basis;
7. duplicate document/page/table-row checks;
8. no full-text retention and no unapproved numeric outputs outside the
   provisional extraction schema.

Only after clean 500-run QA should a 1,000-document run be considered. Do not
run all 1,828 parse-text PDFs automatically. Keep the 296 `ocr_later` PDFs
outside extraction until a separate OCR need/quality review.

## Downstream sequence

1. separate wage-language detection from actual-table/layout confirmation;
2. rerun independent manual/visual calibration;
3. start with a smaller provisional extraction pilot if the calibration passes;
4. consider 500 documents only after that smaller pilot is clean;
5. consider 1,000 documents only after the 500-run is clean;
6. durable extraction merge only after separate approval;
7. ingestion/codification only after extracted fields and source identities
   are stable.
