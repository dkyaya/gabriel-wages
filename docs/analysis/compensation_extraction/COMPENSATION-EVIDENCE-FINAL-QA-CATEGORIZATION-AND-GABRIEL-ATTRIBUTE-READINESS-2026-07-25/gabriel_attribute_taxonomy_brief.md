# GABRIEL compensation attribute taxonomy

Use multi-label classification against the exact supplied evidence span. A true label means the literal span supports the short definition; it does not imply wage effects or causality.

- `cola_or_cpi` — Pay is tied to CPI, COLA, inflation, or a cost-of-living adjustment.
- `step_or_seniority` — Pay changes by step, seniority, service time, or progression schedule.
- `rank_or_classification` — Pay differs by rank, title, classification, grade, or job class.
- `across_the_board_raise` — Pay increases apply broadly across employees or a bargaining unit.
- `percentage_raise` — The document states a percentage raise or percentage wage adjustment.
- `market_or_comparability` — Pay is linked to a market study, peer comparison, recruitment, or retention.
- `parity_or_internal_equity` — Pay is linked to parity, internal equity, compression, or alignment with another group.
- `bargaining_or_settlement` — Pay is described through CBA, settlement, memorandum, arbitration, or factfinding terms.
- `implementation_timing` — Pay depends on effective dates, retroactivity, schedules, or contract periods.
- `fiscal_constraint` — Pay is linked to budgets, funding, affordability, or municipal fiscal limits.
- `non_base_compensation` — Evidence concerns benefits, overtime, stipends, longevity, leave, healthcare, pension, reimbursement, or equipment.
- `reference_only` — Evidence points elsewhere or supplies navigation/context rather than coded evidence.
- `not_useful_for_attribute_analysis` — Evidence lacks enough support for attribute classification in this phase; a reason code is required.

`not_useful_for_attribute_analysis` requires a short reason code; `null` and `no_good` are not valid labels.
