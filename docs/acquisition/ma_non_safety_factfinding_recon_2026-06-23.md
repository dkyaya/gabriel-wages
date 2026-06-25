# MA non-safety factfinding / interest-arbitration reconnaissance

Date: 2026-06-23  
Prepared for: `gabriel-wages` corpus acquisition  
Purpose: reduce Codex cost by replacing broad web searching with a narrow, sourced acquisition plan.

## Executive summary

This reconnaissance did **not** find a verified, directly downloadable final non-safety factfinding report or non-safety interest-arbitration award for Somerville, Newton, or Boston that is ready for ingestion.

It did find several high-value *leads* that make a records-request/manual-acquisition step much cheaper and better scoped:

1. **Boston Teachers Union / Boston School Committee, PS-17-5987**  
   A public DLR petition packet is available from BTU. It is a petition for mediation/fact-finding, not a final factfinding report. It gives a concrete DLR case number and confirms that the impasse involved non-safety teacher units and economic issues. The next step is to query DLR Public Information Search and/or submit a DLR public-records request for the final factfinding report, case closing report, docket list, and any certification of completion.

2. **Newton Public Schools Custodians Association / Newton School Committee, PS-16-5177**  
   A Mass.gov DLR Hearing Officer decision in related prohibited-practice cases states that the School Committee filed a Petition for Mediation and Fact-Finding in PS-16-5177 after alleged impasse in successor negotiations. This is a concrete non-safety DLR factfinding docket lead, but the underlying CBA cycle appears to be 2011-2014, so it is probably outside the preferred observation window and not a direct match to current Newton police rows.

3. **Newton Teachers Association / Newton School Committee, SI-23-10203 and SI-23-10230**  
   Mass.gov strike-petition decisions and related public reporting show DLR/CERB involvement in the 2023-2024 NTA strike/settlement. Public records indicate a request for court involvement and possible binding arbitration if the dispute did not settle. The public record I found points toward settlement rather than a final arbitration award, so this is a **verification lead**, not a ready corpus document.

4. **Somerville non-safety units**  
   Mass.gov DLR decisions identify current Somerville non-safety municipal units, including SMEA Units A/B/D, SEIU crossing guards/E911, and custodians. Public union/school pages identify current educator contracts. I did **not** find a public final factfinding report for Somerville teachers/SMEA/non-safety units overlapping the 2012-2018 Somerville police awards. Because Somerville has two high-scoring safety awards, it remains the highest-value records-request target even without a docket number.

The correct next repo task is **not broad scraping**. It is a targeted documentation/request-prep task using:
- DLR Public Information Search for exact docket/case-number checks;
- DLR public records request for final reports/docket lists where the public-search system is incomplete;
- parallel municipal/school RAO requests only for the highest-value cities.

## Why DLR is the central route

Massachusetts DLR handles mediation, fact-finding, and arbitration services for public employers and employee organizations in contract disputes. DLR's FY2024 Annual Report also explains the key document-type split: in public-sector cases except police/fire, the next step after interest mediation is fact-finding, while police/fire matters proceed through JLMC arbitration. This distinction is exactly why the current H1 sample is confounded by document type: safety comparators are award-heavy, while non-safety comparators are mostly CBAs/MOAs.

DLR factfinding records may not always be searchable or posted. The DLR Public Information Search says it provides frequently requested public documents, but warns that not all DLR public documents are available and that search results are not comprehensive. Factfinding reports also have a confidentiality/publication rule: the report remains private while the parties attempt settlement, but DLR makes it public if the impasse remains unresolved ten days after DLR receives the report.

Implication: a failed web search is not enough to conclude that no report exists. The right follow-up is a narrow DLR PRR asking for case numbers, final reports, closing letters, certifications, and confirmation of non-existence.

## Corpus rules for any found document

Do **not** ingest any document unless it is locally present and entity/source-type verified.

Eligible for `contracts.csv`:
- final non-safety `factfinding` report;
- final non-safety `arbitration_award`, if genuinely an interest/contract-impasse award.

