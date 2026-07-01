# GABRIEL Web-Search Repo Declutter Plan

**Date:** 2026-07-01  
**Status:** planning only; do not delete or move files yet

## Objective

Declutter the current Thursday-report materials after the report is finalized, while keeping active report-facing files visible and preserving fallback scaffold artifacts for later technical use.

## Recommended timing

- Do not archive anything before the Thursday report package is finalized.
- After final PDF/report signoff, create:

`docs/archive/gabriel_websearch_scaffold_2026-07-01/`

- Keep active report-facing files in `docs/analysis/`.

## 1. Keep active

- `docs/analysis/gabriel_websearch_thursday_report_draft_2026-07-01.md`
- `docs/analysis/gabriel_websearch_thursday_report_pdf_ready_2026-07-01.md`
- `docs/analysis/gabriel_websearch_thursday_presentation_outline_2026-07-01.md`
- `docs/analysis/gabriel_tutorial_web_mode_note_2026-07-01.md`
- `docs/analysis/chatgpt_handoff_latest.md`
- `PROGRESS.md`

Reason: these are the live report-facing and session-tracking materials under the corrected framing.

## 2. Archive after PDF/report is finalized

- `docs/analysis/gabriel_websearch_live_smoke_test_status_2026-07-01.md`
- `docs/analysis/gabriel_websearch_report_assets_2026-07-01/`
- `docs/analysis/gabriel_websearch_mass_city_pilot_summary_2026-06-30.md`

Reason: useful record of how the seed/demo package evolved, but no longer central once the corrected report package is final.

## 3. Keep as code scaffold/fallback

- `analysis/gabriel_pilot/gabriel_websearch_custom_fn.py`
- `analysis/gabriel_pilot/run_gabriel_websearch_seed_demo.py`
- `docs/analysis/gabriel_websearch_custom_function_design_2026-06-30.md`
- `docs/acquisition/gabriel_websearch_city_prompt_template_2026-06-30.md`

Reason: these remain useful if built-in GABRIEL web mode is not structured enough or if project-specific schema enforcement is still needed.

## 4. Superseded by built-in web-mode framing

- any language in existing memos that presents `get_all_responses_fn` as the default live path;
- any language that says a toolkit creator must provide the basic web-search backend before the project can test GABRIEL web mode at all;
- any slide/report framing that treats the custom callback as the main story rather than the fallback story.

Concrete files to watch:

- `docs/analysis/gabriel_websearch_custom_function_design_2026-06-30.md`
- `docs/analysis/gabriel_websearch_live_smoke_test_status_2026-07-01.md`
- `docs/analysis/gabriel_websearch_mass_city_pilot_summary_2026-06-30.md`

Reason: these files are not useless, but parts of their framing are now secondary to the tutorial-based built-in web-mode interpretation.

## 5. Generated outputs safe to regenerate

- `analysis/gabriel_pilot/results_gabriel_websearch_seed_demo_2026-06-30.csv`
- `analysis/gabriel_pilot/results_gabriel_websearch_seed_demo_sources_2026-06-30.csv`
- `analysis/gabriel_pilot/results_gabriel_websearch_seed_demo_extractions_2026-06-30.csv`
- old source/extraction seed CSV derivatives created only for demo/report packaging

Reason: these are generated outputs or derivative demo artifacts that can be recreated from the scaffold and seed inputs.

## Archive recommendation

After the Thursday report is finalized:

1. Create `docs/archive/gabriel_websearch_scaffold_2026-07-01/`.
2. Move superseded process memos and finalized support artifacts there, but keep active report-facing files in `docs/analysis/`.
3. Leave the fallback code scaffold in place under `analysis/gabriel_pilot/`.
4. Do not archive or move anything that is still being actively cited by the current report package.
