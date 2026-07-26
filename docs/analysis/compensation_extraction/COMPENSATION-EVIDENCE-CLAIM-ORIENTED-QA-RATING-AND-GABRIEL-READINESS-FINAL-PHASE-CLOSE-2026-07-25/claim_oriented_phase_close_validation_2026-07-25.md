# Claim-oriented phase-close validation

- Prior final categorization: verified and immutable.
- Package and accepted registry chains: verified through predecessor contracts.
- Considered records: 8,939; exactly one primary category each.
- Claim-ready aggregate: 1,505.
- Quantitative direct-text candidates with explicit values: 862/862.
- Exact-span qualitative mechanism records: 643/643.
- GABRIEL claim-rating contamination: zero.
- Attribute taxonomy: stable v1 with 13 attributes.
- Global analysis readiness: false.

## Executed validation

- Claim-oriented focused suite: 69/69 passed.
- Six required predecessor suites: 382/382 passed.
- Immediate prior final-categorization suite: 75/75 passed.
- Combined focused suites: 526/526 passed.
- Dashboard data build: passed.
- Dashboard production build: passed with the existing non-fatal Vite chunk-size warning.
- Repository schema validation: passed (`contracts=64`, `discourse=0`, `coverage=64`, `city_attributes=3`).
- Ingestion tests: 60/60 passed; tests only, no ingestion run.
- Coverage audit: passed; 28 healthy pairs (10 exact, 18 overlap), two adjacent, six unmatched.
- `git diff --check`: passed.
- Idempotent `--resume`: passed with zero writes and unchanged required-output hashes.
- Partial-output completion validation: passed fail-closed.

## Issues found and fixed

1. Taxonomy payloads initially shared nested objects with the module-level v1 codebook, so an adversarial test mutation could affect later validation. Payload construction now deep-copies the immutable definitions, with regression coverage.
2. The GABRIEL-ready validator initially checked category and exact-span support but not the original source lane. It now requires `source_lane=qualitative_exact`, with regression coverage.
3. Predecessor dashboard validators correctly rejected the new descendant phase. Their allowlists now include only the exact claim-oriented phase and overall status; all readiness, contamination, and no-analysis checks remain unchanged.
