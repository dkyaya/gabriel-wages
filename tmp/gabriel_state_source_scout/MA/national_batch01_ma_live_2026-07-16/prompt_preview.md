# GABRIEL State Source Scout — Prompt Preview

## Somerville, MA (`gabriel_state_source_scout_ma_2026-07-16_183246_ma_somerville`)

```text
Find public URLs for municipal labor source documents for Somerville, MA.

Target employer only: CITY OF SOMERVILLE municipal government, Census government ID 166453.
Search target: ordinary non-safety unit in an overlapping cycle (clerical_admin/public_works/library); comparator or impasse material.
Selection purpose: Repair a safety-only corpus city by locating an overlapping ordinary non-safety agreement; this is also the corpus's strongest current comparator-evidence anchor.
Verification cautions: After scouting, verify exact employer, official/union provenance, 2014-2024 cycle dates, and a safety/non-safety overlap before promotion; scout output remains unverified.
County geography context only (not alternate employers): Middlesex County [25017; county; government-units-primary=yes; basis=2020_place_by_county]

Follow the search target strictly. Sources outside it may appear only as clearly labeled context and do not count as requested candidates.
County governments, school districts, transit authorities, hospital/health districts, regional authorities, special districts, and private EMS/fire providers may not substitute for the target city employer's bargaining unit or wage-setting pathway. They may appear only as clearly labeled context if relevant.

Unit rules: police means sworn police or a police bargaining unit; fire means firefighters or a fire bargaining unit. non_safety means ordinary municipal/civilian employees or authoritative civilian wage-setting material. A police, fire, or other safety CBA can never satisfy a non-safety comparator request. EMS, airport police, transit police, sheriffs, county corrections, school police, hospital-district workers, and private providers are not ordinary non-safety comparators. Use unclear when unit identity is ambiguous; do not force non_safety.

Document rules: distinguish a full CBA; arbitration/factfinding award; memorandum or settlement; wage schedule/compensation plan; ordinance/policy; agenda cover; meeting minutes; context-only source; and dead, unreachable, or insufficient source. A memorandum or settlement is qualifying only when it is executed/binding and contains wage-setting terms. Agenda covers, summaries, meeting memos, and minutes are context-only unless they include or directly attach the full agreement, award, wage schedule, or other binding wage-setting document. Index shells, dead links, and inaccessible pages are insufficient, not qualifying documents.

Find up to 2 candidates for each requested unit or source type. Prefer official city, state labor-board, or union sources.

Return JSON only. No prose.

Return:
{
  "municipality": "...",
  "state": "...",
  "candidates": [
    {
      "unit_type": "police | fire | non_safety | unclear | unknown",
      "document_title": "...",
      "union_name": "...",
      "employer": "...",
      "contract_years": "...",
      "source_url": "...",
      "source_owner_type": "city | state_labor_board | union | third_party | news | unknown",
      "document_type": "cba | arbitration_award | factfinding | memorandum_or_settlement | wage_schedule_or_compensation_plan | ordinance_or_policy | agenda_cover_sheet | meeting_minutes | index_page | context_only | dead_or_unreachable | insufficient_source | unknown",
      "candidate_stage": "qualifying_candidate | context_only_candidate | insufficient_candidate",
      "document_completeness": "full_document | partial_document | summary_only | index_or_landing_page | dead_or_unreachable | unclear",
      "comparator_role": "safety_target | ordinary_non_safety_comparator | authoritative_civilian_wage_setting | mechanism_context | no_comparator_role | unclear",
      "wrong_employer_risk": "none | possible | high",
      "context_only_flag": "yes | no",
      "needs_verification_reason": "...",
      "why_relevant": "...",
      "confidence": "high | medium | low"
    }
  ]
}

Every returned item remains unverified scout-stage lead data and must not be described as verified, ingested, codified, or claim-supporting. Context-only and insufficient leads must be labeled with candidate_stage and context_only_flag; they do not count as qualifying agreements or comparators.
Do not invent URLs. It is acceptable to find no qualifying source for this city; return an empty candidates list when none is found.
```

