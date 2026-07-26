# Limited qualitative usage-layer acceptance validation

- Immutable acceptance inputs verified: 32.
- Candidate ID-set SHA-256: `0365d38babf9d4000295a3326c8cfc77b92f8a7ad1f2f1117d0cb40f1613b91b`; passed.
- Layer SHA-256: `cf29690a7687401960804a714d0bdfb0a24407eee10ba70695ee5487a60fcbc5`; passed.
- Schema SHA-256: `3c31d1d663cde730d198184444c6b77591cc186411c9714ea0086f2135d8533a`; passed.
- Registered usage-layer scope: 643 rows; no evidence rows copied or created.
- Restricted/navigation/external-lane contamination: zero.
- Strict primary manifest: 56 rows and non-analytic.
- Analysis outputs created: zero. Global analysis readiness: false.

## Executed validation

- Python compilation for the acceptance runner, acceptance tests, and dashboard builder: passed.
- New acceptance/registration suite: 61/61 passed.
- Seven required predecessor suites: 360/360 passed.
- Combined focused result: 421/421 passed.
- Dashboard data build: passed.
- Dashboard production build: passed; Vite emitted only its existing informational chunk-size warning.
- Repository schema validation: passed; 64 contracts, zero discourse rows, 64 coverage rows, and three city-attribute rows.
- Ingestion pipeline tests: 60/60 passed. This was test execution only; no ingestion batch ran.
- Coverage audit: passed; 28 healthy matched pairs, two exploratory adjacent matches, and six pre-existing unmatched safety units reported.
- `git diff --check`: passed.
- Idempotent `--resume`: passed with zero writes and unchanged required-output hashes.
- Partial-output completion validation: passed fail-closed.

No URL/network/download access, PDF/page access, OCR, model/GABRIEL call, extraction, selection, ingestion run, codification, descriptive or inferential statistic, wage-gap calculation, regression, or causal work occurred. No evidence row or analysis output was created.
