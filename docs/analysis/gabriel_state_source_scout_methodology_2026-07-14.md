# GABRIEL Statewide Source Scout — Schema and Methodology

**Date:** 2026-07-14
**Type:** durable project standard (like `claim_testing_source_wave_methodology_2026-07-12.md` and `source_planning_csv_hygiene_standard_2026-07-08.md`). Update in place for routine use; do not fork a dated copy.
**Status:** source-discovery/staging tool only. Nothing produced by this workflow is ingested evidence — see "What promotion would require" below.

## 1. Purpose

Prior source-availability scans in this project (`pa_nj_source_scan_preflight_2026-07-12.md`, `pennsylvania_source_scan_2026-07-12.md`, `national_corpus_expansion_preflight_2026-07-12.md`) were run as hand-driven, per-city research passes. This document and its companion script (`scripts/gabriel_state_source_scout.py`) generalize that into a repeatable, boundable GABRIEL `whatever(web_search=True)` workflow that can run source-discovery prompts across many municipalities in a state at once and produce a ranked, staged source-candidate queue — one row per candidate document, covering police, fire, and non-safety/general municipal labor sources per municipality.

This is a **scouting and staging** tool. It does not ingest, does not touch `data/contracts.csv` / `data/city_coverage.csv` / `corpus/`, and does not run `codify`. Its output feeds the durable national queue in `national_scout_candidate_queue_2026-07-20.csv`. Routine post-scout work now means light triage plus scout-coverage accounting; deeper source verification is deferred to coordinated waves selected from that queue. The existing 13-step `claim_testing_source_wave_methodology_2026-07-12.md` lifecycle still governs later verification, promotion, ingestion, codification, and claim use.

## 2. `whatever` vs. `codify` — what differs

| | `gabriel.whatever` (this tool) | `gabriel.codify` (`scripts/gabriel_codify_pilot.py`) |
|---|---|---|
| Input | A free-text prompt per row; no corpus document required | A DataFrame of already-ingested, already-extracted evidence-window text |
| Web access | `web_search=True` — the model searches the live web itself | None — codes only the provided window text |
| What it answers | "What sources exist for this municipality?" (discovery) | "What does this already-collected document say?" (measurement) |
| Output | Unstructured/semi-structured candidate-source JSON, no grounding guarantee | Structured attribute-presence codes, verbatim-substring grounding enforced |
| Verification | None built in — every candidate is `verification_status=unverified` until a human/agent confirms the URL resolves and the document matches | Anti-paraphrase / boundary-leak / grounding checks run automatically |
| Where it sits in the project lifecycle | Upstream of ingestion (Steps 1-5 of the source-wave methodology) | Downstream of ingestion (Steps 8-11) |
| Corpus effect | None — writes only to `tmp/` (quarantined) and, after scoring, a candidate CSV in `docs/analysis/` | Writes to the evidence layer (`gabriel_codify_evidence_layer.csv`), never to `data/contracts.csv` directly either |

`whatever` is the right tool for "does a source plausibly exist and where" at scale; `codify` remains the right tool for "what does this specific already-verified document say." Neither one ever writes to `data/contracts.csv`, `data/city_coverage.csv`, or `corpus/` — both are one layer removed from the canonical tables, by design.

## 3. What outputs are quarantined

Every artifact this tool produces is either:
- under `tmp/gabriel_state_source_scout/<state>/<timestamp>/` (git-ignored, working/raw — `raw_outputs.csv`, `parsed_candidates.csv`, `failed_parses.csv`, run metadata, prompt previews), or
- a **staged candidate queue** under `docs/analysis/gabriel_state_source_scout_candidates_<date>.csv`, explicitly marked per-row `verification_status=unverified` and `promotion_status=raw_model_output`.

No row in either location is a member of the causal or discourse corpus. No row has a `full_text_path` into `corpus/`. Nothing here satisfies `docs/schema.md`'s provenance-required fields, and nothing here should be cited as evidence in the claims ledger or any report.

## 4. What promotion would require

A candidate row graduates out of quarantine only by going through the existing, unchanged pipeline discipline — this tool does not shortcut any of it:

