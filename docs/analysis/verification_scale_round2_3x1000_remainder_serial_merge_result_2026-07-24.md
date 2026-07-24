# Verification Scale Round 2 3×1000 Remainder — Serial Merge Result

Date: 2026-07-24
Round: `VERIFICATION-SCALE-ROUND2-3X1000-REMAINDER-2026-07-24`
Merge ID: `VERIFICATION-SCALE-ROUND2-3X1000-REMAINDER-MERGE-2026-07-24`

## Exactly-once merge

The authorized serial merge ran exactly once:

```bash
python scripts/merge_verification_lanes.py \
  --manifest docs/analysis/verification_rounds/VERIFICATION-SCALE-ROUND2-3X1000-REMAINDER-2026-07-24/verification_round_manifest.json \
  --audit-summary tmp/verification_rounds/VERIFICATION-SCALE-ROUND2-3X1000-REMAINDER-2026-07-24/serial_merge_lane_audit_2026-07-24/verification_lane_audit_summary.json \
  --output-dir docs/analysis/verification_ledgers/VERIFICATION-SCALE-ROUND2-3X1000-REMAINDER-2026-07-24 \
  --round-id VERIFICATION-SCALE-ROUND2-3X1000-REMAINDER-2026-07-24 \
  --merge-id VERIFICATION-SCALE-ROUND2-3X1000-REMAINDER-MERGE-2026-07-24
```

Round-specific durable outputs:

- `docs/analysis/verification_ledgers/VERIFICATION-SCALE-ROUND2-3X1000-REMAINDER-2026-07-24/verified_source_routing_ledger.csv`
- `docs/analysis/verification_ledgers/VERIFICATION-SCALE-ROUND2-3X1000-REMAINDER-2026-07-24/verified_source_routing_summary.json`
- `docs/analysis/verification_ledgers/VERIFICATION-SCALE-ROUND2-3X1000-REMAINDER-2026-07-24/verified_source_routing_merge_audit.md`

Project-wide cumulative outputs:

- `docs/analysis/verification_ledgers/verified_source_routing_ledger_cumulative.csv`
- `docs/analysis/verification_ledgers/verified_source_routing_summary_cumulative.json`
- `docs/analysis/verification_ledgers/verified_source_routing_ledger_latest.csv`
- `docs/analysis/verification_ledgers/verified_source_routing_summary_latest.json`

The `latest` files are byte-identical copies of the cumulative files, not
Round 2-only pointers. The Round 1 round-specific ledger remains unchanged.

## Identity and coverage

| Layer | Rows | Unique verification IDs | Unique queue IDs |
|---|---:|---:|---:|
| Round 1 durable | 2,250 | 2,250 | 2,250 |
| Round 2 durable | 2,476 | 2,476 | 2,476 |
| **Cumulative** | **4,726** | **4,726** | **4,726** |

- Round 1 / Round 2 queue-ID overlap: 0.
- Cumulative identities matching the canonical URL-bearing queue: 4,726 /
  4,726.
- URL-bearing queue identities remaining: 0.
- Every cumulative row is terminal and has
  `verification_stage = url_reachability_metadata_verified`.

## Round 2 outcomes

| Routing status | Rows |
|---|---:|
| `reachable_pdf_or_document` | 1,665 |
| `reachable_html` | 127 |
| `reachable_http` | 2 |
| `duplicate_of_verified_source` | 68 |
| `duplicate_same_url_pending` | 22 |
| `blocked_or_forbidden` | 202 |
| `not_found` | 133 |
| `too_large` | 197 |
| `error` | 27 |
| `ssl_error` | 14 |
| `timeout` | 12 |
| `connection_error` | 7 |
| **Total** | **2,476** |

Round 2 reachable or successfully reused is **1,862 / 2,476 (75.2019%)**.
The live round recorded 2,386 logical URL opens and 90 duplicate-linked reuse
rows; the serial merge itself made zero network calls.

Round 2 response content types:

