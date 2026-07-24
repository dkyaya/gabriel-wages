# Content-Triage Readiness Audit

Date: 2026-07-24

## Decision

**PASS — ready for offline metadata-first content-triage planning.** URL routing
is complete, cumulative, terminal, and identity-aligned with the canonical
candidate queue. The correct next boundary is to prioritize sources for later
content relevance, employer/unit, source-quality, and extraction-readiness
review. This audit does not claim that any routed source contains usable wage
data.

Work began at commit
`5c9c524b31a19dd9d68984aacef750f3cac78b33`. The tracked worktree was clean;
the unrelated untracked root `package-lock.json` was reported and left
untouched. `HEAD` includes `5c9c524`, `e028432`, `e86abf7`, `2bab4b0`,
`ee7041a`, `3616bae`, and `98ad608`.

## Canonical inputs

- Cumulative routing ledger:
  `docs/analysis/verification_ledgers/verified_source_routing_ledger_cumulative.csv`
  (`831f40dacf3f0362d5c3c81cb2e59c4d3da502187c94672e381d355ae79f5499`)
- Cumulative routing summary:
  `docs/analysis/verification_ledgers/verified_source_routing_summary_cumulative.json`
- Candidate queue:
  `docs/analysis/national_scout_candidate_queue_2026-07-20.csv`
  (`d46b8bc3c60cbbda9b2f6f618fc447d1878d610fa1beb0924e7bafd47f965e83`)

The ledger and queue each contain 4,726 unique candidate queue identities.
Every routing row is terminal and has
`verification_stage = url_reachability_metadata_verified`.

## Routing pool

- URL-bearing candidate rows: **4,726**
- Durable routed rows: **4,726**
- Routing coverage: **100%**
- Reachable or successfully reused: **3,750 (79.3483%)**
- Additional `duplicate_same_url_pending` rows available for duplicate-group
  disposition: **28**
- Routing-eligible rows under the requested five-status planning definition:
  **3,778**

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

The 3,750 reachable/successfully reused rows have the following canonicalized
response content types:

| Content type | Rows |
|---|---:|
| `application/pdf` | 3,591 |
| `text/html` | 153 |
| DOCX | 4 |
| `application/octet-stream` | 1 |
| `image/jpeg` | 1 |

These are response-metadata outcomes. A PDF response is not yet a relevant CBA,
an employer/unit match, an extractable wage schedule, or evidence.

## Candidate dispositions and source types

Among the 3,750 reachable/successfully reused rows:

| Original candidate disposition | Rows |
|---|---:|
| `scheduled` | 3,014 |
| `context_hold` | 363 |
| `duplicate_hold` | 242 |
| `insufficient_hold` | 121 |
| `already_canonical` | 8 |
| `calibration_rejected` | 2 |

The largest candidate-source types are:

- CBA: 2,399;
- wage schedule or compensation plan: 607;
- memorandum or settlement: 276;
- ordinance or policy: 167;
- arbitration award: 130;
- fact-finding record: 75; and
- context-only: 41.

The remaining 55 rows span agenda sheets, meeting minutes, index pages,
unknown/insufficient types, pay plans, and one blocked/unreadable candidate
label. These labels remain scout metadata until content review.

## Geographic workload

The largest reachable/reused routing pools are Ohio 748, California 551,
Illinois 241, Florida 183, Washington 182, Wisconsin 174, Michigan 140,
Massachusetts 132, New York 113, and Oregon 109.

The largest `reachable_pdf_or_document` pools are Ohio 741, California 528,
Illinois 238, Florida 172, Washington 171, Wisconsin 169, Michigan 131,
Massachusetts 126, New York 107, and Oregon 102.

These counts describe review workload, not evidence strength or municipal wage
outcomes.

## Duplicate and exception boundaries

The five-status routing-eligible pool contains 78 exact-URL duplicate groups
and 93 linked rows beyond the first deterministic representative. The routing
statuses include 70 successful duplicate reuses and 28 duplicate-pending rows.
All identities remain preserved, but the first triage plan selects one
representative per exact-URL group unless duplicates are explicitly requested.

The **261 `too_large` rows** require a separate, bounded strategy. Raising the
10 MiB routing ceiling globally would combine storage, server, and parsing
risks with ordinary review. They are deferred, not declared unusable.

The 339 blocked, 264 not-found, 45 generic-error, 17 SSL-error, 14 timeout, and
eight connection-error rows are terminal routing statuses. They are not
findings that a municipality lacks a source and do not enter the ordinary
reachable-source content-triage batch.

## Why triage is next

Routing answered whether a bounded request produced useful response metadata.
It did not establish source relevance, officialness, correct municipality or
employer, bargaining unit, document type, period, wage-table content, or
extractability. An offline triage plan now creates a controlled selection and
durable schema before any content is opened. This keeps candidate lead,
routing outcome, content triage, quality rating, extraction readiness,
ingestion, codification, and analysis-ready observation as separate stages.

No URL was opened. No document was downloaded or parsed, no PDF/OCR operation
ran, and no network/API/model/hosted-search/scout call occurred. No scout
accounting, ingestion, `gabriel.codify`, wage extraction, wage-gap work,
causal claim, or regression occurred.
