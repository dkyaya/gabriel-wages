# Independent adjudication PREP1 readiness audit

Date: 2026-07-25
Adjudication prep ID:
`TEXT-TABLE-INDEPENDENT-ADJUDICATION-PREP1-2026-07-24`

## Result

**PASS — preparation may proceed, but extraction remains prohibited.**

The latest local commit before work was
`c3580a41bbd750f2f721e0b2f9c52c8ac725c56f`. The tracked worktree was clean.
The unrelated untracked root `package-lock.json` existed before work and is
being left untouched.

Local ancestry checks passed for all requested commits:

- `c3580a4`, `0e9430b`, `7438f1a`, `610f5e8`, `32ae355`;
- `827917b`, `11e689a`, `b45876e`, `74a843a`, `985d581`;
- `46923a2`, `12b3f10`, `ed042c1`, `79df80c`, and `e028432`.

No remote was inspected or configured to perform these local ancestry checks.

## REVIEW2 gate status

The refined REVIEW2 outputs exist and report:

- extraction decision: `continue_schema_refinement`;
- reviewed rows: 150;
- strict likely-signal visual confirmation: 61/80 = 76.25%, below the
  required 80%;
- candidate-bearing wrong-page rate: 42/132 = 31.82%, above the permitted
  15%;
- independent rendered-page material agreement: 10/18 = 55.56%, below the
  required 80%;
- 500-document extraction authorized: no;
- smaller extraction pilot authorized: no.

The assisted labels therefore cannot authorize extraction. Wage prose,
budget/benefit/non-wage tables, incorrect candidate pages, bounded navigation
failures, and compact compensation sheets remain unresolved systematic error
families. Codex-assisted REVIEW2 is also not independent ground truth.

## Packet scope

Preparation is limited to the same 150 calibration identities and retained
local PDF artifacts. The deliverable is a blinded human-review CSV, bounded
page lists, instructions, a case index, render manifest, optional page-level
render aids, and future adjudication/analysis instructions. The packet will
not contain REVIEW1/REVIEW2 labels, extraction-gate labels, detector signal
labels, prior recommended actions, full text, complete tables, or structured
wage values.

Local PDF access is permitted only for pages selected from these 150 artifacts
and only to make bounded review aids. The configured limits are a ±1 candidate
window, four navigation pages, and at most six rendered pages per case.

## Immutable inputs

The original calibration input, every REVIEW1 output, and every REVIEW2 output
are read-only inputs. Baseline hashes include:

| Input | SHA-256 |
|---|---|
| Original calibration input | `489e39cd99ba8812eb0b101b595825cdecd66da630c7a2eea7c612bdcc097535` |
| REVIEW2 reviewed CSV | `e8b31e1771ec8b0c5497561aa0a22993598c0a9a2ff2bf25c7e4a3c8eefa3e8a` |
| REVIEW2 summary JSON | `02f751e78f2ef412444912bb6eda7087907b32da618cb9a9f69082d06366037a` |
| REVIEW2 decision JSON | `662b465f441df4359e3261b40c821e453dd672b5243e24c76634c5ec87b44b3c` |
| REVIEW1 directory file-hash inventory | `722d5b01c7a9aba3e653852aef5de60fa566e6168247b010e3bdde716a39b7b8` |

The protected data and durable ledgers are also read-only. Their starting
hashes match the prior validated REVIEW2 baselines.

## Explicit boundary

- no URLs or remote pages;
- no network, API, hosted-search, or model calls;
- no downloads or redownloads;
- no OCR;
- no wage extraction, including no 500-document or smaller pilot;
- no ingestion or `gabriel.codify`;
- no durable routing, metadata-triage, source-review, PDF-readiness, or
  text/table-detection ledger mutation;
- no final wage observations, wage gaps, causal claims, or regressions;
- no git remote inspection, fetch, pull, push, or remote mutation.

## Exact files used

The canonical paths supplied in the task all existed and were used:

- `AGENTS.md`;
- `PROGRESS.md`;
- `docs/analysis/chatgpt_handoff_latest.md`;
- `docs/analysis/text_table_calibration_subset1_refined_review2_result_2026-07-24.md`;
- `docs/analysis/post_refined_review2_extraction_decision_2026-07-24.md`;
- `docs/analysis/text_table_calibration_subset1_review2_vs_review1_comparison_2026-07-24.md`;
- `docs/analysis/text_table_calibration_subset1_refined_review2_visual_qa_2026-07-24.md`;
- `docs/analysis/text_table_calibration_subset1_refined_review2_validation_2026-07-24.md`;
- `docs/analysis/text_table_calibration/TEXT-TABLE-CALIBRATION-SUBSET1-150-2026-07-24/calibration_review_input.csv`;
- `docs/analysis/text_table_calibration/TEXT-TABLE-CALIBRATION-SUBSET1-150-2026-07-24/calibration_review_rubric.md`;
- `docs/analysis/text_table_calibration/TEXT-TABLE-CALIBRATION-SUBSET1-150-2026-07-24/calibration_review_workbook.md`;
- `docs/analysis/text_table_calibration/TEXT-TABLE-CALIBRATION-SUBSET1-REVIEW1-2026-07-24/`;
- `docs/analysis/text_table_calibration/TEXT-TABLE-CALIBRATION-SUBSET1-REFINED-REVIEW2-2026-07-24/calibration_reviewed.csv`;
- `docs/analysis/text_table_calibration/TEXT-TABLE-CALIBRATION-SUBSET1-REFINED-REVIEW2-2026-07-24/calibration_review_summary.json`;
- `docs/analysis/text_table_calibration/TEXT-TABLE-CALIBRATION-SUBSET1-REFINED-REVIEW2-2026-07-24/calibration_review2_decision.json`;
- `docs/analysis/text_table_detection_ledgers/text_table_detection_ledger_cumulative.csv`;
- `docs/analysis/pdf_readiness_ledgers/pdf_readiness_ledger_cumulative.csv`;
- `docs/analysis/source_review_ledgers/source_review_ledger_cumulative.csv`;
- `docs/dashboard/data/text_table_calibration_status_summary.json`;
- `docs/dashboard/src/components/ProjectHubSections.jsx`;
- `scripts/build_dashboard_data.py`;
- protected `data/contracts.csv`, `data/city_coverage.csv`, and the `corpus/`
  filename inventory.
