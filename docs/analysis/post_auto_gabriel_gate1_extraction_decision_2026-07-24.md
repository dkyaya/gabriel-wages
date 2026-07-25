# Post automated GABRIEL gate 1 extraction decision

Gate ID: `TEXT-TABLE-AUTO-GABRIEL-ADJUDICATION-GATE1-2026-07-24`

## Final decision

`continue_schema_refinement`

Neither a 500-document extraction run nor a smaller extraction pilot is
authorized.

## Rationale

The strict final pass achieved 150/150 schema-valid GABRIEL adjudications and
an estimated wrong-page rate of 6.82%, both of which pass their required
thresholds. Non-wage negative families were also prevented from receiving a
final ready label.

The central recall/coverage criterion failed decisively. Only 27 of 80
original likely/p1 cases (33.75%) became
`extraction_ready_high_confidence` or
`extraction_ready_with_schema_update` with high/medium confidence, versus the
required 80%. Only 28 total rows were ready, below the representative-set
minimum of 30; 19 more require second review and 103 are excluded.

This result cannot be converted into authorization by treating the lower
wrong-page rate as sufficient. The automated gate found that many prior
likely/p1 and REVIEW2-positive cases are wage prose, no-table material,
benefits, contents/index pages, or otherwise lack sufficient row/column
structure in the bounded evidence.

## Allowed next scale

Calibration/refinement on the same bounded local evidence is allowed.
Extraction scale is **zero** until a subsequent calibration gate passes.

The next refinement should:

1. separate true no-candidate cases from page-hint failures;
2. improve deterministic discovery of actual role-by-pay pages without
   increasing the six-page packet limit;
3. create explicit rules for prose, compact compensation sheets, and
   navigation-target pages;
4. analyze the 19 second-review cases and the 53 likely/p1 cases not in a ready
   label;
5. rerun a strict bounded GABRIEL gate and recompute all authorization
   thresholds.

No 500-document or smaller-pilot extraction prompt is created. The only future
prompt created by this task is the gate-2 refinement prompt.

## Boundary

No URLs, downloads, OCR, wage extraction, ingestion, codification, wage-gap
analysis, or regression is authorized or performed by this decision.
