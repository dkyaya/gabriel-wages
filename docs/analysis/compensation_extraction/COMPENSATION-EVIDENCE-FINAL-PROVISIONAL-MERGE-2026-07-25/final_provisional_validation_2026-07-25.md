# Final provisional package validation - 2026-07-25

- Five approved input SHA-256 values: pass (5 / 5)
- Exactly five merge-data inputs: pass
- Five schemas remain separate: pass
- Output ledgers byte-for-byte equal inputs: pass
- Source rows: pass ({'quantitative': 2044, 'qualitative': 1954, 'mixed': 387, 'non_base_wage': 4746, 'reference_and_exclusion': 345})
- Active rows: pass ({'quantitative': 1907, 'qualitative': 1954, 'mixed': 371, 'non_base_wage': 4733, 'reference_and_exclusion': 345})
- Unique case/content-hash-derived identities: pass (1826)
- Duplicate observation IDs: pass (0)
- Duplicate provenance rows: pass (14)
- Newly canonicalized duplicates: pass (5)
- Invalid bounded page pointers: pass (0)
- Base/non-base contamination: pass (0)
- Working-out-of-classification reroutes: pass (3)
- Wasco shadow repair: pass (1)
- Explicit unresolved groups: pass (2)
- Mixed joins and member IDs: pass
- Unit/state/source representation: pass
- OCR-later documents excluded: pass
- Analysis readiness remains false: pass

## Repository-wide validation

- `py_compile` for the merge runner, focused tests, and dashboard builder: pass
- Focused final-provisional-merge tests: pass (14 / 14)
- Dashboard data generation: pass
- Dashboard frontend production build: pass (one non-blocking Vite chunk-size warning)
- Repository schema validation: pass (64 contracts; 0 discourse; 64 coverage rows; 3 city-attribute rows)
- Ingestion pipeline regression tests: pass (60 / 60)
- Coverage audit: pass (19 cities; 28 healthy matches: 10 exact and 18 overlap; 2 adjacent; 6 unmatched safety units)
- Independent post-build package reconciliation: pass
- Approved corrected input ledgers unchanged: pass
- Protected `data/contracts.csv`, `data/city_coverage.csv`, and `corpus/`: unchanged
- Dashboard JSON parse/build and analysis-readiness-false gate: pass
- Bounded secret-pattern scan of new package/code/docs: pass
- `git diff --check`: pass

No URL, hosted search, download, OCR, extraction, document selection,
GABRIEL/API, scout, source review, verification, ingestion, codification,
final-analysis dataset creation, wage-gap calculation, regression, or causal
analysis occurred.
