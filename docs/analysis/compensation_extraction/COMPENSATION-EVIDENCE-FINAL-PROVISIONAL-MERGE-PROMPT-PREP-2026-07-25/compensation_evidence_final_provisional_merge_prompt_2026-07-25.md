# Future task: final provisional compensation-evidence package merge

## Authorization boundary

This prompt is prepared for a future Codex run. Do not execute it unless the
user separately and explicitly authorizes the final provisional merge.

Even when authorized, this task creates only a provisional, QA-gated package.
It does not create a final analysis dataset and does not authorize ingestion,
`gabriel.codify`, wage-gap analysis, regression, or causal inference.

Task ID:
`COMPENSATION-EVIDENCE-FINAL-PROVISIONAL-MERGE-2026-07-25`

Repository:
`/Users/joachimjohnson/Documents/RA_2026/Pol_Fire/gabriel-wages`

Expected starting authority:

- Independent review commit:
  `30fc55db984e7a4de8837e6534b327a87a42403c`
- Independent review decision:
  `independent_review_pass_final_provisional_merge_prompt_allowed`
- The decision authorizes prompt preparation only. Before running this future
  task, require a new user instruction that explicitly authorizes execution of
  the provisional merge.

## Goal

Materialize one rollback-safe provisional package for all 1,826 unique readable
parse-text content hashes. Preserve the five audited evidence schemas as five
separate ledgers. Do not concatenate unlike records into a single table.

The merge is package-level: copy and verify the five corrected ledgers without
changing their rows, then build a non-analytic case index, manifest,
reconciliation report, and hashes around them. The package remains separate
from `data/`, `corpus/`, ingestion inputs, codified outputs, and all final
analysis dataset locations.

## Only allowed merge-data inputs

The following five files are the complete and exclusive merge-data inputs.
No other ledger, CSV, PDF, document, URL, prior extraction output, or OCR-later
artifact may contribute a data row.

Base directory:
`docs/analysis/compensation_extraction/COMPENSATION-EVIDENCE-EXTRACTION-READABLE-PARSE-TEXT-1826-TARGETED-CONFLICT-QA-2026-07-25/`

1. `readable_parse_text_1826_quantitative_ledger_qa_corrected.csv`
   - SHA-256: `7e275b8c45f0d4b77e01249d978fe17862fd3f8d552bf0f4ef77ed0bb3616c86`
2. `readable_parse_text_1826_qualitative_mechanism_ledger_qa_corrected.csv`
   - SHA-256: `d22a4015da83da7d0195e430ef30d475b3678c17696e7a835d6d09bce1a1e0d5`
3. `readable_parse_text_1826_mixed_ledger_qa_corrected.csv`
   - SHA-256: `a204061a4ca4bbfd3512bf964d689fe385dfd71fac93589a4bb9b59e64eb9192`
4. `readable_parse_text_1826_non_base_wage_ledger_qa_corrected.csv`
   - SHA-256: `84df35187461392ea9699660ea86317250a33979e6ff2b4f9256a49b1d9e0ea2`
5. `readable_parse_text_1826_reference_exclusion_ledger_qa_corrected.csv`
   - SHA-256: `2a33987b8f54048d8a397fc7d9a917dafd2dbcf8b7b74a20de8c2642a886e3a1`

The independent-review decision, summary, ledger, report, and validation may be
read only as authority and QA metadata. They are not merge-data inputs and may
not supply, change, or delete an evidence row.

## Expected input reconciliation

Fail closed unless all expected counts reconcile before any package file is
written:

| Schema | Source rows | Active rows |
| --- | ---: | ---: |
| Quantitative base compensation | 2,044 | 1,907 |
| Qualitative mechanisms | 1,954 | 1,954 |
| Mixed quant/qual joins | 387 | 371 |
| Non-base-wage compensation | 4,746 | 4,733 |
| Reference/exclusion | 345 | 345 |

Also require:

- 1,826 unique readable parse-text cases/content hashes remain covered;
- unit representation remains 780 police / 439 fire / 607 non-safety;
- 51 states/DC and 6 source families remain represented;
- duplicate observation IDs remain 0;
- invalid bounded page pointers remain 0;
- active base/non-base contamination remains 0;
- 14 duplicate-provenance rows remain present;
- the 5 newly canonicalized duplicate observations remain linked to their
  canonical records;
- the working-out-of-classification reroute remains 3 inactive quantitative
  source rows plus 3 active provenance-linked non-base rows;
- the Wasco shadow contains one logical repaired record and no malformed tail
  record; and
- OCR-later documents remain excluded.

## Two explicitly unresolved conflict groups

Preserve both groups as explicitly unresolved. Do not guess a rank, step,
classification, pay band, schedule cell, or effective period.

