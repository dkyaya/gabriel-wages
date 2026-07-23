# Tier 1 Wave 2 coordinator 150-row live result review — 2026-07-22

## Decision

PASS; merge-eligible. The one authorized full process completed all 150 serialized requests using direct SDK, compact prompts, exact-ID deterministic hints, and adaptive pacing. It returned 148 parseable outcomes, 122 candidate-positive municipalities, 26 parseable-empty municipalities, two isolated failure-only rows, and no `stopped_before_request` rows. No resume was needed or run.

All output remains unverified scout-stage discovery data. Nothing in this review verifies a URL, employer, bargaining unit, document, date, wage term, cycle match, or causal claim.

## Lineage and gates

- Worker relays: `9395a4c`, `37125c7`, and `6ae1267`; all offline prep evidence passed.
- Coordinator input SHA-256: `f530932c487cef73aae6d18f19e477697c2b2cfbd85dfd8226e608723d7e750e`.
- Rank/order: exact Tier 1 Wave 2 ranks 151–300, Worker 1 then Worker 2 then Worker 3.
- Stronger preflight: PASS; plan-only made zero calls, then the one bounded live gate passed no-search, two hosted-search controls, and the one-row production-runner probe.
- Probe quarantine: the Coral Springs probe is excluded from this run and national accounting. Its handoff remains under the probe `tmp/` directory.
- Coordinator dry run: PASS, 150/150 compact prompts, 150/150 five-hint matches, 150/150 identity/guardrail/schema checks, zero backend calls.
- Official output: `tmp/tier1_wave2_coordinator_150row_serial_live_direct_sdk_2026-07-22_attempt1/`.
- Run ID: `all_2026-07-22_195226`.
- Backend returned and lifecycle completed: yes; `execution_status=completed`, exit 0.

## Outcome accounting

| Measure | Result |
|---|---:|
| Attempted / responses | 150 / 150 |
| Parseable | 148 |
| Candidate-positive municipalities | 122 |
| Parseable-empty municipalities | 26 |
| Failure-only municipalities | 2 |
| Stopped before request | 0 |
| Parsed candidate records | 327 |
| URL-bearing queue-eligible records | 325 |
| Locator-less insufficient records held outside queue | 2 |
| Resume used | No |

The two locator-less records are insufficient police/fire placeholders for Spokane Valley, Washington. Spokane Valley also has URL-bearing records and remains candidate-positive; the two empty-locator records are not inserted into the national source queue.

## Failure-only rows

- Row 56: Joplin, Missouri (`cog_2025_194606`, Worker 2), `connection_error`, 18.610 seconds, no response ID/text/tokens.
- Row 60: Framingham, Massachusetts (`cog_2025_106133`, Worker 2), `empty_response_no_response_id`, 21.295 seconds, no response ID/text/tokens.

The failures were isolated and separated by three successful parseable rows. They did not meet the two-consecutive collapse condition. Both are excluded from successful coverage and retained as separate future retry targets; neither is evidence that a municipal source does not exist.

## Candidate rows and positive municipalities by state

| State | Candidate rows | Positive municipalities |
|---|---:|---:|
| AL | 5 | 2 |
| AR | 6 | 2 |
| AZ | 9 | 5 |
| CO | 10 | 5 |
| CT | 14 | 4 |
| FL | 39 | 14 |
| GA | 5 | 3 |
| IA | 6 | 2 |
| ID | 5 | 2 |
| IN | 8 | 4 |
| KS | 11 | 3 |
| LA | 2 | 1 |
| MA | 22 | 7 |
| MD | 2 | 1 |
| MI | 19 | 6 |
| MN | 6 | 3 |
| MO | 5 | 2 |
| MS | 2 | 1 |
| MT | 3 | 1 |
| NC | 14 | 7 |
| ND | 1 | 1 |
| NH | 6 | 2 |
| NM | 7 | 2 |
| NV | 3 | 1 |
| OH | 18 | 6 |
| OK | 7 | 2 |
| OR | 21 | 6 |
| PA | 1 | 1 |
| SC | 2 | 1 |
| TN | 6 | 3 |
| UT | 15 | 7 |
| VA | 6 | 3 |
| WA | 35 | 10 |
| WI | 6 | 2 |
| WV | 0 | 0 |

