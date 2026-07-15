# GABRIEL Statewide Source Scout — Timeout/Retry Stress Test Summary (2026-07-15)

**Scope:** third iteration of `scripts/gabriel_state_source_scout.py` tuning. Adds `--timeout`, `--max-timeout`, `--sleep-between-prompts`, `--retry-failed-from`, and `--prompt-mode full|minimal`; runs one live test against the 6 Pennsylvania municipalities still failing after the 2026-07-14 pilot and retry (Reading, Scranton, Bethlehem, Lancaster, Harrisburg, York). Still source-scouting/staging only — no ingestion, no `data/contracts.csv`/`data/city_coverage.csv`/corpus/claim-evidence edits, no `gabriel.codify()` call.

## What changed in the script

1. **New CLI controls**: `--timeout SECONDS` / `--max-timeout SECONDS` (both default 90, reproducing the prior hard-coded values byte-for-byte when unspecified; `dynamic_timeout` is derived as `max_timeout > timeout`, so equal defaults preserve the previous `dynamic_timeout=False` behavior exactly). `--sleep-between-prompts SECONDS` (default 0 = unchanged single-call behavior; >0 chunks the batch into `n_parallels`-sized groups with a rest between chunks). `--retry-failed-from PATH` (reads a prior `failed_parses.csv`, extracts distinct `municipality_id` values in first-seen order, and filters the loaded municipality list to just those — verified against the retry's `failed_parses.csv` in a dry run, correctly narrowed the 10-city PA list to exactly the 6 target municipalities). `--prompt-mode full|minimal`.
2. **Minimal prompt template** (`MINIMAL_PROMPT_TEMPLATE`): a shorter prompt requesting a flat `candidates` list (unit_type per item) instead of three separate per-unit-type lists, with fewer requested fields (no `employer`, `contract_years`, `why_relevant`).
3. **Parser now accepts both formats**: `extract_raw_candidate_items()` detects a flat `"candidates"` list (minimal format) vs. the original `police_candidates`/`fire_candidates`/`non_safety_candidates` keys (full format) and normalizes either into the same internal row shape. Added `normalize_unit_type()` (handles model near-misses like `"non-safety"`, `"general municipal"`) alongside the existing owner-type/document-type normalizers. Unit-tested offline (no API call) against a synthetic minimal-format response before the live run — both formats parse correctly and normalization rewrites `"government"` → `city`, `"collective_bargaining_agreement"` → `cba`, `"non-safety"` → `non_safety`.
4. **A real bug found and fixed during this same run's audit**: `--sleep-between-prompts` chunks the batch across multiple `gabriel.whatever()` calls sharing one `save_dir`/`file_name` (deliberately, via `reset_files=False`, so a later chunk's failure can't wipe an earlier chunk's saved success). This live run's raw output revealed that GABRIEL's checkpoint-resume mechanism re-returns every already-saved identifier's row on each subsequent call in the same save_dir — a 6-municipality/3-chunk run produced **12 raw rows**, with byte-identical duplicates per identifier (3x for chunk 1's municipalities, 2x for chunk 2's, 1x for chunk 3's — exactly matching cumulative-return arithmetic). This inflated `candidate_rows` and made the naive `n_parseable = len(municipalities) - len(failed_rows)` arithmetic wrong when a duplicated identifier appeared in both a failed and (later) a successful attempt. **Fix**: `run_live_batch()` now deduplicates the concatenated chunk frames via `drop_duplicates(subset=["Identifier"], keep="last")` before returning. Verified offline against the already-saved `raw_outputs.csv` (no additional API call): before dedup, 12 rows; after, exactly 6, matching the true per-municipality outcome. **This fix has not yet been re-verified against a second live call** (this task's "one live test only" constraint) — flagged for confirmation in a future session before trusting `--sleep-between-prompts` output at face value again.

## Run comparison

| | First pilot (2026-07-14, ~20:35) | Retry (2026-07-14, ~22:35) | Timeout stress test (2026-07-15, ~10:16) |
|---|---|---|---|
| Municipalities prompted | 10 (Philadelphia, Pittsburgh, Allentown, Erie, Reading, Scranton, Bethlehem, Lancaster, Harrisburg, York) | 7 (10 minus the 3 that already succeeded) | 6 (7 minus Erie, which succeeded in the retry) |
| `n_parallels` | 3 | 1 | 2 |
| `timeout` / `max_timeout` | 90 / 90 (hard-coded) | 90 / 90 (hard-coded) | **180 / 240** (`dynamic_timeout` enabled) |
| `prompt_mode` | full | full | **minimal** |
| `sleep_between_prompts` | n/a (not yet implemented) | n/a | **5s between n_parallels=2 chunks** |
| Raw responses (as reported) | 10 | 7 | 12 (before dedup fix; **6 after dedup**) |
| **Parseable** | **3 / 10 (30%)** | **1 / 7 (14%)** | **3 / 6 (50%)** (post-dedup-fix true count; live run's own printed `parseable=0` was wrong due to the bug above) |
| Failed | 7 | 6 | 3 (post-fix; all `timeout_or_capacity`) |
| Candidate rows | 9 | 4 | 15 (post-fix, deduplicated) |
| Cost | ~$0.035 | ~$0.03 | **~$0.040** (6 deduplicated rows; failed rows cost ~$0.0001 total, so cost is dominated by the 3 successful calls) |
| Avg time taken, successful rows | 32.9s (Pittsburgh 31.2s, Philadelphia 34.1s, Allentown 33.3s) | 26.0s (Erie only) | **40.5s** (Reading 50.4s, Bethlehem 29.3s, Harrisburg 41.9s) |

## Did the minimal prompt reduce token/output burden?

Not directly comparable on identical cities (different municipalities succeeded each run), but the **successful-call time-taken figures argue against timeout as the binding constraint in all three runs**: every single successful call across all three runs — full-prompt and minimal-prompt alike — completed in 26–50 seconds, far under even the original 90s default `timeout`. If per-call latency against the Harvard proxy were the bottleneck, successful calls should cluster near whatever timeout ceiling is set; instead they cluster in the same narrow 26–50s band regardless of `prompt_mode` or `timeout`/`max_timeout` value. The minimal prompt did not need a bigger timeout window because none of the runs — including the ones with only a 90s ceiling — actually needed one to succeed.

## Did the longer timeout improve reliability?

**No — and the failure evidence directly contradicts the raised-timeout hypothesis.** All 3 failures this run (Scranton, Lancaster, York) show the identical `timeout_or_capacity` signature as the pilot and retry: `"Can't acquire more than the maximum capacity"`. Tracing this message into the installed `gabriel` package (`gabriel/utils/openai_utils.py`) shows it originates from an `aiolimiter.AsyncLimiter` **request-per-minute / token-per-minute rate-limiter bucket**, not from the OpenAI client's per-call `timeout`/`max_timeout` parameters at all — those control how long GABRIEL waits for an in-flight response, not whether a new request is admitted into the rate-limiter's leaky bucket in the first place. Raising `--timeout`/`--max-timeout` to 180/240 could not have addressed this failure mode because it operates upstream of the timeout logic entirely: a request that can't acquire limiter capacity never gets far enough to hit a client-side timeout. **This revises both the first pilot's and the retry's working hypothesis** (per-call web-search latency): the actual binding constraint looks like a per-minute request/token budget against the Harvard proxy — plausibly a conservative default GABRIEL falls back to when it can't read real rate-limit headers from a custom `base_url`/`extra_headers` proxy setup like this one.

## What plausibly did help this run

The 50% parseable rate (post-dedup-fix) is a real improvement over the pilot's 30% and the retry's 14% on a *harder* municipality set (these 6 had already failed twice). Two changes correlate with the improvement, and — per the rate-limiter finding above — both act on the more-plausible actual bottleneck (requests/tokens per minute), not latency:
- **`prompt_mode=minimal`**: shorter prompt, flatter/smaller requested JSON, likely lower token consumption per call against the limiter's token-per-minute budget.
- **`sleep_between_prompts=5` (chunking into `n_parallels=2` groups with a rest between)**: spaces out request admission, giving the limiter's bucket time to refill between chunks rather than issuing all 6 requests' worth of pressure in one `gabriel.whatever()` call.

Neither is confirmed causal from a single run (no ablation was done this session, and the task specified one live test only), but both are more consistent with a rate-limiter explanation than the timeout increase is.

## Failure-type breakdown (timeout stress test, 3 failed, post-dedup)

All 3 classified `timeout_or_capacity` (`gabriel_error_log` contains `"Can't acquire more than the maximum capacity"`): Scranton, Lancaster, York. Zero `empty_response_with_response_id`, zero `empty_response_no_response_id`, zero `json_parse_error` — same clean single-mode failure signature as the retry.

## New candidates (Reading, Bethlehem, Harrisburg — 15 rows)

Staged in `docs/analysis/gabriel_state_source_scout_candidates_pa_2026-07-15_101602_corrected.csv` (the corrected/deduplicated output; the original buggy run also wrote `gabriel_state_source_scout_candidates_pa_2026-07-15_101602.csv` with inflated duplicate rows — **do not use that file**, it is superseded by the `_corrected` version and left in place only for audit trail). Run-id-scoped filename — does not overwrite any prior candidate CSV. All rows `verification_status=unverified`, `promotion_status=raw_model_output`.

| municipality | unit_type | score | priority | owner_type | doc_type | note |
|---|---|---|---|---|---|---|
| Harrisburg | non_safety | 60 | medium | city | cba | `harrisburgpa.gov` AFSCME labor contract PDF |
| Reading | non_safety | 60 | medium | city | cba | `readingpa.gov` city council agenda item referencing a CBA |
| Harrisburg | police | 53 | medium | city | cba | `harrisburgcitycontroller.com` FOP contract amendment PDF |
| Harrisburg | fire | 53 | medium | city | cba | `harrisburgcitycontroller.com` IAFF contract amendment PDF |
| Harrisburg | fire | 53 | medium | city | cba | `cms2.revize.com` (city-hosted CMS) IAFF document |
| Bethlehem | non_safety | 40 | medium | city | context_only | SEIU/TAMS salary resolution PDF |
| Reading | police | 33 | low | third_party | cba | `codelibrary.amlegal.com` FOP CBA (municipal code library, not primary host) |
| Harrisburg | police | 33 | low | third_party | cba | `ecode360.com` hosted CBA PDF |
| Bethlehem | police/fire | 33 | low | city | context_only | recruitment/ordinance pages, not contract documents |
| (remaining 6 rows) | — | 18-25 | low | mixed | mixed | weaker leads — ordinance articles, recruitment pages, financial statements |

**Assessment:** Harrisburg is the standout municipality this run — it is the only one of the 6 to return plausible primary CBA documents for all three unit types (police, fire, non_safety), each hosted on an official or city-adjacent domain (`harrisburgpa.gov`, `harrisburgcitycontroller.com`). These are meaningfully stronger leads than Bethlehem's (mostly `context_only` recruitment/ordinance pages) or Reading's single non-safety agenda-item hit. None of these 15 rows have been fetched/verified — that step is out of scope for this task.

## Is `whatever(web_search=True)` viable, revised understanding

**The reliability problem is a rate-limiter capacity constraint, not a latency/timeout constraint.** Raising `timeout`/`max_timeout` is not the right lever — every successful call across all three runs to date has finished in under a minute regardless of the ceiling. The two levers that plausibly helped this run (smaller/minimal prompts, deliberate spacing between request chunks) both act on request/token throughput against a per-minute budget, which is the more defensible explanation for `"Can't acquire more than the maximum capacity"` once traced to its source (`aiolimiter.AsyncLimiter`, gated on requests-per-minute and tokens-per-minute, not wall-clock call duration).

## Best configuration so far

`--prompt-mode minimal --n-parallels 2 --sleep-between-prompts 5` (chunked, spaced-out, minimal-token requests) produced the best parseable rate of the three runs (50% vs. 30% vs. 14%) on a harder municipality set. `--timeout`/`--max-timeout` beyond the 90/90 default showed no evidence of mattering and should not be the next tuning target. **Recommended next experiment** (not run this session, per the one-live-test constraint): hold `prompt_mode=minimal` and `sleep_between_prompts` constant, and instead vary the *spacing/chunk size* (e.g. `sleep_between_prompts=10-15`, `n_parallels=1` chunks) to test whether further reducing request-rate pressure against the limiter improves reliability further — this is now the load-bearing hypothesis, not per-call timeout.

## Explicitly not done

No source was verified via outbound HTTP fetch, promoted, or ingested. No `data/contracts.csv`, `data/city_coverage.csv`, corpus, or claim/evidence file was touched. No FOIA/PRR/OPRA/RTKL route was used. No `gabriel.codify()` call was made. Only one live run was executed this session (the chunked, dedup-bug-affected run described above); the dedup fix itself was verified offline against already-saved data, not via a second live call.
