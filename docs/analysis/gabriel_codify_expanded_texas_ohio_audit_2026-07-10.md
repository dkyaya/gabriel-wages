# GABRIEL Codify — Expanded Texas/Ohio — Live Run Audit — 2026-07-10

## Run identity

- Dry-run: `tmp/gabriel_codify_pilots/2026-07-10_204044/`
- Live run: `tmp/gabriel_codify_pilots/2026-07-10_204149/`
- `run_id`: `2026-07-10_204149_live`
- Model: `gpt-5.4-nano` via the Harvard Proxy adapter (`--use-harvard-proxy`).
- Commands: exact commands recorded in `gabriel_codify_expanded_texas_ohio_prompt_preview_2026-07-10.md` (dry run) and this document (live run, below).

```text
python scripts/gabriel_codify_pilot.py --live --use-harvard-proxy --max-calls 9 \
  --windows docs/analysis/gabriel_codify_expanded_texas_ohio_evidence_windows_2026-07-10.csv
```

## Selected rows / windows

All 9 rows from `docs/analysis/gabriel_codify_expanded_texas_ohio_evidence_windows_2026-07-10.csv` — see the prompt-preview doc's table for per-row window sizes.

## Skipped rows

None. San Antonio police's OCR recovery (Task C) succeeded, so no row needed to be dropped from the originally-planned 9.

## Calls attempted/succeeded/failed

**9 attempted, 9 succeeded, 0 failed.** Per `tmp/gabriel_codify_pilots/2026-07-10_204149/live_run_log.txt`:

```
[1] tx_san_antonio_police_2022: SUCCESS
[2] tx_san_antonio_fire_2024: SUCCESS
[3] oh_cincinnati_police_2024: SUCCESS
[4] oh_cincinnati_police_sup_2024: SUCCESS
[5] oh_cincinnati_fire_2023: SUCCESS
[6] oh_cincinnati_other_2025: SUCCESS
[7] oh_toledo_police_2024: SUCCESS
[8] oh_toledo_fire_2024: SUCCESS
[9] oh_toledo_other_2024: SUCCESS

Calls attempted: 9 | succeeded: 9 | failed: 0
```

Actual API cost: $0.00 (per-call pricing rounds to zero on `gpt-5.4-nano` at this scale, consistent with every prior codify batch in this project).

## Rows completed / skipped

9/9 rows completed with a full 19-attribute pass each. 0 skipped.

## Output parse status

**178/178 rows `parse_status=parsed`.** 0 `partially_parsed`, 0 `failed`. Reshape from `gabriel.codify()`'s native wide format (one row per contract, one list-valued column per attribute) into this project's long/tidy schema (`reshape_and_validate_outputs()`) completed without error for every row. 178 rows (not the flat 9×19=171) because 7 attribute/contract combinations returned more than one distinct excerpt — each becomes its own row, as designed.

## Source-grounding status

- **32 `present` rows, all 32 `grounded` (100%).** 0 `unsupported`, 0 `unclear`.
- 146 `not_found` rows, all correctly `source_grounding_status=not_applicable` (grounding is only meaningful for a returned excerpt).
- 0 `notes` flags of any kind (no `METHODOLOGY FLAG` markers).

## Excerpt-boundary leakage: did it recur?

**No.** `live_run_log.txt` reports `boundary_leak_flagged=0` — the pipeline-level fix from the Massachusetts/Seekonk-Wayland runs (`_clean_boundary_leak()` in `scripts/gabriel_codify_pilot.py`) continued to hold with zero detections this run.

## Mechanism-label contamination: did it recur?

**No.** Both layers were clean this run:
1. **Window-construction layer** (`_check_window_contamination`, read-time, checked in the dry run): 0 violations across all 9 windows — every window used only genuine document article/section names as separators, never codebook vocabulary.
2. **Returned-excerpt layer** (`_has_mechanism_label_leakage`, checked on every live-returned excerpt): `mechanism_label_leak_flagged=0` — no returned excerpt echoed this project's own attribute names back as if they were source text.

## Interest/impasse arbitration vs. grievance arbitration: correctly distinguished?

**Yes — this run's strongest positive result.** `tx_san_antonio_police_2022` produced both:
- `interest_arbitration_or_formal_impasse_backstop=present`, excerpt beginning "Section 4. Impasse Procedure. In the event the City and the Association reach an impasse..." (the Chapter 174 ordinance-defined impasse procedure), **and**
- `grievance_or_contract_interpretation_arbitration=present` (two separate excerpts), from the *separate* Article 15 grievance-arbitration mechanism ("Section 4. Arbitration. If a grievance is submitted to arbitration...").

