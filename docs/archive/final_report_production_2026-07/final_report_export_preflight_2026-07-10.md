# Final Report Export Preflight — 2026-07-10

## Repository state

- Working directory confirmed: `/Users/joachimjohnson/Documents/RA_2026/Pol_Fire/gabriel-wages`.
- Starting git status: clean except untracked `.claude/` and `tmp/`.
- Latest starting commit: `d56ae31 Polish mechanism evidence report scaffold`.
- `data/contracts.csv` and `data/city_coverage.csv`: no diff at preflight (`git diff -- data/contracts.csv data/city_coverage.csv` empty).
- `corpus/` and `docs/schema.md`: not edited in this export run.

## Input report files found

- `docs/analysis/report_scaffold_safety_non_safety_wage_mechanisms_2026-07-10.md`
- `docs/analysis/report_appendix_tables_2026-07-10.md`
- `docs/analysis/report_graph_audit_2026-07-10.md`
- `docs/analysis/report_evidence_layer_audit_2026-07-10.md`
- `docs/analysis/report_scaffold_preflight_2026-07-10.md`
- `docs/analysis/report_polish_preflight_2026-07-10.md`
- `docs/analysis/gabriel_codify_evidence_layer.csv`
- `docs/analysis/gabriel_codify_excerpt_browser_latest.html`
- `docs/analysis/gabriel_codify_viewer_usage_2026-07-09.md`
- `docs/analysis/gabriel_codify_viewer_build_audit_2026-07-09.md`
- `docs/analysis/wage_mechanism_evidence_checklist.md`
- `docs/analysis/report_review_checklist_safety_non_safety_wage_mechanisms_2026-07-06.md`
- `docs/analysis/all_groups_source_needs_2026-07-06.csv`

## Report assets found

- Directory present: `docs/analysis/report_assets/`
- Total files: 20
- PNG figures: 7
- SVG figures: 7
- CSV support tables: 6
- Inline figures expected in final report Markdown: 6 PNG references.

## Expected final outputs

- `docs/analysis/final_report_safety_non_safety_wage_mechanisms_2026-07-10.md`
- `docs/final_reports/deeper_look_safety_non_safety_wage_mechanisms_2026-07-10.docx`
- `docs/final_reports/deeper_look_safety_non_safety_wage_mechanisms_2026-07-10.pdf`
- `docs/analysis/final_report_export_audit_2026-07-10.md`
- Optional reproducibility helper: `scripts/export_final_report.py`

## Export constraints

- No GABRIEL/codify run.
- No Harvard Proxy, model, API, or network calls.
- No new source collection, no FOIA/PRR, and no licensed-source scraping.
- No edits to `data/contracts.csv`, `data/city_coverage.csv`, `corpus/`, or `docs/schema.md`.
- Final artifact must be one integrated report with the appendix at the end, not separate main-report and appendix artifacts.
- Preserve the report's evidence-pattern framing; do not strengthen the claims into causal proof.

## Local toolchain

- `pandoc`: not available.
- LibreOffice/`soffice`: not available.
- `python-docx`: available.
- ReportLab: available.
- Poppler tools (`pdfinfo`, `pdftoppm`): available for PDF inspection/render QA.
