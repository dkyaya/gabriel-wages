# Full-Universe Metadata-Triage Remainder Readiness Audit

Date: 2026-07-24
Planned round: `CONTENT-TRIAGE-REMAINDER-ALL-ROUTED-2026-07-24`

## Result

**PASS.** Work began at local commit
`4a49f93335178babebe4c888d9351f2dcc8d3cea`. The tracked worktree was clean.
The unrelated pre-existing untracked root `package-lock.json` was reported and
left untouched. Commits `4a49f93`, `eccbd0d`, `5c9c524`, `e028432`,
`e86abf7`, `2bab4b0`, `ee7041a`, `3616bae`, and `98ad608` are all ancestors
of `HEAD`.

## Existing metadata-only coverage

The preserved Round 1 lane ledgers contain:

- 1,000 rows;
- 1,000 unique `triage_id` values;
- 1,000 unique `candidate_queue_row_id` values;
- 1,000 terminal metadata-only statuses;
- zero URL opens and network calls;
- zero downloads, document/PDF parses, and OCR runs; and
- zero content artifacts.

Both lane summaries remain `metadata_only_completed`, the prior audit
recommendation remains `merge_all_content_triage_lanes`, and no durable
content-triage ledger exists.

## Cumulative routed universe and exact remainder

The cumulative routing ledger
`docs/analysis/verification_ledgers/verified_source_routing_ledger_cumulative.csv`
contains 4,726 rows, 4,726 unique candidate-queue identities, and a nonblank
terminal routing status for every row.

Subtracting the 1,000 Round 1 candidate-queue identities leaves exactly
**3,726** routed rows for metadata-only triage. Round 1 plus the exact
remainder equals the complete 4,726-row routed universe.

### Remaining routing statuses

| Routing status | Rows |
|---|---:|
| `reachable_pdf_or_document` | 2,533 |
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

### Remaining original candidate dispositions

| Disposition | Rows |
|---|---:|
| `scheduled` | 2,600 |
| `context_hold` | 523 |
| `insufficient_hold` | 302 |
| `duplicate_hold` | 291 |
| `already_canonical` | 8 |
| `calibration_rejected` | 2 |

### Remaining candidate source types

The largest candidate-source groups are `cba` (2,000),
`wage_schedule_or_compensation_plan` (803),
`memorandum_or_settlement` (355), `ordinance_or_policy` (206),
`arbitration_award` (151), and `factfinding` (77). Smaller groups retain their
original labels, including context, index, minutes, agenda, unknown, and
insufficient/blocked candidates.

### Remaining routed content types

The remainder includes 2,855 `application/pdf`, 728 `text/html`, 127 blank or
unknown content types, and 16 other small routed-type rows. These are routing
metadata, not claims about actual document contents.

## Why collect the full metadata layer before merge

A single cumulative merge after both rounds avoids presenting a durable ledger
that covers only the highest-priority reachable PDFs while omitting routing
exceptions and lower candidate dispositions. Full-universe metadata triage
also preserves explicit next-action categories for duplicates, oversized
documents, blocked/not-found rows, and transport errors without upgrading
those rows into evidence.

The new remainder round must preserve all original dispositions and routing
statuses. Every relevance, officialness, match, document-type, wage,
mechanism, and extraction-readiness value remains preliminary and
metadata-only.

No URL was opened; no content was downloaded or parsed; and no network, API,
model, hosted-search, scout, ingestion, codification, wage-extraction,
wage-gap, causal, regression, or durable-merge action occurred during
readiness.
