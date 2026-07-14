# Report Production Plan — Deeper Look Into Safety & Non-safety Wage Mechanisms

**Type:** planning document. Describes the recommended sequence for turning the current markdown draft into a formatted artifact, once the PI has reviewed it. No PDF, DOCX, PPTX, or other final-formatted artifact has been created in this run.

## Recommended next run after user review

The next run should not begin formatting until the PI has responded to the open items in `report_review_checklist_safety_non_safety_wage_mechanisms_2026-07-06.md`, particularly Section 1 (claims needing PI review) and Section 6 (suggested questions). Once that review is back, the recommended sequence is:

1. Apply any content edits the PI requested directly to `report_draft_safety_non_safety_wage_mechanisms_2026-07-06.md` (or a new dated copy, per the project's living-vs-dated-file convention — this is a dated report draft, so edits should update this same file rather than forking a new one, consistent with how other dated memos in this project have been revised in place within the same date).
2. Resolve the formatting decisions listed in the review checklist's Section 3 (paragraph counts, section numbering, table placement) before any layout work begins, since these affect the document's structure, not just its appearance.
3. Only then proceed to a dedicated formatting run.

## Whether to create DOCX first, PDF second

Recommend **DOCX first, PDF second**. A DOCX draft is easier for a PI to comment on directly (tracked changes, inline comments) than a PDF, and this report is explicitly described as still reviewable, not final. Once the PI's DOCX-stage edits are incorporated, a PDF can be generated from the same source as a stable, distributable version. Do not generate a PDF as the first or only artifact, since it would discourage the kind of direct-edit review this report still needs.

## How to apply the style guide

The style guide specified for this report is:
- Primary font: Georgia (body and headings).
- Body text: 11pt, black, standard paragraph spacing, not overly dense.
- Headings: Georgia, bold, leaning charcoal (not pure black), with a clear H1/H2/H3 hierarchy matching this draft's current section levels (H1 for the title, H2 for the eight main sections, H3 for group-by-group and mechanism-by-mechanism sub-entries).
- Accent color: deep Harvard crimson, used sparingly — recommended uses are the title-block divider rule, section-heading underline rules, callout-box borders (e.g., around the Main Takeaways list or a "what this report does not claim" box if the PI adds one), and small labels (such as the group-status tags already used in the Group-by-Group section).
- Page setup: letter size, margins 0.75-0.9 inches.
- Footer: page number only.
- Header: short report label ("Safety & Non-safety Wage Mechanisms"), not the full title, to keep the header compact.

When formatting begins, apply the accent color conservatively — the style guide specifies "sparingly," and this report's content (working evidence map, not a polished publication) benefits from a plain, legible presentation more than heavy design treatment. Avoid using crimson for body text or for emphasis within paragraphs; reserve it for structural elements (rules, borders, labels) as specified.

## Which tables should be main text vs. appendix

Based on the current draft and the review checklist's Section 4:

**Main text:**
- Evidence Map (Section 3) — the report's primary reference table, must stay in the main flow.
- Massachusetts institutional comparison content (currently prose in Section 6; could be tabularized during formatting if the PI prefers a table over prose for this content).
- Source-needs must-have and useful tables (Section 7).

**Appendix (already drafted as appendix material):**
- Full group-retention/status table (Appendix A) — a fuller version of the Evidence Map's status column.
- Mechanism disposition summary (Appendix B).
- Source-needs summary note, pointing to the full CSV rather than reproducing it (Appendix C).
- Hypothesis disposition summary, currently prose-only (Appendix D) — consider a condensed table (by recommendation category) if the PI wants more structure during the formatting pass.

**Should move to appendix if not already there:**
- The optional/deferred source-needs table (currently in main-text Section 7) — recommend moving to the appendix during formatting to shorten the main-text Source Needs section, per the review checklist's Section 4.

## Likely filename conventions

Following this project's existing dated-file convention:
- Draft markdown (already created): `report_draft_safety_non_safety_wage_mechanisms_2026-07-06.md`
- DOCX output (recommended first formatted artifact, future run): `report_safety_non_safety_wage_mechanisms_2026-07-06_v1.docx`
- PDF output (recommended second formatted artifact, future run): `report_safety_non_safety_wage_mechanisms_2026-07-06_v1.pdf`
- If a revised version follows PI review, increment the version suffix (`_v2`) rather than changing the date, unless the revision is substantial enough to warrant treating it as effectively a new report (in which case a new date would be appropriate, consistent with how other dated memos in this project are versioned).
- Formatted artifacts should be stored outside `docs/analysis/` in a location the PI specifies (e.g., a `reports/` or `deliverables/` directory), since `docs/analysis/` is this project's working-memo directory, not its finished-output directory. This decision should be confirmed with the PI before the first formatting run, since no such directory currently exists in this repository.

## How to preserve citations/auditability

The draft deliberately names underlying analysis files (e.g., `all_groups_source_needs_2026-07-06.csv`, `hypothesis_disposition_audit_2026-07-06.csv`) at the points where a reader might want to trace a claim back to its full evidentiary record, rather than embedding long quotations or exhaustive citation lists in the report body itself. When formatting:
- Preserve these file-name references as footnotes or endnotes in the formatted version, rather than removing them for a cleaner read — they are the report's auditability mechanism.
- Do not convert file-name references into a formal citation/bibliography format unless the PI specifically requests it; a footnote pointing to a named working file is sufficient for this project's internal-memo context.
- If the PI wants a shorter main-text read, move file-name references to endnotes rather than deleting them.

## What not to do until source acquisition is approved

- Do not add any new corpus row, ingest any new document, or reference a source that has not already been reviewed in a prior session's memo.
- Do not build or reference an OEWS/BLS descriptive wage panel in any version of this report.
- Do not upgrade any claim currently marked "must-have," "useful," or "deferred" source need to a stronger evidentiary status without the underlying source-acquisition work actually having occurred and been documented in a new session memo.
- Do not recommend or reference a public-records request in any version of this report.
- Do not restart GABRIEL attribute design work as part of this report's production; the report's own Section 7 explicitly sequences that after source targets are stable, consistent with every prior project memo's recommendation.
