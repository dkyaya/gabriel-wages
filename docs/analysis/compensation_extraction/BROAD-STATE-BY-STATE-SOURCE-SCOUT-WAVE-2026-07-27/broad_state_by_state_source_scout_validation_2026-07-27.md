# Broad state-by-state scout validation — 2026-07-27

## Result

PASS. The locked 490-target broad geographic queue, completed live scout, 1,301 discovery candidates, 1,219 deduplicated candidates, dashboard update, and required package artifacts reconcile. All candidates remain discovery metadata only and global analysis readiness remains false.

## Required command results

| Command | Result |
|---|---|
| `.venv/bin/python -m py_compile scripts/build_dashboard_data.py scripts/run_broad_state_by_state_source_scout_wave.py` | PASS |
| `.venv/bin/python scripts/test_bounded_tier_c_evidence_memo_supplement.py` | PASS |
| `.venv/bin/python scripts/test_tier_c_evidence_span_rating_summary_140.py` | PASS |
| `.venv/bin/python scripts/test_dashboard_declutter_map_correction_tier_c_text_span_extraction.py` | PASS |
| `.venv/bin/python scripts/test_broad_state_by_state_source_scout_wave.py` | PASS |
| `.venv/bin/python scripts/test_gabriel_state_source_scout_direct_sdk.py` | PASS |
| `.venv/bin/python scripts/build_dashboard_data.py` | PASS; 51 states/DC, 35,589 municipalities, 2,922 scout-covered municipalities, and 6,027 candidate rows |
| `npm --prefix docs/dashboard run build` | PASS; production bundle created (standard Vite chunk-size advisory only) |
| `.venv/bin/python scripts/validate.py` | PASS (`VALIDATION PASSED`) |
| `.venv/bin/python ingest/test_pipeline.py` | PASS (60 passed, 0 failed) |
| `git diff --check` | PASS |

## Scout and reconciliation checks

- Locked queue: 490 rows; SHA-256 `d54c0becd9f40655199b44ca1ae63f9b3f85dc21d15a33528980471104cc62d2`.
- The queue spans 49 states, with 7–11 targets per included state. DC and Hawaii were not redundantly queued because their local municipality universes were already fully scout-covered.
- Live responses: 490; parseable targets: 486; failed parses: 4.
- Candidate rows: 1,301; deduplicated new-locator candidates: 1,219; duplicates or prior-seen locators: 82.
- Candidate review queue: 1,205 rows. Out-of-scope and duplicate/prior-seen rows are excluded from the review queue.
- Source-family counts reconcile to 1,219 deduplicated candidates. CBA candidates are 317 (26.0%); non-CBA opportunities are 902.
- Preflight passed before live scouting: transport and hosted-search smoke checks passed, the one-target production probe parsed, and sanitized-artifact mode prevented raw prompt/response persistence.
- Dashboard counts reconcile from the prior local baseline: 2,436 + 486 = 2,922 scout-covered municipalities; 4,726 + 1,301 = 6,027 candidate rows.
- Dashboard map contract remains `total_scout_coverage_only`; map data date remains 2026-07-27; global analysis readiness remains false.

## Boundary checks

The task recorded zero direct URL opens, verification HEAD/GET requests, downloads, source-document accesses, OCR runs, render runs, text or span extractions, evidence ratings, ingestion or codification runs, wage-gap calculations, regressions, treatment-effect estimates, national or population-prevalence claims, and final causal claims. Raw prompt and raw response persistence counts are both zero. No predecessor scout, verification, source-review, extraction, rating, quarantine, or durable ledger was mutated.
