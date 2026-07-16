# Texas national batch 01 source-verification review

Date: 2026-07-16
Verification scope: the six parsed live-scout candidates for San Antonio and Houston, plus a bounded manual triage of Austin's raw web-search trace because Austin returned no parsed candidates.

## Bottom line

The Texas scout produced one source that is ready to advance to a separate pre-ingestion review: the official City-hosted **2015–2018 Houston Organization of Public Employees (HOPE) meet-and-confer agreement**. It is a full municipal-employee agreement, expressly excludes classified police and fire, runs through June 30, 2018, and contains base-pay changes and pay-grade material.

The remaining parsed results are useful at lower stages but are not ingestion-ready:

- Houston's 2015–2018 police agreement is a strong full-document lead, but its S3 archive owner and chain of custody are not established. It remains only partially verified until an official City or HPOU copy is confirmed.
- Houston's 2021–2024 HOPE agenda item is an official repeat-cycle locator with wage changes, but it supplies only a cover sheet, not the underlying agreement.
- Houston's firefighter item is an official City Attorney memo about a settlement and seven-year dispute. It is not a fact-finding or arbitration award and does not include the executed settlement.
- San Antonio's Fire CBA is genuine, complete, and City-hosted, but it is a fire agreement—not the requested civilian comparator. The scout's `non_safety` label is wrong-unit leakage.
- San Antonio's Municode URL opens, but the returned HTML is only a JavaScript application shell. The claimed ordinance text and institutional non-availability interpretation were not verifiable from the response.
- Austin's trace identifies an official civilian consultation mechanism and a City compensation page, but the useful documents are post-window and do not supply an ordinary non-EMS 2014–2024 agreement or wage schedule.

Nothing in this pass was ingested, codified, added to verified coverage, or used as claim evidence. “Verified candidate” in the new ledger means that the returned source's identity and relevant contents were directly checked; it does not mean the source has passed the project's ingestion, matched-cycle, codification, or claim-support gates.

## What this pass did and did not do

This pass opened the exact six candidate URLs, recorded reachability and final URLs, inspected source ownership, employer and unit identity, determined document type and completeness, read visible dates and wage provisions, and assessed whether each item served the city-specific scout purpose. PDFs were downloaded only to `tmp/source_verification/TX/national_batch01_tx_2026-07-16/`, text-extracted where possible, and visually checked on representative pages. The only follow-up click was the attachment exposed by Houston's HOPE agenda page; it returned the signed two-page cover sheet.

Austin's raw response contained 51 web-trace URLs. All 51 were screened for relevance using the saved trace. Eighteen potentially relevant City, union, budget, compensation, or agreement URLs were directly opened and recorded as trace-only rows. The other 33 were not elevated because their trace labels or domains made them plainly generic news, Reddit, video, case-law, unrelated labor commentary, or otherwise outside the ordinary City-employer comparator purpose. This was a bounded calibration pass, not an open-ended source search.

This pass did **not** search for replacement URLs, request records, authenticate behind logins, verify documents outside the three Texas municipalities, test any source through the ingestion pipeline, map broad agreements to new contract rows, update canonical coverage, run GABRIEL, call a model/API, or run `gabriel.codify`.

## Why the earlier audits were not source verification

The earlier runner and repository audits established that the live run stayed within the authorized three rows, all three responses parsed, six candidate rows reconciled to the raw output, and every candidate remained quarantined as `unverified_scout_candidate`. Those are execution and accounting checks. They do not prove that a URL opens, the host owns the source, the document is complete, the named employer and bargaining unit are correct, the asserted years are visible, or the item contains useful wage material. This pass adds those direct source checks while preserving a separate verification-stage ledger.

## Counts and controlled outcomes

Parsed scout candidates reviewed: **6**.

- San Antonio: **2** parsed candidates.
- Austin: **0** parsed candidates; **51** raw trace URLs screened and **18** directly reviewed as trace-only rows.
- Houston: **4** parsed candidates.

Controlled verification outcomes across the six parsed candidates:

