# Final provisional package schema readiness review result

## Outcome

Decision: `schema_readiness_hold_schema_repairs_required`.

The final provisional package remains intact and useful, but it is not ready
for an analysis-facing promotion. All five hashes and counts pass, schemas
remain separate, active mixed joins validate, duplicate provenance is
preserved, and the two residual groups remain explicit. The hold reflects
missing or ambiguous analytical contracts rather than a failed package copy.

## Critical blockers

- Raw retained content hashes are not exposed in the lane tables or case index.
- City × unit × negotiation-cycle, matched-set, and controlled occupation
  identifiers are absent.
- Contract-period start/end are blank on every quantitative, qualitative, and
  non-base row.
- Quantitative value columns contain raw ranges, prose, formulas, multipliers,
  percentages, and hours rather than analysis-safe normalized values.
- The non-base ledger repeats two provenance header names; values agree, but
  common CSV readers can silently overwrite the first occurrence.
- Analysis-required source cite, corpus, retrieval, and artifact provenance is
  available only through external IDs, not self-contained in the lanes.

## Join and provenance result

- Active mixed joins: 371; all membership/count/case/key checks pass.
- Active qualitative rows referencing inactive mixed rows: 50 across 16 keys.
- Active qualitative rows referencing five absent historical mixed keys: 20.
- Duplicate observation IDs: 0.
- Duplicate-provenance rows: 14.
- Newly canonicalized duplicates: 5.
- Unique opaque document identities: 1,826 with no metadata conflicts.
- Unresolved conflict groups: 2; future analysis views must quarantine their
  five observations without changing provisional records.

## Lane treatment

- Quantitative: retain raw evidence; add normalized value/unit/date/parse
  status before analysis use.
- Qualitative: retain as provisional mechanism evidence/navigation; require a
  verbatim evidence and QA contract before coded mechanism analysis.
- Mixed: keep valid active joins and explicitly label historical inactive or
  missing keys.
- Non-base wage: retain as a separate companion dataset, never a default
  base-wage outcome input; reason-code or subtype the 904 `other` rows.
- Reference/exclusion: retain as audit/control records only.

Analysis readiness remains false. The justified next task is the separately
authorized, nonmutating schema-repair prompt in the review directory, followed
by another independent analysis-readiness review.
