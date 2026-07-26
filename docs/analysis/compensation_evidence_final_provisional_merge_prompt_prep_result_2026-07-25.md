# Final provisional compensation-evidence merge prompt prep result - 2026-07-25

## Outcome

The future final provisional merge prompt is prepared and has not been run.
The preparation is authorized by the independent-review decision, while the
merge itself still requires a separate explicit user authorization.

The future prompt treats the merge as a rollback-safe package promotion, not a
cross-schema concatenation. It requires the five corrected ledgers to remain
five separate, byte-identical evidence tables plus a non-analytic case index,
manifest, hashes, conflict register, reconciliation report, and decision.

## Locked future inputs

Only these five corrected shadow ledgers may contribute rows:

1. `readable_parse_text_1826_quantitative_ledger_qa_corrected.csv`
2. `readable_parse_text_1826_qualitative_mechanism_ledger_qa_corrected.csv`
3. `readable_parse_text_1826_mixed_ledger_qa_corrected.csv`
4. `readable_parse_text_1826_non_base_wage_ledger_qa_corrected.csv`
5. `readable_parse_text_1826_reference_exclusion_ledger_qa_corrected.csv`

Their exact independent-review SHA-256 values are embedded in the prompt. A
future run must recompute and match all five before creating any final output
directory. It must dry-run and reconcile row counts, active counts, IDs,
pointers, duplicates, joins, reroutes, the Wasco repair, representation, and
all 1,826 content hashes before materialization.

## Preservation and stop rules

The prompt requires preservation of every observation/case/source ID,
duplicate and canonical relationship, active/inactive flag, original
observation ID, bounded page pointer, mixed join key, source-review and
text-table identifiers, content hash, and unit/state/source metadata.

Both residual conflict groups and their five observation IDs remain explicitly
unresolved. No rank, step, classification, pay band, schedule cell, or
effective period may be guessed.

OCR-later documents stay excluded. The future package must not write to
`data/`, `corpus/`, ingestion inputs, codified outputs, or final analysis paths.
It must stop before ingestion or codification, and analysis readiness must
remain false.

## Actions not taken

No merge, provisional package materialization, extraction, selection,
GABRIEL/API call, URL access, download, OCR, ingestion, codification, wage-gap
calculation, regression, or causal analysis occurred. No corrected, durable,
QA, or independent-review ledger was changed.
