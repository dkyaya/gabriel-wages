# Dashboard status — provisional 500-document compensation extraction

The dashboard now reports
`compensation_extraction_500_provisional_completed`.

- Frozen cases: 500.
- Final case-level schema validity: 100%.
- Provisional observations: 1,073 quantitative, 1,181 qualitative mechanism,
  and 1,327 non-base-wage.
- Mixed cases: 182; reference/exclusion cases: 90.
- Integrity QA: pass.
- Scale QA: hold, with 83 potential quantitative conflict groups, three exact
  structured-content duplicates, and 102 possible non-base-wage quantitative
  records queued for targeted review.
- 1,000-document recommendation: `premature_pending_targeted_qa`.

The dashboard explicitly describes this as provisional extraction, not an
analysis-ready dataset. Ingestion, codification, wage-gap analysis, and
regression remain not started. No OCR or URL access occurred.
