# PA/NJ Source Scan Summary and Recommended Ingestion Batch — 2026-07-12

This is a scan summary only. No sources were downloaded, ingested, or codified in this run. See `docs/analysis/pa_nj_source_scan_preflight_2026-07-12.md` for constraints, `docs/analysis/pa_nj_candidate_sources_2026-07-12.csv` for all 40 candidate rows, and the two state memos (`pennsylvania_source_scan_2026-07-12.md`, `new_jersey_source_scan_2026-07-12.md`) for full detail.

## Which state looks more immediately ingestible

**New Jersey**, primarily because of one structural fact: PERC (the state Public Employment Relations Commission) maintains a centralized, statutorily-mandated public index of essentially all municipal collective negotiations agreements *and* a separate police/fire interest-arbitration-awards index. Pennsylvania has no equivalent centralized index in this scan's findings — every PA city required a separate ad hoc search, and provenance was more mixed (one Pittsburgh candidate is only third-party-hosted on Scribd).

Pennsylvania is not far behind on a per-city basis, however: Philadelphia alone has a stronger, more complete set of directly-linked documents (including two city-government-hosted arbitration awards) than any single New Jersey city produced in this scan, Newark included. The state-level recommendation favors NJ; the single strongest *city* found in this scan is arguably Philadelphia.

## Best candidate cities

**Pennsylvania:** Philadelphia (strong triad, mixed city/union provenance) > Reading (best confirmed non-safety document in PA, but police leg is a total gap) > Pittsburgh ≈ Allentown (partial leads, no confirmed non-safety CBA) > Erie (weakest; only case-law confirmation of an award, no direct documents).

**New Jersey:** Newark (only city with a directly retrievable non-safety document, plus confirmed police/fire units) > Jersey City ≈ Paterson ≈ Elizabeth (confirmed bargaining units for all legs, but no document-level source without a PERC-index follow-up) > Trenton (least distinct evidence).

## Recommended first ingestion batch (6-12 sources)

**This scan does not recommend ingesting yet.** Per the two-week plan's decision gates, ingestion should wait for bounded criteria to be met (public, clear provenance, safety and non-safety units locatable, recognition clauses support classification) and for a short, targeted follow-up pass to convert `needs_review` rows into confirmed document-level candidates — especially via the NJ PERC index, which this scan identified but did not browse city-by-city.

If/when that follow-up confirms the leads below, this is the recommended first batch (8 sources, 2 matched triads):

| # | State | City | Role | Candidate | Row selection_priority |
|---|-------|------|------|-----------|------------------------|
| 1 | PA | Philadelphia | police | FOP Lodge 5 contracts page / Act 111 award | ingest_next |
| 2 | PA | Philadelphia | fire | IAFF Local 22 consolidated CBA | ingest_next |
| 3 | PA | Philadelphia | fire (arbitration) | City-hosted IAFF Local 22 interest-arbitration award | ingest_next |
| 4 | PA | Philadelphia | non_safety_general | AFSCME DC33 (pending confirmation of signed CBA) | needs_review — confirm before ingest |
| 5 | PA | Reading | non_safety_general | Reading Public Library CBA | ingest_next |
| 6 | NJ | Newark | non_safety_general | City of Newark and IBT Local 97 CBA (2020) | ingest_next |
| 7 | NJ | Newark | police | Newark PBA / Superior Officers CBA (via PERC index) | needs_review — confirm before ingest |
| 8 | NJ | Newark | fire | Newark Firefighters Union / Fire Officers Local 1860 CBA (via PERC index) | needs_review — confirm before ingest |

Rows 1, 2, 3, 5, and 6 are already `ingest_next` in the candidate CSV (document-level, public, clear provenance). Rows 4, 7, and 8 require one more targeted lookup (confirm a signed, not proposed, Philadelphia AFSCME CBA; resolve the two Newark PERC-index entries to actual CBA PDFs) before they should move from `needs_review` to `ingest_next`. This batch would complete a Philadelphia triad and a near-complete Newark triad.

## Which hypotheses/claims the batch would test

- `H1` (safety pressure + conversion channels), `H2` (safety formal impasse/arbitration backstops vs. non-safety), `H4` (minimum-staffing/overtime/premium centrality) — served by the Philadelphia police/fire CBAs and the two arbitration awards.
- `H3` (non-safety routes through classification/admin channels) — served by Philadelphia AFSCME and the Newark IBT Local 97 CBA.
- `H7` (Ohio-style matched-triad design generalizes) — directly tested by adding two new matched-triad states/cities outside the current MA/TX/OH corpus.
- `H5` / `CLM-2026-07-12-07` (peer/comparator wage evidence, currently `urgent` priority and only weakly supported) — the two city-hosted Philadelphia arbitration awards and, pending follow-up, the NJ PERC interest-arbitration-awards index are the most promising leads found in this scan for strengthening this specific claim.
- `CLM-2026-07-12-01` (Ohio-style impasse/arbitration pattern) and `CLM-2026-07-12-06` (interest vs. grievance arbitration distinction) — both would gain a second and third state of evidence beyond Ohio.

## What gaps remain

- No confirmed non-safety document for Pittsburgh, Allentown, Erie, Jersey City, Paterson, Elizabeth, or Trenton — seven of ten scanned cities. The non-safety bottleneck flagged in the national plan is fully reproduced at the PA/NJ level.
- No confirmed document-level police or fire source for Erie (PA) or Trenton (NJ) — the weakest city in each state.
- Provenance verification still needed for the one third-party-hosted (Scribd) Pittsburgh candidate before it should ever be treated as ingest-ready.
- Recognition-clause review is still required (per the recognition-clause-first standard) for both the Philadelphia AFSCME and Newark IBT Local 97 candidates before either is assigned a specific non-safety `occupation_class` — both are correctly recorded as `other` (provisional) in the CSV.
- The NJ PERC index itself was identified but not browsed city-by-city in this scan; the single biggest unlock for New Jersey is a short follow-up pass through that index for Jersey City, Paterson, Elizabeth, and Trenton.

## Should Illinois/New York be scanned before ingesting?

**No — recommend running the follow-up PERC-index lookup and the Philadelphia AFSCME confirmation first, then ingesting the batch above, before starting an Illinois/New York scan.** Both PA and NJ already have at least one near-complete matched triad identified; spending the next session on Illinois/New York now would add scanning breadth before the two-week plan's own decision gate is satisfied ("promote a state if it offers clean matched triads and institutional contrast" — PA and NJ already clear this bar pending the confirmations above). Illinois and New York remain tier-1 states in `national_state_priority_rubric_2026-07-12.csv` and should be the next scan immediately after this batch is reviewed and ingested, not before.