| Content type | Rows |
|---|---:|
| `application/pdf` | 1,921 |
| `text/html` | 457 |
| `unknown` | 82 |
| `application/xml` | 5 |
| DOCX | 4 |
| `text/plain` | 2 |
| `text/xml` | 2 |
| `application/json` | 1 |
| `application/octet-stream` | 1 |
| `image/jpeg` | 1 |

Round 2 bytes read: 674 zero-byte rows, 123 at 1–64 KiB, 935 at 64
KiB–1 MiB, and 744 at 1–10 MiB.

## Cumulative outcomes

| Routing status | Rows |
|---|---:|
| `reachable_pdf_or_document` | 3,533 |
| `reachable_html` | 145 |
| `reachable_http` | 2 |
| `duplicate_of_verified_source` | 70 |
| `duplicate_same_url_pending` | 28 |
| `blocked_or_forbidden` | 339 |
| `not_found` | 264 |
| `too_large` | 261 |
| `error` | 45 |
| `ssl_error` | 17 |
| `timeout` | 14 |
| `connection_error` | 8 |
| **Total** | **4,726** |

Cumulative reachable or successfully reused is **3,750 / 4,726
(79.3483%)**. The two live rounds together recorded 4,628 logical URL opens
and 98 duplicate reuse/link rows.

Cumulative content types:

| Content type | Rows |
|---|---:|
| `application/pdf` | 3,855 |
| `text/html` | 728 |
| `unknown` | 127 |
| `application/xml` | 5 |
| DOCX | 4 |
| `text/plain` | 2 |
| `text/xml` | 2 |
| `application/json` | 1 |
| `application/octet-stream` | 1 |
| `image/jpeg` | 1 |

Cumulative bytes read: 1,033 zero-byte rows, 155 at 1–64 KiB, 1,716 at
64 KiB–1 MiB, and 1,822 at 1–10 MiB.

## Original-disposition outcomes

All Round 1 rows were scheduled. Round 2 preserved every original lower
disposition. Cumulative routing by disposition is:

| Original disposition | Reachable/reused | Other terminal | Total |
|---|---:|---:|---:|
| `scheduled` | 3,014 | 586 | 3,600 |
| `context_hold` | 363 | 160 | 523 |
| `duplicate_hold` | 242 | 49 | 291 |
| `insufficient_hold` | 121 | 181 | 302 |
| `already_canonical` | 8 | 0 | 8 |
| `calibration_rejected` | 2 | 0 | 2 |

These are routing outcomes only. No lower-disposition candidate was upgraded
to content-verified, ingested, codified, or analysis-ready evidence.

## State routing

Round 2’s largest reachable/reused counts are Florida 183, California 180,
Ohio 145, Minnesota 103, Texas 89, Washington 88, Pennsylvania 83, New Jersey
81, Wisconsin 80, and New York 55. Its largest other-terminal counts are
California 86, Florida 58, Illinois and Oregon 36 each, Ohio 29, Minnesota 28,
Washington 26, Wisconsin 25, and Texas 24.

Cumulatively, the largest reachable/reused counts are Ohio 748, California
551, Illinois 241, Florida 183, Washington 182, Wisconsin 174, Michigan 140,
Massachusetts 132, New York 113, and Oregon 109. The largest other-terminal
counts are California 223, Oregon 71, Ohio 70, Florida 58, Illinois 57,
Washington 55, Wisconsin 40, Massachusetts 29, and Minnesota 28.

These comparisons describe routing workload, not source quality or wage
outcomes.

## Artifacts and boundary

The Round 2 ledger has 2,416 nonblank artifact references to 2,330 unique
lane-local metadata files. Cumulatively there are 4,645 nonblank artifact
references. All nonblank paths resolve inside the corresponding lane output
root. No content sample or full PDF/document was introduced, and no
secret-bearing artifact was found.

This merge opened no URL and made no network/API/model/hosted-search call. It
did not update scout queue or coverage accounting, contracts, city coverage,
or corpus. It did not ingest or codify a source, extract a wage, calculate a
wage gap, make a wage-gap or causal claim, or run a regression.

`reachable_*` statuses remain availability/response-metadata routing, not
proof of relevance, employer/unit match, extractability, or analysis-ready
evidence.
