# Future Full Text/Table Detection Run Prompt

This is a future task specification. Do not execute it as part of Pilot 1.

## Objective

Prepare and run a bounded local text-layer/table-detection pass over all
durable PDF-readiness rows whose recommended next action is
`parse_text_layer_later`.

Suggested round ID:

`TEXT-TABLE-DETECTION-FULL-PARSE-TEXT-2026-07-24`

The current durable universe contains 1,828 such rows. Recompute that count
from the durable PDF-readiness ledger when the task begins.

## Input policy

Use:

`docs/analysis/pdf_readiness_ledgers/pdf_readiness_ledger_cumulative.csv`

Select exactly all rows that:

- are terminal durable PDF-readiness rows;
- have `recommended_next_action = parse_text_layer_later`;
- have text-layer status `present` or `partial`;
- retain a local PDF path, hash, positive byte size, and page count; and
- are unique by PDF-readiness, source-review, and candidate identity.

Preferred design: rerun all 1,828 rows, including the 150 Pilot 1 rows, under
the frozen `bounded_keyword_numeric_structure_v1` heuristic so the eventual
cumulative layer has one uniform round. If Pilot 1 rows are excluded
instead, require exact disjointness and prepare a later cumulative merge of
both rounds.

## Lane design

Use four balanced local lanes, approximately 457 rows each if the eligible
count remains 1,828. Four lanes balance local throughput and auditability
without creating unnecessary coordination overhead.

Do not run more than six lanes. Do not retry rows into new output
directories in the same task.

## Bounded runner settings

- local retained artifacts only;
- `max_pages_to_scan = 10`;
- `max_text_chars_per_page = 1500`;
- `timeout_per_file = 30`;
- `no_save_text = true`;
- no network client;
- no URL access;
- no downloads/redownloads;
- no OCR;
- no final wage extraction;
- no ingestion/codification.

The runner may output only:

- terminal status;
- parser/version/timing;
- page and bounded-character counts;
- wage-table, contract-period, and table-structure signal categories;
- one-based candidate page numbers;
- component-signal booleans;
- extraction-pilot scheduling priority;
- generic notes; and
- at most 300 characters of currency/percentage-redacted contract-period
  hints per document.

Never save complete page/document text or reconstructed wage tables.

## Gates

Before local parsing:

1. require clean tracked worktree;
2. verify durable PDF-readiness authority hash and row counts;
3. lock all inputs and lane hashes;
4. require exact eligible identity coverage;
5. run every lane in dry-run mode; and
6. require dry-run audit success and all prohibited-activity counters zero.

After local parsing:

1. require terminal status for every selected row;
2. verify artifact hashes and sizes;
3. audit duplicate/missing/unexpected identities;
4. validate candidate page numbers;
5. enforce 300-character hint caps;
6. scan outputs for full-text artifacts and unredacted money patterns;
7. summarize signal distributions, runtime, and manual-calibration burden;
8. preserve the distinction between heuristic hints and wage evidence; and
9. stop before durable merge.

## Manual calibration requirement

Pilot 1 produced 94 likely, 55 possible, and one unlikely wage-table signal.
Before final wage-table extraction, draw a small stratified human-review
sample across likely/possible/unlikely signals, source types, units, and
page-count bins. Estimate false-positive and false-negative rates and decide
whether heuristic thresholds should change.

Do not rewrite or silently reclassify Pilot 1 outputs. Version any revised
heuristic.

## End-of-task boundary

The full run task must:

- collect and audit lane-local outputs;
- create no durable merged text/table-detection ledger;
- prepare a future cumulative serial merge prompt;
- mutate no scout, routing, metadata-triage, source-review, or PDF-readiness
  ledger;
- write nothing to `corpus/`;
- extract no final wage values;
- ingest or codify nothing;
- calculate no wage gap;
- make no causal claim;
- run no regression; and
- inspect no remote and perform no push.
