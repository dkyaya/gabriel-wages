# Metadata Cleanup Application — 2026-07-05

**Type:** dated application memo. This is the authorized production-edit follow-up to `metadata_cleanup_audit_2026-07-05.md`. Companion machine-readable status table: `metadata_cleanup_applied_edits_2026-07-05.csv`.

## 1. Purpose and scope

This session applied the **user-authorized** subset of the metadata cleanup edits proposed in `metadata_cleanup_proposed_edits_2026-07-05.csv`, following the two explicit schema decisions the user approved for `comparability_clause_flag` and `retrieval_method`. Only metadata fields in `data/contracts.csv` were edited — no corpus documents, no `inbox/` contents, and no new rows were added. `data/city_coverage.csv` required no edit, since none of the applied changes touch `occupation_class`, cycle dates, or `obs_id`. This memo does not make causal claims about why police/fire wages rise faster than other municipal occupations; it is exclusively about the reliability of the metadata itself.

A brief correction to the prior audit: `AGENTS.md` was listed as missing in `metadata_cleanup_audit_2026-07-05.md` §7; it in fact exists in this repository (byte-identical to `CLAUDE.md`). This was confirmed by direct file inspection this session and is noted here since the prior memo is not being rewritten.

## 2. User-approved schema decisions

1. **`comparability_clause_flag` means peer wage / peer-community / peer-employer wage comparability language specifically.** It should not be set to `1` for health-insurance comparability, workers'-compensation comparability, discipline/fact-pattern comparability, internal-classification comparability, or other generic "comparable" language unrelated to wage benchmarking. Where a row's captured "comparable" language is non-wage, that fact is preserved in `comparability_referent` (a free-text, schema-existing field) rather than silently discarded. This definition was also added to `docs/schema.md`'s `comparability_clause_flag` row.
2. **`retrieval_method = public_download` describes how this project obtained the document, not the document's original legal/historical provenance.** A document a third party (e.g., MuckRock) originally obtained via FOIA, but which this project accessed via an open public download, should be coded `public_download`, not `foia`. `foia` is reserved for a direct public-records request made by this project itself. This resolves MC10 from the prior audit with no data-value change (both Somerville rows already read `public_download`).

## 3. Task A — Applicability checklist (which proposed edits were applied vs. skipped)

Reviewed all 21 data rows of `metadata_cleanup_proposed_edits_2026-07-05.csv` against the two schema decisions above. Decision:

