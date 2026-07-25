# PDF-Readiness Pilot 1 (150) Readiness Audit

Date: 2026-07-24

## Result

**PASS.** The durable source-review artifact layer is ready for a bounded,
local-only 150-PDF page-count and text-layer readiness pilot.

Work began at local commit
`985d5813f89c377eb49f9ad76fe9072a7d8c78f9`. The tracked worktree was
clean. The unrelated untracked root `package-lock.json` existed before work
and remains outside this task. Local ancestry includes `985d581`,
`46923a2`, `12b3f10`, `ed042c1`, `79df80c`, and `e028432`.

## Durable input

The canonical input is:

`docs/analysis/source_review_ledgers/source_review_ledger_cumulative.csv`

Its pre-task SHA-256 is:

`e29d580d42068615611b464e6da40654f336f273fa7c40a7b0717d4894148c9f`

The corresponding cumulative summary is:

`docs/analysis/source_review_ledgers/source_review_summary_cumulative.json`

Its pre-task SHA-256 is:

`21e36de3552e3db09fa2090ed46509d702b3d69237d31f5c49082fb1ad9b475a`

The durable layer contains:

- cumulative source-review rows: 2,150;
- unique source-review IDs: 2,150;
- unique candidate-queue IDs: 2,150;
- retained PDF artifact rows: 2,124;
- timeout/forbidden rows without retained PDFs: 21 / 5;
- retained PDF bytes: 4,500,367,582;
- cumulative total artifact bytes including metadata: 4,502,698,363;
- maximum retained PDF: 10,470,269 bytes; and
- repaired-client connection errors: 0.

## Independent artifact gate

Before planning, all 2,124 retained content paths were independently checked.
Every path:

- exists as a regular file;
- resolves beneath its lane-local
  `tmp/source_review_pilots/.../candidate_artifacts/` directory;
- begins with a PDF signature;
- matches the durable ledger's recorded byte size; and
- matches the durable ledger's recorded SHA-256.

Failures were zero. The pilot planner will select only rows with saved local
PDF artifacts and nonblank hashes. The local runner will re-verify each of
the 150 selected hashes and sizes before parsing.

## Current technical-readiness gap

All 2,150 durable rows currently record:

- `pdf_page_count = unknown`; and
- `text_layer_status = unknown`.

No retained PDF has been parsed or OCRed by the source-review layer. The
project therefore knows that 2,124 PDF artifacts are locally available and
hash-intact, but does not yet know their page counts, whether sampled pages
contain extractable text, or the bounded local parser failure rate.

`pypdf 6.13.2` is installed in the project virtual environment. Poppler and
`pdfplumber 0.11.10` are also locally available, but the pilot uses `pypdf`
as the single bounded parser to keep results comparable. At most three pages
and 500 characters per sampled page will contribute to technical counts.
No extracted text will be saved.

## Why readiness precedes more downloading or extraction

The durable artifact layer already occupies approximately 4.50 GB, while
726 additional p2 rows pass the default download-planning gates. More
downloading would increase storage and audit burden without answering whether
the existing local PDFs have text layers or are parser-hostile.

Page count and sampled text-layer status are therefore the immediate
technical bottleneck. They can inform whether the next step should be a
larger local readiness pass, remaining p2 access, a separately authorized
OCR strategy, or a later content- and identity-gated extraction pilot.
Text-layer presence alone does not establish document relevance, wage-table
presence, wage values, or analysis readiness.

## Authorized boundary

This pilot may:

- read the durable source-review ledger;
- open only 150 locked, already-retained local PDF artifacts;
- verify hashes, sizes, and PDF signatures;
- compute page count;
- inspect up to three pages per PDF for text-layer presence; and
- write lane-local CSV/JSON/timing and audit metadata.

It will not open a URL, make a network/API/model call, redownload a document,
run live source review, run OCR, save extracted text, extract wage tables or
values, ingest, codify, update scout accounting, mutate routing/triage/source-
review ledgers, write to `corpus/`, calculate wage gaps, make empirical or
causal claims, or run regressions. It will stop before any durable PDF-
readiness merge.
