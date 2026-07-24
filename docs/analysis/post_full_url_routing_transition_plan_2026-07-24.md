# Post-Full-URL-Routing Transition Plan

Date: 2026-07-24

## Transition decision

The current candidate queue now has durable terminal URL-routing outcomes for
all 4,726 URL-bearing identities. No additional broad live URL-verification
round is needed for this queue.

The project should not respond to routing completion by opening the same URLs
again. The next phase is content triage and extraction-readiness planning.
Routing availability is an operational prerequisite, not proof that a source
is relevant, correctly matched, extractable, or usable for analysis.

## Next-phase sequence

1. **Content triage of reachable/reused sources.** Review document metadata
   and bounded content under a new authorization, preserving the routing
   ledger as immutable provenance.
2. **Source relevance classification.** Determine whether each source is a
   CBA, award, fact-finding record, wage schedule, settlement, context page,
   or unrelated source.
3. **Employer/unit match validation.** Confirm municipality, employer,
   bargaining unit, safety/non-safety role, and 2014–2024 period.
4. **Source-quality rating.** Record officialness, completeness, document
   authority, duplication, legibility, and provenance quality.
5. **Extraction-readiness scoring.** Assess whether wage schedules, effective
   dates, unit identity, and matched-cycle information can be extracted
   reliably.
6. **Prioritized download/extraction plan.** Authorize only high-value
   documents with explicit size, storage, provenance, and retry controls.
7. **Ingestion planning.** Route approved sources through the project’s
   provenance-gated ingestion layer without bypassing quarantine or the
   two-corpus rule.
8. **Later wage extraction and descriptive analysis.** Extract wage values
   only after employer/unit/cycle validation, then build matched
   safety/non-safety comparisons before any descriptive wage-growth-gap
   calculation.

Codification and regressions remain deferred.

## First content-triage batch

Prepare an offline, deterministic batch of **500–1,000 reachable/reused
sources**. Prioritize:

- `official_municipal`-likely PDFs/documents and other public repositories;
- high-priority scheduled candidates before lower-disposition rows;
- likely CBAs, arbitration awards, fact-finding reports, wage schedules, and
  settlement documents;
- large municipalities and high-yield states;
- sources likely to support matched safety/non-safety units in the same city
  and cycle; and
- source-type and state diversity sufficient to test the triage schema.

The batch must retain `candidate_queue_row_id`, `verification_id`, original
candidate disposition, routing status, final URL, content type, artifact
reference, and Round 1/Round 2 lineage.

Do not treat `reachable_pdf_or_document`, `reachable_html`, or
`duplicate_of_verified_source` as automatic promotion. Content, employer,
unit, cycle, and provenance checks remain required.

## Oversized-source strategy

The cumulative ledger contains **261 `too_large` rows**: 64 from Round 1 and
197 from Round 2. Do not raise the 10 MiB ceiling globally or rerun them inside
ordinary routing.

Design a later oversized-source pass with:

- a separately authorized allowlist;
- expected size from headers when available;
- explicit per-file and batch storage ceilings;
- resumable streaming and checksums;
- content-type and archive-safety controls;
- a quarantine path for malformed or unexpectedly large responses; and
- extraction tooling selected only after the document type is known.

Oversized routing is a handling problem, not proof that the source is
unusable.

## Completion boundary

Full routing completion means every current URL-bearing candidate has a
terminal availability/response-metadata outcome. It does not mean:

- 4,726 relevant sources;
- 4,726 official documents;
- complete police/fire and non-safety matching;
- ingested contracts;
- extracted wage values;
- codified mechanisms;
- an analysis-ready panel; or
- evidence of a wage gap or causal mechanism.

The next authorized task should prepare the content-triage and
extraction-readiness framework and its first 500–1,000-row batch. It should
not run another broad URL-routing round.
