# Limited exact-span readiness stress-test report

The focused suite exercises immutable-hash drift, candidate contamination, tier-count drift, duplicate IDs, blank provenance, span hash corruption, offset corruption, page-pointer mismatch, retained-hash mismatch, inactive candidates, forbidden payload columns, carried-file drift, conflict-quarantine drift, decision/prompt mismatch, unsafe output paths, and global-readiness escalation. Each condition must fail closed.

Materialization-time invariants passed. Final test totals are appended to the validation report.