## Newton, MA (`gabriel_state_source_scout_ma_2026-07-16_183246_ma_newton`)

```text
Find public URLs for municipal labor source documents for Newton, MA.

Target employer only: CITY OF NEWTON municipal government, Census government ID 166452.
Search target: ordinary non-safety unit in an overlapping cycle (clerical_admin/public_works/library).
Selection purpose: Repair a safety-only corpus city by locating an overlapping ordinary non-safety agreement.
Verification cautions: After scouting, verify exact employer, official/union provenance, 2014-2024 cycle dates, and a safety/non-safety overlap before promotion; scout output remains unverified.
County geography context only (not alternate employers): Middlesex County [25017; county; government-units-primary=yes; basis=2020_place_by_county]

Follow the search target strictly. Sources outside it may appear only as clearly labeled context and do not count as requested candidates.
County governments, school districts, transit authorities, hospital/health districts, regional authorities, special districts, and private EMS/fire providers may not substitute for the target city employer's bargaining unit or wage-setting pathway. They may appear only as clearly labeled context if relevant.

Unit rules: police means sworn police or a police bargaining unit; fire means firefighters or a fire bargaining unit. non_safety means ordinary municipal/civilian employees or authoritative civilian wage-setting material. A police, fire, or other safety CBA can never satisfy a non-safety comparator request. EMS, airport police, transit police, sheriffs, county corrections, school police, hospital-district workers, and private providers are not ordinary non-safety comparators. Use unclear when unit identity is ambiguous; do not force non_safety.

Document rules: distinguish a full CBA; arbitration/factfinding award; memorandum or settlement; wage schedule/compensation plan; ordinance/policy; agenda cover; meeting minutes; context-only source; and dead, unreachable, or insufficient source. A memorandum or settlement is qualifying only when it is executed/binding and contains wage-setting terms. Agenda covers, summaries, meeting memos, and minutes are context-only unless they include or directly attach the full agreement, award, wage schedule, or other binding wage-setting document. Index shells, dead links, and inaccessible pages are insufficient, not qualifying documents.

Find up to 2 candidates for each requested unit or source type. Prefer official city, state labor-board, or union sources.

Return JSON only. No prose.

Return:
{
  "municipality": "...",
  "state": "...",
  "candidates": [
    {
      "unit_type": "police | fire | non_safety | unclear | unknown",
      "document_title": "...",
      "union_name": "...",
      "employer": "...",
      "contract_years": "...",
      "source_url": "...",
      "source_owner_type": "city | state_labor_board | union | third_party | news | unknown",
      "document_type": "cba | arbitration_award | factfinding | memorandum_or_settlement | wage_schedule_or_compensation_plan | ordinance_or_policy | agenda_cover_sheet | meeting_minutes | index_page | context_only | dead_or_unreachable | insufficient_source | unknown",
      "candidate_stage": "qualifying_candidate | context_only_candidate | insufficient_candidate",
      "document_completeness": "full_document | partial_document | summary_only | index_or_landing_page | dead_or_unreachable | unclear",
      "comparator_role": "safety_target | ordinary_non_safety_comparator | authoritative_civilian_wage_setting | mechanism_context | no_comparator_role | unclear",
      "wrong_employer_risk": "none | possible | high",
      "context_only_flag": "yes | no",
      "needs_verification_reason": "...",
      "why_relevant": "...",
      "confidence": "high | medium | low"
    }
  ]
}

Every returned item remains unverified scout-stage lead data and must not be described as verified, ingested, codified, or claim-supporting. Context-only and insufficient leads must be labeled with candidate_stage and context_only_flag; they do not count as qualifying agreements or comparators.
Do not invent URLs. It is acceptable to find no qualifying source for this city; return an empty candidates list when none is found.
```

## Boston, MA (`gabriel_state_source_scout_ma_2026-07-16_183246_ma_boston`)

