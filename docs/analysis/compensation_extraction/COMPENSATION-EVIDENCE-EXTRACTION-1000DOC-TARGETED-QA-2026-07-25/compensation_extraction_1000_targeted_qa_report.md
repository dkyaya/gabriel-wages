# Targeted QA report: cumulative provisional 1,000-document compensation extraction

- Targeted unresolved rows/groups processed: 151 / 151
- GABRIEL/API used: `false`
- Possible base/non-base records reviewed: 126
- Routing resolution counts: `{"reference_only": 1, "retain_quantitative_base_wage": 5, "route_to_non_base_wage": 120}`
- Quantitative conflict groups reviewed: 25
- Conflict resolution counts: `{"distinct_classification_or_rank": 7, "distinct_effective_period": 5, "distinct_schedule_cell": 6, "insufficient_evidence_needs_review": 2, "non_base_wage_misroute": 5}`
- Unresolved quantitative conflict groups: 2
- Revised unresolved conflict rate: 0.1647%
- Corrected active quantitative observations: 1214
- Corrected active qualitative observations: 1464
- Corrected active mixed cases: 256
- Corrected active non-base-wage observations: 2889
- Corrected active reference/exclusion rows: 175
- Duplicate observation IDs: 0
- Invalid bounded page pointers: 0
- Unresolved base/non-base contamination: 0
- Matched police/fire/non-safety representation intact: `true`
- Recomputed QA: `pass`
- Remaining readable parse-text extraction allowed: `true`

The 126 routing records were resolved with explicit retain/reroute/reference
actions and reason codes. Two conflict groups remain explicitly unresolved:
aggregate fiscal-impact totals that are not employee wage cells, and a salary
capture whose extracted rank conflicts with the visible schedule row. Their
combined rate remains below the 2% gate.

All original cumulative rows remain present in their corrected shadow ledger.
Rerouted records preserve their original quantitative observation ID in
provenance fields, existing duplicate canonicalization is retained, and mixed
membership is recomputed without changing the original cumulative ledgers.

No new extraction, selection, GABRIEL/API call, URL access, download, OCR,
ingestion, codification, final merge, wage-gap calculation, or regression
occurred.