1. **Human/agent verification** — the `source_url` is fetched and confirmed to actually contain the claimed document (not a 404, not a paywall, not a different city/county with the same name — see the Erie County NY / Passaic County false-positive precedents in `pa_nj_candidate_sources_2026-07-12.csv`). Only then does `verification_status` move from `unverified` to `verified` or `rejected`.
2. **Promotion marking** — per `source_planning_csv_hygiene_standard_2026-07-08.md`'s categories (`ingest_next` / `needs_review` / `hold` / `reject`), not this tool's own `likely_ingest_priority` score, which is a heuristic triage signal, not a promotion decision.
3. **Ingestion** — a verified, promoted row still has to go through `ingest/fetchers/` or the `inbox/` + manifest + `ingest/process_inbox.py` path like any other source; this tool never writes to `corpus/` or `data/contracts.csv`.
4. **Validation** — `python scripts/validate.py` after any resulting corpus change, per `AGENTS.md`.

In short: this tool can move a candidate from "unknown" to "worth a human look," never from "unknown" to "in the corpus."

## 5. How this scales to a full state

- The script accepts `--municipalities-csv` to swap the bundled 10-city PA pilot list (`gabriel_state_source_scout_pa_pilot_municipalities_2026-07-14.csv`) for a full statewide gazetteer later — no code change needed, only a differently-sized input CSV with the same required `municipality_id,municipality,state` columns. Three-column files remain backward compatible. In minimal mode, optional full-context columns are used rather than ignored: government name/ID, requested units, selection purpose, anchor cycle, known source/cycle exclusions, known-source notes/URLs, verification cautions, and county geography.
- `--limit N` bounds how many municipalities are prompted in one run, independent of the input list's size — a full-state list can be loaded and worked through in batches across sessions.
- `--n-parallels` and `--max-prompts` bound concurrency and total live-call volume per run; a hard-coded `LIVE_HARD_CAP` (25) in the script prevents an accidental large-scale run — raising it requires a deliberate code edit, not a flag.
- Because each municipality's prompt is independent and stateless, the same script run against a 500-city gazetteer is mechanically identical to a 10-city pilot — only wall-clock and cost scale, not code complexity. The scoring/queue-builder stage (deterministic, no model calls) already operates on the full parsed-candidates table regardless of size.
- The main scaling risks are cost/rate **and transport availability**. `n_parallels` and `--max-prompts` manage request pressure, while the mandatory wrapper preflight and emergency-stop rule below prevent a network/proxy outage from being mistaken for a source result or amplified through retries.

## 5A. Mandatory live-batch transport preflight and emergency stop

Run a **one-prompt, no-search synthetic smoke test before every live scout batch**. A prior successful smoke test or scout batch does not waive the next batch's preflight. The preflight must use the same backend, model, base URL, authentication/header construction, and execution/network context intended for the scout, while keeping web search/tools disabled and using a synthetic prompt such as `Reply with OK.`. It is infrastructure-only and must not contain a municipality or source-research request.

For the Harvard HUIT proxy, prefer `--live-backend direct-sdk`. The direct SDK uses the proven Responses request shape and both required header names without GABRIEL's preliminary header-incomplete rate-limit probe. If a task explicitly chooses the historical GABRIEL backend, its preflight must use that wrapper and must pass the same evidence gate. Backend preference is not live-call authorization.

The preflight succeeds only when all applicable evidence agrees:

- response text is nonempty;
- a response ID is present when the wrapper/runtime exposes response IDs;
- neither the response nor the error metadata contains `Connection error.`;
- output tokens are greater than zero; and
- `model_response_succeeded` or equivalent wrapper success metadata is true.

If any required condition fails, **do not run the scout batch**. Preserve sanitized preflight metadata, error logs, token counts, response-ID presence/absence, runtime/package versions where already captured by the helper, and the exact non-secret command/configuration. Never save or print credential values.

If a live scout batch begins returning repeated connection errors with no response IDs and zero output tokens, stop immediately. Do not expand the batch and do not launch a broad retry pass. Preserve sanitized failure artifacts and diagnose the wrapper/network path separately before any new research call. A connection-error row is an infrastructure failure, not evidence that a municipality has no source.

The direct reference implementation is documented in `docs/analysis/direct_sdk_scout_backend_2026-07-20.md`; the older wrapper evidence is in `docs/analysis/gabriel_wrapper_smoke_test_2026-07-20.md`. This preflight is a necessary execution gate, not authorization to run a live scout; live research still requires the task's normal separate authorization and prompt cap.

## 5B. Full-context cycle and known-source contract