```text
Find public URLs for municipal labor source documents for Boston, MA.

Target employer only: CITY OF BOSTON municipal government, Census government ID 128108.
Search target: fire CBA or impasse/arbitration source overlapping the existing pair.
Selection purpose: Complete the existing matched pair with a fire source, a high-value large-department mechanism test.
Verification cautions: After scouting, verify exact employer, official/union provenance, 2014-2024 cycle dates, and a safety/non-safety overlap before promotion; scout output remains unverified.
County geography context only (not alternate employers): Suffolk County [25025; county; government-units-primary=yes; basis=2020_place_by_county]

Follow the search target strictly. Sources outside it may appear only as clearly labeled context and do not count as requested candidates.
County governments, school districts, transit authorities, hospital/health districts, regional authorities, special districts, and private EMS/fire providers may not substitute for the target city employer's bargaining unit or wage-setting pathway. They may appear only as clearly labeled context if relevant.

Unit rules: police means sworn police or a police bargaining unit; fire means firefighters or a fire bargaining unit. non_safety means ordinary municipal/civilian employees or authoritative civilian wage-setting material. A police, fire, or other safety CBA can never satisfy a non-safety comparator request. EMS, airport police, transit police, sheriffs, county corrections, school police, hospital-district workers, and private providers are not ordinary non-safety comparators. Use unclear when unit identity is ambiguous; do not force non_safety.

Document rules: distinguish a full CBA; arbitration/factfinding award; memorandum or settlement; wage schedule/compensation plan; ordinance/policy; agenda cover; meeting minutes; context-only source; and dead, unreachable, or insufficient source. A memorandum or settlement is qualifying only when it is executed/binding and contains wage-setting terms. Agenda covers, summaries, meeting memos, and minutes are context-only unless they include or directly attach the full agreement, award, wage schedule, or other binding wage-setting document. Index shells, dead links, and inaccessible pages are insufficient, not qualifying documents.

Find up to 2 candidates for each requested unit or source type. Prefer official city, state labor-board, or union sources.

Return JSON only. No prose.

Return:
{
  "municipality": "...",
  "state": "...",
  "candidates": [
    {
      "unit_type": "police | fire | non_safety | unclear | unknown",
      "document_title": "...",
      "union_name": "...",
      "employer": "...",
      "contract_years": "...",
      "source_url": "...",
      "source_owner_type": "city | state_labor_board | union | third_party | news | unknown",
      "document_type": "cba | arbitration_award | factfinding | memorandum_or_settlement | wage_schedule_or_compensation_plan | ordinance_or_policy | agenda_cover_sheet | meeting_minutes | index_page | context_only | dead_or_unreachable | insufficient_source | unknown",
      "candidate_stage": "qualifying_candidate | context_only_candidate | insufficient_candidate",
      "document_completeness": "full_document | partial_document | summary_only | index_or_landing_page | dead_or_unreachable | unclear",
      "comparator_role": "safety_target | ordinary_non_safety_comparator | authoritative_civilian_wage_setting | mechanism_context | no_comparator_role | unclear",
      "wrong_employer_risk": "none | possible | high",
      "context_only_flag": "yes | no",
      "needs_verification_reason": "...",
      "why_relevant": "...",
      "confidence": "high | medium | low"
    }
  ]
}

Every returned item remains unverified scout-stage lead data and must not be described as verified, ingested, codified, or claim-supporting. Context-only and insufficient leads must be labeled with candidate_stage and context_only_flag; they do not count as qualifying agreements or comparators.
Do not invent URLs. It is acceptable to find no qualifying source for this city; return an empty candidates list when none is found.
```

## Worcester, MA (`gabriel_state_source_scout_ma_2026-07-16_183246_ma_worcester`)

