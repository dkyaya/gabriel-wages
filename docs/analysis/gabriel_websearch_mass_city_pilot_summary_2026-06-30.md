# GABRIEL Web-Search Massachusetts City Pilot Summary

**Date:** 2026-06-30  
**Status:** design/seed only; web-search function not executed

## 1. Purpose

This pilot defines a small city-by-city source-discovery and evidence-extraction workflow for Massachusetts municipal labor and wage-setting sources. It is intended for a Thursday discussion with the GABRIEL toolkit creator about whether GABRIEL web search can help discover public sources, classify them, extract short evidence spans, and assign multiple wage-mechanism attributes.

This is not an ingestion task, not a production empirical dataset, and not a causal analysis.

## 2. What Was Tested

The pilot artifacts test the intended shape of a GABRIEL web-search output:

- source discovery by city and query;
- source-level classification into causal, mechanism-proxy, discourse, lead-only, or not-corpus lanes;
- short source-level evidence observations;
- five wage-mechanism attributes: `comparability_emphasis`, `arbitration_or_impasse_backstop`, `wage_reasoning_density`, `named_comparator_signal`, and `source_ingestability`.

The retained source candidates are deliberately bounded: 5 cities, 15 source candidates, and 34 extraction rows.

## 3. Web-Search Function Availability

No local GABRIEL web-search function was found or executed.

Local inspection found:

- `analysis/gabriel_pilot/` contains GABRIEL scoring runners for local input CSVs, including v8/v9 comparability scoring and v10 gold-set dry-runs.
- Those runners call the OpenAI API on already assembled local text. They do not expose a city/query web-search interface and do not return search-result URLs or snippets.
- `ingest/fetchers/` contains open-source fetcher scaffolding, not GABRIEL web search. The only concrete fetcher is a Cornell ILR skeleton whose `parse_listing()` intentionally raises `NotImplementedError` until live DOM selectors are confirmed.
- No local script was found that supports city/query input, search-result ranking, public URL discovery, multi-attribute extraction, or safe search execution.

Because the callable web-search function was unavailable, the CSVs created here are manually seeded from already known public-source leads in repo notes and existing corpus metadata. They are labeled as design/seed outputs and should not be read as search results.

## 4. Cities Searched

The pilot scope is structured around five Massachusetts cities:

- Boston
- Somerville
- Newton
- Wayland
- Seekonk

Each city has three retained seed source candidates, for 15 total rows in `docs/acquisition/gabriel_websearch_mass_city_pilot_sources_2026-06-30.csv`.

## 5. Query Strategy

The pilot query set is designed for small city-by-city execution:

- police CBA, police contract, police arbitration, JLMC, MOA;
- fire CBA, fire contract, fire arbitration, JLMC, MOA;
- teacher contract, school committee bargaining, union bargaining materials;
- public works, DPW, library, clerical, administrative contracts;
- factfinding, mediation, impasse, arbitration award;
- salary comparison, peer districts, comparable communities, surrounding districts;
- budget presentation, school committee contract presentation, fiscal impact memo.

The seed file keeps this bounded at three retained candidates per city. A live GABRIEL search test should cap results before extraction, rather than crawling broadly.

## 6. Source-Discovery Results

The seed source table contains 15 retained candidates:

| City | Retained candidates | Main source families |
| --- | ---: | --- |
| Boston | 3 | BPS/BTU bargaining page, BTU CBA presentation, BPS salary-grid/CBA index |
| Somerville | 3 | police JLMC/arbitration packets, SEU settlement summary |
| Newton | 3 | NTA package comparison, NPS mediation proposal, final MOA lead |
| Wayland | 3 | fire JLMC stipulated award, police CBA, DPW CBA |
| Seekonk | 3 | official police, DPW, and teacher CBA archive PDFs |

Source-type mix:

- 5 ordinary CBAs;
- 2 arbitration-award packets;
- 1 stipulated award;
- 1 MOA lead;
- 1 mediation proposal;
- 3 bargaining updates or settlement summaries;
- 1 school-committee presentation;
- 1 salary-grid/CBA index.

Public-access issues are handled conservatively. Google Drive links and third-party FOIA releases are treated as public leads but not automatically ingested. Index pages are lead-only unless a specific public document is verified later.

## 7. Evidence-Extraction Results

The extraction CSV contains 34 rows:

- Boston BTU shows high `comparability_emphasis` and high `named_comparator_signal`, but `arbitration_or_impasse_backstop` remains none because peer-wage comparison alone is not an impasse backstop.
- Somerville police award packets are calibration positives for both comparability and arbitration/impasse backstop.
- Newton materials are mechanism-proxy or lead-only unless a clean final causal document is manually verified later.
- Wayland fire JLMC is a positive arbitration/impasse calibration source; Wayland DPW is retained as an ordinary-CBA exclusion example.
- Seekonk official CBAs are strong source-ingestability examples, but ordinary grievance arbitration remains near-zero v10 evidence.

## 8. Known-Source Calibration

Because web search was not executable, the pilot did not rediscover known sources autonomously. It seeded known calibration targets so a future executable search run can be evaluated against them.

Calibration expectations:

- Boston BPS/BTU negotiations page: included as `gws_boston_001`; expected high comparability and named-comparator signal, no v10 arbitration/impasse score from peer comparison alone.
- Somerville police arbitration/JLMC packets: included as `gws_somerville_001` and `gws_somerville_002`; expected high comparability and high arbitration/impasse signal.
- Newton teacher bargaining materials: included as `gws_newton_001`, `gws_newton_002`, and `gws_newton_003`; expected mechanism-proxy or manual-review status unless a final source is provenance-complete.
- Wayland fire JLMC: included as `gws_wayland_001`; expected high arbitration/impasse signal.
- Seekonk public official CBA archive PDFs: included as `gws_seekonk_001` through `gws_seekonk_003`; expected high source-ingestability but low wage-reasoning density and low arbitration/impasse signal unless specific impasse evidence appears.

## 9. Best New Leads

No new leads were generated because no live web-search function was executed. The best seeded leads for a future live test are:

- Boston BPS/BTU negotiations page as a non-safety peer-wage mechanism-proxy calibration source.
- Newton NPS mediation proposal as an impasse-process edge case that should not be treated like a final award.
- Seekonk official archive PDFs as a clean small-town CBA discovery and source-ingestability check.

## 10. Failure Modes to Test

A future live GABRIEL web-search run should be evaluated for these failure modes:

- returning index pages without direct public documents;
- ranking agenda or meeting-list pages above actual source documents;
- producing snippets with no real wage-mechanism evidence;
- treating ordinary grievance arbitration as interest arbitration or impasse resolution;
- treating peer-wage comparison alone as arbitration/impasse evidence;
- failing to distinguish causal-corpus candidates from mechanism-proxy or discourse materials;
- over-relying on news articles when primary public documents exist;
- being unable to access full text due to blocked pages, JavaScript barriers, or file-hosting limits.

## 11. Recommendation

This design is useful as an acquisition-assistant test harness, but it is not a validated search result. The next step is a controlled live GABRIEL web-search run, if the toolkit creator can expose the web-search function or provide invocation instructions.

Recommended live test constraints:

- use the five pilot cities only;
- keep up to six queries per city;
- retain no more than ten candidate sources per city;
- extract no more than three short evidence spans per source;
- separate causal, mechanism-proxy, discourse, lead-only, and not-corpus classifications;
- do not ingest any source without a later manual ingestion task.

The pilot should expand city by city only after the live function proves it can recover the seeded calibration sources without confusing grievance arbitration, peer-wage comparison, and formal impasse backstops.
