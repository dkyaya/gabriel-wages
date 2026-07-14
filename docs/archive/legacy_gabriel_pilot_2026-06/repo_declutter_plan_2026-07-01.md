# Repo Declutter Plan

**Date:** 2026-07-01  
**Status:** planning only; do not delete, move, or rename files yet

## 1. Purpose

This memo proposes an all-repo declutter and archive plan for `gabriel-wages`. The goal is to separate active production inputs and current report materials from historical analysis outputs, generated artifacts, and branch-specific scaffolding without breaking reproducibility, provenance, or current Thursday reporting work.

## 2. Principles

- Preserve provenance.
- Do not touch production data or the source corpus.
- Archive before delete.
- Keep final reports and active inputs visible.
- Keep code that can reproduce outputs.
- Move generated outputs only after confirming they are reproducible.
- Avoid breaking report links before Thursday.

## 3. Folder-level inventory

### Core active data and schema

- `data/`
- `docs/schema.md`
- `docs/hypotheses.md`
- `docs/hypotheses_public_source_strategy_2026-06-24.md`

These are the analytical spine of the repo and should remain visible.

### Corpus and ingestion pipeline

- `corpus/`
- `inbox/`
- `ingest/`
- `scripts/validate.py`

These are active production/source-management components and should not be reorganized casually.

### Active GABRIEL scoring code

- `analysis/gabriel_pilot/run_gabriel.py`
- `analysis/gabriel_pilot/run_gabriel_v9.py`
- `analysis/gabriel_pilot/run_gabriel_v10_gold_dryrun.py`
- `analysis/gabriel_pilot/build_input.py`
- `analysis/gabriel_pilot/build_input_v9.py`
- `analysis/gabriel_pilot/summarize_v9.py`
- `analysis/gabriel_pilot/plot_results.py`

### Active GABRIEL outputs

- `analysis/gabriel_pilot/input_v9.csv`
- `analysis/gabriel_pilot/results_v9_model_raw.csv`
- `analysis/gabriel_pilot/results_v9.csv`
- `analysis/gabriel_pilot/results_v9_quote_audit.csv`
- `analysis/gabriel_pilot/results_v9_summary_*.csv`
- `analysis/gabriel_pilot/results_v9_matched_pair_summary.csv`
- `analysis/gabriel_pilot/figures_v9/`
- `docs/analysis/gabriel_v9_preliminary_report_2026-06-25.md`

These are still wired into the current descriptive reporting stack.

### Historical GABRIEL outputs

- `analysis/gabriel_pilot/results.csv`
- `analysis/gabriel_pilot/results_v2.csv` through `results_v8.csv`
- `analysis/gabriel_pilot/report_v3.md`
- `analysis/gabriel_pilot/Graphs V1/`
- `analysis/gabriel_pilot/Graphs V2/`
- `analysis/gabriel_pilot/Graphs V3/`

These are valuable historical analysis artifacts but are no longer the visible active layer.

### Acquisition memos and search/recon notes

- `docs/acquisition/`
- `docs/ma_source_inventory.md`
- `docs/records_requests/`

These are provenance-heavy research process records; many are historical but should be preserved.

### Reports and presentation artifacts

- `reports/6_25/`
- `docs/analysis/gabriel_v9_preliminary_report_2026-06-25.md`
- Thursday report files under `docs/analysis/`

Some are active, some are final deliverables, and some are later archive candidates.

### Web-search scaffold and Thursday package

- `analysis/gabriel_pilot/gabriel_websearch_custom_fn.py`
- `analysis/gabriel_pilot/run_gabriel_websearch_seed_demo.py`
- `analysis/gabriel_pilot/results_gabriel_websearch_seed_demo_2026-06-30.csv`
- `analysis/gabriel_pilot/results_gabriel_websearch_seed_demo_sources_2026-06-30.csv`
- `analysis/gabriel_pilot/results_gabriel_websearch_seed_demo_extractions_2026-06-30.csv`
- `docs/acquisition/gabriel_websearch_*`
- `docs/analysis/gabriel_websearch_*`

