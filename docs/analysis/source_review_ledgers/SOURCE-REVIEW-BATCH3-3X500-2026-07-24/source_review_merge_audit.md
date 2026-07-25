# Source-Review Merge Audit: SOURCE-REVIEW-BATCH3-3X500-2026-07-24

- Pilot ID: `SOURCE-REVIEW-BATCH3-3X500-2026-07-24`
- Merge ID: `SOURCE-REVIEW-BATCH3-3X500-MERGE-2026-07-24`
- Merged at: `2026-07-25T02:29:26Z`
- Durable rows / terminal rows: 1,500 / 1,500
- Unique source-review IDs: 1,500
- Unique candidate-queue IDs: 1,500
- Content artifacts / hashes: 1,480 / 1,480
- Content bytes / maximum: 3,189,614,089 / 10,470,269
- Cumulative durable rows: 2,150
- Cumulative content artifacts: 2,124
- Audit recommendation: `merge_all_source_review_lanes`
- Merge URL/network/download/parse/PDF/OCR counts: `0/0/0/0/0/0`

## Source-review status counts

- `download_forbidden`: 4
- `download_timeout`: 16
- `reviewed_metadata_and_artifact_saved`: 1,480

## Preliminary extraction-readiness counts

- `medium`: 1,480
- `not_ready`: 20

## Operative provenance

Only the audited lane ledgers listed in the round summary were
merged into this round. Any explicit prior durable ledger was
validated, kept unchanged, and combined only in the cumulative
ledger. No diagnostic or superseded attempt was read as a merge
input.

## Stage boundary

This ledger records bounded artifact access and preliminary ratings.
It does not establish final relevance, officialness, employer/unit
match, document identity, wage content, wage gaps, or causal effects.
No URL or document was accessed during this offline serial merge.
