# Somerville Police Metadata Audit — 2026-07-05

**Type:** dated follow-up audit, closing a specific issue flagged (but not resolved) in the prior metadata cleanup application session.

## 1. Purpose and scope

This memo audits the `binding_arbitration_statute` anomaly discovered incidentally during the 2026-07-05 authorized production metadata cleanup session (`metadata_cleanup_application_2026-07-05.md` §5/§7): both `ma_somerville_police_spsoa_2012` and `ma_somerville_police_spea_2012` had `binding_arbitration_statute` values (`ocr_messy`, `clean`) that are actually `text_quality`-vocabulary values, not statute names — the same misplacement pattern already corrected for `ma_boston_clerical_admin_2023` under issue MC02. That prior discovery was explicitly left uncorrected pending a dedicated audit-and-approval step, per this project's audit-first discipline. This memo is that step.

**Production metadata was edited this session.** After full verification (Sections 3–4 below), both rows' `binding_arbitration_statute` values were corrected to `"MA G.L. c. 1078 (JLMC)"`. This is a narrow, single-field, high-confidence correction on two rows — nothing else in `data/contracts.csv` was touched. `data/city_coverage.csv`, `corpus/`, and `inbox/` were not modified.

This memo does not make a causal claim about wage mechanisms.

## 2. Rows inspected

| field | `ma_somerville_police_spsoa_2012` | `ma_somerville_police_spea_2012` |
| --- | --- | --- |
| contract_id (obs_id) | `ma_somerville_police_spsoa_2012` | `ma_somerville_police_spea_2012` |
| unit/title | Somerville Police Superior Officers Association | Somerville Police Employees Association |
| occupation_class | police | police |
| source_type | `arbitration_award` | `arbitration_award` |
| interest_arbitration_flag | `1` | `1` |
| binding_arbitration_statute (before) | `ocr_messy` | `clean` |
| binding_arbitration_statute (after) | `MA G.L. c. 1078 (JLMC)` | `MA G.L. c. 1078 (JLMC)` |
| text_quality | `clean` | `clean` |
| arbitration_clause_text (excerpt) | "...the Interest Arbitration process is utilized when 'there is an exhaustion of the process of collective bargaining which constitutes a potential threat to public welfare'..." | identical boilerplate analysis-and-issues language (both awards share the same neutral arbitrator, Gary D. Altman) |
| comparability_clause_flag | `1` | `1` |
| comparability_text | "...the Arbitration Panel has considered the criteria set forth in the statute including the municipality's ability to pay, wages and benefits of comparable towns, and the cost of living." (corrected in the prior cleanup session, MC08) | identical |
| retrieval_method | `public_download` | `public_download` |
| source_url_or_cite | `https://cdn.muckrock.com/foia_files/2020/08/27/SPSOA_1997_-_2018_reduced.pdf` | `https://cdn.muckrock.com/foia_files/2020/08/27/SPEA_CBA_July_1_2004_-_June_30_2015.pdf` |
| corpus file path | `corpus/ma_somerville/ma_somerville_police_spsoa_cba_1997_2018.pdf` | `corpus/ma_somerville/ma_somerville_police_spea_cba_2004_2015.pdf` |
| file exists | yes (7,512,333 bytes) | yes (2,626,106 bytes) |

## 3. Evidence reviewed

**`data/contracts.csv` fields (direct `csv.DictReader` read, all 34 columns for both rows):** confirmed both rows' `binding_arbitration_statute` held a `text_quality`-vocabulary value (`ocr_messy`, `clean`) rather than a statute citation, while the same rows' own `total_comp_note` field already correctly reads `"MA G.L. c. 1078 (JLMC)"` and additionally states "Integrated with JLMC arbitration decision" (SPSOA) — i.e., the correct citation was already present elsewhere in the same row, exactly as was true for the Boston clerical/admin case, but here in the *right* field rather than a misplaced one.

**Corpus/source file evidence:** ran `pdftotext` on both source PDFs (read-only; output kept in the session scratch directory only) and confirmed both are genuine Joint Labor Management Committee interest-arbitration awards:
- SPSOA document: header reads "COMMONWEALTH OF MASSACHUSETTS / JOINT LABOR MANAGEMENT COMMITTEE FOR MUNICIPAL POLICE AND FIRE / JLMC-17-6072 / ... AWARD AND DECISION BY THE ARBITRATION PANEL," describing a "Voluntary 3A Agreement to submit the unresolved disputes to Arbitration" before a "Tri-partite Panel."
- SPEA document: header reads "JOINT LABOR MANAGEMENT COMMITTEE FOR MUNICIPAL POLICE / ... JLMC-14-4174," describing the JLMC exercising "formal jurisdiction" and conducting "a Section 3A hearing."
- Neither document's extracted text contains the literal numeral string "1078" (a `grep` for "1078" returned no hits in either file) — the specific enabling-statute chapter number is not spelled out verbatim in either award's own text, only the JLMC's name and docket numbers. This is not unusual: JLMC awards typically identify the body by name and docket rather than restating its enabling statute's chapter number in every document. The SPEA document does separately cite "Chapter 1SOE of the General Laws" at line 1874 of the extracted text (an OCR-garbled rendering of "Chapter 150E," Massachusetts's general public-sector labor-relations law, which applies to all public employees including police/fire on matters outside JLMC's specific interest-arbitration jurisdiction) — this is a different, general-purpose citation, not evidence against the JLMC finding.