1. Resolution `qares1826_98591102083229343fecc71f`
   - Observations:
     `qobs_985ddb7a53fed53c92361fdb`,
     `qobs_443497d509eb8f225658b2c9`
   - Reason: aggregate fiscal-impact estimates are not employee wage cells.
2. Resolution `qares1826_3dded7aaf73536d0a8f5842f`
   - Observations:
     `qobs_e7d065a47ede9da2ca9c9bf4`,
     `qobs_c702c01aaa380ba5421a63ef`,
     `qobs_642603a66adb930a4bc11f89`
   - Reason: the bounded rank schedule cannot be mapped safely to the stored
     records because rank/effective-period structure is under-specified.

Their status, IDs, active flags, reason codes, pointers, and provenance must
survive unchanged. The expected unresolved rate is 2 / 1,907 = 0.1049%.

## Required preservation contract

For every source row, preserve without normalization or inference:

- observation ID and canonical observation ID;
- extraction/case ID;
- original/source observation ID;
- duplicate-of link and all duplicate provenance rows;
- active and inactive status flags from every QA layer;
- bounded evidence pointer and page number;
- mixed join key and quantitative/qualitative membership IDs;
- source review ID;
- text-table detection ID;
- PDF-readiness/candidate identity fields when present;
- retained content hash;
- municipality/government, state, unit, source-family, cycle, and contract
  metadata;
- confidence, reason codes, QA status, and explicit unresolved flags; and
- field ordering and values in each source ledger.

Do not delete inactive rows. Do not silently discard duplicates. Do not repair,
reinterpret, or promote records during packaging. Do not move non-base-wage
records into quantitative base compensation or the reverse.

## Required output directory

Write only under a new, non-existing rollback-safe directory:

`docs/analysis/compensation_extraction/COMPENSATION-EVIDENCE-FINAL-PROVISIONAL-MERGE-2026-07-25/`

If that directory already exists, stop. Do not overwrite or resume unless a
separate, explicit recovery plan identifies the exact prior attempt.

## Required outputs

Keep all five schemas separate:

1. `ledgers/quantitative/final_provisional_quantitative_ledger.csv`
2. `ledgers/qualitative/final_provisional_qualitative_mechanism_ledger.csv`
3. `ledgers/mixed/final_provisional_mixed_join_ledger.csv`
4. `ledgers/non_base_wage/final_provisional_non_base_wage_ledger.csv`
5. `ledgers/reference_and_exclusion/final_provisional_reference_exclusion_ledger.csv`

Each output ledger must be a byte-for-byte copy of its allowed corrected input.
The output SHA-256 must therefore equal the corresponding approved input
SHA-256. Any transformation, column reorder, newline rewrite, or row rewrite is
a failure.

Additional package metadata:

- `final_provisional_case_index.csv`
  - one non-analytic identity/provenance row per unique case/content hash;
  - no wage values, mechanism spans, or full text;
  - lane-presence counts and unresolved/duplicate flags only.
- `final_provisional_merge_manifest.json`
- `final_provisional_input_sha256.txt`
- `final_provisional_output_sha256.txt`
- `final_provisional_reconciliation_summary.json`
- `final_provisional_reconciliation_report.md`
- `final_provisional_validation_2026-07-25.md`
- `final_provisional_decision.json`
- `final_provisional_conflict_register.csv`
  - exactly the two unresolved groups and their preserved observation IDs;
  - no fabricated resolution fields.

Do not write any output to `data/`, `corpus/`, `ingest/`, `inbox/`, codified
artifact locations, dashboard analysis datasets, or final-analysis paths.

## Implementation requirements

Create:

- `scripts/run_compensation_evidence_final_provisional_merge.py`
- `scripts/test_compensation_evidence_final_provisional_merge.py`

The runner must support:

- `--mode dry_run`
- `--mode materialize_provisional_package`
- `--output-dir`
- `--require-explicit-merge-authorization`
- `--no-ingestion`
- `--no-codify`
- `--no-analysis`

The materialization mode must refuse to run unless the explicit authorization
flag is present and the user instruction for that future task clearly
authorizes executing this prompt. The runner must never call GABRIEL/API,
network code, OCR, ingestion, or codification.

## Execution order

1. Inspect tracked worktree state. Stop on unexpected tracked changes.
2. Confirm the independent-review decision is exactly
   `independent_review_pass_final_provisional_merge_prompt_allowed` and that it
   still says `final_provisional_merge_allowed = false`. Confirm the current
   user request separately authorizes executing the merge despite that earlier
   preparation-only boundary.
3. Confirm all five allowed inputs exist and no sixth merge-data input is
   configured.
4. Compute SHA-256 for each input and compare to the five exact values above.
   Stop before creating the output directory if any hash differs.
5. Validate CSV headers, physical/source row counts, active row counts, unique
   IDs, pointers, duplicates, reroutes, Wasco repair, mixed joins, case/content
   coverage, representation, and the two unresolved groups in memory.