| Verification status | Count | Meaning in this pass |
|---|---:|---|
| `verified_candidate` | 2 | Source identity and contents verified: San Antonio fire CBA and Houston HOPE 2015–2018. |
| `partially_verified_candidate` | 1 | Houston police document contents verified; source ownership/provenance remains uncertain. |
| `context_only_verified` | 2 | Houston 2021 HOPE cover sheet and firefighter settlement memo are authentic context but not full qualifying contracts/awards. |
| `insufficient_evidence` | 1 | San Antonio Municode returned only an application shell, not the claimed ordinance text. |
| `trace_only_not_candidate` | 18 | Austin trace rows remained outside parsed-candidate status regardless of reachability. |

Only one row has `ingestion_recommendation=later_ingest_candidate`: Houston HOPE 2015–2018. That label still requires the separate pre-ingestion steps described below.

## Results by city

### San Antonio

**Civilian/non-safety comparator result: no usable comparator was verified.**

The City-hosted Fire PDF is a full 89-page collective bargaining agreement between the City of San Antonio and IAFF Local 624, effective October 1, 2009 through September 30, 2014. Its table of contents includes wages. This verifies the source, but it also conclusively shows that the scout returned a safety agreement while labeling it `non_safety`. It does not establish a civilian comparator or civilian non-availability.

The Municode URL returned HTTP 200 without login, but the downloaded HTML contained only the generic Municode client application. No requested node text, effective date, employee scope, or collective-bargaining prohibition was visible. The scout's broad legal interpretation therefore remains unsupported. It should not be ingested or cited.

### Austin

**Non-EMS ordinary non-safety result: no usable in-window lead was verified.**

The strongest Austin trace items are institutional context:

- City EDIMS document `465936` is a five-page 2026 draft resolution for consultation with AFSCME Local 1624 over civilian City-worker conditions.
- City EDIMS document `468416` is the adopted February 26, 2026 consultation policy for groups of non-sworn City employees.
- AFSCME Local 1624's site confirms that it represents both City of Austin and Travis County workers. That mixed-employer scope must be separated in any later use.
- The City Human Resources Compensation Division page separately labels Municipal, EMS, Fire, and Police pay scales and states a $22.05 living wage effective October 2025. The returned HTML did not expose a municipal scale URL or in-window values.

These materials support the existence of a civilian representation/consultation and compensation pathway, but they are outside 2014–2024 or lack the actual wage-setting document needed for a contract-cycle comparison. They are not a substitute for an ordinary non-EMS agreement or in-window pay schedule.

Five plausible trace URLs were unavailable or blocked: four returned 404 and the DOL PDF returned 403. Two reachable union pages were clear wrong-employer leakage: AFSCME Local 3336 is in Portland, Oregon, and AFSCME Local 3866 covers Eastern Michigan University. Other reachable City/union trace pages concerned police, fire, generic agendas, a 2005 transcript, or post-window context.

### Houston

**Repeat-cycle and mechanism result: useful, with one strong non-safety agreement and three lower-stage leads.**

1. **HOPE 2015–2018 — strongest lead.** The official City PDF is a complete 115-page meet-and-confer agreement between HOPE and the City. The bargaining-unit definition covers municipal employees and excludes classified police and fire. Article 10 gives FY2016–FY2018 annualized base-pay increases, a minimum base rate, and shift differentials; Article 19 keeps the agreement in force through June 30, 2018. This is usable for a later pre-ingestion review.
2. **HPOU police agreement — strong but provenance-incomplete.** The 105-page PDF names the Houston Police Officers' Union and City of Houston, runs through December 31, 2018 with continuation terms, and contains 2015–2018 pay and step tables. The host is a `citypuc` S3 repository whose owner was not established. Confirm an official City or HPOU copy before ingestion.
3. **HOPE 2021–2024 cover sheet — repeat-cycle context.** The official City Council agenda page and signed cover sheet state a term ending June 30, 2024, 3% increases in October 2021, July 2022, and July 2023, and a $14.25 minimum wage. The candidate page did not expose the actual agreement through its accessible attachment link. The cover sheet is a locator, not a contract.
4. **Firefighter settlement memo — mechanism context.** The official three-page City Attorney memo covers backpay from July 1, 2017 to March 1, 2024, a seven-year court battle, intercity pay comparisons, and court/arbitration risk. It supports the scout's impasse/settlement purpose but corrects the model's `factfinding` classification: this is an explanatory settlement memo, not a fact-finding report, arbitration award, or the executed settlement itself.