```text
Find public URLs for municipal labor source documents for Worcester, MA.

Target employer only: CITY OF WORCESTER municipal government, Census government ID 106079.
Search target: police base CBA in an overlapping cycle; full non-safety base CBA if available.
Selection purpose: Complete the existing fire/non-safety pair with a police leg; favor a base CBA over another amendment-only document.
Verification cautions: After scouting, verify exact employer, official/union provenance, 2014-2024 cycle dates, and a safety/non-safety overlap before promotion; scout output remains unverified.
County geography context only (not alternate employers): Worcester County [25027; county; government-units-primary=yes; basis=2020_place_by_county]

Follow the search target strictly. Sources outside it may appear only as clearly labeled context and do not count as requested candidates.
County governments, school districts, transit authorities, hospital/health districts, regional authorities, special districts, and private EMS/fire providers may not substitute for the target city employer's bargaining unit or wage-setting pathway. They may appear only as clearly labeled context if relevant.

Unit rules: police means sworn police or a police bargaining unit; fire means firefighters or a fire bargaining unit. non_safety means ordinary municipal/civilian employees or authoritative civilian wage-setting material. A police, fire, or other safety CBA can never satisfy a non-safety comparator request. EMS, airport police, transit police, sheriffs, county corrections, school police, hospital-district workers, and private providers are not ordinary non-safety comparators. Use unclear when unit identity is ambiguous; do not force non_safety.

Document rules: distinguish a full CBA; arbitration/factfinding award; memorandum or settlement; wage schedule/compensation plan; ordinance/policy; agenda cover; meeting minutes; context-only source; and dead, unreachable, or insufficient source. A memorandum or settlement is qualifying only when it is executed/binding and contains wage-setting terms. Agenda covers, summaries, meeting memos, and minutes are context-only unless they include or directly attach the full agreement, award, wage schedule, or other binding wage-setting document. Index shells, dead links, and inaccessible pages are insufficient, not qualifying documents.

Find up to 2 candidates for each requested unit or source type. Prefer official city, state labor-board, or union sources.

Return JSON only. No prose.

Return:
{
  "municipality": "...",
  "state": "...",
  "candidates": [
    {
      "unit_type": "police | fire | non_safety | unclear | unknown",
      "document_title": "...",
      "union_name": "...",
      "employer": "...",
      "contract_years": "...",
      "source_url": "...",
      "source_owner_type": "city | state_labor_board | union | third_party | news | unknown",
      "document_type": "cba | arbitration_award | factfinding | memorandum_or_settlement | wage_schedule_or_compensation_plan | ordinance_or_policy | agenda_cover_sheet | meeting_minutes | index_page | context_only | dead_or_unreachable | insufficient_source | unknown",
      "candidate_stage": "qualifying_candidate | context_only_candidate | insufficient_candidate",
      "document_completeness": "full_document | partial_document | summary_only | index_or_landing_page | dead_or_unreachable | unclear",
      "comparator_role": "safety_target | ordinary_non_safety_comparator | authoritative_civilian_wage_setting | mechanism_context | no_comparator_role | unclear",
      "wrong_employer_risk": "none | possible | high",
      "context_only_flag": "yes | no",
      "needs_verification_reason": "...",
      "why_relevant": "...",
      "confidence": "high | medium | low"
    }
  ]
}

Every returned item remains unverified scout-stage lead data and must not be described as verified, ingested, codified, or claim-supporting. Context-only and insufficient leads must be labeled with candidate_stage and context_only_flag; they do not count as qualifying agreements or comparators.
Do not invent URLs. It is acceptable to find no qualifying source for this city; return an empty candidates list when none is found.
```

## Arlington, MA (`gabriel_state_source_scout_ma_2026-07-16_183246_ma_arlington`)

