# Limited exact-span qualitative promotion validation

- Authorized baseline and all immutable inputs: passed.
- Five package SHA-256 checks: passed.
- 759 exact rows and 1,195 navigation-only rows: reconciled.
- Row-level eligibility and quarantine scope counts: reconciled.
- Span/provenance/history preservation: passed.
- Carried-forward lanes remain separate; global analysis readiness remains false.

## Focused test results

- Hardened limited-promotion suite: 56/56 passed.
- Pipeline hardening accelerator suite: 48/48 passed.
- Limited exact-span readiness-review suite: 37/37 passed.
- Qualitative evidence-contract suite: 37/37 passed.
- Combined focused result: 178/178 passed.

## Repository validation results

- Python compilation for the promotion runner and dashboard builder: passed.
- Dashboard data rebuild: passed (51 states/DC; 35,589 municipalities; 2,436 scout-covered; 4,726 candidate rows).
- Dashboard production build: passed; the existing Vite chunk-size advisory remains non-fatal.
- `scripts/validate.py`: passed (64 contracts, 0 discourse rows, 64 coverage rows, 3 city-attribute rows).
- `ingest/test_pipeline.py`: 60/60 passed.
- `ingest/audit_coverage.py`: completed; 28 healthy matched pairs, 2 exploratory adjacent matches, and 6 unmatched safety units. No corpus rows were changed.
- `git diff --check`: passed.
- Idempotent `--resume`: passed with zero writes and unchanged output hashes.

## Final validation conclusion

All immutable-input, tier-contamination, identity, span, provenance, current-active/QA, mixed-membership, mechanism-typing, cycle, occupation, matching, lane-separation, conflict, checkpoint, dashboard, prompt, relay, and count-reconciliation gates passed. Global analysis readiness remains false. Only a separately authorized limited usage review is allowed next.
