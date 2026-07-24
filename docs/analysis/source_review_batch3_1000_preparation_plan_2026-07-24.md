# Source-Review Batch 3 (1,000 Rows) Preparation Plan

Date: 2026-07-24

This is a planning note only. No Batch 3 input, lane, dry-run, URL access,
download, or artifact directory is created in this task.

## Starting point

The Batch 2 serial merge passed and created:

- 500 durable Batch 2 rows;
- 650 cumulative durable source-review rows;
- 644 retained PDF artifacts;
- 1,310,753,493 cumulative retained PDF bytes;
- zero cumulative connection errors;
- zero PDF parses, OCR runs, or content samples.

The durable results remain preliminary source-access and artifact-metadata
signals.

## Remaining pool

The cumulative metadata-triage ledger has 1,760 rows satisfying both:

- `priority_for_content_review = p1`; and
- `recommended_next_action = content_review_download_allowed_later`.

All 650 durable source-review candidate identities belong to that pool and
are unique. Therefore:

- raw p1/download-allowed rows remaining: 1,110;
- remaining after the planner's default duplicate exclusion: 1,097;
- proposed Batch 3 selection: 1,000;
- default-eligible identities remaining after Batch 3: approximately 97.

The eventual planner must recompute these values from the cumulative
metadata-triage and source-review ledgers and fail if they differ materially.

## Proposed batch

Round ID:

`SOURCE-REVIEW-BATCH3-1000-2026-07-24`

Selection:

- 1,000 p1/download-allowed rows;
- exclude all 650 cumulative durable source-review candidate identities;
- exclude duplicate-deferred, oversized, blocked and lower-disposition rows;
- preserve candidate, verification and metadata-triage identities;
- preserve state, municipality, source-owner and safety/non-safety diversity;
- deterministic selection and lane hashes required.

## Lane design

Recommend **four balanced lanes of 250 rows**, operated in two gated waves
of at most two concurrent lanes.

Why:

- Batch 2 proved the 250-row lane shape, checkpoint behavior and artifact
  audit burden;
- each Batch 2 lane retained about 475–534 MB, while a 500-row lane would
  likely retain about 1 GB;
- four 250-row lanes limit the amount at risk from one interrupted lane;
- running at most two lanes simultaneously preserves the proven aggregate
  concurrency of eight rather than increasing it to sixteen;
- lane-local validation and selective resume remain manageable.

Do not use four simultaneously launched lanes merely because four inputs
exist.

## Expected artifact volume

Pilot 1 plus Batch 2 retained 1,310,753,493 bytes across 644 PDFs from 650
selected rows:

- approximately 2.04 MB per retained PDF;
- approximately 2.02 MB per selected row;
- observed artifact yield: about 99.1%.

A 1,000-row Batch 3 would therefore be expected to retain roughly
2.0–2.1 GB of PDF content, plus metadata, logs, filesystem overhead,
validation reads, and any relay copy. Planning should reserve materially
more than the content estimate—preferably at least 5 GB of free working
headroom beyond existing artifacts—and stop if that capacity is unavailable.

## Bounded live settings

Keep the established settings:

- concurrency: 4 per active lane;
- maximum concurrently active lanes: 2;
- total timeout: 30 seconds;
- connect timeout: 8 seconds;
- read timeout: 20 seconds;
- maximum redirects: 5;
- maximum bytes: 26,214,400 per row;
- environment proxy inheritance: off;
- content samples: off;
- OCR: off;
- PDF parsing: off;
- text and wage extraction: off;
- lane-local artifacts and incremental ledgers required.

## Gates after Batch 3

Before a merge or any further scale decision, require:

1. 1,000/1,000 terminal coverage and zero duplicate identities;
2. zero overlap with all 650 prior durable candidate identities;
3. lane-local artifact paths, matching hashes and matching sizes;
4. total and maximum artifact volume within planned limits;
5. documented timeout, forbidden, connection, SSL, not-found and
   too-large rates;
6. documented manual-review burden;
7. review of whether preliminary ratings are useful without parsing;
8. confirmation that no content sample, PDF parse, OCR, ingestion,
   codification or wage extraction occurred;
9. a separate serial merge and relay review.

## Authorization boundary

Do not prepare Batch 3 inputs or run Batch 3 until the Batch 2 merge commit,
durable 650-row ledger, dashboard refresh, validation, and relay have been
reviewed. This note does not authorize any URL access.
