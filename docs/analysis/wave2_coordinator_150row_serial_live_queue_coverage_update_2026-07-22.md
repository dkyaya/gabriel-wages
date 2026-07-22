# Wave 2 Coordinator Queue and Coverage Update

Date: 2026-07-22

Disposition: **complete — the merge-eligible Wave 2 discovery outcomes were added once to national accounting and dashboard JSON was refreshed.**

## Candidate queue

- Queue rows: 786 → 1,009 (**+223**)
- New URL-bearing Wave 2 rows: 223
- Rows queued for later verification: 634 → 828 (**+194**)
- Held/rejected/context-only rows: 152 → 181 (**+29**)

The 223 new rows consist of 162 high-priority, 18 medium-priority, and 14 low-priority later-verification rows; five context-only holds, 13 insufficient holds, and 11 likely-duplicate holds. By state they are CA 117, TX 28, and IL 78. All remain unverified scout-stage leads.

## Municipality accounting

- Successful scout-covered municipalities: 356 → 504 (**+148**)
- Candidate-positive municipalities: 293 → 391 (**+98**)
- Parseable-empty municipalities: 63 → 113 (**+50**)
- Failure-only municipalities: 8 → 10 (**+2**)
- Retained failed connection/timeout attempts: 24 → 26 (**+2**)
- Remaining unscouted municipalities: 35,233 → 35,085

Huntley and Roselle IL are failure-only, excluded from successful coverage, and retained as failed attempts. No retry was run.

## State deltas

| State | Covered before→after | Candidate-positive before→after | Empty before→after | Failure-only before→after | Candidate rows before→after |
|---|---:|---:|---:|---:|---:|
| CA | 94→144 (+50) | 90→135 (+45) | 4→9 (+5) | 6→6 | 234→351 (+117) |
| TX | 53→103 (+50) | 37→53 (+16) | 16→50 (+34) | 0→0 | 85→113 (+28) |
| IL | 74→122 (+48) | 68→105 (+37) | 6→17 (+11) | 1→3 (+2) | 217→295 (+78) |

## Builder execution

The candidate-queue builder completed at 1,009 rows. The first current-coverage invocation failed in memory before writing because a historical assertion still required the pre-Wave-2 total of 356; the audited guard was corrected to 504 and the successful rebuild completed. The required top-level `build_scout_coverage.py` command then refreshed the authoritative universe/crosswalk from local caches and delegated to the same current-status builder, reproducing the identical 504-municipality outputs. There was one substantive Wave 2 accounting promotion; the delegated rewrite was deterministic and introduced no second outcome set.

`scripts/build_national_scout_candidate_queue.py` now includes the Wave 2 candidate handoff. `scripts/build_national_scout_coverage_status.py` includes the locked input, the two failed IDs, the failed-attempt ledger, and state usage. Wave 1 and Wave 2 mixed-state token allocations are summed rather than overwritten.

## Dashboard refresh and stage boundary

`python scripts/build_dashboard_data.py` completed at 51 states/DC, 35,589 municipalities, 504 scout-covered municipalities, and 1,009 candidate rows. No dashboard frontend or deployment code changed.

No candidate URL was independently opened or downloaded. No source was verified, ingested, codified, promoted into canonical data, or used as claim evidence. `data/contracts.csv`, `data/city_coverage.csv`, and corpus files were not edited.
