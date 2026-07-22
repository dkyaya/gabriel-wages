# Wave 2 3×50 Batch Selection Audit

Date: 2026-07-22

Disposition: **CA50, TX50, and IL50 are locked for offline worker preparation only. No smoke, live scout, API/model call, hosted search, URL opening, verification, ingestion, codification, queue/coverage rebuild, or dashboard mutation occurred.**

## Repository and source-of-truth gate

Work began at local commit `67c2c5d8e40e932a5d79ab116a518fb7f02ed91b` (`Add scout pacing and resume safeguards`). It is a descendant of both `943a458` (dashboard/live-result consolidation) and `67c2c5d` (pace/resume safeguards). The tracked worktree was clean; the pre-existing untracked root `package-lock.json` was reported and left untouched.

The filenames ending in `2026-07-20` remain the current canonical queue and municipality-coverage outputs. This was not guessed: `scripts/build_national_scout_candidate_queue.py` writes `national_scout_candidate_queue_2026-07-20.csv`, while `scripts/build_national_scout_coverage_status.py` reads that queue and writes `national_scout_coverage_municipality_2026-07-20.csv`, `national_scout_coverage_state.csv`, and `national_scout_coverage_county.csv`. All four were last rebuilt through the successful 2026-07-21 coordinator merge.

Selection used:

- employer universe: `docs/analysis/national_municipality_universe.csv`;
- county relationships: `docs/analysis/national_municipality_county_crosswalk.csv`;
- current municipality coverage: `docs/analysis/national_scout_coverage_municipality_2026-07-20.csv`;
- current state/county summaries: `docs/analysis/national_scout_coverage_state.csv` and `docs/analysis/national_scout_coverage_county.csv`;
- current candidate queue: `docs/analysis/national_scout_candidate_queue_2026-07-20.csv`;
- canonical municipality context: `data/contracts.csv` and `data/city_coverage.csv`; and
- operating evidence: the coordinator live/merge reviews and pace/resume documents named in the task.

No external or live source was consulted.

## Current national and state position

The current municipality output contains all 35,589 authoritative universe rows. It records 356 successfully scout-covered municipalities, 293 candidate-positive municipalities, 63 parseable-empty municipalities, eight failure-only municipalities, 24 excluded connection/timeout attempts, and 35,233 remaining unscouted municipalities. The candidate queue has 786 URL-bearing, still-unverified rows.

| State | Universe | Not scouted | Covered | Candidate-positive | Empty | Failure-only | Positive rate | Candidate rows | Rows per covered | Later-verification rows |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| CA | 483 | 383 | 94 | 90 | 4 | 6 | 95.7% | 234 | 2.489 | 210 |
| TX | 1,224 | 1,171 | 53 | 37 | 16 | 0 | 69.8% | 85 | 1.604 | 75 |
| IL | 2,719 | 2,644 | 74 | 68 | 6 | 1 | 91.9% | 217 | 2.932 | 182 |
| NY | 1,523 | 1,498 | 25 | 21 | 4 | 0 | 84.0% | 57 | 2.280 | 48 |
| NJ | 564 | 486 | 77 | 46 | 31 | 1 | 59.7% | 94 | 1.221 | 59 |
| MA | 351 | 343 | 8 | 8 | 0 | 0 | 100.0% | 24 | 3.000 | 13 |
| PA | 2,557 | 2,532 | 25 | 23 | 2 | 0 | 92.0% | 75 | 3.000 | 47 |

The queue row counts by these states are the same as `candidate_rows` above and sum to the current national total when combined with the other covered states.

## State decision

### Worker 1 — California

California remains the strongest scaled discovery state: 90 of 94 successful municipalities are candidate-positive, with 234 queue rows. Its first 94 covered municipalities exhausted the largest-city tiers, but 383 eligible places remain. The next 50 population-ranked places still range from 84,782 to 60,015 residents and span 20 counties, supporting another high-value employer-scale expansion without reusing a covered or failed row.

### Worker 2 — Texas

