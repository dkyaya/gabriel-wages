# Report reference style audit

Date: 2026-07-22

## Reference inspected

The user supplied the formatting reference as:

`/mnt/data/deeper_look_safety_non_safety_wage_mechanisms_2026-07-10 (1).pdf`

That Linux attachment path was not mounted in this macOS workspace. The repository contains the canonical artifact from the same dated report milestone:

`docs/final_reports/deeper_look_safety_non_safety_wage_mechanisms_2026-07-10.pdf`

This 15-page, letter-size ReportLab PDF was used as the visual and structural reference. Its SHA-256 is:

`a2203617d7b58cfbd01477b0f1ce43cf9d50a0aa0626540a144fb83be85e880d`

The canonical report builder, `scripts/export_final_report.py`, and the archived production plan were also inspected to distinguish intentional house style from incidental page content. No substantive content from the reference report is used in the source-discovery report.

## Formatting ideology

### Title page

- Very restrained, centered title block with generous white space.
- Large bold Georgia title in charcoal, usually wrapping to two lines.
- Smaller centered Georgia subtitle in muted gray.
- A short report label in Harvard crimson.
- A centered date beneath the label.
- No dashboard-style metric cards, decorative illustration, or full-bleed color.
- The short report title and page number remain in the footer, even on the cover.

### Header and footer

- The footer is quiet and functional: short report label at left and `Page N` at right.
- Small Georgia text and muted gray keep the running matter subordinate to the report.
- The archived production plan specifies a compact short-title header. The rebuilt source-discovery report therefore uses a small repeated header on interior pages, a thin gray rule, the concise report title at left, and report type at right.

### Section hierarchy

- Major sections use bold Georgia in dark Harvard crimson.
- Subsections use bold Georgia in charcoal.
- Body text remains black and is never colored for emphasis.
- Section spacing, rather than boxes or cards, establishes hierarchy.
- Appendices retain the same hierarchy and use lettered or descriptive subsection headings where appropriate.

### Typography

- Georgia is the dominant font for title, headings, body, tables, captions, headers, and footers.
- Body copy is approximately 10–11 points with compact but readable leading.
- The overall feel is an academic internal report rather than a product brochure.
- Monospace appears only when a literal repository path must remain auditable.

### Figures and captions

- Figures are centered within the text measure.
- Captions are centered immediately below the figure in smaller muted-gray Georgia.
- The reference uses restrained blue for analytical figures, but the report layout itself does not introduce decorative figure color.
- Figures are kept with captions when possible, with enough space before the next section heading.

### Tables

- Tables use thin light-gray grid lines.
- Header rows use a light-gray fill and bold Georgia text.
- Body cells remain white; heavy banding and colored table headers are avoided.
- Wide tables use smaller type and repeated header rows but remain inside the page margins.
- Tables are placed near the related narrative and centered within the available text width.

### Margins and spacing

- US Letter page size.
- Approximately 0.8-inch margins.
- Generous cover whitespace and restrained section spacing.
- Interior pages are relatively dense but maintain readable paragraph leading and separation.
- Page breaks are used intentionally for major recommendation and appendix transitions.

### Appendix style

- The appendix begins on a new page.
- Major appendix headings remain crimson; subsection headings are charcoal.
- Tables are compact, repeat their header rows, and preserve source-path auditability.
- Appendix prose follows the same serif body treatment as the main report.

## Difference from the c3bdbc7 PI PDF

The `c3bdbc7` PDF used a modern dashboard-derived presentation:

- left-aligned oversized cover title;
- evergreen/teal palette;
- a four-card metric band;
- Arial labels and table text;
- tinted alternating rows and dark colored table headers;
- a product-report footer with a long status sentence.

That version was polished and readable, but visually distinct from the older report family. The reference format is quieter, more academic, more serif-led, and less card-heavy.

## Style elements applied to the rebuilt PI report

- centered Georgia title page modeled on the July 10 report;
- Georgia body and headings;
- charcoal title and body, Harvard crimson major sections;
- small repeated interior header and thin gray rule;
- short-title/page-number footer;
- light-gray academic tables with thin rules;
- dedicated recommendation and appendix pages;
- a restrained crimson-bordered caveat on the cover;
- deterministic ReportLab metadata and page-safe table widths;
- no old report claims, figures, or mechanism content.

The caveat remains prominent:

> This report summarizes source-discovery progress. Candidate rows are unverified source leads and should not be interpreted as wage-gap estimates, verified contracts, or causal evidence.
