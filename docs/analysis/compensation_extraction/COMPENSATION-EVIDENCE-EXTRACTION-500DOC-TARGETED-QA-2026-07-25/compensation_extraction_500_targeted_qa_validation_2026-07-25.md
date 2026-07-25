# Targeted QA structural validation — 2026-07-25

- Required review rows processed: `pass` (187)
- Corrected shadow ledgers written separately: `pass`
- Original input hashes recorded: `pass`
- Duplicate observation IDs: `pass` (0)
- Invalid bounded page pointers: `pass` (0)
- Unresolved conflict rate at most 2%: `pass` (1.5217%)
- Unresolved base/non-base contamination: `pass` (0)
- Matched unit representation: `pass`
- GABRIEL/API used: `false`
- Full text/table/raw prompts/raw responses saved: `false`

## Repository-wide command validation

- Python compilation: `pass` for the Gate 1–3 runner, extraction runner and
  tests, targeted-QA runner and tests, and dashboard builder.
- Gate 1 automated adjudication regression tests: `14 passed`.
- Gate 2 refinement regression tests: `10 passed`.
- Gate 3 compensation regression tests: `9 passed`.
- Provisional 500-document extraction tests: `10 passed`.
- Targeted-QA tests: `8 passed`, including an end-to-end temporary-output run
  and immutable-input hash comparison.
- Dashboard data build: `pass`.
- Dashboard Vite production build: `pass` (the existing chunk-size advisory is
  non-fatal).
- Repository schema validation: `pass` (64 contracts, zero discourse rows, 64
  coverage rows, three city-attribute rows).
- Ingestion regression tests: `60 passed, 0 failed`.
- Coverage audit: `pass`; 64 contracts, 19 cities, 28 healthy pairs (10 exact,
  18 overlap), two exploratory adjacent pairs, and six unmatched safety units.
- `git diff --check`: `pass`.

Input SHA-256 values embedded in the targeted-QA summary match the unchanged
original 500-document selection, packet, decision, and five lane ledgers.
Protected corpus/data inputs and durable discovery/review/readiness/detection
authorities were not edited.
