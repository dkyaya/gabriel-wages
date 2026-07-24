# Future 2×2000 Verification Scaling Readiness

Date: 2026-07-24

## Decision

**READY FOR FUTURE ROUTING-ONLY USE.** The bounded verifier and its planner,
auditor, and serial merge layer can support a two-lane profile with up to
2,000 candidate URL rows per lane. The profile is not a new round for the
current queue. Current routing is complete, so the planner produces a zero-row
no-work sentinel when the cumulative ledger is supplied.

Work began at commit
`e028432c3fd00117d9419ace6cd1ca36e4320f5d`. The tracked worktree was clean;
the unrelated untracked root `package-lock.json` was reported and left
untouched. `HEAD` includes `e028432`, `e86abf7`, `2bab4b0`, `ee7041a`,
`3616bae`, and `98ad608`.

## Sources inspected

- Canonical candidate queue:
  `docs/analysis/national_scout_candidate_queue_2026-07-20.csv`
- Round 1 durable ledger:
  `docs/analysis/verification_ledgers/VERIFICATION-SCALE-ROUND1-3X750-2026-07-23/verified_source_routing_ledger.csv`
- Round 2 durable ledger:
  `docs/analysis/verification_ledgers/VERIFICATION-SCALE-ROUND2-3X1000-REMAINDER-2026-07-24/verified_source_routing_ledger.csv`
- Project-wide cumulative/latest ledger and summary:
  `docs/analysis/verification_ledgers/verified_source_routing_ledger_cumulative.csv`
  and
  `docs/analysis/verification_ledgers/verified_source_routing_summary_cumulative.json`
- Round 1 and Round 2 live collection reviews, serial merge results,
  dashboard refreshes, validation records, and the post-routing transition
  plan named in the task.
- Verification planner, bounded verifier, lane auditor, cumulative merge
  script, offline/mock tests, and dashboard builder.

## Current completed routing state

- URL-bearing candidate identities: **4,726**
- Durable routing rows: **4,726**
- Routing coverage: **100%**
- Reachable or successfully reused: **3,750 / 4,726 (79.3483%)**
- Logical URL opens across prior authorized live rounds: **4,628**
- Duplicate reuse/link rows: **98**
- Unrouted current-queue identities: **0**

| Cumulative routing status | Rows |
|---|---:|
| `reachable_pdf_or_document` | 3,533 |
| `reachable_html` | 145 |
| `reachable_http` | 2 |
| `duplicate_of_verified_source` | 70 |
| `duplicate_same_url_pending` | 28 |
| `blocked_or_forbidden` | 339 |
| `not_found` | 264 |
| `too_large` | 261 |
| `error` | 45 |
| `ssl_error` | 17 |
| `timeout` | 14 |
| `connection_error` | 8 |

These are routing and response-metadata outcomes, not content relevance,
employer/unit validation, ingestion, or wage evidence.

## Observed throughput

Round 1 used three 750-row lanes:

| Lane | Runtime | Rows/hour |
|---|---:|---:|
| 1 | 130.782 s | 20,645.059 |
| 2 | 107.948 s | 25,011.945 |
| 3 | 96.105 s | 28,094.183 |

The overlapping Round 1 wall interval was 260.782 seconds for 2,250 rows,
or 31,060.438 selected rows/hour. That interval includes staged launch
spacing.

Round 2 used balanced 826/825/825-row lanes:

| Lane | Rows | Runtime | Rows/hour |
|---|---:|---:|---:|
| 1 | 826 | 143.756 s | 20,685.094 |
| 2 | 825 | 130.393 s | 22,777.341 |
| 3 | 825 | 113.560 s | 26,153.526 |

The overlapping Round 2 wall interval was 260.016 seconds for 2,476 rows,
or 34,280.976 selected rows/hour.

At the observed per-lane range, 2,000 lightweight routing rows project to
approximately 4.3–5.8 minutes of active lane runtime. Allowing for launch
health checks, filesystem variation, and a slower URL mix, a prudent planning
range is **6–10 minutes of wall time** for two healthy lanes. This is not a
service-level guarantee. The deterministic timeout-heavy mathematical bound
is much larger.

## Why 2×2000 is plausible

- The live path performs bounded reachability and response-metadata routing,
  not PDF parsing or wage extraction.
- It uses concurrency eight per lane, fixed connection/read/total timeouts,
  a 10 MiB ceiling, no environment proxy/auth inheritance, and no content
  samples.
- Atomic checkpoint ledgers preserve terminal work after each URL group.
- Duplicate URL groups use one representative fetch within a lane while every
  candidate identity remains in the ledger.
- Both prior rounds completed with high throughput, complete terminal
  ledgers, small metadata artifacts, and clean audit recommendations.
- Synthetic 4,000-row planning, two 2,000-row dry runs, two-lane audit, and
  two-lane serial merge tests pass offline.

The bounded verifier itself required no code change. Inspection confirms
incremental atomic ledger/timing/summary checkpoints, terminal row statuses,
explicit resume plus skip-completed controls, in-lane duplicate reuse,
lane-local artifact confinement, deterministic sanitized artifact names,
disabled-by-default content samples, no full-document saving, per-lane
summaries/status/artifact counts, and bounded in-memory state for a 2,000-row
lane. The auditor was tightened to fail on missing or out-of-lane live
artifact references and to recognize a zero-lane no-work sentinel.

## Why it is not a content-processing profile

Content triage, document download, PDF parsing, OCR, source rating, employer
and bargaining-unit validation, and wage extraction have materially different
CPU, memory, storage, licensing, and review risks. Two 2,000-row lanes would
make those heavier failure and review units unnecessarily large. Use smaller
lanes and task-specific storage limits once bytes, documents, or judgments
enter the workflow.

## Risk comparison

| Profile | Capacity | Strength | Main risk |
|---|---:|---|---|
| 3×750 | 2,250 | Smallest restart/audit unit among scaled profiles | More lane coordination |
| 3×1000 | 3,000 | Proven lower-risk high-throughput fallback | Three concurrent processes and artifact roots |
| 2×2000 | 4,000 | Fewer processes and maximum routing throughput | Each failure or resume affects up to 2,000 identities |

Specific 2×2000 risks:

- larger per-lane resume and reconciliation burden;
- larger lane artifact and identity audit;
- one failed lane can withhold half of a 4,000-row round;
- correlated server throttling under two sustained lanes;
- several thousand metadata artifacts and multi-megabyte ledgers;
- exact duplicate groups may be split only if a group exceeds lane capacity;
- dashboard readers may mistake “routing complete” for “content verified.”

## Recommendation

- Support `bulk_2x2000` for **future unrouted URL queues only**.
- Begin at concurrency eight per lane. Consider 10–12 only after explicit
  operator approval and a new bounded dry/live gate.
- Keep `max_1000` (3×1000) as the lower-risk default/fallback.
- Use smaller lanes for content triage, downloads, parsing, extraction,
  rating, ingestion, codification, or analysis.
- Do not schedule a bulk round for the current 4,726-row queue.

No URL was opened and no live verification, network/API/model/hosted-search
call, scout, ingestion, codification, wage extraction, wage-gap calculation,
causal analysis, or regression occurred in this readiness task.
