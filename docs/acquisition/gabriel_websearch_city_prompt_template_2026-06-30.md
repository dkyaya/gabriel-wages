# GABRIEL City Web-Search Extraction Prompt Template

Use this template for a bounded public-source search and extraction pass. Do not use licensed, authenticated, paywalled, blocked, or anti-bot-protected sources. Do not ingest anything during the search pass.

## Inputs

- City: `{city}`
- State: `{state}`
- Priority units: `{priority_units}`
- Known sources or calibration targets: `{known_sources}`
- Search terms: `{search_terms}`
- Maximum retained sources: `{max_sources}`
- Attributes: `{attributes}`

## Search Task

Search for public municipal labor and wage-setting sources for `{city}, {state}`. Prioritize official municipal, school-district, union, and state-agency sources. Retain at most `{max_sources}` source candidates.

Use bounded query themes only:

- police CBA, police contract, police arbitration, JLMC, MOA;
- fire CBA, fire contract, fire arbitration, JLMC, MOA;
- teacher contract, school committee bargaining, union bargaining materials;
- public works, DPW, library, clerical, administrative contracts;
- factfinding, mediation, impasse, arbitration award;
- salary comparison, peer districts, comparable communities, surrounding districts;
- budget presentation, school committee contract presentation, fiscal impact memo.

Do not crawl broadly. Do not bypass access controls. If a result is an index page, classify it as index-only or lead-only unless a specific public source document is directly available.

## Source Classification

For each retained source candidate, return:

- source title;
- source URL;
- source owner;
- source owner type;
- publication or document date if visible;
- retrieval status;
- document type guess;
- unit or occupation guess;
- occupation class guess;
- safety flag guess;
- cycle start and end guess if visible;
- recommended corpus lane: causal, discourse, mechanism_proxy, acquisition_lead_only, or not_corpus;
- source-type recommendation;
- whether it is a causal candidate;
- whether it is a mechanism-proxy candidate;
- whether it is a discourse candidate;
- whether it is lead-only;
- download or ingest recommendation.

## Attribute Extraction

For each retained source, classify these attributes:

1. `comparability_emphasis`

   Does the source compare wages, benefits, compensation, staffing, or salary schedules to peer towns, peer districts, surrounding communities, comparable municipalities, or named comparator jurisdictions?

2. `arbitration_or_impasse_backstop`

   Does the source indicate that contract settlement or wage-setting is shaped by formal impasse-resolution institutions such as JLMC, interest arbitration, stipulated award, factfinding, mediation after impasse, statutory criteria, or successor-contract reopener procedures?

   Do not count routine grievance arbitration, disciplinary arbitration, or contract-administration procedures. Do not count peer-wage comparison alone.

3. `wage_reasoning_density`

   Does the source explain why wages changed, why a settlement is justified, why a proposal is affordable or unaffordable, or why a group needs wage adjustments? Do not count a generic wage schedule as wage reasoning unless the source explains why wages changed.

4. `named_comparator_signal`

   Does the source name specific comparator municipalities, school districts, peer communities, or surrounding districts?

5. `source_ingestability`

   Is the source a clean public final CBA, MOA, arbitration award, factfinding report, or stipulated award that could later enter the causal corpus through the existing pipeline? Or is it only mechanism-proxy, discourse, or lead-only?

## Evidence Rules

- Provide short verbatim excerpts only.
- Do not paste long passages.
- Do not paraphrase excerpts.
- Do not infer named comparator cities unless they are explicitly visible.
- Do not treat ordinary grievance arbitration as arbitration or impasse backstop evidence.
- Do not treat peer-wage comparison alone as arbitration or impasse backstop evidence.
- Do not treat news articles as replacements for primary documents.
- Clearly mark blocked, inaccessible, or index-only sources.

## Output

Return two tables matching:

- `docs/acquisition/gabriel_websearch_mass_city_pilot_sources_2026-06-30.csv`
- `docs/acquisition/gabriel_websearch_mass_city_pilot_extractions_2026-06-30.csv`

Label any output that was generated from known seed sources rather than live web search as design/seed only.