For national matched-repair and repeat-cycle slices, supply row-aware context whenever the repository already knows a city/unit/cycle/source. The minimal prompt accepts `scout_purpose`, `anchor_cycle`, `known_source_cycle_exclusions`, `known_source_notes`, and `known_source_urls` in addition to the national manifest columns. These columns are optional; their absence preserves the three-column fallback.

- Matched-comparison repair rows should state the existing anchor cycle. A candidate that does not overlap it remains visible but must be labeled `non_overlap_deferred` rather than counted as a repair.
- Repeat-cycle rows should identify already represented cycles and, where practical, exact canonical URLs. The scout should prioritize a different predecessor/successor cycle and label an exact known return as duplicate/context.
- Contract years require visible operative support: cover/title, duration clause, award period, or equivalent operative text. Index labels, snippets, URLs, and inference are uncertainty, not definitive cycle evidence.
- `blocked_or_unreadable` is separate from `dead_or_unreachable`. The latter is reserved for observed 404/410, DNS failure, or equivalent. A live official page/PDF that cannot be inspected is blocked/unreadable.
- A complete executed scanned MOA is not partial merely because text extraction is difficult; if it is binding and contains wage-setting terms, it remains a qualifying lead pending human verification.

## 5C. National-first queue and deferred verification

After each completed live batch, preserve its raw artifacts and add its candidate rows to `national_scout_candidate_queue_2026-07-20.csv` with `scripts/build_national_scout_candidate_queue.py`. Rebuild `national_scout_coverage_municipality_2026-07-20.csv`, `national_scout_coverage_state.csv`, and `national_scout_coverage_county.csv` with `scripts/build_national_scout_coverage_status.py`.

Routine post-scout review is deliberately light: confirm that the response parsed, keep explicit empty results, inspect metadata for obvious context/duplicate/employer/unit/access risks, assign a deterministic queue bucket, and stop. Do not open every URL. Existing TX/MA verification findings may inform calibration columns, but future rows remain unverified until a coordinated verification wave is separately selected.

Scout coverage counts a successful parseable candidate or no-candidate response. Connection-only failures are recorded separately and do not count as discovery coverage. Queue status, calibration verification, later-ingestion recommendation, canonical overlap, codified status, and claim status occupy separate fields and must never be collapsed.

This national-first sequence reduces verification burden: select later waves around high-value within-city police/fire/non-safety sets, institutional contrasts, and geographic gaps rather than reviewing every result or every government in the 35,589-row universe. Ingestion begins only after enough scouting and filtering exist to choose those waves rationally.

## 6. Schema — `gabriel_state_source_scout_candidates_<date>.csv`

One row = one candidate source document for one municipality + unit_type.

