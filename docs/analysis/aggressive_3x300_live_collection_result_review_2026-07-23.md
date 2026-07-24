# Aggressive 3×300 Live Collection Result Review

Date: 2026-07-23/24  
Round: `POST-PI-AGGRESSIVE-ROUND-3X300-2026-07-23`  
Result: stopped at the Lane 1 health gate; non-mergeable

## Gate results

- Locked-input and current-eligibility audit: passed for all 900 rows.
- Plan-only preflight: passed with zero external calls.
- Exactly one stronger live preflight: passed all three controls plus the quarantined one-row probe.
- Three lane dry runs: passed 300/300 prompts and hints per lane with no backend calls.

## Launch and stop sequence

Lane 1 was launched at `2026-07-24T01:27:37Z` using the exact generated direct-SDK command and the fresh isolated directory:

`tmp/parallel_scout_rounds/POST-PI-AGGRESSIVE-ROUND-3X300-2026-07-23/lane_1_live_direct_sdk_attempt1`

The runner started its first request at `2026-07-23T21:27:45.597415-04:00`. Newport, RI failed after 0.228 seconds with `APIConnectionError`, no response ID, no response text, and no token usage. Brookings, SD then failed after 0.002 seconds with the same no-evidence `APIConnectionError`.

The existing two-consecutive-transport-failure rule immediately:

- recorded both attempted rows as terminal `connection_error` failures;
- emitted two adaptive backoff events;
- checkpointed the remaining 298 rows as `stopped_before_request`; and
- completed the immutable failure artifacts after 11.072 seconds.

Because the required eight-minute health check failed immediately, Lane 2 and Lane 3 were not launched. Launching them would have violated the explicit “confirm no immediate widespread transport/lifecycle failure” gate. No fourth lane was launched.

## Per-lane result

| Metric | Lane 1 | Lane 2 | Lane 3 |
|---|---:|---:|---:|
| process launched | yes | no | no |
| requests attempted | 2 | 0 | 0 |
| parseable | 0 | 0 | 0 |
| candidate-positive municipalities | 0 | 0 | 0 |
| parseable-empty municipalities | 0 | 0 | 0 |
| terminal failure rows | 2 | 0 | 0 |
| stopped before request | 298 | 0 | 0 |
| candidate lead rows | 0 | 0 | 0 |
| outer timeouts | 0 | 0 | 0 |
| elapsed | 11.072 s | not started | not started |
| resume used | no | no | no |

The two failure municipalities were Newport, RI and Brookings, SD. Candidate rows by lane and by state are zero. The only attempted-row failures were one each in RI and SD.

Lane 1’s arithmetic attempted rate was 650.289 rows/hour because its two calls failed almost instantly; it is not meaningful throughput and must not be compared with completed scout rounds. There is no valid combined live-collection throughput because two required lanes never started and no row parsed.

## Offline lane audit

Command:

```bash
python scripts/audit_parallel_scout_lanes.py \
  --manifest docs/analysis/parallel_scout_rounds/POST-PI-AGGRESSIVE-ROUND-3X300-2026-07-23/parallel_round_manifest.json \
  --output-dir tmp/parallel_scout_rounds/POST-PI-AGGRESSIVE-ROUND-3X300-2026-07-23/post_lane_audit_attempt1
```

Classification:

- Lane 1: `failed_zero_parseable`
- Lane 2: `missing_artifacts` / not launched
- Lane 3: `missing_artifacts` / not launched
- completed municipality-ID overlap: zero
- recommendation: `do_not_merge_until_resume_or_review`

The absence of a Lane 1 candidate export is expected for a zero-parseable run. The untouched Lane 2 and Lane 3 roots contain only their required lineage notes.

## Interpretation and next action

The stronger preflight had succeeded minutes earlier, so this review does not assign a definitive provider, route, SDK, or local-network root cause. The production lane evidence establishes only an immediate pair of direct-SDK connection failures with no response evidence. The runner’s collapse and checkpoint behavior worked as designed; no indefinite lifecycle stall occurred.

No resume was authorized or attempted. Because Lane 1 has zero parseable successes, a skip-completed resume would not provide a useful evidence advantage. The safest next action is a separately authorized fresh attempt with:

1. a fresh stronger preflight;
2. fresh output directories such as `lane_<N>_live_direct_sdk_attempt2`;
3. an unchanged locked-input hash audit;
4. Lane 1 started first and required to show healthy parseable progress before Lane 2; and
5. no reuse or overwrite of any `attempt1` directory.

Nothing from this stopped collection is merge-eligible.