| proposed-edits row | issue_id | row_identifier / field | decision | why |
| --- | --- | --- | --- | --- |
| 1 | MC01 | Arlington PW 2015, `comparability_referent` | **apply** | concrete, evidenced, schema-safe |
| 2 | MC01 | Arlington PW 2018, `comparability_referent` | **apply** | concrete, evidenced, schema-safe |
| 3 | MC01 | Arlington PW 2015/2018, `comparability_clause_flag` (was `needs_followup`) | **apply, extended to flag=0** | Decision 1 directly resolves this: the row's captured text is non-wage, so under the new definition the flag must be `0` |
| 4 | MC02 | Boston, `longevity_detail` | **apply** | concrete, evidenced, schema-safe |
| 5 | MC02 | Boston, `total_comp_note` | **apply** | concrete, evidenced, schema-safe (paired with row 4 as one swap) |
| 6 | MC02 | Boston, `binding_arbitration_statute` | **apply, after direct PDF re-verification** | audit flagged this as medium-high confidence pending PDF check; this session re-extracted the source PDF and confirmed "Chapter 150E" / "M.G.L. c. 150E" appears cleanly at 3 independent locations in the document (lines 95, 485, 1047 of the extracted text), confirming "Chapter I SOE" (lines 311, 1513) is a corrupted rendering of the same citation — see §evidence below |
| 7 | MC02 | Boston, `interest_arbitration_flag` | **apply** | concrete, evidenced, schema-safe |
| 8 | MC06 | Arlington PW 2015, `interest_arbitration_flag` | **apply** | concrete, evidenced, schema-safe |
| 9 | MC06 | Arlington PW 2018, `interest_arbitration_flag` | **apply** | concrete, evidenced, schema-safe |
| 10 | MC06 | Seekonk PW, `interest_arbitration_flag` | **apply** | concrete, evidenced, schema-safe; clause text is unambiguous ("grievances only") |
| 11 | MC06 | `docs/schema.md` definition clarification | **apply** | docs-only edit, explicitly permitted, needed to record the approved definition |
| 12 | MC08 | Somerville SPSOA, `comparability_text` | **apply** | concrete, evidenced (exact verbatim span already inside the same row's `arbitration_clause_text`), schema-safe |
| 13 | MC08 | Somerville SPSOA, `comparability_referent` | **apply** | paired with row 12 |
| 14 | MC08 | Somerville SPEA, `comparability_text` | **apply** | same as row 12 |
| 15 | MC08 | Somerville SPEA, `comparability_referent` | **apply** | paired with row 14 |
| 16 | MC08 | Seekonk fire, `comparability_referent` | **apply** | concrete, evidenced, schema-safe |
| 17 | MC08 | Wayland fire, `comparability_referent` | **apply** | concrete, evidenced, schema-safe |
| 18 | MC08 | Wayland other, `comparability_referent` | **apply** | concrete, evidenced, schema-safe |
| 19 | MC08 | Seekonk fire / Wayland fire / Wayland other, `comparability_clause_flag` (not explicitly proposed as a row, but implied by the same `needs_followup` schema question in row 20) | **apply, extended to flag=0** | Decision 1 resolves this exactly as for Arlington: all three rows' captured text is non-wage |
| 20 | MC08 | `docs/schema.md` `comparability_clause_flag` definition (was `needs_followup`) | **apply** | Decision 1 directly resolves this |
| 21 | MC10 | Somerville x2, `retrieval_method` (was `needs_followup`) | **skipped — not needed** | Decision 2 confirms the existing value (`public_download`) is already correct; no data change required |

**Net result:** 16 of 16 originally-`production_edit_needed=yes` rows were applied (Somerville re-extraction is 4 field-edits across 2 rows; Boston is 4 field-edits on 1 row; the remaining 8 are single-field edits on 5 rows), plus 5 additional `comparability_clause_flag` flips (2 Arlington + 3 non-Somerville MC08 rows) that were implied but not spelled out as separate CSV rows, made schema-safe and concrete by the user's Decision 1. Both `needs_followup` items were resolved by the user's explicit decisions rather than left open. **No row was skipped for lack of evidence.**

## 4. Edits applied

| issue_id | row_identifier | field | old_value | new_value | rationale | evidence_source |
| --- | --- | --- | --- | --- | --- | --- |
| MC01 | `ma_arlington_public_works_2015` | `comparability_clause_flag` | `1` | `0` | Captured text is a workers'-comp medical-provider clause, not peer wage comparability; user Decision 1 requires flag=0 for non-wage comparable language | direct `data/contracts.csv` read; `non_safety_dpw_existing_corpus_scan_2026-07-04.md` §3 |
| MC01 | `ma_arlington_public_works_2015` | `comparability_referent` | (blank) | "workers' compensation / line-of-duty medical-provider comparability (non-wage)" | preserves the non-wage finding per Decision 1's instruction to keep it in an existing notes/referent field | direct CSV read |
| MC01 | `ma_arlington_public_works_2018` | `comparability_clause_flag` | `1` | `0` | identical pattern to the 2015 cycle (same bargaining unit, successor contract) | direct CSV read |
| MC01 | `ma_arlington_public_works_2018` | `comparability_referent` | (blank) | "workers' compensation / line-of-duty medical-provider comparability (non-wage)" | same as above | direct CSV read |
| MC06 | `ma_arlington_public_works_2015` | `interest_arbitration_flag` | `1` | `0` | `arbitration_clause_text` describes civil-service suspension/dismissal grievance arbitration, not wage-setting interest arbitration | direct CSV read of `arbitration_clause_text` |
| MC06 | `ma_arlington_public_works_2018` | `interest_arbitration_flag` | `1` | `0` | identical clause text to the 2015 cycle | direct CSV read |
| MC06 | `ma_seekonk_public_works_2023` | `interest_arbitration_flag` | `1` | `0` | clause states verbatim "Final binding arbitration will prevail on grievances only" | direct CSV read of `arbitration_clause_text` |
| MC02 | `ma_boston_clerical_admin_2023` | `longevity_detail` | "Full base CBA. City-wide administrative/clerical unit; merged units include SENA 9158E (Public Facilities/DND) and 9158F (BCYF). Has no-strike and binding arbitration clauses." | (blank) | this was a general unit-description note misplaced in a longevity field; `longevity_pay_flag` is also blank for this row, so there is no longevity-specific text to retain here | direct field-by-field `csv.DictReader` read against `docs/schema.md` column definitions |
| MC02 | `ma_boston_clerical_admin_2023` | `total_comp_note` | "MA G.L. c. 1078 (JLMC)" | "Full base CBA. City-wide administrative/clerical unit; merged units include SENA 9158E (Public Facilities/DND) and 9158F (BCYF). Has no-strike and binding arbitration clauses." | swaps in the correctly-homed general note (schema: `total_comp_note` is "free text for non-base items not forced into columns"); removes a bare JLMC citation that could be misread as JLMC coverage for a JLMC-ineligible occupation class | direct CSV read; `ma_clerical_admin_bargaining_impasse_context_2026-07-05.md` §3 |
| MC02 | `ma_boston_clerical_admin_2023` | `binding_arbitration_statute` | "clean" | "MA G.L. c. 150E" | "clean" is a `text_quality` value, not a statute name. Direct re-extraction of `corpus/ma_boston/ma_boston_clerical_sena9158_cba_2023_2027.pdf` this session found "Chapter 150E" cleanly at line 95 ("...collective bargaining conducted pursuant to Chapter 150E of the Massachusetts General Laws...") and "M.G.L. c. 150E" at lines 485 and 1047, confirming the garbled "Chapter I SOE" at lines 311/1513 of the same extracted text is a corrupted rendering of the same citation, and matching the format used by every other `clerical_admin`/`public_works` row in the corpus | direct `pdftotext` re-extraction of the source PDF this session, cross-checked at 3 independent locations in the document |
| MC02 | `ma_boston_clerical_admin_2023` | `interest_arbitration_flag` | `1` | `0` | `arbitration_clause_text` is pure grievance-procedure definitional language (Grievance Form, Grievant, Grievance, day-counting) with no interest-arbitration content; clerical/admin is externally confirmed JLMC-ineligible | direct CSV read of full `arbitration_clause_text`; `ma_clerical_admin_bargaining_impasse_context_2026-07-05.md` |
| MC08 | `ma_somerville_police_spsoa_2012` | `comparability_text` | "B. The reasonable suspicion standard for drug testing is based upon a specific objective fact(s)... comparable fact patterns:" | "In\nreaching the conclusions in the present award, the\nArbitration Panel has considered the criteria set forth in\nthe statute including the municipality's ability to pay,\nwages and benefits of comparable towns, and the cost of\nliving." | re-extracted verbatim (exact substring, including original line breaks) from this row's own `arbitration_clause_text` field, replacing an unrelated drug-testing "comparable fact patterns" clause with the genuine peer-wage-comparability span | direct CSV read; exact verbatim span located programmatically inside the row's own `arbitration_clause_text` |
| MC08 | `ma_somerville_police_spsoa_2012` | `comparability_referent` | (blank) | "comparable towns (statutory interest-arbitration criterion: wages and benefits of comparable towns)" | names the referent the clause pegs the unit to, per `docs/schema.md`'s instruction to quote, not interpret | direct CSV read of `arbitration_clause_text` |
| MC08 | `ma_somerville_police_spea_2012` | `comparability_text` | "B. The reasonable suspicion standard for drug testing is based upon a specific objective fact(s)... comparable fact patterns" | identical verbatim span as the SPSOA row (both awards share the same boilerplate analysis-and-issues language) | same treatment as SPSOA | direct CSV read |
| MC08 | `ma_somerville_police_spea_2012` | `comparability_referent` | (blank) | "comparable towns (statutory interest-arbitration criterion: wages and benefits of comparable towns)" | same referent as SPSOA | direct CSV read |
| MC08 | `ma_seekonk_fire_2022` | `comparability_clause_flag` | `1` | `0` | captured text is work-group-realignment eligibility criteria, not wage comparability; user Decision 1 requires flag=0 | direct CSV read |
| MC08 | `ma_seekonk_fire_2022` | `comparability_referent` | (blank) | "work-group realignment eligibility ('years of employment... somewhat comparable') -- scheduling/seniority context, not wage comparability" | preserves the non-wage finding | direct CSV read |
| MC08 | `ma_wayland_fire_2020` | `comparability_clause_flag` | `1` | `0` | captured text is a health-insurance contribution-parity clause, not wage comparability | direct CSV read |
| MC08 | `ma_wayland_fire_2020` | `comparability_referent` | (blank) | "health insurance plan contribution parity ('comparable plan(s)') -- benefits comparability, not wage comparability" | preserves the non-wage finding | direct CSV read |
| MC08 | `ma_wayland_other_2021` | `comparability_clause_flag` | `1` | `0` | identical health-insurance contribution-parity clause to the Wayland fire row | direct CSV read |
| MC08 | `ma_wayland_other_2021` | `comparability_referent` | (blank) | "health insurance plan contribution parity ('comparable plan(s)') -- benefits comparability, not wage comparability" | preserves the non-wage finding | direct CSV read |
| MC06 | `docs/schema.md` | `interest_arbitration_flag` definition (notes column) | "" (no qualifier) | "specifically wage-setting / impasse interest arbitration (e.g., JLMC-style compulsory arbitration). Grievance, discipline, and ordinary contract-interpretation arbitration should be captured verbatim in `arbitration_clause_text` without setting this flag." | records the clarified field definition so future ingestion does not repeat the same miscoding | cross-row comparison of all `interest_arbitration_flag=1` rows this session and the prior audit |
| MC08 | `docs/schema.md` | `comparability_clause_flag` definition (notes column) | "" (no qualifier) | "peer wage / peer-community / peer-employer wage comparability language specifically. Do not set for health-insurance, workers'-compensation, internal-classification, discipline/fact-pattern, or other non-wage uses of 'comparable.'" | records the user-approved Decision 1 definition | user-approved schema decision, this session |

**Total: 9 rows of `data/contracts.csv` edited across 22 field-level changes, plus 2 `docs/schema.md` definition clarifications.**

## 5. Edits skipped or deferred

| issue_id | row_identifier | field | reason_deferred | needed_followup |
| --- | --- | --- | --- | --- |
| MC10 | `ma_somerville_police_spsoa_2012`; `ma_somerville_police_spea_2012` | `retrieval_method` | Resolved, not deferred: user Decision 2 confirms the current value (`public_download`) is already correct for a document this project accessed via open public download, regardless of its original FOIA provenance. No value change needed. | none — fully resolved |
| MC03 | `ma_seekonk_clerical_admin_2021` | (none — no field proposed) | Prior audit found this already adequately documented (`total_comp_note` already states the school-committee affiliation); no edit was proposed and none was made | none |
| MC04 | `ma_worcester_public_works_2017`; `ma_arlington_public_works_2015/2018/2021` | (none — no field proposed) | Prior audit found the bundling composition already documented in `total_comp_note` for the rows that matter; no edit was proposed and none was made | none |
| MC05 | (no current row) | (none) | No teacher-aide/paraprofessional row currently exists in `data/contracts.csv`; monitoring-only issue, nothing to edit | monitor future ingestion only |
| MC07 | `ma_worcester_fire_2017`; `ma_worcester_clerical_admin_2017`; `ma_worcester_public_works_2017` | (none — no field proposed) | Prior audit found the successor-MOA/incorporation-by-reference limitation already documented in `total_comp_note` for clerical/DPW; fire's wording was flagged only as a low-priority cosmetic option, not proposed as a concrete edit, and was not applied | optional, low-priority wording alignment only |

**New, out-of-scope finding — not corrected this session:** while verifying the applied edits, this session discovered that `ma_somerville_police_spsoa_2012`'s `binding_arbitration_statute` field holds `"ocr_messy"` and `ma_somerville_police_spea_2012`'s holds `"clean"` — both `text_quality`-vocabulary values, not statute names, matching the exact same misplacement pattern found and corrected in Boston's row (MC02). **This was not part of the audited/approved proposed-edits table and was therefore left untouched**, per this session's explicit boundary against unapproved edits and "broad new metadata redesign." It is flagged here and in §6 for a future audit-and-approval cycle. Both rows' `binding_arbitration_statute` should very likely read `"MA G.L. c. 1078 (JLMC)"` (the value used by every other police/fire row, and consistent with these two rows' own award text and `total_comp_note` field, which already correctly cites JLMC), but this proposed value has not gone through the audit-evidence-and-approval process this project's cleanup discipline requires, so it is not written here.

