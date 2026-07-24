# Verification Scale Round 1 3×750 Serial Merge Validation

Date: 2026-07-24  
Result: **PASS**

## Merge and lane integrity

- Six Python modules compiled.
- Eight scaled-verification checks passed. Network behavior in tests used only
  `httpx.MockTransport`; external network calls were zero.
- The final fresh lane audit again reports three
  `completed_merge_eligible` lanes, 2,250 planned/ledger/terminal rows, zero
  cross-lane duplicate verification IDs, zero accounting mutations, and
  `merge_all_verification_lanes`.
- The durable ledger has exactly 2,250 rows, 2,250 unique verification IDs,
  2,250 unique queue identities, and the
  `url_reachability_metadata_verified` routing stage on every row.
- All nonblank artifact paths were validated inside their lane roots.
- All dashboard and verification summary JSON files parse.
- The dashboard production build passed.

## Project validation

- `python scripts/validate.py`: passed with 64 contracts.
- `python ingest/test_pipeline.py`: 60 passed, 0 failed.
- `python ingest/audit_coverage.py`: 64 contracts, 19 cities, 28 healthy
  matched pairs (10 exact, 18 overlapping), two exploratory adjacent pairs,
  and six unmatched safety units.
- `git diff --check`: passed.

## Protected and accounting invariance

Committed-baseline SHA-256 checks passed for:

- `data/contracts.csv`;
- `data/city_coverage.csv`;
- the 4,726-row national scout candidate queue;
- municipality scout coverage;
- state scout coverage; and
- county scout coverage.

There are no diffs under `data/contracts.csv`, `data/city_coverage.csv`, or
`corpus/`. No scout candidate-queue or coverage builder ran. The verification
merge changed only the durable routing/status, dashboard, code, and
documentation layers.

No secret-bearing authorization, cookie, proxy-authorization, password,
token, or API-key JSON field appears in the lane metadata artifacts. No URL
was opened and no network/API/model call occurred during this serial merge or
its validation. No source was ingested or codified; no wage was extracted; no
wage gap, causal claim, or regression was produced.
