# Future Prompt: Merge Full Retained PDF Readiness Exactly Once

Use this prompt only after reviewing the full-retained readiness relay. Do
not execute it as part of the collection task that created this file.

## Task

Run one serial offline durable PDF-readiness merge covering every retained
PDF artifact in the cumulative source-review ledger.

Merge exactly once:

1. `PDF-READINESS-PILOT1-150-2026-07-24`
   - three `lane_*_local_attempt1/pdf_readiness_ledger.csv` files;
   - expected rows: 150.
2. `PDF-READINESS-REMAINDER-ALL-RETAINED-2026-07-24`
   - four `lane_*_local_attempt1/pdf_readiness_ledger.csv` files;
   - expected rows: 1,974.

Do not run a Pilot-1-only merge. Do not rerun local PDF parsing during the
merge.

## Readiness gates

Start from the main coordinator repository and require a clean tracked
worktree. Preserve unrelated untracked files. Confirm the merge task opens no
remote and performs no fetch, pull, or push.

Re-run:

```bash
.venv/bin/python scripts/audit_pdf_readiness_lanes.py \
  --manifest docs/analysis/pdf_readiness_pilots/PDF-READINESS-PILOT1-150-2026-07-24/pdf_readiness_pilot_manifest.json \
  --output-dir tmp/pdf_readiness_pilots/PDF-READINESS-PILOT1-150-2026-07-24/cumulative_merge_readiness_audit

.venv/bin/python scripts/audit_pdf_readiness_lanes.py \
  --manifest docs/analysis/pdf_readiness_pilots/PDF-READINESS-REMAINDER-ALL-RETAINED-2026-07-24/pdf_readiness_pilot_manifest.json \
  --output-dir tmp/pdf_readiness_pilots/PDF-READINESS-REMAINDER-ALL-RETAINED-2026-07-24/cumulative_merge_readiness_audit
```

Require for both rounds:

- every lane `completed_merge_eligible`;
- planned rows equal ledger and terminal rows;
- no duplicate PDF-readiness, source-review, or candidate-queue identities;
- no missing/unexpected rows;
- no hash failure, missing artifact, or terminal parser error;
- no URL, network, download, OCR, extracted-text, wage, ingestion, codify,
  or durable-merge counters; and
- recommendation `merge_all_pdf_readiness_lanes`.

Require cross-round:

- Pilot 1 rows: 150;
- remainder rows: 1,974, or recomputed actual;
- cross-round duplicate source-review IDs: 0;
- cross-round duplicate candidate-queue IDs: 0;
- union row count equals the retained-PDF row count recomputed from
  `docs/analysis/source_review_ledgers/source_review_ledger_cumulative.csv`;
- exact source-review-ID and candidate-queue-ID set equality with retained
  rows having `reviewed_metadata_and_artifact_saved`,
  `application/pdf`, a nonblank artifact path/hash, and positive byte size;
  and
- every readiness artifact path/hash/size equals its durable source-review
  record.

Stop without merging if any gate fails.

## Merge implementation

Create or extend `scripts/merge_pdf_readiness_lanes.py` as an offline,
fail-closed, exactly-once merge tool. It must:

- accept both round manifests and both audit summaries explicitly;
- read only the seven locked local readiness ledgers;
- concatenate deterministically;
- preserve every inherited identity, artifact path/hash/size, page count,
  sampled-page count, parser/version, text-layer status, sanitized error,
  technical parseability, next action, reviewer, and timestamp;
- record readiness round/lane provenance;
- reject any duplicate identity, nonterminal row, coverage mismatch, unsafe
  counter, or pre-existing target output;
- write atomically only after every gate passes; and
- make no network call and open no retained PDF.

Required durable outputs:

- `docs/analysis/pdf_readiness_ledgers/pdf_readiness_ledger_cumulative.csv`
- `docs/analysis/pdf_readiness_ledgers/pdf_readiness_summary_cumulative.json`
- `docs/analysis/pdf_readiness_ledgers/pdf_readiness_merge_audit_cumulative.md`
- `docs/analysis/pdf_readiness_ledgers/pdf_readiness_ledger_latest.csv`
- `docs/analysis/pdf_readiness_ledgers/pdf_readiness_summary_latest.json`

The expected cumulative row count is 2,124, but compute the actual from the
source-review ledger and do not hardcode it.

## Post-merge checks

Confirm:

- exact retained-PDF source-review-ID and candidate-queue-ID equality;
- all durable readiness rows are terminal;
- page-count/text-layer/parseability/next-action distributions reproduce
  the audited collection;
- all 2,124, or actual, recorded artifact paths remain lane-local;
- no copied PDF or extracted text is written;
- the routing, triage, source-review, candidate, scout, contracts, city
  coverage, and `corpus/` layers remain unchanged; and
- no URL, network, download, PDF parse, OCR, wage extraction, ingestion,
  codify, wage-gap analysis, claim, or regression occurs during merge.

Refresh the dashboard to `full_retained_merged`, clearly labeling page count
and text-layer results as technical readiness only. Keep OCR, ingestion,
codification, wage extraction, and wage-gap analysis not started.

Run compile, offline/mock tests, both final lane audits, dashboard build and
JSON parse, `scripts/validate.py`, `ingest/test_pipeline.py`,
`ingest/audit_coverage.py`, immutable-ledger/protected-file checks, secret
checks, and `git diff --check`. Create one local commit and a lite relay; do
not push or inspect remotes.
