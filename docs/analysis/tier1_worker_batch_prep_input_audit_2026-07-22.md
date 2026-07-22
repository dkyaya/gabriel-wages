# Tier 1 Worker Batch Preparation Input Audit

Date: 2026-07-22

Starting local commit: `bbb4dfa1a0836bf3fefe4e52c5f538ee59b08714` (`Build national municipality priority tiers`). Tracked state was clean; the unrelated untracked root `package-lock.json` was reported and left untouched.

## Authoritative inputs

- `docs/analysis/national_municipality_priority_tiers_2026-07-22.csv` — full identity, score, coverage, canonical, failure, county, and eligibility authority.
- `docs/analysis/national_priority_tier_top_targets_2026-07-22.csv` — committed national rank order used for selection.
- `docs/analysis/state_priority_summary_2026-07-22.csv` — 51-state/DC strategic context; no row selection override.
- `docs/analysis/national_failure_retry_priority_2026-07-22.csv` — exact retry exclusion ledger.

The top-target file lacks the full operational-status and county fields. It was joined one-to-one to the full priority table by exact `municipality_id`; `yes`/`no` operational flags were mapped to explicit `true`/`false` strings in the new locked inputs. No fuzzy name join was used.

## Counts and filters

- Full priority rows: 35,589
- Top-target rows: 500
- Tier 1 rows in full table: 1,780
- Tier 1 future-scout eligible: 1,471
- Tier 1 ordinary eligible after excluding retries: 1,462
- Failure-only retries nationally: 10; Tier 1 failures: 9
- Ordinary eligible rows in the top-target file: 493
- Top 150 selected: 150

A row had to be Tier 1, future-scout eligible, non-retry, non-failure-only, not canonical, `not_scouted`, not candidate-positive, exactly classified as municipal/place or township/county-subdivision, and have both exact municipality and Census government IDs. Sorting was score descending, population descending with missing last, state ascending, then municipality ID ascending.

No covered/canonical row was removed from the top-target input because that file already contains only future-eligible rows; the joined full-table gate independently confirmed zero selected covered/canonical rows. The top-target file contains 7 retry rows. Six occur before source-rank 156 and were skipped: Stockton CA (rank 45); Redding CA (rank 78); Oakland CA (rank 82); Moreno Valley CA (rank 91); Oxnard CA (rank 100); Fairfield CA (rank 129).

All ten failure-ledger municipalities were excluded from ordinary selection: Stockton CA; Redding CA; Oakland CA; Moreno Valley CA; Oxnard CA; Fairfield CA; Bloomington IL; Huntley IL; Roselle IL; Princeton NJ.

## Selected-pool profile

- Missing population: 0
- State distribution: AK 1, AL 6, AR 2, AZ 11, CO 9, CT 3, DC 1, FL 15, GA 7, HI 1, IA 4, ID 1, IN 2, KS 4, KY 2, LA 3, MA 9, MD 1, MI 4, MN 4, MO 5, MS 1, NC 8, NE 2, NM 2, NV 4, OH 2, OK 3, OR 3, RI 1, SC 3, SD 1, TN 7, UT 1, VA 7, WA 6, WI 4
- Score range: 75.071–78.002
- Confidence: high 0, medium 0, low 150
- Government types: {'municipal': 150}

No live/API/model/smoke call, source opening or verification, ingestion, codification, queue/coverage change, priority-output mutation, remote action, or push occurred.
