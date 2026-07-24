# Full-Universe Metadata-Only Content-Triage Serial Merge Result

Date: 2026-07-24

## Outcome

**PASS.** The six audited metadata-only lanes were merged exactly once into a
durable cumulative content-triage ledger.

The exact command was:

```text
python scripts/merge_content_triage_lanes.py --manifest docs/analysis/content_triage_rounds/CONTENT-TRIAGE-ROUND1-1000-2026-07-24/content_triage_round_manifest.json --manifest docs/analysis/content_triage_rounds/CONTENT-TRIAGE-REMAINDER-ALL-ROUTED-2026-07-24/content_triage_round_manifest.json --audit-summary tmp/content_triage_rounds/CONTENT-TRIAGE-ROUND1-1000-2026-07-24/cumulative_merge_lane_audit_2026-07-24/content_triage_lane_audit_summary.json --audit-summary tmp/content_triage_rounds/CONTENT-TRIAGE-REMAINDER-ALL-ROUTED-2026-07-24/cumulative_merge_lane_audit_2026-07-24/content_triage_lane_audit_summary.json --routing-ledger-csv docs/analysis/verification_ledgers/verified_source_routing_ledger_cumulative.csv --output-dir docs/analysis/content_triage_ledgers --merge-id CONTENT-TRIAGE-FULL-UNIVERSE-METADATA-MERGE-2026-07-24
```

Outputs:

- cumulative ledger:
  `docs/analysis/content_triage_ledgers/content_triage_metadata_ledger_cumulative.csv`;
- cumulative summary:
  `docs/analysis/content_triage_ledgers/content_triage_metadata_summary_cumulative.json`;
- merge audit:
  `docs/analysis/content_triage_ledgers/content_triage_metadata_merge_audit_cumulative.md`;
- latest ledger:
  `docs/analysis/content_triage_ledgers/content_triage_ledger_latest.csv`; and
- latest summary:
  `docs/analysis/content_triage_ledgers/content_triage_summary_latest.json`.

The cumulative and latest ledgers are byte-identical. The cumulative and
latest summaries are also byte-identical.

## Row and identity audit

- Round 1 rows: 1,000
- All-routed remainder rows: 3,726
- Cumulative ledger rows: 4,726
- Terminal metadata-only rows: 4,726
- Unique `triage_id` values: 4,726
- Unique `candidate_queue_row_id` values: 4,726
- Duplicate triage IDs: 0
- Duplicate candidate-queue IDs: 0
- Cumulative URL-routing ledger rows: 4,726
- Exact candidate-queue identity equality with routing: **yes**
- Cumulative ledger SHA-256:
  `cedc269cc37f207491887151edc9c03000da1495198cdbc691c200f3eceb54c3`

Each row records its source round, source lane, merge ID, merge timestamp, and
the stage `metadata_only_triaged_not_content_reviewed`.

## Cumulative preliminary distributions

### Triage status

| Status | Rows |
|---|---:|
| `high_priority_content_review` | 1,760 |
| `medium_priority_content_review` | 1,232 |
| `low_priority_content_review` | 360 |
| `duplicate_defer_to_canonical` | 295 |
| `oversized_needs_separate_pass` | 261 |
| `blocked_or_unreachable_defer` | 603 |
| `needs_manual_review` | 205 |
| `already_canonical_context` | 8 |
| `excluded_from_content_review` | 2 |

### Recommended next action

| Action | Rows |
|---|---:|
| `content_review_download_allowed_later` | 2,923 |
| `metadata_review_only` | 437 |
| `duplicate_group_review` | 295 |
| `oversized_strategy_later` | 261 |
| `blocked_status_review_later` | 603 |
| `manual_review` | 205 |
| `exclude_for_now` | 2 |

The phrase `download_allowed_later` remains a planning label. No download was
authorized or performed by this merge.

### Preliminary extraction readiness

- `medium`: 2,923
- `low`: 429
- `unknown`: 769
- `none`: 605

### Preliminary source relevance

- `likely_relevant`: 1,760
- `possibly_relevant`: 1,895
- `unknown`: 1,069
- `unlikely_relevant`: 2

### Content-review priority

- `p1`: 1,760
- `p2`: 1,232
- `p3`: 360
- `defer`: 1,372
- `exclude`: 2

## Disposition and routing preservation

Original candidate dispositions remain:

- `scheduled`: 3,600;
- `context_hold`: 523;
- `insufficient_hold`: 302;
- `duplicate_hold`: 291;
- `already_canonical`: 8; and
- `calibration_rejected`: 2.

Disposition-to-priority results are:

```text
already_canonical: defer 8
calibration_rejected: exclude 2
context_hold: defer 175, p3 348
duplicate_hold: defer 291
insufficient_hold: defer 302
scheduled: defer 596, p1 1,760, p2 1,232, p3 12
```

Routing exceptions retain routing-specific triage:

```text
blocked_or_forbidden → blocked_or_unreachable_defer 339
not_found → blocked_or_unreachable_defer 264
too_large → oversized_needs_separate_pass 261
duplicate_of_verified_source → duplicate_defer_to_canonical 70
duplicate_same_url_pending → duplicate_defer_to_canonical 28
error → needs_manual_review 45
ssl_error → needs_manual_review 17
timeout → needs_manual_review 14
connection_error → needs_manual_review 8
```

Reachable PDF/document, HTML, and HTTP rows remain divided conservatively by
their original disposition and committed metadata. Reachability is not a
content finding.

## Source, content-type, and state summary

The largest inherited candidate source-type labels are `cba` (3,000),
`wage_schedule_or_compensation_plan` (803),
`memorandum_or_settlement` (355), `ordinance_or_policy` (206),
`arbitration_award` (151), and `factfinding` (77).

Routed content types include 3,855 `application/pdf`, 728 `text/html`, 127
`unknown`, and 16 rows across smaller routed types.

The largest state groups are OH 818, CA 774, IL 298, FL 241, WA 237, WI 214,
OR 180, MI 166, MA 161, NY 139, MN 131, TX 113, PA 102, NJ 94, and IA 75.

These are inherited candidate/routing metadata distributions, not conclusions
from source-content review.

## Safety and accounting boundary

The merged ledger and summary report zero URL opens, network calls, downloads,
document/PDF parses, OCR runs, and content artifacts. No scout queue or
coverage accounting changed. The cumulative routing ledger and summary remain
unchanged.

No source received a final relevance or quality rating. No ingestion,
codification, wage extraction, wage-gap calculation or claim, causal claim,
or regression occurred. All relevance, officialness, match, document, wage,
mechanism, and extraction-readiness fields remain preliminary metadata-only
scheduling signals.
