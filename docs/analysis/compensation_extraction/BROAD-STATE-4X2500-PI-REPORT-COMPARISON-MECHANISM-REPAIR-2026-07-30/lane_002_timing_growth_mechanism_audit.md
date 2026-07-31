# Lane 002 — Timing and quantitative growth-mechanism audit

## Scope and conclusion

This lane audited three related but analytically distinct layers:

1. all 2,230 valid rated spans with a positive `implementation_or_retroactivity_advantage_strength`;
2. the 416 records previously summarized as quantitatively supported growth mechanisms; and
3. the 95 report claim candidates generated from that 416-record layer.

The 416-record total is the disjoint union of 336 percentage-growth records, 49 COLA/CPI records, 29 step-schedule records, and 2 records previously placed in a retroactive/lump-sum file. The nominal umbrella files `quantitative_growth_mechanism_supported_records.csv` and `.jsonl` are empty; the four subtype files are therefore the reconstructible source of truth.

The principal audit finding is that neither the 2,230 implementation/retroactivity signal count nor the 416 quantitative-growth count should be read as a count of confirmed recurring wage increases. In the 2,230-span rating layer, 2,022 spans (90.7%) are generic effective-date or otherwise unclear timing context. In the 416-record growth layer, 162 records contain a sufficiently clear recurring base-wage, salary-schedule, COLA, or step-schedule increase; 3 contain one-time lump sums, 3 contain retroactive-payment evidence, 2 contain explicit delayed or conditional implementation, and 246 remain unclear or do not describe recurring base-wage growth.

These are documentary mechanism counts, not municipality prevalence estimates, normalized growth estimates, or causal effects.

## Exact layer counts

| Layer | Records | Police | Fire | Combined safety | Non-safety | Unclear |
|---|---:|---:|---:|---:|---:|---:|
| Positive implementation/retroactivity rating strength | 2,230 | 795 | 218 | 1 | 273 | 943 |
| Quantitatively supported growth input | 416 | 124 | 38 | 1 | 64 | 189 |
| Report claim candidates | 95 | 63 | 15 | 0 | 14 | 3 |

The audited side uses the exact unit label when present, then an unambiguous unit-specific source title. It corrects 68 of the 416 inherited side labels. Mixed or generic municipal material remains `unclear`; it is not assigned to safety or non-safety by inference.

## Mechanism audit

### Positive implementation/retroactivity ratings (2,230)

| Audited mechanism | Count |
|---|---:|
| Recurring base increase or schedule timing | 85 |
| Retroactive-payment candidate | 118 |
| Delayed or conditional implementation | 5 |
| One-time lump sum, cleanly isolated | 0 |
| Unclear or generic effective-date context | 2,022 |

The 118 retroactive-payment rows are lexical, compensation-linked candidates, not fully adjudicated payment events. The layer should therefore support a bounded statement that implementation and retroactivity recur in the corpus, but it does not support describing all 2,230 spans as realized retroactive compensation.

### Quantitatively supported growth records (416)

| Audited mechanism | Count |
|---|---:|
| Recurring base or schedule increase | 162 |
| One-time lump sum | 3 |
| Retroactive payment | 3 |
| Delayed or conditional implementation | 2 |
| Unclear or not recurring base growth | 246 |

The reported subtype distribution remains 336 percentage, 49 COLA/CPI, 29 step schedule, and 2 retroactive/lump-sum. The two records in the reported retroactive/lump-sum subtype do not survive substantive review as such: one is an isolated “increase of $1” fragment and the other is a water-rate increase. Conversely, source-grounded one-time, retroactive, and delayed-implementation evidence occurs in records originally classified under other reported subtypes.

### Report claim candidates (95)

| Audited mechanism | Count |
|---|---:|
| Recurring base or schedule increase | 72 |
| Retroactive payment | 2 |
| Delayed or conditional implementation | 2 |
| One-time lump sum | 0 |
| Unclear or not recurring base growth | 19 |

The 76 usable recurring/timing claim records span 45 unique municipalities. Counts are record counts, not unique mechanisms: nested or overlapping spans remain in the source layer. The nineteen unclear records include insurance employee-share percentages, assignment or shift premiums, promotion/rank relationships, and other percentages that are not recurring cycle-level wage growth.

## Named municipality context

### Howland, Ohio

- **Police:** the record contains recurring base-wage terms, including a 2% increase for July 1, 2021 through June 30, 2022. Other source-grounded police increases appear in adjacent periods.
- **Non-safety:** the Road Department/public-works agreement provides a 3% hourly-wage increase for July 1, 2021 through June 30, 2022 and 2% for July 1, 2022 through June 30, 2023. Nested spans duplicate part of this evidence.
- **Fire:** the 5% and 7% claim-candidate percentages concern employee shares of insurance costs, not firefighter wage raises, and must be excluded from growth claims. A broader normalized fire schedule contains a possible wage-increase line, but it is not sufficiently clean in this audited candidate layer.
- **Comparison:** the overlapping 2021–2022 documentary terms show a police 2% base-wage mechanism and a Road Department 3% hourly-wage mechanism. This is a bounded same-municipality mechanism contrast, not a final matched growth estimate or causal comparison.

