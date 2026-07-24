# Source-Review Pilot 1 — 150-Row Input Plan

Date: 2026-07-24

Pilot: `SOURCE-REVIEW-PILOT1-150-2026-07-24`

## Result

**PASS.** The offline planner selected 150 unique p1 candidates in two
balanced 75-row lanes. No source content was accessed.

- Full metadata-triage ledger: 4,726 rows
- p1/download-allowed pool: 1,760
- Eligible after strict duplicate/oversized/blocked filters: 1,747
- Selected pilot rows: 150
- Unique source-review IDs: 150
- Unique candidate-queue IDs: 150
- Unique municipalities: 95
- States represented: 43

## Locked lane inputs

| Lane | Rows | SHA-256 |
|---|---:|---|
| 1 | 75 | `0253cba7ecf358e16679f64273466c239e296caf214e44a110813eeebfec6de3` |
| 2 | 75 | `a5baa87593057a49c0b1e9adfff40051725ede45618c6f0d58f90f40b2630b6e` |

## Selected metadata mix

All 150 rows retain:

- original disposition `scheduled`;
- candidate priority `high`;
- candidate source type `cba`;
- routing status `reachable_pdf_or_document`;
- routed content type `application/pdf`;
- metadata triage `high_priority_content_review`;
- metadata priority `p1`; and
- metadata action `content_review_download_allowed_later`.

These are inherited planning labels, not findings from document content.

Unit-type mix:

- police: 73
- fire: 41
- non-safety: 36

Other selection signals:

- likely-official domain signal: 149; unknown: 1;
- matched-set potential yes: 145; no: 5; and
- strict duplicate-group rows: 0.

State distribution:

```text
AK 4  AZ 1  CA 4  CO 4  CT 4  DC 3  DE 4  FL 4  GA 1  HI 3  IA 4
ID 3  IL 4  IN 3  KS 4  KY 1  MA 4  MD 4  ME 4  MI 4  MN 4  MO 4
MS 1  MT 4  NE 4  NH 4  NJ 4  NM 4  NV 4  NY 4  OH 4  OK 4  OR 4
PA 4  RI 4  SD 4  TN 1  TX 4  VA 4  VT 3  WA 4  WI 4  WY 2
```

## Selection method

The planner:

1. required p1 plus `content_review_download_allowed_later`;
2. required the high-priority content-review triage status and preserved the
   scheduled disposition;
3. placed committed CBA labels first;
4. excluded duplicate groups with multiple rows, oversized routing, blocked
   and error routing, lower dispositions, defer, and exclude rows;
5. prioritized likely-official and matched-set-potential metadata; and
6. round-robined across states, municipalities, and police/fire/non-safety
   unit labels before assigning balanced lanes.

The result is representative enough to test the rating schema, artifact
controls, unit matching, and reviewer consistency without authorizing a
1,760-row p1 download wave. It intentionally samples many states and both
safety and non-safety unit labels.

No URL was opened, no document was downloaded or parsed, no OCR was run, and
no final source officialness, relevance, document type, match, or extraction
readiness rating was assigned.
