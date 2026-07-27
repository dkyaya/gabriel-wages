# Stress-test report

- Missing or hash-drifted predecessor artifacts fail before output creation.
- Any count other than 173 valid plus 28 quarantined fails closed.
- Overlapping valid/quarantine identities fail closed.
- Open downstream statuses or non-exact quote flags fail closed.
- The runner has no network, PDF, retained-file, full-text, OCR, rendering, model, ingestion, or codification dependency.
- Partial outputs fail closed; a complete validated package resumes with zero writes.
