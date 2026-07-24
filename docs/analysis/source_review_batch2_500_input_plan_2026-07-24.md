# Source-Review Batch 2 (500 Rows) Input Plan

Date: 2026-07-24

## Result

**PASS.** `SOURCE-REVIEW-BATCH2-500-2026-07-24` is locked to 500 unique
metadata-triaged candidates in two balanced 250-row lanes. No Pilot 1
candidate or source-review identity is present.

The exact offline planning command was:

```text
.venv/bin/python scripts/prepare_source_review_pilot.py \
  --triage-ledger-csv docs/analysis/content_triage_ledgers/content_triage_metadata_ledger_cumulative.csv \
  --candidate-queue-csv docs/analysis/national_scout_candidate_queue_2026-07-20.csv \
  --output-dir docs/analysis/source_review_pilots/SOURCE-REVIEW-BATCH2-500-2026-07-24 \
  --pilot-id SOURCE-REVIEW-BATCH2-500-2026-07-24 \
  --pilot-size 500 \
  --num-lanes 2 \
  --priority-scope p1_download_allowed \
  --state-diversity \
  --source-type-scope cba_first \
  --exclude-duplicates \
  --exclude-oversized \
  --exclude-blocked \
  --exclude-source-review-ledger-csv docs/analysis/source_review_ledgers/SOURCE-REVIEW-PILOT1-150-2026-07-24/source_review_ledger.csv \
  --balance-lanes \
  --plan-only
```

The planner read only the durable metadata-triage ledger, canonical candidate
queue, and durable Pilot 1 source-review ledger. It opened zero URLs and made
zero network calls.

## Pool and exclusion accounting

- durable metadata-triage rows: 4,726;
- p1 rows: 1,760;
- p1/download-allowed rows: 1,760;
- eligible after source-type, routing, disposition, duplicate, oversized, and
  blocked filters but before prior-review exclusion: 1,747;
- Pilot 1 durable rows read: 150;
- prior candidate identities excluded: 150;
- prior source-review identities recorded for collision checks: 150;
- final eligible pool: 1,597;
- selected Batch 2 rows: 500;
- Batch 2/Pilot 1 candidate overlap: 0;
- Batch 2/Pilot 1 source-review ID overlap: 0;
- duplicate Batch 2 candidate IDs: 0;
- duplicate Batch 2 source-review IDs: 0.

For every selected row, candidate, routing, and metadata-triage identities and
labels equal the durable metadata-triage source row.

## Locked lanes

| Lane | Rows | SHA-256 |
|---|---:|---|
| Lane 1 | 250 | `41a93aafc50c628db05de4597600ceccb20429d9c0a24d926a751b21ac061cef` |
| Lane 2 | 250 | `51050f366f98313719d1848aefec7ea3983c5abad0ceaa6433f7c1617c2469c9` |

Inputs:

- `docs/analysis/source_review_pilots/SOURCE-REVIEW-BATCH2-500-2026-07-24/lane_1_source_review_input.csv`
- `docs/analysis/source_review_pilots/SOURCE-REVIEW-BATCH2-500-2026-07-24/lane_2_source_review_input.csv`

## Selected metadata mix

- states represented: 35;
- unique municipalities: 310;
- candidate source type: 500 `cba`;
- routed content type: 500 `application/pdf`;
- original disposition: 500 `scheduled`;
- metadata priority: 500 p1;
- recommended action: 500
  `content_review_download_allowed_later`;
- likely-official domain signal: 494;
- unknown official-domain signal: 6;
- matched-set potential yes / no: 455 / 45.

Unit labels:

- police: 197;
- fire: 151;
- non-safety: 152.

State counts:

- 26 each: CA, FL, IL, MI, OH;
- 25 each: CT, MA, MN, OR, WA, WI;
- IA 22; NY 19; TX 19; PA 17; NJ 15; NV 15; MT 13; NH 10;
- MO 9; RI 9; MD 8; NE 8; OK 8; ME 7; KS 6; NM 6; AK 5;
- CO 4; DE 4; VA 4; ID 3; IN 3; SD 3; VT 3.

These labels prioritize and diversify source-access work. They do not confirm
that any selected artifact is a CBA, official, relevant, correctly matched,
wage-bearing, or extraction-ready.

## Capacity projection and boundary

Pilot 1's observed retained-content volume projects to approximately
1,006,568,200 bytes for 500 selected rows if yield and size remain similar.
The live runner remains capped at 26,214,400 bytes per row and writes only
lane-local artifacts.

Planning opened no URLs, downloaded or parsed no documents, ran no OCR,
wrote no content artifacts, and did not mutate scout accounting, routing,
metadata-triage, durable source-review, ingestion, codification, contract,
coverage, corpus, or analysis layers.
