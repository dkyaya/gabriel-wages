# Bounded Live Verification Readiness Audit

Date: 2026-07-23/24
Starting commit: `3616bae5d010c7c4b4a2e1c43f47941a93a48b64`
Disposition: **PASS — implement and test offline; do not open URLs**

## Repository and accounting gate

The tracked worktree was clean at the start. The unrelated untracked root
`package-lock.json` was reported and left untouched. Commits `3616bae` and
`98ad608` are ancestors of HEAD.

The canonical input is
`docs/analysis/national_scout_candidate_queue_2026-07-20.csv`, SHA-256
`d46b8bc3c60cbbda9b2f6f618fc447d1878d610fa1beb0924e7bafd47f965e83`.
It contains 4,726 URL-bearing candidate rows:

- high-priority scheduled: 2,825;
- medium-priority scheduled: 490;
- low-priority scheduled: 285;
- total scheduled: 3,600;
- context-only hold: 523;
- insufficient hold: 302;
- likely-duplicate hold: 291;
- already-canonical hold: 8; and
- calibration rejection: 2.

Thus 1,126 rows remain in held/context/duplicate/canonical/rejected
dispositions. They are not discarded: the full-backlog plan retains every
candidate identity. Offline normalization finds 4,609 distinct normalized
URLs, 94 exact-URL duplicate groups, and 117 linked extra rows.

The preceding 3×250 plan remains valid historical conservative planning:
three 250-row inputs, 750 high-priority candidates, and three passing dry
runs. It is conservative because it uses only 20.8% of the scheduled pool per
round and would require five scheduled rounds or seven full-backlog rounds.

## Larger profiles and runtime envelope

All profiles use three lane processes, eight bounded requests per lane, a
20-second outer row budget, 8-second connect timeout, 15-second read timeout,
five redirects, and a 10 MiB response cap.

| Profile | Rows/lane | Round rows | Expected lane runtime* | Timeout-heavy upper bound |
|---|---:|---:|---:|---:|
| `standard_500` | 500 | 1,500 | 2.1–8.4 minutes | 21.0 minutes |
| `aggressive_750` | 750 | 2,250 | 3.1–12.5 minutes | 31.3 minutes |
| `max_1000` | 1,000 | 3,000 | 4.2–16.7 minutes | 41.7 minutes |

\*The expected interval transparently assumes a two-to-eight-second average
response time and excludes coordinator launch overhead. Municipal-server
latency, blocking, and timeout concentration can push a lane toward the
timeout-heavy bound.

`aggressive_750` is the recommended first live profile: it covers 62.5% of
the scheduled pool in one round while retaining manageable checkpoint size
and a conservative eight-request lane limit. `max_1000` should be considered
only after the first live lane audit confirms stable transport, artifacts,
and checkpoint behavior.

## Risks and controls

- Slow municipal servers are contained by connect, read, and outer timeouts.
- PDFs and office documents are classified from bounded response metadata;
  the verifier does not parse them or save large full documents.
- Redirects are followed only to a five-hop cap and recorded explicitly.
- 401/403/407/429 responses are terminal blocked/forbidden outcomes.
- Exact URL duplicates keep all candidate rows while allowing one in-lane
  representative fetch and linked reuse.
- Candidate source-type labels remain preliminary. Reachability does not prove
  officialness, correct employer/unit identity, wage content, or analytical
  relevance.
- Checkpointed ledgers preserve completed and pending rows if interrupted.
- Lane artifacts must remain inside their lane output directory.

No candidate URL was opened. No network, API, model, hosted-search, live
verification, ingestion, `gabriel.codify`, wage extraction, wage-gap
calculation, claim, or regression occurred.
