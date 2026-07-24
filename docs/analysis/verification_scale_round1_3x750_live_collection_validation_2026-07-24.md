# Verification Scale Round 1 3×750 Live Collection Validation

Date: 2026-07-24
Result: **PASS**

## Collection and audit integrity

- Exactly three authorized live lanes exist; no fourth lane exists.
- Each lane has exactly 750 ledger rows and 750 terminal outcomes.
- Each ledger exactly matches its locked input's verification ID, queue ID,
  and duplicate-group mapping.
- The three input hashes remain
  `c03701be…cbfa65`, `ac9ee0b0…048ca`, and
  `a9192b47…9994a`.
- The combined auditor classifies all three lanes
  `completed_merge_eligible`, finds zero cross-lane duplicate verification
  IDs, and recommends `merge_all_verification_lanes`.
- The auditor reports zero accounting mutations.
- Eight duplicate rows reused in-lane representative results while all 2,250
  identities remained present.
- All nonblank artifact paths resolve inside their lane output directory.
- Lane artifact directories contain 2,221 JSON metadata files, total 952,655
  bytes, maximum 627 bytes.
- No content sample or full candidate document was stored.
- Artifact JSON contains no authorization, cookie, proxy-authorization,
  password, token, or API-key header fields.

## Code and project validation

- Five verification/dashboard Python modules compiled.
- Six scaled-verification offline/mock checks passed. Their live-path cases
  use `httpx.MockTransport`, not the public network.
- `python scripts/validate.py` passed with 64 contracts.
- `python ingest/test_pipeline.py`: 60 passed, 0 failed.
- `python ingest/audit_coverage.py`: 64 contracts, 19 cities, 28 healthy
  matched pairs (10 exact, 18 overlapping), two exploratory adjacent pairs,
  and six unmatched safety units.
- `git diff --check` passed.

## Protected and accounting invariance

SHA-256 checks confirm no changes to:

- `data/contracts.csv`;
- `data/city_coverage.csv`;
- `docs/analysis/national_scout_candidate_queue_2026-07-20.csv`;
- national municipality scout coverage;
- national state scout coverage; or
- national county scout coverage.

No queue, coverage, dashboard/project-phase, ingestion, codification,
extraction, wage-gap, causal, or regression builder ran from the live lane
outputs. No durable verified-source ledger merge occurred. No remote was
inspected and no push, fetch, or pull occurred.
