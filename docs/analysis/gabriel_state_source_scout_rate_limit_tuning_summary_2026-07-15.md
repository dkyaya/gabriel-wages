# GABRIEL Statewide Source Scout — Rate-Limit Tuning & Dedup Confirmation Summary (2026-07-15, session 2)

**Scope:** fourth and fifth live tests of `scripts/gabriel_state_source_scout.py`, following the 2026-07-15 timeout stress test's revised hypothesis that the recurring `"Can't acquire more than the maximum capacity"` failure is a rate-limiter capacity constraint (an `aiolimiter.AsyncLimiter` requests/tokens-per-minute bucket), not a per-call latency/timeout constraint. This session (a) live-confirms the checkpoint-echo dedup fix from the prior session, (b) runs a controlled `n_parallels=1` vs. `n_parallels=2` ablation holding prompt mode and spacing constant, and (c) does a lightweight URL sanity check on Harrisburg's strongest candidates. Still source-scouting/staging only — no ingestion, no `data/contracts.csv`/`data/city_coverage.csv`/corpus/claim-evidence edits, no `gabriel.codify()` call.

## Run comparison (all five runs to date)

| | Pilot (07-14 ~20:35) | Retry (07-14 ~22:35) | Timeout/minimal stress test (07-15 ~10:16) | Dedup-confirm (07-15 ~10:40) | Micro-test n=2 (07-15 ~10:44) |
|---|---|---|---|---|---|
| Municipalities | 10 | 7 | 6 | **3** (Scranton, Lancaster, York — the 3 hardest; failed *every* prior attempt) | same 3 |
| `n_parallels` | 3 | 1 | 2 | **1** | **2** |
| `prompt_mode` | full | full | minimal | minimal | minimal |
| `timeout`/`max_timeout` | 90/90 | 90/90 | 180/240 | 90/90 | 90/90 |
| `sleep_between_prompts` | n/a | n/a | 5 | **15** | **15** |
| Parseable | 3/10 (30%) | 1/7 (14%) | 3/6 (50%, post-dedup-fix) | **3/3 (100%)** | **2/3 (67%)** |
| Failed | 7 | 6 | 3 (`timeout_or_capacity`) | **0** | 1 (`timeout_or_capacity`, Lancaster) |
| Candidate rows | 9 | 4 | 15 | **14** | 11 |
| Cost | ~$0.039 | ~$0.010 | ~$0.040 | ~$0.039 | ~$0.011 |
| Avg time, successful calls | 32.9s | 26.0s | 40.5s | 36.3s | 14.3s (of the 2 successes) |
| Duplicate identifiers observed | n/a (bug not yet found) | n/a | **yes** (12 raw rows for 6 munis, bug found+fixed) | **no** | **no** |

## Task 1 — Dedup fix: confirmed safe, but not re-exercised against genuine duplicates

The dedup-confirm run (`n_parallels=1`, `sleep_between_prompts=15`, 3 municipalities) completed cleanly: **3 responses for 3 municipalities, 0 duplicate identifiers**, both in the script's own `raw_outputs.csv` (which reflects the post-`drop_duplicates` result) and in GABRIEL's own internal checkpoint file (`gabriel_save_dir/gabriel_whatever_raw.csv`), which also held exactly 3 rows with no repeats. The micro-test (`n_parallels=2`, same spacing) likewise produced 3 responses for 3 municipalities with zero duplicates in either file.

**Honest conclusion: the checkpoint-echo duplication bug did not recur in either fresh live test this session.** This means the fix's `drop_duplicates(subset=["Identifier"], keep="last")` line ran as a no-op both times — safe (it did not corrupt or drop any genuine data, confirmed by comparing pre- and post-fix row counts against GABRIEL's own checkpoint file), but **not a live demonstration of it actually removing real duplicates**. The original bug was observed only at the original stress test's specific shape (6 municipalities, `n_parallels=2`, 3 chunks of size 2, `sleep_between_prompts=5`); neither of today's smaller 3-municipality tests (1 or 2 chunks) reproduced it. The fix remains: (a) verified offline against the original buggy dataset (12→6 rows, matching ground truth exactly), (b) confirmed harmless/inert in two fresh live runs. A true live reproduction-and-fix confirmation would need a run at closer to the original bug's scale (more chunks) — not done this session, out of scope given the "no hammering" instruction and the small municipality list remaining to test.

