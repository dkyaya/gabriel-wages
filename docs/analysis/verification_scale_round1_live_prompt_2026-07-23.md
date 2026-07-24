# Future Coordinator Prompt — Scaled Verification Round 1 Live Run

Use only under separate explicit live-verification authorization.

Work only in the main coordinator repo. Do not inspect remotes or push. Round:
`VERIFICATION-SCALE-ROUND1-2026-07-23`.

## Locked inputs and gates

Read the manifest, combined audit, three 250-row inputs, per-lane audits,
future commands, and merge handoff under
`docs/analysis/verification_rounds/VERIFICATION-SCALE-ROUND1-2026-07-23/`.
Recompute all input hashes. Require 750 unique verification IDs and queue IDs,
valid municipality/Census identities, scheduled candidate status, stable
duplicate groups, and no cross-lane ID overlap. Stop without substitution if a
gate fails.

Run all three lane dry runs first and require complete artifacts, exact input
coverage, and zero URL opens/network calls. Confirm the live runner has since
been implemented, offline-tested, bounded by timeouts/redirect/content-size
limits, and reviewed for public/licensed-source access constraints. The
framework committed by this planning task intentionally fails closed in live
mode and is not sufficient by itself.

## Live verification

Use fresh isolated directories and lane-local artifacts. Run the exact future
commands only after their implementation review. Use conservative concurrency
(three or fewer per lane), bounded timeouts, explicit redirect tracking, and
no silent URL substitution. Preserve each original queue identity and exact
duplicate group.

Do not:

- ingest or codify a document;
- promote a candidate into contracts/corpus;
- extract wage values;
- calculate or claim a wage gap;
- update discovery queue/coverage accounting; or
- treat verification as analysis-ready evidence.

After all lanes terminate, run `scripts/audit_verification_lanes.py`. Review
lane completeness, terminal statuses, duplicate grouping, failures, and
artifact integrity. Stop before the verified-ledger merge unless the audit
passes and a separately authorized serial merge task is invoked. Commit the
collection/audit documentation locally and create a relay; do not push.
