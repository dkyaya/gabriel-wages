# Future Coordinator Prompt — Scaled Verification Round 1 Ledger Merge

Use only after the three live verification lanes for
`VERIFICATION-SCALE-ROUND1-2026-07-23` have terminated and under separate
explicit serial-merge authorization.

## Merge gates

1. Require clean tracked state and the exact live-collection commit.
2. Recompute manifest/input/output hashes.
3. Re-run `scripts/audit_verification_lanes.py`.
4. Require unique verification IDs, exact 750-row coverage or an explicitly
   approved completed-lane subset, terminal verification statuses, preserved
   duplicate groups, and no ambiguous partial artifacts.
5. Stop if the recommendation is not eligible for the authorized merge.

## One serial verified-ledger merge

Create or update a durable `verified_source_ledger` planning output exactly
once. Preserve every candidate queue ID and original URL. Link duplicates by
group rather than deleting provenance. Record verification dispositions,
review timestamps, reviewer/process identity, and lane artifact paths.

The merge may refresh dashboard verification status and verification workload
summaries. It must not:

- rebuild scout queue or coverage from verification outcomes;
- write `data/contracts.csv`, `data/city_coverage.csv`, or `corpus/`;
- download or ingest a document;
- run `gabriel.codify`;
- extract wage observations;
- calculate wage gaps; or
- promote verification rows into claim evidence.

Document conversion, reachability, employer/unit match, source type,
officialness, duplicate, extractability-signal, and manual-review rates with
candidate-stage caveats. Commit locally, create a relay, and do not push.
