# PI progress report PDF build notes — 2026-07-22

## Status

PASS. A polished six-page, letter-size PDF was generated from the full PI report and copied to the dashboard report path. Both output files are non-empty and byte-identical.

## Method

The repository already contained a ReportLab-based report exporter, so the new focused builder follows the same local-only family of tooling while implementing the source-discovery report's specific layout:

- builder: `scripts/build_pi_progress_pdf.py`;
- PDF engine: ReportLab 5.0.0;
- rendering/inspection: Poppler `pdfinfo` and `pdftoppm`;
- structural/text check: `pypdf`;
- source: `docs/analysis/pi_progress_report_source_discovery_2026-07-22.md`.

The script accepts an explicit `--input` Markdown path and `--output` PDF path. It parses headings, paragraphs, ordered/unordered lists, inline emphasis/code, and simple Markdown tables without network access. Deterministic ReportLab canvas metadata makes identical source/style builds byte-reproducible.

## Outputs

- archival report: `docs/analysis/pi_progress_report_source_discovery_2026-07-22.pdf`;
- dashboard report: `docs/dashboard/reports/pi_progress_report_source_discovery_2026-07-22.pdf`.

Final SHA-256 for both files:

`83f02375beda3f486c45ac1fd5fe1de7ae9641ecbb4fda81626749e8e2848054`

Final size for each file: 130,281 bytes.

## Styling

- Georgia headings/body and Arial labels/tables from the local macOS font set, with built-in serif/sans fallbacks;
- 0.72-inch side margins and page-safe header/footer bands;
- explicit cover title block, ISO report date, four-metric checkpoint band, and prominent source-stage caveat;
- evergreen/teal research-report palette with restrained alternating table rows;
- repeating table headers, custom width allocation for the eight-column wave table, and small but readable table type;
- page headers on interior pages and page numbers on every page;
- a dedicated recommended-next-phase page and separate appendix page;
- ASCII hyphen normalization for consistent cross-platform rendering.

## Visual and structural QA

The first visual render exposed a ReportLab 5 numbered-marker incompatibility and an awkward split in the recommendation section. The builder was corrected, both PDFs were regenerated, and all six final pages were rendered again at 150 DPI.

Final visual inspection confirmed:

- no clipped or overlapping text;
- no overwide or spilled tables;
- no raw Markdown tokens;
- correct bullet and numbered-list markers;
- readable paths and appendix cells;
- clean section transitions, headers, footers, and page numbering;
- prominent unverified-source caveat on the cover;
- no broken internal links or interactive PDF dependency.

`pdfinfo` reports six letter-size pages, no encryption, no JavaScript, and deterministic metadata. Text extraction confirmed the title, section content, stage definitions, source caveats, and absence of Markdown heading/emphasis markers.

## Limitations and boundary

The PDF is a styled representation of the committed Markdown source, not a separate research product. It does not add or verify evidence. Long repository paths are presented as readable reference text rather than clickable internal links. Candidate rows remain unverified source leads; the report contains no verified wage-gap finding or causal claim.

No live/API/model/hosted-search call, URL opening or verification, source ingestion, GABRIEL codification, candidate promotion, or scout accounting change occurred during the PDF build.
