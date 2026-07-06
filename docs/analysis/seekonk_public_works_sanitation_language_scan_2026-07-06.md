# Seekonk Public Works Sanitation Language Scan — 2026-07-06

**Type:** existing-corpus inspection memo. Follow-up to `sanitation_city_service_structure_scan_2026-07-06.md` Task A (Seekonk as the "single most promising already-collected-corpus lead").

**Scope:** read-only inspection of the already-collected Seekonk public works CBA for hidden, implicit, or bundled sanitation/solid-waste language. No document ingestion, no new rows, no GABRIEL, no model/API calls, no OEWS/BLS work, no corpus/inbox changes. This is existing-corpus inspection only.

---

## 1. Purpose and scope

This memo inspects the already-collected `ma_seekonk_public_works_2023` CBA's full text to determine whether sanitation/solid waste/transfer station collection work is present, bundled into existing job titles, implied by operational language, or absent. The task is narrowly scoped to the one document already in this project's corpus; it does not ingest new sources, add rows, or make wage-mechanism claims. It tests the `sanitation_dpw_bundling` hypothesis (H35/SN08) against textual evidence from a specific city's already-existing contract.

---

## 2. Source inspected

| field | value |
| --- | --- |
| **obs_id** | `ma_seekonk_public_works_2023` |
| **city** | Seekonk |
| **occupation_class** | `public_works` |
| **bargaining_unit_name** | AFSCME Council 93 Local 1701 Department of Public Works |
| **contract period** | July 1, 2023 – June 30, 2026 |
| **source_type** | CBA |
| **source_url** | https://www.seekonk-ma.gov/Archive.aspx?ADID=727 |
| **retrieval_date** | 2026-06-24 |
| **retrieval_method** | public_download |
| **full_text_path** | corpus/ma_seekonk/ma_seekonk_public_works_afscme_local_1701_2023_2026.pdf |
| **text_quality** | clean |
| **corpus_file_exists** | Yes (738 KB, successfully extracted to text) |
| **text_readable** | Yes (native PDF; `pdftotext` extraction yielded 675 lines of clean text) |

---

## 3. Search terms and method

**Search terms used:**
- sanitation, solid waste, refuse, trash, garbage, recycl(e/ing), transfer station, landfill, collection, route, pickup, truck, CDL, driver, operator, equipment, highway, laborer, public works, DPW, foreman, call-back, overtime, snow, storm, sewer, water

**Search method:**
- Full text extraction via `pdftotext` (675 lines)
- Grep searches for all terms above (case-insensitive, -ni flags)
- Context inspection of matches found

**Result:** 16 hits on substantive terms; detailed below.

---

## 4. Findings

### 4.1 Explicit sanitation / solid-waste language

**Finding:** None. Zero explicit references to sanitation, solid waste, refuse, garbage, recycling, collection, pickup, or trash appear anywhere in the document.

**Evidence:** All 16 keyword hits map to general DPW or operational contexts, not sanitation-specific language (see Sections 4.2–4.6 below).

---

### 4.2 Possible bundled DPW sanitation-relevant language

**Finding:** One substantive reference to "Transfer Station," but with limited operational detail.

**Exact text found (line 132 of extracted PDF):**
> "The only exceptions to the above will be work at the Transfer Station which will be any consecutive five (5) days, excluding Sunday."

**Context:** This appears in Article II, Section 1 ("Hours of Work") and modifies the standard Monday–Friday, 7 AM–3:30 PM work schedule. The contract states the standard work week is "forty (40) hours, five (5) consecutive eight (8) hour days, Monday through Friday," but "exceptions" for "Transfer Station" work allow "any consecutive five (5) days, excluding Sunday."

**Interpretation:** The reference explicitly names a "Transfer Station" as a work location with different scheduling requirements. This is the single strongest textual signal that sanitation/waste-handling work (transfer station operation) is included in this bargaining unit's scope. However:
- The reference is operationally minimal: only scheduling rules, no job title, no duty description, no classification.
- No job classification or title is linked to "Transfer Station" work elsewhere in the contract.
- No sanitation, collection, refuse, or related terms appear nearby to clarify what "Transfer Station" work entails.

**Classification:** Possible bundled sanitation language (scheduled work location named, but no explicit job title or duty language).

---

### 4.3 CDL / truck / equipment / operator language

**Finding:** Yes. CDL licensing is explicitly mentioned as a reimbursable training expense.

