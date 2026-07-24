# Future Coordinator Prompt — Merge Verification Scale Round 1 3×750

Use only after the live `VERIFICATION-SCALE-ROUND1-3X750-2026-07-23` lane
collection completes. This is a serial verified-ledger merge, not authority
to fetch URLs, ingest, codify, or extract wages.

Work only in the main coordinator repository. Do not inspect remotes or push.

1. Require a clean tracked worktree and the committed live collection.
2. Recompute all three locked input hashes and rerun
   `scripts/audit_verification_lanes.py`.
3. Require exact candidate/verification-ID coverage, consistent duplicate
   groups, terminal lane artifacts, and either:
   `merge_all_verification_lanes`, or explicit user approval for
   `merge_completed_lanes_only_with_user_approval`.
4. Stop on partial rows, ambiguous artifacts, duplicate IDs, hash mismatch,
   or `do_not_merge_until_resume_or_review`.
5. Record before counts from the durable verification ledger, if it exists.
6. Merge approved lanes exactly once into a durable verified-source ledger,
   preserving every candidate queue identity, verification status, duplicate
   link, provenance field, and lane artifact pointer.
7. Enforce idempotency on `verification_id`; do not silently overwrite a prior
   terminal review.
8. Record reachability, blocked/not-found/timeout/error, content type,
   duplicate reuse, and preliminary routing counts.
9. Refresh dashboard verification status only after the ledger merge passes.
10. Validate, commit locally, create a relay, and do not push.

The merged ledger records verification-stage outcomes only. Do not modify
`data/contracts.csv`, `data/city_coverage.csv`, `corpus/`, scout queue or
coverage accounting. Do not ingest documents, run `gabriel.codify`, extract
wages, calculate gaps, or make evidentiary or causal claims.
