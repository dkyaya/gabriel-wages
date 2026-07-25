# Calibration Visual QA Spot-Check

## Method

After the 150-row bounded text-assisted adjudication completed, five pages
were rendered from five locked calibration artifacts. The pages were selected
to challenge five different assisted layout outcomes:

- `step_grade`
- `rank_step`
- `annual_salary_schedule`
- `hourly_schedule`
- `no_wage_table`

This was a small visual quality-control check, not a human review of all 150
documents. Only calibration-subset artifacts were opened. No URL, OCR, full
text export, complete table capture, or structured wage-value extraction was
used.

## Findings

| Calibration row | Assisted outcome challenged | Page checked | Visual finding |
|---|---|---:|---|
| `cal_04e9c405fa82bce92279cc76` | `step_grade` | 5 | Wage-related prose and benefit provisions; no step/grade table was visible on the checked page. |
| `cal_045e7e8100647061f677cbed` | `rank_step` | 3 | Labor-relations and longevity-pay prose; no rank/step table was visible on the checked page. |
| `cal_075c10415a94e03dadfb692f` | `annual_salary_schedule` | 1 | Settlement/amendment prose with compensation-related amounts; no annual salary schedule was visible on the checked page. |
| `cal_01a57230b8158e19db8100b3` | `hourly_schedule` | 1 | Memorandum and agreement prose referring to an attached salary schedule; no hourly schedule was visible on the checked page. |
| `cal_0040c3a549555da713b42502` | `no_wage_table` | 1 | Contents page explicitly points to a later salary table, so the bounded assisted `no_wage_table` conclusion is unsafe. |

## Gate implication

The spot-check found a material method problem in all five challenge cases:
text/numeric-structure concordance was not sufficient to adjudicate actual
table presence or layout. The assisted label counts therefore remain useful
as workflow diagnostics, but they are not independent precision estimates
and do not support a 500-document extraction run.

The calibration gate is `fail` for extraction authorization. The next step is
to refine the review/detector schema so visual or structural table evidence is
distinguished from wage-related prose, then rerun a genuinely independent
calibration subset or direct human adjudication.
