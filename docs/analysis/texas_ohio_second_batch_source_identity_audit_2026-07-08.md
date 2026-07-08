# Texas/Ohio Second-Batch Source Identity Audit — 2026-07-08

This audit reviews the single newly fetched source from this session's held-out-target resolution: the Austin fire CBA. No GABRIEL, Harvard Proxy, model/API, PRR, FOIA, context-only, budget/pay-plan, statute, or SERB-archive ingestion calls were made.

## tx_austin_fire_2023

- Stored path: `corpus/tx_austin/tx_austin_afa975_fire_cba_2023_2025.pdf`
- Source identity verdict: **confirmed**
- City: Austin, TX
- Union/unit: Austin Firefighters Association, Local 975 of the International Association of Fire Fighters, AFL-CIO-CLC
- Employer/jurisdiction: City of Austin
- Document type: cba / labor agreement
- Agreement/cycle years visible: term runs through September 30, 2025 (Article 30 Section 1); earliest textually-anchored date is a wage-increase pay period beginning September 24, 2023, referencing a predecessor "2017-22 Agreement"; the officially posted austintexas.gov page separately labels this document's effective start as September 8, 2023, though that exact date string is not independently visible inside the extracted text (only inferable from the page label and the September 24, 2023 pay-period anchor).
- Text quality observed: clean (100-page text layer via `ingest/extract_text.py`, `method=text_layer`)
- Mismatch from resolved target: none requiring rejection. This is the document the official austintexas.gov labor-relations page itself verbatim-labels the "Current Agreement," distinct from ~24 separate negotiation-process documents (redlines, proposals, ground rules) for a still-in-flight successor.
- Add to `data/contracts.csv`: **yes**
- Caveat: A Dec. 18, 2025 successor agreement was reportedly ratified by City Council (per KUT and Community Impact reporting) but is posted as a set of separate bargaining-session/redline documents, not one clean executed copy; the officially labeled "Current Agreement" full-text document was used instead, consistent with this project's preference for a single clean executed CBA text over a redline/negotiation-artifact set.
- Preamble excerpt: "This Agreement is made between the City of Austin, Texas, hereinafter referred to as the 'City,' and the Austin Firefighters Association, Local 975 of the International Association of Fire Fighters, AFL-CIO-CLC, hereinafter referred to as the 'Association.'"
- Recognition excerpt (Article 3): "The City recognizes the Association as the sole and exclusive bargaining agent for all Fire Fighters pursuant to Local Government Code Section 174.101. Recognition of the Association as the exclusive bargaining agent does not make the Association a necessary party to disciplinary agreements between an individual Fire Fighter and the Fire Chief."
- occupation_class: `fire` (single-occupation firefighters' bargaining unit; no recognition-clause-first ambiguity — this is not a broad/bundled non-safety unit).

## Sources reviewed but not fetched (context only per Task B/C)

No identity audit is required for unfetched sources. See `texas_ohio_heldout_source_resolution_2026-07-08.csv` for Houston fire (unresolved), Austin AFSCME 1624 (resolved but confirmed non-causal), Austin/Cleveland budget-pay-plan pages, and the Ohio SERB archive (all resolved_context_only, none fetched or stored).