**Exact text found (Article IV, Section 9, "Fees"):**
> "The Town will provide reimbursement for CDL related training expenses to eligible employees. Additionally, eligible employees can also request reimbursement for expenses incurred with respect to other Town related licenses that have been successfully obtained by the employee."

**Interpretation:** The explicit mention of "CDL related training expenses" and reimbursement for "eligible employees" indicates that CDL-holding positions exist within this bargaining unit. CDL (Commercial Driver's License) is required for truck operation, including collection-vehicle operation. This language is consistent with positions that could plausibly involve collection-truck driving, but the contract does not explicitly name any such position or tie CDL training to sanitation duties.

**Note:** The same section mentions "special license fees" and "particular equipment and supplies," suggesting equipment-operation roles exist, but without explicit sanitation reference.

**Classification:** Possible bundled sanitation-relevant language (CDL requirement named, consistent with collection driving, but not explicitly linked to any sanitation duty).

---

### 4.4 Overtime / callback / scheduling / operational language

**Finding:** Yes. Overtime rules and callback procedures detail operational coverage expectations, including explicit "snow and ice" and "weather event" language relevant to year-round coverage pressure.

**Exact text found:**

*Overtime (Article II, Section 5):*
> "Overtime shall be divided as equally as possible amongst those employees within the particular classification... The Town will attempt to offer overtime first to the qualified employee with the fewest overtime hours..."

*Weather events (Article II, Section 6):*
> "If an employee works a continuous sixteen (16) hours for a 'weather event' or 'snow storm,' all hours leading up to the sixteenth hour and all of the hours thereafter in the next calendar day is considered overtime."

*Call-back (Article II, Section 7):*
> "Call back shall not be interpreted as Stand-By in this Agreement... for all call back hours, with a minimum of four (4) hours pay."

*Snow-removal incentives (Article III, Section 13):*
> "Effective July 1, 2023, members called out for hurricanes or snow removal before 7:30 AM or after 4:00 PM shall be reimbursed for actual breakfast expenses not to exceed $10..."

**Interpretation:** The contract includes substantial, detailed language on overtime distribution, callback procedures (minimum 4-hour pay guarantee), and weather-event premium pay (continuous 16-hour threshold). These operational mechanisms are fully consistent with DPW sanitation work, which requires year-round weather-event response (collection during or after storms, emergency cleanup, etc.), but the contract does not explicitly link these operational provisions to sanitation duties. They apply to "employees within the particular classification" broadly, not to a named sanitation role.

**Classification:** Operational language present and potentially relevant to sanitation work, but not sanitation-specific.

---

### 4.5 Contractor / substitution / management-rights language

**Finding:** No explicit contractor-substitution or privatization language. No evidence that sanitation collection is outsourced or subcontracted.

**Interpretation:** The contract's silence on contractor substitution for sanitation (if sanitation work exists in this unit) is consistent with municipal-staffed operation. However, this is an absence-of-evidence finding, not evidence of absence — the contract does not state whether sanitation is provided by municipal employees or a contractor.

**Classification:** No contractor substitution language found.

---

### 4.6 Management-rights / reorganization / classification language

**Finding:** Yes. One significant classification change announced in the wage section.

**Exact text found (Article II, Section 4, "Salaries"):**
> "Laborer/Maintenance job classification shall be eliminated upon vacancy (Current incumbent is grandfathered into existing title/wage scale)."

**Interpretation:** A "Laborer/Maintenance" job classification is being systematically eliminated (upon vacancy, not immediately). The note that the "current incumbent is grandfathered" indicates at least one current employee holds this title. This language is consistent with a DPW reorganization that may or may not involve sanitation duties — general DPW labor and maintenance work could plausibly include sanitation collection, and the elimination of a "Laborer" tier could indicate either: (a) general laborers doing mixed DPW tasks (including possible sanitation) are being reclassified into more specific job titles (mechanic, equipment operator, etc.), or (b) those duties are being outsourced or eliminated. The contract does not specify which.

**Classification:** Management flexibility / reclassification language present, but ambiguous whether it affects sanitation specifically.

---

### 4.7 Absences

**Finding:** Notable absence of the following, despite the "Transfer Station" reference:
- No job classifications or titles explicitly tied to collection, transfer station, sanitation, or waste-related work
- No job-description Appendix or Schedule listing specific positions and their duties
- No yard/route/assignment language
- No equipment-specific language (no mention of trucks, loaders, collection vehicles, etc.)
- No sanitation-specific benefits or hazard-pay language
- No recycling-, disposal-, or refuse-management references

---

## 5. Classification of evidence

**Classification:** `sanitation_possible_but_unconfirmed`

**Rationale:**

The contract contains two substantive, but not explicit, signals suggestive of possible sanitation work:

1. **Transfer Station scheduling reference** (the strongest signal): The contract explicitly names "Transfer Station" as a work location with distinct scheduling rules, indicating that transfer-station operation (a sanitation/waste-handling function) is included in the unit's scope of work. This is a real, named location-specific reference.

2. **CDL training reimbursement**: The contract explicitly reimburses CDL-related training, indicating truck-driving positions exist within the unit. CDL is required for collection-vehicle operation.

However, both signals are **operationally minimal and unlinked to explicit job titles or sanitation duties**:
- The "Transfer Station" reference lacks a corresponding job title, job classification, or duty description.
- The CDL reference is general ("eligible employees") with no statement of which positions require a CDL or for what purpose.
- The entire contract contains zero explicit sanitation, collection, refuse, recycling, or waste-related terminology.
- No job-description Appendix or Schedule is included in the extracted text to clarify position titles and duties.

**Conclusion:** The evidence is consistent with sanitation/transfer-station work being bundled into this DPW unit (the `sanitation_dpw_bundling` hypothesis H35/SN08), but the evidence is not explicit enough to confirm it without: (a) an Appendix or Schedule of job descriptions (which may exist but was not found in the extracted text), or (b) a deeper inquiry into the town's actual service delivery structure (whether Seekonk operates its own collection service or contracts it out).

---

## 6. Implication for sanitation source strategy

**Recommendation:** Seekonk is a **promising lead for DPW-bundled sanitation language**, but further investigation is needed to confirm:

1. **First step:** Verify whether the PDF extraction included the full contract (all Appendices and Schedules). The "Laborer/Maintenance" classification elimination reference suggests there should be a wage schedule or position listing; confirm whether any job-description Appendix or position Schedule exists in the original PDF but was not extracted by `pdftotext`.

2. **Second step (if Appendix exists):** Re-read the Appendix to check for job-title, duty, or wage-schedule language explicitly naming or describing collection, sanitation, or transfer-station roles.

3. **Parallel step:** Cross-check the town's own service-delivery structure (does Seekonk operate its own residential collection service, or contract it out?) against this contract's language. The `sanitation_city_service_structure_scan_2026-07-06.md` memo already confirmed Seekonk operates a "Pay-As-You-Throw" program "administered by the Public Works department," but did not conclusively determine whether the actual collection crews are municipal employees or a contractor.

4. **If confirmed municipal-staffed:** The "Transfer Station" reference + CDL language + "Laborer/Maintenance" reclassification would constitute substantive (though still somewhat sparse) corpus evidence of sanitation duties bundled into the DPW unit, supporting the `sanitation_dpw_bundling` hypothesis.

5. **If confirmed contractor-staffed:** The contract's reference to "Transfer Station" work could indicate that the municipal DPW staff operate the transfer station (a fixed-location, non-collection function) while a private hauler handles residential collection — consistent with the contractor-substitution finding in the city-service-structure scan.

---

## 7. Recommended next step

**For this memo:** Confirm whether the PDF contains a job-description Appendix by re-opening the original PDF directly and checking for any Schedule, Appendix, or position-listing pages not captured by `pdftotext` extraction.

**For Seekonk's sanitation status:** Integrate this contract-inspection finding with the town's confirmed service-delivery structure (municipal or contractor) to reach a final determination on whether Seekonk should be treated as:
- A confirmed `sanitation_dpw_bundled` site (if municipal-staffed collection exists and the Appendix clarifies the duties),
- A `sanitation_possible_but_unconfirmed` site pending Appendix review and/or service-structure verification, or
- A `sanitation_contractor_not_municipal_cba` site (if confirmed contractor-staffed, making this contract minimally relevant to sanitation wage mechanisms).

**Do not recommend ingest a new sanitation document or add a new row to `data/contracts.csv` at this time.** This inspection is read-only; any decision to treat Seekonk's existing `public_works` row as carrying sanitation-relevant evidence requires a separate, explicit decision from the user/PI once the Appendix question and service-structure verification are resolved.

---

## 8. Quality note

The PDF text extracted cleanly and completely (675 lines, no OCR errors, native PDF). The absence of job-description Appendix text in the extraction suggests either: (a) the Appendix does not exist in the source PDF, or (b) `pdftotext` failed to extract it (less likely, given the clean extraction of all other sections). Direct PDF inspection is recommended to resolve this uncertainty.
