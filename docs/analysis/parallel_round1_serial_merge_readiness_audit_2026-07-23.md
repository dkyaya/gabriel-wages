# Parallel Round 1 Serial Merge Readiness Audit — 2026-07-23

Disposition: **PASS — serial accounting merge authorized.**

## Repository and lineage gate

- Commit before work: `42dbe6716a88be2cb2113b245bd7733fa27f4be1`.
- Current HEAD descends from `42dbe67`, `4ee7015`, `3a7d762`, and `6db14f0`.
- Tracked worktree before work: clean.
- Unrelated untracked item reported and left untouched: root `package-lock.json`.
- Parallel round: `POST-PI-PARALLEL-ROUND1-2026-07-23`.

## Fresh offline lane audit

Exact command used:

```text
python scripts/audit_parallel_scout_lanes.py --manifest docs/analysis/parallel_scout_rounds/POST-PI-PARALLEL-ROUND1-2026-07-23/parallel_round_manifest.json --output-dir tmp/parallel_scout_rounds/POST-PI-PARALLEL-ROUND1-2026-07-23/lane_audit_for_merge_2026-07-23_attempt1
```

The implemented auditor reads lane output paths from the manifest, so it does
not accept or require the prompt's suggested `--lane-output-root` argument.

| Gate | Lane 1 | Lane 2 |
|---|---:|---:|
| Classification | `completed_merge_eligible` | `completed_merge_eligible` |
| Input SHA-256 valid | yes | yes |
| Attempted | 150 | 150 |
| Parseable | 148 | 149 |
| Candidate-positive municipalities | 137 | 135 |
| Parseable empty | 11 | 14 |
| Failure-only | 2 | 1 |
| Candidate lead rows | 386 | 377 |
| Stopped before request | 0 | 0 |
| Pending timing rows | 0 | 0 |

Lane 1 input SHA-256 is
`56e592291f1dbac83836acddcf0065df40141b51f9e93bfb548a040f52b8e700`.
Lane 2 input SHA-256 is
`f381ce60c362a78561250b08b66ba32822fc583b86892b04fbb24b3a6a7b998d`.
Completed municipality-ID overlap is zero. The fresh recommendation is
`merge_all_lanes`.

The three terminal failure-only rows are Newark, Ohio
(`cog_2025_209070`, `outer_timeout`), St. Cloud, Florida
(`cog_2025_161668`, `empty_response_no_response_id`), and Waterloo, Iowa
(`cog_2025_207992`, `outer_timeout`). They remain outside successful coverage.

## Accounting boundary

The prior live-collection task did not run queue, coverage, yield, dashboard,
or priority builders. The diagnostic one-row probe remains quarantined. The
stopped `bd5e259` output remains quarantined and non-evidence. This merge reads
only the two audited timestamped candidate exports, the two locked lane inputs,
and the terminal failure ledger identified above.

The gates therefore authorize one serial accounting-builder sequence. No live
call, hosted search, source verification, ingestion, codification, wage-gap
calculation, or regression is authorized or performed by this audit.
