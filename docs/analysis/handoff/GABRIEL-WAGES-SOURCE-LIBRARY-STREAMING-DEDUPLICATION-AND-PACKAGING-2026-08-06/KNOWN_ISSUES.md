# Known issues

## Redistribution review is unresolved

All 26,637 canonical identities in the current inventory are marked `manual_review_required` because redistribution rights were not adjudicated in the available metadata. The package must not be placed on a public website or transferred beyond the approved research context until that review is completed.

## One inventory entry is not a source

The zero-byte file `retained_quota.lock` is a workflow control file. It is quarantined and should not be included among packaged originals. Its exclusion leaves 26,636 eligible canonical sources.

## Descriptive metadata are sparse

The canonical inventory currently has blank source type, municipality, state, period, original URL, and extraction-status fields. The physical-source inventory also contains no recovered original URL pointers. Source identity and byte-level provenance are strong; descriptive discovery metadata require later enrichment from existing source-review manifests.

## Extracted-text coverage must be reported separately

An original may have usable extracted text, partial text, deferred OCR, a repair hold, or no companion. Do not infer extraction availability from file extension. Do not package extracted text under `originals/`.

## Exact duplicates have aliases

The physical inventory contains 154 exact-duplicate groups and 162 redundant physical copies. The package should retain one canonical original per SHA-256 identity and preserve the redundant names through the alias index.

## Source contents did not receive a full credential scan

The source-selection metadata contain no credential-like filenames, URL credential fields, or absolute paths. A bounded repository audit found no secret-pattern file. The contents of all 56.16 GB of canonical material were not exhaustively scanned for private information. Handle newly discovered sensitive content through quarantine rather than copying it into issue reports.

## Current repository paths are provenance, not package locations

Existing source locations are relative to the original repository and span several historical storage roots. Recipient-facing tools must use `library_relative_path` and a caller-supplied library root. They must not depend on the original repository layout.

## Some source formats need specialized software

The inventory includes PDF, HTML, Word, spreadsheet, CSV, text, RTF, and JSON files. Extraction quality and viewer support differ by format. Preserve original bytes even when a viewer cannot render a file.

## Source-only scope

This library does not include report arguments, evidentiary classifications, report-specific examples, or visual conclusions. It provides source material and source-management metadata only.

