# Limited qualitative usage-layer validation

- Authorized review decision and 24 immutable material inputs: passed.
- Inherited five-package SHA-256 contract: passed.
- Candidate ID-set SHA-256: `0365d38babf9d4000295a3326c8cfc77b92f8a7ad1f2f1117d0cb40f1613b91b`; authorized/materialized match passed.
- Exactly 643 unique rows materialized; restricted and navigation contamination are zero.
- Strict-primary, cycle, occupation, matching, and carried-lane counts reconcile.
- No analysis results were computed; global analysis readiness remains false.

## Executed validation

- Python compile for the materializer, its test suite, and dashboard builder: passed.
- New usage-layer hardening suite: 66/66 passed.
- Five required predecessor suites: 229/229 passed.
- Combined focused suites: 295/295 passed.
- Dashboard data build: passed.
- Dashboard production build: passed; Vite emitted its existing informational chunk-size warning only.
- Repository schema validation: passed; 64 contracts, zero discourse rows, 64 coverage rows, and three city-attribute rows.
- Ingestion pipeline tests: 60/60 passed.
- Coverage audit: passed; 28 healthy matched pairs, two exploratory adjacent matches, and six pre-existing unmatched safety units reported.
- `git diff --check`: passed.
- Idempotent `--resume`: passed with zero writes and unchanged required-output hashes.
- Partial-output completion validation: passed fail-closed.

No PDF/page access, network/URL/download access, OCR, model/GABRIEL call, extraction, selection, ingestion run, codification, wage-gap calculation, regression, or causal work occurred.
