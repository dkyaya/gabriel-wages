# Texas/Ohio Source-Expansion Selection — 2026-07-10

## Summary

**9 new causal sources selected for ingestion** — within the 6-12 target range. One new Texas city (San Antonio, unmatched safety pair, high institutional contrast value) and two new, fully matched Ohio cities (Cincinnati and Toledo), each with police + fire + non-safety, plus a bonus rank-split police row for Cincinnati. Full candidate list, including everything considered and not selected, is in `docs/analysis/texas_ohio_expansion_source_plan_2026-07-10.csv` (22 rows total).

## Selected sources

| # | state | city | role | title | cycle |
|---|---|---|---|---|---|
| 1 | TX | San Antonio | police | SAPOA Collective Bargaining Agreement | 2022-2026 |
| 2 | TX | San Antonio | fire | San Antonio Fire Fighters Association / IAFF Local 624 CBA | ~2024-2027 (to confirm from text) |
| 3 | OH | Cincinnati | police (non-supervisors) | FOP Queen City Lodge No. 69 Labor Agreement | 2024-2027 |
| 4 | OH | Cincinnati | police (supervisors) | FOP Queen City Lodge No. 69 Labor Agreement (Sergeant–Asst. Chief) | 2024-2027 |
| 5 | OH | Cincinnati | fire | IAFF Local 48 Labor-Management Agreement | 2023-2026 |
| 6 | OH | Cincinnati | non-safety | CODE (Cincinnati Organized & Dedicated Employees) CBA | 2025-2028 |
| 7 | OH | Toledo | police | Toledo Police Patrolman's Association (Local 10) Agreement | 2024-2026 |
| 8 | OH | Toledo | fire | Toledo Firefighters Local 92, IAFF, CBA | 2024-2026 |
| 9 | OH | Toledo | non-safety | AFSCME Ohio Council 8, Local 2058 (Main Unit) CBA | 2024-2027 |

All 9 URLs independently re-verified live this session (`curl -I`, 2026-07-10) — every one returns HTTP 200, `content-type: application/pdf`, from an official city-government domain (`sanantonio.gov`, `cincinnati-oh.gov`/`cincyweb.cincinnati-oh.gov`, `cdn.toledo.oh.gov`). No aggregator, union-hosted mirror, or login-required source among the 9 selected.

## Why selected

