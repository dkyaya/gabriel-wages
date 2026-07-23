# Gabriel Wages report style guide

Date: 2026-07-22

Status: reusable internal report standard

## Purpose

This guide defines the default PI-facing Gabriel Wages report style. It is based on the project's July 10, 2026 academic report family and should be used for progress reports, evidence memoranda, technical appendices, and future checkpoint reports unless a deliverable has a separate approved template.

## Title block

Use a restrained centered title page:

1. Report title in bold Georgia, 24–27 points, charcoal.
2. Descriptive subtitle in Georgia, 12–14 points, muted gray.
3. Report type or project label in bold Georgia, 9.5–11 points, Harvard crimson.
4. Report date in Georgia, 9.5–11 points, muted gray.
5. Generous white space; no decorative hero image or metric-card grid by default.

Recommended project label:

`Gabriel Wages`

Recommended report type examples:

- `PI Progress Report`
- `Source Verification Memorandum`
- `Research Operations Appendix`
- `Evidence Review`

## Running header and footer

- Interior-page header: concise report title at left, report type at right.
- Header font: Georgia, approximately 8 points, muted gray.
- Place a thin light-gray rule beneath the header.
- Footer left: short report title.
- Footer right: `Page N`.
- Cover page may omit the header but should retain the short footer and page number.
- Do not place research claims, metrics, or source-stage status in running matter.

## Page and spacing

- Page size: US Letter.
- Margins: 0.75–0.9 inches; default 0.82 inches.
- Body leading: approximately 1.2–1.3 times font size.
- Use deliberate page breaks for major recommendation sections and appendices.
- Avoid isolated headings and split figure/caption pairs.

## Section hierarchy

- H1/report title: bold Georgia, charcoal.
- H2/major section: bold Georgia, 14–17 points, Harvard crimson.
- H3/subsection: bold Georgia, 11–13 points, charcoal.
- H4/technical label: bold Georgia or a clean sans serif, 9–11 points, charcoal.
- Use spacing and typography for structure. Avoid enclosing every section in a card or colored box.

## Color palette

| Use | Color |
|---|---|
| Major headings / structural accent | Harvard crimson `#A51C30` |
| Title / secondary headings | Charcoal `#333333` |
| Body | Black `#111111` |
| Running matter / captions | Muted gray `#666666` |
| Table header fill | Light gray `#F2F2F2` |
| Table rules | Light gray `#C8C8C8` |
| Optional figure continuity | Restrained blue/teal only where analytically useful |

Crimson should remain structural. Do not use it for body-copy emphasis or data claims.

## Typography

- Primary serif: Georgia.
- Fallback serif: Times New Roman or Times.
- Optional interface/label sans serif: Arial or Helvetica, used sparingly.
- Body: 10–11 points.
- Captions and running matter: 8–9 points.
- Literal repository paths may use a compact monospace face if needed for auditability.

## Tables

- Use light-gray header fill, bold serif header text, thin light-gray rules, and white body rows.
- Repeat header rows across pages.
- Align numeric columns consistently, usually right.
- Keep tables within the text measure; reduce type only for genuinely wide tables.
- Use a short source or interpretation note beneath a table when the numbers could be misread.
- Candidate counts must be labeled as unverified where relevant.

## Figures and captions

- Center figures within the text measure.
- Keep figures and captions together.
- Caption immediately below the figure in smaller muted-gray Georgia.
- Use a concise descriptive caption followed by an optional source line.
- Avoid decorative charts. Every figure should answer a specific research or operations question.
- Operational charts must not imply source verification or substantive wage findings.

## Appendices

- Begin the appendix on a new page.
- Use crimson appendix headings and charcoal subsection headings.
- Preserve identifiers, file paths, schema definitions, and source-stage terminology needed for auditability.
- Use compact tables, repeated headers, and restrained explanatory prose.

## Required source-discovery caveat

Every source-discovery report must display this text prominently on the cover or first substantive page:

> This report summarizes source-discovery progress. Candidate rows are unverified source leads and should not be interpreted as wage-gap estimates, verified contracts, or causal evidence.

Scouting tiers must be described as research-operational prioritization, not evidence quality or findings.

## File naming

- Markdown source: `descriptive_report_name_YYYY-MM-DD.md`
- Archival PDF: `descriptive_report_name_YYYY-MM-DD.pdf`
- Dashboard copy: `docs/dashboard/reports/descriptive_report_name_YYYY-MM-DD.pdf`
- Build notes: `descriptive_report_name_pdf_build_notes_YYYY-MM-DD.md`
- Dated reports are revised in place within the same task/date unless the research checkpoint changes materially.
- Report-library metadata uses a stable lowercase ID, for example `pi-source-discovery-2026-07-22`.

## Generation and QA

- Prefer a deterministic local builder.
- Do not require web fonts or network assets.
- Compile the builder, generate the archival PDF, and copy the exact bytes to the dashboard path.
- Render every final page to PNG and inspect for clipping, overlap, broken glyphs, table spill, poor page breaks, and raw Markdown.
- Verify page count, size, hash, metadata, text-stage caveats, and the absence of JavaScript or encryption.
