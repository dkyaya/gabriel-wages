# Claim Viewer Integration Notes — 2026-07-12

This run does not implement viewer changes. These notes describe how a future viewer could make the evidence layer claim-centered.

## Claim Filters

- Add a `claim_id` filter alongside the existing state, city, occupation, and mechanism filters.
- Default view could show report-ready or maybe-report-ready claims first, with a toggle for `needs_more_evidence` claims.
- The filter source should be `docs/analysis/claim_evidence_matrix_2026-07-12.csv`, not hand-coded viewer logic.

## Adding `claim_id` to the Evidence Matrix

- Keep `evidence_id` as the durable key into `gabriel_codify_evidence_layer.csv`.
- Let one `evidence_id` map to multiple `claim_id` values because the same excerpt may support more than one bounded claim.
- Preserve `evidence_role` so primary support, counterevidence, limitations, and gap indicators remain visually distinct.

## RA / PI Review Flags

- Add optional review fields keyed by `claim_id` + `evidence_id`, such as `ra_review_status`, `pi_review_status`, `review_note`, and `needs_source_check`.
- Review flags should attach to evidence IDs rather than free-text excerpts so they survive viewer rebuilds.
- A future review table can live separately from the evidence layer to avoid contaminating codify output.

## Claim Pages and Excerpt Cards

- Each claim page should show: claim text, scope, status, reasoning, limitations, what would change our mind, and source needs.
- Supporting evidence cards should link back to the excerpt viewer’s existing row-level evidence IDs.
- Gap indicators should display as source-needed cards, not as evidence-present cards.

## Non-Implementation Boundary

No HTML, JavaScript, or viewer build scripts were changed in this run. The current deliverable is the claim register plus the claim-evidence matrix that a later viewer integration can consume.
