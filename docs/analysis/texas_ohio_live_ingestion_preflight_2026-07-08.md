# Texas/Ohio Live Ingestion Preflight — 2026-07-08

This preflight parses the committed dry-run CSV and selects only rows authorized for this controlled live source acquisition run. It performs no downloads, ingestion, metadata edits, GABRIEL calls, Harvard Proxy calls, or model/API calls.

## CSV Parse And Scope Checks

- Input CSV: `docs/analysis/texas_ohio_acquisition_dry_run_2026-07-08.csv`
- Parsed rows: 20
- Required-column check: passed
- Controlled-value check: passed
- Selector: `dry_run_status=ready_for_live_fetch`, `approval_status=approved_first_batch`, `store_now=no`, `ingest_now=no`
- Selected rows: 9
- Expected selected rows: 9
- Selection count check: passed
- Selected-row URL/filename completeness: passed
- Selected-row fetch safety check: passed

## Dry-Run Status Counts

| dry_run_status | rows |
| --- | ---: |
| context_only | 6 |
| needs_url_confirmation | 5 |
| ready_for_live_fetch | 9 |

## Selected Rows

| state | city | source_role | source_target | proposed_contract_id | proposed_filename | source URL / lookup path |
| --- | --- | --- | --- | --- | --- | --- |
| TX | Houston | police | Houston Police Officers' Union (HPOU) Meet & Confer Agreement | tx_houston_police_2024 (tentative -- confirm current contract-year coverage of this specific URL) | `corpus/tx_houston/tx_houston_hpou_police_meet_confer_2024.pdf` | https://www.houstontx.gov/hr/hrfiles/classified_testing/agreement_meet_conf.pdf |
| TX | Houston | non_safety_general | HOPE/AFSCME Local 123 meet-and-confer agreement (2024) | tx_houston_other_2024 (tentative -- occupation_class pending PI schema decision; see proposed_occupation_class note) | `corpus/tx_houston/tx_houston_hope_afscme123_meet_confer_2024.pdf` | https://www.houstontx.gov/hr/hrfiles/employee_relations/hope_meet_cof_agrmnt.pdf |
| TX | Austin | police | Austin Police Association meet-and-confer agreement (2024-2029) | tx_austin_police_2024 | `corpus/tx_austin/tx_austin_apa_police_meet_confer_2024_2029.pdf` | https://www.austintexas.gov/labor-relations/police-meet-and-confer-agreement |
| OH | Columbus | police | Fraternal Order of Police Capital City Lodge No. 9 collective bargaining agreement (2023-2026) | oh_columbus_police_2023 | `corpus/oh_columbus/oh_columbus_fop_lodge9_police_cba_2023_2026.pdf` | https://www.columbus.gov/files/sharedassets/city/v/1/human-resources/labor-relations/fop-cba-2023-2026.pdf |
| OH | Columbus | fire | IAFF Local 67 collective bargaining agreement (2023-2026) | oh_columbus_fire_2023 | `corpus/oh_columbus/oh_columbus_iaff67_fire_cba_2023_2026.pdf` | https://www.columbus.gov/files/sharedassets/city/v/2/human-resources/labor-relations/iaff-cba-2023-2026.pdf |
| OH | Columbus | non_safety_general | AFSCME Local 1632 collective bargaining agreement (2024-2027) | oh_columbus_other_2024 (occupation_class pending recognition-clause read) | `corpus/oh_columbus/oh_columbus_afscme1632_cba_2024_2027.pdf` | https://www.columbus.gov/files/sharedassets/city/v/1/human-resources/labor-relations/afscme-1632-cba-2024-2027.pdf |
| OH | Cleveland | police | Cleveland Police Patrolmen's Association (CPPA) collective bargaining agreement (2025-2028) | oh_cleveland_police_2025 | `corpus/oh_cleveland/oh_cleveland_cppa_patrol_police_cba_2025_2028.pdf` | https://www.clevelandohio.gov/sites/clevelandohio/files/hr/cba/2025-2028%20CPPA%20Patrol%20Officers%20CBA.pdf |
| OH | Cleveland | fire | Cleveland Firefighters IAFF Local 93 collective bargaining agreement (2025-2028) | oh_cleveland_fire_2025 | `corpus/oh_cleveland/oh_cleveland_iaff93_fire_cba_2025_2028.pdf` | https://www.clevelandohio.gov/sites/clevelandohio/files/hr/cba/2025-2028%20Cleveland%20Firefighters%2C%20Local%2093%20CBA.pdf |
| OH | Cleveland | non_safety_general | AFSCME Ohio Council 8 Local 100 collective bargaining agreement (2022-2025) | oh_cleveland_other_2022 (occupation_class pending recognition-clause read) | `corpus/oh_cleveland/oh_cleveland_afscme_local100_cba_2022_2025.pdf` | https://www.clevelandohio.gov/sites/clevelandohio/files/hr/cba/2022-2025%20Local%20100%2C%20AFSCME%20Ohio%20Council%208.pdf |

## Held-Out Rows

| state | city | source_role | source_target | dry_run_status | reason held out |
| --- | --- | --- | --- | --- | --- |
| TX | Houston | fire | HPFFA/IAFF Local 341 collective bargaining agreement (2024-2029) | needs_url_confirmation | dry_run_status=needs_url_confirmation |
| TX | Houston | budget_pay_plan | City of Houston civil-service classification and compensation pages / Municipal Employee Guidebook | context_only | dry_run_status=context_only |
| TX | Austin | fire | Austin Firefighters Association Local 975 collective bargaining agreement (2023-2025 + proposed Oct.2025 successor) | needs_url_confirmation | dry_run_status=needs_url_confirmation |
| TX | Austin | budget_pay_plan | City of Austin civil-service classification/compensation pages (specific URL not yet confirmed) | needs_url_confirmation | dry_run_status=needs_url_confirmation |
| OH | Columbus | budget_pay_plan | Health Administrative Compensation Plan (HACP) | context_only | dry_run_status=context_only |
| OH | Cleveland | budget_pay_plan | City of Cleveland budget/pay-plan documentation (specific URL not yet located) | needs_url_confirmation | dry_run_status=needs_url_confirmation |
| TX | statewide | legal_institutional | Texas Local Government Code Chapter 174 (Fire and Police Employee Relations Act) | context_only | dry_run_status=context_only; approval_status=context_only |
| TX | statewide | legal_institutional | Texas Local Government Code Chapter 146 (Local Control of Municipal Employment Matters in Certain Municipalities) | context_only | dry_run_status=context_only; approval_status=context_only |
| TX | statewide | legal_institutional | Texas Local Government Code Chapter 142 (meet-and-confer for police/fire) and Texas Government Code Chapter 617 (general bargaining prohibition) | context_only | dry_run_status=context_only; approval_status=context_only |
| OH | statewide | legal_institutional | Ohio Revised Code Chapter 4117 (Public Employees' Collective Bargaining) | context_only | dry_run_status=context_only; approval_status=context_only |
| OH | statewide | source_discovery | Ohio SERB document archive (fact-finding reports and conciliation awards since 2012) | needs_url_confirmation | dry_run_status=needs_url_confirmation; approval_status=context_only |

## Unsafe Or Vague Selected Rows

None. All nine selected rows have concrete source targets, source URLs or lookup paths, safe unique corpus filenames, and dry-run status `ready_for_live_fetch`.

## Preflight Decision

Proceed to controlled live fetch for exactly the nine selected rows. All other Texas/Ohio rows remain held out for URL confirmation, context-only use, backup treatment, or deferral.
