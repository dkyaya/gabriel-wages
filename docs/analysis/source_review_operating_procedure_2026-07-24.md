# Source-Review Operating Procedure

Date: 2026-07-24

## Stage boundary

Metadata triage schedules review from already committed candidate and routing
fields. Source review is the later content-bearing stage that confirms
provenance, relevance, municipality/employer/unit identity, document type,
period, technical extraction conditions, and duplicate/canonical decisions.

Neither stage is ingestion, codification, wage extraction, or analysis.

## Pilot design

`SOURCE-REVIEW-PILOT1-150-2026-07-24` contains 150 p1,
download-allowed-later candidates in two 75-row lanes. The pilot is broad
enough to test 43 state environments and safety/non-safety unit labels while
remaining small enough for detailed artifact and rating audits.

The committed pilot inputs are immutable review assignments. A future run must
recompute their SHA-256 hashes, run dry runs first, use fresh lane-local output
directories, and stop before any durable merge.

## Bounded content-review principles

A future live run requires separate authorization. The implemented path:

1. defaults to four workers per lane, 30-second total, eight-second connect,
   and 20-second read limits, at most five redirects, and 25 MiB per response;
2. fetch only the locked source locator for each pilot identity;
3. checkpoint every terminal row incrementally;
4. hash exact downloaded bytes and record observed type and size;
5. keep retained artifacts and logs inside their lane directory;
6. parse only formats explicitly supported by the reviewed implementation;
7. avoid OCR unless separately authorized;
8. sanitize error messages and never persist credentials or auth headers; and
9. leave candidate, routing, metadata-triage, contract, and corpus layers
   unchanged.

The runner additionally disables environment proxy inheritance, requires the
explicit combination of `source_rating_live`, bounded download mode, and
`--allow-live-content-access`, and refuses a nonempty output directory unless
an explicit same-directory resume also requests completed-ID skipping.
Content samples are off by default. No document enters `corpus/` or
`data/contracts.csv` during source review.

The implementation does not parse PDFs. Page count and text-layer status
remain unknown, and OCR is unsupported. This keeps the initial path bounded
to access, retention, hashing, and preliminary artifact metadata.

## Rating discipline

Final officialness, relevance, municipality, employer, unit, document-type,
and extraction-readiness fields require inspectable content or provenance.
When content is missing or ambiguous, use `unknown`, `possible`, or a manual
review status. Do not backfill confident ratings from candidate titles or URL
domains alone.

A wage-table or mechanism-language signal records only whether deeper
extraction may be worthwhile. It is not a wage value, wage-growth estimate,
wage-gap finding, or causal conclusion.

## Duplicate and oversized handling

The first pilot excludes multi-row duplicate groups and all oversized routing
outcomes. Later duplicate review should identify a canonical artifact using
content hash and provenance while preserving every candidate identity.
Oversized sources require a separate lane with lower concurrency, explicit
streaming/byte rules, and possibly manual review; the standard cap should not
be raised globally.

## Artifact and merge handling

Each live lane should produce:

- `source_review_ledger.csv`;
- `source_review_summary.json`;
- `source_review_timing.csv`;
- lane-local content/response metadata artifacts;
- console and exit records; and
- an artifact-integrity inventory.

The auditor must verify hashes, expected identity coverage, terminal statuses,
download/parse counters, artifact paths, content hashes, and rating
vocabularies. Live collection stops before merge. A separate serial task may
merge exactly once only if all lanes are `completed_merge_eligible`.

## Scale decision after the pilot

Recommend a 500-row next batch only when the 150-row pilot has complete
terminal outcomes, clean lane-local artifacts and hashes, acceptable
transport/manual-review burden, and useful preliminary rating signals. If
runtime is exceptionally fast and those quality gates are strong, 750 or
1,000 rows may be considered. Speed alone is insufficient. Artifact volume,
error rates, rating usefulness, and reviewer burden control the decision.
OCR, heavy PDF parsing, and manual interpretation use smaller lanes.

## Downstream flow

Audited source review feeds:

1. content-based source-quality ratings;
2. extraction-readiness routing;
3. an explicit extraction plan by text-layer/table/OCR/manual mode;
4. ingestion planning with required provenance;
5. later verbatim extraction and codification; and
6. still-later descriptive wage analysis after matched comparison gates.

Regressions remain deferred. Source review alone never authorizes wage-gap or
causal claims.
