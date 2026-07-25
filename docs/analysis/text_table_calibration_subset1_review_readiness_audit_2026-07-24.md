# Text/Table Calibration Subset 1 Review Readiness Audit

## Decision

**Ready for a bounded Codex-assisted local adjudication review.**

The locked input is:

`docs/analysis/text_table_calibration/TEXT-TABLE-CALIBRATION-SUBSET1-150-2026-07-24/calibration_review_input.csv`

Its SHA-256 is:

`489e39cd99ba8812eb0b101b595825cdecd66da630c7a2eea7c612bdcc097535`

This input will remain immutable. All review results will be written under:

`docs/analysis/text_table_calibration/TEXT-TABLE-CALIBRATION-SUBSET1-REVIEW1-2026-07-24/`

## Repository gate

- starting commit:
  `610f5e8e9c12f4330de9a2edec2438fa0c778b51`
- requested ancestry: passed
- tracked worktree: clean
- unrelated pre-existing untracked file: root `package-lock.json`
- remotes inspected or modified: no

## Packet and identity checks

- input rows: 150
- unique row-level calibration IDs: 150
- unique text/table-detection IDs: 150
- unique PDF-readiness IDs: 150
- unique source-review IDs: 150
- all manual statuses initialized `not_reviewed`: yes
- all other controlled manual labels initialized `unknown`: yes
- nonblank local artifact paths: 150 / 150
- artifact paths resolving to local files: 150 / 150
- rows with one or more candidate wage-page hints: 132
- candidate wage-page hints: 562
- no-hint boundary rows: 18

All 150 detection identities exist in the 1,828-row durable
text/table-detection ledger, and all 150 inherited artifact paths match that
authority. The runner will obtain the locked content hash, byte size, page
count, and text-layer status from the durable row before opening any PDF.

## Review method

The review method is `codex_assisted_local_adjudication`, not human manual
review. For each locked row, a deterministic local helper will:

1. verify that the local artifact exists and matches the durable SHA-256 and
   byte size;
2. open only that retained PDF;
3. inspect the 1-indexed candidate wage pages, at most one adjacent page, and
   first-page context only while staying within five pages per document;
4. keep page text in memory only and classify structural signals;
5. save controlled labels and short structural notes, not full text, tables,
   or wage values.

This method can estimate consistency and bounded usefulness, but it is not a
substitute for a human page-by-page validation. Ambiguous, missing, mismatched,
or parser-hostile rows will be marked `needs_second_review`.

## Boundaries

- only the 150 listed retained artifacts are eligible to open;
- no URL or network/API/model access;
- no download or redownload;
- no OCR;
- no complete page/document text or table retention;
- no final wage-value extraction or analysis-ready observation;
- no ingestion or `gabriel.codify`;
- no routing, metadata-triage, source-review, PDF-readiness, or durable
  text/table-detection ledger mutation;
- original `calibration_review_input.csv` preserved byte-for-byte;
- `data/contracts.csv`, `data/city_coverage.csv`, and `corpus/` unchanged.

The next gate is a successful dry run that opens zero PDFs and produces a
complete 150-row planned review output.
