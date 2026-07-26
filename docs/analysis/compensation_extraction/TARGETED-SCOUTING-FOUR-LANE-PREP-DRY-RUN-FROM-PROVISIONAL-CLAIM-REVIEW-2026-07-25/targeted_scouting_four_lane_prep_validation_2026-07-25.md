# Targeted scouting four-lane prep validation — 2026-07-25

- Immutable inputs: 17/17 SHA-256 checks passed.
- Master queue: 2,000 high-quality targets; zero weak padding.
- Lane queues: 500/500/500/500; all within cap.
- Required queue fields: complete.
- Live status: 2,000/2,000 `not_started`.
- Duplicate and prior-seen avoidance: passed against three local consolidated ledgers.
- Lockfiles: 4/4; worker prompts: 4/4 plus coordinator merge prompt.
- Live hosted search/model/API calls: zero.
- URL/PDF/page/download/OCR access: zero.
- Verification/extraction/rating/selection/ingestion/codify runs: zero.
- Wage-gap/regression/treatment-effect/final-causal work: zero.
- Global analysis readiness: false.

## Command results

- New four-lane dry-prep suite: **77/77 passed**.
- Three required predecessor suites: **189/189 passed**.
- Combined focused suites: **266/266 passed**.
- Adversarial stress registry: **55/55 passed fail-closed**.
- Python compilation for the dashboard builder, dry-prep runner, and test suite: passed.
- Dashboard data build: passed.
- Dashboard production build: passed with the existing non-fatal Vite chunk-size warning only.
- Repository schema validation: passed (`contracts=64`, `discourse=0`, `coverage=64`, `city_attributes=3`).
- Ingestion tests: **60/60 passed**; tests only, no ingestion run.
- Coverage audit: passed (`28` healthy matched pairs, `6` unmatched safety units, `2` exploratory adjacent matches).
- Idempotent `--resume`: passed with zero writes, zero live runs, zero model calls, and unchanged output hashes.
- `git diff --check`: passed.

## In-scope defect fixed

The first fail-closed dry build exposed duplicate same-name municipality records tied to different government IDs in the national coverage inventory. Discovery-pool construction now canonicalizes on state plus municipality, retaining the highest-population record and then the lexicographically smallest municipality ID as a deterministic tie-breaker. A regression fixture proves that duplicate government entries cannot create duplicate lane targets.