This area is coherent but currently cluttered by scaffold docs, seed outputs, and Thursday-facing materials.

### Comparator-network artifacts

- `docs/analysis/comparator_network_design_2026-06-29.md`
- `docs/analysis/comparator_edge_synthesis_2026-06-29.md`
- `docs/analysis/comparator_edges_from_boston_btu_table_2026-06-29.md`
- `docs/analysis/comparator_edges_from_v9_verified_excerpts_2026-06-29.md`
- `docs/analysis/comparator_mentions_stub_2026-06-29.csv`

These are mostly design/provenance work products rather than active production datasets.

### Logs and API spend

- `logs/api_spend_log.csv`
- `scripts/log_api_spend.py`

Keep visible; they are active process-control artifacts.

### Generated figures

- `analysis/gabriel_pilot/figures_v9/`
- `analysis/gabriel_pilot/Graphs V1/`
- `analysis/gabriel_pilot/Graphs V2/`
- `analysis/gabriel_pilot/Graphs V3/`

### Temporary/demo/seed files

- `analysis/gabriel_pilot/scratch_pdfs/`
- `analysis/gabriel_pilot/results_gabriel_websearch_seed_demo*.csv`
- `docs/analysis/gabriel_websearch_report_assets_2026-07-01/`
- `.DS_Store`
- `__pycache__/`

### Test files and validation scripts

- `ingest/test_pipeline.py`
- `scripts/validate.py`
- `ingest/audit_coverage.py`

## 4. Keep active

- `data/`
- `corpus/`
- `inbox/`
- `ingest/`
- `scripts/`
- `logs/api_spend_log.csv`
- `docs/schema.md`
- `docs/hypotheses.md`
- `docs/hypotheses_public_source_strategy_2026-06-24.md`
- `docs/analysis/chatgpt_handoff_latest.md`
- `PROGRESS.md`
- `analysis/gabriel_pilot/` code files
- v9 active inputs/results/figures used by current descriptive reporting
- current Thursday report-facing web-search files in `docs/analysis/`

Reason: these are either production inputs, active code, active reporting files, or current session-control files.

## 5. Archive after Thursday report finalization

- `docs/analysis/gabriel_websearch_live_smoke_test_status_2026-07-01.md`
- `docs/analysis/gabriel_websearch_report_assets_2026-07-01/`
- `docs/analysis/gabriel_websearch_mass_city_pilot_summary_2026-06-30.md`
- `analysis/gabriel_pilot/results_gabriel_websearch_seed_demo_2026-06-30.csv`
- `analysis/gabriel_pilot/results_gabriel_websearch_seed_demo_sources_2026-06-30.csv`
- `analysis/gabriel_pilot/results_gabriel_websearch_seed_demo_extractions_2026-06-30.csv`

Reason: these support the Thursday package but should not dominate the main active directories once the report is finalized.

## 6. Archive after v10/web-search branch stabilizes

- `docs/analysis/gabriel_v10_gold_dryrun_report_2026-06-29.md`
- `docs/analysis/gabriel_v10_gold_repaired_dryrun_report_2026-06-30.md`
- `docs/analysis/gabriel_v10_gold_set_memo_2026-06-29.md`
- `docs/analysis/gabriel_v10_gold_set_repair_memo_2026-06-30.md`
- `docs/analysis/gabriel_v10_gold_set_2026-06-29.csv`
- `docs/analysis/gabriel_v10_gold_set_repaired_2026-06-30.csv`
- `analysis/gabriel_pilot/input_v10_gold_2026-06-29.csv`
- `analysis/gabriel_pilot/input_v10_gold_repaired_2026-06-30.csv`
- `analysis/gabriel_pilot/results_v10_gold_dryrun_2026-06-29.csv`
- `analysis/gabriel_pilot/results_v10_gold_dryrun_audit_2026-06-29.csv`
- `analysis/gabriel_pilot/results_v10_gold_repaired_dryrun_2026-06-30.csv`
- `analysis/gabriel_pilot/results_v10_gold_repaired_dryrun_audit_2026-06-30.csv`

