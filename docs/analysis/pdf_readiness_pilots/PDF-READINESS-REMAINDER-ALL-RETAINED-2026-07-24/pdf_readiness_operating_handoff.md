# PDF-Readiness Operating Handoff

Pilot: `PDF-READINESS-REMAINDER-ALL-RETAINED-2026-07-24`

Run dry-run validation for every lane before local parsing.
The live-local runner may open only the retained paths in the locked lane CSVs. It must verify hashes before parsing, sample at most three pages, retain only counts/statuses, save no extracted text, and run no OCR.

This layer records technical parseability only. It must not be promoted to content relevance, wage evidence, ingestion, codification, or analysis-ready observations.