- **San Antonio (police + fire, unmatched):** San Antonio (population ≈1.4M) is below both Texas population thresholds (1.9M for compulsory fire arbitration, 1.5M for Chapter 146 non-safety bargaining), yet has adopted full Chapter 174 bargaining for **both** police and fire — the clearest available example of the same legal framework Houston uses, operating *without* Houston's population-triggered compulsion. This is genuine institutional contrast value or the report's Texas discussion, independent of whether a matched non-safety comparison exists. Per this run's explicit design principle ("If only safety rows are available for a Texas city, add them only if they are institutionally valuable and likely to support the report's Texas institutional contrast"), this qualifies.
- **Cincinnati (police ×2 + fire + non-safety, matched triad + bonus):** All four documents are hosted on one official city portal, giving a complete, clean matched triad in a second Ohio city, plus a rank-vs-supervisor police split (paralleling this project's existing Franklin Police Sergeants precedent) at negligible additional acquisition cost.
- **Toledo (police + fire + non-safety, matched triad):** A third complete Ohio institutional tier, again on one official portal, demonstrating Ohio's ORC 4117/SERB framework operates consistently across cities of varying size and administrative structure (Columbus, Cleveland, Cincinnati, Toledo all now represented).

## Not selected, and why

Full detail for every considered-but-not-selected row is in the source plan CSV; summary:

- **San Antonio non-safety:** re-searched live this session (not just relying on the 2026-07-08 scan) — found only a description of AFSCME San Antonio periodically "selecting representatives to sit at the table with management," which reads as a non-binding consultation/representation process, not a signed CBA. No specific document was located. Consistent with the prior scan's finding that San Antonio has no confirmed non-safety statutory bargaining channel. **Not force-added.**
- **Dallas (police/fire joint, non-safety):** the joint police+fire agreement is only confirmed via aggregator/Ballotpedia-hosted copies, not an official `dallascityhall.com` PDF — excluded per this run's provenance rule (avoid mirrors when an official source isn't confirmed). Non-safety wage-setting runs through a civil-service classification/pay system, not a negotiated CBA — excluded per the "no budget/pay-plan documents as causal rows" rule.
- **Fort Worth (police, fire):** current-cycle full CBA text was not directly located at a specific URL in the prior scan, and this session did not re-search Fort Worth live (time-bounded to the two selected states' top-priority candidates). A strong backup for a future session.
- **Fort Worth non-safety, El Paso (all tiers), Dallas non-safety:** no negotiated CBA found; only budget/pay-plan/civil-service systems or (El Paso) secondary-sourced/union-hosted-only material — excluded.
- **Toledo Police Command Officers' Association (TPCOA):** found and URL-located, but not independently re-verified with a live `curl` check, and not needed to satisfy this run's design goals (the core Toledo triad already does). Documented as a `backup` candidate for a future session rather than rushed into this batch.
- **Dayton (police, fire, non-safety):** relying on the 2026-07-08 scan only, not re-searched live this session; Dayton's non-safety DPSU agreement cycle (2020-2023 per the prior scan) is likely stale by now and would need reconfirmation. Documented as `backup`.
- **Akron (all tiers):** confirmed by the prior scan as the weakest-documented Ohio city; not explored further this session. Documented as `deferred`.

## Matched-design impact

- **Texas:** still only one fully matched city (Houston: police + fire + other). Austin remains police + fire + nurse_health (safety-adjacent, not general-municipal). San Antonio adds a second **unmatched** police+fire pair — genuinely useful for institutional contrast (Chapter 174-without-compulsion), but explicitly *not* a second matched triad. This run's own honest assessment, consistent with the prior scan's conclusion: **a second Texas matched triad is not achievable from currently-locatable public sources** without violating this run's design principles (no budget/pay-plan-as-causal-row, no unconfirmed-provenance sources). This should be stated plainly in the report, not implied away.
- **Ohio:** goes from 2 matched cities (Columbus, Cleveland) to **4** (adding Cincinnati and Toledo), each independently confirmed as a complete police+fire+non-safety triad on one official portal. This directly demonstrates Ohio's ORC 4117/SERB framework generalizes across differently-sized cities, addressing the overfitting concern the original multi-city scan was commissioned to check.

## Expected codify value

All 9 sources are ordinary base CBAs (no arbitration-award or fact-finding documents this batch), giving the next codify run continued opportunity to test the refined codebook's grievance-vs-interest-arbitration distinction (Ohio's ORC 4117.14(D)(1) impasse-to-conciliation pathway for police/fire vs. the conditional strike right for non-safety employees is a recurring, well-documented institutional split across all four Ohio cities now in the corpus) and the peer/comparator-wage-comparability attribute (no over-coding expected, consistent with every prior codify batch).

## Caveats

- San Antonio's exact fire-CBA cycle years are not yet confirmed from the document text itself (only from the URL's last-modified date, November 2024) — Task F's extraction pass must confirm the actual effective dates before `contracts.csv` is updated.
- Cincinnati's CODE and Toledo's AFSCME Local 2058 are both broad, potentially mixed-coverage non-safety units — per the recognition-clause-first standard, both are provisionally `occupation_class=other` pending a genuine recognition-clause read in Task F, not assumed narrower.
- No arbitration-award, fact-finding, or impasse documents were selected this batch (all 9 are base CBAs) — a documented gap, not an oversight; Ohio's SERB archive (referenced throughout the source plan CSV) remains a rich, not-yet-tapped source of such documents for a future session.
- This run adds no GABRIEL/codify coverage — these 9 sources become codify-ready only after this run's Task F (extraction) and Task G (schema-conformant `contracts.csv`/`city_coverage.csv` rows) are complete, and codify itself is explicitly out of scope for this run.
