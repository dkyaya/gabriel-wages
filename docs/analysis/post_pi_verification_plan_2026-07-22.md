# Post-PI verification plan — 2026-07-22

## Objective

Convert a bounded subset of unverified scout leads into a transparent, reviewable source ledger. Verification is the next gate because candidate discovery alone does not establish official provenance, exact employer/unit identity, document completeness, operative dates, wage extractability, or same-city bargaining-cycle comparability.

This phase should answer a practical question before more large-scale collection: what share of high-priority candidate leads can become verified, matched, ingestion-ready municipal wage-setting sources?

## Proposed first batch

Verify 50–100 candidate rows. This is large enough to observe recurring source and false-positive patterns while remaining small enough for careful manual review and protocol revision.

Use a stratified sample rather than simply taking the first queue rows:

- **High-yield states:** include records from Washington, Massachusetts, Pennsylvania, Florida, California, Illinois, and New York, with sample confidence recorded.
- **Geographic diversity:** include several medium- or low-sample states so the protocol is not calibrated only to strong portal environments.
- **Employer scale:** include large municipalities likely to have formal labor agreements, compensation plans, and ordinary civilian wage schedules.
- **Matched-set potential:** prioritize municipalities with candidate labels suggesting both police/fire and ordinary non-safety units.
- **Document diversity:** include CBAs/MOUs, salary schedules, compensation plans, ordinances, budget/HR pages, and union-hosted documents so verification rules cover the main queue types.
- **Triage diversity:** focus on high-priority later-verification rows but include a limited sample of medium-priority and likely-duplicate/context-only rows to measure triage precision.

Failure-only municipalities should remain outside this pilot because they have no candidate row to verify. Their 20-row retry lane is a separate future operation.

## Verification procedure

For every selected candidate row:

1. Lock the queue ID, municipality ID, source URL, and scout metadata before review.
2. Confirm the source resolves and record access date/status without silently replacing the URL.
3. Confirm exact municipal employer; reject county, school, authority, district, university, or private-provider substitutions.
4. Confirm bargaining unit or employee group and tag it as police, fire, general/civilian, or another controlled class.
5. Classify source type: CBA/MOU, arbitration/fact-finding record, salary schedule/compensation plan, ordinance, budget, HR page, or context-only material.
6. Record source ownership and provenance: official municipal, official state repository, union, or another documented owner.
7. Record document dates, execution/completeness signals, and the apparent bargaining-cycle window.
8. Check duplicate and superseded-version status against other selected and canonical sources.
9. Assess whether wage fields appear extractable without extracting or coding them in this phase.
10. Assess whether a plausible safety/non-safety same-city cycle match exists; do not infer a match from unit labels alone.
11. Assign verification disposition and ingestion-readiness status with a short evidence note.

## Required outputs

### `verified_source_ledger`

One row per reviewed candidate, preserving queue identity and recording:

- verification status and review date;
- exact employer match;
- source owner/provenance;
- source type;
- document completeness and operative dates;
- access status;
- duplicate/superseded status;
- reviewer note and reason for rejection/hold where applicable.

### Source and unit classification

Use explicit tags for:

- police;
- fire;
- general/civilian;
- salary schedule/compensation plan;
- CBA/MOU;
- ordinance/budget/HR page;
- context-only/non-qualifying source.

### Research-readiness fields

- `wage_field_extractability_flag`: yes/no/unclear, with reason;
- `matched_cycle_potential`: yes/no/unclear, with counterpart queue/source ID when known;
- `ingestion_readiness_flag`: ready/hold/reject;
- `ingestion_blocker`: missing full document, wrong employer/unit, incomplete dates, duplicate, access problem, or other documented reason.

## Batch evaluation

At the end of the pilot, report:

- verified-source conversion rate;
- exact-employer and exact-unit pass rates;
- document-type composition;
- duplicate/context-only/rejection rates;
- safety, non-safety, and potential matched-set counts;
- wage-extractability and ingestion-readiness rates;
- differences by state, source owner, priority score, and triage bucket, with sample-size cautions;
- changes needed to the scout prompt, query hints, priority system, or queue triage before expansion.

## Decision after the pilot

If high-priority leads convert reliably and produce plausible matched safety/non-safety groups, expand verification in coordinated waves and prepare only verified, complete sources for ingestion. If conversion is low or matching is weak, revise the discovery/triage rules before adding many more scout rows. Continue ordinary Tier 1 scouting only at the breadth/verification balance approved by the PI.

## Out of scope

This verification phase does not include wage extraction, contract ingestion, GABRIEL codification, mechanism classification, regression modeling, wage-gap estimates, causal analysis, or final claims. Those require later, separately validated stages.
