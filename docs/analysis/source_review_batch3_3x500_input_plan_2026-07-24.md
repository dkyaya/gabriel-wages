# Source-Review Batch 3 (3×500) Input Plan

Date: 2026-07-24

## Result

`SOURCE-REVIEW-BATCH3-3X500-2026-07-24` is locked at 1,500 rows in three
balanced 500-row lanes. Planning used only the committed cumulative
metadata-triage ledger, candidate queue, and cumulative durable
source-review ledger. No URL was opened and no source was downloaded or
parsed.

## Planner command

```bash
.venv/bin/python scripts/prepare_source_review_pilot.py \
  --triage-ledger-csv docs/analysis/content_triage_ledgers/content_triage_metadata_ledger_cumulative.csv \
  --candidate-queue-csv docs/analysis/national_scout_candidate_queue_2026-07-20.csv \
  --output-dir docs/analysis/source_review_pilots/SOURCE-REVIEW-BATCH3-3X500-2026-07-24 \
  --pilot-id SOURCE-REVIEW-BATCH3-3X500-2026-07-24 \
  --pilot-size 1500 \
  --num-lanes 3 \
  --priority-scope p1_then_p2_download_allowed \
  --state-diversity \
  --source-type-scope cba_first \
  --exclude-duplicates \
  --exclude-oversized \
  --exclude-blocked \
  --exclude-source-review-ledger-csv docs/analysis/source_review_ledgers/source_review_ledger_cumulative.csv \
  --balance-lanes \
  --plan-only
```

## Pool and priority order

- durable metadata-triage rows: 4,726;
- cumulative durable source-review identities excluded: 650;
- default-eligible remaining download-allowed rows: 2,226;
- remaining p1 eligible: 1,097;
- remaining p2 eligible: 1,129;
- remaining p3 eligible: 0;
- selected: 1,500;
- under capacity: no.

The deterministic selection follows the required order:

- p1: 1,097;
- p2: 403;
- p3: 0.

Within each priority level, `cba_first` places CBA-labeled metadata
candidates ahead of other document types while preserving state,
municipality, and unit-type diversity. All 282 remaining eligible p2 CBA
rows were selected before 121 other p2 document candidates.

The plan has:

- unique source-review IDs: 1,500;
- unique candidate-queue IDs: 1,500;
- overlap with the 650 prior candidate identities: 0;
- overlap with prior source-review IDs: 0.

## Lane inputs

| Lane | Rows | p1 | p2 | SHA-256 |
|---|---:|---:|---:|---|
| Lane 1 | 500 | 366 | 134 | `fab5d2666465460fbad18f3039b614e0793ba8179673ae55832f0302627af774` |
| Lane 2 | 500 | 366 | 134 | `54d149db261956c45c9539b077498c50a6644d02aa0f05da7038f3d3c4422c9f` |
| Lane 3 | 500 | 365 | 135 | `aa4b1afa17daf2d2eabd38d0b012df8fe864671dc52a7b20f62b8801020a4991` |

The planner assigns the priority-ordered selection round-robin across the
three lanes. This keeps lane size, priority mix, state coverage, and source
mix balanced while retaining a deterministic global selection rank.

## Selected metadata mix

Candidate source type:

- `cba`: 1,379;
- `wage_schedule_or_compensation_plan`: 64;
- `memorandum_or_settlement`: 23;
- `ordinance_or_policy`: 20;
- `arbitration_award`: 10;
- `factfinding`: 3;
- `pay_plan`: 1.

Routed content type:

- `application/pdf`: 1,500.

Candidate disposition:

- `scheduled`: 1,500.

Unit type:

- police: 655;
- non-safety: 525;
- fire: 320.

Other scheduling signals:

- likely-official domain: 1,429;
- official-domain signal unknown: 71;
- matched-set potential `yes`: 1,249;
- matched-set potential `no`: 251;
- unique municipalities: 798;
- states represented: 47.

State distribution:

```text
AK 5; AL 2; AR 2; AZ 3; CA 236; CO 6; CT 7; DC 2; DE 2; FL 91;
GA 3; IA 6; ID 5; IL 172; IN 4; KS 3; KY 4; LA 3; MA 46; MD 5;
ME 13; MI 83; MN 32; MO 3; MS 2; MT 7; NC 2; ND 2; NE 5; NH 9;
NJ 9; NM 4; NV 3; NY 10; OH 508; OK 4; OR 41; PA 9; SC 2; SD 3;
TN 3; TX 16; UT 3; VA 2; WA 77; WI 37; WV 2; WY 2
```

These distributions are scheduling metadata, not findings about source
officialness, relevance, unit match, document identity, or wage content.

## Artifact projection and disk gate

The 650 durable prior rows retained 1,310,753,493 PDF bytes. At the observed
2,016,544 bytes per selected row, a 1,500-row Batch 3 projects to
approximately 3,024,815,753 retained PDF bytes, plus metadata and filesystem
overhead.

The repository volume had approximately 135.7 GiB available before
planning, so the expected 3 GB-plus collection has adequate headroom. The
per-row cap remains 26,214,400 bytes.

## Planning safety counters

- URLs opened: 0;
- network calls: 0;
- documents downloaded: 0;
- documents/PDFs parsed: 0 / 0;
- OCR runs: 0;
- content artifacts written: 0.

No durable URL-routing, metadata-triage, or source-review ledger was
modified. No scout accounting, ingestion, codification, wage extraction,
wage-gap analysis, causal claim, or regression occurred.
