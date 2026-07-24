# Source-Review Pilot 1 Live Readiness Audit

Date: 2026-07-24

## Result

**PASS.** The locked source-review pilot is ready for the explicitly
authorized bounded live collection, subject to a fresh 150-row dry gate.

Work began at local commit
`a0c2445f577f8256849f65f73b0a4492ad6fda7c`. The tracked worktree was
clean. The unrelated untracked root `package-lock.json` was left untouched.
Local ancestry includes `a0c2445`, `b94aad9`, `79df80c`, `0097d30`,
`4a49f93`, `eccbd0d`, `5c9c524`, `e028432`, `e86abf7`, and `2bab4b0`.

## Locked inputs

Pilot: `SOURCE-REVIEW-PILOT1-150-2026-07-24`

- selected rows: 150;
- lane count: 2;
- lane rows: 75 / 75;
- unique source-review IDs: 150;
- unique candidate-queue IDs: 150;
- cross-lane identity overlap: 0.

Recomputed SHA-256 hashes match the manifest:

- lane 1:
  `0253cba7ecf358e16679f64273466c239e296caf214e44a110813eeebfec6de3`;
- lane 2:
  `a5baa87593057a49c0b1e9adfff40051725ede45618c6f0d58f90f40b2630b6e`.

All selected rows retain the locked metadata mix: scheduled original
disposition, p1 metadata priority, CBA candidate type,
`reachable_pdf_or_document` routing status, and routed
`application/pdf` type. Those fields are planning metadata, not final source
findings.

The previous bounded-path dry audit reports two `dry_run_passed` lanes,
150/150 terminal-planned rows, zero source access, and
`dry_run_complete_no_live_source_review`.

At readiness:

- `lane_1_live_attempt1` did not exist;
- `lane_2_live_attempt1` did not exist;
- no durable `docs/analysis/source_review_ledgers/` layer existed; and
- no source-review merge had occurred.

## Authorized live settings

This task is authorized to open only the 150 locked source locators above,
using exactly:

- review mode: `source_rating_live`;
- download mode: `bounded`;
- explicit `--allow-live-content-access`;
- two lanes, never a third;
- concurrency: 4 per lane;
- total/connect/read timeouts: 30 / 8 / 20 seconds;
- maximum redirects: 5;
- maximum retained response: 26,214,400 bytes;
- content samples: disabled;
- PDF parsing and OCR: disabled; and
- lane-local artifacts only.

## Boundaries

The live collection may produce preliminary access, artifact, provenance, and
technical-readiness metadata. It does not authorize a durable source-review
merge, source ingestion, `gabriel.codify`, wage-table or wage-value
extraction, wage-gap calculation or claim, causal claim, regression, scout
work, scout-accounting changes, routing-ledger changes, metadata-triage-ledger
changes, or writes to `corpus/`, `data/contracts.csv`, or
`data/city_coverage.csv`.
