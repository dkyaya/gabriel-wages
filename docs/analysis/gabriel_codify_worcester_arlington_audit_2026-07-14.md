# GABRIEL Codify Worcester/Arlington — Sample Selection, Run Record & Audit — 2026-07-14

## Purpose and scope

A bounded, "cheap" codify wave (Part 1 of this session) against Worcester and Arlington, MA — both already fully ingested in `data/contracts.csv`, requiring no new sourcing. Deliberately scoped to these two cities only; Philadelphia and Trenton (both design-ready per `docs/analysis/state_city_claims_ledger.md`) were explicitly NOT touched this session.

## Repo state at start of this run

- Latest commit: `5adfd8e` — "Make claims ledger permanent; verify Columbus evidence-layer clean; document Somerville/San Antonio sourcing".
- `data/contracts.csv`: 64 rows, 19 cities (unchanged this session — no new ingestion).
- `docs/analysis/gabriel_codify_evidence_layer.csv`: 781 rows before this run.

## Candidate rows and selection

All 7 Worcester/Arlington rows currently in `data/contracts.csv`:

| contract_id | occupation_class | cycle | text_quality | plain-extraction result |
|---|---|---|---|---|
| `ma_worcester_fire_2017` | fire | 2017-2020 | ocr_messy | 9,809 chars (OCR) |
| `ma_worcester_clerical_admin_2017` | clerical_admin | 2017-2020 | clean | 7,132 chars |
| `ma_worcester_public_works_2017` | public_works | 2017-2020 | clean | 9,483 chars |
| `ma_arlington_fire_2021` | fire | 2021-2024 | ocr_messy (label stale — see below) | 123,383 chars (text_layer) |
| `ma_arlington_public_works_2015` | public_works | 2015-2018 | clean | 97,689 chars |
| `ma_arlington_public_works_2018` | public_works | 2018-2021 | clean | 103,579 chars |
| `ma_arlington_public_works_2021` | public_works | 2021-2024 | ocr_messy | 5,620 chars (text_layer) / 105,305 chars (OCR, this session) |

### Selected (5 of 7)

All 3 Worcester rows (fire, clerical_admin, public_works — Worcester's only occupation classes, forming its exact-cycle 2017-2020 matched triad) plus 2 of Arlington's 4 rows: `ma_arlington_fire_2021` and `ma_arlington_public_works_2021` — the one genuine exact-cycle matched pair (2021-2024), confirmed by `ingest/audit_coverage.py` as Arlington's sole "healthy matched pair."

### Not selected, and why

- `ma_arlington_public_works_2015` (2015-2018) and `ma_arlington_public_works_2018` (2018-2021) — neither overlaps `ma_arlington_fire_2021`'s 2021-2024 cycle (the 2018 row's cycle ends the day before fire's starts: adjacent, not overlapping). Including them would add repeat-cycle DPW context but no new matched-pair value, and would push this "cheap, bounded" wave toward padding rather than the specific goal (make Arlington's one real matched pair codifiable). Left out deliberately — a future session could codify these as MA repeat-cycle data points if that becomes a priority.

Both selections were made explicitly to serve `CLM-2026-07-12-03` (Massachusetts cross-occupation base) and, for Arlington specifically, `H1`/`H2`/`H7` (whether Ohio-style safety/non-safety asymmetry in impasse-backstop mechanisms generalizes).

## The Arlington public_works_2021 OCR recovery

