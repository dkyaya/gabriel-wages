# Verification Scale Round 1 3×750 Serial Merge Result

Date: 2026-07-24  
Round: `VERIFICATION-SCALE-ROUND1-3X750-2026-07-23`  
Merge ID: `VERIFICATION-SCALE-ROUND1-3X750-MERGE-2026-07-24`

## Merge

The authorized serial merge ran exactly once:

```bash
python scripts/merge_verification_lanes.py \
  --manifest docs/analysis/verification_rounds/VERIFICATION-SCALE-ROUND1-3X750-2026-07-23/verification_round_manifest.json \
  --audit-summary tmp/verification_rounds/VERIFICATION-SCALE-ROUND1-3X750-2026-07-23/serial_merge_lane_audit_2026-07-24/verification_lane_audit_summary.json \
  --output-dir docs/analysis/verification_ledgers/VERIFICATION-SCALE-ROUND1-3X750-2026-07-23 \
  --round-id VERIFICATION-SCALE-ROUND1-3X750-2026-07-23 \
  --merge-id VERIFICATION-SCALE-ROUND1-3X750-MERGE-2026-07-24
```

The durable outputs are:

- `docs/analysis/verification_ledgers/VERIFICATION-SCALE-ROUND1-3X750-2026-07-23/verified_source_routing_ledger.csv`
- `docs/analysis/verification_ledgers/VERIFICATION-SCALE-ROUND1-3X750-2026-07-23/verified_source_routing_summary.json`
- `docs/analysis/verification_ledgers/VERIFICATION-SCALE-ROUND1-3X750-2026-07-23/verified_source_routing_merge_audit.md`
- latest ledger and summary copies under
  `docs/analysis/verification_ledgers/`

The ledger has **2,250 rows**, **2,250 terminal outcomes**, 2,250 unique
verification IDs, and 2,250 unique candidate-queue identities. It adds the
round, merge, timestamp, lane, and
`url_reachability_metadata_verified` stage fields while retaining every live
ledger field.

## Routing outcomes

| Status | Rows |
|---|---:|
| `reachable_pdf_or_document` | 1,868 |
| `reachable_html` | 18 |
| `duplicate_of_verified_source` | 2 |
| `duplicate_same_url_pending` | 6 |
| `blocked_or_forbidden` | 137 |
| `not_found` | 131 |
| `too_large` | 64 |
| `error` | 18 |
| `ssl_error` | 3 |
| `timeout` | 2 |
| `connection_error` | 1 |

Reachable or successfully reused rows total **1,888 / 2,250 (83.911%)**.
The eight duplicate-linked rows consist of two successfully reused rows and
six pending same-URL followers whose representative result was not reusable.
All eight identities remain in the ledger.

Content-type routing metadata is 1,934 `application/pdf`, 271 `text/html`,
and 45 unknown. These counts include non-reachable statuses and must not be
treated as reachable-source totals. Bytes-read buckets are 359 zero-byte
rows, 32 rows at 1–64 KiB, 781 at 64 KiB–1 MiB, and 1,078 at 1–10 MiB.

## State routing

The largest reachable/reused counts are Ohio 603, California 371, Illinois
197, Michigan 103, Washington 94, Wisconsin 94, Massachusetts 80, Oregon 62,
New York 58, and Iowa 34. The largest other-terminal counts are California
137, Ohio 41, Oregon 35, Washington 29, Illinois 21, New York 17, Wisconsin
15, Michigan 12, and Iowa/Montana eight each.

These are workload and URL-routing summaries, not state source-quality,
municipality-source-absence, wage, or mechanism findings.

## Artifacts and boundary

The merged rows contain 2,229 nonblank artifact references pointing to 2,221
unique small lane-local metadata JSON files; duplicate reuse explains the
repeated references. Every nonblank path was validated as existing inside its
lane output directory. No content samples, PDFs, or full documents were added.

This merge made zero URL opens or other network/API/model calls. It did not
mutate the candidate queue, scout coverage, contracts, city coverage, or
corpus. It did not ingest or codify a source, review employer/unit relevance,
extract a wage, calculate a wage gap, make a causal claim, or run a
regression. Reachability and response metadata are routing outcomes only.
