# Targeted QA report: provisional 500-document compensation extraction

- Review queue rows processed: 187 / 187
- GABRIEL/API used: `false`
- Exact duplicate groups resolved: 2
- Duplicate observations canonicalized: 3
- Quantitative conflict groups: 83
- Conflict resolution counts: `{"distinct_classification_or_rank": 11, "distinct_effective_period": 5, "distinct_schedule_cell": 26, "insufficient_evidence_needs_review": 14, "non_base_wage_misroute": 27}`
- Unresolved conflict groups: 14
- Revised unresolved conflict rate: 1.52%
- Quantitative records rerouted to non-base wage: 151
- Unresolved base/non-base contamination: 0
- Active corrected quantitative observations: 920
- Active corrected qualitative observations: 1181
- Active corrected mixed cases: 177
- Active corrected non-base-wage observations: 1477
- Active corrected reference/exclusion cases: 90
- Invalid bounded page pointers: 0
- Duplicate observation IDs: 0
- Matched representation intact: `true`
- Integrity QA: `pass`
- Recomputed scale QA: `pass`
- 1,000-document recommendation: `recommend_1000_document_extraction`

Every original source row remains present in a shadow ledger. Canonicalization
and rerouting are represented with explicit provenance fields and active-lane
flags; the original provisional extraction ledgers are unchanged. The
corrected ledgers remain provisional and are not final analysis inputs.

No new extraction, GABRIEL/API call, URL access, download, OCR, ingestion,
codification, wage-gap calculation, regression, or final merge occurred.
