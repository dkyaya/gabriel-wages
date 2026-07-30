# Validation outputs — 2026-07-30

All final validation commands passed after the candidate-review/dashboard transition was materialized.

- Host-level worker audit: `ps aux | rg '[r]un_broad_state_4x2500_live_scout.py|[l]aunch.*4x2500|[s]cout_lane_00[1-4]'` returned no matching worker.
- Queue locks: `python scripts/run_broad_state_4x2500_live_scout.py --validate-locks` passed with 10,000 master rows and four matching 2,500-row shard hashes.
- Scout regression: `python scripts/test_broad_state_4x2500_live_scout.py` passed.
- Finalization/review generation: `python scripts/finalize_broad_state_4x2500_and_review_candidates.py --run --workers-confirmed-stopped` passed.
- Phase-boundary validation: `python scripts/finalize_broad_state_4x2500_and_review_candidates.py --validate` passed all thirteen gates.
- Independent finalization/review regression: `python scripts/test_finalize_broad_state_4x2500_and_review_candidates.py` passed.
- Dashboard data build: `python scripts/build_dashboard_data.py` passed with 16,887 scout-covered municipalities and 23,018 raw candidate rows across the cumulative discovery layers.
- Dashboard production build: `npm run build --prefix docs/dashboard` passed; Vite emitted only its existing large-chunk advisory.
- Global readiness regression: `python scripts/test_global_analysis_readiness_gate.py` passed 20/20 and preserved the gate values.
- Repository schema: `python scripts/validate.py` passed for 64 contracts, 0 discourse rows, 64 coverage rows, and 3 city-attribute rows.
- Ingestion regression: `python ingest/test_pipeline.py` passed 60/60.
- Whitespace/error audit: `git diff --check` passed.

No network verification, URL opening, source download/inspection, extraction, rating, ingestion, codification, wage comparison, regression, prevalence calculation, or causal analysis was performed by the finalization/review phase.