These are two genuinely distinct institutional mechanisms in the same document, and the model correctly coded them under separate attributes rather than conflating them — the exact test this codebook refinement was designed for (see `gabriel_codify_texas_ohio_scaleup_audit_2026-07-09.md` for the original Houston-fire test case this pattern was built around).

`oh_toledo_police_2024` also correctly coded `interest_arbitration_or_formal_impasse_backstop=present` for its narrow-issue health-benefits reopener clause ("If no agreement is reached, the matter shall be subject to an interest arbitration"), consistent with this contract's known narrow-issue-arbitration character (see `texas_ohio_expansion_mechanism_excerpt_extraction_2026-07-10.csv`'s parallel finding for the sibling Toledo AFSCME 2058 contract).

## Peer/comparator wage comparability: over-coded?

**Not over-coded — if anything, under-coded (one observed false negative, documented honestly rather than corrected by hand).** `peer_comparator_wage_comparability` was `not_found` for all 9 rows, including `tx_san_antonio_police_2022`, whose window (Excerpt 8) contains genuine, on-point comparability language from Attachment 3's factfinding guidelines: *"A comparison of wages, hours and conditions of employment of San Antonio Police Officers and Firefighters with the wages, hours, and conditions of employment of other public and private employees in the local labor market area... and with other employees generally in public and private employment in comparable cities in the State of Texas."* This is a plausible match for the attribute's own definition ("Explicit use of peer cities, comparable communities... to justify wage levels"), and the model missed it. Per this project's discipline (RA discretion must not contaminate GABRIEL's own coding), this excerpt was **not** manually added to the output — it is recorded here as an observed limitation for a future re-run or codebook refinement, not silently corrected. The deterministic (non-model) mechanism-excerpt CSV (`texas_ohio_expansion_mechanism_excerpt_extraction_2026-07-10.csv`) already separately captures this same clause as a source-grounded fact, independent of codify's judgment.

`non_safety_wage_restraint_or_admin_channel` was also `not_found` for both non-safety rows (`oh_cincinnati_other_2025`, `oh_toledo_other_2024`) despite each window containing grievance-mediation-channel language (FMCS/SERB mediation for CODE; standard grievance procedure for AFSCME 2058) — on reflection this looks like an *appropriately conservative* call, not a miss: the attribute is specifically about wage-setting being routed through an administrative/consultation channel rather than bargaining, and an ordinary grievance-mediation procedure (dispute resolution under an existing contract) is a different claim from that. No over-coding observed anywhere in this batch.

## Were excerpts short and usable?

Yes. All 32 present excerpts are short (well under the 40-word cap the prompt requested), verbatim, and legible. No long copied passages.

## San Antonio police OCR impact on codify usability

Directly enabled 8 of the 9 rows' worth of `present` findings for that contract (the highest-yield row in this batch: 8 present findings across `interest_arbitration_or_formal_impasse_backstop`, `grievance_or_contract_interpretation_arbitration` ×2, `management_rights_or_service_flexibility` ×2, `no_strike_or_work_stoppage_constraint`, `civil_service_or_statutory_employment_channel`, and `union_security_or_institutional_power`). Without the bounded OCR recovery in Task C, this row would have had no usable window at all and would have been skipped entirely, per this run's own contingency plan.

## Safe to append to evidence layer/viewer?

**Yes.** 100% source-grounding pass rate, zero contamination, zero boundary leakage, zero parse failures, zero notes flags. This is the cleanest single-batch result of any Texas/Ohio codify run in this project to date (compare: the original Texas/Ohio scale-up run had 1 flagged header-leakage row of 95 present; this run has 0 of 32).

## Recommended next step

**Report scaffolding with coded mechanism-evidence graphs.** The evidence layer now covers all 4 Texas cities with contracts (Houston, Austin, San Antonio) and all 4 Ohio matched cities (Columbus, Cleveland, Cincinnati, Toledo), giving the next report-scaffolding session a materially broader Texas/Ohio base than any prior session had. Per this run's explicit scope, no report artifact is produced here — report language should present these findings as GABRIEL-coded evidence *patterns* (what mechanisms were found present/not-found, and how consistently across cities), not as proof of a causal wage effect.