Not eligible as `factfinding` or `arbitration_award`:
- petition for mediation/fact-finding;
- strike-petition ruling;
- prohibited-practice / ULP decision;
- representation / unit-clarification decision;
- ordinary grievance-arbitration decision;
- CBA/MOA, unless classified as `source_type = cba`;
- news story or union bargaining update.

If returned records are petitions, docket sheets, closing letters, or certifications only, keep them in the acquisition file as provenance leads. Do not add corpus rows unless a schema-supported source document is obtained.

## Priority lead table

| Priority | City | Lead | Unit / occupation | Approx. cycle | Evidence found | Current status | Why it matters | Next action |
|---:|---|---|---|---|---|---|---|---|
| 1 | Somerville | SMEA / SEU / teacher / clerical / custodial non-safety factfinding, if any | teacher, clerical_admin, public_works, library, or other non-safety | ideally 2012-2018 | DLR decisions identify Somerville non-safety units; public union/school pages show current contracts, but no final factfinding report found | no docket found; high-value PRR target | Somerville has two high-scoring police awards; a same-city non-safety factfinding report would directly address the document-type confound | DLR PRR for any 2012-2018 non-safety mediation/factfinding dockets and reports; parallel Somerville / SPS RAO request |
| 2 | Boston | BTU / Boston School Committee, PS-17-5987 | teacher | 2016 successor negotiations after 2016 expiration | BTU-hosted DLR petition packet gives case number PS-17-5987, identifies BTU units, and lists salary/economic issues among disputed topics | petition found; final report not found | strongest concrete non-safety DLR docket lead; not a direct BPPA 2020-2025 match but useful for award-vs-award or factfinding-vs-award design | search DLR Public Info by case no. `PS-17-5987` / `17-5987`; PRR DLR for final report, closing report, docket list, certification, or no-record confirmation |
| 3 | Newton | Newton School Custodians Association / Newton School Committee, PS-16-5177 | public_works / school custodians | 2011-2014 CBA successor negotiations | Mass.gov DLR Hearing Officer decision says School Committee filed Petition for Mediation and Fact-Finding, PS-16-5177 | docket lead found; final report not found | concrete non-safety factfinding docket; likely outside observation window but useful to validate DLR retrieval route | search DLR Public Info by `PS-16-5177` / `16-5177`; PRR DLR for final report/closing docs; do not prioritize over Somerville if time-limited |
| 4 | Newton | NTA 2023-2024 strike / possible binding-arbitration output | teacher | 2023-2024 / 2024-2027 settlement | Mass.gov CERB strike-petition records and public reporting show strike/settlement; CERB sought possible binding arbitration if no agreement by deadline | likely settlement, not award; verify | future Newton pairing lead, not current match to 2015-2018 police row | PRR DLR for SI-23-10203 and SI-23-10230 related records, plus any contract-impasse/factfinding/interest-arbitration docket opened for NTA |
| 5 | Boston | SENA Local 9158 / City of Boston | clerical_admin | preferably 2019-2025 | Mass.gov SENA hits are ULP/representation decisions, not factfinding; Boston OLR has CBAs | no factfinding docket found | clerical/admin would be cleaner than teachers if an impasse report exists | DLR PRR for SENA contract-impasse dockets 2018-present; city OLR PRR if DLR returns index only |

## City notes

### Somerville

**What was found**
- Mass.gov DLR decisions identify Somerville's non-safety bargaining landscape. One 2023 DLR hearing-officer decision lists ten groups of Somerville bargaining-unit employees, including SMEA Units A/B/D, SEIU crossing guards/E911, and custodians represented by Firemen and Oilers Local 3.
- Another Mass.gov CERB decision describes SMEA Unit D as a specialized non-safety unit and lists example job titles.
- Somerville Educators Union pages host current contracts, but the visible public sources I found were CBAs/current bargaining materials, not final DLR factfinding reports.
- Some Somerville School Committee materials reference collective bargaining with AFSCME Clerical Local 2070 and SEU units, but those are agenda/current-process leads, not final awards/reports.

**What was not found**
- No public final factfinding report for Somerville teachers/SMEA/AFSCME/non-safety units overlapping 2012-2018.
- No concrete DLR PS docket number for a Somerville non-safety contract impasse.

