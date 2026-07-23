# Parallel Round 1 Serial Merge Queue/Coverage Update — 2026-07-23

Disposition: **PASS — both audited lanes entered national discovery accounting
through the authorized serial builder sequence.**

## Builder sequence

The coordinator invoked each requested top-level command once:

```text
python scripts/build_national_scout_candidate_queue.py
python scripts/build_national_scout_coverage_status.py
python scripts/build_scout_coverage.py
```

`build_scout_coverage.py` refreshed the cached Census universe/crosswalk and
delegated its status write to the same current-status builder, reproducing the
same 1,091-municipality result. This is a deterministic orchestrator rewrite,
not a second lane merge or a second outcome set. No live process ran.

## National deltas

| Measure | Before | After | Delta |
|---|---:|---:|---:|
| URL-bearing candidate queue rows | 1,602 | 2,362 | +760 |
| Scout-covered municipalities | 794 | 1,091 | +297 |
| Candidate-positive municipalities | 612 | 884 | +272 |
| Parseable-empty municipalities | 182 | 207 | +25 |
| Failure-only municipalities | 20 | 23 | +3 |
| Failed transport/no-response attempts retained | 36 | 39 | +3 |

The lane artifacts contain 763 parsed lead rows. Three are explicit
insufficient placeholders without a source URL—two Shoreline, Washington
unit placeholders and one Coconut Creek, Florida comparator placeholder—so
they remain outside the URL-bearing queue. The actual queue addition is 760.

After the merge, 1,892 rows are queued for later coordinated verification:
1,516 high priority, 261 medium priority, and 115 low priority. The other 470
rows remain held or rejected: 188 context-only, 153 insufficient, 119 likely
duplicates, eight already canonical holds, and two calibration rejections.
Relative to the pre-merge queue, this is +599 rows queued for later
verification and +161 held/rejected rows. These are scheduling states, not
source verification or ingestion decisions.

## Round failure-only outcomes

- Newark, Ohio (`cog_2025_209070`) — `outer_timeout`
- St. Cloud, Florida (`cog_2025_161668`) —
  `empty_response_no_response_id`
- Waterloo, Iowa (`cog_2025_207992`) — `outer_timeout`

All three remain failure-only and are excluded from successful scout coverage.

## Affected-state deltas

Columns are successful coverage, candidate-positive municipalities,
parseable-empty municipalities, failure-only municipalities, and URL-bearing
queue rows.

| State | Covered Δ | Positive Δ | Empty Δ | Failure-only Δ | Queue rows Δ |
|---|---:|---:|---:|---:|---:|
| CT | +12 | +11 | +1 | 0 | +28 |
| FL | +56 | +39 | +17 | +1 | +90 |
| IA | +5 | +5 | 0 | +1 | +15 |
| IN | +2 | +2 | 0 | 0 | +3 |
| KY | +1 | +1 | 0 | 0 | +1 |
| MA | +20 | +19 | +1 | 0 | +53 |
| MD | +3 | +3 | 0 | 0 | +7 |
| MI | +25 | +23 | +2 | 0 | +60 |
| MT | +2 | +2 | 0 | 0 | +7 |
| NE | +1 | +1 | 0 | 0 | +1 |
| NM | +6 | +6 | 0 | 0 | +12 |
| NV | +1 | +1 | 0 | 0 | +2 |
| OH | +83 | +81 | +2 | +1 | +268 |
| OR | +31 | +29 | +2 | 0 | +76 |
| RI | +3 | +3 | 0 | 0 | +10 |
| SD | +1 | +1 | 0 | 0 | +4 |
| WA | +35 | +35 | 0 | 0 | +96 |
| WI | +10 | +10 | 0 | 0 | +27 |
| **Total** | **+297** | **+272** | **+25** | **+3** | **+760** |

## Checkpoint

Progress moved from 794/2,000 (39.7%) to 1,091/2,000 (54.5%). The remaining
gap is 909 municipalities, or approximately seven comparable 150-row waves.
This is a workflow checkpoint only.

No diagnostic probe or stopped `bd5e259` artifact entered accounting. No URL
was opened or verified; no source was ingested or codified; no candidate was
promoted to evidence; and no wage-gap calculation, claim, causal analysis, or
regression occurred.
