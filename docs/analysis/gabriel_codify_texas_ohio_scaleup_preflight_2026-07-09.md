# GABRIEL Codify Texas/Ohio Scale-Up Preflight — 2026-07-09

## Purpose

This is the first scaled GABRIEL/codify run after the PI-facing evidence-viewer overhaul (commit `632a4a5`). It extends codify coverage from the 4-row full-codebook pilot to up to 8 additional Texas/Ohio matched-city rows, using the same binary `present`/`not_found` semantics, the same 19-attribute codebook, and the same Harvard Proxy adapter. This memo records repo state and safety checks before any live call is made.

## Repo state at start of this run

- `git status`: clean except the pre-existing, gitignored-by-convention `tmp/` scratch directory (untracked; not part of this run's inputs). No unexpected uncommitted changes.
- Latest commit: `632a4a5` — "Overhaul codify excerpt viewer" (the PI-facing viewer overhaul run).
- `data/contracts.csv`: **44 data rows** (header + 44).
- `data/city_coverage.csv`: **44 data rows** (header + 44).
- `docs/analysis/gabriel_codify_evidence_layer.csv`: **92 data rows** (53 present, 39 not_found — the 4-row pilot's output, carried through the viewer overhaul with no new codify calls).

All counts match this run's expected starting state exactly.

## Already-coded contract_ids (do not re-run)

From the 4-row full-codebook pilot (2026-07-09, Harvard Proxy):
- `tx_houston_fire_2024`
- `tx_houston_other_2024`
- `tx_austin_nursehealth_2023`
- `oh_columbus_fire_2023`

## Selected remaining Texas/Ohio contract_ids for this run (max 8 live calls)

All 8 confirmed present in `data/contracts.csv` (obs_id match) with a corresponding corpus file on disk under `corpus/`:

| # | contract_id | state | city | occupation_class | source_type | corpus file |
|---|---|---|---|---|---|---|
| 1 | `tx_houston_police_2024` | TX | Houston | police | cba | `corpus/tx_houston/tx_houston_hpou_police_meet_confer_2024.pdf` |
| 2 | `tx_austin_police_2024` | TX | Austin | police | cba | `corpus/tx_austin/tx_austin_apa_police_meet_confer_2024_2029.pdf` |
| 3 | `tx_austin_fire_2023` | TX | Austin | fire | cba | `corpus/tx_austin/tx_austin_afa975_fire_cba_2023_2025.pdf` |
| 4 | `oh_columbus_police_2023` | OH | Columbus | police | cba | `corpus/oh_columbus/oh_columbus_fop_lodge9_police_cba_2023_2026.pdf` |
| 5 | `oh_columbus_other_2024` | OH | Columbus | other | cba | `corpus/oh_columbus/oh_columbus_afscme1632_cba_2024_2027.pdf` |
| 6 | `oh_cleveland_police_2025` | OH | Cleveland | police | cba | `corpus/oh_cleveland/oh_cleveland_cppa_patrol_police_cba_2025_2028.pdf` |
| 7 | `oh_cleveland_fire_2025` | OH | Cleveland | fire | cba | `corpus/oh_cleveland/oh_cleveland_iaff93_fire_cba_2025_2028.pdf` |
| 8 | `oh_cleveland_other_2022` | OH | Cleveland | other | cba | `corpus/oh_cleveland/oh_cleveland_afscme_local100_cba_2022_2025.pdf` |

Evidence windows for all 8 are built entirely from **already-extracted, already-verified verbatim excerpts** captured in this project's prior hand-extraction files (`texas_ohio_mechanism_excerpt_extraction_2026-07-08.csv` and `texas_ohio_second_batch_mechanism_excerpt_extraction_2026-07-08.csv`) — no new corpus ingestion, no new document opening, no invented text. See Task C deliverable for the assembled windows.

This gives all 8 Texas/Ohio matched cities from `texas_ohio_ingestion_extraction_summary_2026-07-08.md` at least one codified safety AND one codified non-safety/comparison row once this run and the prior pilot are combined (Houston: police+fire+other; Austin: police+fire+nurse_health; Columbus: police+fire+other; Cleveland: police+fire+other).

## Why Massachusetts is held for the next run

This run's explicit scope is Texas/Ohio only. Massachusetts has extensive corpus and theory material already staged (label maps in `scripts/build_codify_evidence_viewer.py` already include `ma`, per the prior overhaul session), but running it now would combine two untested things at once — the append/union builder mode (Task B, new this run) and a new state's evidence windows. Proving the append workflow cleanly on a second Texas/Ohio batch first means any bug surfaces against known-good data, not against a first-of-its-kind Massachusetts batch. The recommended next scale-up, once this run is confirmed safe, is a curated Massachusetts codify batch.

## Live-call cap

- **Hard cap for this run: 8 live calls**, one per selected row (corrected from the original 7-row list to 8 remaining rows per this run's own instructions).
- `scripts/gabriel_codify_pilot.py`'s in-code `HARD_MAX_CALLS` is raised from `4` to `8` as a deliberate, documented code change for this run only (see Task D/E). `--max-calls` above 8 is still refused.
- One `gabriel.codify()` invocation per row (not batched), so a failure on row N does not affect rows 1..N-1.

## Credential / adapter safety check (presence only, no values read)

- `HARVARD_SUBSCRIPTION_KEY` is **not** set in the ambient shell environment.
- A git-ignored `.env` file is present in the repo root; loading it via `python-dotenv`'s `load_dotenv()` makes `HARVARD_SUBSCRIPTION_KEY` available (checked as a boolean only — value never printed, logged, or written to any file in this repo).
- This matches the same adapter path used successfully in the 2026-07-09 4-row pilot (`gabriel_codify_harvard_proxy_adapter_design_2026-07-09.md`), so live calls are expected to be possible in this run, contingent on Task D's dry run and Task E's first-call check.

## Stop rules (unchanged from the pilot design, restated for this run)

- Dry run first, always.
- If credentials are unavailable at live-run time, do not live-run; dry-run outputs only.
- If the first live call fails for a nontrivial adapter/API reason, stop all live calls immediately — do not retry.
- If a later row fails for a row-specific text/window reason, skip that row, record why, and continue only if the failure is clearly row-specific (not systemic).
- Never exceed 8 live calls in this run.
- Do not run Massachusetts.
- Do not run the full corpus.
- No edits to `data/contracts.csv`, `data/city_coverage.csv`, or `corpus/` at any point.
