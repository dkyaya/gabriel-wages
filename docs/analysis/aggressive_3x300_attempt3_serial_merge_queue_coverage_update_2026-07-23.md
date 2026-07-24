# Aggressive 3×300 Attempt 3 Serial Merge — Queue and Coverage Update

Date: 2026-07-23/24  
Round: `POST-PI-AGGRESSIVE-ROUND-3X300-2026-07-23`

## Result

**Complete.** After the fresh three-lane audit returned `merge_all_lanes`,
the coordinator ran the required national accounting commands once each, in
order:

```text
python scripts/build_national_scout_candidate_queue.py
python scripts/build_national_scout_coverage_status.py
python scripts/build_scout_coverage.py
```

As in prior merges, the top-level coverage orchestrator deterministically
rewrote the same current coverage status while refreshing its universe-derived
outputs. No command was manually re-run.

## National before and after

| Metric | Before | After | Change |
|---|---:|---:|---:|
| URL-bearing candidate queue rows | 3,347 | 4,726 | +1,379 |
| Successfully scout-covered municipalities | 1,537 | 2,436 | +899 |
| Candidate-positive municipalities | 1,267 | 1,858 | +591 |
| Parseable-empty municipalities | 270 | 578 | +308 |
| Failure-only municipalities | 27 | 28 | +1 |

Attempt 3 produced 1,389 parsed lead rows. Ten rows lacked a nonblank source
locator and therefore remain outside the URL-bearing queue: California 2,
Louisiana 1, Maryland 1, Maine 1, Ohio 1, Tennessee 2, and Virginia 2. Every
one of the 591 candidate-positive municipalities still has at least one
URL-bearing lead, so this locator filter did not convert any positive
municipality to parseable-empty.

Candidate-positive plus parseable-empty municipalities equals successful
coverage: `1,858 + 578 = 2,436`.

## Queue disposition

The 4,726-row unverified queue currently contains:

- 2,825 high-priority later-verification rows;
- 490 medium-priority later-verification rows;
- 285 low-priority later-verification rows;
- 523 context-only holds;
- 302 insufficient holds;
- 291 likely-duplicate holds;
- eight already-canonical holds; and
- two calibration rejections.

Thus 3,600 URL-bearing rows are scheduled for later verification and 1,126 are
held or rejected. These are deterministic scout-stage triage labels, not
source-verification findings.

## Failure-only boundary

Shelby, Ohio (`cog_2025_209091`) is retained as
`scout_attempt_failed_connection` from run `all_2026-07-23_221645`.
Its `outer_timeout` is the only Attempt 3 failure-only result. It has no
candidate rows and is not counted among the 2,436 successfully covered
municipalities.

The cumulative failed-attempt ledger now contains 44 retained attempts across
28 failure-only municipalities. Attempts 1–2 and the Newport diagnostic probe
remain quarantined and are not accounting inputs.

## State deltas from Attempt 3

Only affected states are shown. `Candidates` means newly added URL-bearing
queue rows, not verified sources.

| State | Covered | Positive | Empty | Failure-only | Candidates |
|---|---:|---:|---:|---:|---:|
| AK | +10 | +9 | +1 | 0 | +19 |
| AL | +8 | +3 | +5 | 0 | +5 |
| AR | +8 | +3 | +5 | 0 | +5 |
| AZ | +4 | +4 | 0 | 0 | +8 |
| CA | +146 | +141 | +5 | 0 | +385 |
| CO | +5 | +2 | +3 | 0 | +4 |
| CT | +3 | +2 | +1 | 0 | +6 |
| DE | +6 | +5 | +1 | 0 | +13 |
| IA | +9 | +6 | +3 | 0 | +16 |
| ID | +9 | +3 | +6 | 0 | +6 |
| IL | +1 | +1 | 0 | 0 | +3 |
| IN | +2 | +2 | 0 | 0 | +3 |
| KS | +16 | +12 | +4 | 0 | +27 |
| LA | +19 | +7 | +12 | 0 | +15 |
| MA | +3 | +2 | +1 | 0 | +6 |
| MD | +27 | +14 | +13 | 0 | +26 |
| ME | +18 | +15 | +3 | 0 | +40 |
| MI | +3 | +2 | +1 | 0 | +5 |
| MN | +57 | +36 | +21 | 0 | +81 |
| MO | +39 | +23 | +16 | 0 | +45 |
| MS | +31 | +4 | +27 | 0 | +8 |
| MT | +14 | +11 | +3 | 0 | +31 |
| ND | +4 | +2 | +2 | 0 | +7 |
| NE | +6 | +5 | +1 | 0 | +14 |
| NH | +8 | +6 | +2 | 0 | +18 |
| NM | +20 | +7 | +13 | 0 | +12 |
| NV | +4 | +4 | 0 | 0 | +11 |
| NY | +43 | +34 | +9 | 0 | +78 |
| OH | +149 | +96 | +53 | +1 | +244 |
| PA | +52 | +15 | +37 | 0 | +26 |
| RI | +2 | +2 | 0 | 0 | +8 |
| SC | +2 | 0 | +2 | 0 | 0 |
| SD | +15 | +10 | +5 | 0 | +27 |
| TN | +15 | +9 | +6 | 0 | +13 |
| UT | +27 | +16 | +11 | 0 | +19 |
| VA | +14 | +10 | +4 | 0 | +14 |
| VT | +7 | +4 | +3 | 0 | +12 |
| WI | +73 | +53 | +20 | 0 | +100 |
| WV | +10 | +5 | +5 | 0 | +10 |
| WY | +10 | +6 | +4 | 0 | +9 |
| **Total** | **+899** | **+591** | **+308** | **+1** | **+1,379** |

## Checkpoint effect and boundary

Official progress changed from 1,537/2,000 (76.9%) to 2,436/2,000
(121.8%). The workflow checkpoint is exceeded by 436 successfully
scout-covered municipalities. Broad ordinary discovery is now paused pending
an explicit user or PI decision.

No source URL was independently opened or verified. No source was ingested or
codified, no scout row became verified evidence, and no wage-gap calculation,
claim, causal claim, or regression occurred.
