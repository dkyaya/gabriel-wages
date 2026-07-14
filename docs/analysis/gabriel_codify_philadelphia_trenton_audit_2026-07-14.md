# GABRIEL Codify Philadelphia/Trenton — Sample Selection, Run Record & Audit — 2026-07-14

## Purpose and scope

Task 5 of this session: codify Philadelphia, PA and Trenton, NJ — the two strongest remaining design-ready PA/NJ cities — only after Tasks 1-4 (ledger rebuild, no_strike extractor fix, corpus-wide regression) were complete and clean. Regression confirmed `SUMMARY: 0 rows with flag changes, 0 extraction errors, 0 timed out` before this wave began.

## Repo state at start of this run

- Latest commit at session start: `d434f6f`.
- `data/contracts.csv`: 64 rows, 19 cities, with 2 field corrections applied earlier this session (`ma_arlington_fire_2021`, `tx_san_antonio_fire_2024` `no_strike_clause_flag` 0→1, per checklist item 19).
- `docs/analysis/gabriel_codify_evidence_layer.csv`: 894 rows before this run (6 prior waves).

## Candidate rows and selection

| contract_id | occupation_class | cycle | source_type | text_quality |
|---|---|---|---|---|
| `pa_philadelphia_police_2025` | police | 2025-2027 | arbitration_award | clean |
| `pa_philadelphia_fire_2017` | fire | 2017-2020 | arbitration_award | ocr_messy |
| `pa_philadelphia_other_2025` | other | 2025-2028 | cba | ocr_messy |
| `pa_philadelphia_other_2017` | other | 2017-2020 | cba | ocr_messy |
| `pa_philadelphia_other_2021` | other | 2021-2024 | cba | ocr_messy |
| `nj_trenton_police_2019` | police | 2019-2024 | cba | ocr_messy |
| `nj_trenton_fire_2021` | fire | 2021-2026 | cba | ocr_messy |
| `nj_trenton_other_2019` | other | 2019-2023 | cba | ocr_messy |

### Selected (7 of 8)

Per the task's own framing ("Philadelphia is matched on both legs: police/non-safety and fire/non-safety"): `pa_philadelphia_police_2025` + `pa_philadelphia_other_2025` (overlap-cycle, both 2025-202x) and `pa_philadelphia_fire_2017` + `pa_philadelphia_other_2017` (exact-cycle, both 2017-2020) — 4 rows. Per "Trenton is a matched triad with all three legs overlapping": all 3 Trenton rows (pairwise overlap 2021-2023) — 3 rows. Total 7, under the 9-call hard cap.

### Not selected, and why

`pa_philadelphia_other_2021` (AFSCME DC33, 2021-2024) does not overlap either Philadelphia matched cycle (ends 2024, before police's 2025-2027 starts; starts 2021, after fire's 2017-2020 ends) — no matched-pair value for this wave, excluded to keep the wave bounded and focused on the two genuine matched legs named in the task.

## Window construction and self-audit

7 evidence-window rows were built (`docs/analysis/gabriel_codify_philadelphia_trenton_evidence_windows_2026-07-14.csv`), 37 excerpts total, using the same exact-substring extraction method introduced in the Worcester/Arlington wave (start/end anchor pairs resolved directly against the actual extracted, whitespace-normalized source text — not hand-retyped). **All 37 excerpts verified as genuine, unmodified, contiguous substrings on the first build pass** (one anchor needed correction before the first successful build; zero mismatches after).

Dry run: `tmp/gabriel_codify_pilots/2026-07-14_155424/` — no network call, no credential read, input-side contamination check passed on all 7 windows.

## Live run

`tmp/gabriel_codify_pilots/2026-07-14_163232/` — **7 calls attempted, 7 succeeded, 0 failed.** No `errors.jsonl` written.

`docs/analysis/gabriel_codify_philadelphia_trenton_outputs_2026-07-14.csv` — as originally written by the pilot script: 142 rows, 39 present, 103 not_found. **As corrected during this session's audit (see below): 145 rows, 46 present, 99 not_found.**

