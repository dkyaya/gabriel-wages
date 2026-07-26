# Bounded qualitative span disambiguation follow-up result

Decision: `bounded_qualitative_span_disambiguation_partial_additional_repair_needed`

The exact-only follow-up preserved all 455 previously verified qualitative spans and reviewed only the frozen 891 ambiguous and 608 unavailable rows. It hashed 700 retained PDFs and accessed exactly 1,011 approved target pages. OCR-later, rendered-image, non-target, invalid-pointer, and page-text persistence counts are zero.

Deterministic structured-field and exact-token rules resolved 277 ambiguous rows and 27 unavailable rows. Unique exact QA spans therefore increased from 455 to 759. The remaining 614 ambiguous and 581 unavailable rows remain navigation-only; no coded qualitative analysis view was created.

All 1,954 observation IDs, provenance fields, page pointers, content/PDF hashes, historical QA fields, and prior verified spans reconcile. The 862 quantitative candidates, 1,045 quantitative exceptions, 4,733 non-base companion rows, 345 reference/control rows, and two-group/five-observation conflict quarantine were copied forward byte-for-byte. Analysis readiness and analysis-facing promotion remain false.

The 32-test focused suite covers safe and unsafe repeated anchors, unavailable rows, exact-token fallback, fuzzy/paraphrase and cross-line rejection, full-page leakage, prior-span immutability, hash/offset integrity, checkpoint schema/reuse, approved-page enforcement, carried-forward byte identity, and analysis-readiness=false. No implementation defect was found; two initial positive-path fixtures correctly triggered the pre-existing full-page-leakage guard and were fixed by adding unrelated page context without weakening the guard.
