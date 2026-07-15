# GABRIEL Statewide Source Scout — Tuning Matrix & Reliability Interpretation (2026-07-15, session 3)

**Scope:** instruments the scout with per-run cost accounting (Task 1) and a `--compare-runs` utility (Task 2), then runs a controlled 4-cell tuning matrix (Task 3) on the same 3 stress-test municipalities (Scranton, Lancaster, York) to isolate the effect of `sleep_between_prompts` (10/20s), `n_parallels` (1/2), and `prompt_mode` (minimal/full) on reliability, cost, and candidate yield. Scout tuning only — no verification, no ingestion, no `data/contracts.csv`/`data/city_coverage.csv`/corpus/claim-evidence edits, no `gabriel.codify()` call.

## What was added to the script

1. **Cost accounting** (`compute_cost_summary()`, `write_cost_summary()`, `append_cost_log()`): every live run now writes `cost_summary.json`/`cost_summary.csv` to its own output directory and appends one row to the durable, never-overwritten `docs/analysis/gabriel_state_source_scout_cost_log.csv`. Tracks total/successful/failed cost, per-prompt/per-parseable-response/per-candidate cost, token totals and averages, and average successful-call time, alongside the run's settings (model, prompt_mode, search_context_size, n_parallels, sleep_between_prompts, timeout, max_timeout). Unit-tested offline against a synthetic 2-row DataFrame before use in a live run.
2. **Run comparison utility** (`--compare-runs DIR1 DIR2 ... [--compare-output PATH]`): reads each directory's `run_metadata.json` (required), `cost_summary.json` (optional — degrades gracefully to `None` for runs predating this session, confirmed against the two live runs from the prior rate-limit-tuning session), `failed_parses.csv` (failure-type breakdown), and `raw_outputs.csv` (duplicate-identifier sanity check). Produces one markdown table row per run. This replaces the manual `pandas`-snippet reconstruction used in every prior relay bundle.

## Tuning matrix — 4 live cells, all on Scranton/Lancaster/York

| Cell | prompt_mode | n_parallels | sleep_between_prompts | Parse rate | Total cost | Cost/parseable | Avg successful call time | Candidate rows | Duplicate IDs |
|---|---|---|---|---|---|---|---|---|---|
| 1 | minimal | 1 | 10s | **3/3 (100%)** | $0.0320 | $0.0107 | 26.7s | 12 | 0 |
| 2 | minimal | 1 | 20s | **3/3 (100%)** | $0.0305 | $0.0102 | 23.0s | 14 | 0 |
| 3 | minimal | 2 | 20s | **2/3 (67%)** — Lancaster failed | $0.0223 | $0.0112 | 30.7s | 12 | 0 |
| 4 (optional) | full | 1 | 20s | **3/3 (100%)** | $0.0332 | $0.0111 | 23.6s | **8** | 0 |

For reference, the prior session's two runs on the same 3 municipalities (predate cost accounting, cost pulled from `raw_outputs.csv` directly): `minimal/n=1/sleep=15` → 3/3 (100%), ~$0.0387; `minimal/n=2/sleep=15` → 2/3 (67%, Lancaster failed) — same failure city, same signature, at a different spacing.

## Task 4 — Reliability interpretation

**What is the best configuration so far?** `prompt_mode=minimal`, `n_parallels=1`, `sleep_between_prompts` anywhere in the 10-20s range tested, `timeout=90`/`max_timeout=90`. This is now **4 for 4** live runs at 100% parseable on these three municipalities (sleep=10, 15, 20, all at `n_parallels=1`).

**Is `n_parallels=1` consistently better?** **Yes — decisively.** Every `n_parallels=1` run this project has attempted on Scranton/Lancaster/York succeeded 3/3 (4 runs: sleep=10/15/20 this session plus sleep=15 last session). Every `n_parallels=2` run on the same three municipalities has landed at 2/3 (67%), and **the same municipality (Lancaster) failed both times** — always when paired concurrently with Scranton in the first chunk. This is not just "concurrency is worse on average," it's a specific, reproducible pairing failure, strengthening (not just repeating) the concurrency-is-the-binding-constraint finding from the prior session.

**Does 10s vs. 15s vs. 20s spacing matter?** **Not within this range, given `n_parallels=1`.** All three spacings (10/15/20s) produced identical 100% success. Cost and average successful-call time varied only within normal run-to-run noise (23-27s call time, $0.030-0.039 total cost) and showed no trend with spacing. **Spacing does not appear to be the active ingredient — concurrency is.** This means `sleep_between_prompts` may matter less for reliability than previously believed once `n_parallels=1` is already in place; its main remaining value is likely pacing large batches to avoid a *sustained* elevated request rate over many sequential calls, not preventing any single collision (there's only ever one in-flight request at a time under `n_parallels=1` regardless of the sleep value).

**Does the full prompt provide enough extra value to justify higher token/cost/failure risk?** **No — the single data point available argues against it.** Cell 4 (`full`, same municipalities/spacing) matched the minimal prompt's 100% success rate and cost (~$0.033 vs. ~$0.030-0.032 for minimal) — so no meaningful reliability or cost penalty — but **produced only 8 candidate rows vs. minimal's 12-14**, despite consuming *more* input tokens (108,175 vs. ~92-95k) for similar output tokens (5,733 vs. 5,777-5,968). The full prompt's extra requested fields (`triad_status`, `best_next_action`, `employer`, `contract_years`, `why_relevant` per item) appear to consume output-token budget that would otherwise go toward more candidate items, at equal token cost. **One data point only — not a definitive ablation — but it points toward minimal as the better default on yield-per-dollar, not just reliability.**

## Cost and wall-clock estimates for scaling

Using the `n_parallels=1` + `prompt_mode=minimal` configuration's observed successful-call cost (~$0.010-0.013/prompt across the three 100%-success runs this session plus the prior session's sleep=15 run) as the representative per-prompt cost, and ~23-31s average successful-call time plus 15-20s spacing per municipality as the representative per-item wall-clock cost:

