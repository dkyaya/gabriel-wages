# GABRIEL Codify Full-Codebook Pilot Design — 2026-07-09

## 1. Purpose and scope

This is a **small, capped live pilot**, not full extraction. It routes `gabriel.codify()` through a Harvard Proxy `response_fn` adapter (see `gabriel_codify_harvard_proxy_adapter_design_2026-07-09.md`) and codes exactly 4 evidence windows against the project's full refined 19-attribute wage-mechanism codebook. **Maximum 4 live GABRIEL/codify calls**, one per selected row — enforced in code, not just documented. No `data/contracts.csv`, `data/city_coverage.csv`, or `corpus/` edits occur at any point.

## 2. Why we are using all refined attributes now

The prior dry-run pilot (2026-07-08) tested a smaller, 11-code subset of this project's mechanism vocabulary purely to validate the interface (no credentials were available, so it never ran live). This session has both a working Harvard Proxy adapter and a matured, PI-refined 19-attribute codebook that distinguishes several mechanisms the smaller set collapsed together — most importantly, **interest/impasse arbitration vs. grievance/contract-interpretation arbitration**, which the smaller codebook's single `arbitration_impasse_backstop` code could not separate. Running the full codebook now, on the same institutionally-important sample (Houston Fire's arbitration award is exactly the document where this distinction matters most), is the most informative test this pilot can run with its 4-call budget.

## 3. Selected rows/windows and rationale

| contract_id | state | city | occupation_class | source_file | text_quality | window chars/words | reason |
|---|---|---|---|---|---|---|---|
| `tx_houston_fire_2024` | TX | Houston | fire | `corpus/tx_houston/tx_houston_hpffa_fire_arbitration_award_2026.pdf` | clean | 3,363 / 512 | Arbitration/settlement source; institutionally important; tests whether the model correctly separates grievance arbitration (this document) from interest/impasse arbitration (Sec.174.1535, not this document) |
| `tx_houston_other_2024` | TX | Houston | other | `corpus/tx_houston/tx_houston_hope_afscme123_meet_confer_2024.pdf` | clean | 5,906 / 552 | Broad HOPE/AFSCME Local 123 non-safety meet-and-confer comparison in Texas |
| `tx_austin_nursehealth_2023` | TX | Austin | nurse_health | `corpus/tx_austin/tx_austin_aemsa_ems_meet_confer_2023_2027.pdf` | clean | 2,649 / 411 | Safety-adjacent non-police/fire comparison; tests the `nurse_health` classification against `civil_service_or_statutory_employment_channel` (EMS shares a Ch.143 Civil Service Commission with police/fire) |
| `oh_columbus_fire_2023` | OH | Columbus | fire | `corpus/oh_columbus/oh_columbus_iaff67_fire_cba_2023_2026.pdf` | clean | 6,674 / 791 | Cleaner, richer prior extraction than Columbus's non-safety AFSCME row; Ohio Chapter 4117/SERB institutional comparison to Houston's Chapter 174 case |

Each window combines (a) the `evidence_status=present` excerpts already captured verbatim in this project's prior hand extractions (`houston_fire_mechanism_excerpt_extraction_2026-07-08.csv`, `texas_ohio_mechanism_excerpt_extraction_2026-07-08.csv`, `texas_second_matched_city_mechanism_excerpt_extraction_2026-07-08.csv`) and (b) 2-3 new raw passages located this session via local term search over the same already-extracted corpus text (statutory-channel references, management-rights body text, no-strike clause text) — targeting the 8 attributes new to the refined codebook that the prior 11-code extraction did not cover. All text is read from files already present in `corpus/`; nothing was ingested or downloaded.

## 4. Full 19-attribute codebook

See `scripts/gabriel_codify_pilot.py`'s `CATEGORIES` dict for the exact text sent to `codify()` (verbatim identical to the task's specification): `peer_comparator_wage_comparability`, `interest_arbitration_or_formal_impasse_backstop`, `grievance_or_contract_interpretation_arbitration`, `staffing_shortage_recruitment_retention`, `minimum_staffing_or_continuous_coverage`, `overtime_callback_holdover_mandatory_extra_work`, `classification_reclassification_or_grade_structure`, `training_certification_credential_premiums`, `hazard_risk_stress_or_line_of_duty_rationale`, `premium_pay_differentials`, `benefits_total_compensation_or_pension`, `subcontracting_outsourcing_or_volunteer_substitution`, `management_rights_or_service_flexibility`, `no_strike_or_work_stoppage_constraint`, `civil_service_or_statutory_employment_channel`, `union_security_or_institutional_power`, `budget_capacity_or_fiscal_constraint`, `non_safety_wage_restraint_or_admin_channel`, `other`.

