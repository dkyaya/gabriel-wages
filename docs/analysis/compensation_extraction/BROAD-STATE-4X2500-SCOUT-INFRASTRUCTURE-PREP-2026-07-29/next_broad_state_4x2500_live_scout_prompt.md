# Next task: broad state 4 × 2,500 live scout

Run exactly four independent live scouting lanes over the committed locked shards:
- lane_001 / broad_4x2500_shard_001: 2,500 targets, T+0.
- lane_002 / broad_4x2500_shard_002: 2,500 targets, T+8.
- lane_003 / broad_4x2500_shard_003: 2,500 targets, T+16.
- lane_004 / broad_4x2500_shard_004: 2,500 targets, T+24.

Controlled overlap is required. Each worker is independently runnable and resumable, writes only to its isolated lane directory, validates its committed queue hash, and checkpoints after every target. Workers must not update dashboard/status/docs. The coordinator merges completed outcomes, counts only unique committed parseable municipalities as actual coverage, updates the dashboard once, and emits a resume prompt for incomplete lanes.

This is scouting only. Do not run candidate review, verification, URL checking, download, source review, source inspection, text/span extraction, rating, ingestion, codification, quantitative normalization, wage-gap analysis, regression, treatment effects, prevalence analysis, or causal analysis. Candidate review remains deferred until all shards finish or the user explicitly stops scouting. Keep the map on total scout coverage only and keep global_analysis_readiness false.

Future rating tasks must verify all downstream summary inputs before closing. Reconstruct fully derivable missing summaries deterministically from committed valid/quarantine/results ledgers; fail closed for missing non-derivable artifacts.
