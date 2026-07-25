# Source-Review Batch 3 (3×500) Live Collection Result Review

Date: 2026-07-24

## Result

`SOURCE-REVIEW-BATCH3-3X500-2026-07-24` completed all 1,500 locked rows in
three 500-row lanes. Every lane exited zero, every row has a terminal
source-review status, artifact integrity passed, and the audit recommends
`merge_all_source_review_lanes`.

This is a collected, audited, **not merged** result. The cumulative durable
source-review ledger remains unchanged at 650 rows.

## Locked scope and lane result

| Lane | Planned | Terminal | Saved PDFs | Forbidden | Timeout | Classification |
|---|---:|---:|---:|---:|---:|---|
| Lane 1 | 500 | 500 | 492 | 3 | 5 | `completed_merge_eligible` |
| Lane 2 | 500 | 500 | 494 | 1 | 5 | `completed_merge_eligible` |
| Lane 3 | 500 | 500 | 494 | 0 | 6 | `completed_merge_eligible` |
| **Total** | **1,500** | **1,500** | **1,480** | **4** | **16** | **3 lanes eligible** |

Identity gates:

- unique source-review IDs: 1,500;
- unique candidate-queue IDs: 1,500;
- duplicate source-review IDs: 0;
- duplicate candidate-queue IDs: 0;
- overlap with 650 cumulative durable candidate identities: 0;
- overlap with prior source-review IDs: 0;
- fourth lane: not run;
- retry directory: not created.

## Selection mix

- p1: 1,097;
- p2: 403;
- p3: 0.

Priority to outcome:

- p1: 1,083 saved, 12 timeout, 2 forbidden;
- p2: 397 saved, 4 timeout, 2 forbidden.

The p2 fill contains all 282 remaining eligible CBA-labeled rows followed by
121 other download-allowed source types. Selection metadata remains a
scheduling signal, not a final content judgment.

## Terminal distributions

`source_review_status`:

- `reviewed_metadata_and_artifact_saved`: 1,480;
- `download_timeout`: 16;
- `download_forbidden`: 4.

`url_access_status`:

- `reached`: 1,480;
- `timeout`: 16;
- `forbidden`: 4.

`download_status`:

- `artifact_saved`: 1,480;
- `timeout`: 16;
- `forbidden`: 4.

Observed content type:

- `application/pdf`: 1,480;
- `unknown`: 20.

Connection, SSL, not-found, too-large, unsupported-type and generic-error
counts are zero.

## Artifact result

- retained content artifacts: 1,480;
- lane-local response-metadata artifacts: 1,500;
- rows with content hashes: 1,480;
- rows with matching hashes: 1,480;
- retained PDF bytes: 3,189,614,089;
- response-metadata bytes: 1,624,454;
- retained total artifact bytes: 3,191,238,543;
- minimum retained PDF: 7,030 bytes;
- median retained PDF: 1,381,775 bytes;
- maximum retained PDF: 10,470,269 bytes;
- content samples: 0;
- documents parsed: 0;
- PDFs parsed: 0;
- OCR runs: 0.

The lane auditor confirmed that every nonblank content path resolves under
its lane-local `candidate_artifacts` directory and that recorded hashes and
sizes match the retained files.

Content-size buckets:

- zero bytes: 20 terminal non-download outcomes;
- 1–64 KiB: 11;
- 64 KiB–1 MiB: 590;
- 1–10 MiB: 879.

## Preliminary ratings

These ratings describe URL/domain and retained-artifact metadata. No PDF
text or substantive source content was parsed.

Source officialness:

- `official_state_repository`: 471;
- `official_municipal`: 468;
- `uncertain`: 451;
- `unknown`: 87;
- `official_union`: 23.

Source relevance:

- `possible`: 1,480;
- `unknown`: 20.

Municipality, employer, and bargaining-unit match each:

- `possible`: 1,480;
- `unknown`: 20.

Document type:

- `cba_candidate`: 1,359;
- `unknown`: 141.

The 141 unknown document types include the 20 failed-access rows and 121
accessible p2 rows whose metadata source type is not CBA. Their artifacts
were not parsed and should not be relabeled based on access alone.

Technical extraction readiness:

- `medium`: 1,480;
- `not_ready`: 20.

All rows retain:

- wage-table signal: 1,500 `unknown`;
- wage-growth signal: 1,500 `unknown`;
- mechanism-language signal: 1,500 `unknown`;
- PDF page count: unknown;
- text-layer status: unknown.

## Runtime

| Lane | Start | End | Wall seconds | Rows/hour |
|---|---|---|---:|---:|
| Lane 1 | 23:57:01Z | 00:08:18Z | 677 | 2,658.79 |
| Lane 2 | 23:57:38Z | 00:09:43Z | 725 | 2,482.76 |
| Lane 3 | 23:58:56Z | 00:10:53Z | 717 | 2,510.46 |
| Combined gated window | 23:57:01Z | 00:10:53Z | 832 | 6,490.38 |

- mean individual attempt: 5.604151 seconds;
- maximum individual attempt: 65.345466 seconds.

The combined rate reflects overlapping lanes and should not be interpreted
as content-review throughput. No content was parsed or substantively rated.

## Comparison to prior rounds

| Measure | Pilot 1 | Batch 2 | Batch 3 |
|---|---:|---:|---:|
| Selected rows | 150 | 500 | 1,500 |
| Saved PDFs | 149 | 495 | 1,480 |
| Artifact yield | 99.33% | 99.00% | 98.67% |
| Forbidden | 1 | 0 | 4 |
| Timeout | 0 | 5 | 16 |
| Connection errors | 0 | 0 | 0 |
| Retained PDF bytes | 301,970,460 | 1,008,783,033 | 3,189,614,089 |
| Maximum PDF bytes | 10,319,152 | 9,476,151 | 10,470,269 |
| PDF parses / OCR | 0 / 0 | 0 / 0 | 0 / 0 |

Batch 3 retained about 5.4% more content than the preflight per-selected-row
projection, but remained far inside disk and per-row limits. The non-success
rate rose modestly from 1.0% in Batch 2 to 1.33% in Batch 3, without a
transport regression.

## Manual-review burden

Immediate transport/access burden is 20 rows, or 1.33%:

- 16 timeouts;
- 4 forbidden responses.

In addition, 121 accessible non-CBA metadata candidates remain
document-type `unknown` by design. They are useful for later schema
calibration but cannot receive final document ratings without content
inspection.

## Audit and next phase

Audit result:

- three lanes: `completed_merge_eligible`;
- terminal coverage: 1,500 / 1,500;
- artifact integrity: passed;
- recommendation: `merge_all_source_review_lanes`.

Recommended sequence:

1. perform a separately authorized serial Batch 3 merge using only these
   three lane ledgers;
2. preserve the 650 prior durable rows cumulatively, yielding 2,150 durable
   rows if the merge passes;
3. before automatically downloading the remaining 726 default-eligible p2
   rows, run a bounded text-layer/page-count evaluation pilot on retained
   artifacts to test whether actual parsing-readiness information is useful;
4. decide after that pilot whether to finish the remaining download-allowed
   pool or focus on targeted source/content review.

Do not scale based on the 6,490 rows/hour figure alone.

## Boundary

No durable Batch 3 source-review merge occurred. No durable routing,
metadata-triage, or source-review ledger changed. No scout accounting,
corpus write, PDF parse, OCR, content sample, ingestion, codification, wage
table or wage-value extraction, wage-gap calculation or claim, causal claim,
or regression occurred.
