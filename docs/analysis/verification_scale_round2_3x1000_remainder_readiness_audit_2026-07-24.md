# Verification Scale Round 2 3×1000 Remainder Readiness Audit

Date: 2026-07-24  
Round: `VERIFICATION-SCALE-ROUND2-3X1000-REMAINDER-2026-07-24`  
Starting commit: `2bab4b02ce801975e6c86612528486d012abd6e7`

## Repository and lineage

- The tracked worktree was clean before work.
- The unrelated untracked root `package-lock.json` was reported and left
  untouched.
- Current `HEAD` descends from `2bab4b0`, `642dbda`, `ee7041a`, `3616bae`,
  and `98ad608`.

## Canonical inputs and exact remainder

- Canonical candidate queue:
  `docs/analysis/national_scout_candidate_queue_2026-07-20.csv`
- Round 1 durable routing ledger:
  `docs/analysis/verification_ledgers/VERIFICATION-SCALE-ROUND1-3X750-2026-07-23/verified_source_routing_ledger.csv`

The canonical queue has 4,726 URL-bearing rows and 4,726 unique queue IDs.
Round 1 has 2,250 terminal routing rows, 2,250 unique verification IDs, 2,250
unique candidate-queue IDs, and
`verification_stage = url_reachability_metadata_verified` on every row. All
2,250 Round 1 queue identities map back to the canonical queue.

The exact identity subtraction leaves **2,476 URL-bearing rows**:

| Original disposition | Remaining |
|---|---:|
| High-priority scheduled | 575 |
| Medium-priority scheduled | 490 |
| Low-priority scheduled | 285 |
| **All scheduled** | **1,350** |
| Context hold | 523 |
| Insufficient hold | 302 |
| Likely-duplicate hold | 291 |
| Already-canonical hold | 8 |
| Calibration rejection | 2 |
| **All non-scheduled** | **1,126** |
| **Total remainder** | **2,476** |

There are no Round 1 ledger identities absent from the canonical queue and no
duplicate queue or verification identity in either layer.

## Option B

Option B first selects all 1,350 remaining scheduled rows, then includes all
1,126 remaining URL-bearing context/insufficient/duplicate/canonical/
calibration dispositions. Their original status is retained. They are being
routed because the user requested disposition of the complete candidate URL
pool, not promoted into high-quality or analysis-ready evidence.

The 3×1,000 profile supplies a 3,000-row ceiling. Because only 2,476 eligible
rows remain, the plan must be 524 rows under capacity and include the entire
remainder. Duplicate-aware balanced assignment is expected to produce
approximately 826/825/825 rows.

Round 1 completed 2,250 terminal routing outcomes with 1,888 reachable/reused
(83.911%), small metadata-only artifacts, no retained content, and a clean
three-lane audit. That performance justifies the larger *capacity* while
retaining the same concurrency-eight, 20/8/15-second timing, five-redirect,
and 10 MiB response safeguards.

## Risks and boundary

- Slow municipal servers may consume the per-row timeout.
- Blocked/forbidden and not-found URLs remain explicit routing outcomes.
- Oversized documents remain `too_large`; the global cap is not increased.
- Exact duplicate groups should reuse one representative fetch without
  dropping identities.
- Held/context/canonical/rejected rows may be lower-quality leads and retain
  those original dispositions.

Readiness work opened no URL and made no network, API, model, hosted-search,
or scout call. It did not ingest or codify a source, extract a wage, calculate
a wage gap, make a claim, run a regression, or change scout accounting.
Planning may proceed.
