# Full Retained PDF-Readiness Serial Merge Readiness Audit

Date: 2026-07-24

Merge ID: `PDF-READINESS-FULL-RETAINED-MERGE-2026-07-24`

## Result

**PASS.** The two approved local-readiness rounds are complete, disjoint,
structurally merge-eligible, and exactly equal to the retained-PDF subset of
the cumulative durable source-review ledger. The project is ready for one
serial offline cumulative PDF-readiness merge.

Work began at local commit
`b45876e2cd2541ce3a51b9d2ce397d7a715908a6`. The tracked worktree was
clean. The unrelated untracked root `package-lock.json` existed before this
task and remains outside scope. Local ancestry includes `b45876e`,
`74a843a`, `985d581`, `46923a2`, `12b3f10`, `ed042c1`, `79df80c`, and
`e028432`.

No durable `docs/analysis/pdf_readiness_ledgers/` directory existed before
the merge. The merge will create or update only the durable
PDF-readiness-ledger and status/documentation layers.

## Approved rounds and fresh audits

### `PDF-READINESS-PILOT1-150-2026-07-24`

- planned / ledger / terminal rows: 150 / 150 / 150;
- lane classifications: three `completed_merge_eligible`;
- readiness status: 150 `readiness_checked`;
- text layer present / partial / absent: 107 / 19 / 24;
- technical parseability high / medium / low: 107 / 19 / 24;
- next action parse-text-layer / OCR-later: 126 / 24;
- page counts: 150;
- duplicate readiness/source-review/candidate identities: 0 / 0 / 0;
- missing/hash/parser failures: 0 / 0 / 0; and
- recommendation: `merge_all_pdf_readiness_lanes`.

Fresh audit:

`tmp/pdf_readiness_pilots/PDF-READINESS-PILOT1-150-2026-07-24/cumulative_merge_readiness_audit_2026-07-24/pdf_readiness_lane_audit_summary.json`

### `PDF-READINESS-REMAINDER-ALL-RETAINED-2026-07-24`

- planned / ledger / terminal rows: 1,974 / 1,974 / 1,974;
- lane classifications: four `completed_merge_eligible`;
- readiness status: 1,974 `readiness_checked`;
- text layer present / partial / absent: 1,501 / 201 / 272;
- technical parseability high / medium / low: 1,501 / 201 / 272;
- next action parse-text-layer / OCR-later: 1,702 / 272;
- page counts: 1,974;
- duplicate readiness/source-review/candidate identities: 0 / 0 / 0;
- missing/hash/parser failures: 0 / 0 / 0; and
- recommendation: `merge_all_pdf_readiness_lanes`.

Fresh audit:

`tmp/pdf_readiness_pilots/PDF-READINESS-REMAINDER-ALL-RETAINED-2026-07-24/cumulative_merge_readiness_audit_2026-07-24/pdf_readiness_lane_audit_summary.json`

## Combined identity and authority checks

The cumulative source-review authority is:

`docs/analysis/source_review_ledgers/source_review_ledger_cumulative.csv`

Its pre-task SHA-256 is:

`e29d580d42068615611b464e6da40654f336f273fa7c40a7b0717d4894148c9f`

The authority contains 2,150 total rows and 2,124 retained-PDF rows, defined
as `reviewed_metadata_and_artifact_saved`, observed `application/pdf`,
nonblank artifact path and hash, and positive byte size.

Fresh offline CSV-only checks found:

- Pilot 1 readiness rows: 150;
- remainder readiness rows: 1,974;
- combined readiness rows: 2,124;
- unique PDF-readiness IDs: 2,124;
- unique source-review IDs: 2,124;
- unique candidate-queue IDs: 2,124;
- cross-round source-review duplicates: 0;
- cross-round candidate-queue duplicates: 0;
- exact retained source-review-ID set equality: yes;
- exact retained candidate-queue-ID set equality: yes; and
- inherited identity, artifact path, SHA-256, byte size, content type,
  source-review round, state, municipality, government, unit type, priority,
  source type, preliminary officialness/relevance/document type, and
  extraction-readiness equality: 2,124 / 2,124.

The merge gate read CSV and JSON metadata only. It did not open retained PDF
artifacts.

## Combined technical-readiness result

- readiness status: 2,124 `readiness_checked`;
- text layer present / partial / absent: 1,608 / 220 / 296;
- technical parseability high / medium / low: 1,608 / 220 / 296;
- `parse_text_layer_later`: 1,828;
- `ocr_later`: 296;
- page counts: 2,124;
- page minimum / median / mean / p90 / maximum:
  1 / 44 / 50.860640 / 84 / 463;
- total pages represented: 108,028; and
- page-count bins 1-10 / 11-25 / 26-50 / 51-100 / over 100:
  86 / 215 / 990 / 701 / 132.

These are technical parser-readiness results only. Text-layer presence does
not establish source relevance, agreement identity, employer or unit match,
wage-table presence, wage values, ingestion readiness, codified evidence,
or an analysis-ready observation.

## Safety and mutation gate

Both fresh audits report:

- URLs opened: 0;
- network calls: 0;
- downloads/redownloads: 0 / 0;
- OCR runs: 0;
- full extracted-text artifacts: 0;
- wage tables/values extracted: 0 / 0;
- ingestion/codify actions: 0 / 0; and
- prior durable PDF-readiness merges: 0.

Pre-task hashes were recorded for contracts, city coverage, candidate queue,
scout accounting, durable routing, durable metadata triage, cumulative
source review, its cumulative summary, and the complete `corpus/` tree.
They will be required to remain unchanged.

## Merge recommendation

**Proceed with exactly one serial offline merge of both approved rounds.**
The merge must fail closed on any duplicate, nonterminal row, audit failure,
retained-PDF authority mismatch, inherited-field mismatch, pre-existing
durable target, or unsafe counter. It may create only the cumulative/latest
PDF-readiness ledger, summary, merge audit, dashboard status, and operating
documentation.

It must not open a URL or retained PDF, download a document, parse a PDF,
run OCR, save text, extract wages, ingest, codify, mutate scout/routing/
triage/source-review layers, calculate a wage gap, make an empirical or
causal claim, or run a regression.