## 5. Global coding rules

Sent verbatim as `additional_instructions` to `codify()`: use source text only; no causal inference; no institutional-mechanism inference beyond what the text explicitly references; never conflate interest/impasse arbitration with grievance/contract-interpretation arbitration; never mark `peer_comparator_wage_comparability` present for generic "competitive wages" without an explicit external comparator; default to `not_found`; use `unclear` for suggestive-but-insufficient text; keep excerpts short and verbatim; attribute evidence to the given window only, not assumed missing context. Full text in `scripts/gabriel_codify_pilot.py`'s `ADDITIONAL_INSTRUCTIONS` constant.

## 6. Expected output schema

Per attribute, per row: `evidence_status` (present/not_found/unclear), `excerpt` (verbatim, <40 words, blank if not_found), `excerpt_location` (if identifiable), `confidence` (high/medium/low/not_applicable), `caveat` (one sentence if uncertain/partial, else blank).

## 7. Live-call cap and stop rules

- **Hard cap: 4 live calls**, enforced in `scripts/gabriel_codify_pilot.py` (`HARD_MAX_CALLS = 4`), not just via CLI flag.
- Each selected row gets its own `gabriel.codify()` invocation (not one batched call for all 4), so the run can stop cleanly after the first nontrivial failure without losing prior successes.
- `max_categories_per_call=19` and `max_words_per_call=1500` are set so codify does not internally split any row into multiple category-batch or chunk calls (all 4 windows are under 800 words; 19 categories fit in one batch) — this guarantees exactly 1 live call per row, 4 total, not more.
- `n_rounds=1` skips codify's internal multi-round completion/refinement loop, which would otherwise double the call count.
- If the first live call fails for a nontrivial adapter/API reason, live calls stop immediately; the failure is documented, not retried.
- If parsing fails but the raw output is valid and source-grounded, the run does not retry live calls — the parser is fixed offline instead.

## 8. Source-grounding audit plan

For every returned excerpt where `evidence_status` is `present` or `unclear`: verify it is a verbatim (or near-verbatim, allowing for minor whitespace normalization) substring of that row's `window_text`. Any excerpt that is not found in the window text is flagged `unsupported` (a hallucination signal). Cross-check the model's `interest_arbitration_or_formal_impasse_backstop` vs. `grievance_or_contract_interpretation_arbitration` calls against this project's own established finding (Houston Fire's arbitration is grievance/contract-interpretation, not interest/impasse) to test whether the refined codebook's split actually holds up in practice. Compare overall `present` counts against the deterministic hand-extraction files' known answer counts for the 11 codes that carry over conceptually.

## 9. How outputs would support future filtering by state/city/occupation/source/attribute

The parsed output table (`gabriel_codify_full_codebook_outputs_2026-07-09.csv`) carries `state`, `city`, `occupation_class`, `contract_id`, `source_role`, and `attribute` as first-class columns alongside `evidence_status`/`excerpt`/`confidence`. This is a long/tidy table — one row per (contract, attribute) pair — that supports direct filtering (e.g., "every `civil_service_or_statutory_employment_channel=present` row where `state=OH`") without any additional transformation, which is exactly the durable evidence-layer shape this project's earlier pilot design set out to test.
