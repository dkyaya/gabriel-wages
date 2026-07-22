# Tier 1 Wave 2 Worker Batch Preparation Input Audit

Date: 2026-07-22

Starting commit: `bef5077ef0d7837642fed651bd5d68a77110bacc`. Required ancestors `b6bd6b3` and `bef5077` were present. Tracked state was clean; the unrelated pre-existing untracked root `package-lock.json` was reported and left untouched.

## Files used

- `docs/analysis/national_municipality_priority_tiers_2026-07-22.csv` — stale but authoritative score/components/identity layer.
- `docs/analysis/national_priority_tier_top_targets_2026-07-22.csv` — canonical top-500 Tier 1 rank order.
- `docs/analysis/national_scout_coverage_municipality_2026-07-20.csv` — current official coverage/failure/canonical overlay after Tier 1 Wave 1.
- `docs/analysis/national_scout_candidate_queue_2026-07-20.csv` — current 1,277-row candidate queue used to reject any redundant queued municipality.
- `docs/analysis/tier1_post_tiering_top150_scout_input_2026-07-22.csv` — exact prior 150-row exclusion set.
- `docs/analysis/national_failure_retry_priority_2026-07-22.csv` — older ten-row retry evidence; current coverage adds eight later timeout-only rows.
- `docs/analysis/municipality_search_hints_2026-07-22.csv` — exact-ID deterministic query hints from `bef5077`.

## Counts and deterministic filter

- Full priority rows: 35,589
- Top-target rows: 500
- Tier 1 rows: 1,780
- Tier 1 future-scout eligible in the stale priority layer: 1,471
- Current successfully scout-covered: 646
- Current failure-only: 18
- Prior official Tier 1 Wave 1 rows excluded: 150 (99 candidate-positive, 43 parseable-empty, 8 failure-only)
- Older failure-only retry rows excluded: 10; all current failure-only rows excluded: 18
- Current ordinary eligible Tier 1 rows nationally after coverage/failure/queue/prior-wave exclusions: 1,312
- Ordinary eligible Tier 1 rows remaining in the canonical top-500 file: 343
- Selected rows: 150

Eligibility required Tier 1, stale future-eligible/nonretry/nonfailure/noncanonical status, current `not_scouted`, current noncanonical/noncorpus status, no prior-Wave-1 membership, intended municipality/township category, exact IDs, and five deterministic hints. Sorting was score descending, population descending with missing last, state, then municipality ID. No fuzzy join or ad hoc replacement was used.

Overlay exclusions observed in the top-500 pool: current_covered_or_failed=157, currently_queued=99, prior_wave_selected=150, stale_failure=7, stale_retry=7.

## Selected profile

- State distribution: AL 3, AR 2, AZ 5, CO 6, CT 4, FL 16, GA 3, IA 2, ID 3, IN 4, KS 3, LA 2, MA 9, MD 1, MI 7, MN 4, MO 4, MS 1, MT 1, NC 12, ND 1, NH 2, NM 2, NV 1, OH 6, OK 3, OR 6, PA 3, SC 3, TN 4, UT 11, VA 3, WA 10, WI 2, WV 1
- Score range: 74.436–75.067
- Confidence: high 0, medium 3, low 147
- Missing population: 0
- Source top-target rank span: 157–307

The national priority layer intentionally still reflects pre-Tier-1-Wave-1 operational status. Current coverage was therefore authoritative for exclusions; priority scores and methodology were not rebuilt or changed.

No live/API/model call, smoke, hosted-search diagnostic, URL opening, verification, ingestion, codification, queue/coverage/priority rebuild, remote inspection/action, or push occurred.