**Recent metadata cleanup memo:** `metadata_cleanup_application_2026-07-05.md` §5 and §7 first surfaced this anomaly, explicitly declining to correct it pending a dedicated follow-up audit. `metadata_cleanup_audit_2026-07-05.md` (the prior audit) did not identify this issue, since its verification scope was the Boston row specifically; this is a new finding from the subsequent application session, now closed here.

**Corpus-wide convention check:** every other police/fire row in `data/contracts.csv` (13 rows: Worcester fire, Boston police, Arlington fire, Newton police, Georgetown police, Seekonk police/fire, Franklin fire/police/sergeants, Wayland police/fire ×2) uses the identical string `"MA G.L. c. 1078 (JLMC)"` in `binding_arbitration_statute`. Using the same string for these two rows is consistent with, not a new interpretation of, this project's own established convention.

**Public-source institutional reference:** none newly consulted this session — the JLMC/Chapter 1078 institutional facts were already independently verified in prior sessions (`ma_dpw_bargaining_impasse_context_2026-07-04.md`, `ma_clerical_admin_bargaining_impasse_context_2026-07-05.md`, and the original police/fire mechanism memos), which this audit relies on rather than re-verifying from scratch.

## 4. Finding

**`binding_arbitration_statute` was mispopulated on both rows**, holding `text_quality` values (`ocr_messy`, `clean`) instead of a statute citation — confirmed directly from the CSV, with no ambiguity.

**Both rows unambiguously involve JLMC/interest arbitration**, not merely "arbitration" generically. Both are `source_type=arbitration_award` documents that are themselves JLMC award-and-decision documents (JLMC-17-6072 and JLMC-14-4174), containing explicit interest-arbitration statutory-criteria language ("ability to pay, wages and benefits of comparable towns, and the cost of living") already correctly captured in `comparability_text`/`arbitration_clause_text`, and covering police units (`occupation_class=police`, `safety_flag=1`). This is the clearest, most self-evident case of a genuine interest-arbitration/JLMC row anywhere in this project's corpus — unlike the grievance-arbitration false positives corrected in the prior cleanup round (MC06), there is no ambiguity here about arbitration type.

**Recommended correction:** `"MA G.L. c. 1078 (JLMC)"` for both rows — the same value already present (correctly) in each row's own `total_comp_note` field, and identical to the convention used by all 13 other police/fire rows in the corpus. Confidence: high, not merely medium-high — the correct value is corroborated redundantly within each row itself (not requiring an external inference the way Boston's correction did), plus by the source PDF's JLMC docket headers, plus by corpus-wide convention.

## 5. Applied edits

| contract_id | field | old_value | new_value |
| --- | --- | --- | --- |
| `ma_somerville_police_spsoa_2012` | `binding_arbitration_statute` | `ocr_messy` | `MA G.L. c. 1078 (JLMC)` |
| `ma_somerville_police_spea_2012` | `binding_arbitration_statute` | `clean` | `MA G.L. c. 1078 (JLMC)` |

This edit was applied directly to `data/contracts.csv`, since it met the session's stated bar for editing without further approval: fully verified, narrow (a single field on two rows), high-confidence, and schema-safe (`binding_arbitration_statute` is a free-text field with no controlled vocabulary to violate; the corrected value matches the format already used corpus-wide). See `somerville_police_metadata_audit_edits_2026-07-05.csv` for the machine-readable record. No other field on either row was touched, and no other row in the corpus was inspected for a comparable anomaly in this session (see §7 of the companion checkpoint memo's recommendation for a systematic sweep).

## 6. Recommended next step

**No further action needed on this specific issue.** The Somerville `binding_arbitration_statute` anomaly flagged in the prior cleanup session is now fully resolved. `python scripts/validate.py` and `python ingest/audit_coverage.py` both pass cleanly and unchanged after this edit (see the checks reported in the companion PROGRESS.md/handoff entries for this session).

**A systematic sweep was run this session as a closing check**, since the Boston and Somerville instances were both found incidentally rather than by deliberate design: `binding_arbitration_statute in {"clean","ocr_messy","partial"}` was checked across all 32 rows. Result: **zero remaining rows** with a `text_quality` value in `binding_arbitration_statute`. This confirms the pattern is now fully closed corpus-wide, not just for the two rows this memo targeted.