## Task 2 — n_parallels=1 vs. n_parallels=2 ablation (the clean result this session)

Because the dedup-confirm run (`n_parallels=1`) came back clean and cheap (~$0.039, ~110s wall-clock), the optional second micro-test (`n_parallels=2`) was run on the *same three* municipalities, holding `prompt_mode=minimal` and `sleep_between_prompts=15` constant — a genuine controlled ablation, not a different city set:

- **`n_parallels=1`: 3/3 parseable (100%).** Scranton, Lancaster, and York — three cities that had failed every one of their three prior attempts (pilot, retry, stress test) — all succeeded when the sequential/one-in-flight setting was combined with 15s spacing.
- **`n_parallels=2`: 2/3 parseable (67%).** Lancaster — paired concurrently with Scranton in the first chunk — hit the same `"Can't acquire more than the maximum capacity"` timeout at the 60s mark. The *same* Lancaster prompt succeeded moments later when run alone under `n_parallels=1`.

This is the clearest single piece of evidence in this project's scout-tuning history that **concurrency itself, not just total request volume, is what the rate limiter is reacting to** — the identical prompt for the identical city failed only when a second concurrent request was in flight alongside it. This strengthens the rate-limiter hypothesis further: two simultaneous web-search tool calls against the Harvard proxy are enough to exhaust whatever capacity budget GABRIEL's `aiolimiter` bucket is tracking, even 15 seconds after the previous chunk finished.

## Did `sleep_between_prompts=15` help?

