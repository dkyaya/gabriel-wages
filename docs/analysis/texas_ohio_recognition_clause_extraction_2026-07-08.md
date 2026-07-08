# Texas/Ohio Recognition-Clause Extraction — 2026-07-08

Recognition-clause-first extraction was completed for the three broad non-safety sources. All three remain `occupation_class=other`; no schema expansion is authorized in this run.

## tx_houston_other_2024

- Source file: `corpus/tx_houston/tx_houston_hope_afscme123_meet_confer_2024.pdf`
- Recognition clause found: yes
- Recognition/coverage excerpt: "onary Union Steward. 1.22 Work Schedule Work schedule shall mean the UM’s work schedule listed in the City’s official electronic timekeeping system. 4 Article 2 RECOGNITION; NO STRIKE, NO CALL The City recognizes HOPE as the SEBA on behalf of all Members of the Bargaining Unit. Texas state law prohibits public employees from striking and HOPE, as the SEBA, affirms that it does not advocate illegal strikes by municipal employees, ..."
- Classification/wage schedule found: unclear
- Classification excerpt: ""
- Departments or units covered: clerical/admin; public works/DPW; custodial/facilities; technical/general municipal; health/nurse; library possible but not separately itemized in excerpt; excludes classified police/fire
- Department excerpt: "............................................................................1 1.07 Department ................................................................................................2 1.08 Department Director. .................................................................................. 2 1.09 Department Labor Management Cooperation Council (DLMCC) ...............2 1.10 HOPE .........................................................................................................2 1.11 HOPE Member (Member) ..........................................................................2 1.12 HOPE Representative ................................................................................2 1.13 HOPE’s Executive Board ...........................................................................3 1.14 Human Resources Director (HR Director) ..................................................3 1.15 Labor Management Cooperation Council (LMCC) .............."
- Likely occupation-class interpretation: mixed broad municipal/non-safety unit; do not assign a narrower existing class at this stage.
- Conservative occupation_class to use now: `other`
- Overlap with prior mechanism groups: clerical/admin; public works/DPW; custodial/facilities; technical/general municipal; health/nurse; library possible but not separately itemized in excerpt; excludes classified police/fire
- Unresolved caveat: Recognition is broad and does not support a more precise schema occupation_class without a full classification appendage.

## oh_columbus_other_2024

- Source file: `corpus/oh_columbus/oh_columbus_afscme1632_cba_2024_2027.pdf`
- Recognition clause found: unclear
- Recognition/coverage excerpt: ""
- Classification/wage schedule found: yes
- Classification excerpt: "ion. (5) Immediate supervisor. (6) Union office held. Section 4.2. Bargaining Unit. (A) The bargaining unit means that group of City of Columbus employees meeting the definition of a public employee pursuant to Section 4117.01 of the Ohio Revised Code, serving in class titles included in Appendix A attached hereto, and who are not: 1) uniformed employees of the Police or Fire Divisions within the Department of Public Safety; 2) ..."
- Departments or units covered: clerical/admin; building/zoning; technical/general municipal; dispatcher/public-safety civilian; public works/DPW possible through Appendix A but not isolated here
- Department excerpt: "1 from the Department of Recreation and Parks 1 from the Department of Development 10 1 from the Departments of Finance and Management; and the Offices of the City Auditor, and Treasurer (to be selected from among the employees in these areas) 1 from the Department of Building and Zoning Services 1 from the Departments of Technology, Neighborhoods and City Attorney (to be selected from among the employees in these ..."
- Likely occupation-class interpretation: mixed broad municipal/non-safety unit; do not assign a narrower existing class at this stage.
- Conservative occupation_class to use now: `other`
- Overlap with prior mechanism groups: clerical/admin; building/zoning; technical/general municipal; dispatcher/public-safety civilian; public works/DPW possible through Appendix A but not isolated here
- Unresolved caveat: Recognition points to Appendix A class titles across City functions; keep other unless a later schema/category decision separates mixed municipal units.

## oh_cleveland_other_2022

- Source file: `corpus/oh_cleveland/oh_cleveland_afscme_local100_cba_2022_2025.pdf`
- Recognition clause found: unclear
- Recognition/coverage excerpt: ""
- Classification/wage schedule found: yes
- Classification excerpt: "c Informati on Officer Public Heallh Nursing A ide Publ ic Health Nutritionist Public Health Sanitarian l Publ ic Health Sanitarian 2 Public Hea lth Sanitarian 3 Public Health Sanitarian 4 Quality ASSLll"ance A nalyst Quality Control A nalyst Qua I ity Contro I Coo rd inato1· Rad io Technician 6 Radio Dispatcher Radio Dispatcher - Water Radio Dispatcher - Water Pollt1tion Control Receptionist Recol'ds Manager Recreation Aide Recreation lhstn1cto1· ..."
- Departments or units covered: clerical/admin; public works/utilities; building/facilities; technical/general municipal; public health; dispatcher/public-safety civilian; airport/ARFF-adjacent titles
- Department excerpt: "ADDENDA Page No. Departlnent of Aging ............................................................................................................. 84 Department of Building and Housing ......... .. ... ...... ....... .... .... ............ .................. ... .............. 77 Department of Community Development ............................................................................ 74 Departn1ent of Finance .. ........... .... .. .. ..... .... .. ........ .............. ... ............ .... ............... ...... ........... .98 General Government ............................................. ............ ... .... ....... ........ ...... ... ... ....... ........... 82 Mayor's Office of Capital Projects ..."
- Likely occupation-class interpretation: mixed broad municipal/non-safety unit; do not assign a narrower existing class at this stage.
- Conservative occupation_class to use now: `other`
- Overlap with prior mechanism groups: clerical/admin; public works/utilities; building/facilities; technical/general municipal; public health; dispatcher/public-safety civilian; airport/ARFF-adjacent titles
- Unresolved caveat: Very broad multi-department job-classification list; text includes health, dispatcher, public utilities, building, and administrative titles, so current schema-safe class is other.
