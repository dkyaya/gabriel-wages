# Aggressive 3×300 Lane Dry-Run Review

Date: 2026-07-23/24  
Round: `POST-PI-AGGRESSIVE-ROUND-3X300-2026-07-23`

The exact three generated dry-run commands were executed against fresh isolated dry-run directories. No dry run called a backend.

| Check | Lane 1 | Lane 2 | Lane 3 |
|---|---:|---:|---:|
| locked input rows | 300 | 300 | 300 |
| prompts generated | 300 | 300 | 300 |
| exact five-hint matches | 300 | 300 | 300 |
| compact mode | yes | yes | yes |
| mixed states allowed | yes | yes | yes |
| live hard cap | 300 | 300 | 300 |
| adaptive pacing | yes | yes | yes |
| live attempted | no | no | no |
| backend returned | no | no | no |
| row-timing rows | 300 | 300 | 300 |
| timing status | `dry_run_planned` | `dry_run_planned` | `dry_run_planned` |

For all three lanes, adaptive metadata was exactly min/base/max/backoff `3/5/15/10` seconds with stability/failure windows `25/2`, and the fixed fallback sleep was five seconds.

Every locked municipality ID, municipality/state identity, employer, Census government ID, and all five row-specific hints appeared in its lane preview. All 900 prompt blocks retained:

- exact-employer and geography controls;
- police/fire and ordinary non-safety unit separation;
- safety-not-a-comparator prohibition;
- strict source/document/year evidence rules;
- explicit no-candidate guidance;
- blocked-versus-dead separation;
- duplicate controls;
- unverified scout-stage handling; and
- the public-records-request prohibition.

The identity order in each 300-row timing ledger exactly matched its locked lane input. All three dry-run gates passed.

