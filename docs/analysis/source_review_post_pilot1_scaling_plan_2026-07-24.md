# Source Review After Pilot 1: Scaling Plan

Date: 2026-07-24

## Current position

The repaired HTTPX retry for
`SOURCE-REVIEW-PILOT1-150-2026-07-24` is durably merged. It contains 150
terminal rows, 149 retained PDF artifacts with matching hashes, one forbidden
row, and zero connection errors. The original `d97f5e4` attempt is preserved
but superseded because its 149 connection errors came from the retired
source-review-only transport path.

Pilot 1 supports planning a bounded follow-on because terminal coverage,
artifact locality, content hashes, size integrity, error burden, and bounded
transport all passed. It does not support interpreting the artifacts as
confirmed CBAs or extracting wages: the PDFs have not been parsed, text-layer
availability and page counts are unknown, and relevance and employer/unit
matches remain preliminary.

## Recommended next batch

Prepare, but do not run without separate authorization:

`SOURCE-REVIEW-BATCH2-500-2026-07-24`

Recommended selection:

- 500 p1, `content_review_download_allowed_later` rows;
- exclude the 150 Pilot 1 candidate identities;
- exclude duplicate-deferred, oversized, blocked, and lower-disposition rows;
- preserve state, municipality, and safety/non-safety diversity;
- retain the same candidate, routing, and metadata-triage identities.

Recommended lane design: **two balanced lanes of 250 rows**.

Two lanes preserve the proven Pilot 1 operating shape and cap aggregate
concurrency at eight while avoiding the extra cross-lane artifact and
duplicate audit surface of a third lane. Each lane would likely retain about
500 MB if artifact yield and mean size resemble Pilot 1, which is substantial
but still easier to checkpoint and audit than a single 500-row lane. If local
disk headroom is inadequate at planning time, the planner should stop rather
than silently reduce safeguards or overwrite existing artifacts.

Recommended bounded settings:

- concurrency: 4 per lane;
- total timeout: 30 seconds;
- connect timeout: 8 seconds;
- read timeout: 20 seconds;
- maximum redirects: 5;
- maximum bytes: 26,214,400 per row;
- environment proxy inheritance: off;
- content samples: off;
- OCR: off;
- PDF parsing and wage extraction: off;
- lane-local artifacts and incremental checkpoints required.

## Why not 750 or 1,000 yet

Pilot 1 retained 301,970,460 bytes across 149 artifacts. A simple linear
projection is about 1,006,568,200 bytes for 500 rows and about
2,013,136,400 bytes for 1,000 rows, before metadata, logs, duplicate copies,
filesystem overhead, or unusually large documents. These projections are
capacity estimates, not promises.

More importantly:

- ratings remain preliminary access/artifact signals;
- PDFs were not parsed;
- page count and text-layer availability are unknown;
- actual relevance, document type, employer/unit match, and wage-content
  yield have not been measured;
- storage and review burden grow with artifact count even when transport is
  fast;
- speed alone does not establish that a larger batch produces useful research
  evidence.

The 500-row batch should therefore be the next scaling checkpoint. A direct
jump to 750 or 1,000 is not recommended.

## Gates after 500

Before any further scale decision, require:

1. complete terminal coverage and zero duplicate identities;
2. lane-local artifact paths, matching hashes, and matching recorded sizes;
3. total and maximum artifact volume within planned disk limits;
4. stable transport errors and a documented manual-review burden;
5. a decision about whether bounded PDF metadata/text-layer inspection is
   needed before further source-access scale;
6. evidence that preliminary officialness/relevance/match ratings are useful
   for prioritization;
7. preservation of the no-ingestion, no-codify, no-wage-extraction boundary;
8. separate serial merge and relay review.

OCR, heavy PDF parsing, content interpretation, and manual source rating
should use smaller purpose-built batches. Ingestion planning should begin
only after actual content-review and source-rating gates. Wage extraction,
wage-gap analysis, and regressions remain later phases.
