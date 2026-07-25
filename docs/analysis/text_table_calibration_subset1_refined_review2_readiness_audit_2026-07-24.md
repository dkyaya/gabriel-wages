# Refined Calibration REVIEW2 Readiness Audit

## Decision

**Ready to run the bounded refined re-review.**

- calibration ID:
  `TEXT-TABLE-CALIBRATION-SUBSET1-150-2026-07-24`
- prior review:
  `TEXT-TABLE-CALIBRATION-SUBSET1-REVIEW1-2026-07-24`
- new review:
  `TEXT-TABLE-CALIBRATION-SUBSET1-REFINED-REVIEW2-2026-07-24`
- mode: `refined_visual_gate_v1`
- starting commit:
  `0e9430bc2d902764fec0fc98debf411123b7c4a0`

The tracked worktree was clean. The unrelated pre-existing untracked root
`package-lock.json` was reported and will remain untouched. All 14 requested
ancestor commits are in the local history. No remote was inspected.

## Locked input and prior-review provenance

The operative input is:

`docs/analysis/text_table_calibration/TEXT-TABLE-CALIBRATION-SUBSET1-150-2026-07-24/calibration_review_input.csv`

REVIEW1 remains immutable diagnostic provenance:

- reviewed CSV:
  `docs/analysis/text_table_calibration/TEXT-TABLE-CALIBRATION-SUBSET1-REVIEW1-2026-07-24/calibration_reviewed.csv`;
- summary:
  `docs/analysis/text_table_calibration/TEXT-TABLE-CALIBRATION-SUBSET1-REVIEW1-2026-07-24/calibration_review_summary.json`;
- rendered challenge:
  `docs/analysis/text_table_calibration/TEXT-TABLE-CALIBRATION-SUBSET1-REVIEW1-2026-07-24/calibration_visual_qa_spotcheck.md`.

The original packet has 150 rows and exactly 150 unique values for each of:

- `calibration_id`;
- `text_table_detection_id`;
- `pdf_readiness_id`;
- `source_review_id`.

All 150 rows have a nonblank local artifact path. All paths exist and their
byte sizes match the durable text/table-detection authority. All shared
identity, artifact-path, page-count, candidate-page, text-layer, signal, and
priority fields agree with that authority. Candidate wage-page hints are
nonblank for 132 rows and legitimately blank for 18 rows.

The production REVIEW2 directory and dry-run directory did not exist at the
readiness gate. The review helper therefore retains its fail-closed,
no-overwrite behavior.

## Immutable hashes

- original calibration input:
  `489e39cd99ba8812eb0b101b595825cdecd66da630c7a2eea7c612bdcc097535`;
- REVIEW1 reviewed CSV:
  `a50cd8a8c0b2b4d261db03c0b0cf183c060ce5e11b95bc89b77fcd965f0ff13c`;
- REVIEW1 summary:
  `48711714817c45246cefce8168a22c661d726e3cce8c24c97081abb04f236455`;
- durable text/table-detection ledger:
  `4992efe74c4d76d66e345ab9716b987df850b73b3db98af17a2573da98bced03`;
- durable PDF-readiness ledger:
  `dd120453068a668b5c818352402ca828073ac9639ee4d8d1ffc88f9488d4d953`;
- durable source-review ledger:
  `e29d580d42068615611b464e6da40654f336f273fa7c40a7b0717d4894148c9f`;
- `data/contracts.csv`:
  `ed26cff96061e45ff668a02231547a6c9c11ec4b138772bfb3d5de34a229e1e8`;
- `data/city_coverage.csv`:
  `4fdf135ff3741893f5a4c45edc52a70159adc87598b777dfc4373dd8481249e3`;
- sorted corpus filename inventory:
  `32e084f0bbbbf118681e25e607c1dbf1c6c78e8c7d9221416f4ead4b2d080322`.

## Parser and renderer

- local parser: `pypdf 6.13.2`;
- renderer: `/opt/homebrew/bin/pdftoppm`;
- metadata checker: `/opt/homebrew/bin/pdfinfo`.

Rendering is available, so the required visual gate will not be silently
downgraded to text-only review.

## Review method plan

The production command will:

1. verify each selected artifact against the durable hash and byte size;
2. inspect no more than six direct candidate/context/neighbor pages;
3. follow no more than four bounded contents/index/appendix navigation pages;
4. render no more than three pages per document at 96 DPI;
5. discard every temporary render immediately after the document;
6. save controlled labels, counters, page numbers, and notes capped at 300
   characters, but no page text, complete table, or wage value;
7. identify the method as assisted refined local adjudication, not human
   manual review.

After REVIEW2, an independent rendered-page challenge will sample at least
15 rows across original likely/possible/unlikely signals and p1/p2/p3
priorities. That challenge will inspect temporary page renders independently
from the stored REVIEW2 labels and document agreement or disagreement.

## Boundaries

- only the 150 locked local artifacts are eligible for opening;
- no URL, network, API, model, hosted search, source review, verification, or
  scout operation;
- no download or redownload;
- no OCR;
- no full text, full table, wage-table extraction, or final wage value;
- no ingestion or `gabriel.codify`;
- no routing, metadata-triage, source-review, PDF-readiness, durable
  text/table-detection, original input, or REVIEW1 mutation;
- no wage-gap calculation, causal claim, regression, remote inspection, or
  push.