## Outcomes by worker

| Worker | Parseable | Positive | Empty | Failure-only | Parsed candidates |
|---|---:|---:|---:|---:|---:|
| Worker 1 (151–200) | 50 | 45 | 5 | 0 | 127 |
| Worker 2 (201–250) | 48 | 39 | 9 | 2 | 96 |
| Worker 3 (251–300) | 50 | 38 | 12 | 0 | 104 |

## Runtime and adaptive pacing

- Wall time: 5,738.638 seconds (95m38.638s).
- Effective throughput: 94.099 attempted rows/hour.
- Average/median backend elapsed per attempted row: 31.275/29.223 seconds.
- Actual/planned sleep: 1,046.214/1,046.000 seconds.
- Actual adaptive sleep levels: min 3.0, median 7.5, max 10.0 seconds.
- Pacing events: 144 stable holds, five stable step-downs, one backoff.
- The single connection error stepped pacing to 10 seconds. Subsequent 25-row stable windows stepped it down through 9, 8, and 7 seconds by run end.
- No two-consecutive transport failure occurred; compact/hints/adaptive execution was operationally stable.

Runtime comparisons:

| Prior run | Runtime | This run faster by | Relative improvement |
|---|---:|---:|---:|
| Coordinator Wave 1 | 6,937.000s | 1,198.362s (19m58.362s) | 17.28% |
| Coordinator Wave 2 | 6,149.884s | 411.246s (6m51.246s) | 6.69% |
| Tier 1 Wave 1 | 6,723.519s | 984.881s (16m24.881s) | 14.65% |

## Usage, cost, and compact-prompt comparison

- Input/reasoning/output/total tokens: 4,335,653 / 182,344 / 315,479 / 4,651,132.
- Average input tokens per attempted row: 28,904.353.
- Estimate-only standard text-token cost: `$1.26147935`; actual HUIT, hosted-search, and tool billing remains unavailable.
- The compact template’s offline representative character/token proxy was 36.09% shorter than minimal. Actual hosted-search input usage was 77,297 tokens (1.82%) higher than Tier 1 Wave 1’s 4,258,356, or about 515 more input tokens per attempted row. Search-result/tool context and deterministic hints are included in the SDK usage, so this full-run comparison does not isolate prompt-template tokens.
- Output tokens rose 2.07%, reasoning tokens fell 7.41%, and total tokens rose 1.83% versus Tier 1 Wave 1.

The speed gain therefore cannot be credited to lower measured input tokens alone. Lower backend elapsed, different municipalities/search results, and adaptive timing all contribute. Adaptive sleep actually added about 301 seconds relative to Tier 1 Wave 1’s 745.208 seconds, yet the overall run still finished 984.881 seconds faster.

## Yield comparison

- Candidate-positive rate among parseable municipalities: 82.43%.
- Parsed candidates per parseable municipality: 2.209.
- Parsed candidate rows/hour: 205.136.
- Prior candidate densities were 1.651 (Wave 1), 1.507 (Wave 2), and 1.887 (Tier 1 Wave 1).

Tier 1 Wave 2 improved both candidate density and candidate-positive rate over the prior reviewed waves. This supports the operational usefulness of Tier 1 targeting and hints, but it does not establish source quality: all records still require coordinated source verification.

## Merge eligibility and limitations

The run is merge-eligible because all 150 requests reached terminal status; 148 have parseable responses; the two failures are isolated and explicitly excluded; all lifecycle, prompt, timing, raw, parsed, failure, and usage artifacts are present; and protected files remained unchanged. No resume was needed because the process completed in one attempt.

Limitations include unverified sources, model/search variability, two non-URL insufficient placeholders, estimate-only cost, inability to separate prompt-template tokens from hosted-search context in usage totals, and adaptive recovery that stayed above its base after the single backoff. No source verification, ingestion, codification, canonical promotion, or claim use occurred.
