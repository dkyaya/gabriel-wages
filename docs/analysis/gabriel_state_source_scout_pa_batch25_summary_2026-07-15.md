# GABRIEL Statewide Source Scout — PA 25-Municipality Batch Summary (2026-07-15)

**Scope:** first scale-up of the tuned scout configuration (`n_parallels=1`, `prompt_mode=minimal`, `sleep_between_prompts=15`, `timeout=90/max_timeout=90`, confirmed across four prior tuning sessions) from 3-10 municipality tests to a 25-municipality Pennsylvania batch, plus one immediate retry of failures, plus new persistent scout coverage accounting. **Scout-stage only** — no source verification, no candidate audit, no ingestion, no `gabriel.codify()` call, no `data/contracts.csv`/`data/city_coverage.csv`/corpus/claim-evidence edits.

**Critical terminology note (per Task 6 of this session's instructions):** every count below describes **scout-positive, unverified** model output — a candidate lead the model found via web search, not a confirmed, reachable, or ingested document. No municipality below should be read as "collected" or "verified." See `docs/analysis/gabriel_state_source_scout_coverage_methodology_2026-07-15.md` for the full vocabulary discipline.

## Batch composition

25 Pennsylvania municipalities: the 10 cities from the 2026-07-14 pilot (Philadelphia, Pittsburgh, Allentown, Erie, Reading, Scranton, Bethlehem, Lancaster, Harrisburg, York) plus 15 additional mid-size PA cities/boroughs (Altoona, Wilkes-Barre, Chester, Williamsport, Easton, Lebanon, Hazleton, New Castle, Norristown, Pottstown, Chambersburg, Carlisle, State College, Johnstown, McKeesport), selected from general knowledge of Pennsylvania's larger municipalities — not a verified statewide gazetteer (see `docs/analysis/gabriel_state_source_scout_pa_batch25_municipalities_2026-07-15.csv`'s `population_rank_note` column, which is explicit about this being an approximate, documented-but-unverified basis, per the task's own "do not spend the whole run creating a perfect statewide gazetteer" instruction).

## Parse rates

| Stage | Municipalities | Parseable | Failed | Parse rate |
|---|---|---|---|---|
| Main run | 25 | 20 | 5 | 80% |
| Retry (5 failed municipalities) | 5 | 5 | 0 | **100%** |
| **Final (after one retry)** | 25 | **25** | 0 | **100%** |

**A new failure signature appeared this batch**: all 5 main-run failures classified `empty_response_no_response_id` with `gabriel_error_log` showing `"Connection error."` — distinct from every prior session's dominant `timeout_or_capacity` (`"Can't acquire more than the maximum capacity"`) signature. This looks like transient network/connection issues rather than the previously-diagnosed rate-limiter capacity constraint. All 5 resolved cleanly on a single retry pass with the identical configuration — consistent with a transient-error explanation (the same settings that failed once succeeded moments later) rather than a systematic problem with these 5 specific municipalities or this configuration. No duplicate identifiers were produced in either the main run or the retry (25 raw rows / 25 unique identifiers, 5/5 in the retry) — the checkpoint-echo dedup fix continues to hold clean.

## Candidate breakdown (final, post-retry)

| Metric | Count | Share of 25 |
|---|---|---|
| Municipalities with any candidate lead | 23 | 92% |
| Municipalities with a police candidate lead | 20 | 80% |
| Municipalities with a fire candidate lead | 16 | 64% |
| Municipalities with a non-safety candidate lead | 14 | 56% |
| Municipalities with a likely triad (leads spanning all 3 unit types) | **10** | 40% |
| Total candidate rows | **75** | — |
| Official-or-union-sourced candidate rows (`city`/`state_labor_board`/`union`) | 65 | 87% of rows |
| High-priority candidate rows (`likely_ingest_priority=high`) | 3 | 4% of rows |

**Municipalities with a likely triad this batch**: Philadelphia, Erie, Scranton, Harrisburg, York, Altoona, Williamsport, Hazleton, Chambersburg, Johnstown. (Note: "likely triad" is a scout-stage signal — leads exist for all three unit types — not a claim that the underlying documents share a matched bargaining cycle, which remains a downstream, human-verified step per `AGENTS.md`'s cross-occupation design.)

**Two municipalities (Bethlehem, Carlisle) parsed successfully but returned zero candidates** — the model explicitly reported no sources found, a legitimate scout outcome distinct from a parse failure.

## Cost, tokens, and wall-clock time

| | Main run | Retry | **Combined** |
|---|---|---|---|
| Total cost | $0.2188 | $0.0501 | **$0.2688** |
| Input tokens | 667,744 | 146,569 | **814,313** (state-coverage total: 814,151; small rounding from float accumulation) |
| Reasoning tokens | 30,021 | 6,954 | **36,975** |
| Output tokens | 38,145 | 9,646 | **47,791** |
| Successful-call wall-clock (sum) | ~591.8s (20 calls, main run avg 29.6s x 20) | ~130.3s (5 calls, retry avg 26.1s x 5) | **722.2s** (25 calls) |

- **Average cost per municipality** (25 scouted, all now parseable): **$0.0108**.
- **Average cost per parseable municipality**: same, **$0.0108** (100% parseable after retry).
- **Average candidate rows per parseable municipality**: 75 / 25 = **3.0 rows/municipality**.
- **Average successful-call time**: 722.2s / 25 = **~28.9s/municipality**.

## Scaling estimates (from this batch's own observed rates, via the new state-coverage file)

| Scale | Estimated cost | Estimated wall-clock (sequential, `n_parallels=1` + 15s spacing) |
|---|---|---|
| 100 municipalities | **~$1.08** | **~73 minutes** |
| 500 municipalities | **~$5.38** | **~6.1 hours** |
| 1,000 municipalities | **~$10.75** | **~12.2 hours** |

These are close to (and cross-validate) the prior tuning-matrix session's 3-municipality-sample estimates (~$1.10/~80min, ~$5.50/~6.7hr, ~$11/~13hr for the same scale points) — a good sign that the smaller sample's estimates were not badly biased. As before: `LIVE_HARD_CAP=25` means any run at these scales requires many separate invocations (a 1,000-city run needs ~40), and a nonzero retry rate should be budgeted for (this batch needed one retry pass covering 20% of municipalities, though all resolved cleanly).

## Coverage accounting (new this session)

`docs/analysis/gabriel_state_source_scout_municipality_coverage.csv` (25 rows, one per municipality, upsertable for future re-scouting) and `docs/analysis/gabriel_state_source_scout_state_coverage.csv` (1 row for PA, recomputed in full from all municipality rows on file) are now live, built via `scripts/gabriel_state_source_scout.py --build-coverage`. See `docs/analysis/gabriel_state_source_scout_coverage_methodology_2026-07-15.md` for field definitions and the scout-positive-vs.-verified vocabulary discipline these files must be read under.

## Best next step

**Move to a URL-reachability / `data/contracts.csv`-overlap verification pass on the accumulated candidate backlog before any further scout scaling.** Across all scout sessions to date (2026-07-14 pilot/retry through this 25-city batch), the project has accumulated a substantial number of unverified candidate rows across ~30+ distinct Pennsylvania municipalities. The scout configuration itself is now well-confirmed (5 tuning sessions, consistent ~$0.01/municipality and ~30s/municipality figures, a clean 100% final parse rate on a real 25-city batch) — further scout-only scaling has diminishing returns relative to converting the existing lead backlog into verified, promotable candidates. The 3 high-priority candidate rows and the 10 likely-triad municipalities from this batch are the most natural starting point for that pass, following the URL-check pattern established in the 2026-07-14 retry session (`curl`-based reachability + `data/contracts.csv` overlap comparison, read-only, no ingestion).

## Explicitly not done

No source was verified, fetched, promoted, or ingested. No `data/contracts.csv`, `data/city_coverage.csv`, corpus, or claim/evidence file was touched. No FOIA/PRR/OPRA/RTKL route was used. No `gabriel.codify()` call was made. Two live `gabriel.whatever` calls this session (25-prompt main run, 5-prompt retry, both within the task's authorized scope); no further live runs attempted.
