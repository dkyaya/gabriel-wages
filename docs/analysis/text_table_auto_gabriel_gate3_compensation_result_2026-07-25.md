# Automated GABRIEL Gate 3 compensation-evidence result

Gate ID: `TEXT-TABLE-AUTO-GABRIEL-GATE3-COMPENSATION-EVIDENCE-2026-07-25`

Method: `automated_bounded_rendered_image_plus_text_layout_gabriel_compensation_evidence_adjudication`

## Execution

- Frozen cases: 150
- Backend: `huit_openai_responses_direct_sdk`
- Model: `gpt-5.4-nano`
- Schema-valid adjudications: 150/150 (100%)
- Image evidence: used for all 150 cases; no text-only fallback occurred
- Existing rendered images attached: 682 (93,613,400 bytes across requests)
- Local bounded pages evaluated: 769
- Bounded text characters: 632,553
- Maximum packet: six pages/images, four navigation pages, 1,500 text
  characters per page, and 6,000 per case
- Failed final cases: zero

The 150-case no-call dry run passed before live work. The first preflight
reached the API but was rejected before adjudication because that endpoint's
strict-schema dialect does not accept `uniqueItems`. Local duplicate rejection
was retained while the unsupported transport keyword was removed. The second
one-case image preflight passed. The primary full pass returned 145 locally
valid responses; five otherwise controlled responses repeated an allowed
qualitative field. A bounded five-case resume deduplicated controlled values
locally and produced the final 150/150 ledger. No heuristic-only fallback was
used.

## Best-use categories

| Compensation evidence category | Count |
| --- | ---: |
| `mixed_quant_qual_ready` | 84 |
| `non_wage_compensation` | 31 |
| `quant_table_ready` | 14 |
| `qual_mechanism_ready` | 12 |
| `not_compensation_relevant` | 7 |
| `quant_compact_ready` | 1 |
| `reference_navigation_only` | 1 |
| `quant_prose_ready` | 0 |
| `second_review_required` | 0 |
| `error` | 0 |

Quantitative evidence presence is 112 yes, 16 maybe, and 22 no. Qualitative
mechanism evidence presence is 122 yes, nine maybe, 18 no, and one unknown.

## Evidence types

Quantitative subtype counts are 34 prose-specific-rate, 22 wage-table, 14
prose-percentage-raise, 11 grade-step, 11 percentage-increase schedule, six
compact sheets, five hourly schedules, two salary schedules, one rank-step,
one pay band, 41 none, and two unknown. The category and subtype answer
different questions: a case with rate prose plus mechanism language is best
used as mixed evidence even when its quantitative subtype is prose.

Qualitative subtype counts are 71 implementation/effective-date logic, 22 CBA
terms, eight step/seniority, five CPI/COLA, five comparability/market-study,
five fiscal/budget logic, four certification/education incentive, three
arbitration/factfinding reasoning, three longevity/service-based pay, two
parity/internal equity, one memorandum/settlement, and 21 none.

Non-wage-compensation subtype counts are 19 leave, 13 healthcare
contributions, 10 stipends, nine overtime, six benefits, six longevity, six
pension, five education/certification, three reimbursements, three
uniform/equipment, 11 other, 55 not applicable, and four unknown. These labels
preserve compensation-adjacent evidence without treating it as base wage.

## Extractable field signals

The bounded classification identifies potential quantitative field families,
not extracted values. The most frequent are effective date (105), percentage
increase (77), rate (73), hourly rate (48), unit (42), step (36),
classification (34), contract period (32), annual salary (29), salary (28),
grade (28), and rank (6).

Potential qualitative field families are implementation rule (131), mechanism
(92), eligibility rule (90), step progression (35), fiscal constraint (24),
parity logic (20), bargaining logic (18), comparability basis (10), indexing
formula (9), reopener clause (3), and differentiation logic (1).

## Page relation, strength, and recommendation

Relationships are 97 exact-evidence pages, 29 adjacent pages, one later-
evidence pointer, one no-candidate page, 22 unknown, and zero wrong pages.
Evidence strength is 79 high, 58 medium, 12 low, and one unknown. Gate 3
confidence is 78 high, 65 medium, and seven low.

Recommendations are 102 mixed-extraction-ready, 22 qualitative-extraction-
ready, 15 quantitative-extraction-ready, eight exclude-for-now, and three
reference-followup-needed. Category, recommendation, and confidence are
combined by the deterministic decision rule; 108 rows satisfy its ready rule.

## Representation and authorization metrics

- Original likely/p1 ready: 70/80 = 87.50%; required at least 80%.
- Schema-valid responses: 150/150 = 100%; required at least 95%.
- Decision-rule ready cases: 108.
- Ready units: 36 police / 32 fire / 40 non-safety.
- Ready sources: 48 CBAs / 26 wage plans / 14 ordinances / 13 memoranda or
  settlements / six arbitration awards / one factfinding source.
- Reference-only plus second-review share: 1/150 = 0.67%; not dominant.
- Errors: zero.

Quantitative-support cases number 95, qualitative-mechanism-support cases 92,
and mixed-category cases 84. These sets overlap by design.

## Result

Gate 3 resolves the over-narrow wage-table framing: 64 Gate 2 exclusions and
22 Gate 2 second-review cases now satisfy the broader ready rule, while 31
non-base-wage cases and seven irrelevant cases remain separated from the base-
wage path. All 22 Gate 2 ready cases remain ready.

Decision: `500_doc_compensation_extraction_allowed`.

This authorizes preparation and a future run of a combined quantitative plus
qualitative compensation-evidence extraction design. It does not mean that
Gate 3 extracted any wage value or final mechanism observation, and it does
not authorize ingestion, codification, or wage-gap analysis.

No URL/hosted search, download/redownload, OCR, scout, source review, wage
extraction, qualitative final extraction, ingestion, codification, regression,
remote action, or durable-ledger mutation occurred.
