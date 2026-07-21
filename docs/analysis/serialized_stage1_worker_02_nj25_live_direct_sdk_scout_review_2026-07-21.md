# Serialized Stage 1 Worker 02 NJ25 Live Direct-SDK Scout Review

Date: 2026-07-21

Disposition: **complete and merge-eligible; all rows remain unverified scout-stage leads**

## Plain-English result

The coordinator recovered the locked NJ25 batch only after Worker 01 CA25.2 completed and the API lane stayed quiet for more than five minutes. The fresh NJ dry run passed all 25 prompt checks. Its one-request synthetic preflight returned `OK.`, a response ID, and 6 output tokens with no search/tools. Only then did the exact locked 25-row NJ live command run.

The live process completed without connection collapse: 25 response rows were preserved, 24 contained successful parseable model output, one timed out, and 24 candidate rows parsed. The parseable-outcome rate is 24/25, or 96%. Princeton is the sole failure; it returned `APITimeoutError: Request timed out.` after 90.055 seconds with no response ID, text, or tokens. It was not retried and does not count as source-discovery covered. Twelve municipalities returned candidates and twelve returned parseable empty candidate lists; both outcome types count as source-discovery coverage, while Princeton does not.

No source URL was opened or verified. Nothing was downloaded, ingested, codified, promoted, or used as claim evidence. The candidate handoff labels every row `unverified_scout_candidate`.

## Gate and command record

- Required quiet interval after CA finalization: 5 minutes 54 seconds before the NJ dry-run; longer before the NJ smoke.
- Dry run: pass; 25 prompts; `live_attempted=false`.
- Smoke: pass; exact `Reply with OK.` prompt; no tools/search; response ID present; 10 input, 0 reasoning, 6 output, and 16 total tokens.
- Live backend: direct SDK only.
- Live run ID: `nj_2026-07-21_172457`.
- Execution status: `completed`.
- Internal parallelism: 1.
- Prompt spacing: 15 seconds.
- SDK retries: 0.
- Search context: low.

Exact live command:

```bash
.venv/bin/python scripts/gabriel_state_source_scout.py \
  --state NJ \
  --municipalities-csv docs/analysis/parallel_worker_02_nj25_scout_input_2026-07-21.csv \
  --output-dir tmp/serialized_stage1_worker_02_nj25_live_direct_sdk_2026-07-21 \
  --prompt-mode minimal \
  --max-prompts 25 \
  --n-parallels 1 \
  --sleep-between-prompts 15 \
  --search-context-size low \
  --live \
  --live-backend direct-sdk \
  --direct-sdk-max-retries 0
```

## Candidate and outcome counts

| Municipality | Police | Fire | Non-safety | Total | Outcome |
| --- | ---: | ---: | ---: | ---: | --- |
| Paterson | 0 | 0 | 0 | 0 | parseable empty |
| Elizabeth | 0 | 0 | 2 | 2 | parseable with candidates |
| Princeton | 0 | 0 | 0 | 0 | timeout; not covered |
| Clifton | 0 | 0 | 0 | 0 | parseable empty |
| Bayonne | 2 | 0 | 0 | 2 | parseable with candidates |
| East Orange | 1 | 0 | 0 | 1 | parseable with candidates |
| Passaic | 0 | 0 | 0 | 0 | parseable empty |
| Union City | 0 | 0 | 0 | 0 | parseable empty |
| Vineland | 0 | 0 | 0 | 0 | parseable empty |
| Hoboken | 0 | 0 | 0 | 0 | parseable empty |
| New Brunswick | 0 | 0 | 0 | 0 | parseable empty |
| Perth Amboy | 1 | 1 | 1 | 3 | parseable with candidates |
| Plainfield | 0 | 0 | 0 | 0 | parseable empty |
| West New York | 2 | 0 | 0 | 2 | parseable with candidates |
| Hackensack | 0 | 0 | 0 | 0 | parseable empty |
| Sayreville | 0 | 0 | 0 | 0 | parseable empty |
| Linden | 0 | 0 | 0 | 0 | parseable empty |
| Fort Lee | 1 | 0 | 1 | 2 | parseable with candidates |
| Kearny | 0 | 0 | 0 | 0 | parseable empty |
| Atlantic City | 2 | 1 | 1 | 4 | parseable with candidates |
| Fair Lawn | 1 | 0 | 0 | 1 | parseable with candidates |
| Long Branch | 1 | 0 | 0 | 1 | parseable with candidates |
| Garfield | 1 | 0 | 1 | 2 | parseable with candidates |
| Rahway | 0 | 0 | 1 | 1 | parseable with candidates |
| Morristown | 1 | 1 | 1 | 3 | parseable with candidates |
| **Total** | **13** | **3** | **8** | **24** | **24 parseable; 1 timeout** |

## Scout-stage quality observations

The apparent Perth Amboy and Morristown three-unit sets and Atlantic City's police/fire/civilian shape are the strongest matched-set leads. Garfield supplies an apparent police/civilian pair. These are model-returned leads only; no employer, unit, date, execution, completeness, official ownership, or overlap claim has been verified.

Visible leakage and limitations are more substantial than candidate count alone suggests:

- all 24 candidate rows have a locator and retain `verification_status=unverified` / `promotion_status=raw_model_output`;
- 22 rows conservatively report `wrong_employer_risk=possible`; two report `none`; no row reports `high` risk;
- no obvious police/fire title was classified as `non_safety` in the parsed output;
- 19 rows are labeled qualifying, three context-only, and two insufficient;
- two rows are `blocked_or_unreadable=yes`; no row is labeled dead/unreachable, preserving the blocked-versus-dead distinction;
- one row reports possible duplicate risk and none reports an exact known source;
- only nine rows claim full-document status; 13 are partial and two blocked/unreadable;
- several candidates extend beyond 2024, while Elizabeth's two civilian rows, Rahway's civilian row, and other apparent terms begin after the observation window. These cannot be treated as in-window matched legs without later verification; and
- twelve parseable empty results are valid discovery outcomes, not proof that qualifying municipal sources do not exist.

## Usage and estimate-only cost

The live run recorded 701,097 input tokens, 27,074 reasoning tokens, 37,755 output tokens, and 738,852 total tokens. Actual billed cost is unavailable. The configured OpenAI-reference token estimate is `$0.18741315`, comprising `$0.1402194` input and `$0.04719375` output; reasoning is treated as included within output and is not charged twice. This is `estimate_only=true` and `pricing_missing_or_unconfirmed=true`: it excludes hosted-search/tool fees and is not confirmed Harvard HUIT billing.

## Artifact and merge disposition

The live directory contains the prompt preview, finalized run metadata, 25-row raw output, 24-row parsed-candidate file, one-row failure ledger, JSON/CSV cost summary, and sanitized console log. The normalized handoff is `docs/analysis/serialized_stage1_worker_02_nj25_live_direct_sdk_scout_candidates_2026-07-21.csv`.

Worker 02 is merge-eligible. Because Worker 01 is also complete and merge-eligible, the coordinator may now perform exactly one national candidate-queue and scout-coverage rebuild. Princeton and CA Fairfield must remain failure-only and excluded from discovery coverage.
