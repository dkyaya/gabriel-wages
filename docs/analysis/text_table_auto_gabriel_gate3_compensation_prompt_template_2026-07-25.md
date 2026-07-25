# Gate 3 compensation-evidence prompt template

You are evaluating bounded page evidence from a municipal labor or
compensation source. Classify the evidence by its best research use.

The research needs both:

1. quantitative compensation data, including rates, salaries, hourly or
   annual amounts, steps, grades, ranks, classifications, pay bands,
   percentage increases, effective dates, and contract periods; and
2. qualitative mechanism evidence explaining how compensation is set,
   adjusted, negotiated, differentiated, constrained, or implemented.

Do not focus only on classic wage tables. Distinguish:

- clean wage, salary, or rate schedules;
- compact compensation sheets and ordinance-style listings;
- prose stating specific rates, percentage raises, or effective-date changes;
- qualitative compensation-setting mechanisms such as bargaining terms,
  CPI/COLA/indexing, comparability, market studies, parity/internal equity,
  step progression, rank/class differentiation, longevity, certification,
  fiscal constraints, reopeners, arbitration reasoning, settlement logic, or
  implementation rules;
- pages that only point to evidence elsewhere;
- benefits and non-base-wage compensation such as overtime, stipends,
  pensions, leave, healthcare contributions, reimbursements, or uniforms;
- grievance, discipline, front matter, signatures, and other material without
  useful compensation evidence.

## Rules

- Judge only the bounded pages/images supplied. Do not infer unseen evidence.
- Do not extract or repeat final wage rows or complete mechanism passages.
- Do not calculate any amount, increase, gap, trend, or causal effect.
- Wage-related prose is quantitative only if it states a specific rate,
  salary, percentage change, effective date, or implementable quantitative
  rule.
- Prose explaining how pay is set is qualitative mechanism evidence even when
  it contains no wage table or numeric amount.
- Benefits/overtime/stipends/longevity are non-base-wage compensation unless
  the bounded evidence also contains qualifying base-wage or mechanism
  evidence.
- A contents/index/reference page without its target is
  `reference_navigation_only`.
- A mixed case has both usable quantitative evidence and useful qualitative
  mechanism evidence.
- The output is calibration classification, not extracted research data.

Return one strict JSON object using exactly the fields and controlled values
in `gate3_compensation_evidence_v1`. Return one to eight short uppercase
reason codes and a rationale no longer than 300 characters that contains no
wage values. When images are not supplied, return `not_applicable` for the
image-observation fields. Do not return markdown or extra keys.

The primary prompt must not contain REVIEW1, REVIEW2, Gate 1, Gate 2, prior
automated labels, or prior recommended actions.

## Packet limits

- at most six bounded pages/images per case;
- at most four navigation pages;
- at most 1,500 redacted text characters per page;
- at most 6,000 redacted text characters per case;
- no whole PDF or document;
- no raw prior labels;
- no full page/document text, complete table, wage rows, or final mechanism
  observations.
