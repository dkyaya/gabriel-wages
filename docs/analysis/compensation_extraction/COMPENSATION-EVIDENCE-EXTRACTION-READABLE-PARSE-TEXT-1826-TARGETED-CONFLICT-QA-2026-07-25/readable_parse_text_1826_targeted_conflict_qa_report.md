# Targeted conflict QA: readable parse-text 1,826-case provisional layer

- Review groups processed: 37 / 37
- GABRIEL/API used: `false`
- New extraction or document selection: `false`
- Targeted resolution counts: `{"distinct_classification_or_rank": 13, "distinct_effective_period": 10, "distinct_schedule_cell": 11, "insufficient_evidence_needs_review": 2, "non_base_wage_misroute": 1}`
- Conflict groups resolved: 35
- Conflict groups left explicitly unresolved: 2
- Cumulative conflict counts: `{"distinct_classification_or_rank": 50, "distinct_effective_period": 17, "distinct_schedule_cell": 60, "insufficient_evidence_needs_review": 2, "non_base_wage_misroute": 1}`
- Revised unresolved quantitative conflict rate: 0.1049%
- Corrected active quantitative observations: 1907
- Corrected active qualitative mechanism observations: 1954
- Corrected active mixed cases: 371
- Corrected active non-base-wage observations: 4733
- Corrected active reference/exclusion cases: 345
- Duplicate observation IDs: 0
- Invalid bounded page pointers: 0
- Base/non-base contamination: 0
- Recomputed targeted QA: `pass`

Thirty-five groups were resolved from existing structured fields and tightly
bounded local page checks. Two inherited groups remain under-specified: one
contains aggregate fiscal-impact totals rather than employee wage cells, and
one has a rank/column mismatch that the bounded evidence does not safely
resolve. A three-record temporary working-out-of-classification premium group
was moved from active base quantitative evidence to explicit non-base-wage
shadow records while preserving every original observation ID and pointer.

The five newly canonicalized duplicate observations and all prior provenance
remain intact. Original cumulative ledgers were read-only. No URL, hosted
search, download, OCR, extraction, GABRIEL/API call, ingestion, codification,
final merge, wage-gap calculation, regression, or causal analysis occurred.