| field | type | notes |
|---|---|---|
| `run_id` | string | timestamp-based id shared by every row from one script invocation |
| `state` | string | 2-letter USPS |
| `municipality` | string | as returned/prompted |
| `municipality_id` | string | from the municipality list input |
| `unit_type` | enum | `police`, `fire`, `non_safety`, `unknown` |
| `union_name` | string | verbatim from model output |
| `employer` | string | verbatim from model output |
| `document_title` | string | verbatim from model output |
| `contract_years` | string | free text (model output rarely gives clean ISO ranges) |
| `source_url` | string | as returned; not verified |
| `source_owner` | string | verbatim from model output |
| `source_owner_type` | enum | `city`, `state_labor_board`, `union`, `school`, `third_party`, `news`, `unknown` |
| `document_type` | enum | `cba`, `arbitration_award`, `factfinding`, `memorandum_or_settlement`, `wage_schedule_or_compensation_plan`, `ordinance_or_policy`, `agenda_cover_sheet`, `meeting_minutes`, `index_page`, `context_only`, `blocked_or_unreadable`, `dead_or_unreachable`, `insufficient_source`, `unknown` |
| `candidate_stage` | enum | `qualifying_candidate`, `context_only_candidate`, `insufficient_candidate` |
| `document_completeness` | enum | `full_document`, `partial_document`, `summary_only`, `index_or_landing_page`, `blocked_or_unreadable`, `dead_or_unreachable`, `unclear` |
| `visible_year_evidence` | enum | `cover_or_title`, `duration_clause`, `award_period`, `other_operative_text`, `index_or_snippet_only`, `model_inference_only`, `unclear` |
| `overlap_with_anchor_cycle` | enum | `overlap`, `non_overlap_deferred`, `no_anchor_supplied`, `unclear` |
| `duplicate_risk` | enum | `none`, `possible`, `exact_known_source` |
| `blocked_or_unreadable_flag` | enum | `yes`, `no` |
| `cycle_match_notes` | string | visible-year basis, overlap result, deferral, or uncertainty |
| `comparator_role` | enum | `safety_target`, `ordinary_non_safety_comparator`, `authoritative_civilian_wage_setting`, `mechanism_context`, `no_comparator_role`, `unclear` |
| `wrong_employer_risk` | enum | `none`, `possible`, `high` |
| `context_only_flag` | enum | `yes`, `no` |
| `needs_verification_reason` | string | concise human/source-verification requirement |
| `triad_value` | enum | `high`, `medium`, `low` — derived from the scoring layer (Section 7) |
| `provenance_score` | number | 0-100, deterministic score from Section 7 |
| `likely_ingest_priority` | enum | `high`, `medium`, `low` — derived from `provenance_score` |
| `why_relevant` | string | verbatim from model output |
| `confidence` | string | verbatim from model output (model's own self-reported confidence, not verified) |
| `raw_response_ref` | string | path to this municipality's raw response file under `tmp/gabriel_state_source_scout/...` |
| `verification_status` | enum | default `unverified` (also `verified`, `rejected`) |
| `promotion_status` | enum | default `raw_model_output` (also `needs_review`, `ingest_next`, `hold`, `reject`, matching the existing hygiene standard's vocabulary) |

CSV hygiene: written with `csv.DictWriter`, parsed back and row-width/required-column-checked immediately after writing, per `source_planning_csv_hygiene_standard_2026-07-08.md`.

## 7. Scoring rules (deterministic, no model call)

Applied to every parsed candidate row to compute `provenance_score` (0-100, additive/subtractive points, clamped) and derived `likely_ingest_priority` / `triad_value`:

**Rewards:**
- official city (`.gov`/city-owned domain, or `source_owner_type=city`): +20
- state labor-board source (`source_owner_type=state_labor_board`): +20
- union-local source (`source_owner_type=union`): +12
- PDF or other direct-document link (URL ends `.pdf` or `document_type` in {`cba`, `arbitration_award`, `factfinding`, `pay_plan`}): +15
- current/recent contract cycle (any 4-digit year in `contract_years` >= 2018): +10
- matched-triad value (municipality has ≥2 distinct `unit_type` candidates this run, this row counts toward that): +10
- specific document title (`document_title` non-empty and not a generic placeholder like "contract" or "agreement"): +8
- specific union/employer named (`union_name` and `employer` both non-empty, not "unknown"): +8
- non-safety balance bonus (row is `unit_type=non_safety`, historically the bottleneck leg per `claim_testing_source_wave_methodology_2026-07-12.md` Section 3): +7

**Penalties:**
- news-only source (`source_owner_type=news`): -20
- context-only document (`document_type=context_only`): -20
- third-party document host (e.g. Scribd, DocumentCloud, generic file-sharing domains): -15
- missing URL: -25
- vague/generic title: -8
- uncertain jurisdiction (municipality name ambiguous with a same-named place in another state/county, and the model did not disambiguate): -15
- public-records-only path implied (`why_relevant`/`document_title` mentions FOIA/PRR/OPRA/RTKL as the only route): -25 (this project never files these; such a candidate is low-value even as a lead)
- school-only source not tied to municipal comparison (`source_owner_type=school` and `unit_type` not clearly municipal): -15
- blocked/unreadable source: -20 (kept distinct from the stronger dead/unreachable penalty)
- non-overlap/deferred candidate for a supplied anchor cycle: -20
- possible duplicate: -15; exact known source: -40

`provenance_score` is clamped to [0, 100]. `likely_ingest_priority`: `high` if score ≥ 65, `medium` if 35-64, `low` if < 35. `triad_value`: `high` if the municipality has all three unit types represented among its candidate rows this run, `medium` if two, `low` if one or zero.

## 8. Relationship to existing methodology

This tool's output is Step "0" feeding into `claim_testing_source_wave_methodology_2026-07-12.md`'s Steps 1-5 (choose claims → choose states → scan cities → mark candidates → promote). It does not replace that lifecycle's human-in-the-loop verification and promotion discipline (Steps 5-13 unchanged). Future agents should still read that document before promoting anything this tool surfaces.
