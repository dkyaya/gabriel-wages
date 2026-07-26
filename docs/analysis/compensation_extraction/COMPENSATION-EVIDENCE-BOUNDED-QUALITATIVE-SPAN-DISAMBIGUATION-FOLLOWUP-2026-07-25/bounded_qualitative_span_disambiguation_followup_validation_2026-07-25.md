# Bounded qualitative span disambiguation validation

- Immutable prior input hashes: 19/19 passed.
- Immutable package hashes: 5/5 passed.
- Previously verified spans preserved: 455/455.
- Review accounting: 1499/1499.
- Approved review pages accounted for: 1011/1011; OCR-later/non-target: 0/0.
- Exact unique QA spans after follow-up: 759/1954.
- Full page text persisted: 0. Analysis readiness: false.

## Focused and regression validation

- Python compilation: passed for the predecessor PDF span-capture runner, the new disambiguation runner, and the dashboard builder.
- Disambiguation focused suite: 32/32 passed.
- Predecessor PDF text-layer span-capture suite: 32/32 passed.
- Required disambiguation failure modes represented: 15/15.
- Complete-output resume/idempotency check: passed with zero PDF page reaccesses.
- Wrong-hash, prior-span offset/hash mismatch, non-target page, checkpoint leakage, duplicate-ID, fuzzy/paraphrase, cross-line, ambiguous-repeat, and full-page-text leakage cases all failed closed as designed.
- Carried-forward quantitative, exception, non-base, reference/control, conflict-quarantine, and residual-metadata outputs are byte-identical to their approved predecessors.

## Repository validation

- `.venv/bin/python scripts/build_dashboard_data.py`: passed; 51 states/DC, 35,589 municipalities, 2,436 scout-covered municipalities, and 4,726 candidate rows.
- `npm --prefix docs/dashboard run build`: passed. Vite emitted its existing non-blocking chunk-size advisory.
- `.venv/bin/python scripts/validate.py`: passed; 64 contracts, zero discourse rows, 64 coverage rows, and three city-attribute rows.
- `.venv/bin/python ingest/test_pipeline.py`: 60/60 passed.
- `.venv/bin/python ingest/audit_coverage.py`: completed; 28 healthy matched pairs (10 exact-cycle, 18 overlap-cycle), two exploratory adjacent matches, and six unmatched safety units.
- `git diff --check`: passed.

## Boundary confirmation

- No package, prior repair, prior span-capture, or durable ledger was modified.
- No GABRIEL/API, extraction, selection, OCR, rendered-image use, ingestion, codification, wage-gap calculation, regression, or causal analysis occurred.
- Only the 1,011 approved pages for the 1,499 unresolved rows were accessed; all 455 previously verified rows were preserved without PDF reaccess.
- No coded qualitative analysis view was created because 614 ambiguous and 581 unavailable rows remain.
