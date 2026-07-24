# Verification Scale Round 1 3×750 Serial Merge Readiness Audit

Date: 2026-07-24  
Round: `VERIFICATION-SCALE-ROUND1-3X750-2026-07-23`  
Starting commit: `642dbdab2190572a70b39e6221370a7796323b09`

## Repository and lineage gates

- The tracked worktree was clean before work. The unrelated untracked root
  `package-lock.json` was reported, left untouched, and excluded.
- Current `HEAD` descends from `642dbda`, `ee7041a`, `3616bae`, and
  `98ad608`.
- No round-specific durable routing ledger or prior serial-merge audit existed
  before this task.

## Locked inputs

| Lane | Rows | SHA-256 |
|---|---:|---|
| Lane 1 | 750 | `c03701be02afaa6c64cb63a8bb46cf9cae59f8665c3b2969e693b41a31cbfa65` |
| Lane 2 | 750 | `ac9ee0b048f331df295ead483305d72c587ce8962b89426f84b5f42d96d048ca` |
| Lane 3 | 750 | `a9192b47724dcc39eb09ac2760325a9fccd98fadc0b16452518fe4538ec9994a` |

The fresh offline audit command was:

```bash
python scripts/audit_verification_lanes.py \
  --manifest docs/analysis/verification_rounds/VERIFICATION-SCALE-ROUND1-3X750-2026-07-23/verification_round_manifest.json \
  --output-dir tmp/verification_rounds/VERIFICATION-SCALE-ROUND1-3X750-2026-07-23/serial_merge_lane_audit_2026-07-24
```

## Fresh lane audit

| Lane | Classification | Planned | Ledger | Terminal |
|---|---|---:|---:|---:|
| Lane 1 | `completed_merge_eligible` | 750 | 750 | 750 |
| Lane 2 | `completed_merge_eligible` | 750 | 750 | 750 |
| Lane 3 | `completed_merge_eligible` | 750 | 750 | 750 |

- Planned rows / ledger rows / terminal rows: **2,250 / 2,250 / 2,250**.
- Cross-lane duplicate verification IDs: **0**.
- Recorded scout/accounting mutations: **0**.
- URL opens/network calls from the already completed live round: **2,242**.
- Duplicate-linked/reuse rows: **8**.
- Recommendation: `merge_all_verification_lanes`.

Combined terminal status counts are 1,868
`reachable_pdf_or_document`, 18 `reachable_html`, two
`duplicate_of_verified_source`, six `duplicate_same_url_pending`, 137
`blocked_or_forbidden`, 131 `not_found`, 64 `too_large`, 18 `error`, three
`ssl_error`, two `timeout`, and one `connection_error`.

## Artifact and stage boundary

The completed live validation already established 2,221 lane-local metadata
JSON files, 952,655 bytes total and 627 bytes maximum. All nonblank ledger
artifact paths remain lane-local. No HTML content sample, PDF, or full
candidate document was retained, and no secret-bearing artifact field was
found.

The live task did not run scout queue/coverage or dashboard/accounting
builders. It also created no ingestion, codification, wage extraction,
wage-gap, causal, or regression output. The durable merge authorized here
will create only a routing/availability ledger and verification-status
outputs. It will not open URLs, mutate scout accounting, promote a source into
the corpus, ingest/codify evidence, extract wages, or support a wage-gap
claim.

All readiness gates pass. The serial verification-routing merge may proceed
exactly once.
