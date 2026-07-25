# Future Prompt: Conditional 500-Document Wage-Table Extraction

Do not run this prompt as part of calibration review.

Status: **blocked by failed calibration gate**. This prompt is archival
planning material and must not be used until a revised independent
calibration passes.

## Preconditions

Run only after:

- a revised detector/review schema distinguishes wage-related prose from
  actual tables and table layouts;
- a new independent manual/visual calibration passes;
- the 55 `needs_second_review` calibration cases have been reviewed directly
  or a documented representative adjudication supports proceeding;
- the provisional extraction schema and field-level QA rules are approved;
- the coordinator worktree is clean and protected/durable baselines are
  recorded.

If these gates are not met, stop and refine the detector/schema or run a
smaller extraction pilot.

## Task

Prepare and run a bounded local 500-document wage-table extraction pilot over
already-retained PDFs.

Use only high-confidence durable detection candidates, informed by the
reviewed calibration lessons. Preserve p1/p2, police/fire/non-safety,
CBA/wage-schedule/other source-type, officialness, state, page-count, and
layout diversity.

## Required controls

- local retained artifacts and locked candidate pages only;
- verify artifact hash and page count before extraction;
- no URLs, downloads, OCR, APIs/models, scouts, or live review;
- no complete page/document text or copied PDFs;
- no ingestion or `gabriel.codify`;
- write a provisional extraction ledger, not `data/contracts.csv` or an
  analysis-ready wage table;
- preserve every upstream identity and caveat;
- retain table/page provenance, header/effective-date/rate-basis fields,
  extraction status, and sanitized errors;
- balance lanes and make each lane resumable;
- stop before durable final extraction merge;
- do not calculate wage gaps or make causal claims.

## Quality gates

Audit:

- selected identities and calibration-informed eligibility;
- terminal extraction coverage;
- artifact hashes and page bounds;
- duplicate document/page/table-row identities;
- table-layout and effective-date/rate-basis completeness;
- false-positive/no-table outcomes;
- human QA across confidence, unit, source, layout, and state strata;
- absence of full-text artifacts, OCR, ingestion, and codification.

If the 500-run QA is clean, prepare—but do not automatically execute—a
1,000-document follow-on. If it is not clean, refine schema/rules and rerun a
smaller controlled subset.
