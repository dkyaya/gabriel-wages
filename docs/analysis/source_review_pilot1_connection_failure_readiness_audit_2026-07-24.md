# Source-Review Pilot 1 Connection-Failure Diagnosis Readiness Audit

Date: 2026-07-24

## Result

**PASS.** A bounded client diagnosis and one diagnostic probe of at most ten
locked pilot rows may proceed. Scaling and a durable source-review merge
remain blocked.

Work began at local commit
`d97f5e423d48b4a3fef4f1ba4d21d9e2de1a1470`. The tracked worktree was
clean. The unrelated untracked root `package-lock.json` was present before
work and was left untouched. Local ancestry includes `d97f5e4`, `a0c2445`,
`b94aad9`, `79df80c`, and `e028432`.

## Reproduced live result

The preserved Pilot 1 lane ledgers contain:

- 150 terminal rows;
- 150 unique source-review IDs;
- 150 unique candidate-queue row IDs;
- `download_connection_error`: 149;
- `download_forbidden`: 1;
- retained content artifacts: 0; and
- content hashes: 0.

The same counts appear in the access and download fields: 149 connection
errors and one forbidden response. The failures span the locked pilot's 94
source hosts. Row elapsed times range from 0.148 to 6.918 seconds, with a
0.864-second median. No durable `docs/analysis/source_review_ledgers/` output
exists.

## Why scaling is blocked

The lanes are structurally complete and therefore auditable, but the content
yield is zero. Terminal accounting is not a substitute for a retained source
body, hash, or content-supported rating. A 500-, 750-, or 1,000-row run would
only amplify an unresolved transport failure.

## Why the client path is the leading hypothesis

All 150 inputs were selected from rows previously classified
`reachable_pdf_or_document` by the bounded URL verifier. The source-review
inputs use nonblank absolute HTTPS locators, and `source_locator` equals the
previously recorded `final_url` for all 150 rows. A genuine simultaneous
failure across 149 rows and 94 hosts is less plausible than a systematic
transport/configuration difference. The source-review runner also collapses
the underlying transport exception into a generic connection category, which
prevents the preserved attempt from distinguishing DNS, socket, protocol, or
other connection causes.

This is a diagnosis hypothesis, not yet a proven root cause. The HTTP-client
comparison, mocked regression tests, offline dry run, and one bounded
ten-row probe are required before drawing a firmer conclusion.

## Diagnostic scope and boundary

The authorized scope is:

1. compare the source-review HTTP path with the earlier successful verifier;
2. patch a demonstrated or strongly indicated client/configuration mismatch;
3. test all transport behavior with mocks;
4. create a diverse ten-row input drawn only from the locked 150-row pilot;
5. dry-run that input offline; and
6. if every gate passes, make one live attempt per selected row with
   concurrency two and the existing 30/8/20-second, five-redirect, 25 MiB,
   no-sample limits.

This task will not rerun the 150-row pilot, start an additional probe after
network activity, scale the batch, merge source-review outcomes, ingest,
codify, parse PDFs, run OCR, extract wages, calculate wage gaps, run
regressions, update scout accounting, mutate routing or metadata-triage
ledgers, or write to `corpus/`, `data/contracts.csv`, or
`data/city_coverage.csv`.
