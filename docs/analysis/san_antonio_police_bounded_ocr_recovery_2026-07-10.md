# San Antonio Police — Bounded OCR/Text Recovery — 2026-07-10

## Target

`tx_san_antonio_police_2022` — `corpus/tx_san_antonio/tx_san_antonio_sapoa_police_cba_2022_2026.pdf`

## Known issue at session start

218-page image scan (Xerox WorkCentre 7855, 270° page rotation), no extractable text layer. `pdftotext -layout` on the original PDF yields 218 characters total across the whole document (essentially 1 stray character per page) — confirmed again at the start of this session. `data/contracts.csv`'s `text_quality` was `partial`; the row's `total_comp_note` explicitly flagged the union identity and cycle dates as taken from the source portal's filename/path, not the document body, and no OCR had been attempted in either the original expansion run or the interrupted-run recovery.

## Method

Bounded, single-pass OCR of this one document only — no other corpus file was touched:

1. `pdftoppm -r 150 -png` rendered all 218 pages to PNG at 150 DPI. **74 seconds.** `pdftoppm` correctly read the PDF's embedded `/Rotate 270` metadata — no manual rotation correction was needed; page 1 rendered right-side-up.
2. `tesseract --psm 6` OCR'd all 218 rendered pages. **~2.5 minutes.**
3. Combined into a single cache file with `--- OCR page N ---` boundary markers (same convention as the prior Wayland OCR recovery), stored under `tmp/san_antonio_ocr/full_cache.txt` (not committed — working scratch only).

**Total runtime: ~4 minutes**, well within a bounded single pass. A full-document pass was chosen over pre-targeted pages because (a) page 1's own OCR output was immediately clean and correctly oriented, giving high confidence the rest of the document would OCR comparably well, and (b) with no text layer at all, there was no way to locate a table of contents' page numbers without OCR'ing at least a reconnaissance batch first — at this document's demonstrated per-page OCR speed (~0.7s/page), a full pass cost barely more than a targeted one and avoided the risk of missing a relevant article by guessing page ranges wrong.

## Output / cache paths

- Full raw OCR cache (218 pages, 483,412 characters, not committed): `tmp/san_antonio_ocr/full_cache.txt`
- Curated, marker-sliced excerpt cache (committed, 10,720 characters, 9 sections): `docs/analysis/san_antonio_police_bounded_ocr_extract_2026-07-10.txt`

The curated cache was built by exact `.index()`-based marker-slicing directly from the full raw cache (same method as the prior Wayland OCR recovery, chosen specifically to eliminate hand-transcription risk) — every section is a byte-verifiable contiguous substring of the raw OCR output, confirmed programmatically before this document was written (whitespace-normalized substring check, 9/9 sections pass). Original PDF was never modified, read-only throughout.

## Recovered text quality

Substantially better than expected. Average ~2,217 characters/page (218 pages), comparable density to this project's other clean-scanned CBAs. Spot-checked across the whole document:

- **Article structure fully legible**: Duration (Art. 1), Definitions (Art. 2), Association Rights/Recognition (Art. 3), No Strike Clause (Art. 6), Management Rights (Art. 7), Grievance Procedure (Art. 15), Wages (Art. 16), Impasse Procedure, Civilianization (Art. 39), and a full table of contents.
- **Minor character-level OCR artifacts present** (e.g., "Section 1, |" for "Section 1.", "Cc." for "C.", occasional stray characters) — these do not obscure meaning anywhere spot-checked, but are frequent enough that this is not `clean`-grade extraction.
- **No fabrication risk**: every excerpt used downstream (curated cache, mechanism excerpts, codify windows) is a marker-sliced, programmatically-verified substring of the raw OCR text — never hand-retyped or paraphrased.

## Whether the source became usable for codify

**Yes — clearly usable.** Recovered text includes genuine, on-topic language for at least 6 of this run's target mechanism families: recognition (Art. 3 §1), no-strike (Art. 6), management rights (Art. 7 §1 A–D), grievance/contract-interpretation arbitration (Art. 15 §§1, 4), classification/wage-grade structure (Art. 16 §1, Step A–F schedule), and — notably — a genuine **peer/comparator wage-comparability clause**: Attachment 3 (City Ordinance 51838), the factfinding-panel guidelines incorporated by reference into the Impasse Procedure article, explicitly directs factfinders to compare San Antonio police/fire wages against "other public and private employees in the local labor market area" and "comparable cities in the State of Texas." This is a substantively important find — before this OCR pass, this project had no confirmed comparator-wage language for San Antonio at all.

## A genuine document-text correction this OCR pass supports

Article 1 (Duration) and the title page together confirm this agreement's actual cycle: the title page reads "May 12, 2022 Through September 30, 2026," and Article 1 independently confirms the end date ("shall remain in effect until the 30th day of September, 2026"). The existing `contracts.csv` row's `cycle_start=2022-10-01` was an assumption ("Cycle start month/day (Oct 1) assumed from Texas Chapter 174 agreements' typical fiscal-year alignment; not confirmed from document text"), not a document-derived fact. Per this project's verbatim-capture discipline, this session corrects `cycle_start` to `2022-05-12` (document-confirmed) — `cycle_end` (`2026-09-30`) was already correct and needed no change. See the `data/contracts.csv` diff for this row's updated `total_comp_note`.

## text_quality: partial → ocr_messy (justified update)

Updating `tx_san_antonio_police_2022`'s `text_quality` from `partial` to `ocr_messy` (both are valid controlled values per `docs/schema.md`). Justification: `partial` no longer accurately describes this row — the document is not partially extracted, it is now *fully* OCR'd with recovered, legible, article-structured text across all 218 pages. `ocr_messy` (not `clean`) is the accurate label given the consistent minor character-level artifacts documented above (stray punctuation, occasional misrecognized characters) that a native-text extraction would not have. This mirrors the same `text_quality` value already used for `oh_cleveland_fire_2025` and other genuinely-OCR'd-but-imperfect rows in this project's corpus.

`python scripts/validate.py` re-run after the update — see the checks section of the audit doc for this run.

## Limitations

- OCR was not proofread word-for-word across all 218 pages — only the ~10 sections pulled into the curated cache were spot-checked in full. Other articles not reviewed this session (e.g., the detailed disciplinary-actions article, full wage-step Attachment 2 tables) may contain OCR errors not caught here.
- The curated cache and this session's codify window (Task E) draw only from the 9 sections excerpted above — a future session revisiting this document could locate additional mechanism evidence (e.g., overtime/callback detail, health-benefits language, training/certification pay) not pulled into this pass's bounded excerpt set.
- No OCR confidence scores were captured (`tesseract --psm 6` default output only); no second OCR engine or settings sweep was attempted, consistent with keeping this a single bounded pass.
