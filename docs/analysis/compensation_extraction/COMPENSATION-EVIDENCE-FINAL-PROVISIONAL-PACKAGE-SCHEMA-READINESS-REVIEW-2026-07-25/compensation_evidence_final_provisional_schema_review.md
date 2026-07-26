# Final provisional compensation-evidence schema readiness review

## Decision

`schema_readiness_hold_schema_repairs_required`

The package passes immutable-package integrity review, but it is not yet safe
for an analysis-facing promotion. The five files are internally stable and
remain useful provisional evidence. The hold is about analytical schema
semantics—not a loss of rows or a failed package copy.

Analysis readiness remains `false`. No promotion, ingestion, codification,
analysis dataset, wage-gap calculation, regression, or causal analysis was
performed or authorized.

## Package integrity

- All five ledger SHA-256 values match the package manifest and recorded
  output hash file.
- The input and output hash sets match exactly.
- Source/active rows reconcile at 2,044/1,907 quantitative, 1,954/1,954
  qualitative, 387/371 mixed, 4,746/4,733 non-base wage, and 345/345
  reference/exclusion.
- Schemas remain physically separate; no cross-schema concatenation exists.
- There are 1,826 stable opaque document identities with consistent metadata.
- Duplicate observation IDs remain zero; 14 duplicate-provenance rows and five
  newly canonicalized observations remain preserved.
- All 371 active mixed rows have valid declared member counts, member IDs,
  case IDs, active members, and join keys.
- Both residual conflict groups remain explicit and all five affected
  quantitative observations remain active in the provisional ledger.
- OCR-later documents remain excluded.

## Why package QA does not establish analysis readiness

### 1. Analytical identity is incomplete

Every active observation has an extraction case ID, opaque document identity,
text-table detection ID, source-review ID, candidate-queue ID, state,
municipality, government, unit type, and source family. These are strong audit
keys.

However, the lane schemas do not carry:

- the raw retained content hash;
- a city × unit × negotiation-cycle or matched-set identifier;
- a negotiation-cycle identifier; or
- the controlled analytical `occupation_class`.

The case index also stores only the opaque `document_identity_id` as a hash
reference; it does not expose the raw retained hash. `unit_type` distinguishes
police, fire, and non-safety but is not enough to implement the project's
cross-occupation matched-city-cycle design. Source-review/detection IDs provide
join paths, but provenance needed for analysis is not self-contained.

### 2. Quantitative fields are provisional evidence, not normalized wage facts

Of 1,907 active quantitative rows:

- 1,176 (61.67%) have at least one nominal amount field;
- 1,739 (91.19%) have an amount or percentage field;
- 627 (32.88%) identify an occupation/classification/rank;
- 1,217 (63.82%) have an effective-date expression;
- 1,338 (70.16%) have a currency/unit expression;
- 0 have a populated contract-period start or end; and
- 194 use the `other` compensation type.

The nominal numeric columns are raw strings, not analysis-safe numeric fields.
Examples include ranges, current/new pairs, prose formulas, percentages in
salary fields, multipliers, hours, and qualitative rate references. A future
schema must preserve every raw value while adding explicit parsed value,
range, unit, annualization, and parse-status fields. Ambiguous strings must be
quarantined rather than coerced.

QA is also still provisional: 1,461 active quantitative rows are labeled
`provisional_unverified`, 102 `needs_conflict_review`, 97 `needs_review`, and
five retain a historical `needs_non_base_wage_review` status even though the
later routing layer resolved contamination. An analysis view must derive one
authoritative current status from the later QA fields without dropping any
earlier status or provenance.

### 3. Qualitative evidence is structured but not verbatim-analysis ready

All 1,954 active qualitative rows have a mechanism type and bounded evidence
pointer, and 1,935 (99.03%) populate at least one mechanism-detail field. The
schema covers bargaining logic, indexing, comparability, parity, progression,
eligibility, implementation, fiscal constraints, reopeners, and
differentiation.

But no dedicated verbatim evidence-span field exists, contract-period fields
are empty on all rows, and 1,709 rows are `provisional_unverified` while 245
are `needs_review`. The mechanism fields may support evidence navigation and
descriptive schema work, but they should not be promoted as final coded
mechanism measurements without a separate verbatim/provenance and QA rule.

### 4. Active mixed joins are valid, but historical keys need explicit semantics

All 371 active mixed rows pass strict membership checks. No active
quantitative row points to an inactive or absent mixed key.

Fifty active qualitative rows retain keys for 16 inactive mixed rows, and 20
additional active qualitative rows retain five historical mixed keys absent
from the mixed ledger. These are preserved provenance references, not active
mixed memberships. A future schema must keep the raw keys while deriving an
explicit `mixed_membership_status` so analysts cannot mistakenly join them as
current mixed cases.

### 5. Non-base compensation is correctly separate but needs a safe contract

The 4,733 active non-base observations remain physically separate from base
wage evidence. This is correct. They should remain a companion dataset for
benefits/premiums/mechanism research and must never be included in a base-wage
outcome by default.

The schema has duplicated header names for
`source_quantitative_observation_id` and `source_mixed_join_key`. Both copies
currently contain identical values (134 and 85 populated rows respectively),
so no current value conflict was found, but ordinary dictionary-based CSV
readers silently overwrite the first occurrence. A lossless schema repair must
rename both occurrences and assert equality before deriving one canonical
lineage field.

The `other` family contains 904 active observations (19.10%). It is too broad
for unrestricted mechanism or benefits analysis. Preserve it, require a reason
code, and either subtype it deterministically or keep it excluded from typed
non-base analyses.

### 6. Reference/exclusion rows are control records, not outcomes

The 345 active rows comprise 256 exclusions, 82 reference-only cases, and
seven second-review cases. Bounded pointers exist for 314 rows; missing
pointers are acceptable for some no-candidate/exclusion cases but must remain
explicit. This lane should stay an audit/control table and must not enter wage
or mechanism outcome calculations.

### 7. Residual conflict treatment

The following groups remain unresolved:

- `qares1826_98591102083229343fecc71f`
- `qares1826_3dded7aaf73536d0a8f5842f`

The provisional rows and pointers remain unchanged. A future analysis-facing
view must quarantine the five member observations from derived outcomes while
retaining them in an exceptions table and preserving the conflict register.
This is not permission to infer missing rank, step, cell, classification, or
effective-period distinctions.

## Readiness conclusion

The package is suitable as the immutable source for a **schema-repair and
analysis-view preparation task**, but not yet for analysis-facing promotion.
Critical repairs are:

1. create unique column names for duplicate non-base lineage fields;
2. add or deterministically bridge raw content hashes and full provenance;
3. add matched-set, negotiation-cycle, and controlled occupation identifiers;
4. preserve raw quantitative strings while adding normalized values and parse
   status;
5. define a single derived current-active/current-QA contract;
6. distinguish active mixed membership from historical keys;
7. quarantine the two residual conflict groups;
8. keep non-base and reference/exclusion lanes outside base-wage outcomes; and
9. establish a verbatim-evidence/QA rule for qualitative mechanism promotion.

The accompanying `next_schema_repair_prompt.md` is justified. It is a future
prompt only and requires separate authorization before execution.
