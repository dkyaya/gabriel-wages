# Texas/Ohio Source-Expansion Preflight — 2026-07-10

## Purpose

Expand the Texas and Ohio source base — matched safety/non-safety comparisons and institutional contrast — before the next GABRIEL/codify run and before report scaffolding begins. **This run performs no GABRIEL/codify calls, no Harvard Proxy calls, and no model/API calls of any kind.**

## Repo state at start of this run

- `git status`: clean except the pre-existing, untracked `tmp/` scratch directory. No unexpected uncommitted changes.
- Latest commit: `24a035f` — "Add Seekonk and Wayland to codify viewer".
- `data/contracts.csv`: **44 data rows**.
- `data/city_coverage.csv`: **44 data rows**.
- Distinct cities (`city_id`): **13**.
- Healthy matched pairs (`ingest/audit_coverage.py`): **18** (confirmed at session start, see Task K).

All counts match this run's expected starting state exactly.

## Existing Texas/Ohio contract_ids (grouped by state/city/occupation)

| state | city | occupation_class | source_type | cycle | text_quality | obs_id |
|---|---|---|---|---|---|---|
| TX | Houston | police | cba | 2024-07-01–2025-06-30 | clean | `tx_houston_police_2024` |
| TX | Houston | fire | arbitration_award | 2024-07-01–2029-06-30 | clean | `tx_houston_fire_2024` |
| TX | Houston | other | cba | 2024-11-01–2027-06-30 | clean | `tx_houston_other_2024` |
| TX | Austin | police | cba | 2024-10-29–2029-09-30 | ocr_messy | `tx_austin_police_2024` |
| TX | Austin | fire | cba | 2023-09-24–2025-09-30 | clean | `tx_austin_fire_2023` |
| TX | Austin | nurse_health | cba | 2023-10-01–2027-09-30 | clean | `tx_austin_nursehealth_2023` |
| OH | Columbus | police | cba | 2023-12-09–2026-12-08 | clean | `oh_columbus_police_2023` |
| OH | Columbus | fire | cba | 2023-11-01–2026-10-31 | clean | `oh_columbus_fire_2023` |
| OH | Columbus | other | cba | 2024-04-01–2027-03-31 | clean | `oh_columbus_other_2024` |
| OH | Cleveland | police | cba | 2025-04-01–2028-03-31 | clean | `oh_cleveland_police_2025` |
| OH | Cleveland | fire | cba | 2025-04-01–2028-03-31 | ocr_messy | `oh_cleveland_fire_2025` |
| OH | Cleveland | other | cba | 2022-04-01–2025-03-31 | clean | `oh_cleveland_other_2022` |

12 TX/OH rows total. Houston and Columbus each have a full safety+non-safety matched triad (exact-cycle or overlap-cycle). Austin has police+fire+nurse_health (a safety-adjacent, not general-municipal, comparison). Cleveland has police+fire+other (matched, overlap-cycle).

## Current codify coverage for TX/OH

Per `docs/analysis/gabriel_codify_evidence_layer.csv` (603 rows total as of the last codify run): Houston, Austin, Columbus, and Cleveland are all already codified (Texas/Ohio pilot + scale-up batches, 2026-07-09). **This run adds no new codify rows** — new sources ingested here become codify-ready for the *next* batch, not this one.

## Reason for expanding before the report

1. **Overfitting risk already identified by this project's own prior research.** `texas_ohio_multicity_pre_ingestion_scan_2026-07-08.md` explicitly warned that Houston is population-exceptional (its compulsory fire arbitration and Chapter 146 non-safety channel are gated to cities above 1.9M/1.5M residents respectively — thresholds only Houston meets in Texas) and that treating Houston+Columbus alone as "Texas and Ohio" would risk reporting Houston-specific institutional exceptions as general findings. That scan's own "first batch" recommendation (Houston+Austin, Columbus+Cleveland) has already been executed; this run picks up its documented "backup" tier.
2. **Ohio's institutional framework (ORC 4117/SERB) is uniform statewide, unlike Massachusetts's varying-town-size design or Texas's population-gated statutes** — a second/third Ohio city is a low-cost, low-risk way to demonstrate the Ohio comparison isn't overfit to Columbus, per the prior scan's own Section 6 finding.
3. **Texas's non-safety statutory bargaining channel is essentially Houston-only** among cities examined so far — the prior scan found no confirmed non-safety CBA/negotiated-agreement channel in San Antonio, Dallas, or Fort Worth. This run tests whether that finding still holds and, if so, documents it explicitly rather than forcing a mismatched source into the corpus.
4. **The next major milestone (codify → rebuild viewer → report with GABRIEL-coded mechanism graphs) is more defensible with a broader, non-overfit Texas/Ohio base** — this is the last opportunity to add TX/OH breadth before that pipeline runs.

## Target source types

`cba` (primary), `arbitration_award`/`factfinding` (secondary, opportunistic — e.g., Ohio SERB filings) — **never** budget/pay-plan/statute/context-only documents as causal rows (per this run's explicit boundary).

## Target cities

- **Texas backups (priority order per this run's task instructions):** San Antonio, Dallas, Fort Worth, El Paso.
- **Ohio backups (priority order per this run's task instructions):** Cincinnati, Toledo, Dayton, Akron.

The prior multi-city scan's own city-comparison table (Section 7 of `texas_ohio_multicity_pre_ingestion_scan_2026-07-08.md`) will be used as the starting point for Task B's source plan, with each candidate URL independently re-verified this session (Task C) before any download.

## Stop rules

- No GABRIEL/codify, Harvard Proxy, or model/API calls of any kind in this run.
- No FOIA/PRR — public-download sources only.
- No discourse/proxy/context-only material (statutes, SERB guidance pages, budget/pay-plan documents, news coverage) added as causal `contracts.csv` rows — legal/institutional context sources are documented as context only, not ingested as causal rows.
- No edits to existing corpus files except a documented filename/path typo fix, if one is found.
- No `docs/schema.md` changes.
- No final report PDF/DOCX artifacts.
- No causal claims stronger than the source evidence supports — this run adds source rows and deterministic verbatim excerpts only; mechanism-presence judgments remain GABRIEL's job in the next codify run, not this session's.
- Recognition-clause-first: any broad/mixed non-safety agreement gets `occupation_class=other` until coverage is confirmed narrower.
- If a candidate source cannot be confirmed as an official public-download document with clear provenance, it is deferred/documented as not ingested rather than force-added.

## Explicit confirmation: no GABRIEL/codify/model/API calls authorized this run

This preflight memo, and every subsequent task in this run, is scoped to source discovery, download, text extraction, quality assessment, `data/contracts.csv`/`data/city_coverage.csv` updates, and deterministic (non-model) excerpt preparation only. GABRIEL/codify of the newly added sources is explicitly deferred to a future session, per this run's own task instructions.
