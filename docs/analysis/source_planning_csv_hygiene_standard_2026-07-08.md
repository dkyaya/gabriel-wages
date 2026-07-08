# Source-Planning CSV Hygiene Standard

**Date:** 2026-07-08
**Scope:** planning, audit, source-target, and ingestion-preparation CSVs used before any corpus edit.

## Why this standard exists

The Texas/Ohio planning files exposed a real row-shift problem: free-text fields contained unescaped commas, and hand-typed CSV rows split those commas into extra columns. A row could look readable in a text editor while Python's `csv` parser shifted every downstream field into the wrong column. That is not cosmetic. It can break later ingestion scripts or, worse, silently attach a URL, source type, or occupation-class value to the wrong field.

## Required practice

Future planning and ingestion CSVs must be written with a structured writer such as Python `csv.writer`, `csv.DictWriter`, or pandas. Do not hand-type free-text CSV rows where commas can leak into columns.

After writing or editing any planning CSV, immediately parse it back with Python and fail-stop if it does not parse cleanly. The parse-back check must include:

- Row-width checks: every row must have exactly the header's column count.
- Required-column checks: expected headers must be present before downstream work uses the file.
- Controlled-value checks: status, priority, corpus, source-type, occupation-class, retrieval-method, and similar enumerated fields must contain only declared values.
- Duplicate-key checks where relevant: source targets, proposed filenames, proposed IDs, or other row keys should not duplicate unless the file explicitly allows duplicates.
- Missing-critical-value checks for rows marked first-batch, approved, ingest-ready, or fetch-ready.

All nontrivial free-text fields should be quoted by the writer. This includes `source_target`, `source_url_or_lookup_path`, `reason`, `caveat`, `notes`, `fetch_instruction`, and any field likely to contain commas, semicolons, parentheticals, URLs, lists, or titles.

If a CSV fails any parse-back, row-width, controlled-value, or duplicate-key check, stop and repair the CSV before doing content analysis from it. Do not carry a structurally suspect CSV into an approved source plan, relay bundle, or ingestion run.

## Relay workflow rule

CSV hygiene is now part of the standard relay/checklist workflow. A relay bundle or handoff that depends on a planning CSV should state whether the file was parse-checked, row-width-checked, controlled-value-checked, and duplicate-checked. When a planning CSV is newly created, the writer method and parse-back result should be recorded in the session log or handoff.
