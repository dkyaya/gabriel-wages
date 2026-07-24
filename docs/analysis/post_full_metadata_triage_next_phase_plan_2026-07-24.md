# Post-Full-Metadata-Triage Next-Phase Plan

Date: 2026-07-24

## Current gate

Metadata-only content triage is durably merged for all 4,726 routed
URL-bearing candidate identities.

The preliminary scheduling distribution is:

- p1: 1,760;
- p2: 1,232;
- p3: 360;
- defer: 1,372; and
- exclude: 2.

This completes an offline planning layer, not source-content review. No source
has yet received a final relevance, employer/unit-match, source-quality, or
extraction-readiness determination.

## Recommended next substantive phase

1. **Define the source-rating schema and audit rules.** Establish explicit,
   content-supported fields for officialness, relevance, employer and
   municipality match, bargaining-unit match, document type, period, text
   quality, wage-table signal, and extraction suitability. Keep ratings
   separate from the metadata-triage ledger.
2. **Prepare a bounded content-review/download pilot.** Select 100–200 p1
   rows, with deterministic identity locks, lane-local artifacts, conservative
   concurrency and byte limits, content-safety checks, and a stop-before-merge
   boundary.
3. **Run an independent oversized-source plan.** Keep the 261
   `oversized_needs_separate_pass` rows outside ordinary download limits.
   Prioritize official/high-value candidates and use streaming or
   metadata-first handling rather than raising the global cap.
4. **Score extraction readiness from actual content.** Only after authorized
   content review should the project decide whether a source can support
   bounded PDF/text extraction, OCR, manual review, or exclusion.
5. **Plan ingestion after content and source-rating gates.** Do not place a
   document in the contract/corpus layer until relevance, provenance,
   employer/unit, date/cycle, and matched-comparison requirements pass.

## Why the first pilot should be 100–200 rows

The 2,923 `content_review_download_allowed_later` rows are only metadata-based
recommendations. Downloading all of them immediately would scale content,
storage, document-size, format, duplicate, and manual-review risks before the
project has measured content-review precision or extraction yield.

A 100–200-row pilot is large enough to estimate:

- how often p1 metadata labels correspond to the intended source;
- employer, municipality, unit, and period match rates;
- document-type and source-quality distributions;
- PDF/text/OCR handling needs;
- duplicate and canonical-source behavior;
- artifact volume and reviewer burden; and
- the share plausibly suitable for later structured extraction.

The pilot should sample official-looking p1 documents across states,
municipality sizes, safety/non-safety unit types, and likely CBA, award,
fact-finding, settlement, and wage-schedule categories. It must use a separate
authorization because it would open and potentially download source content.

## Continuing boundaries

- No wage extraction should begin during source rating.
- No wage-gap calculation or claim should begin before structured extraction
  and ingestion gates pass.
- No causal claim should be inferred from content routing or ratings.
- Regressions remain deferred.
- Candidate, routing, metadata triage, content review, source rating,
  extraction readiness, ingestion, codification, and analysis-ready wage
  observations must remain distinct stages.
