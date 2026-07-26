# GABRIEL claim-rating summary review validation — 2026-07-25

- Immutable valid rating SHA-256: `de7ce29aa5c749e0faadab97ccade17d1f470e35e1dc48a95767baf70ed191e9` — passed.
- Immutable quarantine SHA-256: `f6a2035c12ad5bb514b1c3d3297707bd73beee531fc554ac5150e61c3aa25ae9` — passed.
- Valid rows: 636 — passed.
- Explicit exclusions: 7 — passed.
- Reconciled universe: 643 — passed.
- Attribute summaries: 14 v1.1 attributes; 722 positive attribute cells — passed.
- Quarantined-row contamination: 0 — passed.
- GABRIEL/API/model calls: none.
- PDF/page/OCR/URL/download/extraction/selection/ingestion/codify work: none.
- Wage-gap/regression/treatment-effect/final-causal work: none.
- Global analysis readiness: false.

## Commands

- New summary-review suite: 58/58 passed.
- Required predecessor suites: 251/251 passed.
- Combined focused suites: 309/309 passed.
- Dashboard data build: passed.
- Dashboard production build: passed with the existing non-fatal Vite chunk-size warning.
- Repository schema validation: passed.
- Ingestion pipeline tests: 60/60 passed (tests only; no ingestion run).
- Coverage audit: passed; six unmatched safety units reported.
- Idempotent `--resume`: passed with zero writes and zero model calls.
- `git diff --check`: passed.

## Regressions repaired

1. Corrected the summary runner's claim-relevance controlled-value alias.
2. Kept the narrative boundary validator fail-closed and made the summary scope wording explicit.
3. Added an explicit final-causal prohibition to the claims-limit document.
4. Corrected the predecessor dashboard-note template so seven explicit exclusions still permit the authorized 636-row summary review.