**Recommended search/request terms**
- Somerville School Committee
- Somerville Teachers Association
- Somerville Educators Union / SEU
- Somerville Municipal Employees Association / SMEA
- SMEA Unit A, Unit B, Unit D
- AFSCME Clerical Local 2070
- SEIU Local 888 crossing guards / E911
- Firemen and Oilers Local 3 custodians
- contract impasse, mediation, fact-finding, PS docket, 2012-2018

**Action**
Submit a DLR master request first. If DLR returns no records or only an index, send parallel RAO requests to Somerville and Somerville Public Schools/School Committee for copies of any DLR factfinding reports, mediation/factfinding petitions, certifications, or closing letters.

### Boston

#### BTU PS-17-5987

**What was found**
- BTU hosts a four-page DLR petition packet for "Petition for Mediation and Fact-Finding in Public Employment or Voluntary Interest Mediation."
- The petition face page shows:
  - Case No.: PS-17-5987
  - Date filed: 2017-05-16
  - Employer: School Committee of the City of Boston
  - Labor organization: Boston Teachers Union Local 66, AFT Massachusetts
  - Contract expiration date: 2016-08-31
  - Negotiations commenced: 2016-02-02
  - Number of negotiation sessions: 30+
  - Number of employees: 6500+
- Attachment A identifies four units: teachers/nurses/academic personnel, paraprofessionals, substitute teachers, and ABA.
- Attachment B lists economic issues including salaries, longevity, educational-degree payments, related economic items, pay equity, and class-size overage payments.
- The cover letter says the parties had negotiated for more than sixteen months and held more than thirty sessions.

**Why it matters**
This is the strongest concrete DLR case-number lead. It is a teacher case, non-safety, and includes wage/economic issues. It is not a direct same-cycle match to the existing BPPA 2020-2025 row, but it could be useful for an award/factfinding-vs-award/factfinding comparison if a comparable safety award in that period exists or is added later.

**Do not ingest the petition**
The petition is not a final factfinding report or arbitration award. It can support an acquisition memo or PRR, but not a `contracts.csv` row as `source_type = factfinding`.

**Action**
Search DLR Public Information Search for:
- `PS-17-5987`
- `17-5987`
- `Boston Teachers Union`
- `School Committee of the City of Boston`

Then submit a DLR PRR if needed for:
- final factfinding report, if issued;
- case closing report;
- mediator's report / notice sufficient to determine disposition;
- certification of completion;
- docket list and document index;
- no-record confirmation if no factfinding report was issued or if settlement occurred before factfinding.

#### SENA / Boston clerical-admin

**What was found**
- Mass.gov search results for SENA Local 9158 are mostly Hearing Officer/CERB decisions about ULP/representation/work-transfer issues.
- Boston OLR hosts CBAs/MOAs, but no SENA final factfinding report was found.

**Action**
Treat SENA as a records-request target, not a web-download target. Ask DLR for SENA/City of Boston contract-impasse dockets and final factfinding reports from 2018-present.

### Newton

#### Newton custodians PS-16-5177

**What was found**
- A Mass.gov DLR Hearing Officer decision for MUP-16-5186 and MUP-16-5542 states that the Newton School Committee filed a Petition for Mediation and Fact-Finding on 2016-03-31, docketed as PS-16-5177, alleging impasse in successor negotiations concerning the 2011-2014 CBA.
- The unit is Newton Public Schools Custodians Association, a non-safety school custodial unit.

**Why it matters**
This is a concrete non-safety factfinding docket lead. The cycle is probably too old for the main observation window and not a direct Newton-police match, but it can be a useful test of the DLR retrieval route.

**Action**
Search DLR Public Info by `PS-16-5177` and `16-5177`. If not available, include it in a DLR PRR with the exact docket number.

#### Newton Teachers Association 2023-2024

**What was found**
- Mass.gov has CERB strike-petition materials for Newton Teachers Association / Newton School Committee, including SI-23-10203 and SI-23-10230.
- Public reporting and NTA/NPS contract pages indicate a 2024 settlement and 2024-2027 CBAs/MOAs.
- I did not find a final factfinding report or interest-arbitration award.

