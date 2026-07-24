# Future Coordinator Prompt Template — 2×2000 Routing-Ledger Merge

Use only after a separately authorized future `bulk_2x2000` live round has
finished and preserved both lane outputs.

## Placeholders

- Round ID: `<FUTURE_ROUND_ID>`
- Round manifest: `<FUTURE_ROUND_MANIFEST.json>`
- Fresh serial audit output: `<FUTURE_SERIAL_AUDIT_DIR>`
- Merge ID: `<FUTURE_MERGE_ID>`
- Round-specific ledger output: `<FUTURE_LEDGER_OUTPUT_DIR>`

## Boundary

This is a serial, offline routing-ledger merge only. Do not open URLs, run
live verification or scouts, call APIs/models, ingest, codify, download or
parse content, extract wages, calculate wage gaps, make claims, run
regressions, inspect remotes, or push.

## Gates

1. Require a clean tracked worktree and exact manifest/input hashes.
2. Re-run `scripts/audit_verification_lanes.py` across the two live lanes.
3. Require:
   - both lanes `completed_merge_eligible`;
   - manifest, ledger, and terminal totals equal;
   - zero duplicate verification IDs or candidate queue IDs;
   - every routing status terminal;
   - all artifact references present and lane-local;
   - zero scout/accounting mutations; and
   - recommendation `merge_all_verification_lanes`.
4. Compare both lane identity sets with the prior cumulative ledger and stop
   on any overlap.

## Exactly-once merge

Run `scripts/merge_verification_lanes.py` once with the fresh audit summary.
Require:

- a round-specific immutable routing ledger and summary;
- cumulative ledger rows equal prior cumulative plus the new round;
- no identity overlap;
- `latest` byte-identical to project-wide cumulative, not newest-round-only;
- preserved original candidate dispositions and terminal statuses; and
- no scout queue/coverage, ingestion, contract, city-coverage, or corpus
  mutation.

Refresh dashboard routing status from the cumulative summary. Use routing
language only; do not call the outcomes content-verified, ingested,
extractable, or wage evidence.

Validate, create one local commit and relay, and report exact round and
cumulative counts. No live URL opening or downstream evidence work is
authorized by this template.
