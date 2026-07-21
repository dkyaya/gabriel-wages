# Serialized Parallel Stage 1 Recovery Review

Date: 2026-07-21

Disposition: **both locked batches completed and were merged once; parallel preparation plus serialized live execution is validated; parallel-live Stage 1 and Stage 2 remain unproven**

## Why serialized recovery was needed

The earlier two-worker attempts did not produce a mergeable pair. CA25.2 failed a no-search smoke, and NJ25 later passed smoke but its hosted-search run collapsed after two no-ID/no-text/no-token connection errors. A bounded follow-up showed that the same credential, direct-SDK request shape, interpreter, and packages worked 5/5 when requests were sequential. The safest evidence-based recovery was therefore one coordinator-controlled API lane: CA dry/smoke/live to completion, more than five quiet minutes, then NJ dry/smoke/live to completion.

No CA and NJ smoke or live interval overlapped. Both live runs used the direct-SDK backend, `gpt-5.4-nano`, low search context, `n_parallels=1`, 15-second spacing, a 90-second live timeout, and zero SDK retries. No wrapper scout ran.

## Worker results

| Metric | Worker 01 CA25.2 | Worker 02 NJ25 | Pooled |
| --- | ---: | ---: | ---: |
| Locked municipalities | 25 | 25 | 50 |
| Dry-run prompts passed | 25 | 25 | 50 |
| Smoke result | pass | pass | 2/2 pass |
| Live raw response rows | 25 | 25 | 50 |
| Parseable municipality outcomes | 24 | 24 | 48 |
| Parseable outcome rate | 96% | 96% | 96% |
| Candidate-positive municipalities | 24 | 12 | 36 |
| Parseable empty municipalities | 0 | 12 | 12 |
| Timeout-only failures | 1 | 1 | 2 |
| Candidate rows | 65 | 24 | 89 |
| Police candidate rows | 27 | 13 | 40 |
| Fire candidate rows | 15 | 3 | 18 |
| Non-safety candidate rows | 23 | 8 | 31 |

Fairfield CA and Princeton NJ each timed out once at approximately 90 seconds with no response ID, response text, or token record. Neither was retried. Neither counts as discovery-covered. There were no repeated connection errors, no stop-guard truncation, no JSON parser failures, and no stopped-before-request rows. All other 48 outcomes are covered: a parseable empty list counts as completed discovery, while a transport-only timeout does not.

## Usage and cost boundary

The CA live run used 801,963 input, 36,458 reasoning, 62,444 output, and 864,407 total tokens. The NJ live run used 701,097 input, 27,074 reasoning, 37,755 output, and 738,852 total tokens. Pooled live usage is 1,503,060 input, 63,532 reasoning, 100,199 output, and 1,603,259 total tokens.

Actual billed dollar cost is unavailable. The two live summaries report an explicitly estimate-only OpenAI-reference token total of `$0.42586075` (`$0.23844760` CA plus `$0.18741315` NJ). It is not confirmed Harvard HUIT billing and excludes hosted-search/tool fees, cached-input treatment, taxes, credits, discounts, and other adjustments. The two synthetic smokes each used 10 input and 6 output tokens and each recorded a separate `$0.0000095` estimate-only value.

## One coordinator merge

Only after both live artifact sets passed the eligibility audit did the coordinator update the two deterministic builders and rebuild national accounting once. The queue preserved all 451 prior rows exactly and added 65 CA25.2 plus 24 NJ25 rows, for 540 total. The queue now contains 433 later-verification rows and 107 holds/rejections.

The coverage rebuild preserved all 159 previously covered municipalities and added 48 successful outcomes, for 207 covered municipalities nationally:

- 181 candidate-positive;
- 26 parseable empty;
- seven separate failure-only municipalities; and
- 23 retained failed connection/timeout attempts, including superseded MA attempts.

State coverage is now CA 45 and NJ 27. CA has 44 candidate-positive municipalities, one parseable empty municipality, and five failure-only municipalities. NJ has 15 candidate-positive, 12 parseable empty, and one failure-only municipality. The national queue and coverage continue to preserve all prior PA, TX, MA, NJ, IL, NY, and CA results.

No URL was opened, source verified, document downloaded, source ingested, text codified, canonical contract/city coverage altered, or scout row used as claim evidence during the merge.

## Operating-mode decision

This recovery validates **parallel or isolated preparation plus one serialized smoke/live API lane**. It shows that both locked 25-row batches can complete with a 96% parseable rate when their entire API critical sections are serialized. It does not validate concurrent live workers because no live interval overlapped.

Do not move to Stage 2. Keep `n_parallels=1` and the single coordinator-controlled API lane for near-term production work. A future concurrency test would need separate authorization and a design that cannot endanger research-batch completion. Fairfield and Princeton now join the timeout-only exclusion list and should not be retried without separate authorization.
