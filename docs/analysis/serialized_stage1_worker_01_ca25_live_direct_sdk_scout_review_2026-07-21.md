# Serialized Stage 1 Worker 01 CA25.2 Live Direct-SDK Scout Review

Date: 2026-07-21

Disposition: **complete and merge-eligible; all rows remain unverified scout-stage leads**

## Plain-English result

The coordinator recovered the locked CA25.2 batch through the serialized API lane. The fresh dry run passed all 25 prompt checks. The one-request synthetic preflight then returned `OK.`, a response ID, and 6 output tokens with no search/tools. Only after that success did the exact locked 25-row CA live command run.

The live process completed without connection collapse: 25 response rows were preserved, 24 contained successful parseable model output, one timed out, and 65 candidate rows parsed. The parseable-outcome rate is 24/25, or 96%. Fairfield is the sole failure; it returned `APITimeoutError: Request timed out.` after 90.056 seconds with no response ID, text, or tokens. It was not retried and does not count as source-discovery covered. The other 24 municipalities are merge-eligible because each has a parseable candidate-bearing result. There were no parseable empty candidate lists.

No source URL was opened or verified. Nothing was downloaded, ingested, codified, promoted, or used as claim evidence. The candidate handoff labels every row `unverified_scout_candidate`.

## Gate and command record

- Dry run: pass; 25 prompts; `live_attempted=false`.
- Smoke: pass; exact `Reply with OK.` prompt; no tools/search; response ID present; 10 input, 0 reasoning, 6 output, and 16 total tokens.
- Live backend: direct SDK only.
- Live run ID: `ca_2026-07-21_165516`.
- Execution status: `completed`.
- Internal parallelism: 1.
- Prompt spacing: 15 seconds.
- SDK retries: 0.
- Search context: low.

Exact live command:

```bash
.venv/bin/python scripts/gabriel_state_source_scout.py \
  --state CA \
  --municipalities-csv docs/analysis/parallel_worker_01_ca25_scout_input_2026-07-21.csv \
  --output-dir tmp/serialized_stage1_worker_01_ca25_live_direct_sdk_2026-07-21 \
  --prompt-mode minimal \
  --max-prompts 25 \
  --n-parallels 1 \
  --sleep-between-prompts 15 \
  --search-context-size low \
  --live \
  --live-backend direct-sdk \
  --direct-sdk-max-retries 0
```

## Candidate counts

| Municipality | Police | Fire | Non-safety | Total | Outcome |
| --- | ---: | ---: | ---: | ---: | --- |
| Irvine | 1 | 0 | 1 | 2 | parseable with candidates |
| Santa Ana | 2 | 0 | 1 | 3 | parseable with candidates |
| Huntington Beach | 1 | 1 | 0 | 2 | parseable with candidates |
| Glendale | 1 | 1 | 1 | 3 | parseable with candidates |
| Ontario | 1 | 1 | 1 | 3 | parseable with candidates |
| Elk Grove | 2 | 0 | 0 | 2 | parseable with candidates |
| Oceanside | 1 | 1 | 1 | 3 | parseable with candidates |
| Garden Grove | 2 | 0 | 1 | 3 | parseable with candidates |
| Corona | 1 | 1 | 1 | 3 | parseable with candidates |
| Roseville | 1 | 1 | 1 | 3 | parseable with candidates |
| Hayward | 1 | 1 | 1 | 3 | parseable with candidates |
| Sunnyvale | 1 | 0 | 1 | 2 | parseable with candidates |
| Escondido | 0 | 0 | 1 | 1 | parseable with candidates |
| Pomona | 1 | 0 | 1 | 2 | parseable with candidates |
| Fullerton | 1 | 0 | 1 | 2 | parseable with candidates |
| Torrance | 1 | 1 | 1 | 3 | parseable with candidates |
| Pasadena | 1 | 1 | 1 | 3 | parseable with candidates |
| Santa Clara | 1 | 1 | 1 | 3 | parseable with candidates |
| Clovis | 2 | 2 | 2 | 6 | parseable with candidates |
| Concord | 1 | 0 | 1 | 2 | parseable with candidates |
| Fairfield | 0 | 0 | 0 | 0 | timeout; not covered |
| Richmond | 1 | 1 | 1 | 3 | parseable with candidates |
| San Luis Obispo | 1 | 1 | 1 | 3 | parseable with candidates |
| Davis | 1 | 1 | 1 | 3 | parseable with candidates |
| Eureka | 1 | 0 | 1 | 2 | parseable with candidates |
| **Total** | **27** | **15** | **23** | **65** | **24 parseable; 1 timeout** |

## Scout-stage quality observations

The apparent three-unit sets for Glendale, Ontario, Oceanside, Corona, Roseville, Hayward, Pasadena, Santa Clara, Clovis, Richmond, San Luis Obispo, and Davis are the strongest matched-set shapes, but no employer, unit, date, execution, or source-owner claim has been verified. High-scoring individual leads include city-hosted civilian material for Davis, Fullerton, and Hayward, plus city-hosted apparent safety/civilian combinations for Corona, Hayward, and San Luis Obispo.

Visible leakage remains manageable but material:

- all 65 rows have a locator and retain `verification_status=unverified` / `promotion_status=raw_model_output`;
- 50 rows conservatively report `wrong_employer_risk=possible`; 15 report `none`; no returned row explicitly reports `high` risk;
- no obvious police/fire title was classified as `non_safety` in the parsed output;
- 63 rows are labeled qualifying and two Torrance rows are `insufficient_candidate` plus `blocked_or_unreadable=yes`;
- no row is labeled dead/unreachable, so the blocked-versus-dead distinction was preserved;
- three rows report possible duplicate risk and none reports an exact known source;
- several candidates extend beyond the 2014-2024 observation window, and Clovis police/fire, Concord police, Richmond fire, and Davis police appear to begin after 2024. These are not established in-window matched legs and must be held or down-ranked during later verification; and
- candidate volume and model labels are discovery metadata, not evidence that a complete, executed, same-cycle agreement exists.

## Usage and estimate-only cost

The live run recorded 801,963 input tokens, 36,458 reasoning tokens, 62,444 output tokens, and 864,407 total tokens. Actual billed cost is unavailable. The configured OpenAI-reference token estimate is `$0.2384476`, comprising `$0.1603926` input and `$0.0780550` output; reasoning is treated as included within output and is not charged twice. This is `estimate_only=true` and `pricing_missing_or_unconfirmed=true`: it excludes hosted-search/tool fees and is not confirmed Harvard HUIT billing.

## Artifact and merge disposition

The live directory contains the prompt preview, finalized run metadata, 25-row raw output, 65-row parsed-candidate file, one-row failure ledger, JSON/CSV cost summary, and sanitized console log. The normalized handoff is `docs/analysis/serialized_stage1_worker_01_ca25_live_direct_sdk_scout_candidates_2026-07-21.csv`.

Worker 01 is merge-eligible, but no national queue or coverage rebuild may occur unless Worker 02 NJ25 also completes with merge-eligible output. The API lane must remain quiet for at least five minutes before the NJ smoke.
