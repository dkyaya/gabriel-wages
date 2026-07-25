# Text/Table Detection Pilot 1 Readiness Audit

Date: 2026-07-24

Pilot: `TEXT-TABLE-DETECTION-PILOT1-150-2026-07-24`

## Result

**PASS.** The durable PDF-readiness layer is complete, the requested
parse-text candidate universe is intact, and the repository is ready to
prepare a locked 150-PDF local text/table-detection pilot.

Work began at local commit
`11e689a6d7b21c0dd60d8af8c349c571d6000322`. The tracked worktree was
clean. The unrelated untracked root `package-lock.json` existed before this
task and remains outside scope. Local ancestry includes `11e689a`,
`b45876e`, `74a843a`, `985d581`, `46923a2`, `12b3f10`, `ed042c1`,
`79df80c`, and `e028432`.

No pilot input or temporary output directory existed before this task.

## Files used

The operative durable technical-readiness authority is:

`docs/analysis/pdf_readiness_ledgers/pdf_readiness_ledger_cumulative.csv`

Its pre-task SHA-256 is:

`dd120453068a668b5c818352402ca828073ac9639ee4d8d1ffc88f9488d4d953`

Supporting authorities used for identity and metadata checks are:

- `docs/analysis/source_review_ledgers/source_review_ledger_cumulative.csv`;
- `docs/analysis/source_review_ledgers/source_review_summary_cumulative.json`;
- `docs/analysis/content_triage_ledgers/content_triage_metadata_ledger_cumulative.csv`;
- `docs/analysis/pdf_readiness_ledgers/pdf_readiness_summary_cumulative.json`;
- `docs/analysis/pdf_readiness_ledgers/pdf_readiness_ledger_latest.csv`; and
- `docs/analysis/pdf_readiness_ledgers/pdf_readiness_summary_latest.json`.

The project instructions and current operating interpretation were read from
`AGENTS.md`, `PROGRESS.md`, and
`docs/analysis/chatgpt_handoff_latest.md`. The full-retained readiness
readiness audit, merge result, dashboard refresh, next-phase plan, and
validation record were also used.

## Durable readiness universe

- durable PDF-readiness rows: 2,124;
- unique PDF-readiness IDs: 2,124;
- `parse_text_layer_later`: 1,828;
- `ocr_later`: 296;
- eligible text-layer `present`: 1,608;
- eligible text-layer `partial`: 220;
- eligible p1 / p2: 1,501 / 327;
- eligible police / fire / non-safety: 782 / 439 / 607;
- eligible source-review Pilot 1 / Batch 2 / Batch 3:
  127 / 404 / 1,297;
- eligible states plus DC represented: 51;
- pages represented by parse-text candidates: 94,200; and
- retained artifact paths, hashes, and positive byte sizes recorded:
  1,828 / 1,828 / 1,828.

Filesystem metadata checks found all 1,828 parse-text artifact paths present
and all 1,828 local byte sizes equal to the durable record. These readiness
checks did not open or parse a PDF. The live-local pilot will reverify each
locked artifact SHA-256 before parsing.

The durable readiness ledger has no wage-extraction columns. Its cumulative
summary records zero OCR runs, zero wage-table/value extraction, zero
full-text artifacts, and zero ingestion/codification actions.

## Why this pilot is the next gate

The project has established local artifact integrity, page counts, and
sampled text-layer presence for every retained PDF. It has not established
whether bounded text-layer processing can conservatively identify likely
table pages or contract-period hints without producing final wage
observations.

A 150-PDF pilot should therefore precede:

1. a full pass over all 1,828 parse-text candidates;
2. any OCR decision for the 296 deferred PDFs;
3. final wage-value extraction;
4. ingestion or codification; and
5. any descriptive or causal wage analysis.

The pilot may record page numbers, signal counts, confidence categories, and
at most 300 characters of redacted contract-period hints per document. It
must not retain page text or extract final wage values.

## Authorization boundary

This task is authorized to:

- select 150 rows from the durable `parse_text_layer_later` universe;
- open only those locked local retained artifacts after dry-run gates pass;
- verify their recorded hashes and sizes;
- scan at most 10 deterministic pages per PDF;
- inspect at most 1,500 extracted characters per scanned page in memory;
- retain only bounded signals, page hints, and a maximum 300-character
  redacted contract-period hint per document; and
- collect and audit lane-local pilot outputs.

It is not authorized to:

- open a URL or make a network/API/model call;
- download or redownload a document;
- run OCR;
- save full page or document text;
- extract final wage values;
- ingest or codify evidence;
- mutate scout, routing, metadata-triage, source-review, or PDF-readiness
  ledgers;
- create a durable text/table-detection merged ledger;
- calculate a wage gap, make an empirical or causal claim, or run a
  regression; or
- inspect remotes or push.
