# Stress-test report

The coordinator fail-closes on count, lane, identity, hash-integrity, controlled-status, or predecessor-lineage drift. Worker resume rejects identities outside the locked lane. Empty/error/deferred classifications remain outside extraction-ready manifests. An already-existing output directory blocks a second prepare, and a completed lane rerun is idempotent over row identities.
