# Ingestion/codification stress-test report

The deterministic runner rejects missing inputs, predecessor decision drift, count mismatch, duplicate/overlapping identities, quarantine leakage, uncontrolled buckets, invalid rating boundaries, lane-size mismatch, and incomplete lane execution. It is idempotent when rebuilt into a fresh directory.
