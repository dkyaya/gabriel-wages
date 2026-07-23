# Tier 1 Wave 2 queue and coverage update — 2026-07-22

## Decision and boundary

The complete Tier 1 Wave 2 output was merge-eligible. The successful national build incorporates only run `all_2026-07-22_195226`; the preflight probe, stopped historical attempts, Joplin failure, Framingham failure, and two locator-less Spokane Valley placeholders are excluded from successful/URL-bearing accounting as appropriate.

No source URL was opened or verified. No contract was downloaded or ingested. No codification, canonical promotion, protected CSV edit, corpus edit, or claim use occurred.

## National deltas

| Metric | Before | After | Delta |
|---|---:|---:|---:|
| Candidate queue rows | 1,277 | 1,602 | +325 |
| Successful scout-covered municipalities | 646 | 794 | +148 |
| Candidate-positive municipalities | 490 | 612 | +122 |
| Parseable-empty municipalities | 156 | 182 | +26 |
| Failure-only municipalities | 18 | 20 | +2 |
| Remaining not scouted | 34,925 | 34,775 | −150 |
| Retained failed attempts excluded from coverage | 34 | 36 | +2 |

The live parser produced 327 candidate records. Exactly 325 had locators and entered the national source queue. Two locator-less Spokane Valley insufficient records were held outside the queue.

## New queue triage

| New Wave 2 triage bucket | Rows |
|---|---:|
| High-priority later verification | 195 |
| Medium-priority later verification | 32 |
| Low-priority later verification | 13 |
| Context-only hold | 42 |
| Insufficient hold | 19 |
| Likely-duplicate hold | 24 |
| Total URL-bearing rows | 325 |

Rows queued for later coordinated verification: 240. Rows held as context-only, insufficient, or likely duplicate: 85. These are scheduling labels only; none is verified or ingestion-ready.

## State coverage deltas

| State | Successful + | Positive + | Empty + | Failure-only + | Successful after |
|---|---:|---:|---:|---:|---:|
| AL | 3 | 2 | 1 | 0 | 9 |
| AR | 2 | 2 | 0 | 0 | 3 |
| AZ | 5 | 5 | 0 | 0 | 15 |
| CO | 6 | 5 | 1 | 0 | 15 |
| CT | 4 | 4 | 0 | 0 | 7 |
| FL | 16 | 14 | 2 | 0 | 30 |
| GA | 3 | 3 | 0 | 0 | 10 |
| IA | 2 | 2 | 0 | 0 | 6 |
| ID | 3 | 2 | 1 | 0 | 4 |
| IN | 4 | 4 | 0 | 0 | 4 |
| KS | 3 | 3 | 0 | 0 | 7 |
| LA | 2 | 1 | 1 | 0 | 5 |
| MA | 8 | 7 | 1 | 1 | 25 |
| MD | 1 | 1 | 0 | 0 | 2 |
| MI | 7 | 6 | 1 | 0 | 11 |
| MN | 4 | 3 | 1 | 0 | 8 |
| MO | 3 | 2 | 1 | 1 | 7 |
| MS | 1 | 1 | 0 | 0 | 2 |
| MT | 1 | 1 | 0 | 0 | 1 |
| NC | 12 | 7 | 5 | 0 | 20 |
| ND | 1 | 1 | 0 | 0 | 1 |
| NH | 2 | 2 | 0 | 0 | 2 |
| NM | 2 | 2 | 0 | 0 | 4 |
| NV | 1 | 1 | 0 | 0 | 4 |
| OH | 6 | 6 | 0 | 0 | 8 |
| OK | 3 | 2 | 1 | 0 | 6 |
| OR | 6 | 6 | 0 | 0 | 9 |
| PA | 3 | 1 | 2 | 0 | 28 |
| SC | 3 | 1 | 2 | 0 | 6 |
| TN | 4 | 3 | 1 | 0 | 11 |
| UT | 11 | 7 | 4 | 0 | 12 |
| VA | 3 | 3 | 0 | 0 | 10 |
| WA | 10 | 10 | 0 | 0 | 15 |
| WI | 2 | 2 | 0 | 0 | 6 |
| WV | 1 | 0 | 1 | 0 | 1 |

## Build audit

The builders use explicit accepted-run lists and fail-closed assertions. Two queue-builder attempts stopped before writing while its historical state-count and missing-locator expectations were updated. The next queue pass wrote the audited 1,602-row output. Coverage then stopped before writing at its historical 646-total assertion; after updating that assertion to the audited 794 total, the requested coverage builders completed successfully. These guard stops are retained in task evidence; no stale or partially accepted coverage product was treated as final.

Final successful outputs parse back with unique queue IDs, the 35,589-row authoritative municipality universe, 51 state/DC rows, and current county associations. The production queue source is the dated Wave 2 handoff `docs/analysis/gabriel_state_source_scout_candidates_all_2026-07-22_195226.csv`, which is byte-identical to the live run's parsed candidate artifact.
