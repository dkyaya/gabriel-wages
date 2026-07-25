# Provisional 500-document compensation extraction decision

Task ID: `COMPENSATION-EVIDENCE-EXTRACTION-500DOC-PROVISIONAL-LANES-2026-07-25`

## Decision

`premature_pending_targeted_qa`

The frozen 500-document run completed and passed integrity QA, but it did not
pass the separate scale-to-1,000 QA gate. The provisional ledgers must remain
unmerged, uningested, and outside any final analysis dataset.

## Integrity result

- Frozen unique document identities: 500 / 500.
- Final schema-valid case results: 500 / 500 (100%).
- Packet compliance: pass; 2,843 page records, at most six pages per case,
  at most 1,499 bounded text characters per page, and at most 5,999 per case.
- Invalid observation page pointers: 0.
- Duplicate observation IDs: 0.
- Evidence-bearing cases: 410.
- Dispositions: 182 mixed ready, 126 non-base wage, 58 qualitative ready,
  44 quantitative ready, 43 exclude, 41 reference only, and six second review.

## Scale hold

- Potential same-key quantitative conflict groups: 83, affecting provisional
  records that require evidence-level review.
- Exact structured-content duplicates: two quantitative and one non-base-wage
  duplicate; qualitative duplicates: zero.
- Quantitative records carrying possible non-base-wage signals: 102. They are
  flagged `needs_non_base_wage_review`; they were neither deleted nor silently
  promoted as base pay.
- Review queue rows: 187 in
  `compensation_extraction_500_conflict_review.csv`.

The computed conflict-group rate is 7.7353% of quantitative observations,
above the 2% scale rule. The scale QA status is therefore
`integrity_pass_scale_hold`, and the 1,000-document recommendation is
`premature_pending_targeted_qa`.

## Allowed next action

Perform targeted bounded QA on the 187 review rows: resolve the three exact
duplicates, determine whether the 83 potential conflict groups are true
contradictions or distinct schedule cells, and re-route the 102 possible
non-base-wage quantitative records where warranted. Recompute QA without new
document selection or extraction. Scaling to 1,000 remains closed until that
review passes.

No final merge, ingestion, codification, wage-gap calculation, regression, or
causal claim is authorized by this result.
