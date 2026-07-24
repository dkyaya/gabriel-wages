# Verification Merge Handoff — VERIFICATION-SCALE-ROUND1-2026-07-23

Audit Lane 1, Lane 2, Lane 3 together with `scripts/audit_verification_lanes.py`. Require
exact input coverage, unique verification IDs, terminal lane outputs, preserved
duplicate groups, and no ambiguous partial rows. Only a separately authorized
serial task may merge eligible lanes into a durable verified-source ledger.

That merge must not update scout coverage, ingest contracts, run
`gabriel.codify`, extract wages, calculate wage gaps, or turn a verification
status into claim evidence. Candidate, verified, ingested, codified, and
analysis-ready stages remain distinct.
