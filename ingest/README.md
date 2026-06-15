# Ingestion Pipeline

Turns source documents into validated `contracts.csv` rows. One document in → OCR-aware text extraction → verbatim clause-span extraction (regex first, optional LLM fallback) → schema-valid row → coverage update → validation.

## Two intake paths (by source legality)

**Open sources → `fetchers/`.** Genuinely public portals (Cornell ILR, state PERBs, municipal clerks) are pulled programmatically. Each fetcher isolates DOM parsing in `parse_listing()` marked `# CONFIRM-SELECTOR`, because the live page structure must be verified before a real run and changes over time. Run any fetcher with `--dry-run` first.

**Licensed + FOIA → `inbox/`.** Westlaw, Lexis, Bloomberg Law, and FOIA material are **not scraped** — their terms prohibit automated extraction. You retrieve them under your own license/request, drop the files in `inbox/licensed/` or `inbox/foia/`, describe them in `inbox/manifest.csv`, and `process_inbox.py` runs them through the identical pipeline. This keeps the project compliant while still automating everything downstream of retrieval.

Both paths converge on the same `pipeline.py`, so extraction, flagging, quarantine, and validation are identical regardless of source.

## Components

| File | Role |
|---|---|
| `extract_text.py` | PDF → text. Tries the embedded text layer; if it's thin/absent (scanned doc), falls back to OCR (pdf2image + tesseract). Returns a `text_quality` tag (`clean`/`ocr_messy`/`partial`). Auto-detection handles the "not sure yet" document mix. |
| `extract_spans.py` | Text → verbatim clause spans. **Stage 1 regex** (deterministic, auditable) locates interest-arbitration, comparability (+ referent), me-too, and no-strike clauses, absorbing the clause body when only a heading matches. **Stage 2 LLM fallback** (optional, off without an API key) finds what regex missed and is gated by an anti-paraphrase guard: any LLM-returned span that isn't a literal substring of the source is discarded. |
| `pipeline.py` | One document + metadata → one validated row. Derives `safety_flag`, captures spans verbatim, never invents provenance. Rows missing required metadata go to `data/needs_metadata.csv` (quarantine), never into the corpus. |
| `process_inbox.py` | Batch-ingests `inbox/` documents per `manifest.csv`. Supports `--dry-run` and `--llm`. |
| `fetchers/` | Open-source fetchers. `BaseFetcher` + per-source subclasses. |
| `audit_coverage.py` | Reports safety units lacking a matched non-safety comparison unit (the design's dead weight) first. |
| `test_pipeline.py` | 18 self-contained tests (no pytest). Covers extraction, heading-body merge, referent capture, the verbatim guard, and quarantine. |

## The verbatim discipline, enforced in code

The schema rule "capture verbatim, never pre-code" is not left to RA diligence here — it's mechanical. Regex returns the exact source paragraph. The LLM stage is constrained to return literal quotes and *verified* against the source (`_verify_verbatim`), so a paraphrase silently fails the check rather than contaminating a row. What GABRIEL scores is always source text, never model- or RA-rewritten text.

## Usage

```bash
# one-off debug
python ingest/pipeline.py path/to.pdf path/to.meta.json [--llm]

# batch from inbox (the main Option-B workflow)
python ingest/process_inbox.py --dry-run     # parse only
python ingest/process_inbox.py               # ingest + validate
python ingest/process_inbox.py --llm         # enable LLM span fallback

# open-source fetch (confirm selectors first)
python -c "from ingest.fetchers import CornellILRFetcher; CornellILRFetcher(dry_run=True).run()"

# health checks
python ingest/audit_coverage.py
python ingest/test_pipeline.py
python scripts/validate.py
```

## LLM fallback setup

The LLM stage uses the Anthropic API and stays off unless `ANTHROPIC_API_KEY` is set in the environment. Model string is `claude-sonnet-4-6`. With no key, the pipeline runs regex-only and lists unresolved clause types in the ingest result so you can spot-check them manually.

## What you must confirm before a real fetch run

Live portal DOMs can't be tested from a sandbox and drift over time. Each fetcher's `parse_listing()` raises `NotImplementedError` with a pointer rather than guessing selectors, so it fails loudly instead of scraping wrong elements. Confirm the current structure of each target portal, implement `parse_listing()`, and dry-run before writing anything.
