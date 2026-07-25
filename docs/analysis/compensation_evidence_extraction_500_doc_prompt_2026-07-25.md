# Future prompt: 500-document compensation-evidence extraction

This prompt is prepared because Gate 3 computed
`500_doc_compensation_extraction_allowed`. It is not executed by Gate 3.

## Objective

Build a provisional, QA-gated extraction ledger for 500 retained local
document/page packets. Extract both quantitative compensation fields and
qualitative compensation-setting mechanisms while preserving their distinct
schemas and provenance.

## Non-negotiable scope

- Use only local retained artifacts authorized by durable PDF readiness and
  text/table detection.
- Do not open URLs, download/redownload, use hosted search, run scouts, verify
  sources, or run OCR.
- Do not ingest contracts or run `gabriel.codify`.
- Do not create a final analysis dataset, calculate wage gaps, run regressions,
  or make causal claims.
- Do not save full documents, complete page text, or full tables.

## Selection

Select exactly 500 unique document identities with bounded page packets using
Gate 3 lessons. Stratify across police, fire, and non-safety; source types;
states; and the expected quantitative, qualitative, and mixed paths. Preserve
city × occupation × negotiation-cycle identity and ensure the selection
contains matched non-safety comparison opportunities. Keep reference-only,
benefits-only, low-confidence, and irrelevant packets outside the primary
base-compensation lanes.

## Provisional schemas

Quantitative fields may include rate, salary, hourly/annual salary,
percentage increase, effective date, step, grade, rank, classification, unit,
and contract period. Qualitative fields may include mechanism, bargaining
logic, indexing formula, comparability basis, parity logic, step progression,
eligibility, implementation, fiscal constraint, reopener, and differentiation
logic.

Every observation must retain document identity, page number, bounded evidence
type, extraction path, confidence, source type, and QA status. Capture only the
minimum bounded evidence needed for audit; never save a full table or page.

## Lanes and resumability

1. Freeze a 500-row selection manifest and hash it.
2. Divide it into non-overlapping lanes with unique output directories.
3. Make each lane restartable by stable case ID; never overwrite completed
   rows without an explicit retry record.
4. Keep quantitative, qualitative, mixed, non-base-wage, reference, and
   exclusion outcomes explicit.
5. Produce lane summaries and stop before final merge.

## QA gate

Before merge, require complete identities/provenance, allowed-value validity,
no duplicate unit-cycle observations, bounded evidence compliance, confidence
and missingness reports, cross-unit/source/state representation, and a blinded
sample review of each extraction path. Fail closed on conflicting numeric
values, unsupported mechanism labels, page mismatch, or provenance gaps.

After all lanes pass, prepare a separate merge authorization report. Do not
ingest, codify, analyze wage gaps, or run regressions in the extraction task.
