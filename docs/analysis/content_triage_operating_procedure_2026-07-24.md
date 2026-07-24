# Content-Triage Operating Procedure

Date: 2026-07-24

## Purpose

Content triage follows URL routing and precedes source download, rating,
extraction, ingestion, codification, or analysis. Routing records response
availability and metadata. Triage asks which routed candidates deserve deeper
review and what the next controlled action should be.

## Batch and lane design

The first plan contains 1,000 rows split into two 500-row lanes. Each row
retains its candidate queue, routing, municipality/Census, disposition,
duplicate-group, and source-locator identities. Planning is deterministic;
lanes have no cross-lane triage or queue-ID overlap.

The default profile selects:

1. scheduled high-priority candidates;
2. direct reachable PDF/documents before HTML/other response types;
3. likely CBA, wage schedule, award, fact-finding, and settlement types;
4. official-looking owners/domains;
5. municipalities with inferred safety/non-safety candidate potential;
6. higher-yield states; and
7. stable candidate identity.

These are scheduling heuristics, not content findings.

## Metadata-first rule

Dry run validates identity/schema only and records `triage_planned`. A future
metadata review may use committed routing metadata, candidate title/type,
owner, municipality, unit label, response type, redirect, and size. It must
keep all relevance, officialness, match, source-type, wage, mechanism, and
extraction fields preliminary.

Opening or downloading source content requires a separately implemented,
bounded, and authorized path. Dry-run completion is not authorization.

## Duplicate behavior

Every candidate identity remains in the cumulative routing ledger. Exact-URL
groups receive a deterministic representative for first review; linked rows
are deferred by default and retain the group identity. Later triage can attach
the representative’s content-review outcome without silently deleting,
promoting, or merging the original candidate rows.

## Oversized and unreachable behavior

`too_large` rows use the separate oversized-source plan. Blocked, not-found,
SSL, timeout, connection, and generic-error rows remain routing exceptions for
later targeted/manual disposition. They are not source-absence findings and do
not enter the ordinary reachable-source triage lanes.

## Later content-review outputs

A future implementation should produce lane-local:

- checkpointed content-triage ledger;
- row timing and terminal status;
- bounded metadata/content artifact inventory;
- manual-review queue;
- duplicate canonicalization note;
- source-quality and extraction-readiness routing; and
- a lane audit suitable for a separately authorized serial merge.

Do not download full documents until authorization defines size, storage,
provenance, checksum, legal-source, and failure controls.

## Downstream handoff

Only content-triaged, relevant, correctly matched, quality-rated, and
extraction-ready sources should enter a download/extraction plan. Approved
documents then move through the project ingestion layer with full provenance,
the two-corpus rule, verbatim-span safeguards, and coverage discipline.

Triage is not ingestion or wage extraction. Preliminary wage/mechanism signals
are routing instructions only. No wage-gap or causal claim follows from them.
