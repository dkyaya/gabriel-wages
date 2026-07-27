# Stress-test report

- Missing, duplicate, inactive, non-lane, non-one-to-one, or hash-drifted rows fail before outputs.
- Raw value strings are copied byte-for-byte at the field level and checked after triage.
- Missing units and compound/range values route to later normalization; upstream QA needs-review rows remain ambiguous.
- Missing cycles prevent mechanism-linkage candidacy and are never imputed.
- The runner has no network, PDF, retained-file, full-text, OCR, rendering, model, ingestion, or codification dependency.
- Partial outputs fail closed; a complete package resumes with zero writes.
