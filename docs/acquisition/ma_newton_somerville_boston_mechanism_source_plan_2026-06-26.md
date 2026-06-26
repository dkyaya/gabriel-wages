# Newton, Somerville, and Boston Mechanism-Source Plan
Date: 2026-06-26
Status: Planning input for Codex acquisition/recon run

This document is a planning note for the next bounded public-only mechanism-source pass. It should be read before creating the city-specific recon memos and combined mechanism-source queue.

Expected Codex outputs:
- docs/acquisition/ma_newton_mechanism_source_recon_2026-06-25.md
- docs/acquisition/ma_somerville_mechanism_source_recon_2026-06-25.md
- docs/acquisition/ma_boston_mechanism_source_recon_2026-06-25.md
- docs/acquisition/ma_mechanism_source_queue_2026-06-25.csv

Newton Mechanism-Source Recon Plan

Purpose

Newton is a high-priority mechanism-search target because the current corpus contains an unmatched Newton police row, while Newton Public Schools and the Newton Teachers Association expose unusually rich public materials around the 2023-2024 teacher negotiations. The purpose of this pass is not merely to find more contracts. The goal is to find public documents that explain wage reasoning, bargaining positions, salary comparisons, settlement logic, or fiscal justifications.

This memo should guide a bounded Codex acquisition pass. Documents should be classified before ingestion. Final signed agreements may be causal-corpus candidates. Bargaining updates, presentations, public statements, meeting materials, and settlement summaries are more likely mechanism-proxy or discourse candidates.

Research value

Newton is useful for three reasons:

1. It has an existing safety-side gap in the corpus: ma_newton_police_2015.
2. It has a public 2023-2024 school bargaining episode that produced extensive public documents.
3. It may reveal whether non-safety school-side bargaining uses peer-district comparison, general fiscal capacity arguments, staffing/workload arguments, or other non-police/fire wage rationales.

Priority source routes

Priority	Source route	Source type	Why it matters
P1	https://www.newteach.org/copy-of-negotiations-team	Newton Teachers Association bargaining/negotiations updates	Richest visible route for bargaining proposals, counterproposals, mediation updates, and settlement documents
P1	https://www.newton.k12.ma.us/human-resources/collective-bargaining-agreements	Newton Public Schools collective bargaining agreements	Official district route for final contracts and salary schedules
P1	https://www.newton.k12.ma.us/sc-meetings	Newton School Committee meeting materials	Official route for school committee materials and public meeting packet leads
P2	https://www.newteach.org/contracts	Newton Teachers Association contracts page	Union-side route for final contracts, salary schedules, and settlement summaries
P2	Fig City News Newton NTA/NPS negotiation coverage	Public reporting and document leads	Useful only as a lead or discourse candidate, not as causal contract evidence unless it links to primary materials
P3	WBUR / local news Newton strike coverage	Public narrative/discourse	Useful for context, but secondary to official or union documents

Target search terms

Use targeted page/PDF search only. Do not broad crawl.

Search within Newton pages and PDFs for:

* comparable
* comparison
* peer districts
* peer communities
* market
* salary
* wage
* compensation
* settlement
* fiscal impact
* contract cost
* mediation
* factfinding
* proposal
* counterproposal
* memorandum of agreement
* school committee update
* negotiations update

High-value target documents

Candidate	Expected document type	Likely corpus destination	Priority	Notes
NTA 2023-2024 bargaining proposals and counterproposals	Bargaining proposal / counterproposal	mechanism_proxy or discourse_candidate	P1	Look for salary rationale, district comparisons, or wage tables
School Committee outline/proposals for mediation	Bargaining proposal / mediation document	mechanism_proxy or discourse_candidate	P1	High value if it explains the school committee’s wage position
February 2024 Memorandum of Agreement between NTA and School Committee	MOA/final settlement	causal_candidate if full final agreement; otherwise mechanism_proxy	P1	May be a clean non-safety causal row if not already in corpus
NTA strike victory summary / plain-language settlement summary	Union-side settlement summary	discourse_candidate or mechanism_proxy	P2	Useful if it explains wage wins or comparisons
School Committee meeting packet around July 2023 to February 2024	Public meeting packet	mechanism_proxy or acquisition_lead_only	P2	Useful only if packet includes wage exhibits or bargaining explanations
Newton Public Schools final Unit A/B/C/D/E contracts 2024-2027	CBA	causal_candidate	P2	Useful for later non-safety corpus expansion, but not necessarily mechanism-rich
NESA administrative assistant/secretary MOA or agreement	MOA/CBA	causal_candidate	P2	Possible non-safety clerical/admin comparator

