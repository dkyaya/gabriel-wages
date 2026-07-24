# Aggressive 3×300 Attempt 3 Lane Dry-Run Review

Date: 2026-07-23/24

| Check | Lane 1 | Lane 2 | Lane 3 |
|---|---:|---:|---:|
| prompts generated | 300 | 300 | 300 |
| compact mode | yes | yes | yes |
| exact hint matches | 300 | 300 | 300 |
| mixed states allowed | yes | yes | yes |
| live hard cap | 300 | 300 | 300 |
| adaptive sleep | yes | yes | yes |
| live attempted | no | no | no |
| backend returned | no | no | no |
| timing rows | 300 | 300 | 300 |
| timing state | `dry_run_planned` | `dry_run_planned` | `dry_run_planned` |

Every lane preserved exact locked identity order. Every municipality ID, municipality/state, government name, Census government ID, and all five row-specific hints appeared in its preview.

All 900 prompts retained the exact-employer, safety/non-safety, source/document/year, no-candidate, blocked/dead, duplicate, unverified-stage, and public-records-request controls. Adaptive metadata is exactly min/base/max/backoff `3/5/15/10` with stability/failure windows `25/2`; fixed fallback sleep is five seconds.

All dry-run gates passed without an API/model/backend call.

