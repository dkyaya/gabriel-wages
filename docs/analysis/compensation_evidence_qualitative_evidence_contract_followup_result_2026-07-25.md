# Qualitative evidence-contract follow-up result

Decision: `qualitative_evidence_contract_limited_review_allowed_exact_span_only`

The contract accounts for all 1,954 qualitative mechanism rows in three disjoint provisional tiers: 759 exact-span coded candidates, 614 ambiguous exact-span navigation rows, and 581 unavailable-span navigation rows. Candidate contamination is zero. All exact candidates retain unique exact-span QA, valid hashes/offsets, page pointers, provenance, historical QA, and separate span QA.

This is not full qualitative readiness. The 614 ambiguous and 581 unavailable rows remain navigation-only. A future, separately authorized analysis-readiness review may evaluate only the limited 759-row exact-span candidate tier; analysis readiness and promotion remain false until that review.

No PDFs were reopened. No URL access, OCR, images, GABRIEL/API, extraction, selection, ingestion, codification, wage-gap work, regression, or causal analysis occurred. The 862 quantitative candidates, 1,045 quantitative exceptions, 4,733 non-base companion rows, 345 reference/control rows, and two-group/five-observation conflict quarantine were copied forward byte-for-byte.

The hardening loop found one orchestration defect: initial materialization checked for the future prompt before the reporting step created it. The run stopped closed, the partial new directory was discarded, the validator was split into pre-report and complete-output phases, regression tests were added, and clean rematerialization passed.
