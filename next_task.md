# Next task: bounded follow-up for ambiguous or unavailable qualitative spans

Do not run this task without new explicit user authorization.

The current decision is `bounded_pdf_text_layer_span_capture_partial_additional_repair_needed`. The hardened layer accounts for all 1,954 qualitative rows and captured 1,346 exact single-line substrings, but only 455 are unique-candidate QA passes. Review only the 891 explicitly ambiguous and 608 unmatched rows.

The follow-up must preserve the 455 exact QA spans, all historical and span QA fields, page pointers, hashes, identifiers, and lane separation. It may use only the same retained readable PDFs and same recorded pages; no OCR, image rendering, URLs, downloads, models, new extraction, selection, ingestion, codification, or analysis. Do not infer or paraphrase. Any resolution must remain an exact, single-line short substring with round-trip offsets and SHA-256. If a unique safe span cannot be established, retain navigation-only status.

Carry forward unchanged: 1,359 exact cycles, 203 matched documents in 91 groups, 467 cycle quarantines, 1,458 controlled occupations, 239 non-safety subclasses, 368 occupation quarantines, 862 quantitative candidates, 1,045 quantitative exceptions, 4,733 non-base companion rows, 345 reference/control rows, and two unresolved groups/five observations. Keep analysis readiness false and stop before any analysis-readiness review unless separately authorized later.
