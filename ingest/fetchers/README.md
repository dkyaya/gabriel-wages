# Fetchers — open sources only

Programmatic pulls for GENUINELY PUBLIC portals. Licensed sources
(Westlaw/Lexis/Bloomberg) and FOIA material do NOT belong here — they go
through `inbox/` + `process_inbox.py`, because automated extraction violates
those services' terms of use.

## Adding a fetcher

1. Subclass `BaseFetcher`, set `name` and `source_url_or_cite`.
2. Implement `discover()` to return `FetchItem`s.
3. Implement `parse_listing(html)` against the CURRENT live DOM. The provided
   `CornellILRFetcher.parse_listing` raises `NotImplementedError` on purpose —
   confirm selectors on the live page before writing it, so the fetcher fails
   loudly rather than scraping wrong elements.
4. Always `dry_run=True` first; inspect `logs/fetch_*.json`.

## Politeness

`BaseFetcher` sends a descriptive User-Agent and sleeps `POLITE_DELAY_S`
between downloads. Respect each portal's robots.txt and rate limits; these
are public research resources.

## Candidate open targets

- Cornell ILR Union Contract Collection (digitalcommons.ilr.cornell.edu)
- State PERB / PERC sites (NJ PERC, NY PERB, MA DLR, CA PERB) — many post
  awards and fact-finding decisions as PDFs
- DOL OLMS CBA file collection
- Municipal clerk / union-local sites for individual contracts
