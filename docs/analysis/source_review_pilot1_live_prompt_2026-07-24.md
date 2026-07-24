# Future Coordinator Prompt — Source-Review Pilot 1 Live

Use only after separate explicit authorization to open and download the locked
pilot sources and after a bounded content-review implementation has been
reviewed. This prompt does not authorize ingestion, codification, wage
extraction, wage-gap analysis, causal claims, or merge.

Work only in the main coordinator repository. Do not inspect remotes or push.

## Locked pilot

Pilot: `SOURCE-REVIEW-PILOT1-150-2026-07-24`

Read the manifest, combined input audit, both lane inputs and audits, and
operating handoff under:

`docs/analysis/source_review_pilots/SOURCE-REVIEW-PILOT1-150-2026-07-24/`

Require:

- lane 1: 75 rows,
  `0253cba7ecf358e16679f64273466c239e296caf214e44a110813eeebfec6de3`;
- lane 2: 75 rows,
  `a5baa87593057a49c0b1e9adfff40051725ede45618c6f0d58f90f40b2630b6e`;
- 150 unique source-review IDs and candidate-queue IDs;
- no cross-lane identity overlap; and
- p1, scheduled, CBA-candidate, reachable-PDF metadata preserved.

Run fresh dry runs first and require 75/75 planned rows per lane with zero URL
opens, downloads, parses, OCR runs, and content artifacts.

## Live implementation and controls

Proceed only if the source-review runner has a separately reviewed live mode.
Use conservative concurrency and bounded total/connect/read timeouts, at most
five redirects, a documented per-response byte cap, and content samples off by
default. Refuse existing live directories. Store downloaded artifacts,
response metadata, hashes, timing, logs, and checkpointed terminal ledgers
inside lane-local output directories.

Do not increase concurrency mid-run. Preserve a healthy lane if its sibling
fails. Do not retry into a new directory without a separately audited resume
plan. Never write reviewed source files to `corpus/` or rows to
`data/contracts.csv`.

Ratings must be supported by observed content and remain unknown when evidence
is insufficient. Wage-table and mechanism fields are routing signals only.

## Audit and stop

After both lanes terminate, run `scripts/audit_source_review_lanes.py`. Review
input hashes, identities, terminal statuses, content hashes, artifacts,
officialness/relevance/match ratings, document types, extraction-readiness
ratings, download/parse failures, and merge recommendation.

Create live result and validation documents, one local commit, and a relay.
Stop before durable source-review merge regardless of recommendation. Do not
ingest, codify, extract wages, calculate wage gaps, make causal claims, or run
regressions.
