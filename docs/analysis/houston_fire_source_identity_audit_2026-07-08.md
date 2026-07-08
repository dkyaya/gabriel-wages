# Houston Fire Source Identity Audit — 2026-07-08

Reviews the three newly fetched Houston Fire documents. No GABRIEL, Harvard Proxy, model/API, PRR, FOIA, or context-only ingestion calls were made.

## tx_houston_fire_2024 (primary source: Arbitration Opinion and Award)

- Stored path (primary): `corpus/tx_houston/tx_houston_hpffa_fire_arbitration_award_2026.pdf`
- Companion paths: `corpus/tx_houston/tx_houston_hpffa_fire_settlement_agreement_2026.pdf`, `corpus/tx_houston/tx_houston_hpffa_fire_mou_2024.pdf`
- **Identity verdict: confirmed**
- City: Houston, TX
- Union/unit: Houston Professional Fire Fighters Association, Local 341, International Association of Fire Fighters (HPFFA/IAFF Local 341) — rank-and-file firefighters
- Employer/jurisdiction: City of Houston (represented by City Attorney's Office, Labor, Employment & Civil Service Section; Fire Chief Tom Muñoz appeared as a witness)
- Document type: **arbitration award** (grievance/contract-interpretation arbitration under CBA Article 14 — not a Sec.174.1535 compulsory interest arbitration; the award interprets and enforces an already-executed CBA's escalator clause, it does not set the CBA's original terms)
- Agreement/cycle years visible: the underlying "2024-2029 Collective Bargaining Agreement" is referenced repeatedly and consistently across all three documents; the Settlement Agreement states it was "ratified by City of Houston City Council on or about June 18, 2024" and "expires on June 30, 2029." (The MOU's title header reads "Collective Bargaining Agreement 2025 Through 2029" — an apparent inconsistency with the "2024-2029" label used everywhere else, most likely a fiscal-year-vs-calendar-year framing artifact rather than a different agreement; the Settlement and Award are both unambiguous and consistent on "2024-2029.")
- Text quality observed: **clean** (Arbitration Award, text_layer, 44,958 chars); **ocr_messy** (Settlement Agreement, OCR, 7,175 chars; MOU, OCR, 4,236 chars)
- CBA/labor-agreement/settlement/award classification: **arbitration award**, with an incorporated settlement agreement (Attachment 1) and a referenced clarifying MOU. Confirmed NOT a Sec.174.1535 mandatory-interest-arbitration proceeding.
- Mismatch from target: none requiring rejection. This is not the base CBA's full original text (which remains unresolved — see `houston_fire_source_resolution_2026-07-08.csv`), but it is a genuine, verbatim, high-quality wage-setting/wage-enforcing document for the same bargaining unit and cycle, consistent with this project's existing practice of ingesting arbitration awards as valid `contracts.csv` rows (see the Massachusetts JLMC award precedent in `docs/schema.md`'s `interest_arbitration_flag` note).
- Add to `data/contracts.csv`: **yes**
- Caveat: `hfdcoa.org` is the official website of the Houston Fire Department **Chief Officers Association** — a real, distinct, legitimate professional association representing chief officers, not the same union as HPFFA (rank-and-file) and not HPFFA's or the City's own official site. Treated as `official_or_high_quality_source=yes` on the strength of (a) internal consistency (real case number, dates, named Houston officials, a real Houston City Hall Annex address), and (b) independent corroboration from ABC13 Houston news reporting describing the identical S.B. 916/new-revenue/three-percent-escalator ruling — not because `hfdcoa.org` is itself one of the two contracting parties.

### Verbatim identity excerpts

- Award caption: "IN THE ARBITRATION BETWEEN HOUSTON PROFESSIONAL FIRE FIGHTERS ASSOCIATION, LOCAL 341, ASSOCIATION AND CITY OF HOUSTON, CITY... AAA CASE NO. 01-25-0005-2917... Collective Bargaining Agreement (CBA): 2024-2029... Decision: The Grievance is sustained."
- Award ruling: "Based on an evaluation of the evidence...the Associated showed by a preponderance of the evidence that the City violated CBA Article 17 § 2, further clarified by the MOU, by failing to provide an additional three percent escalator pay increase... The Grievance is sustained. ...The City is to pay the three percent pay escalator for FY26 retroactive to September 1, 2025." (dated "February 27, 2026," signed William E. Hartsfield, Arbitrator)
- Settlement recital: "The Parties are signatories to the 2024-2029 Collective Bargaining Agreement (CBA) ratified by City of Houston City Council on or about June 18, 2024, and Memorandum of Understanding dated June 11, 2024 (MOU)..."
- MOU header: "MEMORANDUM OF UNDERSTANDING REGARDING THE COLLECTIVE BARGAINING AGREEMENT 2025 THROUGH 2029 BETWEEN THE CITY OF HOUSTON, TEXAS AND HOUSTON PROFESSIONAL FIRE FIGHTERS ASSOCIATION, LOCAL 341..."

## Documents reviewed but not fetched/ingested

- **Interim Amendment No. 1** — genuine (verified in scratch, OCR), but a narrow procedural amendment unrelated to the escalator dispute; not stored in `corpus/`, per scope discipline.
- **Fire Department Classification and Salary Structure, Effective July 2024** — genuine wage-schedule appendix (verified in scratch, clean text layer), but not incorporated by reference into the Award/Settlement/MOU chain; deferred rather than fetched, so `base_wage_entry`/`base_wage_top` are left blank on the new row rather than populated from an unstored document.
- **Original full 2024-2029 CBA text (official City of Houston copy)** — still unresolved; the non-official khou.com news mirror was not used, per repo convention.
