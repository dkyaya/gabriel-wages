# Readable parse-text 1,826 targeted conflict QA result — 2026-07-25

## Outcome

Deterministic targeted conflict QA passed for the cumulative provisional
readable parse-text layer. All 37 queued conflict groups were reviewed using
existing structured fields and, where necessary, only the single bounded local
page identified by the stored evidence pointer. Thirty-five groups were
resolved and two remain explicitly unresolved.

This is a corrected provisional shadow layer, not a final merge or analysis
dataset. All 1,826 unique readable content hashes remain covered. OCR-later
documents remain untouched.

## Resolution results

- Review groups processed: 37 / 37
- Resolved: 35
- Unresolved: 2
- `distinct_schedule_cell`: 11
- `distinct_effective_period`: 10
- `distinct_classification_or_rank`: 13
- `non_base_wage_misroute`: 1 group / 3 observations
- `insufficient_evidence_needs_review`: 2
- `duplicate_or_same_observation`: 0 newly assigned in this pass
- `true_conflict_unresolved`: 0

The non-base misroute is a three-value working-out-of-classification premium
rule. The original quantitative observations remain in the shadow ledger with
their IDs and provenance but are inactive; three new non-base-wage shadow
records point back to those original IDs and retain the same bounded page
pointers.

The two unresolved groups are not guessed away. One contains aggregate
fiscal-impact totals rather than employee wage cells. The other contains a
rank/column mismatch that the bounded evidence does not safely disambiguate.

## Corrected shadow counts

- Active quantitative observations: 1,907
- Active qualitative mechanism observations: 1,954
- Active mixed cases: 371
- Active non-base-wage observations: 4,733
- Active reference/exclusion cases: 345
- Quantitative conflict groups: 130
- Cumulative conflict classifications:
  - distinct schedule cell: 60
  - distinct classification/rank: 50
  - distinct effective period: 17
  - non-base-wage misroute: 1
  - insufficient evidence: 2
- Revised unresolved quantitative conflict rate: 2 / 1,907 = 0.1049%

## Integrity and provenance

- Duplicate observation IDs: 0
- Invalid bounded page pointers: 0
- Base/non-base contamination: 0
- Newly canonicalized duplicate observations preserved: 5
- All duplicate-provenance rows preserved: 14
- Matched representation intact: 780 police / 439 fire / 607 non-safety
- States/DC represented: 51
- Source families represented: 6
- Corrected ledgers separate from upstream cumulative ledgers: yes
- Upstream input hashes unchanged: yes

A pre-existing embedded-newline defect split one logical Wasco non-base-wage
observation across two physical CSV records. The new shadow ledger rejoins that
single logical record deterministically, preserving its original observation
ID, bounded pointer, and provenance. The source cumulative ledger remains
byte-for-byte unchanged. This repair reconciles the documented pre-QA active
non-base count of 4,730 before the three working-out-of-classification reroutes.

## Decision

Decision: `readable_parse_text_1826_targeted_conflict_qa_passed`.

All declared targeted-QA integrity gates pass. The corrected layer remains
provisional and analysis readiness remains false. This task does not authorize
a final provisional merge, ingestion, `gabriel.codify`, wage-gap analysis, or
regression. The next safe action is an independent bounded review of the two
remaining unresolved groups and the shadow-ledger record-boundary repair,
followed by a separate explicit decision about any final provisional merge.

## Boundaries observed

GABRIEL/API was not used. No document selection, extraction, URL access,
hosted search, download, redownload, OCR, scout, source review, verification,
ingestion, codification, final merge, wage-gap calculation, regression, or
causal analysis occurred. No full document text, full page text, full tables,
raw prompts, raw responses, image copies, credentials, or secrets were saved.