## Source-grounding audit

**35/39 present excerpts (89.7%) passed the automated grounding check cleanly on the first pass.** 4/39 (10.3%) were automatically detected as boundary-leakage cases and correctly downgraded to `unclear` with a full explanatory note — consistent with the ~9% rate seen in the Seekonk/Wayland wave, not a new failure mode:

| contract_id | attribute | what happened |
|---|---|---|
| `pa_philadelphia_other_2017` | `civil_service_or_statutory_employment_channel` | Excerpt crossed one separator boundary; cleaned to the longer, genuine side. |
| `pa_philadelphia_other_2017` | `other` | Excerpt crossed one separator boundary; cleaned to the longer, genuine side. |
| `nj_trenton_fire_2021` | `grievance_or_contract_interpretation_arbitration` | Excerpt crossed one separator boundary; cleaned to the longer, genuine side. |
| `nj_trenton_other_2019` | `union_security_or_institutional_power` | Excerpt crossed one separator boundary; cleaned to the longer, genuine side. |

0/39 mechanism-label-leakage flags.

## A new failure mode found and resolved: duplicate-key JSON overwrite (`pa_philadelphia_fire_2017`)

**This wave surfaced a genuinely new failure mode, distinct from boundary leakage or mechanism-label contamination.** `pa_philadelphia_fire_2017` — despite the live call reporting `SUCCESS` — returned **zero present rows across all 19 attributes** in the pilot script's initial output, even though its evidence window plainly contained explicit Act 111 interest-arbitration and PICA budget/ability-to-pay language (independently self-audited as genuine before the call).

**Root cause, confirmed by direct inspection of the raw saved model response** (`tmp/gabriel_codify_pilots/2026-07-14_163232/gabriel_save_dir/pa_philadelphia_fire_2017/coding_results.csv`): the model's raw response text contained the **full 19-key JSON object written out twice, concatenated within one pair of braces** — the first copy had genuine, correct content (`interest_arbitration_or_formal_impasse_backstop` present ×2, `civil_service_or_statutory_employment_channel` present ×1, `budget_capacity_or_fiscal_constraint` present ×3, `other` present ×1); the second copy was entirely empty (`[]` for every key). Because JSON permits duplicate object keys and Python's `json.loads` resolves duplicates by keeping the **last** occurrence, the empty second copy silently overwrote every genuine finding from the first copy when `gabriel.codify()`'s own internal parsing ran `json.loads()` on this response. **Confirmed isolated to this one call**: all other 11 calls this session (5 Worcester/Arlington + 6 remaining Philadelphia/Trenton) were checked directly for the same duplicate-key pattern and found clean.