```text
Find public URLs for municipal labor source documents for Arlington, MA.

Target employer only: TOWN OF ARLINGTON municipal government, Census government ID 166519.
Search target: police CBA or formal impasse source overlapping the existing exact-cycle pair.
Selection purpose: Complete the exact-cycle fire/public-works pair with police and test the city's currently symmetric impasse pattern.
Verification cautions: After scouting, verify exact employer, official/union provenance, 2014-2024 cycle dates, and a safety/non-safety overlap before promotion; scout output remains unverified. Confirm the township government—not a same-name city, county, school district, or statistical place—is the employer. Confirm that the government actually has paid public-safety bargaining units; universe inclusion alone does not prove unit availability.
County geography context only (not alternate employers): Middlesex County [25017; county; government-units-primary=yes; basis=2024_county_subdivision_geoid]

Follow the search target strictly. Sources outside it may appear only as clearly labeled context and do not count as requested candidates.
County governments, school districts, transit authorities, hospital/health districts, regional authorities, special districts, and private EMS/fire providers may not substitute for the target city employer's bargaining unit or wage-setting pathway. They may appear only as clearly labeled context if relevant.

Unit rules: police means sworn police or a police bargaining unit; fire means firefighters or a fire bargaining unit. non_safety means ordinary municipal/civilian employees or authoritative civilian wage-setting material. A police, fire, or other safety CBA can never satisfy a non-safety comparator request. EMS, airport police, transit police, sheriffs, county corrections, school police, hospital-district workers, and private providers are not ordinary non-safety comparators. Use unclear when unit identity is ambiguous; do not force non_safety.

Document rules: distinguish a full CBA; arbitration/factfinding award; memorandum or settlement; wage schedule/compensation plan; ordinance/policy; agenda cover; meeting minutes; context-only source; and dead, unreachable, or insufficient source. A memorandum or settlement is qualifying only when it is executed/binding and contains wage-setting terms. Agenda covers, summaries, meeting memos, and minutes are context-only unless they include or directly attach the full agreement, award, wage schedule, or other binding wage-setting document. Index shells, dead links, and inaccessible pages are insufficient, not qualifying documents.

Find up to 2 candidates for each requested unit or source type. Prefer official city, state labor-board, or union sources.

Return JSON only. No prose.

Return:
{
  "municipality": "...",
  "state": "...",
  "candidates": [
    {
      "unit_type": "police | fire | non_safety | unclear | unknown",
      "document_title": "...",
      "union_name": "...",
      "employer": "...",
      "contract_years": "...",
      "source_url": "...",
      "source_owner_type": "city | state_labor_board | union | third_party | news | unknown",
      "document_type": "cba | arbitration_award | factfinding | memorandum_or_settlement | wage_schedule_or_compensation_plan | ordinance_or_policy | agenda_cover_sheet | meeting_minutes | index_page | context_only | dead_or_unreachable | insufficient_source | unknown",
      "candidate_stage": "qualifying_candidate | context_only_candidate | insufficient_candidate",
      "document_completeness": "full_document | partial_document | summary_only | index_or_landing_page | dead_or_unreachable | unclear",
      "comparator_role": "safety_target | ordinary_non_safety_comparator | authoritative_civilian_wage_setting | mechanism_context | no_comparator_role | unclear",
      "wrong_employer_risk": "none | possible | high",
      "context_only_flag": "yes | no",
      "needs_verification_reason": "...",
      "why_relevant": "...",
      "confidence": "high | medium | low"
    }
  ]
}

Every returned item remains unverified scout-stage lead data and must not be described as verified, ingested, codified, or claim-supporting. Context-only and insufficient leads must be labeled with candidate_stage and context_only_flag; they do not count as qualifying agreements or comparators.
Do not invent URLs. It is acceptable to find no qualifying source for this city; return an empty candidates list when none is found.
```

## Georgetown, MA (`gabriel_state_source_scout_ma_2026-07-16_183246_ma_georgetown`)

