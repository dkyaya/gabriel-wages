# Refined calibration REVIEW2 result

Date: 2026-07-24
Calibration: `TEXT-TABLE-CALIBRATION-SUBSET1-150-2026-07-24`
Review: `TEXT-TABLE-CALIBRATION-SUBSET1-REFINED-REVIEW2-2026-07-24`
Method: `codex_assisted_refined_visual_gate`

## Outcome

The refined review completed terminal adjudication for all 150 rows using
only the 150 selected retained local PDFs. The workflow opened 150 PDFs,
inspected 762 bounded pages, rendered 407 bounded pages with zero render
failures, and retained no page images, full text, full tables, or final wage
values.

This is assisted calibration, not independent human ground truth. The
extraction decision is **`continue_schema_refinement`**. Neither the
500-document run nor a smaller extraction pilot is authorized.

## Refined labels

| `wage_language_present_label` | Rows |
|---|---:|
| yes | 111 |
| maybe | 16 |
| no | 22 |
| unknown | 1 |

| `pay_numeric_language_present_label` | Rows |
|---|---:|
| yes | 126 |
| no | 23 |
| unknown | 1 |

| `visual_table_structure_label` | Rows |
|---|---:|
| confirmed_table | 77 |
| possible_table | 15 |
| prose_only | 7 |
| index_or_contents | 23 |
| benefits_table | 4 |
| classification_only | 3 |
| non_wage_table | 16 |
| front_matter | 2 |
| unknown | 3 |

| `wage_schedule_table_confirmed_label` | Rows |
|---|---:|
| yes | 77 |
| maybe | 16 |
| no | 56 |
| unknown | 1 |

| `candidate_page_relationship_label` | Rows |
|---|---:|
| exact_table_page | 84 |
| adjacent_to_table | 3 |
| points_to_later_table | 3 |
| wrong_page | 42 |
| no_candidate_page | 17 |
| unknown | 1 |

| `table_navigation_signal` | Rows |
|---|---:|
| direct | 84 |
| nearby | 3 |
| index_or_contents | 2 |
| appendix_reference | 1 |
| none | 59 |
| unknown | 1 |

| `visual_confirmation_method` | Rows |
|---|---:|
| text_structure_plus_rendered_check | 149 |
| text_structure_only | 1 |

| `extraction_gate_label` | Rows |
|---|---:|
| pass_high_confidence | 74 |
| pass_with_schema_update | 15 |
| second_review_required | 29 |
| fail_exclude | 32 |

Calibration status was `reviewed` for 119 rows and
`needs_second_review` for 31 rows. Extraction complexity was easy for 26,
moderate for 48, hard for 44, and not extractable for 32.

## Gate-reason themes

- 74: repeated wage/pay rows and columns appeared on a bounded
  candidate-related page under the automated render check;
- 27: wage/pay language appeared without an assisted confirmed table;
- 24: bounded evidence appeared to be benefits, non-wage,
  classification, or front matter;
- 15: possible table structure requires schema/layout adjudication;
- 8: no bounded wage-table structure was confirmed;
- 1: contents/index/appendix language pointed to a later table;
- 1: bounded reviewed pages returned no text; OCR was not run.

These are REVIEW2 assisted labels. The independent challenge materially
disagreed with several of the 74 apparent high-confidence cases.

## Authorization metrics

- Likely-signal strict visual confirmation: 61/80 = **76.25%**
- Likely-signal inclusive yes/maybe rate: 68/80 = **85.00%**
- Wrong-page rate among candidate-bearing rows: 42/132 = **31.82%**
- p1 `pass_high_confidence`: **61**
- p1 `pass_with_schema_update`: **7**
- `second_review_required`: **29**
- `fail_exclude`: **32**
- Independent rendered QA primary agreement: 10/18 = **55.56%**
- Independent rendered QA exact-gate agreement: 8/18 = **44.44%**

The strict likely confirmation rate is below 80%, the wrong-page rate is
above 15%, and the rendered QA agreement is below 80%. Major ambiguity
remains around wage prose, budget/benefit pages, compact compensation sheets,
and contents/appendix navigation.

## Comparison with REVIEW1

REVIEW2 demoted many REVIEW1 positive rows: among the 134 REVIEW1 yes/maybe
rows, 18 became `fail_exclude` and 27 became `second_review_required`.
Across all rows, 81 recommended extraction actions changed. REVIEW2 also
identified 42 wrong pages among the 132 pages REVIEW1 had called correct or
partially correct.

Those changes are directionally useful, but REVIEW2 is still assisted and
shared local structural features with the detector. The blinded challenge
found only 55.56% material agreement, so the refined gates do not pass.

## Decision

**`continue_schema_refinement`**

The 500-document extraction is not allowed. A smaller extraction pilot is
also not authorized by this calibration because the independent challenge
failed and both false-positive and false-negative table-family ambiguities
remain.

The next step is independent human adjudication of a balanced visual subset,
plus rule changes that:

1. make rendered row/column evidence—not text alignment—the decisive table
   criterion;
2. follow contents/appendix pointers within a tightly bounded target-page
   budget;
3. distinguish aggregate budget/benefit tables from employee wage schedules;
4. recognize compact schedule-like salary sheets without treating ordinary
   wage prose as tables;
5. rerun a blinded challenge before any extraction authorization.

## Boundaries and counters

- URLs opened: 0
- Network/API/model calls: 0
- Downloads or redownloads: 0
- OCR runs: 0
- Full-text or full-table artifacts retained: 0
- Final wage values extracted: 0
- Ingestion actions: 0
- Codify actions: 0
- Durable-ledger mutations: 0

The original calibration input and every REVIEW1 output remained unchanged.
