# Stress-test report

- Missing or hash-drifted predecessor artifacts fail before output creation.
- Any count other than 140 valid plus 19 quarantined fails closed.
- Overlapping valid/quarantine IDs or quarantine entries in candidate scope fail closed.
- Aggregate mechanism, relevance, strength, direction, and causal-support drift fails closed.
- The runner has no network, model, PDF, retained-source, full-text, OCR, rendering, ingestion, or codification dependency.
- Complete reruns are read-only; partial packages cannot masquerade as complete.
