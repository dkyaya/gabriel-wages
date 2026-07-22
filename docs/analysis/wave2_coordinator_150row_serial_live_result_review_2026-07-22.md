# Wave 2 Coordinator 150-Row Serialized Live Result Review

Date: 2026-07-22

Run: `all_2026-07-22_114424`

Disposition: **complete and merge-eligible, with 148 parseable outcomes and two isolated failure-only municipalities excluded from successful coverage.**

## Execution result

The coordinator ran exactly one direct-SDK live process against locked input SHA-256 `1227234e23635f6bae0d700d95ae7ac0890098c4906c106fffe3ef446b554bbf`. It used `--state ALL --allow-mixed-states`, exact max/cap 150, `n_parallels=1`, five-second spacing, 90-second timeout, and zero SDK retries.

- Locked / attempted / raw / timing rows: 150 / 150 / 150 / 150
- Newly attempted rows: 150
- Resume-skipped rows: 0
- Parseable rows: 148
- Candidate-positive municipalities: 98
- Parseable-empty municipalities: 50
- Failure-only municipalities: 2
- URL-bearing candidate rows: 223
- Stopped-before-request rows: 0
- Exit code: 0
- Lifecycle: `completed`; live process completed and backend returned

Raw and timing identity order matches the CA50→TX50→IL50 locked CSV exactly. Every parseable outcome has a response ID and positive output-token count. Protected canonical/corpus, pre-run queue/coverage, and dashboard files match their pre-live hashes.

## State result

| State | Attempted | Parseable | Candidate-positive municipalities | Parseable empty | Failure-only | Candidate rows |
|---|---:|---:|---:|---:|---:|---:|
| CA | 50 | 50 | 45 | 5 | 0 | 117 |
| TX | 50 | 50 | 16 | 34 | 0 | 28 |
| IL | 50 | 48 | 37 | 11 | 2 | 78 |
| **Total** | **150** | **148** | **98** | **50** | **2** | **223** |

All candidates remain unverified scout-stage leads. Candidate count is scheduling volume, not verification, evidence quality, ingestion readiness, or claim support.

## Isolated failures and stop-gate review

- Row 113, Huntley IL (`cog_2025_162476`): `empty_response_no_response_id`; one 502 Bad Gateway response; 58.798 seconds; no text, response ID, or tokens.
- Row 138, Roselle IL (`cog_2025_162300`): `timeout_or_capacity`; 90.050 seconds; no text, response ID, or tokens.

The failures were non-consecutive and each was followed by a parseable response. There was no repeated transport collapse, systematic schema/parser failure, stopped-before-request row, lifecycle/artifact loss, protected mutation, or secret exposure. Huntley and Roselle are excluded from successful coverage and remain failure-only.

## Timing and usage

- Total elapsed: 6,149.884 seconds (102m 29.884s)
- Total recorded sleep: 745.158 seconds (12m 25.158s)
- Average attempted-row request time: 36.026 seconds
- Median attempted-row request time: 32.066 seconds
- Effective throughput: 87.807 rows/hour
- Input tokens: 4,396,997
- Reasoning tokens: 187,734
- Output tokens: 281,748
- Total tokens: 4,678,745
- Estimate-only standard-token cost: $1.2315844
- Actual billed/HUIT/hosted-search cost: unavailable

Wave 1 took 6,937 seconds (115m 37s) at 15-second spacing and approximately 77.84 rows/hour. Wave 2 was 787.116 seconds (13m 07.116s, 11.347%) faster and about 9.97 rows/hour higher. The five-second setting removed about 1,490 scheduled seconds relative to 15-second spacing, but Wave 2 request latency was higher, so only about 787 seconds reached wall-clock savings.

Five-second pacing appeared operationally stable: 148/150 parseable, no consecutive failure collapse, and complete artifacts. This is evidence for future sequential use, not authorization for concurrency or automatic retries.

## Resume and merge decision

No resume was needed or used because the parent attempted all 150 rows, returned all 150 raw records, reached terminal `completed` status, and is merge-eligible with two isolated failures. Retrying failures would add a second live process beyond this task's one-process authorization and is intentionally deferred.

The national accounting builders may include the 148 parseable outcomes once. They must exclude Huntley and Roselle from successful coverage while retaining their failure attempts. No verification, URL opening outside hosted search, source download, ingestion, codification, canonical promotion, or claim use occurred.
