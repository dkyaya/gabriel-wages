# Future task: repair provisional compensation schemas before analysis promotion

This is a future Codex task prompt. Do not run it without separate explicit
user authorization.

## Objective

Create a rollback-safe, analysis-view-preparation layer from the immutable
five-ledger final provisional package. Repair schema mechanics and construct
validated identity/provenance bridges while preserving every original row and
raw field. Stop before analysis-facing promotion, ingestion, codification,
wage-gap calculation, regression, or causal analysis.

## Immutable source package

Use only the five final provisional ledgers as observation-bearing inputs:

1. `ledgers/quantitative/final_provisional_quantitative_ledger.csv`
2. `ledgers/qualitative/final_provisional_qualitative_mechanism_ledger.csv`
3. `ledgers/mixed/final_provisional_mixed_join_ledger.csv`
4. `ledgers/non_base_wage/final_provisional_non_base_wage_ledger.csv`
5. `ledgers/reference_and_exclusion/final_provisional_reference_exclusion_ledger.csv`

Package root:

`docs/analysis/compensation_extraction/COMPENSATION-EVIDENCE-FINAL-PROVISIONAL-MERGE-2026-07-25/`

Use package manifests, hashes, case index, conflict register, and the schema
readiness review as non-observation control inputs. Durable local ledgers may
be read only to build identity/provenance bridges. Do not mutate any source.

## Required preflight

1. Require a clean tracked worktree and the package commit or descendant.
2. Reverify all five package SHA-256 values.
3. Hash every durable bridge input before work.
4. Run a no-write dry run.
5. Prove that output paths are new, provisional, rollback-safe, and outside
   `data/`, `corpus/`, ingestion, codified, and analysis dataset paths.
6. Stop if a bridge is one-to-many, an identity is missing, an input hash
   changes, or a transformation would require guessing.

## Required repairs

### Unique non-base lineage columns

- Parse the non-base CSV by column position, not `DictReader` name collision.
- Rename the first and second copies of
  `source_quantitative_observation_id` and `source_mixed_join_key` with
  explicit layer-qualified names.
- Assert both copies agree on every row before deriving a canonical lineage
  field. Current expected populated counts are 134 and 85; expected value
  disagreements are zero.
- Preserve both source columns and their ordinal positions in a schema map.

### Identity, cycle, matching, and provenance bridge

- Add the raw retained content hash only through a deterministic one-to-one
  local join using existing source-review/text-table IDs.
- Add controlled `occupation_class`, city × unit × negotiation-cycle key, and
  matched-set ID only when supported by durable structured metadata.
- Add contract/cycle dates and required provenance fields: source type,
  source corpus, source cite, retrieval date/method, and artifact pointer.
- Quarantine rows whose identifiers cannot be established without inference.
- Preserve original document/case/source/detection/candidate IDs.

### Quantitative raw-versus-normalized contract

- Never overwrite the raw rate/salary/hourly/annual/percentage/date/unit fields.
- Add normalized scalar/range minimum/range maximum, currency, frequency,
  wage concept, annualization status, effective-date parse status, and a
  bounded transformation reason code.
- Do not coerce ranges, current/new pairs, prose formulas, multipliers, hours,
  or percentages into scalar wage amounts.
- Quarantine the 168 rows with neither an amount nor percentage and every
  ambiguous `other` compensation row unless a deterministic concept exists.
- Exclude the five member observations in the two unresolved conflict groups
  from analysis views while preserving them in the provisional and exception
  tables.

### Current active and QA semantics

- Preserve every provisional, targeted-QA, and readable-conflict-QA flag.
- Derive one documented `current_active` field exactly from
  `active_in_readable_conflict_qa_lane`.
- Derive `current_qa_status` by an explicit precedence table; do not erase
  historical statuses.
- Keep inactive duplicates/reroutes and all 14 duplicate-provenance rows in a
  provenance table.

### Mixed membership

- Keep all raw mixed keys.
- Validate the 371 active mixed rows and their member IDs again.
- Derive `mixed_membership_status` values such as `active`,
  `historical_inactive`, `historical_missing`, and `none`.
- Expected historical cases: 50 qualitative rows referencing 16 inactive
  mixed rows, plus 20 qualitative rows referencing five absent historical
  mixed keys.
- Never treat a historical key as an active join.

### Qualitative evidence

- Preserve mechanism fields and bounded pointers.
- Do not promote mechanism fields as final coded measurements without an
  explicit literal/verbatim evidence-span and QA contract.
- If verbatim spans are not recoverable from existing bounded structured
  artifacts without new extraction, report that blocker and stop; do not call
  a model or open PDFs under this schema-repair task.

### Non-base and reference lanes

- Keep non-base wage as a companion dataset, never a base-wage outcome input.
- Preserve `other` rows with reason codes; deterministically subtype or exclude
  them from typed analyses.
- Keep reference/exclusion as a control dataset only.

## Outputs

Write a new provisional schema-repair directory containing:

- schema contracts and column maps;
- losslessly repaired five-lane shadow files;
- identity/provenance/matched-set bridge audit;
- quantitative parse-status report and exception ledger;
- mixed membership status audit;
- unresolved-conflict quarantine ledger;
- non-base `other` disposition report;
- dry-run, validation, and decision reports; and
- a new analysis-readiness review prompt only if all repair gates pass.

Do not create an analysis-facing dataset. Analysis readiness must remain false
until a separate review explicitly authorizes promotion.

## Hard boundaries

No URLs, hosted search, downloads, OCR, extraction, document selection,
GABRIEL/API, scouts, source review, verification, ingestion, codification,
wage gaps, regressions, causal analysis, or remote inspection/configuration.
No source package or durable-ledger mutation. Do not fabricate identifiers,
dates, occupations, values, units, joins, or verbatim spans.

## Decision

Return one of:

- `schema_repairs_complete_repeat_analysis_readiness_review`
- `schema_repairs_partial_additional_bounded_evidence_needed`
- `schema_repairs_blocked_identity_or_provenance_failure`
- `schema_repairs_failed_integrity_issue`

Commit locally, update/push dashboard status only if it changes, and create a
lite relay excluding the repaired full ledgers, PDFs, images, full text/tables,
raw prompts/responses, secrets, build artifacts, and unrelated files.
