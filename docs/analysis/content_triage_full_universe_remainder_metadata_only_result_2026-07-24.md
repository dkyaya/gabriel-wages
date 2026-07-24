# Full-Universe Remainder Metadata-Only Triage Result

Date: 2026-07-24
Round: `CONTENT-TRIAGE-REMAINDER-ALL-ROUTED-2026-07-24`

## Outcome

All 3,726 routed candidate identities not already covered by metadata-only
Round 1 received terminal, offline metadata-only triage outcomes.

| Measure | Lane 1 | Lane 2 | Lane 3 | Lane 4 | Combined |
|---|---:|---:|---:|---:|---:|
| Input/ledger/terminal rows | 932 | 932 | 931 | 931 | 3,726 |
| URLs opened | 0 | 0 | 0 | 0 | 0 |
| Network calls | 0 | 0 | 0 | 0 | 0 |
| Documents downloaded | 0 | 0 | 0 | 0 | 0 |
| Documents/PDFs parsed | 0 | 0 | 0 | 0 | 0 |
| OCR runs | 0 | 0 | 0 | 0 | 0 |
| Content artifacts | 0 | 0 | 0 | 0 | 0 |

Round 1 remains unchanged at 1,000 rows. The two rounds together contain
4,726 unique candidate-queue identities and 4,726 unique triage identities,
with zero cross-round overlap and no routed identity omitted.

## Remainder preliminary distributions

### Triage status

| Status | Rows |
|---|---:|
| `high_priority_content_review` | 760 |
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
| `content_review_download_allowed_later` | 1,923 |
| `metadata_review_only` | 437 |
| `duplicate_group_review` | 295 |
| `oversized_strategy_later` | 261 |
| `blocked_status_review_later` | 603 |
| `manual_review` | 205 |
| `exclude_for_now` | 2 |

`content_review_download_allowed_later` is only a future routing
recommendation. It did not authorize or trigger a download.

### Preliminary extraction readiness

| Value | Rows |
|---|---:|
| `medium` | 1,923 |
| `low` | 429 |
| `unknown` | 769 |
| `none` | 605 |

### Preliminary source relevance

| Value | Rows |
|---|---:|
| `likely_relevant` | 760 |
| `possibly_relevant` | 1,895 |
| `unknown` | 1,069 |
| `unlikely_relevant` | 2 |

### Content-review priority

| Value | Rows |
|---|---:|
| `p1` | 760 |
| `p2` | 1,232 |
| `p3` | 360 |
| `defer` | 1,372 |
| `exclude` | 2 |

Lower-disposition rows were not promoted to `p1`. The disposition-to-priority
audit is:

```text
already_canonical: defer 8
calibration_rejected: exclude 2
context_hold: p3 348, defer 175
duplicate_hold: defer 291
insufficient_hold: defer 302
scheduled: p1 760, p2 1,232, p3 12, defer 596
```

## Routing-status cross-tab

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

Reachable PDF/document, HTML, and HTTP rows were further divided by original
disposition, source-type label, and priority into the content-review,
duplicate, canonical, excluded, or manual categories reported above. Those
decisions remain preliminary and metadata-only.

## Audit and merge boundary

All four lanes are `completed_merge_eligible`. The audit found 3,726/3,726
terminal rows, no duplicate lane identities, complete selected-row coverage,
and zero source-access activity. Its recommendation is
`merge_all_content_triage_lanes`.

No durable content-triage ledger merge occurred. Round 1 and the remainder
stay as separate collected lane outputs until a future cumulative serial
merge is explicitly authorized.

No URL, download, content parse, PDF parse, OCR, source rating, ingestion,
codification, wage extraction, wage-gap calculation or claim, causal claim,
regression, scout-accounting change, or routing-ledger mutation occurred.
