# Cumulative 1,000-document compensation extraction targeted QA result

Task ID: `COMPENSATION-EVIDENCE-EXTRACTION-1000DOC-TARGETED-QA-2026-07-25`

## Result

The deterministic targeted QA pass processed all 151 unresolved rows/groups
from the cumulative provisional 1,000-document extraction layer. No new
document was selected, no extraction was run, and GABRIEL/API was not used.

The recomputed integrity QA passes. The remaining unique readable parse-text
documents are authorized for a future provisional extraction run, subject to
the same bounded-packet, lane, resumability, provenance, and stop-before-final-
merge controls.

## Routing review

The 126 possible base/non-base quantitative records were classified as:

- `retain_quantitative_base_wage`: 5;
- `route_to_non_base_wage`: 120;
- `split_quant_and_non_base_components`: 0;
- `reference_only`: 1;
- `insufficient_evidence_needs_review`: 0.

The five retained records are bounded, visually checked base-salary cells in
which certification is a classification descriptor or premium-time values are
separate columns. Every rerouted or reference-only record preserves the source
quantitative observation ID, bounded evidence pointer, and mixed join key when
present. The shadow ledgers retain all source rows and add explicit active-lane
flags; the source cumulative ledgers are unchanged.

An additional 11 observations from four conflict groups were routed to
non-base-wage families, and one promotional-exam percentage was routed to the
reference/exclusion lane. In total, the corrected layer creates 131 new
non-base-wage provenance records and two reference rows from quantitative
sources.

## Quantitative conflicts

The 25 under-specified conflict groups were classified as:

- `distinct_classification_or_rank`: 7;
- `distinct_effective_period`: 5;
- `distinct_schedule_cell`: 6;
- `non_base_wage_misroute`: 5;
- `insufficient_evidence_needs_review`: 2.

Twenty-three groups are resolved. Two remain explicit rather than guessed:

1. aggregate fiscal-impact dollar estimates that are not employee wage cells
   and do not have a safe lane conversion; and
2. a salary capture whose extracted rank conflicts with the visible schedule
   row and whose source reason codes already mark ambiguous columns.

The revised unresolved rate is `2 / 1,214 = 0.1647%`, below the 2% threshold.

## Corrected provisional shadow layer

- Active quantitative observations: 1,214
- Active qualitative mechanism observations: 1,464
- Active mixed cases: 256
- Active non-base-wage observations: 2,889
- Active reference/exclusion rows: 175
- Duplicate observation IDs: 0
- Invalid bounded page pointers: 0
- Existing canonicalized duplicate observations preserved: 9
- Unresolved base/non-base contamination: 0
- Unit representation: 363 police / 237 fire / 400 non-safety
- Matched representation intact: `true`
- Corrected ledgers provisional and separate: `true`

## Recomputed decision

- Integrity QA: `pass`
- Targeted QA: `pass`
- Decision: `remaining_readable_parse_text_extraction_allowed`
- Remaining readable parse-text extraction allowed: `true`
- Final analysis merge allowed: `false`
- Ingestion allowed: `false`
- Codification allowed: `false`

The current durable detection ledger has 1,828 rows and 1,826 unique content
hashes. Removing the frozen 1,000 selected hashes leaves 827 rows representing
826 unique retained readable content hashes. This is an inventory for the next
planning task, not a selection or extraction performed here.

## Boundaries

No URL access, hosted search, download, redownload, OCR, scout, source review,
verification, new extraction, document selection, GABRIEL/API call, ingestion,
`gabriel.codify`, final analysis merge, wage-gap calculation, regression, or
causal claim occurred. No full document/page text, full table, raw prompt/raw
response, image copy, credential, or secret was saved.

## Validation

Python compilation passed. The seven relevant offline/mock suites passed 72
tests: 12 cumulative-extraction, 10 provisional-500 extraction, 8 prior
targeted-QA, 9 cumulative targeted-QA, 14 Gate 1, 10 Gate 2, and 9 Gate 3.
Dashboard data and frontend production builds passed; repository validation and
all 60 ingestion pipeline tests passed. Coverage remains 28 healthy matched
pairs (10 exact, 18 overlap), 2 adjacent pairs, and 6 unmatched safety units.
Input-hash checks, secret scanning, JSON parsing, protected-path checks, and
`git diff --check` passed.
