# Remaining readable parse-text dashboard status note

The dashboard phase is `compensation_extraction_readable_parse_text_1826_materialized_qa_pass`.

The card reports 1,826/1,826 unique readable parse-text hashes covered at 100% case-level schema validity. It shows 1,910 active quantitative observations, 1,954 qualitative mechanisms, 371 mixed cases, 4,730 non-base-wage observations, and 345 reference/exclusion cases.

The exact Hartland education/certification case passed one bounded preflight and one bounded live request. The corrected 1,000-case seed received zero calls and none of the 825 already-valid remaining cases was resent. The frozen remaining selection SHA-256 remains `43b768fba4e3d122727d2cbf9614885922a55be5f2bd1afd37d36f47a4695d81`.

Integrity QA passes with zero duplicate observation IDs, invalid page pointers, or base/non-base contamination. The 37 unresolved quantitative conflict groups have a 1.9372% rate, below the 2% gate; targeted conflict QA is still required before any final provisional merge.

Analysis readiness remains false. OCR-later documents remain untouched. Final merge, ingestion, codification, wage-gap analysis, and regression are not authorized.
