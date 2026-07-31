# PI Report Appendix Tables

## A. Evidence-base status

| Stage | Count | Note |
|---|---:|---|
| Scout coverage | 16,887 municipalities | 47.45% of 35,589 eligible/known municipality universe |
| 4x2500 scout wave | 10,000 terminal outcomes | 9,968 parseable; 32 failed/unparseable |
| Candidate formation | 9,977 raw / 9,072 deduped | 5,768 verification-ready |
| Verification | 5,768 reviewed | 3,950 reachable/source-review-ready |
| Source review/download | 3,672 retained | 3,248 PDF; 350 HTML; 74 other |
| Text readiness | 2,940 ready | 2,577 PDF; 291 HTML; 72 other; 601 OCR-later |
| Text extraction | 2,795 clean/span-ready | 145 quality/problem rows |
| Span extraction | 19,118 candidates | 18,612 rating-ready |
| Span rating | 18,554 valid | 58 quarantined and excluded |
| Normalization | 11,548 quantitative records | 672 full; 1,563 partial; 3,769 mechanism-only; 720 deferred; 4,824 unusable |
| Matched structure | 2,712 municipality-cycle groups | 65 safety/non-safety candidates; 303 comparable wage candidates; 141 growth-readiness candidates |
| Focused rescue/validation | 416 quantitative growth records | 4 bounded comparisons: 1 PI-usable, 3 conditional |

## B. Mechanism findings and rated strength

| Mechanism | Rated signal count | Average strength | Median strength | Finding level |
|---|---:|---:|---:|---|
| Non-base compensation | 3,718 | 1.646 | 1.0 | Core |
| Direct base-wage evidence | 2,687 | 1.452 | 1.0 | Core |
| Implementation and retroactivity | 2,230 | 1.853 | 2.0 | Core |
| Automatic raises and indexing | 1,431 | 1.377 | 1.0 | Core |
| Bargaining and dispute resolution | 1,135 | 1.285 | 1.0 | Supporting |
| Rank, step, specialization, classification | 763 | 2.427 | 2.0 | Core |
| Strike/no-strike constraints | 587 | 2.539 | 2.0 | Supporting |
| Market and staffing pressure | 398 | 1.374 | 1.0 | Supporting |
| Safety-advantage hints | 192 | 0.987 | 1.0 | Context |
| Fiscal and governance constraints | 188 | 1.531 | 1.0 | Context |

Average and median strength use the project's 0-4 rating scale. They describe span-level support and specificity, not effect magnitude.

## C. Bounded local documentary wage comparisons

| Municipality/state | Period | Safety value | Non-safety value | Difference | Percent | Status | Report use | Key caveat |
|---|---|---|---|---:|---:|---|---|---|
| Shreve, OH | 2024 | $22.00/hour (part-time police officers) | $16.00/hour (part-time utility clerk) | $6.00/hour | 37.5% | validated_pi_report_usable | Supporting example | Same ordinance and hourly basis; duties, experience, schedule, and job requirements are not matched. |
| Cammack Village, AR | 2024 | $25.00/hour maximum (part-time patrolman) | $20.00/hour maximum (administrative assistant) | $5.00/hour | 25.0% | validated_with_caveats_manual_review | Qualified supporting example | Authorized maxima, not confirmed actual wages; enactment fields require manual/legal confirmation. |
| Canastota, NY | 2023-2024 | $23.91/hour (Police Officer Year 1 step) | $24.82/hour (Code Enforcement Officer) | -$0.91/hour | -3.67% | validated_with_caveats_manual_review | Qualified counterexample | Entry-step police rate is not tenure/experience-equivalent to the single code-enforcement rate. |
| Alburtis, PA | Jan-Jun 2018 | $33.57/hour (Chief of Police) | $11.22/hour (Administrative Assistant) | $22.35/hour | 199.2% | validated_with_caveats_manual_review | Limits/appendix only | Chief was outside the police bargaining unit; roles, rank, hours, and schedule position are not comparable. |

Every comparison remains local and documentary. Shreve is PI-usable as a supporting example; Cammack Village and Canastota require heavy caveats; Alburtis is limits/appendix only.

## D. Quantitative growth-mechanism counts

| Growth mechanism | Supported records | PI claim candidates used here |
|---|---:|---:|
| Source-reported percentage increase | 336 | 2 |
| COLA/CPI adjustment | 49 | 2 |
| Step-schedule increase | 29 | 2 |
| Retroactive or lump-sum mechanism | 2 | 0 |
| **Total** | **416** | **6** |

## E. Normalization and matching status

| Structure | Count | Interpretation |
|---|---:|---|
| Full normalization | 672 | Initially met structured comparison requirements |
| Partial normalization | 1,563 | Useful value present; key comparison fields missing |
| Mechanism-only normalization | 3,769 | Growth-rule evidence without wage-level comparability |
| Deferred manual review | 720 | Potentially parseable but not safely automated |
| Unusable normalization | 4,824 | Insufficient evidence for safe structured comparison |
| Municipality-cycle groups | 2,712 | Evidence grouped by place and cycle where possible |
| Safety/non-safety matched-cycle candidates | 65 | Both sides present, subject to comparability review |
| Comparable normalized wage candidates | 303 | Potential wage-level pairs, not final estimates |
| Cycle-to-cycle growth-readiness candidates | 141 | Potential repeated-cycle structures |
| Future-gap-potential-only candidates | 15 | Both sides present but not currently claim-ready |