## 6. Validation implications

- `python scripts/validate.py` **passed** after the edits: `VALIDATION PASSED — all rows conform to docs/schema.md` (`contracts: 32 | discourse: 0 | coverage: 32 | city_attributes: 3`), identical counts to before the edit.
- No controlled-vocabulary field was touched in a way that could violate `validate.py`'s enums: `interest_arbitration_flag` and `comparability_clause_flag` remain valid `0`/`1` values; `binding_arbitration_statute` is a free-text field with no enum check, so writing `"MA G.L. c. 150E"` (a value already used elsewhere in the corpus) introduces no new uncontrolled vocabulary.
- No required field was left blank by these edits: `longevity_detail` and `comparability_text`/`comparability_referent` are all optional per `docs/schema.md`, so clearing `ma_boston_clerical_admin_2023`'s `longevity_detail` does not create a validation failure.
- `python ingest/audit_coverage.py` output is **byte-for-byte unchanged** from before the edits (12 healthy matched pairs, 3 unmatched safety units, same obs_ids) — expected, since none of the applied edits touch `occupation_class`, `cycle_start`/`cycle_end`, or `obs_id`. `data/city_coverage.csv` therefore required no update and was not edited.
- Column order, column count (34), row count (32), and the file's CRLF-between-records / bare-LF-within-quoted-fields convention were all preserved (verified programmatically before and after).

