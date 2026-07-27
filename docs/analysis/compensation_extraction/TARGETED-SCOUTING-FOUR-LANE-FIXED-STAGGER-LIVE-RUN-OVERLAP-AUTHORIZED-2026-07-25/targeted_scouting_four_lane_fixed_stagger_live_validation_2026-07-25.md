# Fixed-stagger live validation — 2026-07-25

Initial live validation passed: all four immutable queue/ID hashes, exact 500-row lane scopes, 2,000-row combined scope, credential presence, corrected controlled-overlap contract, bounded concurrency, and live API handshake. The four lane states are `{'lane_1': 'completed', 'lane_2': 'completed', 'lane_3': 'completed', 'lane_4': 'completed'}`; candidates retained: 4,228; explicit skips/duplicates: 549.

## Live execution reconciliation

- Fixed starts: T+0 / T+8 / T+16 / T+24 exactly.
- Controlled overlap: explicitly authorized, recorded, and used.
- Locked targets processed: 500 / 500 / 500 / 500 = 2,000.
- Hosted-search lane requests: 2,000; bounded no-search API handshake: 1.
- Parsed leads before combined deduplication: 1,013 / 778 / 1,276 / 1,241.
- Deduplicated retained leads: 1,002 / 754 / 1,260 / 1,212 = 4,228.
- Duplicate candidate locators excluded: 80.
- Target outcomes with no retained lead or invalid response: 469 (465 no-high-specificity results, three schema/response failures, one isolated transport failure).
- Transport behavior: one isolated Lane 3 failure, no retry, followed by successful requests; no consecutive-failure stop gate fired.
- Raw prompts saved: 0; raw responses saved: 0.
- Hardening repair: the pre-commit diff check exposed three multiline 502 error bodies in redacted metadata. The runner now preserves only the error class plus `detail omitted`; checkpoints and final metadata were scrubbed deterministically, and raw-error scans pass.

## Focused tests

- New fixed-stagger live suite: 15/15 passed.
- Four-lane prep predecessor: 77/77 passed.
- Provisional claim-review predecessor: 62/62 passed.
- Claim-oriented phase-close predecessor: 69/69 passed.
- Combined focused suites: 223/223 passed.

## Repository validation

- `.venv/bin/python -m py_compile scripts/build_dashboard_data.py`: passed.
- `.venv/bin/python scripts/build_dashboard_data.py`: passed.
- `npm --prefix docs/dashboard run build`: passed; existing non-fatal Vite chunk-size warning only.
- `.venv/bin/python scripts/validate.py`: passed.
- `.venv/bin/python ingest/test_pipeline.py`: 60/60 passed.
- `.venv/bin/python ingest/audit_coverage.py`: passed; 28 healthy matched pairs, six unmatched safety units, two exploratory adjacent matches.
- `git diff --check`: passed.
- Completed-output `--resume`: passed with zero writes.

Candidate leads remain unverified, unextracted, unrated, and non-causal. No URL was opened as a document; no PDF/page/download/OCR, source verification, extraction, selection, ingestion, codification, quantitative analysis, wage-gap calculation, regression, treatment-effect estimation, or final-causal work occurred. Global analysis readiness remains false.
