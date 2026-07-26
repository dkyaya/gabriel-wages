# Next task: targeted cumulative 1,000-case routing and conflict QA

The frozen cumulative extraction is complete at 1,000/1,000 strict-valid
cases. Do not run new extraction and do not change selected identities.

Use only:

- `compensation_extraction_1000_conflict_review.csv`;
- the cumulative provisional quantitative/non-base/mixed ledgers;
- existing bounded evidence pointers and local retained artifacts.

Review the 151 unresolved rows/groups:

1. Resolve 126 active quantitative records flagged by the stricter cumulative
   non-base scan. Classify each as `retain_quantitative_base_wage`,
   `route_to_non_base_wage`, `split_quant_and_non_base_components`,
   `reference_only`, or `insufficient_evidence_needs_review`.
2. Resolve or retain explicitly the 25 under-specified quantitative conflict
   groups. Do not invent missing step, rank, classification, or effective-date
   distinctions.
3. Preserve the nine already canonicalized duplicate observations and every
   provenance row.
4. Write corrected cumulative shadow ledgers; never overwrite the current
   provisional cumulative ledgers.
5. Recompute integrity QA. Further provisional scale is eligible only if
   duplicate IDs and invalid pointers remain zero, base/non-base contamination
   is zero, unresolved conflict rate remains at most 2%, and matching remains
   intact.

Default to no GABRIEL/API. Any model use would require a separately bounded and
explicitly authorized QA-only preflight. Continue to prohibit URLs, hosted
search, downloads, OCR, scouts, source review, verification, ingestion,
`gabriel.codify`, final analysis merge, wage-gap work, regressions, and durable
upstream-ledger mutation.
