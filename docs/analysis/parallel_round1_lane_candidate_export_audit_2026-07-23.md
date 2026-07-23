# Parallel Round 1 Lane Candidate Export Audit — 2026-07-23

Disposition: **PASS — both durable exports are byte-identical to their isolated
lane artifacts.**

| Lane | Isolated parsed-candidates artifact | Timestamped durable export | Rows | SHA-256 | Byte-identical |
|---|---|---|---:|---|---|
| 1 | `tmp/parallel_scout_rounds/POST-PI-PARALLEL-ROUND1-2026-07-23/lane_1_live_direct_sdk_attempt1/parsed_candidates.csv` | `docs/analysis/gabriel_state_source_scout_candidates_all_2026-07-23_152836.csv` | 386 | `587ba2b68169d759184bdcc4d60955a08df7295f7f86ca0ba1ea10d39ba9440a` | yes |
| 2 | `tmp/parallel_scout_rounds/POST-PI-PARALLEL-ROUND1-2026-07-23/lane_2_live_direct_sdk_attempt1/parsed_candidates.csv` | `docs/analysis/gabriel_state_source_scout_candidates_all_2026-07-23_153758.csv` | 377 | `4f1e181890ba7c55a56f27e167616530242694fb6634a345189b8e19259dbd37` | yes |

The 763 parsed lead rows include three explicit insufficient rows without a
source URL: two Shoreline, Washington unit placeholders and one Coconut Creek,
Florida comparator placeholder. The queue builder correctly excludes these
non-locator rows, so at most 760 new URL-bearing queue rows can be added. Their
municipalities still have other URL-bearing candidates and remain
candidate-positive.

Future parallel live runs should direct or suppress the runner's secondary
timestamped export so all collection artifacts stay inside their lane output
directory until the serial merge. This audit does not open or verify any URL
and does not promote any candidate into verified evidence.
