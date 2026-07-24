# Source-Review Pilot 1 Live Collection Result Review

Date: 2026-07-24

## Outcome

The two authorized bounded lanes completed 150/150 terminal source-review
rows. The collection is structurally complete and artifact-safe, but it
produced no retained source body and therefore failed the quality gate for
scaling.

| Lane | Input | Ledger | Terminal | Status mix | Runtime | Rows/hour |
|---|---:|---:|---:|---|---:|---:|
| 1 | 75 | 75 | 75 | 74 connection errors; 1 forbidden | 27 s | 10,000.0 |
| 2 | 75 | 75 | 75 | 75 connection errors | 26 s | 10,384.6 |
| **Combined** | **150** | **150** | **150** | **149 connection errors; 1 forbidden** | **39 s wall clock** | **13,846.2** |

Both lane scripts exited zero. Exactly the 150 locked source-review IDs and
candidate-queue IDs appear in the ledgers, with no missing, unexpected, or
duplicate identity.

## Terminal and access outcomes

`source_review_status`:

- `download_connection_error`: 149;
- `download_forbidden`: 1.

`url_access_status`:

- `connection_error`: 149;
- `forbidden`: 1.

`download_status`:

- `connection_error`: 149;
- `forbidden`: 1.

The 150 locked locators each received one logical access attempt. No third
lane or retry ran.

## Content and artifacts

- observed content type: `unknown` for 150 rows;
- observed byte-size distribution: 0 bytes for 150 rows;
- retained content artifacts: 0;
- rows with content hash: 0;
- lane-local response-metadata JSON artifacts: 150;
- content samples: 0;
- total artifact files: 150;
- response-metadata artifact bytes: 114,939;
- retained content bytes: 0;
- total artifact bytes: 114,939;
- maximum artifact size: 805 bytes;
- PDF page count: `unknown` for 150 rows;
- text-layer status: `unknown` for 150 rows.

Every nonblank artifact path resolves inside its lane output directory. The
auditor found all response-metadata files present and reported artifact
integrity passed. No raw response header, auth value, cookie, content sample,
or source body was retained.

## Preliminary ratings

No content-supported rating could be produced:

- `source_officialness_rating = unknown`: 150;
- `source_relevance_rating = unknown`: 150;
- `municipality_match_rating = unknown`: 150;
- `employer_match_rating = unknown`: 150;
- `bargaining_unit_match_rating = unknown`: 150;
- `document_type_rating = unknown`: 150;
- `extraction_readiness_rating = not_ready`: 150.

Wage-table, wage-growth, and mechanism-language signals remain `unknown`.
These outcomes are preliminary source-review transport records, not evidence
about source relevance, employer/unit match, document type, or wage content.

## Error and manual-review burden

The connection/forbidden burden is 150/150 rows. No source body was retained,
so the pilot yielded no hash-bearing content artifact and no useful content
rating. The very high calculated rows/hour reflects fast terminal transport
failure, not productive source review.

No retry is authorized or run in this task. Diagnosis or any retry must be a
separate, bounded, explicitly authorized task.

## Audit and merge boundary

The live lane audit reports:

- two `completed_merge_eligible` lanes;
- planned / ledger / terminal rows: 150 / 150 / 150;
- cross-lane duplicate review IDs: 0;
- cross-lane duplicate queue IDs: 0;
- artifact integrity: passed; and
- recommendation: `merge_all_source_review_lanes`.

That recommendation reflects complete terminal accounting and safe artifacts.
It does not mean content review succeeded. No durable source-review merge
occurred in this task.

## Scaling recommendation

**Do not scale to 500, 750, or 1,000.** Although completion and artifact-safety
gates passed, the substantive scale gates failed:

- retained source bodies: 0/150;
- content hashes: 0/150;
- preliminary rating usefulness: none;
- connection/forbidden burden: 150/150; and
- manual-review/diagnostic burden: 150/150.

A later task should first preserve or merge these terminal outcomes as
authorized, diagnose the connection behavior without broadening the queue,
and obtain explicit authorization for any bounded retry. Speed alone is not a
scale signal. OCR, heavy parsing, and manual review remain inappropriate for
large lanes.

## Boundary confirmation

This task performed only the authorized 150 locator attempts and lane audit.
It did not merge a durable source-review ledger, ingest, codify, extract wage
tables or values, calculate or claim wage gaps, make causal claims, run
regressions, run scouts or URL verification, update scout accounting, mutate
routing or metadata-triage ledgers, or write to contracts, city coverage, or
`corpus/`.
