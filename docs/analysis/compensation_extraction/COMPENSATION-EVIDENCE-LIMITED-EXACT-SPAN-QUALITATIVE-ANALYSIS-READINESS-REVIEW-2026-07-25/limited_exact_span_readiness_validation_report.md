# Limited exact-span readiness validation report

- Immutable required inputs: 21/21 SHA-256 checks passed.
- Exact candidates: 759/759 valid and unique; hashes, offsets, lengths, page pointers, active flags, identity, and provenance passed.
- Tier reconciliation: 759 + 614 + 581 = 1,954.
- Candidate contamination: zero.
- Historical QA and span QA remain separate.
- Forbidden page/full-text/model payload fields: zero.
- Carried-forward lane hashes: unchanged.
- Residual conflict quarantine: two groups/five observations.
- PDF/page access and forbidden operations in this review: zero.
- Global analysis readiness: false.

Full repository validation results are appended after command execution.

## Completed command results

- Python compilation (evidence-contract runner, limited-readiness runner, dashboard builder): passed.
- Predecessor qualitative evidence-contract focused tests: 37/37 passed.
- Limited exact-span readiness focused tests: 37/37 passed.
- Dashboard data build: passed.
- Dashboard production build: passed (the existing chunk-size advisory remains non-fatal).
- Repository schema validation: passed; 64 contracts, zero discourse, 64 coverage rows, three city-attribute rows.
- Ingestion pipeline tests: 60/60 passed.
- Coverage audit: passed; 28 healthy matched pairs, two exploratory adjacent matches, six unmatched safety units.
- `git diff --check`: passed.
