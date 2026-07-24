# Source-Review Batch 2 (500 Rows) Live Collection Result

Date: 2026-07-24

## Result

**PASS.** Both locked Batch 2 lanes completed, every selected row has a
terminal source-review status, 495 bounded PDF artifacts were retained with
matching hashes and byte sizes, and five rows ended in bounded timeouts.
There were no connection errors. Both lanes are
`completed_merge_eligible`, artifact integrity passed, and the audit
recommendation is `merge_all_source_review_lanes`.

This is a collection and audit result only. No durable Batch 2 source-review
merge occurred.

## Locked scope and lane completion

| Lane | Input / terminal rows | Runtime | Rows/hour | Content artifacts | Content bytes |
|---|---:|---:|---:|---:|---:|
| Lane 1 | 250 / 250 | 262 s | 3,435.115 | 247 | 534,120,629 |
| Lane 2 | 250 / 250 | 279 s | 3,225.806 | 248 | 474,662,404 |
| **Combined** | **500 / 500** | **1,502 s end-to-end** | **1,198.402** | **495** | **1,008,783,033** |

The end-to-end wall clock runs from the first Lane 1 attempt to the final
Lane 2 completion and includes the checkpoint/launch gate and intervening
orchestration interval. Both guarded scripts exited zero. No third lane or
retry ran.

The locked Batch 2 rows contain 500 unique source-review IDs and 500 unique
candidate-queue IDs. Their candidate identities have zero overlap with the
150-row durable Pilot 1 ledger.

## Terminal outcomes

### `source_review_status`

- `reviewed_metadata_and_artifact_saved`: 495
- `download_timeout`: 5

### `url_access_status`

- `reached`: 495
- `timeout`: 5

### `download_status`

- `artifact_saved`: 495
- `timeout`: 5

There were zero connection, forbidden, TLS, not-found, too-large,
unsupported-content-type, or generic-error outcomes.

## Artifacts and observed content types

- observed `application/pdf`: 495;
- observed `unknown`: 5 timeout rows;
- content artifacts: 495;
- response-metadata artifacts: 500;
- rows with content hashes: 495;
- independently matching content hashes and sizes: 495;
- retained content bytes: 1,008,783,033;
- response-metadata bytes: 543,237;
- total retained artifact bytes: 1,009,326,270;
- minimum nonzero content artifact: 18,771 bytes;
- median content artifact: 1,249,035 bytes;
- maximum content artifact: 9,476,151 bytes;
- content samples: 0.

Content byte-size distribution:

- zero bytes: 5;
- 1–64 KiB: 1;
- 64 KiB–1 MiB: 207;
- 1–10 MiB: 287;
- more than 10 MiB: 0.

Every nonblank content and metadata path resolves inside its corresponding
`lane_*_live_attempt1/candidate_artifacts` directory. The audit reports no
missing, out-of-lane, hash-mismatched, or size-mismatched artifacts.

Documents parsed, PDFs parsed, OCR runs, and content samples are all zero.
Page count and text-layer status remain `unknown` for all 500 rows.

## Preliminary technical ratings

These values are conservative access- and artifact-metadata signals, not
final content-supported source ratings.

### Source officialness

- `official_municipal`: 235
- `official_state_repository`: 47
- `official_union`: 22
- `uncertain`: 185
- `unknown`: 11

### Relevance and identity match

- source relevance: 495 `possible`, 5 `unknown`;
- municipality match: 495 `possible`, 5 `unknown`;
- employer match: 495 `possible`, 5 `unknown`;
- bargaining-unit match: 495 `possible`, 5 `unknown`.

### Document type and extraction readiness

- document type: 495 `cba_candidate`, 5 `unknown`;
- extraction readiness: 495 `medium`, 5 `not_ready`;
- wage-table signal: 500 `unknown`;
- wage-growth signal: 500 `unknown`;
- mechanism-language signal: 500 `unknown`.

No content-supported relevance, municipality, employer, bargaining-unit,
document-type, wage, or mechanism finding was made.

## Runtime and review burden

- Lane 1: 262 seconds, 3,435.115 rows/hour;
- Lane 2: 279 seconds, 3,225.806 rows/hour;
- end-to-end wall clock: 1,502 seconds;
- end-to-end throughput: 1,198.402 rows/hour;
- mean row attempt: 4.269 seconds;
- maximum row attempt: 64.355 seconds;
- immediate timeout/manual-review burden: 5 rows, or 1.0%.

The end-to-end rate includes the controlled sequential launch gate and an
orchestration interval between the two lane executions. Lane-local rates are
the better transport-throughput measure.

## Comparison with Pilot 1

| Measure | Pilot 1 HTTPX | Batch 2 |
|---|---:|---:|
| Selected / terminal rows | 150 / 150 | 500 / 500 |
| Saved artifacts | 149 | 495 |
| Non-success terminal rows | 1 forbidden | 5 timeouts |
| Connection errors | 0 | 0 |
| Artifact yield | 99.333% | 99.000% |
| Retained content bytes | 301,970,460 | 1,008,783,033 |
| Maximum artifact bytes | 10,319,152 | 9,476,151 |
| Documents/PDFs parsed | 0 / 0 | 0 / 0 |
| OCR/content samples | 0 / 0 | 0 / 0 |

Observed Batch 2 content volume was within 0.22% of the simple Pilot 1
projection of 1,006,568,200 bytes. Transport and artifact integrity therefore
scaled predictably, but rating usefulness remains limited by the deliberate
no-parse boundary.

## Audit and scaling recommendation

- Lane 1: `completed_merge_eligible`;
- Lane 2: `completed_merge_eligible`;
- terminal coverage: 500/500;
- artifact integrity: passed;
- recommendation: `merge_all_source_review_lanes`.

A separately authorized serial task may merge Batch 2 after relay review.
After that merge, planning a 750-row checkpoint is reasonable because
terminal coverage, 99% artifact yield, bounded error burden, hash/locality
integrity, and volume projection all passed. A 1,000-row source-access batch
is not yet recommended: approximately 2 GB of content would be expected and
the preliminary ratings still have not been tested against parsed content.
Do not scale based on speed alone.

No durable Batch 2 merge, scout-accounting change, routing,
metadata-triage or durable source-review ledger mutation, ingestion,
`gabriel.codify`, wage extraction, wage-gap calculation or claim, causal
claim, or regression occurred.
