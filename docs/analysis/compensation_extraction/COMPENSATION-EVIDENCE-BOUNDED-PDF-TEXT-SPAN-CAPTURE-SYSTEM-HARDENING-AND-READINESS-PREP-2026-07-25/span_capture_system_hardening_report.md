# Span capture system hardening report

The runner enforces immutable structured-input hashes and hashes each of 788 unique PDFs before parsing. A page-access guard admits only the 1223 precomputed `(PDF hash, path, page)` tuples. OCR-later inputs fail before parsing. Pages are opened through pypdf's text layer only; text exists only in memory for one approved page and is cleared after related rows are processed.

Checkpoint rows contain spans and provenance but no page text. Schema/input signatures prevent stale reuse. Resume materializes final outputs only after all 1,954 unique observation IDs are present. Exact spans must round-trip by offsets, match their SHA-256, obey the 500-character cap, remain single-line for safe CSV/repository handling, and not equal the full page text. Ambiguous multiple candidates remain navigation-only.

All carried-forward lane files are byte-checked copies. The final invariant file records row uniqueness, page access, no-OCR, no-leakage, span hash, and span-length checks.
