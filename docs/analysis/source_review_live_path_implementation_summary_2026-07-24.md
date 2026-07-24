# Bounded Source-Review Live-Path Implementation Summary

Date: 2026-07-24

## Outcome

The locked 150-row pilot now has a fail-closed, bounded content-access path
ready for a later separately authorized run. No live source review was run in
this task.

`scripts/source_review_sources.py` now requires all of
`--review-mode source_rating_live`, `--download-mode bounded`, and
`--allow-live-content-access` before it can instantiate the real transport.
The future pilot defaults are concurrency four per lane, 30-second total,
eight-second connect, and 20-second read limits, five redirects, 25 MiB per
response, and content samples off.

The transport disables environment proxy inheritance, accepts HTTP(S) only,
uses bounded chunked reads, sanitizes recorded URLs/errors and filenames, and
supports incremental ledger/summary/timing checkpoints. Fresh live output is
mandatory. Resume is permitted only into the same output directory with
explicit completed-source-review-ID skipping.

## Artifact and rating boundaries

Retained content, when later authorized, is written only under each lane's
`candidate_artifacts/content/` directory. Every retained artifact receives a
SHA-256 hash and byte count; a small sanitized per-row response-metadata JSON
is written lane-locally. Content samples are disabled by default. Paths are
validated as lane-local, and protected project areas are refused.

No PDF parser is used. `pdf_page_count` and `text_layer_status` remain
`unknown`; OCR is unsupported and all parse/OCR counters remain zero.
Observed type, byte size, hash, and access outcome may support a preliminary
technical extraction-readiness value. Candidate type may be retained only as
`cba_candidate`. Relevance and municipality/employer/unit match remain
`possible` or `unknown`; wage-table, wage-growth, and mechanism-language
signals remain `unknown`.

The updated auditor requires exact lane identities and terminal coverage,
lane-local existing artifact paths, matching content hashes and sizes,
per-row metadata artifacts, zero parse/OCR and protected/downstream markers,
and no duplicate review or queue identities before returning
`completed_merge_eligible`.

## Mocked test coverage

Thirteen offline tests pass. They cover:

- missing live authorization and incompatible no-download gates;
- bounded mocked PDF retention and hashing;
- mocked HTML retention without parsing or extraction;
- byte-cap deferral without a full artifact;
- terminal timeout, 404, forbidden, and TLS-error outcomes;
- refusal to reuse a nonempty output without resume;
- filename/path-traversal resistance and rejection of non-lane artifact roots;
- deterministic planning and zero-network dry runs; and
- two complete mocked live lanes audited as `completed_merge_eligible` with
  clean artifacts.

Every live-path test injects a fake transport. Socket creation is blocked in
the network-sensitive tests; no candidate URL or external network endpoint is
used.

## Locked dry-run result

The unchanged inputs were rerun into:

- `tmp/source_review_pilots/SOURCE-REVIEW-PILOT1-150-2026-07-24/lane_1_dry_run_livepath_impl`;
- `tmp/source_review_pilots/SOURCE-REVIEW-PILOT1-150-2026-07-24/lane_2_dry_run_livepath_impl`.

Each contains 75 `planned_not_reviewed` rows. The audit reports 150/150
terminal-planned rows, two `dry_run_passed` lanes,
`dry_run_complete_no_live_source_review`, clean dry artifact integrity, and
zero URL, network, download, parse, PDF, OCR, content-artifact, or sample
counters.

## Scaling decision framework

A clean 150-row run can justify 500 next only if terminal completion,
artifact/hash integrity, runtime, transport/manual-review burden, and the
usefulness of preliminary ratings all pass. An exceptionally fast run may
support considering 750 or 1,000 only when the same quality gates remain
strong. Speed alone is not a scale gate. OCR, heavy parsing, and intensive
manual review require smaller lanes.

## Boundary confirmation

This implementation task opened no real URL, made no real network/API/model
or scout call, downloaded or parsed no real document, ran no OCR or live
source review, and changed no scout accounting, routing ledger,
metadata-triage ledger, contract, coverage, or corpus file. It performed no
source-rating merge, extraction, ingestion, codification, wage calculation,
wage-gap analysis, causal analysis, or regression.
