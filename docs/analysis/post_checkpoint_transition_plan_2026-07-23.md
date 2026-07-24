# Post-Checkpoint Transition Plan

Date: 2026-07-23/24  
Status: source-discovery scale-up checkpoint reached and exceeded

## Decision

Official scout coverage is now 2,436 municipalities against the approximately
2,000-municipality workflow checkpoint. Broad ordinary scouting should stop.
Do not run another discovery wave, aggressive lane, or failure-retry lane
unless the user or PI explicitly authorizes it after reviewing downstream
conversion and matching results.

The 4,726 queued rows are unverified source leads. Scout coverage is not
verified-source coverage, and the checkpoint does not establish a wage or
mechanism result.

## Next-phase sequence

1. **Candidate source verification.** Confirm exact municipal employer,
   bargaining unit, safety/non-safety occupation, official provenance,
   document type, operative dates, access, completeness, and duplicate status.
   A municipality qualifies for collection only when a safety source and an
   overlapping non-safety comparator are both obtainable.
2. **Wage-data extraction.** Capture comparable wage concepts, schedules,
   start/end dates, and bargaining-cycle identifiers from verified documents.
   Preserve exact text and table provenance; do not paraphrase mechanism spans.
3. **Structured ingestion.** Use the provenance-gated ingestion pipeline and
   keep one row per bargaining unit, contract cycle, and municipality. Keep
   causal contracts separate from discourse materials.
4. **Source quality and extractability rating.** Record document completeness,
   text quality, wage-table usability, employer/unit certainty, and
   safety/non-safety match readiness.
5. **Descriptive wage-growth-gap calculation.** Only for validated matched
   municipality/time windows, calculate safety wage growth minus matched
   non-safety wage growth using documented harmonization rules.
6. **Mechanism tagging and correlation documentation.** Retain verbatim
   mechanism spans, apply GABRIEL measures later, and document descriptive
   associations and counterexamples without causal attribution.
7. **Dashboard wage-growth-gap filtering.** Add the planned gap-percentage
   layer only when validated matched data exist. Show missing observations as
   unavailable, with source-quality and comparison filters.

Regressions remain deferred until verified conversion, extraction consistency,
matched-set coverage, measurement rules, and the descriptive data product are
stable.

## Proposed first verification batch

Prepare a bounded batch of **50–100 candidate rows**, with final size chosen
after a deterministic deduplication and match-potential audit. This planning
task should not open URLs until separately authorized.

Selection should balance:

- high-yield states from the refreshed yield report, while avoiding domination
  by one state;
- larger municipalities, where multiple bargaining units and public records
  are more likely to support matched comparison;
- municipalities with likely safety and non-safety unit combinations in the
  queue;
- source-owner and document-type diversity, including city portals, union
  sources, state labor-board materials, CBAs, awards, and wage schedules;
- document-year coverage in the 2014–2024 window;
- high and medium verification-priority rows, with a small diagnostic sample
  of lower-yield or underrepresented strata; and
- exclusion of context-only, likely-duplicate, insufficient, already-canonical,
  and failure-only rows unless a row has a documented verification reason.

Prioritize municipality-level matched sets rather than isolated safety
documents. A safety agreement without an overlapping non-safety comparison is
dead weight for the core design and should be flagged before collection.

## First-cycle deliverables

The first downstream cycle should report:

- lead-to-verified-source conversion;
- wage-data extractability;
- safety/non-safety match rate;
- usable descriptive gap availability;
- source-quality and document-type differences;
- common verification failure reasons; and
- recommended changes to the next verification or targeted gap-filling batch.

Those operational results—not the raw number of scout leads—should determine
whether any later discovery is needed.
