# Parallel Round 2 3×150 Serial Merge — Queue and Coverage Update

Date: 2026-07-23

Round: `POST-PI-PARALLEL-ROUND2-3X150-2026-07-23`

## Result

**Complete.** After the fresh three-lane audit returned
`merge_all_lanes`, the coordinator ran each authorized national accounting
command exactly once:

```text
python scripts/build_national_scout_candidate_queue.py
python scripts/build_national_scout_coverage_status.py
python scripts/build_scout_coverage.py
```

The top-level coverage orchestrator deterministically rewrote the same current
coverage status while refreshing county/universe-derived outputs. No command
was re-run after completion.

## National before and after

| Metric | Before | After | Change |
|---|---:|---:|---:|
| URL-bearing candidate queue rows | 2,362 | 3,347 | +985 |
| Successfully scout-covered municipalities | 1,091 | 1,537 | +446 |
| Candidate-positive municipalities | 884 | 1,267 | +383 |
| Parseable-empty municipalities | 207 | 270 | +63 |
| Failure-only municipalities | 23 | 27 | +4 |

All 985 parsed Round 2 lead rows had a nonblank source URL and entered the
unverified candidate queue. The resulting queue has 2,634 rows scheduled for
later verification: 2,110 high-, 334 medium-, and 190 low-priority rows. The
remaining 713 rows are held or rejected: 307 context-only, 215 insufficient,
181 likely duplicate, eight already-canonical holds, and two calibration
rejections. These are operational triage labels, not verification results.

Candidate-positive plus parseable-empty municipalities equals successful
coverage: `1,267 + 270 = 1,537`.

## Failure-only boundary

The following terminal transport failures were retained in the failure-only
lane and were not counted as successfully scout-covered:

- Twinsburg, Ohio — `empty_response_no_response_id`
- Oakland Park, Florida — `empty_response_no_response_id`
- Hollister, California — `outer_timeout`
- College Place, Washington — `empty_response_no_response_id`

The cumulative failed-attempt ledger now contains 43 attempts across 27
failure-only municipalities. A municipality with both an older failed attempt
and a successful parseable outcome remains successfully covered; only
failure-only municipalities are counted in the 27.

## State deltas from this round

Only affected states are shown. `Candidates` means URL-bearing candidate queue
rows, not verified sources.

| State | Covered | Positive | Empty | Failure-only | Candidates |
|---|---:|---:|---:|---:|---:|
| AK | +2 | +2 | 0 | 0 | +7 |
| AR | +5 | +3 | +2 | 0 | +5 |
| CA | +14 | +14 | 0 | +1 | +38 |
| CT | +2 | +2 | 0 | 0 | +4 |
| DE | +2 | +2 | 0 | 0 | +4 |
| FL | +59 | +37 | +22 | +1 | +74 |
| IA | +16 | +11 | +5 | 0 | +27 |
| ID | +5 | +3 | +2 | 0 | +7 |
| IN | +26 | +20 | +6 | 0 | +44 |
| KS | +1 | 0 | +1 | 0 | 0 |
| KY | +13 | +7 | +6 | 0 | +12 |
| MA | +12 | +11 | +1 | 0 | +34 |
| MD | +6 | +6 | 0 | 0 | +19 |
| ME | +2 | +2 | 0 | 0 | +6 |
| MI | +34 | +29 | +5 | 0 | +74 |
| MN | +17 | +16 | +1 | 0 | +34 |
| MS | +1 | +1 | 0 | 0 | +2 |
| MT | +4 | +4 | 0 | 0 | +12 |
| ND | +4 | +3 | +1 | 0 | +4 |
| NE | +6 | +6 | 0 | 0 | +9 |
| NH | +3 | +3 | 0 | 0 | +13 |
| NM | +2 | +2 | 0 | 0 | +4 |
| NV | +2 | +2 | 0 | 0 | +6 |
| NY | +2 | +2 | 0 | 0 | +4 |
| OH | +88 | +84 | +4 | +1 | +281 |
| OK | +9 | +4 | +5 | 0 | +6 |
| OR | +29 | +29 | 0 | 0 | +72 |
| RI | +2 | +2 | 0 | 0 | +6 |
| SD | +1 | +1 | 0 | 0 | +3 |
| VT | +1 | +1 | 0 | 0 | +3 |
| WA | +40 | +39 | +1 | +1 | +94 |
| WI | +33 | +32 | +1 | 0 | +70 |
| WY | +3 | +3 | 0 | 0 | +7 |
| **Total** | **+446** | **+383** | **+63** | **+4** | **+985** |

## Checkpoint effect

Official progress changed from 1,091/2,000 (54.5%) to 1,537/2,000
(76.9%). The remaining distance is 463 successfully scout-covered
municipalities, equivalent to four additional 150-row waves if considered
serially. A full 3 × 300 round would almost certainly exceed the checkpoint:
at Round 2's 99.1% parseable rate it would add roughly 892 successful outcomes
and reach about 2,429.

No source URL was independently opened or verified. No source was ingested or
codified, and no scout lead was promoted to verified evidence. No wage-gap
calculation, finding, causal claim, or regression occurred.