```text
Find public URLs for municipal labor source documents for Georgetown, MA.

Target employer only: TOWN OF GEORGETOWN municipal government, Census government ID 166487.
Search target: fire agreement or authoritative evidence that no municipal fire bargaining agreement exists.
Selection purpose: Complete the existing matched pair with a fire leg, if a paid or call department has a written agreement.
Verification cautions: After scouting, verify exact employer, official/union provenance, 2014-2024 cycle dates, and a safety/non-safety overlap before promotion; scout output remains unverified. Confirm the township government—not a same-name city, county, school district, or statistical place—is the employer. Confirm that the government actually has paid public-safety bargaining units; universe inclusion alone does not prove unit availability.
County geography context only (not alternate employers): Essex County [25009; county; government-units-primary=yes; basis=2024_county_subdivision_geoid]

Follow the search target strictly. Sources outside it may appear only as clearly labeled context and do not count as requested candidates.
County governments, school districts, transit authorities, hospital/health districts, regional authorities, special districts, and private EMS/fire providers may not substitute for the target city employer's bargaining unit or wage-setting pathway. They may appear only as clearly labeled context if relevant.

Unit rules: police means sworn police or a police bargaining unit; fire means firefighters or a fire bargaining unit. non_safety means ordinary municipal/civilian employees or authoritative civilian wage-setting material. A police, fire, or other safety CBA can never satisfy a non-safety comparator request. EMS, airport police, transit police, sheriffs, county corrections, school police, hospital-district workers, and private providers are not ordinary non-safety comparators. Use unclear when unit identity is ambiguous; do not force non_safety.

Document rules: distinguish a full CBA; arbitration/factfinding award; memorandum or settlement; wage schedule/compensation plan; ordinance/policy; agenda cover; meeting minutes; context-only source; and dead, unreachable, or insufficient source. A memorandum or settlement is qualifying only when it is executed/binding and contains wage-setting terms. Agenda covers, summaries, meeting memos, and minutes are context-only unless they include or directly attach the full agreement, award, wage schedule, or other binding wage-setting document. Index shells, dead links, and inaccessible pages are insufficient, not qualifying documents.

Find up to 2 candidates for each requested unit or source type. Prefer official city, state labor-board, or union sources.

Return JSON only. No prose.

Return:
{
  "municipality": "...",
  "state": "...",
  "candidates": [
    {
      "unit_type": "police | fire | non_safety | unclear | unknown",
      "document_title": "...",
      "union_name": "...",
      "employer": "...",
      "contract_years": "...",
      "source_url": "...",
      "source_owner_type": "city | state_labor_board | union | third_party | news | unknown",
      "document_type": "cba | arbitration_award | factfinding | memorandum_or_settlement | wage_schedule_or_compensation_plan | ordinance_or_policy | agenda_cover_sheet | meeting_minutes | index_page | context_only | dead_or_unreachable | insufficient_source | unknown",
      "candidate_stage": "qualifying_candidate | context_only_candidate | insufficient_candidate",
      "document_completeness": "full_document | partial_document | summary_only | index_or_landing_page | dead_or_unreachable | unclear",
      "comparator_role": "safety_target | ordinary_non_safety_comparator | authoritative_civilian_wage_setting | mechanism_context | no_comparator_role | unclear",
      "wrong_employer_risk": "none | possible | high",
      "context_only_flag": "yes | no",
      "needs_verification_reason": "...",
      "why_relevant": "...",
      "confidence": "high | medium | low"
    }
  ]
}

Every returned item remains unverified scout-stage lead data and must not be described as verified, ingested, codified, or claim-supporting. Context-only and insufficient leads must be labeled with candidate_stage and context_only_flag; they do not count as qualifying agreements or comparators.
Do not invent URLs. It is acceptable to find no qualifying source for this city; return an empty candidates list when none is found.
```

## Franklin, MA (`gabriel_state_source_scout_ma_2026-07-16_183246_ma_franklin`)

