# Texas Second Matched-City Summary — 2026-07-08

Completes the pre-GABRIEL matched-city design target: two matched cities per comparison state.

## Austin non-safety search result

**Resolved.** A genuine, complete meet-and-confer agreement between the City of Austin and the **Austin EMS Association (AEMSA)** was located at the official `austintexas.gov/labor-relations` page family (the same hosting pattern already used for Austin's police and fire agreements). The agreement runs October 1, 2023 – September 30, 2027, and contains a real 4-year base wage schedule (FY23-24 baseline; +4.0% FY24-25; +3.0% FY25-26; +3.0% FY26-27), Education Incentive Pay, Shift Differential, On-Call/Call-Back Pay, and a grievance-arbitration clause. This decisively supersedes the prior AFSCME Local 1624 consultation-policy dead end.

A search of Austin's own council records (File #26-1362, a City Clerk compensation item) surfaced boilerplate language distinguishing "non-sworn employees not covered by collective bargaining or meet and confer agreements" from those who are — this red-herring lead was checked and confirmed not to point to a separate civilian agreement; it simply reflects that police, fire, and EMS are the three groups with negotiated agreements at Austin.

## Whether Austin became matched

**Yes.** Austin police (2024-2029) and Austin fire (2023-2025) both now show a healthy overlap-cycle match against the new EMS row (2023-2027) in `ingest/audit_coverage.py`.

## Backup city evaluation

**Not triggered.** Because Austin was successfully resolved, Fort Worth and San Antonio were not evaluated for fetch/ingestion this session (Task C). Both remain documented in `docs/analysis/texas_second_matched_city_source_resolution_2026-07-08.csv` as `deferred`, carrying forward prior planning findings that neither city has a confirmed non-safety institutional channel (Fort Worth: "Pay for Performance Program for non-civil-service employees instead"; San Antonio: "None identified").

## Rows added

- `data/contracts.csv`: one new row, `tx_austin_nursehealth_2023` (Austin EMS Association, `occupation_class=nurse_health`, `safety_flag=0`, `source_type=cba`, cycle 2023-10-01 to 2027-09-30).
- `data/city_coverage.csv`: one matching row for `tx_austin_nursehealth_2023`.

## New Texas matched-city status

**Texas now has two fully matched cities: Houston and Austin.**

- Houston: police + fire, both healthy overlap-cycle matches against HOPE/AFSCME Local 123 (other, 2024-2027).
- Austin: police + fire, both healthy overlap-cycle matches against the Austin EMS Association (nurse_health, 2023-2027).

## Ohio matched-city status (unchanged this run)

- Columbus: police + fire, healthy overlap-cycle matches against AFSCME Local 1632 (other, 2024-2027).
- Cleveland: police + fire, exploratory-adjacent matches against AFSCME Local 100 (other, 2022-2025) — not "healthy" per the audit's own classification (the non-safety cycle ends 2025 while the safety cycles start 2025), but still Ohio's second city per this project's design framing.

## Recognition-clause findings

Not applicable to a bundled/broad non-safety unit — the EMS agreement is a clean single-occupation unit (Article 2's own definition restricts coverage to "Emergency Medical Services Personnel" per Texas Health and Safety Code Chapter 773, explicitly excluding civilians). `occupation_class=nurse_health` is final, not provisional. See `texas_second_matched_city_recognition_clause_extraction_2026-07-08.md`/`.csv`.

## Mechanism-excerpt highlights

- **Arbitration/impasse backstop:** grievance/contract-interpretation arbitration ("final and binding," arbitrator authority "strictly limited to interpreting and applying the explicit provisions of this Agreement") — not interest arbitration. A separate limited "impact bargaining" mediation clause also exists.
- **Overtime/call-back:** On-Call Pay ($5.00/hour), Call-Back Pay (time-and-a-half, minimum 2 hours).
- **Training/certification:** Education Incentive Pay ($220/month Bachelor's, $300/month Master's).
- **Premium pay:** Shift Differential ($100/month for shifts falling 4:00pm-6:00am).
- **Safety/risk framing:** a line-of-duty-injury exception to a tuition-reimbursement obligation.
- Not found: peer-wage comparability, subcontracting/outsourcing.

Full table: `docs/analysis/texas_second_matched_city_mechanism_excerpt_extraction_2026-07-08.csv`.

## Readiness for the tiny GABRIEL/codify pilot

**Ready.** Both comparison states now have two matched cities each (Texas: Houston, Austin; Ohio: Columbus, Cleveland), satisfying this run's stated design target. No remaining structural blocker for a Texas/Ohio pilot. (Cleveland's adjacent-not-overlap match status is a minor caveat worth carrying into report language, not a blocker — it already counted as "matched" under this run's own framing before this session began.)
