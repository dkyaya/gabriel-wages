# Full Retained PDF-Readiness Remainder Readiness Audit

Date: 2026-07-24

Round: `PDF-READINESS-REMAINDER-ALL-RETAINED-2026-07-24`

## Result

**PASS.** The completed 150-row PDF-readiness pilot is intact, the durable
source-review layer contains 2,124 retained local PDFs, and exactly 1,974
retained PDFs remain outside Pilot 1. The project is ready to plan and run a
local-only readiness pass over that complete remainder.

Work began at local commit
`74a843a825c5ef8b2a3b5b272ffbfc56a10d444a`. The tracked worktree was
clean. The unrelated untracked root `package-lock.json` existed before this
task and remains outside scope. Local ancestry includes `74a843a`,
`985d581`, `46923a2`, `12b3f10`, `ed042c1`, `79df80c`, and `e028432`.

## Durable source-review input

The canonical source-review input is:

`docs/analysis/source_review_ledgers/source_review_ledger_cumulative.csv`

- pre-task SHA-256:
  `e29d580d42068615611b464e6da40654f336f273fa7c40a7b0717d4894148c9f`;
- cumulative source-review rows: 2,150;
- unique source-review IDs: 2,150;
- unique candidate-queue IDs: 2,150;
- retained PDF artifact rows: 2,124;
- retained PDF bytes: 4,500,367,582;
- timeout rows without retained PDFs: 21;
- forbidden rows without retained PDFs: 5; and
- repaired-client connection errors: 0.

Every one of the 2,124 eligible retained rows has a nonblank lane-local
artifact path, SHA-256, positive byte size, observed `application/pdf`
content type, and `reviewed_metadata_and_artifact_saved` source-review
status.

## Preserved Pilot 1 readiness outputs

The three completed local ledgers at:

`tmp/pdf_readiness_pilots/PDF-READINESS-PILOT1-150-2026-07-24/`

contain:

- rows: 150;
- unique PDF-readiness IDs: 150;
- unique source-review IDs: 150;
- unique candidate-queue IDs: 150;
- terminal `readiness_checked` rows: 150;
- rows with page counts: 150;
- text-layer present / partial / absent: 107 / 19 / 24;
- parser errors: 0;
- hash failures: 0;
- missing artifacts: 0;
- URLs opened: 0;
- downloads or redownloads: 0;
- OCR runs: 0;
- full extracted-text artifacts: 0; and
- durable PDF-readiness merges: 0.

Pilot 1 remains preserved and will not be rerun or merged alone in this
task.

## Exact remainder

Subtracting Pilot 1 source-review identities from the 2,124 retained-PDF
universe yields:

- already readiness-checked: 150;
- retained PDFs remaining: 1,974;
- remainder recorded artifact bytes: 4,165,691,340; and
- Pilot 1 plus remainder: 2,124 / 2,124 retained PDFs.

There is zero source-review-identity overlap between Pilot 1 and the
remainder.

### Source-review round distribution

- `SOURCE-REVIEW-PILOT1-150-2026-07-24`: 118
- `SOURCE-REVIEW-BATCH2-500-2026-07-24`: 463
- `SOURCE-REVIEW-BATCH3-3X500-2026-07-24`: 1,393

### Metadata priority

- p1: 1,661
- p2: 313

### Unit type

- police: 862
- fire: 461
- non-safety: 651

### Candidate source type

- CBA: 1,928
- wage schedule or compensation plan: 35
- memorandum or settlement: 6
- ordinance or policy: 5

### Preliminary officialness signal

- official municipal: 737
- official state repository: 513
- official union: 35
- uncertain: 633
- unknown: 56

The remainder spans 39 states or state-equivalent jurisdictions. Ohio is the
largest group at 534, followed by California at 256 and Illinois at 196.
These are inherited source-review metadata distributions, not substantive
source-quality findings.

## Why the complete local pass comes before merge or extraction

Pilot 1 was deliberately diversity-weighted. It demonstrated that the
bounded parser can safely verify hashes, count pages, and identify sampled
text layers, but its raw rates are not population estimates. Running the
same local-only checks on every remaining retained PDF establishes exact
technical-readiness coverage before a single cumulative durable merge.

This order:

1. prevents a 150-row partial durable layer from being mistaken for full
   retained-PDF coverage;
2. produces a complete parser-error, page-count, and text-layer inventory;
3. identifies the exact no-text subset before any separately authorized OCR
   strategy;
4. avoids more bulk downloading while 4.50 GB of retained artifacts remain
   technically unclassified; and
5. keeps later wage-table work behind both technical and substantive content
   gates.

Text-layer presence does not prove that a PDF is the intended agreement,
matches the employer or bargaining unit, contains a wage table, or supports
an analysis-ready wage observation.

## Authorized boundary

This task may open only the 1,974 locked, already-retained local PDFs after
planning and dry-run gates pass. It may verify hashes, sizes, and signatures,
count pages, and inspect at most three bounded pages per PDF for text-layer
presence.

It will not open a URL, make a network/API/model call, redownload a document,
run live source review, run OCR, save extracted text, extract wage tables or
values, ingest, codify, update scout accounting, mutate routing, triage, or
source-review ledgers, write to `corpus/`, calculate wage gaps, make causal
claims, or run regressions. It will stop before any durable PDF-readiness
merge.