Texas has a lower positive rate than CA or IL, but the state remains strategically valuable for the project’s institutional contrast and matched-non-safety source gap. Only 53 of 1,224 municipalities are covered. The next 50 population-ranked municipal places range from 77,516 to 35,741 residents, include 18 multi-county employers and 31 counties, and extend beyond the first large-city wave. An empty result is acceptable; the scout must not substitute school, county, advisory, authority, special-district, or private-provider material for an exact municipal employer.

### Worker 3 — Illinois

Illinois is selected over New York. Its evidence base is larger and its yield is stronger: 68/74 candidate-positive (91.9%) and 2.932 candidate rows per covered municipality, versus New York’s 21/25 (84.0%) and 2.280. Illinois also has 50 clean unscouted municipal/place rows immediately available after 74 covered municipalities and Bloomington are excluded. The batch reaches a smaller suburban/local-employer tier, so yield may decline, but the observed evidence supports IL as the cleaner Wave 2 discovery choice.

## Alternatives deferred

- **New York:** still a good future state and preferred over repeating New Jersey, but its smaller 25-municipality evidence base and lower observed yield do not beat Illinois for this wave.
- **New Jersey:** deferred because its latest 50-row expansion produced 31 candidate-positive and 19 empty results; overall positive yield is 59.7%, below CA, IL, NY, and PA. Broader NJ work should wait for national tiering or a targeted exact-employer hypothesis.
- **Pennsylvania:** its 92.0% rate and three rows per covered municipality are promising, but they come from only 25 covered municipalities. Illinois offers nearly the same rate across 74 covered municipalities and therefore a more stable basis for the third lane.
- **Massachusetts:** 8/8 is encouraging but too small to extrapolate, and the authoritative universe includes many county-subdivision town governments that are outside this task’s `municipal/place` gate.

## Deterministic eligibility and exclusion audit

`scripts/build_wave2_3x50_batches.py` requires every selected row to satisfy all of the following:

1. state is the assigned CA, TX, or IL state;
2. `active_status=Y`, `government_type=municipal`, and `geography_type=place` in the authoritative universe;
3. current `scout_coverage_status=not_scouted`, `failed_connection_attempt_count=0`, and `queue_status=not_scouted`;
4. neither universe nor current coverage marks the municipality as already in corpus;
5. current canonical-overlap status is `not_already_ingested_canonical`;
6. municipality ID and exact state/name are absent from the current queue;
7. exact state/name is absent from both canonical contracts and canonical city coverage;
8. the municipality is not Bloomington, Oakland, Stockton, Oxnard, Redding, Fairfield, Princeton, or Moreno Valley; and
9. all county relationships reconcile to the universe count and Census government ID.

Eligible rows are ordered by descending 2023 population, then municipality name and municipality ID. The first 50 are locked. Independent assertions prove 50 rows per worker, one state/worker/queue ID per file, 150 unique municipality IDs, 150 unique Census government IDs, only `municipal/place`, all `not_scouted`, complete crosswalk joins, and zero forbidden-name overlap.

The selected files have exact SHA-256 values:

- CA50: `f8b0e99e0a7343d3efacf3829325cb86db7b775814e933af21dacbbc0069f123`;
- TX50: `d393601295ea86ab9a52e712bff0c7cc9cf7e0977e97793c134a6b1c02af4c6f`; and
- IL50: `2257832562c87f76cdcbb6ec7efb5793034bc9d6484d39fd90bde05b7bb1c28b`.

No already-covered, canonical, current-queue, failure-only, or prohibited-employer row is selected. The named timeout-only rows are deferred rather than mixed into a fresh-discovery wave. In particular, Moreno Valley remains an isolated historical failure and is not automatically retried through the new resume system.

## Discovery value and boundary

The wave prioritizes larger remaining exact municipal employers within three empirically useful states. Using current state averages as a rough—not guaranteed—planning reference implies about 48 CA, 35 TX, and 46 IL candidate-positive municipalities and roughly 124, 80, and 147 candidate rows respectively. Because the new batches move down each state’s population distribution, a more cautious pooled planning range is 108–132 candidate-positive municipalities and 260–360 candidate rows.

These are selection expectations only. Every future result remains an unverified scout-stage lead. The preparation task does not establish that any agreement exists, is official, covers the selected employer/unit/cycle, contains wage evidence, avoids duplication, or is suitable for ingestion or claim use.
