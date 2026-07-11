# Final Report Export Audit — 2026-07-10

## Export commands used

```text
python -m py_compile scripts/export_final_report.py
python scripts/export_final_report.py check-tools
python scripts/export_final_report.py integrate --scaffold docs/analysis/report_scaffold_safety_non_safety_wage_mechanisms_2026-07-10.md --appendix docs/analysis/report_appendix_tables_2026-07-10.md --output docs/analysis/final_report_safety_non_safety_wage_mechanisms_2026-07-10.md
python scripts/export_final_report.py export --input docs/analysis/final_report_safety_non_safety_wage_mechanisms_2026-07-10.md --output-dir docs/final_reports
pdfinfo docs/final_reports/deeper_look_safety_non_safety_wage_mechanisms_2026-07-10.pdf
pdftoppm -png -r 120 docs/final_reports/deeper_look_safety_non_safety_wage_mechanisms_2026-07-10.pdf tmp/final_report_pdf_render_2026-07-10/page
```

## Inputs

- Main scaffold: `docs/analysis/report_scaffold_safety_non_safety_wage_mechanisms_2026-07-10.md`
- Appendix: `docs/analysis/report_appendix_tables_2026-07-10.md`
- Evidence layer: `docs/analysis/gabriel_codify_evidence_layer.csv`
- Viewer: `docs/analysis/gabriel_codify_excerpt_browser_latest.html`
- Report assets: `docs/analysis/report_assets/`

## Outputs

- Integrated Markdown: `docs/analysis/final_report_safety_non_safety_wage_mechanisms_2026-07-10.md` — 36,592 bytes.
- DOCX: `docs/final_reports/deeper_look_safety_non_safety_wage_mechanisms_2026-07-10.docx` — 797,087 bytes.
- PDF: `docs/final_reports/deeper_look_safety_non_safety_wage_mechanisms_2026-07-10.pdf` — 1,012,886 bytes.

## Export method

- DOCX generated locally with `python-docx`.
- PDF generated locally with ReportLab.
- `pandoc` and LibreOffice/`soffice` were not installed, so no pandoc export or DOCX-to-PDF conversion path was available.
- PDF visual QA used Poppler (`pdftoppm`) to render all pages to PNG.

## Figure and appendix checks

- Inline Markdown image references: 6.
- Missing inline image paths: 0.
- DOCX embedded media files: 6.
- PDF pages: 15, letter size.
- Appendix is included in the same integrated report and starts on a new page under `# Appendix`.
- Graph references resolved from `docs/analysis/` to `report_assets/`.
- Tables and figures were checked in the rendered PDF contact sheet and dense appendix pages; no obvious clipping, cut-off figures, or page-boundary overflow was observed.

## Limitations

- DOCX visual rendering to PNG could not be completed because LibreOffice/`soffice` is unavailable in this environment.
- The appendix tables are intentionally dense. They are readable in the rendered PDF but should still receive a human review pass for preferred font size and table comfort.
- The export script is a local Markdown-to-DOCX/PDF renderer for this report's Markdown subset, not a general-purpose Markdown publishing system.
- No GABRIEL/codify/model/API calls were made; this export uses only existing reviewed report inputs and report assets.

## Recommended human review checklist

- Title page/title block: confirm title, subtitle, label, and date.
- Executive summary: confirm framing stays "evidence patterns, not causal estimates."
- Graph readability: confirm all six inline figures are legible and not cut off.
- State sections: confirm Massachusetts, Texas, and Ohio caveats remain accurate.
- "What appears to drive the wage gap?" framing: confirm it does not overstate a single leading cause.
- Appendix start and formatting: confirm appendix begins on its own page and is part of the same report.
- Page numbering: confirm footer numbering appears throughout.
- PDF rendering: scan the final PDF directly, especially appendix tables and graph pages.