**Why it matters**
This is a current, high-salience non-safety teacher impasse. It is likely not a final award if the dispute settled, but the PRR should verify whether any DLR factfinding, binding-arbitration, case-closing, or certification records exist.

**Action**
Ask DLR for:
- SI-23-10203 and SI-23-10230 related records sufficient to identify any underlying contract-impasse dockets;
- any NTA / Newton School Committee mediation/factfinding/interest-arbitration docket from 2023-2024;
- confirmation whether any final report or award was issued.

## Negative / false-positive findings

| Source/hit type | Why not ingest |
|---|---|
| Mass.gov DLR Hearing Officer / CERB prohibited-practice decisions | These are adjudications about ULP/representation/work-transfer/strike issues, not final contract-impasse factfinding reports or interest-arbitration awards. They may contain useful docket leads but are not corpus rows under current `contracts.csv` schema. |
| JLMC Interest Arbitration Decisions page | Useful for police/fire safety awards only. It does not solve the non-safety comparator gap. |
| DESE / district educator contract pages | These are CBAs/current contract documents. Useful for wage outcomes if needed, but they do not de-confound award-vs-CBA source type. |
| Union bargaining-update pages and press releases | Useful for chronology and contact/lead generation. Not causal-corpus source documents unless the full underlying CBA/MOA/factfinding report is obtained and classified correctly. |
| Petition for Mediation and Fact-Finding | A petition is a lead, not a final report. It should not be ingested as `factfinding`; use it to request the final report or confirm none exists. |
| Strike-petition rulings | These can identify impasse context and court/DLR involvement, but they are not wage-setting factfinding reports or interest-arbitration awards. |

## Recommended manual/low-cost sequence

1. **DLR Public Information Search: exact docket checks**
   - Use `https://pubinfo.dlr.state.ma.us/`.
   - Search Case Documents by exact case numbers:
     - `PS-17-5987` and `17-5987`
     - `PS-16-5177` and `16-5177`
     - `SI-23-10203`
     - `SI-23-10230`
   - Also search by party names:
     - Boston Teachers Union
     - School Committee of the City of Boston
     - Newton Public Schools Custodians Association
     - Newton School Committee
     - Newton Teachers Association
     - Somerville Municipal Employees Association
     - Somerville Educators Union
     - Somerville School Committee
     - City of Somerville
     - SENA Local 9158
   - Save any document index / case list as acquisition evidence, but do not stage anything as a corpus document unless it is the final report/award.

2. **DLR master public-records request**
   - Ask for final factfinding reports, final interest-arbitration awards if any, case closing reports, certifications of completion, petitions, docket lists, and no-record confirmations for the specific targets above.
   - Include exact case numbers for Boston BTU and Newton custodians.
   - For Somerville, ask for an index first if the request is broad.

3. **City/school RAO requests after DLR**
   - Somerville/SPS first, because Somerville has two high-value police award observations and no non-safety comparator.
   - Newton/NPS second, especially if DLR cannot confirm NTA or custodian records.
   - Boston/BPS/OLR third, targeted to BTU PS-17-5987 and SENA/clerical-admin impasse records.

4. **Intake returned records**
   - Save returned PDFs under `inbox/foia/`.
   - Record custodian, response date, retrieval method (`foia` unless public direct download), and exact citation/URL.
   - Conduct first-page/entity check before any manifest row.
   - Do not manually add `contracts.csv` rows.
   - Use `process_inbox.py` only after the full source document is local and source_type is verified.

## Suggested DLR PRR language

> I am requesting public records sufficient to identify and obtain final fact-finding reports, final interest-arbitration awards, case closing reports, certifications of completion of the collective-bargaining process, docket/case numbers, petitions, appointment notices, or closing letters for non-public-safety public-sector contract-impasse matters involving the following employers and bargaining units. I am not requesting ordinary discipline/grievance arbitration records unless they are part of a collective-bargaining/contract-impasse matter.

