# Lane 001 — Non-base compensation and wage-schedule side audit

## Bottom line

Non-safety non-base evidence exists. The controlled normalized side field identifies **226 non-safety non-base spans across 100 sources and 96 municipality-state combinations**. The record is therefore not safety-only. It includes clerical opt-out stipends and longevity provisions, public-works shift differentials, clothing and boot allowances, certification stipends, overtime references, and other non-base channels.

The side-resolved evidence is nevertheless safety-heavy: police, fire, and combined-safety account for **1,528 of 1,754 resolved non-base spans (87.12%)**, versus 226 non-safety spans (12.88%). That ratio is not a prevalence estimate. More than half of the full non-base universe—**1,964 of 3,718 spans (52.82%)**—does not have a sufficiently controlled side assignment and remains `unclear`.

The report should also distinguish direct value signals from complete schedules. The **2,687** figure is the number of valid ratings with a positive `base_wage_direct_value_strength`, not a count of 2,687 complete wage schedules. Of those signals, **661** have an explicit salary-, wage-, step-, or grade/pay-band schedule tag. Only **six** of those 661 schedule-tagged spans are currently `normalization_full`; 600 are `normalization_unusable`, usually because the retained span is a heading, reference, or fragment rather than a complete comparison row.

## Counting method

The audit starts from the 18,554 valid rating records.

- **Non-base universe:** `non_base_compensation_signal_strength > 0`.
- **Direct base-wage/value universe:** `base_wage_direct_value_strength > 0`.
- **Explicit schedule subset:** a direct-value signal carrying `salary_schedule`, `wage_schedule`, `step_schedule`, or `grade_or_payband`.
- **Side:** joined by `span_id` to `normalized_quantitative_records`. The controlled values `police`, `fire`, `combined_safety`, and `non_safety` are preserved. `mixed`, `unclear`, missing, and non-unique assignments are conservatively combined as `unclear`.

No free-text inference was used to fill aggregate side counts. This matters because a unit-specific source title can coexist with a town-wide table or an exact span for another occupation. The selected examples below were separately checked against exact source spans and titles.

## Side counts

| Evidence layer | Police | Fire | Combined safety | Non-safety | Unclear | Total |
|---|---:|---:|---:|---:|---:|---:|
| Non-base compensation signals | 1,239 | 280 | 9 | 226 | 1,964 | 3,718 |
| Direct base-wage/value signals | 802 | 123 | 4 | 319 | 1,439 | 2,687 |
| Explicit schedule-tagged subset | 263 | 23 | 0 | 35 | 340 | 661 |

Among side-resolved direct-value signals, 929 of 1,248 are safety-side (74.44%) and 319 are non-safety (25.56%). Among side-resolved explicit schedule tags, 286 of 321 are safety-side (89.10%) and 35 are non-safety (10.90%). In both layers, more than half of the total remains side-unclear, so these resolved shares describe data coverage rather than population prevalence.

## Non-base evidence by side

The controlled tags show non-base mechanisms on both sides.

- **Police:** 438 stipend/allowance tags, 449 overtime/premium references, 108 longevity tags, 106 shift-differential tags, 53 lump-sum tags, and 37 certification/education tags.
- **Fire:** 120 stipend/allowance tags, 97 overtime/premium references, 31 longevity tags, 16 lump-sum tags, six certification/education tags, and five shift-differential tags.
- **Combined safety:** five stipend/allowance tags, three overtime/premium references, and one lump-sum tag.
- **Non-safety:** 109 stipend/allowance tags, 83 overtime/premium references, 13 longevity tags, seven lump-sum tags, six shift-differential tags, and three certification/education tags.

These tags are multi-label and do not sum to span totals.

### Strongest source-grounded examples

1. **Police — Old Tappan, New Jersey.** Ordinance 1233-23 says: “All Police Personnel covered by collective bargaining agreement will be entitled to shift differential equal to 5% of their gross annual salary.” This is a quantitatively specific police non-base mechanism, not evidence of prevalence.
2. **Fire — Miami, Ohio.** The IAFF agreement records: “Longevity Pay- Hourly Difference—$1.00 per hour for every 5 years of continuous active…” This is direct firefighter longevity evidence; the complete eligibility language and effective period still need document context before quantitative comparison.
3. **Combined safety — South Zanesville, Ohio.** Meeting minutes record an allowance for “Part time police and Assistant fire chief to receive $350.00 a year.” The row is fully normalized as a stipend, but the meeting-minutes context should accompany any report use.
4. **Non-safety — Port Huron Township clerical unit, Michigan.** The contract-settlement record says employees opting out of health coverage had their stipend raised “from $175 per pay period to $400 per pay period.” This directly answers the side question: non-safety non-base compensation is present and quantitatively specific.

The non-safety example is an opt-out stipend, not a base-wage increase. It should be used to establish the existence and form of a compensation channel, not to imply a safety/non-safety differential.

## Direct wage and schedule evidence

The direct-value layer contains 2,687 signals, of which 2,625 have normalized records in the pre-rescue ledger:

| Status | Count |
|---|---:|
| Full | 533 |
| Partial | 1,155 |
| Mechanism only | 55 |
| Deferred manual review | 267 |
| Unusable | 615 |
| No normalized record | 62 |

The rescue pass upgraded 10 of the partial direct-value records to full normalization and identified another 168 as near-gap-ready. The effective direct-value full count is therefore **543**, not 533. The schedule-tagged subset received no full upgrade and only one near-gap-ready promotion.

