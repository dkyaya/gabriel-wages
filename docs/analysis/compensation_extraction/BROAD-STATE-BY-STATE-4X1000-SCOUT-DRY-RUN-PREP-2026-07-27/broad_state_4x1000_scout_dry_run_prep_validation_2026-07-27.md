# Validation report — 2026-07-27

## Result

PASS. The 4,000-row master, four 1,000-row shard queues, 4,000 unique-municipality plan, source-family rotation, prior-candidate preservation control, no-call boundary, and dashboard accounting all reconcile. Actual coverage remains 2,922 and actual candidate rows remain 6,027.

## Required command results

| Command | Result |
|---|---|
| `.venv/bin/python -m py_compile scripts/build_dashboard_data.py scripts/run_broad_state_4x1000_scout_dry_run_prep.py scripts/test_broad_state_4x1000_scout_dry_run_prep.py` | PASS |
| `.venv/bin/python scripts/test_broad_state_by_state_source_scout_wave.py` | PASS |
| `.venv/bin/python scripts/test_bounded_tier_c_evidence_memo_supplement.py` | PASS |
| `.venv/bin/python scripts/test_dashboard_declutter_map_correction_tier_c_text_span_extraction.py` | PASS |
| `.venv/bin/python scripts/test_broad_state_4x1000_scout_dry_run_prep.py` | PASS; complete-package validation produced zero writes |
| `.venv/bin/python scripts/build_dashboard_data.py` | PASS; 51 states/DC, 35,589 municipalities, 2,922 actually scout-covered, 6,027 actual candidate rows |
| `npm --prefix docs/dashboard run build` | PASS; production bundle created, with the standard non-fatal Vite chunk-size advisory |
| `.venv/bin/python scripts/validate.py` | PASS (`VALIDATION PASSED`) |
| `.venv/bin/python ingest/test_pipeline.py` | PASS (60 passed, 0 failed) |
| `git diff --check` | PASS |

## Queue and shard checks

- Master count: 4,000; unique municipalities: 4,000.
- Shards: four controlled IDs with exactly 1,000 targets apiece.
- Every shard contains all four regions, at least 48 states, and exactly 125 targets from each of eight source-family query bundles.
- Master queue equals the exact union of shard queues.
- Maximum planned state allocation: 87 targets, or 2.175% of the master.
- All targets are locally enumerated, future-scout eligible, absent from actual coverage, and absent from the prior 490-target queue.
- Weak, duplicate, and needs-review target tiers are excluded.
- The prior 1,205-row candidate-review queue hash is preserved in the planning package; candidate review did not occur.

## Boundary checks

Hosted-search, direct-SDK, API/model, URL-open, HEAD/GET, download, source-document, candidate-review, OCR, rendering, extraction, span, rating, ingestion, codification, quantitative, wage-gap, regression, treatment-effect, national/population-prevalence, and final-causal counters are all zero. Raw prompt and response persistence are zero. Planned municipalities were not added to the dashboard map, and global analysis readiness remains false.
