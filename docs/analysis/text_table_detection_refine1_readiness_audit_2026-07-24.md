# Text/Table Detection Refine 1 Readiness Audit

## Decision

**Ready to prepare the refined visual/table gate.**

Refinement ID:

`TEXT-TABLE-DETECTION-REFINE1-VISUAL-TABLE-GATE-2026-07-24`

This task may change review tooling, schema/rubric documentation, tests, and
the calibration dashboard status. It will not re-review the 150 rows, run
wage extraction, or mutate any original or durable ledger.

## Repository gate

- starting commit:
  `7438f1a68fc0a9874fb5340523f1d9325055ba80`
- requested ancestry: passed for all 13 listed commits
- tracked worktree: clean
- unrelated pre-existing untracked file: root `package-lock.json`
- remotes inspected or modified: no

## Failed calibration authority

The following reviewed packet is the diagnostic authority:

- review result:
  `docs/analysis/text_table_calibration_subset1_review_result_2026-07-24.md`
- reviewed CSV:
  `docs/analysis/text_table_calibration/TEXT-TABLE-CALIBRATION-SUBSET1-REVIEW1-2026-07-24/calibration_reviewed.csv`
- reviewed summary:
  `docs/analysis/text_table_calibration/TEXT-TABLE-CALIBRATION-SUBSET1-REVIEW1-2026-07-24/calibration_review_summary.json`
- rendered challenge:
  `docs/analysis/text_table_calibration/TEXT-TABLE-CALIBRATION-SUBSET1-REVIEW1-2026-07-24/calibration_visual_qa_spotcheck.md`

Verified facts:

- input/reviewed rows: 150 / 150
- `reviewed`: 95
- `needs_second_review`: 55
- calibration extraction gate: `fail`
- next recommendation: `refine_detector_or_schema`
- rendered challenge rows: 5
- rendered challenge material disagreements: 5 / 5

Assisted false-positive-family labels were:

- benefit table: 10
- classification without pay: 2
- index or contents: 1
- non-wage schedule: 4
- numeric appendix: 1
- percentage prose: 1
- other bounded signal without a confirmed table: 18
- unknown: 1
- not applicable under the old rules: 112

These counts are diagnostic, not calibrated precision estimates.

## Failure diagnosis

The failed gate reflects five linked problems:

1. wage/pay words and numeric density were sufficient to label wage-related
   prose as a table;
2. benefit and other numeric schedules were insufficiently separated from
   wage/salary schedules;
3. front matter and memoranda could receive table-layout labels;
4. contents/index pages could reference a real salary table beyond the old
   page window;
5. the assisted adjudicator reused detector features and therefore measured
   concordance rather than independent precision.

The 500-document extraction prompt remains prohibited because these failures
affect both candidate-page precision and claimed layout type. Extraction
cannot be authorized until wage language, pay-number language, actual table
structure, page relationship, and confirmation method are recorded
separately and a later independent calibration passes.

## Immutable baselines

- original calibration input SHA-256:
  `489e39cd99ba8812eb0b101b595825cdecd66da630c7a2eea7c612bdcc097535`
- REVIEW1 reviewed CSV SHA-256:
  `a50cd8a8c0b2b4d261db03c0b0cf183c060ce5e11b95bc89b77fcd965f0ff13c`
- REVIEW1 summary SHA-256:
  `48711714817c45246cefce8168a22c661d726e3cce8c24c97081abb04f236455`
- durable text/table ledger SHA-256:
  `4992efe74c4d76d66e345ab9716b987df850b73b3db98af17a2573da98bced03`
- durable PDF-readiness ledger SHA-256:
  `dd120453068a668b5c818352402ca828073ac9639ee4d8d1ffc88f9488d4d953`
- durable source-review ledger SHA-256:
  `e29d580d42068615611b464e6da40654f336f273fa7c40a7b0717d4894148c9f`
- `data/contracts.csv` SHA-256:
  `ed26cff96061e45ff668a02231547a6c9c11ec4b138772bfb3d5de34a229e1e8`
- `data/city_coverage.csv` SHA-256:
  `4fdf135ff3741893f5a4c45edc52a70159adc87598b777dfc4373dd8481249e3`
- corpus filename-list SHA-256:
  `32e084f0bbbbf118681e25e607c1dbf1c6c78e8c7d9221416f4ead4b2d080322`

The original calibration input and all REVIEW1 outputs will remain
byte-identical.

## Permitted local scope

Implementation and tests may use synthetic local PDFs. If bounded rule
development needs a real artifact, only paths present in the original
150-row calibration input are eligible. This preparation task does not run
the refined review over those artifacts.

## Boundaries

- no URL, network, API, model, or hosted-search access;
- no download or redownload;
- no OCR;
- no wage-table or wage-value extraction;
- no full page/document text or complete table retention;
- no ingestion or `gabriel.codify`;
- no scout, routing, metadata-triage, source-review, PDF-readiness, durable
  text/table-detection, or original calibration mutation;
- no wage-gap calculation, regression, causal claim, remote inspection, or
  push.