Houston HOPE material is therefore usable in two different senses: the 2015–2018 full agreement is a later-ingestion candidate, while the 2021–2024 cover sheet is only a verified locator/context source. They must not be merged or assigned the same stage.

## Wrong-employer and wrong-unit leakage

No parsed candidate substituted a county, school district, transit authority, hospital/health district, regional authority, special district, or private provider for the target City employer.

There was nevertheless meaningful calibration leakage:

- San Antonio's parsed Fire CBA was assigned `original_unit_type=non_safety`; direct inspection corrected it to `verified_unit_type=fire`.
- Austin's raw trace included at least two clear wrong-employer pages: Portland AFSCME Local 3336 and Eastern Michigan University AFSCME Local 3866. Neither became a parsed candidate.
- Austin Local 1624 represents both City and County workers. Its page is not wrong-employer by itself, but later documents must identify City employees explicitly rather than treating mixed City/County union material as interchangeable.

## Strongest leads and rejections

Strongest verified or partially verified leads, in order:

1. Houston HOPE 2015–2018 full City-hosted agreement — verified non-safety later-ingestion candidate.
2. Houston HPOU 2015–2018 full police agreement — partially verified; official provenance still needed.
3. Houston HOPE 2021–2024 official cover sheet — verified repeat-cycle and wage locator, context only.
4. Houston firefighter settlement memo — verified impasse/settlement context, not the underlying causal document.

Rejected or context-only items:

- San Antonio Fire 2009–2014: authentic but wrong unit and not responsive to the civilian-comparator purpose.
- San Antonio Municode: insufficient evidence because only the client shell was returned.
- All Austin rows: trace-only; none provides an in-window ordinary non-EMS comparator document.
- Houston HOPE 2021 cover and fire memo: context-only; do not ingest as substitutes for the full agreement or settlement/award.
- Austin Local 3336 and Local 3866: wrong employers.

## What must happen before ingestion

For Houston HOPE 2015–2018, a separate pre-ingestion pass should:

1. map covered classifications to one or more valid occupation-specific contract rows without collapsing heterogeneous occupations;
2. retain one bargaining unit and one negotiation cycle per row;
3. establish the precise effective/start date in addition to the June 30, 2018 endpoint;
4. confirm overlap with a verified Houston police or fire cycle;
5. populate all required provenance fields and preserve verbatim wage/mechanism spans only through the ingestion pipeline; and
6. run validation and coverage audit after, not during, that later ingestion task.

For the police PDF, first obtain or confirm an official City/HPOU copy. For the 2021 HOPE cycle, retrieve the actual agreement rather than ingesting the cover sheet. For the fire dispute, obtain the executed settlement, qualifying arbitration award, or other causal document and verify the union/parties. No current item should be manually appended to `contracts.csv`.

## Calibration and scaling recommendation

The row-aware prompt is materially safer than a generic city prompt: none of six parsed candidates used a wrong employer, and it identified the strongest intended Houston non-safety agreement. It is not yet calibrated well enough for a large next-state release. Only one of six parsed rows is a clear later-ingestion candidate; San Antonio still produced wrong-unit context, Austin returned no candidate despite plausible post-window traces, and the trace itself contained wrong employers.

Before scaling, tighten the output rule so a row labeled `non_safety` must identify an ordinary municipal employee unit or an authoritative civilian pay plan; a safety CBA cannot be returned merely to explain civilian exclusion. Prefer direct full-document URLs and official City/union ownership; classify agenda covers and explanatory memos as context; and allow an explicit “no qualifying candidate found” result. After those adjustments and a dry-run review, the next live scout—if separately authorized—should remain a small state slice with verification capacity reserved immediately afterward, not a broad batch.

## Audit artifacts

- Controlled verification ledger: `docs/analysis/national_batch01_tx_source_verification_2026-07-16.csv`
- Quarantined downloads, response headers, extracted text, representative renders, and SHA-256 manifest: `tmp/source_verification/TX/national_batch01_tx_2026-07-16/`
