# Next task: separate schema and analysis-readiness review

The final provisional package has been materialized and passed its package
integrity gates at:

`docs/analysis/compensation_extraction/COMPENSATION-EVIDENCE-FINAL-PROVISIONAL-MERGE-2026-07-25/`

The next task should independently review whether the five still-separate
provisional schemas are suitable for a future analysis-facing promotion. It
should inspect schema contracts, join cardinality, provisional/inactive-row
handling, duplicate/canonical semantics, the two explicit unresolved groups,
and safe treatment of non-base compensation. It must issue an explicit
analysis-readiness decision rather than assuming that package QA implies
analytic validity.

Do not ingest or run `gabriel.codify` during that review. Do not create a final
analysis dataset, calculate wage gaps, run regressions, or make causal claims.
Keep OCR-later documents untouched. URLs, downloads, OCR, new extraction,
document selection, GABRIEL/API, scouts, source review, verification, and
mutation of the provisional package or its corrected source ledgers remain
prohibited unless separately authorized by a later task.
