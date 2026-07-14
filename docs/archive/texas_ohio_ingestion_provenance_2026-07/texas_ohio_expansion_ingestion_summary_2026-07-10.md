# Texas/Ohio Source-Expansion Ingestion Summary — 2026-07-10

## Context: interrupted-run recovery

This run's terminal session was accidentally closed mid-execution, likely around Task G (writing the new rows to `data/contracts.csv`/`data/city_coverage.csv`). This document is written by the recovery/completion run, which treated the repo's actual file state as ground truth rather than re-running the original prompt from the top.

### What was already complete before the interruption

Recovered from the working tree (uncommitted, but on disk) at the start of this recovery run:

- `docs/analysis/texas_ohio_expansion_preflight_2026-07-10.md` (Task A) — complete.
- `docs/analysis/texas_ohio_expansion_source_plan_2026-07-10.csv` (Task B/C, 22 candidate rows) — complete.
- `docs/analysis/texas_ohio_expansion_selection_2026-07-10.md` (Task D, 9 sources selected) — complete.
- `docs/analysis/texas_ohio_expansion_text_quality_2026-07-10.csv` (Task F, 10 rows incl. header) — complete.
- 9 source PDFs already downloaded into `corpus/tx_san_antonio/`, `corpus/oh_cincinnati/`, `corpus/oh_toledo/`.
- `data/contracts.csv` — **already had all 9 new rows appended** (44 → 53 data rows).
- `data/city_coverage.csv` — **already had all 9 matching new rows appended** (44 → 53 data rows).

**Conclusion: Task G had already completed cleanly before the interruption.** The interruption appears to have occurred after Task G but before Task H (mechanism excerpt extraction) began — that file did not exist on disk, and no partial/malformed rows, truncated CSV lines, or duplicate `obs_id`/`contract_id` values were found in either CSV.

### What this recovery run completed

1. Full recovery audit (git status, file inventory, diff review) — confirmed no corruption, no duplication, no partial rows.
2. Ran `python scripts/validate.py` — **PASSED** (53 contracts, 53 coverage, 0 discourse, 3 city_attributes).
3. Ran `python ingest/audit_coverage.py` — confirmed Cincinnati and Toledo are now healthy police+fire+other matched triads (overlap-cycle); San Antonio correctly flagged as unmatched (no non-safety comparison unit exists for it, as documented at selection time).
4. Custom audit: row-width checks, duplicate-ID checks, controlled-vocabulary checks (`occupation_class`, `source_type`, `source_corpus`, `retrieval_method`, `text_quality`), `safety_flag` consistency, `full_text_path` existence — all clean.
5. Created `docs/analysis/texas_ohio_expansion_mechanism_excerpt_extraction_2026-07-10.csv` (Task 3 of this recovery run / originally Task H) — 8 excerpt rows across 6 of the 9 new contracts, built entirely from verbatim clause text already captured in `contracts.csv`/`texas_ohio_expansion_text_quality_2026-07-10.csv` during the pre-interruption session. No new PDF reading, no GABRIEL/codify, no model calls.
6. Created this summary document.
7. Lightly updated `docs/analysis/wage_mechanism_evidence_checklist.md`, `docs/analysis/report_review_checklist_safety_non_safety_wage_mechanisms_2026-07-06.md`, and `docs/analysis/all_groups_source_needs_2026-07-06.csv`.
8. Updated `PROGRESS.md` and `docs/analysis/chatgpt_handoff_latest.md`.

## Sources searched

Per `texas_ohio_expansion_source_plan_2026-07-10.csv` (22 candidate rows spanning San Antonio, Dallas, Fort Worth, El Paso in Texas; Cincinnati, Toledo, Dayton, Akron in Ohio).

## Sources selected and ingested (9)

| # | contract_id | state | city | occupation_class | source_type | text_quality |
|---|---|---|---|---|---|---|
| 1 | `tx_san_antonio_police_2022` | TX | San Antonio | police | cba | partial (no text layer) |
| 2 | `tx_san_antonio_fire_2024` | TX | San Antonio | fire | cba | clean |
| 3 | `oh_cincinnati_police_2024` | OH | Cincinnati | police | cba | clean |
| 4 | `oh_cincinnati_police_sup_2024` | OH | Cincinnati | police | cba | clean |
| 5 | `oh_cincinnati_fire_2023` | OH | Cincinnati | fire | cba | clean |
| 6 | `oh_cincinnati_other_2025` | OH | Cincinnati | other | cba | clean |
| 7 | `oh_toledo_police_2024` | OH | Toledo | police | cba | clean |
| 8 | `oh_toledo_fire_2024` | OH | Toledo | fire | cba | clean |
| 9 | `oh_toledo_other_2024` | OH | Toledo | other | cba | clean |

All 9 use `source_type=cba`, `source_corpus=causal`, `retrieval_method=public_download`. No FOIA/PRR retrieval method was used or introduced anywhere in `contracts.csv` (verified: all 53 rows use `public_download`).

## Rejected / deferred sources

