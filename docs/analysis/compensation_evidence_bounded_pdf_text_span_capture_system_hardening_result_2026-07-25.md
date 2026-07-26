# Bounded PDF text-layer qualitative span capture and hardening result

Decision: `bounded_pdf_text_layer_span_capture_partial_additional_repair_needed`

The bounded run verified 788 retained PDF hashes and accessed exactly 1,223 approved text-layer pages for all 1,954 active qualitative rows. It accessed zero OCR-later documents, zero non-target pages, zero rendered images, and persisted zero full-page text.

The run captured 1,346 exact, single-line literal substrings. Of those, 455 have a unique-candidate exact-substring QA pass; 891 have multiple exact candidates and remain explicitly ambiguous. The remaining 608 rows have no safe exact structured-field or mechanism-anchor match. Therefore 1,499 rows remain navigation-only and no coded qualitative analysis view was created.

The system is deterministic and resumable. Thirty-two focused tests cover immutable hashes, approved-page access, no-OCR behavior, empty pages, repeated occurrences, missing matches and paths, wrong hashes, duplicate identifiers, checkpoint signatures, partial resume, idempotent complete-output reuse, offset/hash round trips, page-text leakage, historical-QA preservation, and multiline-span rejection. The hardening loop found and fixed four issues: generalized resume accounting, corrected an invalid test output boundary, separated `span_qa_status` from historical `qa_status` in the navigation shadow, and rejected multiline stored spans after they exposed repository whitespace defects.

All upstream package, prior repair, and durable ledgers stayed read-only. The task byte-preserved 862 quantitative candidates, 1,045 quantitative exceptions, 4,733 non-base companion rows, 345 reference/control rows, and the quarantine for two unresolved groups/five observations. Cycle/matching and occupation metadata counts were carried forward unchanged. Analysis readiness remains false.