6. Run dry-run first. The dry-run may write only to `tmp/` and must not create
   the final output directory or copy a ledger.
7. Run all offline tests and inspect the dry-run reconciliation.
8. Only after every dry-run gate passes, create a fresh temporary staging
   directory under the final output parent.
9. Copy the five ledgers byte-for-byte, build the case index/manifest/register,
   compute output hashes, and validate the staged package.
10. Atomically rename the staging directory to the final output directory only
    after complete validation. On failure, leave the existing source ledgers
    unchanged and do not publish a partial final directory.
11. Reopen every output and rerun all counts, ID, pointer, duplicate, join,
    conflict, provenance, and SHA-256 checks.
12. Stop before ingestion, codification, analysis, or any final-analysis merge.
13. Update dashboard status only to provisional-package-materialized and keep
    analysis readiness false.
14. Run validation, commit locally, use plain `git push` only if dashboard files
    changed, and create a lite relay without the five full ledgers.

## Focused tests

Tests must prove:

- dry-run creates no final output and copies no ledger;
- exactly five merge-data inputs are accepted;
- a missing, extra, or hash-mismatched input fails before materialization;
- all output ledger bytes and SHA-256 values equal their inputs;
- expected source and active counts reconcile;
- duplicate IDs remain zero and all 14 duplicate-provenance rows remain;
- all 5 newly canonicalized duplicates retain valid canonical links;
- inactive rows are retained;
- bounded page pointers remain valid;
- mixed join keys and member IDs remain unchanged;
- working-out-of-classification reroutes remain separate and linked;
- the Wasco logical record remains repaired without changing its original ID;
- exactly two unresolved groups remain explicit with the exact observation IDs
  listed above;
- all 1,826 unique content hashes and unit/state/source representation remain;
- OCR-later documents are excluded;
- no output enters `data/`, `corpus/`, ingestion, codified, or analysis paths;
- no URL/network/GABRIEL/OCR/ingestion/codify/analysis code path exists; and
- analysis readiness remains false.

## Required validation commands

```bash
.venv/bin/python -m py_compile scripts/run_compensation_evidence_final_provisional_merge.py scripts/test_compensation_evidence_final_provisional_merge.py scripts/build_dashboard_data.py
.venv/bin/python scripts/test_compensation_evidence_final_provisional_merge.py
.venv/bin/python scripts/build_dashboard_data.py
npm --prefix docs/dashboard run build
.venv/bin/python scripts/validate.py
.venv/bin/python ingest/test_pipeline.py
.venv/bin/python ingest/audit_coverage.py
git diff --check
```

Also independently verify all five source hashes again after materialization and
confirm no protected upstream ledger changed.

## Decision and dashboard rules

The future decision must be one of:

- `final_provisional_package_materialized_qa_pass`
- `final_provisional_package_blocked_integrity_failure`

Even on pass:

- `final_analysis_ready` must remain `false`;
- `ingestion_allowed` must remain `false`;
- `codify_allowed` must remain `false`;
- `wage_gap_analysis_allowed` must remain `false`;
- `regression_allowed` must remain `false`; and
- the next action must be a separate schema/analysis-readiness review, not
  automatic ingestion or analysis.

## Hard constraints

- Do not open URLs or use hosted search.
- Do not fetch, pull, inspect, configure, or change remotes.
- Do not download or redownload documents.
- Do not run OCR or include OCR-later documents.
- Do not run scouts, source review, verification, extraction, or selection.
- Do not call GABRIEL/API/models.
- Do not ingest or run `gabriel.codify`.
- Do not calculate wage gaps, run regressions, or make causal claims.
- Do not create a final analysis dataset.
- Do not write full document/page text, full tables, raw prompts/responses, or
  image copies.
- Do not print or save credentials, tokens, cookies, raw auth headers, dotenv
  values, or environment values.
- Do not mutate the five corrected inputs or any durable/prior ledger.
- Do not resolve the two remaining conflict groups by guessing.

## Commit, push, and relay

Recommended commit message:

`Materialize final provisional compensation evidence package`

Use plain `git push` only if dashboard-relevant files changed. Do not inspect or
repair remotes.

Create:

`tmp/compensation_evidence_final_provisional_merge_relay_2026-07-25_<commit>.zip`

Include scripts, tests, manifests, summaries, conflict register, validation,
decision, dashboard status, `next_task.md`, git status/log, and push status.
Exclude the five full copied ledgers, PDFs, rendered images, raw prompts,
responses, full text, full tables, secrets, build artifacts, and unrelated
`package-lock.json`.

## Final response requirements

Report the commit/push status, five input and output hashes, dry-run result,
materialization result, case/content-hash coverage, all five source/active
counts, duplicate/pointer/contamination counts, unresolved groups, provenance
and join preservation, OCR exclusion, QA decision, dashboard status, analysis
readiness, forbidden-action confirmations, relay path, and next recommendation.
