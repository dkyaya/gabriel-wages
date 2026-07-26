# Next task: bounded GABRIEL compensation-attribute analysis

Do not run this task without new explicit user authorization.

The current decision is `final_qa_phase_closed_gabriel_attribute_analysis_ready`. Run only the complete prepared prompt at `docs/analysis/compensation_extraction/COMPENSATION-EVIDENCE-FINAL-QA-CATEGORIZATION-AND-GABRIEL-ATTRIBUTE-READINESS-2026-07-25/next_gabriel_attribute_analysis_prompt.md`, and only after new explicit user authorization.

Use only the 643 exact-span rows in `gabriel_attribute_ready_evidence_manifest.csv`. Assign the controlled 13-attribute taxonomy from each supplied literal span, validate every assignment against the exact-evidence schema, and quarantine invalid model output.

Do not fetch sources, open PDFs/pages, OCR, extract, select documents, ingest, codify, compute statistics, calculate wage gaps, run regressions, or make causal claims. Preserve all other categories and lanes outside the model input, and keep global analysis readiness false.
