# Scaled Candidate-Source Verification Framework Validation

Date: 2026-07-23/24
Mode: offline planning and dry-run validation only

## Result

**PASS.** The framework prepares and audits deterministic verification plans
without opening a URL or making a network/API/model call.

## Commands and checks

- Five requested Python modules compile.
- `scripts/test_scaled_verification_batches.py` passes five reported checks:
  identity preservation and exact duplicate groups; scheduled/held/duplicate
  scope switches; canonical 3×250 planning; no-network dry runner plus lane
  auditor; and candidate queue/coverage hash invariance.
- The canonical Round 1 planner reproducibly selects 750 scheduled rows into
  lanes of 250/250/250, with 750 unique verification IDs and queue IDs.
- All first-round rows are high-priority scheduled candidates because the
  high-priority pool contains 2,825 rows.
- The full-backlog inventory contains all 4,726 original queue IDs exactly
  once. Five nominal 3×250 rounds cover the 3,600 scheduled rows; two
  additional rounds cover the 1,126 separate dispositions.
- Each of the three real lane dry runs writes 250 ledger/timing rows. The
  combined auditor classifies all three `dry_run_passed`, inspects 750 rows,
  finds zero cross-lane ID duplication, and recommends
  `dry_run_complete_do_not_merge_live_ledger`.
- `scripts/build_dashboard_data.py` reports 51 states/DC, 35,589 universe
  rows, 2,436 scout-covered municipalities, and 4,726 candidate rows.
- Fourteen dashboard JSON files parse, including the new
  `verification_status_summary.json`.
- `python scripts/validate.py` passes.
- `python ingest/test_pipeline.py` passes 60/60.
- `python ingest/audit_coverage.py` reports 64 contracts, 19 cities, 28
  healthy matched pairs (10 exact and 18 overlap), two exploratory adjacent
  pairs, and six unmatched safety units.
- The dashboard production build passes with 43 transformed modules.
- `git diff --check` passes.

The first dashboard log-capture command pointed `tee` one directory above the
repository and returned a missing-log-path error after Vite itself completed.
The same build was immediately rerun with the correct path and passed; the
successful output is preserved in
`tmp/scaled_verification_framework_validation_2026-07-23/`.

## Invariance and safety

Final SHA-256 checks remain:

- `data/contracts.csv`:
  `ed26cff96061e45ff668a02231547a6c9c11ec4b138772bfb3d5de34a229e1e8`
- `data/city_coverage.csv`:
  `4fdf135ff3741893f5a4c45edc52a70159adc87598b777dfc4373dd8481249e3`
- candidate queue:
  `d46b8bc3c60cbbda9b2f6f618fc447d1878d610fa1beb0924e7bafd47f965e83`
- municipality coverage:
  `2339ecc448f0252a5a1d533e458688d7b9e8359a5b6af013784fef4f6847e96c`
- state coverage:
  `bad2948a2990e91280b510e5d93c1ab29aa65959f83693a641a1e902836e5a21`
- county coverage:
  `717fa7534f3bbc41c70136dab249a61cb037e72f5b65fa93ca18bb06ff5c6033`
- aggregate corpus hash:
  `8a449bed6ccaf66e40083a1179b2cf2ee6481c781617ecacdc30f8e236c8611a`

No candidate URL was opened or resolved. No live verification, live scout,
hosted search, network/API/model call, source download, ingestion,
`gabriel.codify`, wage extraction, wage-gap calculation/claim, causal claim,
regression, candidate promotion, remote action, or push occurred. Queue and
coverage accounting and protected contract/corpus paths are unchanged.
