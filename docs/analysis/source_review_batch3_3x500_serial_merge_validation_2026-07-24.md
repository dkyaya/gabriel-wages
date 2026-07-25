# Source-Review Batch 3 (3×500) Serial-Merge Validation

Date: 2026-07-24

## Result

**PASS.** The offline Batch 3 serial merge, round-specific durable outputs,
cumulative/latest pointers, artifact references, dashboard, and unchanged
upstream layers passed all requested validation gates.

## Commands and results

- Six requested Python modules compiled successfully:
  `source_review_sources.py`, `audit_source_review_lanes.py`,
  `prepare_source_review_pilot.py`, `merge_source_review_lanes.py`,
  `test_source_review_planning.py`, and `build_dashboard_data.py`.
- `scripts/test_source_review_planning.py`: 30 tests passed. These include
  fail-closed merge gates, cumulative-pointer equality, prior-identity
  exclusion, artifact/hash/rating preservation, mocked HTTP behavior, and
  protected-layer isolation.
- The final source-review lane audit reports 1,500/1,500 terminal rows,
  three `completed_merge_eligible` lanes, intact artifacts, and
  `merge_all_source_review_lanes`.
- `scripts/build_dashboard_data.py` completed successfully.
- All 16 dashboard JSON files parsed.
- The dashboard Vite production build completed successfully.
- `scripts/validate.py` passed: 64 contracts, zero discourse rows, 64
  coverage rows, and three city-attribute rows.
- `ingest/test_pipeline.py`: 60 tests passed.
- `ingest/audit_coverage.py` reports 64 contracts, 19 cities, 28 healthy
  matched pairs (10 exact and 18 overlapping), two exploratory adjacent
  matches, and six unmatched safety units.
- `git diff --check` passed.

The exact command outputs are retained under:

`tmp/source_review_pilots/SOURCE-REVIEW-BATCH3-3X500-2026-07-24/batch3_3x500_serial_merge_validation_2026-07-24/`

The final audit artifacts are retained under:

`tmp/source_review_pilots/SOURCE-REVIEW-BATCH3-3X500-2026-07-24/final_serial_merge_validation_lane_audit/`

## Independent durable-ledger and artifact checks

An independent verifier reproduced the cumulative durable ledger by
concatenating the round-specific Pilot 1, Batch 2, and Batch 3 ledgers in
deterministic order. It confirmed:

- cumulative rows: 2,150;
- unique source-review IDs: 2,150;
- unique candidate-queue IDs: 2,150;
- duplicate identities: 0;
- terminal durable-stage rows: 2,150;
- Batch 3 rows: 1,500;
- cumulative saved PDF artifacts: 2,124;
- cumulative content hashes independently matching retained files: 2,124;
- cumulative retained PDF bytes: 4,500,367,582;
- cumulative response-metadata bytes: 2,330,781;
- cumulative total artifact bytes: 4,502,698,363;
- maximum retained PDF: 10,470,269 bytes;
- all content paths lane-local;
- all retained content begins with a PDF signature;
- metadata JSON records checked: 2,150; and
- secret-bearing metadata keys found: 0.

The cumulative/latest ledger pair is byte-identical, as is the
cumulative/latest summary pair.

## Immutability and process boundary

Post-merge hashes match the pre-merge baselines for:

- `data/contracts.csv`;
- `data/city_coverage.csv`;
- the national candidate queue;
- scout-coverage accounting;
- the cumulative URL-routing ledger;
- the cumulative metadata-triage ledger;
- the 150-row Pilot 1 durable ledger;
- the 500-row Batch 2 durable ledger; and
- all 79 files under `corpus/`.

The merge counters record zero URL opens, network calls, downloads, document
parses, PDF parses, OCR runs, content samples, ingestion actions, codify
actions, wage extractions, wage-gap calculations, causal claims, and
regressions. No live source review ran during the merge.

The unrelated untracked root `package-lock.json` existed before this task
and remained outside the work and commit.

## Interpretation

Validation establishes durable identity, artifact, and status integrity. It
does not turn preliminary access/artifact-metadata fields into final source
ratings, content-supported relevance, confirmed bargaining-unit matches,
extraction-ready evidence, ingested sources, codified evidence, or wage
observations. No retained PDF was parsed or OCRed.