```text
Find public URLs for municipal labor source documents for Franklin, MA.

Target employer only: CITY OF FRANKLIN TOWN municipal government, Census government ID 194918.
Search target: police; fire; at least one ordinary general-municipal non-safety unit (clerical_admin/public_works/sanitation/library); public impasse/arbitration/factfinding material when available; prioritize a repeat cycle for the already represented units.
Cycle evidence emphasis: identify contract years for every candidate and prioritize repeat-cycle sources plus public impasse/arbitration/factfinding evidence.
Selection purpose: Add a repeat cycle for the existing Franklin matched-design anchor instead of accumulating a new safety-only city.
Verification cautions: After scouting, verify exact employer, official/union provenance, 2014-2024 cycle dates, and a safety/non-safety overlap before promotion; scout output remains unverified. Confirm that the government actually has paid public-safety bargaining units; universe inclusion alone does not prove unit availability.
County geography context only (not alternate employers): Norfolk County [25021; county; government-units-primary=yes; basis=2020_place_by_county]

Follow the search target strictly. Sources outside it may appear only as clearly labeled context and do not count as requested candidates.
County governments, school districts, transit authorities, hospital/health districts, regional authorities, special districts, and private EMS/fire providers may not substitute for the target city employer's bargaining unit or wage-setting pathway. They may appear only as clearly labeled context if relevant.

Unit rules: police means sworn police or a police bargaining unit; fire means firefighters or a fire bargaining unit. non_safety means ordinary municipal/civilian employees or authoritative civilian wage-setting material. A police, fire, or other safety CBA can never satisfy a non-safety comparator request. EMS, airport police, transit police, sheriffs, county corrections, school police, hospital-district workers, and private providers are not ordinary non-safety comparators. Use unclear when unit identity is ambiguous; do not force non_safety.

Document rules: distinguish a full CBA; arbitration/factfinding award; memorandum or settlement; wage schedule/compensation plan; ordinance/policy; agenda cover; meeting minutes; context-only source; and dead, unreachable, or insufficient source. A memorandum or settlement is qualifying only when it is executed/binding and contains wage-setting terms. Agenda covers, summaries, meeting memos, and minutes are context-only unless they include or directly attach the full agreement, award, wage schedule, or other binding wage-setting document. Index shells, dead links, and inaccessible pages are insufficient, not qualifying documents.

Find up to 2 candidates for each requested unit or source type. Prefer official city, state labor-board, or union sources.

Return JSON only. No prose.

Return:
{
  "municipality": "...",
  "state": "...",
  "candidates": [
    {
      "unit_type": "police | fire | non_safety | unclear | unknown",
      "document_title": "...",
      "union_name": "...",
      "employer": "...",
      "contract_years": "...",
      "source_url": "...",
      "source_owner_type": "city | state_labor_board | union | third_party | news | unknown",
      "document_type": "cba | arbitration_award | factfinding | memorandum_or_settlement | wage_schedule_or_compensation_plan | ordinance_or_policy | agenda_cover_sheet | meeting_minutes | index_page | context_only | dead_or_unreachable | insufficient_source | unknown",
      "candidate_stage": "qualifying_candidate | context_only_candidate | insufficient_candidate",
      "document_completeness": "full_document | partial_document | summary_only | index_or_landing_page | dead_or_unreachable | unclear",
      "comparator_role": "safety_target | ordinary_non_safety_comparator | authoritative_civilian_wage_setting | mechanism_context | no_comparator_role | unclear",
      "wrong_employer_risk": "none | possible | high",
      "context_only_flag": "yes | no",
      "needs_verification_reason": "...",
      "why_relevant": "...",
      "confidence": "high | medium | low"
    }
  ]
}

Every returned item remains unverified scout-stage lead data and must not be described as verified, ingested, codified, or claim-supporting. Context-only and insufficient leads must be labeled with candidate_stage and context_only_flag; they do not count as qualifying agreements or comparators.
Do not invent URLs. It is acceptable to find no qualifying source for this city; return an empty candidates list when none is found.
```

## Seekonk, MA (`gabriel_state_source_scout_ma_2026-07-16_183246_ma_seekonk`)