`ma_arlington_public_works_2021`'s standard text-layer extraction returned only 5,620 characters across 35 pages (~160 chars/page — just above the pipeline's 100-chars/page OCR-fallback threshold, so it never triggered automatic OCR, even though only the first ~2 pages actually carried a text layer). A bounded, single-pass OCR run (`pdf2image` at 150 DPI + `pytesseract`, same method as the prior session's Wayland recovery) produced 105,305 characters — comparable to the adjacent 2018-2021 cycle's 103,579-character clean extraction — confirming the underlying document is a normal, full-length base CBA that simply lacked a text layer for most of its pages. This makes the row usable for the first time. Minor character-level OCR artifacts are present (e.g. "ClO" for "AFL-CIO", "Vil" for "VII") and were preserved verbatim in the excerpts below rather than silently corrected, per this project's capture-verbatim discipline. **Note:** the recovered text was used only to build this session's evidence window; `data/contracts.csv`'s `text_quality` field for this row was NOT changed (out of scope for a codify-only session — flagged as a candidate cleanup for a future session).

Separately, `ma_arlington_fire_2021` is labeled `ocr_messy` in `data/contracts.csv` but actually extracts cleanly via the text layer (123,383 characters, full 44-page document) — a stale/inaccurate label, also not corrected this session (out of scope; flagged for a future data-quality pass).

## Window construction and self-audit

5 evidence-window rows were built (`docs/analysis/gabriel_codify_worcester_arlington_evidence_windows_2026-07-14.csv`), 36 excerpts total, using neutral `--- Excerpt N [location] ---` separators (no codebook vocabulary in window bodies, consistent with the input-side contamination guard in `scripts/gabriel_codify_pilot.py`).

**Self-audit before any live call:** every one of the 36 hand-selected excerpts was independently re-extracted as an exact, whitespace-normalized substring directly from the source text (start/end anchor pairs resolved against the actual extracted document, not retyped by hand) and verified as a genuine contiguous match — 0 mismatches after two rounds of fixing (the first hand-typed draft had several transcription artifacts: a mis-typed curly quote, a page-footer string accidentally spanning two of my sentences, and a few line-wrap/whitespace assumptions that didn't match the real text; all were caught and fixed by this substring-verification step before any network call). Several excerpts intentionally preserve minor extraction-layer artifacts present in the actual source text (e.g. "shail" for "shall", stray "*" characters) rather than silently correcting them.

Dry run: `tmp/gabriel_codify_pilots/2026-07-14_145509/` — no network call, no credential read, input-side contamination check passed on all 5 windows (0 hits for any of the 19 codebook attribute names or generic tells).

## Live run

`tmp/gabriel_codify_pilots/2026-07-14_145533/` — **5 calls attempted, 5 succeeded, 0 failed.** No `errors.jsonl` written. One `gabriel.codify()` invocation per row, well under the 9-call hard cap (no code change to `HARD_MAX_CALLS` needed this session).

`docs/analysis/gabriel_codify_worcester_arlington_outputs_2026-07-14.csv` — **113 rows total: 49 present, 64 not_found.** This is a direct copy of `validated_outputs.csv` (the pilot script's own reshape/grounding/leakage-cleanup pipeline, unchanged since the 2026-07-10 fix).

## Source-grounding audit

**49/49 present excerpts pass the automated grounding check cleanly (`grounded`), 0 `unsupported`, 0 boundary-leakage flags, 0 mechanism-label-leakage flags.** The cleanest result of any codify wave in this project to date (every prior wave had at least a few flagged/unclear rows). Excerpt length: min 11 words, max 103 words, average 34.0 words — one excerpt (103 words, the Disability Reform Law passage) runs longer than the 40-word instruction guidance, a minor, known instruction-adherence gap consistent with prior waves, not a correctness problem.

## Whether this run is safe to append to the evidence layer/viewer

**Yes, cleanly, no flagged rows to carry forward.** Ran:
```
python scripts/build_codify_evidence_viewer.py \
  --input docs/analysis/gabriel_codify_full_codebook_outputs_2026-07-09.csv \
  --input docs/analysis/gabriel_codify_texas_ohio_scaleup_outputs_2026-07-09.csv \
  --input docs/analysis/gabriel_codify_massachusetts_outputs_2026-07-09.csv \
  --input docs/analysis/gabriel_codify_expanded_texas_ohio_outputs_2026-07-10.csv \
  --input docs/analysis/gabriel_codify_seekonk_wayland_outputs_2026-07-10.csv \
  --input docs/analysis/gabriel_codify_worcester_arlington_outputs_2026-07-14.csv \
  --evidence-out docs/analysis/gabriel_codify_evidence_layer.csv \
  --html-latest-out docs/analysis/gabriel_codify_excerpt_browser_latest.html \
  --archive-html docs/analysis/gabriel_codify_excerpt_browser_2026-07-14_worcester_arlington.html
```
Result: 894 total input rows read across all 6 waves, **0 duplicate rows skipped** (idempotent append confirmed), 894 evidence rows written. 342 present (up from an implied 293 before this run), 333 verified present (up from 284), 9 rows flagged in notes (unchanged — all pre-existing from prior waves; this run added zero new flagged rows).

## Attribute-level findings

Per-contract present-attribute sets:

- **`ma_worcester_fire_2017`** (6): `overtime_callback_holdover_mandatory_extra_work`, `benefits_total_compensation_or_pension`, `subcontracting_outsourcing_or_volunteer_substitution`, `management_rights_or_service_flexibility`, `civil_service_or_statutory_employment_channel`, `budget_capacity_or_fiscal_constraint`.
- **`ma_worcester_clerical_admin_2017`** (4): `grievance_or_contract_interpretation_arbitration`, `classification_reclassification_or_grade_structure`, `benefits_total_compensation_or_pension`, `other`.
- **`ma_worcester_public_works_2017`** (3): `overtime_callback_holdover_mandatory_extra_work`, `classification_reclassification_or_grade_structure`, `budget_capacity_or_fiscal_constraint`.
- **`ma_arlington_fire_2021`** (9): `civil_service_or_statutory_employment_channel`, `hazard_risk_stress_or_line_of_duty_rationale`, `interest_arbitration_or_formal_impasse_backstop`, `management_rights_or_service_flexibility`, `no_strike_or_work_stoppage_constraint`, `overtime_callback_holdover_mandatory_extra_work`, `staffing_shortage_recruitment_retention`, `union_security_or_institutional_power`, `other`.
- **`ma_arlington_public_works_2021`** (9): `civil_service_or_statutory_employment_channel`, `classification_reclassification_or_grade_structure`, `grievance_or_contract_interpretation_arbitration`, `interest_arbitration_or_formal_impasse_backstop`, `management_rights_or_service_flexibility`, `no_strike_or_work_stoppage_constraint`, `overtime_callback_holdover_mandatory_extra_work`, `premium_pay_differentials`, `subcontracting_outsourcing_or_volunteer_substitution`.

**Worcester's three documents are thin by construction, not by extraction failure.** All three are wage/benefits *amendment* MOAs to a prior base contract not in this corpus (the fire and public_works MOAs are explicitly "off the record... not binding until approved," and the public_works MOA is titled "DRAFT #1" on its own cover) — they amend specific articles (wages, health insurance, sick leave, a new probationary-period clause, a position reclassified out of the bargaining unit) rather than restating a full agreement. No recognition/no-strike/interest-arbitration/minimum-staffing article is visible in any of the three windows, which correctly and honestly reflects what these specific documents contain — not an absence of those provisions in Worcester's underlying labor relationships (the base contracts they amend are simply not in this corpus).

**Arlington fire and Arlington public_works — the corpus's richest genuine matched PAIR (not triad) result — share 5 attributes**: `civil_service_or_statutory_employment_channel`, `interest_arbitration_or_formal_impasse_backstop`, `management_rights_or_service_flexibility`, `no_strike_or_work_stoppage_constraint`, `overtime_callback_holdover_mandatory_extra_work`. This is a genuinely important and somewhat unexpected result — see the claim-driven analysis in `docs/analysis/state_city_claims_ledger.md`'s Arlington section and the hypothesis-tracker update below: **both the safety and non-safety row show interest-arbitration/impasse-backstop AND no-strike language**, a symmetric pattern that differs from the Ohio triads' asymmetric pattern (safety has interest-arbitration, non-safety typically doesn't) underlying `CLM-2026-07-12-01`. Both documents cite the same Massachusetts statutory impasse mechanism (Chapter 1078 of the Acts of 1973, "mediation and fact-finding") — i.e., in Arlington, both occupation classes access the *same* town-wide statutory impasse channel, not a safety-specific one.

## Whether excerpts were short and usable

Yes — 49/49 grounded cleanly, no cleanup needed, all excerpts are short (avg 34 words) verbatim clause-level spans.

## Comparison with deterministic extraction

No dedicated deterministic-extraction excerpt CSV exists for Worcester/Arlington (unlike the `interest_arbitration_flag`/`no_strike_clause_flag` etc. in `data/contracts.csv`, which capture only binary flags, not spans, for a narrower trigger set than GABRIEL's 19-attribute codebook). Spot-checked: `data/contracts.csv`'s `ma_arlington_fire_2021` row's `interest_arbitration_flag` and `ma_arlington_public_works_2021`'s `no_strike_clause_flag` — **not yet checked against this session's codify findings**; flagged as a cross-check worth running in a future session (the deterministic layer's `no_strike` regex trigger list should, in principle, also catch the same "no strike"/"work stoppage" language this codify wave found independently — consistency between the two layers would be a useful validation, inconsistency would be a new investigation).

## Recommended next step

Per this run's own findings: Philadelphia and Trenton remain the strongest next codify-wave candidates (see Part 2 below and the updated ledger). This Worcester/Arlington wave is complete and clean; no rework needed.
