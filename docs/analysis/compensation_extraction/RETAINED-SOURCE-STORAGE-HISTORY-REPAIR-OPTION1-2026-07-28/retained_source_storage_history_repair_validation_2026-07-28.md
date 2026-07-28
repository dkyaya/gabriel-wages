# Retained-source storage/history repair validation

All required validation gates passed.

## Integrity and preservation

- Manifest rows: 4,961.
- Hash-manifest rows: 4,961.
- Unique hashes: 4,961.
- PDF/HTML/other: 3,980 / 941 / 40.
- Before-repair original size/hash matches: 4,961 / 4,961.
- After-preservation original size/hash matches: 4,961 / 4,961.
- After-preservation artifact-copy size/hash matches: 4,961 / 4,961.
- Total bytes: 12,475,949,771.

## Git/history

- Branch: `main`.
- Unchanged pushed base: `845333f`.
- Original local-only heavy HEAD: `d17549f`.
- Repaired commit: `52a9243`.
- Repaired tracked retained paths: 0.
- Repaired retained blob paths ahead of base: 0.
- Repaired blobs over 100 MiB: 0.
- Force push: no.
- Pushed-history rewrite: no.
- Plain repaired push: passed on attempt 1.

## Project commands

- Python compilation: passed.
- Dashboard data build: passed.
- Dashboard frontend build: passed.
- Repository schema validation: passed.
- Ingestion regression suite: 60 passed, 0 failed.
- Storage/history repair regression suite: passed.
- `git diff --check`: passed.

## Dashboard and research boundaries

The map filter remains `total_scout_coverage_only`. Readiness counts remain 4,961 reviewed and 4,051 extraction-ready. Global analysis readiness remains false. No research stage, redownload, extraction, OCR, rendering, rating, ingestion, codification, statistical analysis, prevalence analysis, or causal analysis occurred.
