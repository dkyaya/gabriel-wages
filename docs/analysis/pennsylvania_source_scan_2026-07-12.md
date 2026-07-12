# Pennsylvania Source Scan — 2026-07-12

Scope: bounded, public-web source-availability scan. No downloads, no ingestion, no codify. See `docs/analysis/pa_nj_source_scan_preflight_2026-07-12.md` for constraints and `docs/analysis/pa_nj_candidate_sources_2026-07-12.csv` for the full candidate list (21 Pennsylvania rows).

## Cities scanned

Philadelphia, Pittsburgh, Allentown, Erie, Reading.

## Strongest candidate matched cities

**Philadelphia is the clear PA leader.** All three legs of a matched triad have document-level or near-document-level candidates:
- Police: FOP Lodge 5 contracts page (`fop5.org/contracts/`) plus a city-hosted Act 111 award announcement on `phila.gov`.
- Fire: an IAFF Local 22 consolidated-contract PDF plus a city-hosted interest-arbitration award on `phila.gov`.
- Non-safety: AFSCME District Council 33 (blue-collar) and District Council 47 (white-collar) both represent City of Philadelphia employees, though this scan located a contract *proposal* rather than a confirmed signed CBA PDF — marked `needs_review`, not `ingest_next`.

Philadelphia is the only PA city in this scan with city-government-hosted (not just union-hosted) arbitration award documents for both police and fire, which is unusually strong provenance.

**Reading produced the strongest single non-safety document found anywhere in Pennsylvania**: a directly retrievable Reading Public Library CBA PDF on the city's own domain (`readingpa.gov`), plus council-minutes confirmation of a 2023-2026 AFSCME Local 2763 general-employee CBA (document link not yet located). Reading's police leg is currently a complete gap — no FOP lodge document surfaced at all.

Pittsburgh and Allentown each have plausible but unconfirmed triads: Pittsburgh's police CBA is only found third-party-hosted (Scribd), its fire leg is context-only, and its non-safety leg is inferred from a budget-appendix reference to AFSCME Local 2719 rather than a CBA. Allentown has city-confirmed police and union-hosted fire leads but no non-safety source at all.

Erie is the weakest PA city scanned: only case-law references confirming that a police Act 111 award exists (FOP Lodge 7 / Haas Memorial Lodge), a fire union contact page with no contract link, and no non-safety source. Note: an early search on "Erie" surfaced Erie **County, New York** labor-relations documents (`erie.gov`) — a jurisdiction false positive, explicitly excluded and documented in the candidate CSV so it is not mistaken for Erie, PA in a future run.

## Non-safety availability

Non-safety (AFSCME/general-municipal) is the binding constraint in Pennsylvania, consistent with the national plan's stated bottleneck. Only Reading produced a directly downloadable non-safety document (the library CBA); Philadelphia and Pittsburgh have confirmed non-safety unions and partial evidence but no confirmed signed-CBA PDF; Allentown and Erie have no non-safety candidate at all.

## Arbitration / factfinding availability

Pennsylvania's Act 111 (binding interest arbitration for police/fire, no strike right) is well-documented as a statewide institutional mechanism, and the Pennsylvania Labor Relations Board (PLRB) administers related unfair-practice/representation matters. However, unlike New Jersey, this scan did not find a single centralized, browsable PLRB index of Act 111 awards by city — award documents were found city-by-city (Philadelphia via `phila.gov`; Erie only via case law referencing an award, not the award itself). This raises expected search/ingestion burden for PA relative to NJ.

## Source-owner / provenance notes

- Philadelphia: mixed city-government (`phila.gov`) and union-hosted sources — the strongest provenance mix in PA.
- Pittsburgh: one candidate hosted on a third-party document-sharing site (Scribd) rather than an official domain — provenance needs verification before any future ingestion.
- Reading: city-domain-hosted (`readingpa.gov`) for both the library CBA and the AFSCME minutes reference — good provenance.
- Allentown and Erie: mostly union or city-news-page references without direct contract PDFs.

## Likely ingestion burden

- **Philadelphia: low-medium.** Most documents are already linked; the main remaining work is confirming a signed (not proposed) AFSCME CBA.
- **Reading: low** for the two confirmed non-safety documents; **high** for police, which is a complete unlocated gap.
- **Pittsburgh, Allentown, Erie: medium-high.** Each requires additional direct searching of city HR/council-agenda pages beyond what surfaced in this web-search-only scan; none has a confirmed non-safety document.

## Recommended next action

1. Do not ingest yet. First verify (in a short, targeted follow-up, still without downloading into corpus) that the Philadelphia AFSCME DC33/DC47 signed CBA and the Reading AFSCME 2763 CBA can be located as direct documents.
2. If confirmed, Philadelphia is ready for a reviewed ingestion pass first; Reading's library CBA can be ingested as a standalone non-safety comparator once a matched Reading safety document is found.
3. Pittsburgh, Allentown, and Erie need another round of targeted city-HR-page searching before they are ingestion-ready; none should be promoted ahead of Philadelphia.

## Promote for ingestion?

**Conditionally yes — Philadelphia only, pending non-safety CBA confirmation.** Pennsylvania as a whole is not yet ready for a full ingestion batch; only Philadelphia currently has a plausible complete triad with acceptable provenance. See `docs/analysis/pa_nj_source_scan_summary_2026-07-12.md` for the cross-state recommendation.
