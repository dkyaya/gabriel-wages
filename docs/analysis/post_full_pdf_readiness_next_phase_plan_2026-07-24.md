# Post-Full-PDF-Readiness Next-Phase Plan

Date: 2026-07-24

## Current durable state

The full retained PDF-readiness merge is complete:

- retained PDFs checked: 2,124;
- `parse_text_layer_later`: 1,828;
- `ocr_later`: 296;
- total pages represented: 108,028;
- text layer present / partial / absent: 1,608 / 220 / 296;
- page counts available: 2,124 / 2,124; and
- parser/hash/missing/signature failures in the collected readiness rounds:
  0 / 0 / 0 / 0.

The durable stage is
`technical_readiness_checked_not_extracted`. No PDF was opened or parsed
during the serial merge.

## Recommended substantive phase

The next task should prepare a bounded **text-layer content-structure and
table-detection pilot**. It should not perform a full-corpus wage extraction.

Recommended sequence:

1. select a deterministic 100-200 PDF sample from the 1,828
   `parse_text_layer_later` rows;
2. run local-only, bounded text-layer and layout/table-structure checks;
3. preserve source identity and content-relevance uncertainty;
4. report table-detection and contract-period signals without promoting
   results to ingested or codified evidence; and
5. use pilot yield and manual-review burden to design any later extraction
   workflow.

## Recommended pilot design

Use 150 PDFs by default, with coverage across:

- p1 and p2 metadata priority;
- police, fire, and non-safety units;
- municipal, state-repository, union, uncertain, and unknown preliminary
  officialness signals;
- multiple states and municipalities;
- page-count bins 1-10, 11-25, 26-50, 51-100, and over 100;
- source-review Pilot 1, Batch 2, and Batch 3 artifacts;
- CBAs; and
- wage schedules or compensation plans where available.

Selection should remain deterministic and disjoint by source-review and
candidate identity. The pilot should not assume that a `cba_candidate`
metadata label proves the artifact is the intended agreement.

## Pilot outputs

The pilot may produce bounded structural metadata such as:

- parser and layout library/version;
- pages inspected;
- text extraction success by page;
- table-detection confidence;
- candidate table page numbers;
- bounded non-wage structural snippets only if separately authorized;
- candidate contract-period hints;
- source-identity and relevance caveats;
- manual-review routing; and
- an extraction-readiness recommendation.

It should not populate final wage observations, calculate growth, infer
mechanisms, ingest records, codify evidence, or analyze wage gaps.

## Why OCR should not start automatically

The 296 `ocr_later` rows had no text on the bounded sampled pages. That does
not prove all pages are image-only, and it does not show that the artifacts
are substantively relevant or worth OCR expense. OCR could also generate
large, noisy text outputs that require additional provenance, confidence,
and verbatim safeguards.

Before authorizing OCR:

1. inspect a small stratified no-text sample;
2. distinguish fully image-only files from mixed or parser-hostile files;
3. confirm source identity and relevance;
4. define text-retention and quality controls; and
5. establish a separate storage and audit budget.

## Why broad scouting should remain paused

The project already retains 2,124 PDFs representing 4.50 GB and 108,028
pages. Technical access is no longer the main uncertainty. The next useful
question is whether bounded local extraction can identify relevant document
structure and candidate tables while preserving identity and provenance.

Broad scouting would add candidate leads rather than resolve this
content-readiness bottleneck.

## Why remaining p2 downloads should wait

Downloading more p2 sources would increase storage and review burden before
the project knows:

- how often text-bearing PDFs expose usable table structures;
- how much manual validation is required;
- whether source identity and relevance can be established efficiently;
- which parsers are robust to the observed PDF population; and
- what extraction schema should precede ingestion and codification.

Finish or expand downloads only after the bounded text-layer/table-detection
pilot provides evidence that the additional artifact volume will be useful.

## Continuing boundaries

The next task should remain local-only unless separately authorized. It
should run no OCR, ingest no contract, run no `gabriel.codify`, extract no
final wage values, calculate no wage gap, make no empirical or causal claim,
and run no regression.
