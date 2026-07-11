# GABRIEL Codify — Expanded Texas/Ohio — Prompt Preview — 2026-07-10

## Dry-run command (exact)

```text
python scripts/gabriel_codify_pilot.py --dry-run --use-harvard-proxy --max-calls 9 \
  --windows docs/analysis/gabriel_codify_expanded_texas_ohio_evidence_windows_2026-07-10.csv
```

Output directory: `tmp/gabriel_codify_pilots/2026-07-10_204044/`. Result: **9 rows selected, 0 rejected, no network call, no credential read, no contamination violations.**

## Selected rows (9 of 9)

| # | contract_id | state/city | occupation_class | window chars | window words |
|---|---|---|---|---|---|
| 1 | `tx_san_antonio_police_2022` | TX/San Antonio | police | 5,101 | 835 |
| 2 | `tx_san_antonio_fire_2024` | TX/San Antonio | fire | 2,089 | 334 |
| 3 | `oh_cincinnati_police_2024` | OH/Cincinnati | police | 1,760 | 290 |
| 4 | `oh_cincinnati_police_sup_2024` | OH/Cincinnati | police | 1,419 | 223 |
| 5 | `oh_cincinnati_fire_2023` | OH/Cincinnati | fire | 1,784 | 287 |
| 6 | `oh_cincinnati_other_2025` | OH/Cincinnati | other | 2,773 | 421 |
| 7 | `oh_toledo_police_2024` | OH/Toledo | police | 1,327 | 203 |
| 8 | `oh_toledo_fire_2024` | OH/Toledo | fire | 1,872 | 311 |
| 9 | `oh_toledo_other_2024` | OH/Toledo | other | 1,830 | 296 |

All 9 windows are well under the `MAX_WORDS_PER_CALL=1500` cap, so each row produces exactly one `gabriel.codify()` call — 9 calls total, matching `--max-calls 9`.

## Skipped rows

None. San Antonio police (`tx_san_antonio_police_2022`) was initially at risk of being skipped (218-page image scan, no text layer) but the bounded OCR recovery in Task C succeeded, so all 9 originally-planned rows proceed.

## Full codebook reference (19 attributes, unchanged from prior Texas/Ohio/Massachusetts/Seekonk-Wayland batches)

`peer_comparator_wage_comparability`, `interest_arbitration_or_formal_impasse_backstop`, `grievance_or_contract_interpretation_arbitration`, `staffing_shortage_recruitment_retention`, `minimum_staffing_or_continuous_coverage`, `overtime_callback_holdover_mandatory_extra_work`, `classification_reclassification_or_grade_structure`, `training_certification_credential_premiums`, `hazard_risk_stress_or_line_of_duty_rationale`, `premium_pay_differentials`, `benefits_total_compensation_or_pension`, `subcontracting_outsourcing_or_volunteer_substitution`, `management_rights_or_service_flexibility`, `no_strike_or_work_stoppage_constraint`, `civil_service_or_statutory_employment_channel`, `union_security_or_institutional_power`, `budget_capacity_or_fiscal_constraint`, `non_safety_wage_restraint_or_admin_channel`, `other`.

Full definitions are in `scripts/gabriel_codify_pilot.py`'s `CATEGORIES` dict (unchanged this run) and reproduced verbatim in `tmp/gabriel_codify_pilots/2026-07-10_204044/prompt_preview.md`.

## Output schema (per-row, wide -> long reshape via `reshape_and_validate_outputs()`)

`run_id, contract_id, state, city, occupation_class, source_role, attribute, evidence_status, excerpt, excerpt_location, confidence, caveat, raw_output_ref, parse_status, source_grounding_status, notes` — same schema as every prior codify batch (pilot, Texas/Ohio scale-up, Massachusetts, Seekonk/Wayland).

## Representative prompt preview (one row)

From `tmp/gabriel_codify_pilots/2026-07-10_204044/prompt_preview.md`:

```
### tx_san_antonio_police_2022 (tx_san_antonio_police_2022_w1)
- state/city/occupation_class: TX/San Antonio/police
- source_file: corpus/tx_san_antonio/tx_san_antonio_sapoa_police_cba_2022_2026.pdf
- chars: 5101
```

The `window_text` sent for this row begins:

```
--- Excerpt 1 [Article 1, Duration] ---
This Agreement shall be effective upon ratification of the membership and approval of the City
Council. All pay increases, leave, or changes in benefits, shall be implemented in accordance with
the respective timelines outlined herein...

--- Excerpt 2 [Article 3, Section 1, Recognition] ---
The City hereby recognizes the Association as the sole and exclusive collective bargaining agent
for the unit consisting of all sworn Police Officers, except the Chief.
```

...continuing through 8 excerpts (Duration, Recognition, No Strike, Management Rights, Grievance Arbitration, Wage Schedule, Impasse Procedure, and Factfinding Comparability Guidelines).

## Confirmation: source-window bodies are neutral and separator-safe

Every window uses the strictly neutral `--- Excerpt N [location] ---` separator convention (no mechanism/codebook vocabulary in the separator or anywhere in the window body — locations are genuine document article/section references such as "Article 3, Section 1, Recognition" or "2129.01, Recognition", never a codebook attribute name). `scripts/gabriel_codify_pilot.py`'s `_check_window_contamination()` read-time guardrail (checks every window for the codebook's 19 attribute keys plus the generic tells `"Mechanism"`/`"Arbitration / impasse"`) ran automatically during the dry run above and found **zero violations** across all 9 windows — confirmed by the dry run completing without the guardrail's fail-safe `sys.exit(1)` error path triggering.

## Code change this run

`scripts/gabriel_codify_pilot.py`: `HARD_MAX_CALLS` raised `8 -> 9` (deliberate code edit, per this script's own established pattern — see the comment directly above the constant) to accommodate this run's approved 9-row batch in a single run.
