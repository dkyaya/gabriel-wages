# Wayland Bounded OCR/Text Recovery — 2026-07-10

## Target file

`corpus/ma_wayland/ma_wayland_afscme_1_2_2020_2023.pdf` (`ma_wayland_other_2021` in `data/contracts.csv`) — the AFSCME Local 690 Wayland-1/Wayland-2 agreement, the only Massachusetts corpus source with dispatch and Community Health Nurse content (per `pre_report_must_have_evidence_review_2026-07-06.csv`). Prior sessions' `pdftotext` extraction (both plain and `-layout`) returned ~0 usable characters — the PDF is a pure image scan (Xerox AltaLink C8045 scanner output, 48 pages, 792×612pt letter size, page rotation 270°, no embedded text layer at all).

## Method used

1. `pdftoppm -r 150 -png` rendered all 48 pages to PNG images at 150 DPI (Poppler correctly applied the PDF's own rotation metadata — no manual rotation needed). Runtime: ~16 seconds.
2. `tesseract <page>.png <page> --psm 6` (page-segmentation mode 6, "uniform block of text") OCR'd all 48 page images. Runtime: ~35 seconds for all 48 pages.
3. Total bounded pass: **~51 seconds, all 48 pages, one pass, no re-runs.** This is a genuinely bounded operation, not an open-ended OCR project — page targeting *before* OCR was not feasible (no prior page-content knowledge existed to target), so a single full-document pass at a modest DPI was the pragmatic bounded approach, consistent with this task's instructions.
4. Grepped the 48 resulting `.txt` files for `dispatch|nurse|JCC|Communications Center|Health Nurse|Community Safety` and separately for wage-grade markers (`G-3|G-4|G-7|G-15|pay grade|wage schedule`) to identify which of the 48 pages actually contain the target content, rather than reviewing all 48 by hand.
5. Read the identified pages directly (not just grep snippets) to confirm genuine, coherent, usable text.

## Pages attempted / pages found useful

All 48 pages were OCR'd (page targeting wasn't feasible before the pass), but only a subset turned out to contain the dispatch/nurse content of interest:

| page | content |
|---|---|
| 1 | Title page (agreement dates, union locals) |
| 4 | **Article 2 — Recognition clause**, explicitly naming Community Health Nurses (since 2005) and "all regular full-time dispatch personnel" (Joint Communications Center) as bargaining-unit members |
| 5 | Article 3 — Definitions, including a lateral-dispatcher probationary-period carve-out |
| 7 | Article 5/6 — union dues/agency-fee deduction, union business leave |
| 24–25 | Article 26/27 — education incentive explicitly covering Community Health Nurses; holiday pay rules specific to dispatchers (double-time-and-a-half for holiday work) and Community Health Nurses (10-holiday schedule tied to the school year) |
| 37 | Article 38 — CPR training stipend explicitly carved out for dispatchers ("Joint Communication Dispatcher") |
| 39–40 | **Appendix A — full wage schedule tables** (FY2022 and FY2023), with grade-to-title mapping explicitly listing `G-3 JCC Dispatcher`, `G-4 JCC Dispatcher Coordinator`, `G-7A Public Health Nurse`, `G-15 Community Health Nurse`, and their dollar-figure step tables |

A small consolidated cache of these 9 pages' raw OCR text (21,433 characters) was saved to `docs/analysis/wayland_other_bounded_ocr_extract_2026-07-10.txt` for traceability — the original PDF was never modified, and no corpus file was touched.

## Result quality

**Substantially better than expected.** Even a single-pass, modest-DPI (150) OCR run produced clean, coherent, directly usable text — full dollar-figure wage tables, article/section numbering intact, and multiple genuinely dispatcher-specific and nurse-specific mechanism clauses (recognition, holiday pay, training stipends, education incentive). This matches and exceeds the specific pay-grade figures a prior session's "bounded OCR pass" reportedly recovered by hand (G-3/G-4 dispatcher grades, G-7A/G-15 nurse grades) — this session's pass independently reproduces those same figures from the same document, confirming the recovery is accurate, not a one-off fluke.

## Did the row become usable for codify?

**Yes.** `ma_wayland_other_2021` is now included in this session's Seekonk/Wayland codify sample (see `gabriel_codify_seekonk_wayland_sample_selection_2026-07-10.md`), with its evidence window built from this OCR-recovered text — the only source of dispatch/nurse_health mechanism evidence anywhere in this project's Massachusetts corpus.

## Limitations

- OCR at 150 DPI is not perfect: minor character-level errors are visible in the wage tables (e.g. a stray `[` before some grade rows, occasional garbled characters like `16-8` where `G-8` was likely intended, a misplaced `(` from a facing-page bleed-through). These are typical scanned-OCR artifacts, not fabrications — the underlying numbers and grade/title labels are legible and internally consistent (e.g. the FY2022 and FY2023 tables show a plausible ~2.5% year-over-year step increase across all grades).
- This was a single OCR pass with no manual correction or a second higher-DPI re-pass on the specific wage-table pages, which could further reduce these minor artifacts if ever needed for a wage-figure-precision use case (not needed for this session's mechanism-attribute codify use case, which only needs the surrounding clause text to be legible).
- `data/contracts.csv`'s `text_quality` field for `ma_wayland_other_2021` remains `ocr_messy` (unchanged — this run did not edit `data/contracts.csv`), which is still an accurate characterization of the *stored* corpus file's own extractability; this session's OCR recovery is a session-scoped cache artifact, not a correction to that field.
- The other 39 OCR'd pages (not listed in the table above) were reviewed only via grep, not read in full — they are presumed to contain other, non-dispatch/nurse bargaining-unit content (DPW, clerical) already covered by this project's other Wayland/Seekonk rows, and were not needed for this session's scope.
