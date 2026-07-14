# Houston Fire Source-Resolution Summary — 2026-07-08

Narrow, single-target follow-up to the Texas/Ohio held-out-target run (commit `6ce5080`), focused exclusively on resolving Houston Fire.

## Sources searched

- The official houstontx.gov press-release page and HR/legal document folders (re-checked; no full-CBA text found, only a City Council presentation slide deck, consistent with the prior session's finding).
- The Houston Professional Fire Fighters Association's own official site (`local341.org`) — no CBA/documents section found; member content is behind a login-gated portal not accessible to this run.
- The non-official news mirror (`interactive.khou.com`) — reviewed but not re-used, per repo convention requiring an official replacement.
- **New this session:** the Houston Fire Department Chief Officers Association's official site (`hfdcoa.org`), found via web search, which hosts a page (`/cba-2024-2029/`) with five HPFFA/City of Houston documents: a Memorandum of Understanding (2024-06-11), an Interim Amendment No. 1, a Fire Department wage-schedule exhibit, a Settlement Agreement and Release (2026), and an Arbitration Opinion and Award (2026-02-27).

## Whether an exact source was found

**Yes, partially.** No official full base-CBA text (all ~30 articles) was located. However, a genuine, verifiable, high-quality **arbitration award** was found and confirmed: HPFFA Local 341 v. City of Houston, AAA Case No. 01-25-0005-2917, Arbitrator William E. Hartsfield, decided 2026-02-27, ruling on a "Three Percent Pay Escalator" grievance under the 2024-2029 CBA's Article 17 Section 2. This award quotes substantial CBA text verbatim (Articles 2, 6, 14, 17, 25) and incorporates a companion Settlement Agreement (Attachment 1) resolving related FY26 monetary grievances (uniform allowance, holiday buy-back, sick-reserve cash-out). A clarifying MOU (2024) was also fetched as a third companion document. Identity was independently corroborated by ABC13 Houston news reporting of the same ruling.

## Source resolved/fetched/failed/deferred

- **Resolved and fetched (3 documents, 1 contracts.csv row):** Arbitration Opinion and Award (primary), Settlement Agreement and Release (companion, incorporated by reference), MOU (companion, clarifies the escalator clause at issue).
- **Resolved but deferred (2 documents, not fetched into corpus/):** Interim Amendment No. 1 (unrelated procedural item), Fire Department wage-schedule Exhibit A (genuine but not incorporated by reference into the ingested chain).
- **Still unresolved:** the original full base-CBA text from an official City of Houston source.
- **Rejected:** the non-official khou.com news mirror.

## Files stored

- `corpus/tx_houston/tx_houston_hpffa_fire_arbitration_award_2026.pdf` (146,618 bytes, clean text layer)
- `corpus/tx_houston/tx_houston_hpffa_fire_settlement_agreement_2026.pdf` (325,094 bytes, OCR)
- `corpus/tx_houston/tx_houston_hpffa_fire_mou_2024.pdf` (138,397 bytes, OCR)

## Rows added

- `data/contracts.csv`: one new row, `tx_houston_fire_2024` (occupation_class=fire, safety_flag=1, source_type=arbitration_award, cycle 2024-07-01 to 2029-06-30). `interest_arbitration_flag=0` — this is grievance/contract-interpretation arbitration under CBA Article 14, explicitly **not** the Sec.174.1535 compulsory interest-arbitration mechanism; the distinction is documented in `binding_arbitration_statute` and the identity audit.
- `data/city_coverage.csv`: one matching row for `tx_houston_fire_2024`, per repo convention.

## Houston matching status after this run

**Houston now has all three institutional tiers represented and matched:** police (`tx_houston_police_2024`) and fire (`tx_houston_fire_2024`) both show a healthy overlap-cycle match against the non-safety HOPE/AFSCME Local 123 row (`tx_houston_other_2024`, 2024-2027), per `ingest/audit_coverage.py`. This is the first Texas/Ohio city with all three tiers matched.

## Mechanism-excerpt highlights

- **Arbitration/impasse backstop:** CBA Article 14 quoted verbatim — grievance arbitration is "final and binding" but the arbitrator has no authority "to establish provisions of a new agreement."
- **Wage schedule:** Article 17 Section 2's full 5-year fiscal-year base-salary schedule (10% FY25; 3%+escalator FY26-27; 4%+escalator FY28-29), with escalators contingent on new public-safety revenue.
- **Training/certification:** EMT Suppression/Administration Assignment Pay tied to a "current valid State of Texas EMT certification" (MOU Section 4).
- **Total compensation:** Settlement Agreement allocates $1.5M/year for Holiday Buy Back and up to $800/year uniform-allowance credits; MOU caps aggregate Special/Incentive Pay at $10M/year.
- **Safety/public-safety framing:** the escalator is explicitly tied to "additional new revenues to the City for public safety."
- Not found: peer-comparator wage comparability, staffing/recruitment/retention, subcontracting/outsourcing.

Full table: `docs/analysis/houston_fire_mechanism_excerpt_extraction_2026-07-08.csv`.

## Validation/audit results

```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 43 | discourse: 0 | coverage: 43 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 43 | discourse: 0 | coverage: 43 | city_attributes: 3 | cities: 13
healthy matched pairs: 16
  exact-cycle: 9
  overlap-cycle: 7
exploratory adjacent matches: 2
safety units unmatched: 5
```

**No GABRIEL calls. No Harvard Proxy calls. No model/API calls from project scripts. No PRRs/FOIA. No statutes, budgets, pay plans, city pages, news stories, or legal pages were ingested as causal rows. The source was correctly classified as `arbitration_award` (a real award, not a legal/arbitration context page) and NOT as a Sec.174.1535 compulsory interest-arbitration instrument. `docs/schema.md` was not modified.**

## Recommended next step

**Source found and ingested for Houston Fire.** Recommend moving to a tiny GABRIEL/codify pilot as the next step, now that Houston has all three matched tiers. The full base-CBA text (all ~30 articles) remains a lower-priority open item for a future session — the current row already provides genuine, verbatim, wage-mechanism-rich text (compensation schedule, grievance-arbitration clause, training/certification pay, total compensation) sufficient to support an initial pilot without blocking on it.
