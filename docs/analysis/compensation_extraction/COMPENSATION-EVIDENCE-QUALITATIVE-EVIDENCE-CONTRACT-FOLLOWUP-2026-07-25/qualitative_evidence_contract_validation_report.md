# Qualitative evidence-contract validation report

- Immutable upstream hashes: 19/19 passed.
- Frozen qualitative IDs: 1,954/1,954 unique and order-aligned.
- Tier reconciliation: 759 + 614 + 581 = 1,954.
- Exact candidate QA: 759/759 `span_exact_unique_verified`, pass=true, valid hashes/offsets/lengths, single-line.
- Candidate contamination: zero ambiguous or unavailable rows.
- Historical QA and span QA remain separate.
- Forbidden full-page/raw payload columns: zero.
- PDF/page accesses in this task: zero.
- Carried-forward files: byte-identical to approved predecessors.
- Analysis readiness: false.

## Focused validation

- Evidence-contract suite: 37/37 passed.
- Predecessor span-disambiguation suite: 32/32 passed.
- No-write preflight: 19 immutable hashes; 759/614/581 tiers; zero writes and zero PDF access.
- Complete-output resume: reused with zero writes.
- Fail-closed cases include input-hash drift, wrong tier counts, duplicate IDs, corrupted exact-span hashes/offsets, ambiguous or unavailable candidate contamination, historical-QA overwrite, page-text columns, carried-file drift, incorrect future-prompt phase, output-boundary violation, and analysis-readiness promotion.

## Repository validation

- Python compilation: passed for the contract runner, predecessor disambiguation runner, and dashboard builder.
- Dashboard data build: passed; 51 states/DC, 35,589 municipalities, 2,436 scout-covered municipalities, and 4,726 candidate rows.
- Dashboard frontend build: passed. Vite emitted its existing non-blocking chunk-size advisory.
- Repository schema validation: passed; 64 contracts, zero discourse rows, 64 coverage rows, and three city-attribute rows.
- Ingestion pipeline suite: 60/60 passed.
- Coverage audit: 28 healthy matched pairs (10 exact-cycle and 18 overlap-cycle), two exploratory adjacent matches, and six unmatched safety units.
- `git diff --check`: passed.

## Hardening issue and correction

The initial materialization stopped closed because the validator required the future-review prompt before the reporting phase created it. No upstream input was changed and no decision was produced. The task-only partial directory was removed; validation now distinguishes pre-report from complete-output checks and revalidates after prompt creation. Two regression tests cover both phases. Clean rematerialization and all validations passed.

## Boundary confirmation

- No package, prior repair, prior span-capture, disambiguation, or durable ledger was modified.
- No PDF or page was accessed.
- No URL, hosted search, download, OCR, image, GABRIEL/API, extraction, selection, ingestion, codification, wage-gap calculation, regression, or causal analysis occurred.
- Analysis readiness and analysis-facing promotion remain false.