Evidence classification

Use this classification before ingestion:

Evidence level	Definition	Action
High	Contains peer-district, peer-community, market salary, or wage-comparison exhibit	Stage and document as high-priority mechanism evidence
Medium	Explains wage settlement, fiscal cost, step movement, or compensation package without external comparables	Stage if public and manageable; document as wage-rationale evidence
Low	Final agreement with wage schedules but little reasoning	Ingest only if needed as a causal row; otherwise document
None	Agenda notice, executive-session item, or news article without primary materials	Do not ingest; record as lead only if useful

Likely corpus handling

* Final signed collective bargaining agreements, memoranda of agreement, or official salary schedules may be causal_candidate.
* Bargaining updates, proposals, counterproposals, summaries, public statements, and school committee presentations should be treated as mechanism_proxy or discourse_candidate.
* Meeting agendas and executive-session notices should usually be not_corpus.
* News stories should not replace primary documents, but they can point to public documents.

Stop rules

Stop Newton search when any of the following occurs:

1. Ten useful-looking Newton source documents have been reviewed.
2. Five consecutive materials are agenda-only or executive-session-only.
3. A document route requires login, public-records request, or blocked access.
4. The same documents repeat across NPS, NTA, and news sources.
5. Codex has enough high-priority Newton documents to stage and classify.

Recommended Newton outputs

Create or update a mechanism-source queue with:

* document title
* source URL
* source owner
* date
* unit
* document type
* public access status
* wage reasoning signal
* comparability signal
* likely corpus destination
* recommended next action

Preliminary expectation

Newton is likely the best first test of whether public school bargaining materials contain mechanism evidence. It may not produce a clean peer-community comparability exhibit, but it is likely to produce wage-rationale materials. If Newton has no explicit comparability evidence despite rich public negotiations materials, that is substantively useful: it suggests non-safety bargaining may be visible but framed around fiscal capacity, staffing, workload, and settlement cost rather than peer-community wage comparisons.

⸻

Somerville Mechanism-Source Recon Plan

Purpose

Somerville is the highest-value mechanism-search case because the v9 GABRIEL signal is driven heavily by Somerville police arbitration awards. The key empirical question is whether public non-safety Somerville materials show similar comparability reasoning, different reasoning, or little public reasoning at all.

This pass should look for Somerville educator, school committee, municipal, and union materials that explain wage bargaining or contract settlement logic. The goal is not broad contract expansion. The goal is to compare the safety-side award reasoning against non-safety public bargaining materials.

Research value

Somerville is useful for four reasons:

1. Somerville police arbitration awards are the strongest current evidence for explicit peer-community comparability.
2. Current safety-side rows remain unmatched in the audit.
3. Somerville educator materials are publicly visible through union and school committee routes.
4. A non-safety Somerville bargaining packet, presentation, or settlement memo would be highly valuable even if it belongs in a proxy/discourse queue rather than the causal corpus.

Priority source routes

Priority	Source route	Source type	Why it matters
P1	https://sites.google.com/somervilleeducators.com/somerville-educators-union/member-resources/contracts	Somerville Educators Union contracts	Public union route for educator contracts by unit
P1	https://somerville.k12.ma.us/district-leadership/somerville-school-committee	Somerville School Committee page	Official route for school committee governance and materials
P1	https://somerville.k12.ma.us/district-leadership/somerville-school-committee/school-committee-meetings	School Committee meeting route	Official meeting/materials route, directs to city events calendar
P2	https://sites.google.com/somervilleeducators.com/somerville-educators-union/seu	Somerville Educators Union public page	Public union narrative and press-release route
P2	https://sites.google.com/somervilleeducators.com/somerville-educators-union/board-meetings/minutes	SEU minutes route	May contain union-side meeting references; likely lower evidentiary value
P2	Somerville Times 2022 and 2025 contract coverage	Public reporting	Useful for leads and discourse context, not as a primary causal document
P3	MTA contract highlights mentioning Somerville	Public union-sector context	Useful as context, not a primary city document

Target search terms

Search targeted pages and PDFs for:

* comparable
* comparison
* peer
* salary
* wage
* compensation
* paraprofessional
* starting salary
* market
* bargaining
* contract campaign
* ratified
* settlement
* school committee vote
* fiscal impact
* equity-focused paid parental leave
* workload
* staffing
* special education
* class size

