# Post-Batch-3 Source-Review Next-Phase Plan

Date: 2026-07-24

## Current durable state

Batch 3 has passed its serial offline merge. The durable source-review layer
now contains:

- Pilot 1: 150 rows;
- Batch 2: 500 rows;
- Batch 3: 1,500 rows;
- cumulative source-review rows: 2,150;
- cumulative retained PDF artifacts: 2,124;
- cumulative retained PDF bytes: 4,500,367,582;
- cumulative response-metadata bytes: 2,330,781;
- cumulative total artifact bytes: 4,502,698,363;
- timeout outcomes: 21;
- forbidden outcomes: 5;
- repaired HTTPX connection errors: 0; and
- parsed PDFs / OCR runs: 0 / 0.

All ratings remain preliminary access/artifact-metadata signals.

## Remaining download-allowed pool

Against the 2,150 durable candidate identities:

- raw metadata-triage download-allowed remainder: 773 rows;
  - p1: 13;
  - p2: 760;
  - p3: 0.
- default planner-eligible remainder after duplicate, oversized, blocked,
  lower-disposition, defer and exclude gates: 726 rows;
  - p1: 0;
  - p2: 726;
  - p3: 0.

The 13 raw remaining p1 identities and 34 of the raw p2 identities fail at
least one default source-review planning gate. They should not be promoted
merely to exhaust the download-allowed queue.

## Why not automatically download the remaining p2 pool

Basic bounded HTTP access is no longer the principal uncertainty. The
repaired client has zero connection errors across 2,150 durable attempts and
retained 2,124 artifacts. The next bottleneck is technical and substantive
readiness:

- no retained PDF has been parsed;
- all page counts are unknown;
- all text-layer statuses are unknown;
- all wage-table, wage-growth and mechanism-language signals are unknown;
- source relevance and municipality/employer/unit match remain
  possible/unknown rather than content-confirmed;
- the durable artifacts already occupy approximately 4.50 GB; and
- downloading 726 more sources would increase storage and audit burden
  without showing whether the existing corpus is cheaply parseable.

The access layer therefore has enough scale for a readiness test. More
downloading should depend on what that test learns.

## Recommended next task

Prepare and run a bounded text-layer/page-count readiness pilot over
**100–200 retained PDFs**, with 150 as the suggested default.

Sampling should include:

- Pilot 1, Batch 2 and Batch 3 artifacts;
- p1 and p2 metadata priorities;
- police, fire and non-safety units;
- municipal, state-repository, union and uncertain officialness signals;
- a range of retained byte sizes and states; and
- distinct candidate and source-review identities.

The readiness runner should operate only on already-retained local artifacts.
It should not open URLs or redownload documents.

Required outputs per sampled artifact:

- source-review and candidate identity;
- local artifact path and verified SHA-256;
- observed byte size and content type;
- PDF page count when safely available;
- text-layer status:
  - present;
  - absent;
  - partial/uncertain;
  - unreadable/error;
- bounded parser success/failure category;
- basic technical parseability/readiness rating;
- parser/library and version;
- elapsed time; and
- sanitized error category.

## Pilot boundaries

The readiness pilot should:

- use a lightweight local PDF library already available or explicitly
  approved;
- cap work per file and fail terminally;
- avoid saving full extracted text;
- avoid OCR;
- avoid wage-table and wage-value extraction;
- avoid mechanism classification;
- avoid ingestion and `gabriel.codify`;
- avoid edits to `data/contracts.csv`, `data/city_coverage.csv`, `corpus/`,
  scout accounting, URL-routing ledgers and metadata-triage ledgers; and
- stop before any durable parsing/readiness merge unless separately
  authorized.

Page count and text-layer presence are technical properties. They do not
establish source relevance, document identity, wage content or empirical
findings.

## Decisions after the readiness pilot

Use the pilot to choose among:

1. **Finish the remaining 726 p2 downloads** if retained PDFs are commonly
   parseable, storage remains comfortable and broader access coverage adds
   value.
2. **Run a larger local text-layer/page-count pass** if technical readiness
   is informative and inexpensive but the sample is too small for planning.
3. **Design a bounded wage-table extraction pilot** only from artifacts whose
   content, identity and parseability gates are confirmed.
4. **Create a separate OCR strategy** only for the text-layer-absent subset,
   with smaller lanes and separate authorization.

No wage extraction, wage-gap analysis or regression should begin solely
because the access/artifact layer is now large.
