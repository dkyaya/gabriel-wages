# GABRIEL Statewide Source Scout — PA Retry Summary (2026-07-14)

**Scope:** hardening pass on `scripts/gabriel_state_source_scout.py` (failure-type logging) plus a capped, `n_parallels=1` live retry of the 7 Pennsylvania municipalities that failed to parse in the first pilot. Still source-scouting/staging only — no ingestion, no `data/contracts.csv`/`data/city_coverage.csv`/corpus/claim-evidence edits.

## What changed in the script

1. **`failed_parses.csv` now carries full GABRIEL diagnostics per failed row**: `failure_type`, `gabriel_successful`, `gabriel_error_log`, `gabriel_response_ids`, `time_taken`, `input_tokens`, `reasoning_tokens`, `output_tokens`, `cost`, `response_nonempty`, `web_sources_nonempty` — not just a generic `error` string. `failure_type` is deterministically classified via `classify_failure()` into `timeout_or_capacity`, `empty_response_with_response_id`, `empty_response_no_response_id`, `json_parse_error`, or `other`.
2. **Owner/document-type normalization extended**: found (in this retry's own Erie results) that the model returned `"private_legal_vendor"` for case-law-aggregator sources (`caselaw.findlaw.com`, `law.justia.com`) — added to `OWNER_TYPE_SYNONYMS` (→ `third_party`) and to `THIRD_PARTY_HOST_MARKERS` so these correctly score as third-party document hosts rather than passing through unscored.
3. **Fixed a real same-day filename collision bug**, found while running this retry: the durable candidate-CSV output was named `gabriel_state_source_scout_candidates_<calendar-date>.csv`. Running a second batch on the same date silently overwrote the first pilot's 9-row candidate file with the retry's 4-row file. **The clobbered file was restored from git commit `d3006ff`** (confirmed byte-identical afterward via `git diff --stat`, no diff). The script now names the durable output by `run_id` (state + full `HHMMSS` timestamp), which cannot collide across runs on the same day.

## Run comparison

| | First pilot (2026-07-14, ~20:35) | Retry (2026-07-14, ~22:35) |
|---|---|---|
| Municipalities prompted | 10 (Philadelphia, Pittsburgh, Allentown, Erie, Reading, Scranton, Bethlehem, Lancaster, Harrisburg, York) | 7 (the 10 minus the 3 that already succeeded: Erie, Reading, Scranton, Bethlehem, Lancaster, Harrisburg, York) |
| `n_parallels` | 3 | 1 |
| Raw responses | 10 | 7 |
| **Parseable** | **3** (30%) | **1** (14%) |
| Failed | 7 | 6 |
| Candidate rows produced | 9 | 4 |
| Cost | ~$0.035 | ~$0.03 (6 of 7 timed out after full retry/cooldown cycles, so cost is dominated by failed-attempt overhead, not successful completions) |

**Which cities are now covered:** Erie parsed successfully this retry (previously `timeout_or_capacity`). The other 6 (Reading, Scranton, Bethlehem, Lancaster, Harrisburg, York) **still failed** — and every one of them is now classified `timeout_or_capacity` (see failure-type breakdown below), including Scranton/Bethlehem/Lancaster, which had been the distinct `empty_response_with_response_id` mode in the first pilot. That mode did not recur this retry.

## Did `n_parallels=1` improve reliability?

**No — it got worse in this run: 14% (1/7) vs. 30% (3/10) in the first pilot.** This is the opposite of the archived 2026-07-01 precedent (`docs/archive/legacy_gabriel_pilot_2026-06/gabriel_builtin_web_boston_graduated_retry_2026-07-01.md`), where a single-worker retry succeeded after a higher-concurrency attempt failed. Two candidate explanations, neither confirmed:

- **Session/proxy-side variance, not a concurrency effect.** The retry ran ~2 hours after the first pilot; GABRIEL's own internal timeout/cooldown logic (pause-after-3-timeouts, 60s sleep) behaved similarly in both runs regardless of `n_parallels`, suggesting the bottleneck is per-request latency against the Harvard proxy's web-search tool call, not queueing/capacity contention between parallel workers. `n_parallels=1` removes queueing contention but does nothing for a single request that itself takes >60-90s to get a web-search result back.
- **The 2026-07-01 precedent's single success was on a much smaller, single-city prompt** (`max_output_tokens` 180-320, one city) run with `n_parallels=1` from the start — it never tested whether `n_parallels=1` specifically *fixed* a failure at higher concurrency; that comparison was never made in the archived session. This retry is the first controlled same-prompt, same-cities, different-`n_parallels` comparison in this project's history, and it does not support "lower concurrency reliably fixes this proxy's timeouts" as a general rule.

**Revised recommendation:** `n_parallels` is not the dominant lever. The binding constraint looks like per-call web-search latency against the Harvard proxy, which neither concurrency setting resolves. A future attempt should test a **higher timeout** (`timeout`/`max_timeout` are currently hard-coded to 90s in `run_live_batch`) before trying more `n_parallels` tuning.

## Failure-type breakdown (retry, 6 failed)

All 6 failed rows classified `timeout_or_capacity` (`gabriel_error_log` contains `"Can't acquire more than the maximum capacity"` / `"OpenAI client timed out"`): Reading, Scranton, Bethlehem, Lancaster, Harrisburg, York. Zero `empty_response_with_response_id`, zero `empty_response_no_response_id`, zero `json_parse_error` this retry — a cleaner (if less successful) failure signature than the first pilot's mixed 4-timeout/3-empty-with-id split.

## New candidates (Erie, 4 rows)

Staged in `docs/analysis/gabriel_state_source_scout_candidates_pa_2026-07-14_223544.csv` (run_id-scoped filename — does **not** overwrite the original `gabriel_state_source_scout_candidates_2026-07-14.csv`). All rows `verification_status=unverified`, `promotion_status=raw_model_output`.

| unit_type | score | priority | owner_type | doc_type | source |
|---|---|---|---|---|---|
| police | 26 | low | third_party | arbitration_award | FindLaw case-law page re: FOP Lodge 7 grievance arbitration |
| fire | 11 | low | third_party | unknown | Justia case-law page re: IAFF Local 293 / Act 111 dispute |
| fire | 26 | low | third_party | arbitration_award | FindLaw case-law page re: a 2002 Act 111 interest-arbitration award (DROP) |
| non_safety | 60 | medium | union | cba | AFSCME Council 13 news release: "AFSCME Local 2206 Members Ratify Strong New Contract with Erie City" |

**Assessment:** these are meaningfully weaker than the first pilot's Philadelphia/Pittsburgh candidates. All three safety-side rows are third-party case-law citations *about* arbitration disputes, not the underlying CBA/award documents themselves — useful as a lead (they confirm FOP Lodge 7 and IAFF Local 293 are the real bargaining units and that Act 111 interest arbitration has occurred for Erie fire) but not a document to verify-and-ingest directly. The non_safety row (AFSCME Local 2206 ratification news) is the most actionable — it names a real, recent (implied current) contract and could seed a targeted follow-up search for the actual signed agreement or a Legistar/council ratification record, following the same pattern that worked for Pittsburgh in the first pilot.

## Task 6 — URL sanity check (top first-pilot candidates, no ingestion)

Lightweight reachability check performed via `curl` HEAD-equivalent requests (`-o /dev/null -w '%{http_code} ...'`, `--max-time 20`) — no file saved, no download into `corpus/`, no ingestion. All 7 rows from Pittsburgh + Philadelphia's first-pilot triads checked; results below are actual HTTP responses, not domain-plausibility guesses.

| Candidate | URL | HTTP result | Type | Likely official? | New vs. existing corpus row? |
|---|---|---|---|---|---|
| Pittsburgh police (score 71) | `apps.pittsburghpa.gov/redtail/.../20764_2023_2025_CONTRACT_RATIFICATION_.pdf` | **Connection timed out** (TCP connect to `205.141.190.118:443` never completed, confirmed via `curl -v --http1.1`) | PDF (unverified) | Unknown — could not verify from this environment; the `pittsburghpa.gov` document-management subdomain may block this environment's egress, or the host itself may be slow/unreachable | New — Pittsburgh has zero rows in `data/contracts.csv` |
| Pittsburgh police (score 36, Legistar) | `pittsburgh.legistar.com/LegislationDetail.aspx?GUID=...` | **HTTP 200**, `text/html`, 121,865 bytes | HTML legislation-detail page | Yes — Legistar is Pittsburgh's real city-council legislative system | New |
| Pittsburgh non_safety (score 78) | `pittsburghpa.gov/files/.../2026-operating-budget-september.pdf` | **HTTP 403** (blocked — likely a WAF/bot-detection rule on the asset CDN, not confirmation the document doesn't exist) | PDF (unverified) | Likely yes — official city domain and path convention, but blocked to automated fetch | New |
| Philadelphia police (score 71) | `phila.gov/media/20170815123224/AAA-City-FOP5-Act-111-Award-2017.pdf` | **HTTP 200**, `application/pdf`, 2,953,423 bytes | Confirmed PDF | Yes — official `phila.gov` media asset | **New, not a duplicate** — confirmed by directly reading `data/contracts.csv` (read-only, no edits): the existing `pa_philadelphia_police_2025` row cites a *different* URL (`fop5.org/.../FOP-5-Act-111-Award-2025-2027.pdf`, the 2025-2027 award). This candidate is an earlier 2017 Act 111 award, not currently in the corpus — a genuine, verified-reachable new lead within the project's 2014-2024 observation window's neighborhood (2017-dated). |
| Philadelphia fire (score 71) | `phila.gov/media/20180517092629/Signed-2017-2020-Local-22-Award.pdf` | **HTTP 200**, `application/pdf`, 1,748,415 bytes | Confirmed PDF | Yes | **Confirmed exact duplicate** — `data/contracts.csv`'s `pa_philadelphia_fire_2017` row's `source_url_or_cite` is this *exact same URL*, byte-for-byte. This candidate rediscovered an already-ingested document; not a new lead. |
| Philadelphia fire (score 51, union-hosted) | `iaff22webcmslive.velarium.com/.../NotOfficial-Local22ConsolidatedContract.pdf` | **HTTP 200**, `application/pdf`, 647,630 bytes | Confirmed PDF | The filename itself is labeled `NotOfficial` by the union's own CMS — a real document but explicitly self-flagged as not the official/binding version | New URL (not in `data/contracts.csv`), but since the identical, officially-signed version is already ingested via the `phila.gov` URL above, this adds no new evidentiary value — lower priority than it would otherwise be. |
| Philadelphia non_safety (score 78) | `phila.gov/media/20220812141851/City-PDP-Local-159-Act-195-Interim-Award-2022.pdf` | **HTTP 200**, `application/pdf`, 440,590 bytes | Confirmed PDF | Yes | **New, not a duplicate** — confirmed against `data/contracts.csv`'s three existing Philadelphia `other` rows (`pa_philadelphia_other_2021` → afscme33.org, `pa_philadelphia_other_2025` → afscme2187.org, `pa_philadelphia_other_2017` → afscme2186.org): none share this URL or this employer/union ("Local 159," a distinct AFSCME local from 2186/2187/33). A genuinely new document and possibly a new bargaining unit for Philadelphia not yet represented in the corpus. |

**Bottom line:** 5 of 7 URLs are confirmed-live, genuine PDF or HTML documents on official domains (Legistar, `phila.gov`). 1 (`pittsburghpa.gov` budget PDF) is blocked by what looks like bot detection, not necessarily broken. 1 (`apps.pittsburghpa.gov` Redtail PDF) could not be reached from this environment at all (TCP-level timeout) — genuinely unverified, not assumed dead. Direct comparison against `data/contracts.csv` (read-only) resolved the Philadelphia overlap question precisely: the fire candidate is an **exact duplicate** of the already-ingested `pa_philadelphia_fire_2017` (this pilot rediscovered it, which is itself a useful cross-check that the workflow surfaces real, already-verified documents); the police and non_safety candidates are **genuinely new** — a 2017 Act 111 police award and a Local 159 non-safety Act 195 interim award, neither currently in the corpus.

## Is `whatever(web_search=True)` viable as small resumable batches?

**Partially, with a revised understanding of the bottleneck.** The retry confirms the workflow's core design (per-municipality independence, resumable via `--municipalities-csv` filtering to just the failed rows) works mechanically exactly as intended — rerunning only the 7 failed cities was a one-line command with no code changes needed. But the reliability problem is not solved by smaller batches or lower concurrency alone: 6 of 7 retried municipalities failed again, all via the same `timeout_or_capacity` signature. Before a full-state run, the next lever to test is the per-call `timeout`/`max_timeout` (currently 90s, hard-coded in `run_live_batch`), not batch size or `n_parallels`.

## Explicitly not done

No source was verified via outbound HTTP fetch, promoted, or ingested. No `data/contracts.csv`, `data/city_coverage.csv`, corpus, or claim/evidence file was touched. No FOIA/PRR/OPRA/RTKL route was used. No `gabriel.codify()` call was made. Only one live retry batch was run (not retried further, per the task's "one live retry run only" instruction).