High-value target documents

Candidate	Expected document type	Likely corpus destination	Priority	Notes
SEU Unit A / Unit C contracts or MOAs, 2022-2025 and 2025-2028	CBA/MOA	causal_candidate	P1	Useful for non-safety Somerville rows if clean and public
SEU press release or contract campaign materials	Public bargaining narrative	discourse_candidate or mechanism_proxy	P1	Useful if it explains wage gains and bargaining rationale
School Committee packet for 2022 SEU ratification vote	Meeting packet / presentation	mechanism_proxy	P1	High value if it contains settlement cost or wage rationale
School Committee packet for 2025 SEU ratification vote	Meeting packet / presentation	mechanism_proxy	P1	May contain recent wage rationale, though outside police-award cycle
Somerville Times contract coverage	News/discourse	discourse_candidate or acquisition_lead_only	P2	Use only as lead/context unless primary docs are linked
SEU board minutes	Union minutes	acquisition_lead_only	P3	Likely too thin; use only if they point to public attachments

Evidence classification

Evidence level	Definition	Action
High	Mentions peer communities, salary comparisons, market comparability, or external wage benchmarks	Stage and document as high-priority mechanism evidence
Medium	Explains wage settlement through equity, retention, staffing, workload, or fiscal rationale	Stage as mechanism-proxy evidence if public and manageable
Low	Signed CBA with wage schedule but little reasoning	Ingest only if useful as causal row; otherwise document
None	Meeting notice, agenda item, generic minutes, or press coverage without linked primary materials	Record as lead only

Likely corpus handling

* Final SEU collective bargaining agreements or memoranda of agreement may be causal-corpus candidates.
* School committee presentations, contract campaign materials, and public bargaining narratives are more likely discourse/proxy evidence.
* Somerville Times or Cambridge Day articles can be used as leads and context, but should not substitute for primary documents.
* If a document is hosted on Google Drive, Codex should not assume stable download unless it can fetch the actual public file cleanly.

Stop rules

Stop Somerville search when:

1. Ten useful-looking materials have been reviewed.
2. Five consecutive documents are agenda-only, minutes-only, or press-only without primary attachments.
3. Google Drive or city event routes block direct access.
4. No document contains wage rationale beyond final wage schedules.
5. Codex has enough material to classify Somerville as high, medium, or low public-mechanism potential.

Recommended Somerville outputs

Create or update a mechanism-source queue with:

* document title
* source URL
* source owner
* date
* unit
* document type
* public access status
* wage reasoning signal
* comparability signal
* likely corpus destination
* recommended next action

Preliminary expectation

Somerville may produce useful non-safety wage-rationale material, but it may not produce peer-community comparability evidence as explicit as the police arbitration awards. If the best Somerville non-safety materials emphasize staffing, equity, paraprofessional minimums, special education workload, class size, or parental leave, that contrast is still substantively useful. It would suggest that safety arbitration awards expose a different kind of reasoning than educator settlement materials.

⸻

Boston Mechanism-Source Recon Plan

Purpose

Boston is a complex but potentially rich mechanism-search target. The current corpus already includes Boston safety and clerical/admin material, but Boston’s public school and city labor sources may contain stronger bargaining narratives, settlement presentations, fiscal-impact materials, and wage-rationale documents.

The goal is to find public documents that explain wage reasoning, not simply to ingest another Boston contract. Boston should be treated as a fragmented, multi-employer case: Boston Public Schools materials may not map neatly onto city-side municipal units, but they can help test whether non-safety bargaining materials use peer-comparison language.

Research value

Boston is useful for four reasons:

1. It is a large municipality with public labor-relations materials.
2. Boston Public Schools has a public Boston Teachers Union negotiation page and School Committee presentation materials.
3. Boston Teachers Union pages expose contract, bargaining-update, and summary documents.
4. Boston may reveal whether non-safety public bargaining is framed around peer comparability, equity, low-paid worker adjustments, staffing, inclusion, or fiscal capacity.

Priority source routes

