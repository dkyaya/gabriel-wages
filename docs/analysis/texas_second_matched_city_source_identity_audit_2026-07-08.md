# Texas Second Matched-City Source Identity Audit — 2026-07-08

Reviews the single newly fetched document: the Austin EMS Association meet-and-confer agreement. No GABRIEL, Harvard Proxy, model/API, PRR, FOIA, or context-only ingestion calls were made.

## tx_austin_nursehealth_2023

- Stored path: `corpus/tx_austin/tx_austin_aemsa_ems_meet_confer_2023_2027.pdf`
- **Identity verdict: confirmed**
- City: Austin, TX
- Union/unit: Austin EMS Association (AEMSA)
- Employer/jurisdiction: City of Austin / Austin-Travis County Emergency Medical Services Department
- Document type: **meet-and-confer agreement** (Texas Local Government Code Chapter 142, Subchapter D, Sections 142.151-142.163)
- Agreement/cycle years visible: effective "the date it is ratified by the City Council or October 1, 2023, whichever occurs later"; remains in effect "until September 30, 2027" (Article 23, Term of Agreement)
- Text quality observed: **clean** (text_layer, 88 pages, 250,194 chars via `ingest/extract_text.py`)
- Mismatch from target: none requiring rejection. This is the base, complete, executed agreement (not the July 18, 2024 amendment, which was reviewed for context only and not separately fetched, since the base agreement is a self-sufficient complete text).
- Add to `data/contracts.csv`: **yes**
- Caveat: Austin-Travis County EMS is governed by its own Chapter 142 Subchapter D meet-and-confer statute and shares a joint Firefighters'/Police Officers'/EMS Civil Service Commission under Chapter 143 with police and fire — i.e., it is civil-service-protected and statutorily adjacent to public safety, but is not itself "police" or "fire" under this project's controlled `occupation_class` vocabulary. Classified as `occupation_class=nurse_health` (closest schema fit for pre-hospital emergency medical/paramedic personnel), `safety_flag=0`.

### Verbatim identity excerpts

- Recognition (Article 3): "The CITY recognizes the ASSOCIATION as the sole and exclusive bargaining agent for all Uniformed Staff, as defined in Article 2 of this Agreement."
- Bargaining-unit definition (Article 2, Definitions, item 14): "'Uniformed Staff' means a member of the bargaining unit represented by the ASSOCIATION...The term applies only to employees: a) Employed in the Department as 'Emergency Medical Services Personnel' as defined by Texas Health and Safety Code, Chapter 773; and b) Whose position requires substantial knowledge of 'Emergency Prehospital Care' as defined by Texas Health and Safety Code, Chapter 773." The same definition explicitly states the term "excludes civilian employees."
- Term (Article 23): "...shall be effective...the date it is ratified by the City Council or October 1, 2023, whichever occurs later...It shall remain in full force and effect...until September 30, 2027."
- Wage schedule (Article 6, Section 1): "For Fiscal Year 2023-2024...the pay scale attached as Appendix A shall apply...For Fiscal Year 2024-2025...the pay scale...reflects a 4.0% increase to base wages...For Fiscal Year 2025-2026...reflects a 3.0% increase...For Fiscal Year 2026-2027...reflects a 3.0% increase."

## Recognition-clause-first determination

This is a **single-occupation bargaining unit** (EMS/paramedic personnel only, civilians explicitly excluded by the unit's own definition) — not a broad, bundled multi-department unit. The recognition-clause-first rule's ambiguity concern (does the unit span multiple occupation classes requiring a conservative `occupation_class=other` placeholder?) does not apply here, analogous to how Austin's fire and police agreements were determined to be clean single-occupation units. `occupation_class=nurse_health` is final, not provisional.