Then list:
- Boston Teachers Union Local 66 / School Committee of the City of Boston, including PS-17-5987 and any resulting final report or closing/certification records.
- Newton Public Schools Custodians Association / Newton School Committee, including PS-16-5177 and any resulting final report or closing/certification records.
- Newton Teachers Association / Newton School Committee, including any 2023-2024 mediation, factfinding, interest-arbitration, or strike-related records connected to SI-23-10203 and SI-23-10230.
- City of Somerville / Somerville School Committee non-safety bargaining units, including SMEA Units A/B/D, SEU/teacher units, AFSCME clerical, custodial, library, public works, and other non-safety municipal/school units, from 2012-2018.
- City of Boston / Boston School Committee non-safety units, including SENA Local 9158, BTU, SEIU 888, AFSCME, OPEIU 6, and other clerical/admin or teacher units, from 2016-present.

Suggested narrowing sentence:

> If this request is too broad, please first provide an index, docket list, case captions, or case numbers for responsive non-safety contract-impasse matters so that I can narrow the request.

## Sources consulted

Official / high-authority sources:
- Massachusetts DLR organization page: `https://www.mass.gov/orgs/department-of-labor-relations`
- DLR Contract (Interest) Mediation and Fact Finding page: `https://www.mass.gov/contract-interest-mediation-and-fact-finding`
- DLR Fact-finding page: `https://www.mass.gov/info-details/fact-finding`
- DLR FAQ - Impasse: `https://www.mass.gov/info-details/faq-impasse`
- DLR Public Records Request: `https://www.mass.gov/department-of-labor-relations-public-records-request`
- DLR PRR form: `https://www.mass.gov/forms/department-of-labor-relations-public-records-request`
- DLR Public Information Search: `https://pubinfo.dlr.state.ma.us/`
- FY2024 DLR Annual Report: `https://malegislature.gov/Reports/19922/FY24%20DLR%20Annual%20Report.pdf`
- 456 CMR 21.00: `https://www.mass.gov/regulations/456-CMR-2100-rules-for-interest-mediation-fact-finding-and-interest-arbitration-in-disputes-involving-public-employers-and-public-employees-private-sector-interest-mediation`
- 456 CMR 21 PDF: `https://www.mass.gov/doc/456-cmr-21-rules-for-interest-mediation-fact-finding-and-interest-arbitration-in-disputes-involving-public-employers-and-public-employees-private-sector-interest-mediation/download`

Target-specific sources:
- BTU PS-17-5987 petition packet: `https://btu.org/wp-content/uploads/2017/05/Case_Filed.pdf`
- Newton custodians DLR Hearing Officer decision, MUP-16-5186 / MUP-16-5542: `https://www.mass.gov/doc/mup-16-5186-mup-16-5542-hearing-officer-decision/download`
- Newton Teachers Association strike-petition record, SI-23-10203: `https://www.mass.gov/doc/si-23-10203-ruling-on-strike-petition-interim-order/download`
- Newton Teachers Association amended/supplemental strike-petition records, SI-23-10230 / SI-23-10203 variants:
  - `https://www.mass.gov/doc/si-23-10230-amended-cerb-ruling-on-supplemental-strike-petition/download`
  - `https://www.mass.gov/doc/si-23-10230-cerb-ruling-on-stike/download`
  - `https://www.mass.gov/doc/si-23-10203-amended-cerb-ruling-on-supplemental-strike-petition/download`
- Somerville SMEA unit-clarification / unit-description decisions:
  - `https://www.mass.gov/doc/mcr-23-9789-hearing-officer-decision/download`
  - `https://www.mass.gov/doc/cas-23-9758-cerb-decision/download`
- Boston SENA / DLR decisions page: `https://www.mass.gov/info-details/dlr-hearing-officer-cerb-and-arbitration-decisions`

Useful index / secondary route:
- StateReference DLR cases index: `https://www.statereference.com/pages/dlr_cases`
- StateReference DLR contracts index: `https://www.statereference.com/pages/dlr_contracts`

Note: StateReference is useful as an index because it sources DLR Public Information Search records, but the original DLR source should be preferred for provenance when possible.