**Resolution:** re-parsed the raw saved response using a `first-value-wins` JSON object-pairs hook (rather than Python's default last-wins) to recover the model's genuine first-pass answer. Every recovered span was then independently re-verified as a genuine, unmodified, verbatim substring of the source PDF text (same self-audit discipline as window construction) before being written into `docs/analysis/gabriel_codify_philadelphia_trenton_outputs_2026-07-14.csv`, replacing the 19 spurious `not_found` rows with 15 genuine `not_found` rows + 7 recovered `present` rows. `source_grounding_status` for these 7 rows is honestly recorded as `grounded` (they are genuinely grounded). **They are additionally flagged via this project's standard `METHODOLOGY FLAG` convention** (the same mechanism used for boundary-leakage and mechanism-label-contamination cases) because their provenance is irregular — a manual reconstruction, not the pipeline's normal path — and are therefore correctly excluded from the viewer's default "verified present" count (368) even though the underlying text is independently confirmed genuine. This is a deliberate, conservative choice: an unusual-provenance row gets the same "flagged for reviewer attention, data preserved, not silently promoted" treatment as every other irregular case in this project, rather than being specially exempted.

**Not done:** no change was made to `scripts/gabriel_codify_pilot.py` or the `gabriel` package itself. A first-value-wins (or duplicate-key-detecting, fail-loud) parsing safeguard for this failure mode would be a reasonable future addition to the pilot script's `reshape_and_validate_outputs()` function, parallel to the existing boundary-leakage and mechanism-label-leakage checks — flagged as a recommended follow-up, not built this session (out of scope for a single-row, single-session anomaly; worth building generically only once a second example confirms it recurs).

## Whether this run is safe to append to the evidence layer/viewer

**Yes**, with both the 4 boundary-leak rows and the 7 duplicate-key-recovery rows carried forward transparently, consistent with this project's established practice. Ran:
```
python scripts/build_codify_evidence_viewer.py \
  --input docs/analysis/gabriel_codify_full_codebook_outputs_2026-07-09.csv \
  --input docs/analysis/gabriel_codify_texas_ohio_scaleup_outputs_2026-07-09.csv \
  --input docs/analysis/gabriel_codify_massachusetts_outputs_2026-07-09.csv \
  --input docs/analysis/gabriel_codify_expanded_texas_ohio_outputs_2026-07-10.csv \
  --input docs/analysis/gabriel_codify_seekonk_wayland_outputs_2026-07-10.csv \
  --input docs/analysis/gabriel_codify_worcester_arlington_outputs_2026-07-14.csv \
  --input docs/analysis/gabriel_codify_philadelphia_trenton_outputs_2026-07-14.csv \
  --evidence-out docs/analysis/gabriel_codify_evidence_layer.csv \
  --html-latest-out docs/analysis/gabriel_codify_excerpt_browser_latest.html \
  --archive-html docs/analysis/gabriel_codify_excerpt_browser_2026-07-14_philadelphia_trenton.html
```
Result: 1039 total input rows across all 7 waves, **0 duplicate rows skipped** (idempotent append confirmed). 388 present (up from 342 before this run's initial append, 342+39=381, +7 recovered = 388), 368 verified present (unchanged from the correctly-flagged-out recovery rows' perspective — the 7 recovered rows plus the 4 new boundary-leak rows are excluded from this count by design), 35 rows flagged in notes (13 pre-existing + 4 new boundary-leak + 22 recovery-related, all transparently explained).

## Attribute-level findings

Per-contract present-attribute sets (verified/grounded rows only unless noted):

- **`pa_philadelphia_police_2025`** (7): `budget_capacity_or_fiscal_constraint` (×2 — PICA ability-to-pay standard, balanced-budget statutory requirement), `interest_arbitration_or_formal_impasse_backstop` (the Act 111 framing itself), `management_rights_or_service_flexibility` + `subcontracting_outsourcing_or_volunteer_substitution` (both from the same Civilianization provision, which ties a 1.5%+1.5% wage-schedule increase directly to "operational flexibility"), `peer_comparator_wage_comparability` (a peer-cities *tax-projection-accuracy* comparison — flag this carefully, see caveat below), `staffing_shortage_recruitment_retention` (a retention-incentive directive).
- **`pa_philadelphia_fire_2017`** (4, all flagged/manually-recovered — see above): `interest_arbitration_or_formal_impasse_backstop` (×2), `civil_service_or_statutory_employment_channel` (Heart and Lung Act / Civil Service Regulation 32 medical-provider list), `budget_capacity_or_fiscal_constraint` (×3, same PICA/balanced-budget pattern as police), `other` (Heart and Lung Appeal definition).
- **`pa_philadelphia_other_2025`** (7, DC47 term sheet): `civil_service_or_statutory_employment_channel`, `classification_reclassification_or_grade_structure` (wage-step increases), `grievance_or_contract_interpretation_arbitration` (×5 — a detailed OOC/temporary-promotion dispute-to-mediation-to-arbitration pathway, plus a separate Contract-Grievance-to-PA-Bureau-of-Mediation pathway). **No `interest_arbitration_or_formal_impasse_backstop` finding.**
- **`pa_philadelphia_other_2017`** (1 clean + 2 flagged, DC47 2186 MOA): `overtime_callback_holdover_mandatory_extra_work` (an overtime-rounding rule change) clean; `civil_service_or_statutory_employment_channel` and `other` both boundary-leak-flagged (unclear).
- **`nj_trenton_police_2019`** (7): `interest_arbitration_or_formal_impasse_backstop` (present — but see the important caveat below), `civil_service_or_statutory_employment_channel` (×2), `grievance_or_contract_interpretation_arbitration`, `hazard_risk_stress_or_line_of_duty_rationale` + `benefits_total_compensation_or_pension` (both from the same line-of-duty-death funeral-expense clause), `management_rights_or_service_flexibility`, `no_strike_or_work_stoppage_constraint` (a statute-referencing, not clause-stated, no-strike article).
- **`nj_trenton_fire_2021`** (5 clean + 1 flagged): `hazard_risk_stress_or_line_of_duty_rationale` + `minimum_staffing_or_continuous_coverage` + `overtime_callback_holdover_mandatory_extra_work` (all three from the same explicit health-and-safety-justified minimum-staffing-to-overtime-program clause), `overtime_callback_holdover_mandatory_extra_work` (×2 more — callback pay, court-appearance premium), `interest_arbitration_or_formal_impasse_backstop` (present — same important caveat as Trenton police, see below), `benefits_total_compensation_or_pension` (line-of-duty-death funeral expense); `grievance_or_contract_interpretation_arbitration` boundary-leak-flagged.
- **`nj_trenton_other_2019`** (4 clean + 1 flagged): `no_strike_or_work_stoppage_constraint` (a direct, clause-stated no-strike provision, unlike the safety rows' statute-referencing version), `overtime_callback_holdover_mandatory_extra_work` (standby pay), `union_security_or_institutional_power` (dues checkoff) clean, plus one more `union_security_or_institutional_power` (agency/representation fee) boundary-leak-flagged; `grievance_or_contract_interpretation_arbitration` clean.

### Important caveat: Trenton's `interest_arbitration_or_formal_impasse_backstop` findings are an EXCLUSION, not a grant

Both Trenton police and Trenton fire's `interest_arbitration_or_formal_impasse_backstop=present` excerpts are, on inspection, the SAME clause type already flagged in a prior session as a false-positive-adjacent "inversion" pattern (`wage_mechanism_evidence_checklist.md` item 13, for the fire row specifically): the clause explicitly states that "fiscal matters as wages, hours, and benefits are **not** subject to interest arbitration" under the CBA's own internal Article XVI/XVII (police) or Section 14.06 (fire). GABRIEL correctly identified this as text *about* interest arbitration (the attribute's coding instructions do not require the mechanism to be affirmatively granted, only discussed as a wage-setting-relevant institution) — but a reader must not interpret "present" here as "Trenton CBAs give police/fire an internal interest-arbitration channel for wages." The correct institutional reading, consistent with the prior session's finding, is the opposite: **Trenton routes police/fire wage disputes to NJ's EXTERNAL Police and Fire Public Interest Arbitration Reform Act, deliberately excluding them from the internal CBA arbitration article.** This is itself a substantively interesting, genuine finding — just not the naive "safety has an internal interest-arbitration clause" reading. See the updated Trenton ledger section and National Claim 4 discussion for how this is handled.

## Recommended next step

Philadelphia and Trenton are now both codified. See `docs/analysis/state_city_claims_ledger.md`'s National Claim 4 for how this wave's results bear on the Ohio-vs-Arlington impasse-symmetry question. No further codify wave is recommended immediately; a claim-register/hypothesis-tracker/ledger update pass (done as part of this same session) and, longer-term, a reviewer audit of all `interest_arbitration_or_formal_impasse_backstop` positives corpus-wide (already an open item per `CLM-2026-07-12-06`) are the natural next steps — this session's Trenton finding is itself a strong argument for prioritizing that audit.