The narrower 661-row explicit schedule subset is much less comparison-ready:

| Status | Count |
|---|---:|
| Full | 6 |
| Partial | 6 |
| Mechanism only | 25 |
| Deferred manual review | 24 |
| Unusable | 600 |

Examples show both the value and the limitation:

- **Police — Cohasset, Massachusetts:** a six-step patrol schedule maps tenure bands from under one year through 27+ years to six annual values. This is strong schedule structure, but it demonstrates that “police rate” is not a single number. One stored amount also has a punctuation/extraction anomaly requiring source-local confirmation.
- **Fire — Berlin Township, Ohio:** a three-step hourly table lists $23.05, $23.93, and $24.85. The span is fully normalized, but a comparison must still match the category and step.
- **Non-safety — Mayer, Minnesota:** Public Works Utilities Operator Step 3 is listed at $29.24 per hour for the 2024-2026 agreement. This is fully normalized; a safety comparator would need a defensibly analogous schedule location.
- **Combined safety:** no controlled combined-safety row appears in the explicit schedule-tagged subset. The report should not manufacture one.

## What normalization and bounded comparisons support now

Normalization supports a claim of structured quantitative potential, not a final comparison. After the rescue overlay, the direct-value layer has 543 fully normalized signals and 168 additional near-gap-ready records, but most complete-schedule references are still fragmented or unnormalized. The non-base layer has 140 fully normalized signals and four rescue-promoted near-gap-ready records; it supports a robust documentary-mechanism claim but not a matched total-compensation gap.

The bounded comparison validation currently supports four named local statements:

- **Shreve, Ohio:** PI-usable supporting example. The same operative ordinance lists part-time police at $22.00/hour and a part-time utility clerk at $16.00/hour, a bounded local documentary difference of $6.00/hour or 37.5%. Duties, experience, schedules, requirements, and hours equivalence remain unmatched.
- **Cammack Village, Arkansas:** conditional. The same schedule lists a part-time patrolman maximum of $25.00/hour and administrative-assistant maximum of $20.00/hour. They are authorized maxima, not established actual wages; enactment and occupational comparability remain open.
- **Canastota, New York:** conditional and directionally opposite. The 2023-2024 schedule lists Police Officer Year 1 at $23.91/hour and Code Enforcement Officer at $24.82/hour. The -$0.91/hour listed-rate contrast is source-grounded, but entry-step and tenure equivalence are absent.
- **Alburtis, Pennsylvania:** limits/appendix only. The January-June 2018 overlap lists the Chief of Police at $33.57/hour and Administrative Assistant at $11.22/hour, but the Chief was outside the bargaining unit and the roles, rank, hours, and schedule positions are not comparable.

These are bounded local documentary position-rate statements. They do not authorize a final wage-gap estimate, cross-city average, national prevalence claim, regression, treatment effect, or causal claim.

## Position and schedule-location comparability rules

A schedule pairing should enter an analytic comparison only when all applicable rules pass:

1. **Same municipality and overlapping operative period.** Use the actual rate window, not a broad document label.
2. **Same compensation concept.** Base must be paired with base; the same identified premium may be paired with that premium. Do not mix base, maximum authorization, total compensation, overtime, stipends, or allowances.
3. **Compatible pay basis.** Prefer hourly/hourly or annual/annual. Any conversion requires explicit work hours or a separately flagged assumption.
4. **Explicit positions and occupation sides.** Both records require a named classification and a clear police, fire, or non-safety assignment.
5. **Matched schedule location.** Entry with entry, top with top, or the same tenure/step/grade/pay-band concept. A Year 1 officer does not automatically match an unlabeled non-safety rate.
6. **Rank and responsibility alignment.** Chief, captain, supervisor, specialist, and line-worker rates are not interchangeable.
7. **Employment-status alignment.** Full-time, part-time, seasonal, temporary, exempt, and non-exempt status—and their workweek/work-year—must be aligned or explicitly limited.
8. **Operative status.** Confirm enactment and effective status. Label ranges and maxima as authorized values, not actual paid wages.
9. **Bargaining-unit scope.** The core observation is one unit-contract-cycle. A chief outside a unit or a town-wide ordinance line can illustrate a rate, but cannot silently become a matched unit record.
10. **Non-base symmetry.** A base comparison cannot be interpreted as total compensation unless longevity, shift, hazard, certification, uniform, overtime-related, stipend, and allowance components are aligned or explicitly excluded.

Failure on schedule location, rank, employment status, or operative status limits a row to a named-position documentary contrast or context. Municipality and year alone are not sufficient.

## Required report-language repairs

Use:

> The valid rated layer contains 2,687 direct base-wage/value signals, including 661 explicitly schedule-tagged spans. Only six schedule-tagged spans are fully normalized in the current ledger, so these counts identify quantitative source material rather than 661 comparison-ready schedules.

Use:

> Non-base compensation appears in both safety and non-safety records. Among side-resolved signals the evidence is safety-heavy, but more than half of the signal universe is side-unclear, so the distribution is not a prevalence estimate.

Do not say that 2,687 complete wage schedules were recovered, that non-base compensation is uniquely safety-side, or that the corpus already estimates a safety/non-safety total-compensation gap.

## Claim boundaries

No OCR, download, source review, text extraction, rerating, quarantined-row ingestion, wage-gap estimation, national prevalence analysis, regression, treatment-effect analysis, or causal inference occurred in this lane.
