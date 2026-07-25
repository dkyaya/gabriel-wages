# Full Text/Table Detection Run Readiness Audit

Date: 2026-07-25

Run: `TEXT-TABLE-DETECTION-FULL-PARSE-TEXT-2026-07-24`

## Result

**PASS.** The durable PDF-readiness authority contains 1,828 unique,
terminal `parse_text_layer_later` rows with `present` or `partial` text
layers. Every eligible row has a recorded retained local PDF path, content
hash, positive byte size, and positive page count. All 1,828 paths exist and
their local byte sizes match the durable records.

Work began at local commit
`4a9c2c78e3812c6ac02cd78a574a228399e55a3e`. The tracked worktree was
clean. The unrelated untracked root `package-lock.json` existed before this
task and remains outside scope.

Local ancestry includes `4a9c2c7`, `11e689a`, `b45876e`, `74a843a`,
`985d581`, `46923a2`, `12b3f10`, `ed042c1`, `79df80c`, and `e028432`.
Neither the full-run plan/output directories nor a durable
text/table-detection ledger existed before this task.

## Files used

The operative technical-readiness authority is:

`docs/analysis/pdf_readiness_ledgers/pdf_readiness_ledger_cumulative.csv`

Its pre-task SHA-256 is:

`dd120453068a668b5c818352402ca828073ac9639ee4d8d1ffc88f9488d4d953`

Supporting identity and metadata authorities are:

- `docs/analysis/source_review_ledgers/source_review_ledger_cumulative.csv`;
- `docs/analysis/source_review_ledgers/source_review_summary_cumulative.json`;
- `docs/analysis/content_triage_ledgers/content_triage_metadata_ledger_cumulative.csv`;
- `docs/analysis/pdf_readiness_ledgers/pdf_readiness_summary_cumulative.json`;
- `docs/analysis/pdf_readiness_ledgers/pdf_readiness_ledger_latest.csv`; and
- `docs/analysis/pdf_readiness_ledgers/pdf_readiness_summary_latest.json`.

The project instructions and current interpretation were read from
`AGENTS.md`, `PROGRESS.md`, and
`docs/analysis/chatgpt_handoff_latest.md`. The Pilot 1 readiness, schema,
input, result, no-merge, dashboard, validation, and future full-run records
were read in full. Pilot 1’s three local lane ledgers and its local lane
audit were also checked.

## Pilot 1 gate

Pilot 1 remains preserved and unmerged:

- selected and terminal rows: 150 / 150;
- unique text/table-detection IDs: 150;
- unique PDF-readiness IDs: 150;
- detection status: 150 `detection_checked`;
- lane classifications: three `completed_merge_eligible`;
- candidate wage-page hints: 599;
- maximum bounded contract-period hint: 300 characters;
- URLs/network calls: 0 / 0;
- downloads/redownloads: 0 / 0;
- OCR runs: 0;
- full-text artifacts: 0;
- final wage values extracted: 0;
- ingestion/codification actions: 0 / 0; and
- durable text/table-detection merges: 0.

The successful pilot froze `pypdf 6.13.2`, the
`bounded_keyword_numeric_structure_v1` heuristic, a ten-page maximum,
1,500 inspected characters per page, and a 300-character redacted
contract-period hint cap.

## Full parse-text universe

- durable PDF-readiness rows: 2,124;
- eligible `parse_text_layer_later` rows: 1,828;
- excluded `ocr_later` rows: 296;
- text-layer `present`: 1,608;
- text-layer `partial`: 220;
- unique PDF-readiness/source-review/candidate identities:
  1,828 / 1,828 / 1,828;
- retained paths present: 1,828 / 1,828;
- recorded sizes matching local files: 1,828 / 1,828;
- represented PDF bytes: 3,646,511,196; and
- represented pages: 94,200.

### Source-review round

- Pilot 1: 127
- Batch 2: 404
- Batch 3: 1,297

### Metadata priority

- p1: 1,501
- p2: 327

### Unit type

- police: 782
- fire: 439
- non-safety: 607

### Preliminary officialness

- official municipal: 648
- official state repository: 525
- official union: 42
- uncertain: 546
- unknown: 67

These inherited officialness values remain preliminary source-review
metadata signals.

### Candidate source type

- CBA: 1,719
- wage schedule or compensation plan: 58
- memorandum or settlement: 20
- ordinance or policy: 19
- arbitration award: 10
- factfinding: 2

### Page-count bin

- 1–10 pages: 76
- 11–25: 174
- 26–50: 846
- 51–100: 617
- over 100: 115

All 50 states plus DC are represented. The largest eligible concentrations
are Ohio 528, California 238, Illinois 131, Florida 102, Washington 95, and
Michigan 94; the remaining 38.8% span the other 45 state/DC groups.

## Why the full run is justified

Pilot 1 demonstrated that the frozen bounded detector produces terminal
local results without retaining full text or final wage values. Rerunning
all 1,828 eligible identities—including all 150 pilot identities—under one
new full-run namespace will provide a uniform round suitable for a later
exact-identity durable merge.

The full run does not validate heuristic precision. Pilot 1 classified
149/150 rows as likely or possible wage-table candidates, so the full
results must remain recall-oriented page hints until a stratified manual
calibration estimates false-positive and false-negative rates.

Visual PDF rendering is not part of this task: it is a bounded structural
text-layer pass, not a layout review or PDF deliverable. The local parser
will inspect only the locked pages in memory after every dry-run gate passes.

## Authorization boundary

This task may:

- lock all 1,828 durable parse-text candidates into four balanced lanes;
- rerun the 150 Pilot 1 identities under the full-run namespace;
- verify each locked artifact hash and size locally;
- scan at most ten deterministic pages and 1,500 characters per page;
- retain signal categories, one-based page hints, counts, and at most 300
  redacted contract-period characters per document; and
- collect and audit lane-local outputs.

It may not:

- open a URL or make a network/API/model call;
- download or redownload a document;
- run OCR;
- save complete page or document text;
- reconstruct a table or extract final wage values;
- ingest or codify evidence;
- mutate scout, routing, content-triage, source-review, or PDF-readiness
  ledgers;
- create or update a durable text/table-detection ledger;
- calculate wage gaps, make empirical or causal claims, or run regressions;
  or
- inspect remotes or push.
