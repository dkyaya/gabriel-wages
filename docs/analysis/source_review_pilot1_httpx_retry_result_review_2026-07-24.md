# Source-Review Pilot 1 HTTPX Retry Result Review

Date: 2026-07-24

## Result

**The bounded HTTPX retry succeeded.** Both locked 75-row lanes completed,
all 150 rows have terminal source-review outcomes, and 149 rows retained
lane-local PDF artifacts with matching SHA-256 hashes. The same single Tempe
row that was forbidden in the original attempt and diagnostic probe remained
forbidden. Connection errors fell from 149 in the original `d97f5e4` attempt
to zero in this retry.

Both lanes are `completed_merge_eligible`; the lane audit recommendation is
`merge_all_source_review_lanes`. This is a structural and artifact-integrity
recommendation for a future serial merge, not a finding that the retained
documents are relevant, correctly matched, wage-bearing, or extraction-ready.
No durable source-review merge occurred.

## Locked scope and lane completion

| Lane | Input / terminal rows | Runtime | Rows/hour | Content artifacts | Content bytes |
|---|---:|---:|---:|---:|---:|
| Lane 1 | 75 / 75 | 26 s | 10,384.615 | 74 | 131,853,168 |
| Lane 2 | 75 / 75 | 33 s | 8,181.818 | 75 | 170,117,292 |
| **Combined** | **150 / 150** | **115 s wall clock** | **4,695.652** | **149** | **301,970,460** |

The combined wall clock measures from the start of the gated Lane 1 script to
the end of Lane 2, including the required checkpoint gate and the delay before
Lane 2 launch. Each script exited zero. Input identities exactly equal the
locked 150-row pilot, with no duplicate source-review or candidate-queue IDs.
No third lane or additional retry ran.

## Terminal outcomes

### `source_review_status`

- `reviewed_metadata_and_artifact_saved`: 149
- `download_forbidden`: 1

### `url_access_status`

- `reached`: 149
- `forbidden`: 1

### `download_status`

- `artifact_saved`: 149
- `forbidden`: 1

There were zero connection, timeout, TLS, not-found, too-large, unsupported
type, or generic error outcomes.

## Artifacts and observed types

- observed `application/pdf`: 149;
- observed `unknown`: 1 forbidden response;
- retained content artifacts: 149;
- rows with content hashes: 149;
- rows whose retained bytes match the recorded hash: 149;
- retained content bytes: 301,970,460;
- minimum nonzero retained artifact: 200,327 bytes;
- median nonzero retained artifact: 1,148,784 bytes;
- maximum retained artifact: 10,319,152 bytes;
- metadata artifacts: 150, totaling 163,090 bytes;
- combined content and metadata artifact bytes: 302,133,550;
- content samples: 0.

The content-size distribution is:

- zero bytes: 1;
- 64 KiB–1 MiB: 69;
- 1–10 MiB: 80;
- over 10 MiB: 0.

Every recorded content and metadata path exists inside its corresponding
`lane_*_live_attempt2_httpx` directory. The audit reports no missing,
out-of-lane, hash-mismatched, or size-mismatched artifacts.

PDF page count and text-layer status remain `unknown` for all 150 rows because
the runner did not parse PDFs. Documents parsed, PDFs parsed, OCR runs, and
content samples are all zero.

## Preliminary technical ratings

These values are conservative source-access and artifact-metadata signals.
They are not final content-supported ratings.

### Source officialness

- `official_municipal`: 82
- `official_state_repository`: 18
- `official_union`: 7
- `uncertain`: 41
- `unknown`: 2

### Relevance and identity match

- source relevance: 149 `possible`, 1 `unknown`;
- municipality match: 149 `possible`, 1 `unknown`;
- employer match: 149 `possible`, 1 `unknown`;
- bargaining-unit match: 149 `possible`, 1 `unknown`;
- safety-unit signal: 150 `unknown`;
- non-safety-unit signal: 150 `unknown`.

### Document type and technical extraction readiness

- document type: 149 `cba_candidate`, 1 `unknown`;
- extraction readiness: 149 `medium`, 1 `not_ready`;
- wage-table signal: 150 `unknown`;
- wage-growth signal: 150 `unknown`;
- mechanism-language signal: 150 `unknown`.

The immediate transport/manual-review burden is one row, or 0.6667%. No
document content was inspected deeply enough to confirm source relevance,
employer/unit match, document type, contract period, wage tables, or mechanism
language.

## Comparison with the original failed attempt

| Measure | Original `d97f5e4` attempt | HTTPX retry |
|---|---:|---:|
| Terminal rows | 150 | 150 |
| Connection errors | 149 | 0 |
| Forbidden | 1 | 1 |
| Retained content artifacts | 0 | 149 |
| Rows with content hashes | 0 | 149 |
| Retained content bytes | 0 | 301,970,460 |

The controlled result corroborates the connection diagnosis: the earlier
near-universal failures were caused by the superseded source-review transport
path, not a simultaneous loss of the locked source universe. The original
attempt remains preserved and unmerged as diagnostic provenance.

## Audit and scaling recommendation

The audit has:

- Lane 1: `completed_merge_eligible`;
- Lane 2: `completed_merge_eligible`;
- combined artifact integrity: passed;
- terminal coverage: 150/150; and
- recommendation: `merge_all_source_review_lanes`.

A separate serial task may merge only the repaired HTTPX retry outcomes if
the user approves, while preserving the original attempt as superseded
provenance. After that serial merge and relay review, a bounded 500-row batch
may be planned because completion, artifact yield, error burden, locality,
hash, and runtime gates all passed. A 750- or 1,000-row batch is not yet
recommended: the current ratings remain metadata/artifact-based, and speed
alone cannot establish content-review usefulness. OCR, deeper parsing, or
manual content review should continue to use smaller lanes.

No durable source-review merge, scout-accounting change, routing or
metadata-triage ledger mutation, ingestion, `gabriel.codify`, wage
extraction, wage-gap analysis or claim, causal claim, or regression occurred.
