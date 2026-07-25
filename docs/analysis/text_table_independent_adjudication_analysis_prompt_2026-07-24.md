# Future prompt: analyze independent text/table adjudication

This instruction is for a future analysis after the human reviewer has frozen:

`independent_adjudication_human_reviewed.csv`

Do not run it during packet preparation, and do not extract wage values.

## Validation first

Require 150 unique adjudication, calibration, source-review, PDF-readiness, and
candidate-queue identities. Validate every human categorical field against the
adjudication schema. Reject an analysis with `not_reviewed` rows, missing
reviewer/timestamp values, or overwritten identity/page fields.

Only after the independent file is frozen may analysis join the original
calibration signal/priority and compare human results with REVIEW1/REVIEW2.

## Required metrics

Report:

- strict human-confirmed likely/p1 rate, with numerator and denominator;
- candidate-bearing wrong-page rate, with numerator and denominator;
- counts of `extraction_ready` and
  `extraction_ready_with_schema_update`, overall and by unit/source/table type;
- second-review and exclusion counts;
- navigation-needed and target-found outcomes;
- compact compensation sheet count and recommendations;
- systematic false-positive families, especially wage prose, benefits,
  budget/fiscal tables, classification-without-pay, index/front matter, and
  non-wage appendices;
- human confidence and unresolved low-confidence cases;
- post-freeze disagreement with REVIEW1/REVIEW2, clearly described as a
  diagnostic rather than a relabeling of the human record.

## Decision rule

Choose exactly one:

- authorize 500-document extraction;
- authorize only a smaller extraction pilot;
- continue refinement with no extraction.

The 500-document run cannot be authorized unless strict human-confirmed
likely/p1 is at least 80%, wrong pages are no more than 15%, enough
extraction-ready/schema-update rows support the scale, and no systematic
false-positive family remains unresolved.

A smaller pilot also requires defensible bounded page precision and a
well-defined schema family; it is not an automatic fallback when the 500-row
gate fails. If the evidence is insufficient or a systematic error family
remains, keep both scales closed and recommend continued refinement.

The decision document must explicitly state whether the 500-document run is
allowed, whether a smaller pilot is allowed, and why.