## 7. Remaining metadata risks

- **New finding, not yet approved for correction:** the Somerville `binding_arbitration_statute` misplacement described in §5 above. Recommend a short, targeted follow-up audit (mirroring MC02's method) before any production edit, since this project's discipline requires audit-then-approve, not opportunistic fixes discovered mid-application.
- **MC07's optional cosmetic wording alignment** for Worcester fire's `total_comp_note` (to explicitly say "incorporates prior base CBA by reference," matching its two sibling 2017 rows) remains open but low-priority and was not proposed as a concrete edit.
- **No other issues from the original 10-issue audit remain open for `data/contracts.csv`** beyond the two items above; MC03, MC04, MC05, and MC09 were confirmed to need no action in the audit and are not revisited here.
- Further cleanup is recommended only for the new Somerville finding, on the same audit-first basis as everything else in this two-session cleanup arc — not as an immediate follow-on edit.

## 8. Recommended next step

1. Review the cleaned `data/contracts.csv` diff (`git diff` or the relay bundle's `git_diff_data_contracts.patch`) to confirm the applied edits read correctly.
2. Decide whether to authorize a small follow-up audit-and-approval cycle for the newly-discovered Somerville `binding_arbitration_statute` anomaly (§5/§7) before touching it.
3. Only after the above, resume research planning, future source acquisition, or GABRIEL/attribute design — and only with explicit user approval for any GABRIEL run, model/API call, or new ingestion, none of which are authorized by this cleanup session.
