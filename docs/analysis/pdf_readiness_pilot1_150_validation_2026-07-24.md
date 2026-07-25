# PDF-Readiness Pilot 1 (150) Validation

Date: 2026-07-24

## Result

**PASS.** The locked plan, three dry-run lanes, three bounded local lanes,
audits, dashboard status, immutable upstream layers, and repository-wide
tests passed.

## Requested command results

- Five requested Python modules compiled.
- `scripts/test_pdf_readiness_planning.py`: 11 tests passed.
- Final readiness lane audit:
  - planned / ledger / terminal: 150 / 150 / 150;
  - three `completed_merge_eligible` lanes;
  - duplicate readiness/source-review/candidate IDs: 0 / 0 / 0;
  - hash failures: 0;
  - missing artifacts: 0;
  - parser errors: 0; and
  - recommendation: `merge_all_pdf_readiness_lanes`.
- Dashboard builder completed and all 17 dashboard JSON files parsed.
- Dashboard Vite production build completed.
- `scripts/validate.py` passed:
  64 contracts, zero discourse rows, 64 coverage rows, and three
  city-attribute rows.
- `ingest/test_pipeline.py`: 60 tests passed.
- Coverage audit:
  64 contracts, 19 cities, 28 healthy matched pairs (10 exact and 18
  overlapping), two exploratory adjacent matches, and six unmatched safety
  units.
- `git diff --check` passed.

Command logs are retained under:

`tmp/pdf_readiness_pilots/PDF-READINESS-PILOT1-150-2026-07-24/pdf_readiness_pilot1_validation_2026-07-24/`

The final audit is retained under:

`tmp/pdf_readiness_pilots/PDF-READINESS-PILOT1-150-2026-07-24/final_local_readiness_validation_lane_audit/`

## Independent result verification

The independent verifier confirmed:

- exact equality between the 150 locked input identities and local output
  identities;
- lane rows: 50 / 50 / 50;
- unique readiness/source-review/candidate identities: 150 / 150 / 150;
- terminal `readiness_checked`: 150;
- artifact existence/hash/size/signature checks passed: 150 / 150 / 150 /
  150;
- page counts obtained: 150;
- text layer present / partial / absent: 107 / 19 / 24;
- sampled pages checked / with text: 431 / 341;
- parser, artifact, hash, signature, and per-file timeout failures: 0;
- dry-run and local output directories contain only ledger, summary, and
  timing files;
- copied PDFs: 0;
- full extracted-text files: 0; and
- secret-bearing output indicators: 0.

## Immutable upstream and protected layers

Pre-task hashes remained unchanged for:

- `data/contracts.csv`;
- `data/city_coverage.csv`;
- the national candidate queue;
- scout-coverage accounting;
- the cumulative URL-routing ledger;
- the cumulative metadata-triage ledger;
- cumulative/latest durable source-review ledgers;
- cumulative/latest durable source-review summaries; and
- the complete 79-file `corpus/` tree.

No durable PDF-readiness ledger directory exists. The collected lane outputs
and audit remain lane-local/transient pending separate merge authorization.

## Process boundary

- URLs opened: 0
- network/API/model calls: 0
- downloads/redownloads: 0
- live source review or URL verification: 0
- OCR runs: 0
- full-text artifacts: 0
- wage tables/values extracted: 0 / 0
- ingestion/codify actions: 0 / 0
- scout-accounting changes: 0
- routing/triage/source-review-ledger mutations: 0
- durable readiness merges: 0
- wage-gap calculations, causal claims, and regressions: 0

Page count and sampled text-layer presence remain technical readiness
signals. Validation does not establish source relevance, document identity,
employer/unit match, wage content, or analysis-ready evidence.