```text
Find public URLs for municipal labor source documents for Seekonk, MA.

Target employer only: TOWN OF SEEKONK municipal government, Census government ID 166481.
Search target: police; fire; at least one ordinary general-municipal non-safety unit (clerical_admin/public_works/sanitation/library); public impasse/arbitration/factfinding material when available; prioritize a repeat cycle for the already represented units.
Cycle evidence emphasis: identify contract years for every candidate and prioritize repeat-cycle sources plus public impasse/arbitration/factfinding evidence.
Selection purpose: Add a repeat cycle for the existing Seekonk matched-design anchor instead of accumulating a new safety-only city.
Verification cautions: After scouting, verify exact employer, official/union provenance, 2014-2024 cycle dates, and a safety/non-safety overlap before promotion; scout output remains unverified. Confirm the township government—not a same-name city, county, school district, or statistical place—is the employer. Confirm that the government actually has paid public-safety bargaining units; universe inclusion alone does not prove unit availability.
County geography context only (not alternate employers): Bristol County [25005; county; government-units-primary=yes; basis=2024_county_subdivision_geoid]

Follow the search target strictly. Sources outside it may appear only as clearly labeled context and do not count as requested candidates.
County governments, school districts, transit authorities, hospital/health districts, regional authorities, special districts, and private EMS/fire providers may not substitute for the target city employer's bargaining unit or wage-setting pathway. They may appear only as clearly labeled context if relevant.

Unit rules: police means sworn police or a police bargaining unit; fire means firefighters or a fire bargaining unit. non_safety means ordinary municipal/civilian employees or authoritative civilian wage-setting material. A police, fire, or other safety CBA can never satisfy a non-safety comparator request. EMS, airport police, transit police, sheriffs, county corrections, school police, hospital-district workers, and private providers are not ordinary non-safety comparators. Use unclear when unit identity is ambiguous; do not force non_safety.

Document rules: distinguish a full CBA; arbitration/factfinding award; memorandum or settlement; wage schedule/compensation plan; ordinance/policy; agenda cover; meeting minutes; context-only source; and dead, unreachable, or insufficient source. A memorandum or settlement is qualifying only when it is executed/binding and contains wage-setting terms. Agenda covers, summaries, meeting memos, and minutes are context-only unless they include or directly attach the full agreement, award, wage schedule, or other binding wage-setting document. Index shells, dead links, and inaccessible pages are insufficient, not qualifying documents.

Find up to 2 candidates for each requested unit or source type. Prefer official city, state labor-board, or union sources.

Return JSON only. No prose.

Return:
{
  "municipality": "...",
  "state": "...",
  "candidates": [
    {
      "unit_type": "police | fire | non_safety | unclear | unknown",
      "document_title": "...",
      "union_name": "...",
      "employer": "...",
      "contract_years": "...",
      "source_url": "...",
      "source_owner_type": "city | state_labor_board | union | third_party | news | unknown",
      "document_type": "cba | arbitration_award | factfinding | memorandum_or_settlement | wage_schedule_or_compensation_plan | ordinance_or_policy | agenda_cover_sheet | meeting_minutes | index_page | context_only | dead_or_unreachable | insufficient_source | unknown",
      "candidate_stage": "qualifying_candidate | context_only_candidate | insufficient_candidate",
      "document_completeness": "full_document | partial_document | summary_only | index_or_landing_page | dead_or_unreachable | unclear",
      "comparator_role": "safety_target | ordinary_non_safety_comparator | authoritative_civilian_wage_setting | mechanism_context | no_comparator_role | unclear",
      "wrong_employer_risk": "none | possible | high",
      "context_only_flag": "yes | no",
      "needs_verification_reason": "...",
      "why_relevant": "...",
      "confidence": "high | medium | low"
    }
  ]
}

Every returned item remains unverified scout-stage lead data and must not be described as verified, ingested, codified, or claim-supporting. Context-only and insufficient leads must be labeled with candidate_stage and context_only_flag; they do not count as qualifying agreements or comparators.
Do not invent URLs. It is acceptable to find no qualifying source for this city; return an empty candidates list when none is found.
```
