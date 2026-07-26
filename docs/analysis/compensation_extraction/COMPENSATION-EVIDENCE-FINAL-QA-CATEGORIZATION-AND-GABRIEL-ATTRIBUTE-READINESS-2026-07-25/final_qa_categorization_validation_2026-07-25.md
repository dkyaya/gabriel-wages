# Final QA categorization validation

- Package SHA-256 checks: 5/5 passed.
- Immutable direct evidence inputs verified: 21.
- Considered records: 8,939; exactly one primary category each.
- Category counts: {"companion_context_only": 5078, "gabriel_attribute_ready": 643, "limited_documentary_claim_ready": 862, "navigation_only": 614, "quarantined": 121, "write_off_this_phase": 1621}.
- GABRIEL-ready contamination: zero.
- Attribute taxonomy: 13 controlled attributes; no vague null/no_good bucket.
- Global analysis readiness: false.

## Executed validation

- Python compilation: passed for the phase-close runner, focused test suite, and dashboard builder.
- New final phase-close suite: 74/74 passed.
- Six required predecessor suites: 381/381 passed.
- Combined focused suites: 455/455 passed.
- Dashboard data build: passed.
- Dashboard production build: passed; the existing non-fatal Vite chunk-size warning remains.
- Repository schema validation: passed (`contracts=64`, `discourse=0`, `coverage=64`, `city_attributes=3`).
- Ingestion pipeline tests: 60/60 passed; tests only, no ingestion run.
- Coverage audit: passed; 28 healthy matches (10 exact, 18 overlap), two exploratory adjacent matches, and six unmatched safety units.
- `git diff --check`: passed.
- Idempotent `--resume`: passed with zero writes.
- Partial-output completion validation: passed fail-closed.

## Hardening finding

The first post-dashboard pass found one descendant-state compatibility defect: the registry-review validator and three older materialized-output tests ended their explicit closed-state allowlists at registry acceptance. They now recognize only the exact final phase-close state in addition to prior states. Readiness, promotion, lane-separation, contamination, and non-analysis assertions remain unchanged, and the registry-review suite has a dedicated phase-close regression test.