- **San Antonio non-safety**: re-searched live; only a non-binding AFSCME "representation" process found, no signed CBA — not force-added.
- **Dallas (police/fire joint, non-safety)**: joint agreement only confirmed via aggregator/mirror hosting, not an official city domain; non-safety runs through a civil-service pay plan, not a negotiated CBA — excluded.
- **Fort Worth (police, fire)**: current-cycle full-text URL not directly located — deferred as a backup candidate.
- **Fort Worth non-safety, El Paso (all tiers)**: no negotiated CBA found, or union-hosted-only secondary sourcing — excluded/deferred.
- **Toledo Police Command Officers' Association (TPCOA)**: URL located but not independently re-verified live, and not needed for this batch's design goals — documented as a backup.
- **Dayton (police, fire, non-safety)**: relying on the prior 2026-07-08 scan only, not re-verified live this session — documented as backup.
- **Akron (all tiers)**: weakest-documented Ohio city, not explored — deferred.

Full detail for every considered source is in `docs/analysis/texas_ohio_expansion_source_plan_2026-07-10.csv`.

## New contract_ids (9)

`tx_san_antonio_police_2022`, `tx_san_antonio_fire_2024`, `oh_cincinnati_police_2024`, `oh_cincinnati_police_sup_2024`, `oh_cincinnati_fire_2023`, `oh_cincinnati_other_2025`, `oh_toledo_police_2024`, `oh_toledo_fire_2024`, `oh_toledo_other_2024`

## New city_coverage rows (9)

One matching row per new contract_id above — confirmed 1:1, no orphans in either direction.

## New matched cities / pairs

- **Cincinnati, OH**: new complete police+fire+non-safety triad (overlap-cycle match), plus a bonus police non-supervisor/supervisor rank split. Third Ohio city with a healthy matched triad (after Columbus, Cleveland).
- **Toledo, OH**: new complete police+fire+non-safety triad (overlap-cycle match). Fourth Ohio matched city.
- **San Antonio, TX**: police + fire added, but **remains unmatched** — no confirmed non-safety bargaining channel exists for San Antonio. Retained for institutional-contrast value (full Chapter 174 bargaining without Houston's population-triggered compulsory-arbitration exception), not for the matched-comparison design. `ingest/audit_coverage.py` correctly flags both San Antonio rows as safety-units-without-comparison.

Ohio now has **4** healthy matched cities (Columbus, Cleveland, Cincinnati, Toledo); Texas still has only **1** fully matched city (Houston), with Austin as a safety-adjacent (nurse_health) match and San Antonio as an intentionally unmatched institutional-contrast addition.

## Text quality summary

- 8 of 9 new sources: `clean` native-PDF extraction (200K+ chars each, recognition clauses independently locatable).
- 1 of 9 (`tx_san_antonio_police_2022`): `partial` — 218-page image scan (Xerox WorkCentre 7855, 270° rotation) with no text layer; `pdftotext` yielded ~0 usable characters. No OCR was performed (out of this run's authorized scope). Union identity and cycle dates were taken from the source portal's own filename/path, consistent with this project's existing `ma_boston_police_2020`/`ma_newton_police_2015` partial-quality precedent.

## Deterministic mechanism families observed (this batch)

Captured in `texas_ohio_expansion_mechanism_excerpt_extraction_2026-07-10.csv` (8 excerpt rows, 6 of 9 contracts represented):

- **recognition** (5 excerpts): Cincinnati police non-supervisors, Cincinnati CODE (other), Toledo police, Toledo fire, Toledo AFSCME 2058 (other).
- **grievance_arbitration** (2 excerpts): San Antonio fire, Cincinnati police non-supervisors.
- **narrow_issue_arbitration_reopener** (1 excerpt): Toledo AFSCME 2058 — a health-insurance-cost reopener clause, explicitly distinct from general interest arbitration.

Three of the 9 new contracts (`tx_san_antonio_police_2022`, `oh_cincinnati_police_sup_2024`, `oh_cincinnati_fire_2023`) contributed **zero** excerpt rows: San Antonio police because its text has no extractable layer; the other two because their recognition clauses were confirmed present at extraction time but not separately quoted verbatim in this session's working notes. This is a documented gap, not an omission — no clause text was fabricated or paraphrased into the excerpt file.

No new GABRIEL/codify mechanism coding was performed. Mechanism-*strength* or -*presence* judgment remains GABRIEL's job in a future codify run; this file records only verbatim, source-grounded spans deterministically pulled from work already done during ingestion.

## Expected next codify batch size

9 new causal sources across 3 cities (San Antonio, Cincinnati, Toledo), all `text_quality=clean` except one `partial` row. Consistent with the prior Texas/Ohio codify batches (Houston, Austin, Columbus, Cleveland), this is a reasonably sized next codify batch — no further source expansion is required before running it.

## Limitations

- Texas remains structurally harder to expand on the matched-comparison design than Ohio: only Houston has a confirmed matched triad; Austin's non-safety comparison (EMS) is safety-adjacent, not a general-municipal unit; San Antonio, Dallas, Fort Worth, and El Paso all lack a confirmed negotiated non-safety CBA channel as of this session's live re-checks.
- `tx_san_antonio_police_2022` is `text_quality=partial` with cycle dates estimated from the source portal's filename, not confirmed from document text — treat with the same caution as this project's existing partial-quality Massachusetts rows.
- Mechanism excerpts in this batch are opportunistic (whatever verbatim spans were already captured during ingestion), not an exhaustive per-clause-type extraction pass — a future codify run may surface additional mechanism families (comparability, me-too, longevity) not captured here.
- No arbitration-award, fact-finding, or impasse documents were added this batch — all 9 are base CBAs; Ohio's SERB archive remains an untapped source of such documents for a future session.
- This run performed no GABRIEL/codify calls, no Harvard Proxy calls, no model/API calls, and no FOIA/PRR retrieval, consistent with this run's explicit scope boundary.
