# Oversized Source Handling Plan

Date: 2026-07-24

## Current exception pool

The cumulative routing ledger contains **261 `too_large` outcomes**. These
responses crossed the normal 10 MiB bounded-routing ceiling. They were not
downloaded into the corpus and were excluded from the ordinary first
content-triage batch.

`too_large` is an operational handling status, not evidence that the source is
irrelevant, invalid, or non-extractable.

## Why not raise the global ceiling

A blanket increase would expose every ordinary routing/content lane to greater
bandwidth, storage, memory, decompression, malformed-file, retry, and artifact
audit burden. Some large locators may be portals, archives, scans, or
unexpected downloads rather than high-value agreements. The correct response
is a separate allowlisted strategy after source priority and expected type are
known.

## Future bounded options

1. **HEAD-only or manual metadata review.** Use existing response metadata,
   title, source owner, and domain to determine whether further handling is
   justified.
2. **Targeted larger cap.** Permit a higher ceiling only for official,
   high-priority PDF/document candidates on an audited allowlist.
3. **Streamed PDF metadata pass.** Read bounded headers/trailers or page-count
   metadata without loading a full document into memory or parsing wage data.
4. **Separate oversized lane.** Use lower concurrency, explicit batch-byte
   limits, checksums, quarantine, and resumable streaming.
5. **Manual archival route.** If the locator is a giant portal or aggregate
   download, identify a document-level public route through manual review.

Before any future run, define per-file and total-batch byte ceilings, accepted
content types, archive/decompression policy, storage/quarantine paths, resume
rules, and artifact checksums. Licensed or authenticated sources must continue
through their permitted manual/manifest path.

No oversized URL was opened, no cap was raised, and no source was downloaded,
parsed, OCRed, ingested, codified, or extracted in this task.
