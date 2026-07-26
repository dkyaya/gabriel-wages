# Cumulative 1,000-document targeted QA validation — 2026-07-25

- Exact unresolved scope: `pass` (151)
- Base/non-base rows accounted for: `pass` (126)
- Conflict groups accounted for: `pass` (25)
- Corrected shadow ledgers separate from originals: `pass`
- Input SHA-256 values recorded: `pass`
- Duplicate observation IDs: `pass` (0)
- Invalid bounded page pointers: `pass` (0)
- Unresolved conflict rate at most 2%: `pass` (0.1647%)
- Unresolved base/non-base contamination: `pass` (0)
- Existing canonicalized duplicate observations preserved: `pass` (9)
- Matched representation: `pass`
- GABRIEL/API used: `false`
- Full text/table/raw prompt/raw response/image artifacts saved: `false`

Repository-wide command validation is appended in the task result and relay
after the required test/build/validation commands complete.

## Repository-wide validation

- Python compilation for extraction, prior targeted-QA, cumulative targeted-QA, dashboard builder, and focused tests: `pass`
- Cumulative 1,000-document extraction tests: `12 passed`
- Provisional 500-document extraction tests: `10 passed`
- Prior 500-document targeted-QA tests: `8 passed`
- Cumulative 1,000-document targeted-QA tests: `9 passed`
- Automated Gate 1 tests: `14 passed`
- Automated Gate 2 tests: `10 passed`
- Automated Gate 3 compensation tests: `9 passed`
- Total relevant offline/mock tests: `72 passed`
- Dashboard data build: `pass`
- Dashboard Vite production build: `pass` (existing chunk-size warning only)
- Repository schema validation: `pass` (`64` contracts, `0` discourse, `64` coverage rows, `3` city attributes)
- Ingestion pipeline tests: `60 passed / 0 failed`
- Coverage audit: `28` healthy pairs (`10` exact, `18` overlap), `2` adjacent, `6` unmatched safety units
- `git diff --check`: `pass`
- Recorded cumulative input hashes rechecked: `9 / 9 unchanged`
- Frozen selection SHA-256 preserved: `147e311e7a6d6c3aeb98c52357f6d46ea8ee52798be45493bf0a1c138a3b9f15`
- Secret-pattern scan of new task artifacts: `pass` (zero matches)
- Protected durable/original data paths changed: `false`
