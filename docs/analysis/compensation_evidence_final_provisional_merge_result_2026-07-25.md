# Final provisional compensation-evidence package result - 2026-07-25

## Outcome

Decision: `final_provisional_package_materialized_qa_pass`.

The explicitly authorized package-level merge completed. The five corrected
shadow ledgers were verified, copied byte-for-byte into five separate package
lanes, validated in a rollback-safe staging directory, atomically published,
and reopened for post-publication verification.

This is a provisional evidence package, not a final analysis dataset. Analysis
readiness, ingestion, codification, wage-gap analysis, and regression remain
false.

## Package

Path:
`docs/analysis/compensation_extraction/COMPENSATION-EVIDENCE-FINAL-PROVISIONAL-MERGE-2026-07-25/`

| Schema | Source rows | Active rows |
| --- | ---: | ---: |
| Quantitative base compensation | 2,044 | 1,907 |
| Qualitative mechanisms | 1,954 | 1,954 |
| Mixed quant/qual joins | 387 | 371 |
| Non-base-wage compensation | 4,746 | 4,733 |
| Reference/exclusion | 345 | 345 |

All five outputs are byte-for-byte identical to their approved corrected
inputs and therefore retain the same SHA-256 values.

## Integrity reconciliation

- Unique case/content-hash-derived identities: 1,826
- Independent-review unique readable content-hash attestation: 1,826
- Unit representation: 780 police / 439 fire / 607 non-safety
- States/DC: 51
- Source families: 6
- Duplicate observation IDs: 0
- Duplicate-provenance rows: 14
- Newly canonicalized duplicates: 5
- Invalid bounded page pointers: 0
- Active base/non-base contamination: 0
- Working-out-of-classification reroutes: 3
- Wasco shadow-only record repair: 1
- Explicit unresolved groups: 2
- Unresolved rate: 0.1049%
- Historical mixed-key provenance references preserved: 5

The two residual groups remain explicitly unresolved in
`final_provisional_conflict_register.csv`; no rank, step, schedule cell,
classification, pay band, or effective period was inferred.

## Boundary

No extraction, selection, GABRIEL/API call, URL access, download, OCR, scout,
source review, verification, ingestion, `gabriel.codify`, final-analysis
dataset creation, wage-gap calculation, regression, or causal analysis
occurred. OCR-later documents remain excluded. The next action is a separately
authorized schema and analysis-readiness review, not automatic ingestion or
analysis.