Reason: they are current design-branch artifacts, but still referenced by analysis memos and the handoff log.

## 7. Generated outputs safe to regenerate

- `analysis/gabriel_pilot/figures_v9/`
- `analysis/gabriel_pilot/Graphs V1/`
- `analysis/gabriel_pilot/Graphs V2/`
- `analysis/gabriel_pilot/Graphs V3/`
- `analysis/gabriel_pilot/results_v9_summary_*.csv`
- `analysis/gabriel_pilot/results_v9_matched_pair_summary.csv`
- `analysis/gabriel_pilot/results_v9_quote_audit.csv`
- `analysis/gabriel_pilot/results_gabriel_websearch_seed_demo*.csv`
- `.DS_Store`
- `__pycache__/`
- `analysis/gabriel_pilot/scratch_pdfs/`

Move these only after verifying the code path that reproduces them remains intact.

## 8. Historical/provenance files to keep but relocate later

- `docs/acquisition/*.md`
- `docs/records_requests/*.md`
- `docs/session_snapshots/*.md`
- `docs/ma_source_inventory.md`
- `inbox/processed_manifest.csv`
- `docs/analysis/comparator_*.md`
- `docs/analysis/comparator_mentions_stub_2026-06-29.csv`
- `analysis/gabriel_pilot/report_v3.md`
- `reports/6_25/`

Reason: these preserve research process, historical decisions, and deliverable provenance even when they are no longer active inputs.

## 9. Files/folders that should not be touched

- `data/contracts.csv`
- `data/city_coverage.csv`
- `data/discourse.csv`
- `data/city_attributes.csv`
- `corpus/`
- `inbox/`
- `ingest/`
- `scripts/validate.py`
- `ingest/audit_coverage.py`
- `logs/api_spend_log.csv`

These are production data, production provenance, or validation infrastructure.

## 10. Candidate archive layout

Do not create these folders yet. This is only the proposed end state.

```text
docs/archive/
  acquisition_recon_2026-06/
  comparator_network_2026-06/
  gabriel_v8_v9_debug_2026-06/
  gabriel_v10_gold_2026-06/
  gabriel_websearch_scaffold_2026-07/
  obsolete_reports_2026-06/

analysis/archive/
  gabriel_pilot_generated_2026-06/
  gabriel_v10_gold_generated_2026-06/
  websearch_seed_outputs_2026-07/
  legacy_graphs_v1_v3_2026-06/
```

## 11. Proposed cleanup sequence

1. Get user approval on the archive categories and timing.
2. Leave `data/`, `corpus/`, `inbox/`, `ingest/`, and validation/logging infrastructure untouched.
3. After the Thursday package is finalized, archive the Thursday-only support files and seed outputs.
4. After v10/web-search work stabilizes, archive v10 gold-set branch artifacts and older generated pilot outputs.
5. Move historical recon, comparator memos, session snapshots, and old report deliverables into `docs/archive/`.
6. Clean low-risk generated clutter last: `.DS_Store`, `__pycache__/`, empty scratch folders, and redundant legacy graphs.

## 12. Open questions for the user before actual cleanup

- Should `reports/6_25/` remain as a top-level deliverables folder, or should final report exports later move under `docs/archive/obsolete_reports_2026-06/`?
- Do you want to keep all versioned pilot outputs (`results_v2.csv` through `results_v8.csv`) side-by-side in `analysis/gabriel_pilot/`, or archive them once v9 remains the visible baseline?
- Should `docs/acquisition/` stay fully visible as research provenance, or should only the currently actionable queues stay in place?
- Do you want `docs/analysis/` to remain a working notebook-style directory, or do you want it tightened to only current active memos plus a nearby archive?
- Should `.DS_Store` and `__pycache__/` cleanup happen repo-wide in the eventual archive pass, or be left alone unless they become noisy in git status?