Priority	Source route	Source type	Why it matters
P1	https://www.bostonpublicschools.org/school-committee/btu-contract-negotiations	BPS BTU contract negotiations page	Official public route for Boston Teachers Union agreement materials
P1	https://resources.finalsite.net/images/v1744817505/bostonpublicschoolsorg/xur4pktuwowr7kgoeiow/FINALApril162025BTUCBAPresentation.pdf	BPS April 2025 School Committee presentation	High-value official presentation explaining the BTU agreement
P1	https://btu.org/contract-bargaining-updates/	BTU bargaining updates	Union-side bargaining narrative and summaries
P1	https://btu.org/contracts/	BTU contracts page	Public route for contracts, summaries, and wage documents
P2	https://ohr.bostonpublicschools.org/careers1/salary-grids-cbas	BPS salary grids and CBAs	Official BPS salary/CBA route for multiple units
P2	Boston City Council / Legistar collective bargaining docket materials	City fiscal approvals	Useful for fiscal-impact documents and appropriations
P2	Boston Municipal Research Bureau BTU contract analysis	Public fiscal analysis	Useful as discourse/proxy context, not causal evidence
P3	Local reporting on BTU negotiations	News/discourse	Use as context or lead only

Target search terms

Search targeted pages and PDFs for:

* comparable
* comparison
* peer
* market
* salary
* wage
* compensation
* lowest-paid workers
* paraprofessionals
* market rate adjustment
* fiscal impact
* supplemental appropriation
* collective bargaining reserve
* contract cost
* inclusion
* staffing
* retention
* bargaining summary
* tentative agreement
* memorandum of agreement

High-value target documents

Candidate	Expected document type	Likely corpus destination	Priority	Notes
April 2025 BTU Collective Bargaining Agreement School Committee presentation	Official presentation	mechanism_proxy or discourse_candidate	P1	High-value explanation of contract terms and rationale
BTU 2024-2027 Memorandum of Agreement	MOA	causal_candidate	P1	Potential causal row if not already included
BTU plain-language summary / one-page summary / FAQ	Settlement summary	mechanism_proxy or discourse_candidate	P1	Useful if it explains wage structure or lowest-paid worker adjustments
BTU bargaining updates archive	Union bargaining updates	discourse_candidate or mechanism_proxy	P1	Useful if updates explain wage demands, city response, or settlement logic
BPS salary grids and CBAs for paraprofessionals, administrative, cafeteria, custodial, or other units	CBA/salary grid	causal_candidate or acquisition_lead_only	P2	Useful for non-safety comparator expansion
City Council supplemental appropriation materials for BTU agreement	Fiscal approval document	mechanism_proxy or discourse_candidate	P2	Useful if it quantifies wage costs and fiscal rationale
Boston Municipal Research Bureau BTU contract analysis	Public policy/fiscal analysis	discourse_candidate	P2	Useful for high-level fiscal interpretation, not a primary bargaining document

Evidence classification

Evidence level	Definition	Action
High	Contains explicit market, peer, comparable city/district, or salary comparison logic	Stage and document as high-priority mechanism evidence
Medium	Explains wage increases through equity, lowest-paid workers, staffing, retention, fiscal cost, or implementation needs	Stage as mechanism-proxy evidence
Low	Final contract or MOA with wage schedules but little reasoning	Ingest only if useful as causal row
None	Agenda-only, news-only, or video-only source without usable text/materials	Record as lead only

Likely corpus handling

* Final Boston Teachers Union Memorandum of Agreement or Collective Bargaining Agreement may be causal-corpus candidates.
* Official School Committee presentations, BTU summaries, bargaining updates, fiscal memoranda, and municipal research documents are likely mechanism-proxy or discourse candidates.
* Salary grids can support wage context but should not be treated as mechanism evidence by themselves.
* News stories should not replace official or union documents, but they can point to public documents.

Stop rules

Stop Boston search when:

1. Ten useful-looking documents have been reviewed.
2. Five consecutive routes provide only news coverage, agenda notices, or duplicate summaries.
3. The route requires login, public-records request, or blocked access.
4. Materials focus only on non-wage educational policy and contain no wage/fiscal rationale.
5. Codex has enough material to classify Boston as high, medium, or low public-mechanism potential.

Recommended Boston outputs

Create or update a mechanism-source queue with:

* document title
* source URL
* source owner
* date
* unit
* document type
* public access status
* wage reasoning signal
* comparability signal
* likely corpus destination
* recommended next action

Preliminary expectation

Boston is likely to produce useful wage-rationale and fiscal-impact materials, but not necessarily peer-community comparability evidence. The most likely themes are lowest-paid worker adjustments, paraprofessional wages, inclusion staffing, contract cost, and budget implementation. That is still valuable: if Boston non-safety/teacher materials use equity/fiscal/staffing logic rather than peer-comparability logic, that contrast helps sharpen the mechanism story.