| Scale | Estimated cost (~$0.011/prompt) | Estimated wall-clock (sequential, ~45-50s/municipality incl. spacing) |
|---|---|---|
| 100 municipalities | **~$1.10** | **~75-85 minutes** |
| 500 municipalities | **~$5.50** | **~6.3-7.1 hours** |
| 1,000 municipalities | **~$11.00** | **~12.5-14.2 hours** |

**Caveats on these estimates:**
- These are **successful-call cost/time** estimates for the recommended configuration, not a blended historical average. The pilot/retry/stress-test sessions' blended per-prompt cost was actually *lower* (~$0.001-0.007/prompt) only because many calls failed cheaply (a failed `timeout_or_capacity` call costs ~$0.00003-0.0001, near-zero) — that blended figure is not representative of a configuration that mostly succeeds, and using it would understate real cost at scale.
- `LIVE_HARD_CAP=25` (hard-coded, not overridable via flag) means a 1,000-municipality run requires **~40 separate script invocations**, each individually capped — the wall-clock estimate above assumes those invocations run back-to-back with no idle time between batches; in practice, spacing out invocations across a session/day would extend real elapsed time without changing total compute cost.

**What failure rate should we expect?** **This session's evidence is 9-for-9 (100%) at `n_parallels=1` across three spacings** — but that sample is **three municipalities tested repeatedly, not 100-1,000 distinct cities**, so 0% is very unlikely to hold exactly at scale. A more defensible planning assumption is **a low but nonzero failure rate (rough band: 0-10%)** — consistent with 100% on this small, repeated sample while acknowledging untested variance across proxy load, city-name ambiguity, and web-search result availability across hundreds of unfamiliar municipalities. Budget for a retry pass, not zero failures.

**What retry strategy should be used at scale?**
1. Run in `LIVE_HARD_CAP`-bounded batches (≤25 municipalities), `n_parallels=1`, `prompt_mode=minimal`, `sleep_between_prompts=15` (a reasonable middle value from the tested 10-20s range with no observed reliability difference).
2. After each batch, immediately run `--retry-failed-from <that batch's failed_parses.csv>` — cheap (few municipalities, same settings) and, per this project's whole tuning history, the fastest way to close out stragglers rather than accumulating a growing backlog across many large batches.
3. Use the new `--compare-runs` utility after each batch (or small group of batches) to track parse rate and cost drift over time without hand-reconstructing tables.
4. Do not raise `n_parallels` to speed up a large run — every controlled comparison in this project's four tuning sessions (10-20s spacing, two different municipality sets) shows `n_parallels=2` costs real reliability for a wall-clock gain that a properly-batched `n_parallels=1` run doesn't actually need at this cost scale (~$11 for 1,000 cities is not a burdensome budget to trade for reliability).

## Recommended default scout configuration

```text
prompt_mode=minimal
n_parallels=1
sleep_between_prompts=15
timeout=90
max_timeout=90
search_context_size=low
model=gpt-5.4-nano
```

Unchanged from the configuration the task started with — this session's matrix **confirms** it rather than finding a better one. The one new piece of information is that `sleep_between_prompts` can likely be lowered toward 10s (or possibly further, untested) without reliability loss as long as `n_parallels=1` holds, which would shave wall-clock time at scale, but this wasn't tested below 10s this session and should be treated as a hypothesis, not a confirmed finding.

## Task 5 — Candidate handling

New candidate CSVs from this session, all run-id-scoped, none overwriting prior files:
- `docs/analysis/gabriel_state_source_scout_candidates_pa_2026-07-15_110146.csv` (12 rows, cell 1: minimal/n1/sleep10)
- `docs/analysis/gabriel_state_source_scout_candidates_pa_2026-07-15_110349.csv` (14 rows, cell 2: minimal/n1/sleep20)
- `docs/analysis/gabriel_state_source_scout_candidates_pa_2026-07-15_110557.csv` (12 rows, cell 3: minimal/n2/sleep20 — Scranton/York only, Lancaster failed)
- `docs/analysis/gabriel_state_source_scout_candidates_pa_2026-07-15_110810.csv` (8 rows, cell 4: full/n1/sleep20)

All rows `verification_status=unverified`, `promotion_status=raw_model_output`. No verification, promotion, or ingestion performed this session (out of scope per task instructions).

## Explicitly not done

No source was verified, fetched, promoted, or ingested. No `data/contracts.csv`, `data/city_coverage.csv`, corpus, or claim/evidence file was touched. No FOIA/PRR/OPRA/RTKL route was used. No `gabriel.codify()` call was made. Four live `gabriel.whatever` calls this session (3 prompts each, all within the task's capped matrix); no further live runs attempted.
