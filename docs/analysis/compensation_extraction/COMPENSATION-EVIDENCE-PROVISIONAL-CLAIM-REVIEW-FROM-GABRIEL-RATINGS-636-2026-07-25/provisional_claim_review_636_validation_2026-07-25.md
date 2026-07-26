# Provisional claim review validation — 2026-07-25

- Required immutable summary-review inputs: 20/20 hash checks passed.
- Valid summary scope: 636 — passed.
- Explicit quarantine exclusions: 7 — passed.
- Positive attribute cells: 722 — passed.
- Claim registry: 35 unique claims; all five controlled claim types present — passed.
- Claim boundaries: 35/35 present — passed.
- Provisional causal candidates: 5/5 explicitly provisional — passed.
- Quantitative future lane: 862 acknowledged, 0 analyzed — passed.
- GABRIEL/API/model calls: none.
- PDF/page/OCR/URL/download/extraction/selection/ingestion/codify work: none.
- Wage-gap/regression/treatment-effect/final-causal work: none.
- Global analysis readiness: false.

## Command results

- New provisional-claim-review suite: **62/62 passed**.
- Five required predecessor suites: **309/309 passed**.
- Combined focused suites: **371/371 passed**.
- Adversarial stress registry: **46/46 passed fail-closed**.
- `python -m py_compile` for the dashboard builder, runner, and test suite: passed.
- Dashboard data build: passed.
- Dashboard production build: passed with the existing non-fatal Vite chunk-size warning only.
- Repository schema validation: passed (`contracts=64`, `discourse=0`, `coverage=64`, `city_attributes=3`).
- Ingestion tests: **60/60 passed**; no ingestion run occurred.
- Coverage audit: passed (`28` healthy matched pairs, `6` unmatched safety units reported, `2` exploratory adjacent matches).
- Idempotent `--resume`: passed with zero writes, zero model calls, and unchanged output hashes.
- `git diff --check`: passed.
