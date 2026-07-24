# Future Coordinator Prompt — Source-Review Pilot 1 Serial Merge

Use only after both separately authorized live source-review lanes have
completed and their relay has been reviewed.

Work only in the main coordinator repository. Do not open URLs, download
sources, inspect remotes, or push.

## Merge gates

Pilot: `SOURCE-REVIEW-PILOT1-150-2026-07-24`

Recompute lane input hashes and rerun `scripts/audit_source_review_lanes.py`.
Require both lanes to be `completed_merge_eligible`, all 150 selected
identities to have one terminal source-review outcome, zero duplicate
source-review or candidate-queue IDs, valid artifact paths and hashes where
content was retained, and a recommendation to merge all source-review lanes.

Confirm candidate, routing, metadata-triage, contract, coverage, and corpus
inputs are unchanged. Stop if any gate fails.

## Merge exactly once

Use or create a fail-closed serial merge script that:

- preserves all source-review identities and content-supported ratings;
- records source pilot, lane, merge ID, and merge timestamp;
- writes a pilot-specific durable ledger, summary, and merge audit;
- updates cumulative/latest source-review pointers without losing prior
  rounds; and
- refreshes dashboard source-review status from the merged summary.

The merge must not open URLs, download or parse documents, run OCR, ingest
sources, run `gabriel.codify`, extract wages, calculate wage gaps, make causal
claims, or run regressions.

Validate, create one local commit, create a complete relay, and do not push.
