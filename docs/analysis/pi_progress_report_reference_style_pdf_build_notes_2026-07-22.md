# PI progress report reference-style PDF build notes — 2026-07-22

## Source and reference

- Content source: `docs/analysis/pi_progress_report_source_discovery_2026-07-22.md`
- User-specified visual reference: `/mnt/data/deeper_look_safety_non_safety_wage_mechanisms_2026-07-10 (1).pdf`
- Reference actually inspected: `docs/final_reports/deeper_look_safety_non_safety_wage_mechanisms_2026-07-10.pdf`
- Reference SHA-256: `a2203617d7b58cfbd01477b0f1ce43cf9d50a0aa0626540a144fb83be85e880d`

The `/mnt/data/` attachment path was not mounted in this workspace. The repository contains the canonical July 10 report with the same title and date; it was used as the transparent fallback style reference. Its 15 pages were rendered and visually inspected before the new builder was restyled.

## Build method

`scripts/build_pi_progress_pdf.py` is a local-only ReportLab generator. It parses the current Markdown headings, paragraphs, ordered and unordered lists, code/path lines, and simple tables. It accepts:

- `--input`
- `--output`
- `--title`
- `--subtitle`
- `--report-date`
- `--report-type`

The generator embeds locally available Georgia fonts and applies the older report’s visual logic:

- sparse, centered title page;
- charcoal Georgia title and serif body;
- crimson report label and major headings;
- repeated concise interior header;
- thin gray header rule;
- footer with short title at left and `Page N` at right;
- gray, thin-grid tables with restrained header fill;
- generous letter-size margins and academic spacing; and
- a prominent crimson-bordered source-discovery caveat.

Metadata timestamps are fixed where feasible so identical source, options, fonts, and ReportLab versions produce stable output.

## Outputs

- Analysis copy: `docs/analysis/pi_progress_report_source_discovery_2026-07-22.pdf`
- Dashboard-public copy: `docs/dashboard/reports/pi_progress_report_source_discovery_2026-07-22.pdf`
- Page count: 6
- Page size: US letter, 612 × 792 points
- Final file size: 67,815 bytes
- SHA-256, both copies: `4d39ec04f1594f32a08e6093d8812ea799ee3e4a88b133e0dbb4a3230b70df23`

The dashboard copy is byte-for-byte identical to the analysis copy.

## Visual validation

All six final pages were rendered at 150 DPI under `tmp/pdfs/pi_progress_report_final_2026-07-22/` and reviewed for:

- page-level clipping or overflow;
- raw Markdown artifacts;
- heading hierarchy and crimson consistency;
- table width and line wrapping;
- bullet and numbered-list alignment;
- repeated header/footer placement;
- page-number continuity;
- caveat visibility; and
- sufficient bottom clearance.

No overwide tables, broken headings, clipped text, footer collisions, or raw Markdown markers were observed. The final source was also updated so its dashboard description reflects the new eleven-file project hub and report-library index rather than the superseded ten-file MVP.

## Comparison with the prior `c3bdbc7` PDF

The prior PDF was 130,281 bytes with SHA-256 `83f02375beda3f486c45ac1fd5fe1de7ae9641ecbb4fda81626749e8e2848054`. It used an evergreen, card-oriented, contemporary cover and metric-band treatment. The rebuilt report is intentionally lighter and more academic:

- substantially more title-page whitespace;
- Georgia throughout the narrative;
- crimson rather than evergreen report hierarchy;
- simpler thin-grid tables;
- no cover metric cards;
- restrained repeated header/footer; and
- typography and pacing aligned with the July 10 project report.

The smaller file size reflects simpler visual construction, not omitted report content.

## Content limitation

The report remains a source-discovery progress report. It describes candidate rows as unverified source leads, distinguishes scouting from verification and ingestion, and does not make wage-gap estimates, bargaining-mechanism findings, or causal claims.
