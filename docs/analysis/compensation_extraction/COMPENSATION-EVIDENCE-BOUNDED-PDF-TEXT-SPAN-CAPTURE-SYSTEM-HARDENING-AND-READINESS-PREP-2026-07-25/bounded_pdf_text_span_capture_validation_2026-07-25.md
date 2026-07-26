# Bounded PDF text-layer span capture validation

- Immutable structured input SHA-256 checks: 12/12 passed.
- Immutable final-package ledger SHA-256 checks: 5/5 passed.
- Retained PDF SHA-256 checks: 788/788 passed before page parsing.
- Post-hardening no-write dry run: passed; writes performed: 0.
- Qualitative row uniqueness/accounting: 1954/1954.
- Approved unique pages accessed: 1223/1223; non-target: 0.
- OCR-later documents opened: 0; rendered images: 0; page text persisted: 0.
- Exact literal substrings captured: 1346; unique-candidate span QA passes: 455; ambiguous exact spans: 891; unavailable/not sufficient: 1499.
- Stored-span single-line and repository-whitespace checks: passed.
- Focused hardening tests: 32/32 passed.
- Carried-forward byte checks: quantitative candidates/exceptions, non-base, reference/control, conflicts, and residual quarantine passed.
- Predecessor schema-repair suites: 9/9 and 13/13 passed.
- Dashboard data build and Vite production build: passed (Vite emitted only its advisory chunk-size warning).
- Repository validation and ingestion tests: passed; 60/60 ingestion tests.
- Coverage audit: 28 healthy matched pairs, 2 exploratory adjacent matches, and 6 unmatched safety units.
- Repository diff whitespace check: passed.
- Analysis readiness remains false.