### Coleraine, Minnesota

- **Police:** the LELS agreement states a 5% wage increase effective January 1, 2024. Later 5% terms for 2025 and 2026 appear in broader normalized records, but only the 2024 term belongs to the audited 416/95 layer.
- **Fire/non-safety:** no comparable fire or non-safety growth record is present in the audited layer.
- **Use:** strong unit-specific police recurring-growth example; not a cross-occupation comparison.

### Sunrise Beach, Missouri

- **Police:** Resolution 2024-06 identifies a 1.5% pay-scale step percentage and describes it as essentially representing a COLA.
- **Fire/non-safety:** a later non-safety City Clerk pay level exists elsewhere in normalized data, but no comparable non-safety growth mechanism is present in the audited 416 records; no fire comparison is present.
- **Use:** quantitatively supported police step/COLA mechanism for 2024, not a matched safety/non-safety growth claim.

### Phippsburg, Maine

- **Non-safety:** the clean 3.2% COLA evidence belongs to the Assessing Agent, a non-safety role.
- **Unclear:** another fragment reports “3.2% COLA” and “8.7% COLA” without a reliable row header or unit label.
- **Safety:** the inherited police classification is unsupported. Other percentage fragments concern budgets, schools, or county amounts rather than a validated police/fire wage mechanism.
- **Use:** retain the Assessing Agent COLA as a non-safety growth mechanism; exclude the record from police-growth and cross-occupation comparison claims.

### Bath, Ohio

- **Police:** a factfinding record documents contested proposals—an employer proposal of 4% for 2022 and 3.5% for 2023, versus union/pattern terms of 2.25% and 2%, together with a first-step issue.
- **One-time context:** the broader report mentions a $0.60 hourly term and a one-time $1,200 bonus, but those items are not claim candidates in the audited 416 subset.
- **Fire/non-safety:** no comparable fire or non-safety percentage-growth mechanism is present in the audited layer.
- **Use:** bargaining-proposal evidence showing quantitative wage positions, not proof of implemented raises.

### Tonka Bay, Minnesota

- **Non-safety:** all three inherited police claim candidates come from a Teamsters Local 320 agreement for Maintenance Employees. They are non-safety records.
- **Mechanism:** a salary-schedule statement reports that the 2023 schedule reflects a 2.75% increase over 2019. A later schedule fragment contains 2.75% and 3.5% but has OCR-corrupted or ambiguous year alignment.
- **Fire/police:** no comparable police or fire growth mechanism is present in the audited layer.
- **Use:** retain as non-safety recurring schedule evidence with a year-alignment caveat; do not use it as police evidence.

## Strongest side-specific examples

### Firefighter evidence

The strongest clean firefighter example is Marion Township, Ohio. The IAFF agreement provides explicit general wage increases of 1.75% effective January 1, 2018; 1.85% in 2019; 2.75% in 2021; and 3.25% in 2022. This supports a recurring, source-reported firefighter wage-growth mechanism. It does not establish a cross-occupation differential without a matched non-safety term.

Olmsted Township, Ohio, provides a useful but weaker bargaining example: a fire factfinding record presents proposed increases of 3% in 2016, 3% in 2017, and 2% in 2018. Turtlecreek, Ohio, similarly documents a proposed 3% 2025 wage-scale term. Both are proposal evidence and must not be described as implemented raises.

### Non-safety evidence

Howland’s Road Department agreement is the strongest non-safety example in the named set: 3% and 2% hourly-wage increases over successive agreement years. Other clean examples include a 16.5% hourly-wage adjustment for Goodrich, Michigan’s DPW Supervisor beginning July 1, and a 3% wage increase for Yale, Michigan clerical/DPW employees. Tonka Bay’s maintenance schedule is also non-safety, but its year alignment requires a caveat.

## PI-facing conclusions

- Within the audited corpus, recurring base-wage and schedule increases occur for police, fire, and non-safety units. The report-ready claim subset contains 48 police, 9 fire, 13 non-safety, and 2 unclear recurring-growth records.
- Firefighter growth evidence exists and should not be omitted: Marion Township supplies a clear implemented schedule of general wage increases, while Olmsted Township and Turtlecreek supply quantitative proposal evidence.
- Non-safety evidence is also substantive. Howland Road Department, Goodrich DPW, Yale clerical/DPW, and Tonka Bay maintenance records show that quantitative growth mechanisms are not unique to public-safety units.
- The audited named comparisons mostly show mechanism-specific documentary contrasts, not complete cross-occupation matched estimates. Howland is the clearest overlapping police/non-safety example; Phippsburg and Tonka Bay require correction from inherited police labels to non-safety.
- One-time lump sums, retroactive payments, and delayed implementation must remain separate from recurring base growth. Collapsing these channels would overstate recurring wage growth.
- Nothing in this lane supports a national prevalence claim, a final wage-gap estimate, or a causal conclusion.