Yes, in combination with `n_parallels=1`: **100% parseable on the three hardest municipalities in the project's scout history** (each had failed 100% of prior attempts — 3/3 combined across pilot+retry+stress test before today). This is the single best result of any run to date, on the hardest available test set. Whether the 15s spacing (vs. the stress test's 5s) or the `n_parallels=1` setting (vs. the stress test's 2) is doing more of the work is not separable from this session's two runs alone — both changed at once relative to the stress test — but the direct `n=1` vs. `n=2` ablation on identical inputs (this session) isolates concurrency as the more clearly causal factor.

## Task 3 — Harrisburg URL sanity check (read-only, no download to corpus)

Checked the 5 candidate URLs from the corrected timeout-test's Harrisburg rows via `curl` (`--max-time 20`, `-o /dev/null`, content-type/size/redirect inspection only):

| Candidate | unit_type | score | HTTP result | Content type | Official? | Direct doc vs. context page? | Priority | Caveat |
|---|---|---|---|---|---|---|---|---|
| `harrisburgpa.gov/.../AFSCME-Labor-Contract...pdf` | non_safety | 60 | **302 → 404** (redirects to `cms2.revize.com`, but that path doesn't exist) | text/html (error page) | Domain is official, but **the document is not actually there** | Dead link | **Low — do not pursue this URL** | The scored URL is broken; if this contract exists, it would need a fresh search, not a fetch of this exact link |
| `harrisburgcitycontroller.com/.../FOP-Contract-Amendment.pdf` | police | 53 | 200 (only with TLS verification bypassed) | application/pdf, 455KB | Plausibly official (city controller's own domain) | Direct PDF | Medium — real document, but... | **Host's TLS certificate expired 2026-04-22** (~3 months ago as of this test). Any future fetch/ingestion would need to either wait for cert renewal or explicitly document a verified-insecure fetch — flag before promoting |
| `cms2.revize.com/.../IAFF.pdf` | fire | 53 | **200, valid TLS** | application/pdf, 2.88MB | Yes — city's actual CMS host (same platform the AFSCME link tried and failed to redirect to) | Direct PDF | **High — cleanest of the 5** | None found |
| `harrisburgcitycontroller.com/.../Second-Amendment-to-IAFF-Contract.pdf` | fire | 53 | 200 (TLS bypassed, same expired cert) | application/pdf, 543KB | Plausibly official | Direct PDF | Medium | Same expired-cert caveat as the FOP amendment above |
| `ecode360.com/.../517728933.pdf` | police | 33 | 200, valid TLS | application/pdf, 38.9KB | No — third-party municipal code library (already reflected in the lower score) | Direct PDF (hosted copy) | Low (as scored) | Third-party host, not primary source; may duplicate a primary that doesn't yet have a URL in hand |

**Bottom line:** 3 of 5 Harrisburg URLs are confirmed-live, real PDF documents (the `cms2.revize.com` IAFF fire CBA is the cleanest — official host, valid TLS, no caveats). 1 (the highest-scored non_safety AFSCME link) is a dead redirect — a real finding that would have wasted a future verification pass if not checked here. 2 sit on a domain with an **expired TLS certificate** — real documents, but a genuine due-diligence flag for any future fetch attempt (a naive `requests.get()` or browser visit would fail/warn on the cert, not just this specific `curl` invocation).

## Rate-limit hypothesis — status after this session

**Strengthened.** The `n_parallels=1` vs. `n_parallels=2` ablation on identical inputs is the most direct evidence yet: the same prompt, for the same city, under the same spacing, succeeded when run alone and failed when run alongside one other concurrent request. This is inconsistent with a pure per-call-latency explanation (which wouldn't care how many other calls are in flight) and consistent with a shared capacity budget that a second simultaneous request can exhaust.

## Is `whatever(web_search=True)` viable as small, spaced, minimal batches?

**Yes, with the specific configuration validated this session.** `n_parallels=1` + `prompt_mode=minimal` + `sleep_between_prompts=15` achieved 100% parseable on the three most stubborn municipalities in the project's history — a result no prior configuration (including `n_parallels=1` at default 5s-equivalent spacing in the 2026-07-14 retry, which got 14%) came close to. The tradeoff is wall-clock time: fully sequential single-flight calls with 15s rests between them do not scale to a full-state run without batching across many separate invocations — but that tradeoff is the right one given this project's cost/reliability priorities (cost remains trivial at ~$0.01-0.04 per 3-6 municipalities either way).

## What should be done before full-state scaling

1. **Adopt `n_parallels=1` + `prompt_mode=minimal` + `sleep_between_prompts=15` (or higher) as the default recommended configuration**, not the pilot's `n_parallels=3` or the retry's un-spaced `n_parallels=1`.
2. **Do not scale via higher concurrency.** This session's ablation directly shows concurrency (not just volume) triggers the rate limiter; a full-state run should batch via *more sequential invocations*, not *more parallel workers*.
3. **Re-verify the dedup fix under conditions closer to the original bug's shape** (more chunks, e.g. 6+ municipalities at `n_parallels=2`) before fully trusting `--sleep-between-prompts` at scale — this session's two tests didn't reproduce it, so it remains only indirectly confirmed.
4. **Fix the Harrisburg AFSCME dead link before any promotion**, and **flag the `harrisburgcitycontroller.com` expired certificate** as a fetch-time caveat for whoever verifies those two documents next.
5. Scranton, Lancaster, and York (now all succeeded) plus Reading/Bethlehem/Harrisburg (succeeded in the prior stress test) means **all 6 of the previously-fully-failing PA municipalities have now produced at least one successful parse** — a good point to pause scout tuning and let a verification pass (URL checks + `data/contracts.csv` overlap comparison, following the 2026-07-14 retry session's pattern) catch up on the accumulated candidate backlog before running more `whatever` calls.

## Task 5 — Candidate handling

New candidates from this session are staged at run-id-scoped filenames — none overwrite prior candidate CSVs:
- `docs/analysis/gabriel_state_source_scout_candidates_pa_2026-07-15_104013.csv` (14 rows, dedup-confirm run: Scranton/Lancaster/York, `n_parallels=1`)
- `docs/analysis/gabriel_state_source_scout_candidates_pa_2026-07-15_104359.csv` (11 rows, micro-test run: Scranton/York, `n_parallels=2`; Lancaster failed this run)

All rows `verification_status=unverified`, `promotion_status=raw_model_output`. Notably strong new leads: Scranton's and York's direct `scrantonpa.gov`/`yorkcity.org`-hosted CBA PDFs across all three unit types, and Lancaster's PA Labor Relations Board (PLRB) fire final-order PDF (`source_owner_type=state_labor_board`, score 73 — the highest single score of any candidate this project's scout has produced).

## Explicitly not done

No source was fetched to disk/ingested/promoted (Harrisburg URL checks were `curl` metadata-only, `-o /dev/null`). No `data/contracts.csv`, `data/city_coverage.csv`, corpus, or claim/evidence file was touched. No FOIA/PRR/OPRA/RTKL route was used. No `gabriel.codify()` call was made. Two live `gabriel.whatever` calls this session (3 prompts each, both within the task's capped scope); no further live runs attempted.
