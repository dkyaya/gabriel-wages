# Content-Triage Operating Handoff — CONTENT-TRIAGE-REMAINDER-ALL-ROUTED-2026-07-24

Run every nonempty lane input through `scripts/content_triage_sources.py
--review-mode metadata_only`, then audit them together with
`scripts/audit_content_triage_lanes.py`.

This plan authorizes offline metadata-only triage. It never authorizes content
access, download, parsing, OCR, or human source review. Do not ingest, codify,
extract wages, or calculate wage gaps.
