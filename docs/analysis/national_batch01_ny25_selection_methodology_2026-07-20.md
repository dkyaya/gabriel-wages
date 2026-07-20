# New York 25-Municipality State-Scaling Scout Batch — Selection Methodology

Date: 2026-07-20

Stage: scout-input selection and dry-run preparation only. This method does not establish source availability, verify a document, run a live/model/API request, ingest a contract, update canonical coverage, codify text, or support a claim.

## Why New York is the next state

New York is the strongest next state-scale batch after Illinois in the existing local planning evidence. The untouched national manifest's next five high-priority claim targets are Buffalo, Rochester, Syracuse, Yonkers, and Albany at ranks 19–23. The same manifest contains five more New York replication cities—New York City, Utica, Schenectady, White Plains, and New Rochelle—so ten of the 25 rows already have explicit national-wave priority context. No other untouched state supplies an earlier five-city claim-target block plus this much same-state replication context. Washington, Oregon, California, Connecticut, Minnesota, and other candidate states remain useful later waves; New York is selected first because its manifest sequence is more immediately claim-connected and can support a complete city-only 25-row batch.

The state also supplies a high-value national contrast: the nation's largest municipal employer, several large legacy industrial and administrative cities, downstate suburban cities, and smaller upstate city governments. The selected rows span western New York, the Finger Lakes, central New York, the Mohawk Valley, the Capital Region, the Southern Tier, the North Country, the Hudson Valley, Westchester, and New York City's five borough counties. That gives population, administrative, regional, and government-scale contrast without using town/township governments or special districts.

Likely municipal labor-source availability is only a selection hypothesis here. It is based on the manifest's `ready_for_scout` status, government size, and the plausibility of multi-unit municipal employment; no source page or URL was opened to prove availability.

## Authoritative inputs and exclusions

1. `national_municipality_universe.csv` is the employer universe. Every row is a New York record with `government_type=municipal`, `geography_type=place`, and a `CITY OF ...` government name.
2. `national_scout_coverage_municipality_2026-07-20.csv` is the discovery-status gate. All 25 rows are `not_scouted`, have zero failed request attempts, and are neither successful coverage nor failure-only rows. Bloomington IL is outside both the selected state and this batch and is not retried.
3. `national_municipality_county_crosswalk.csv` supplies all county relationships. The input preserves 29 relationships: 24 single-county cities and New York City's five borough-county relationships.
4. `next_wave_municipality_scout_manifest_2026-07-16.csv` supplies priority and claim context for ten rows. Supplemental rows broaden state coverage rather than limiting the batch to the 100-row national manifest.
5. The national scout queue and current canonical-overlap fields were checked locally at municipality level. None of the 25 has a queue row or canonical-corpus overlap. No source URL was opened and no source/cycle exclusion was invented.

The batch excludes counties, towns/townships, villages, school districts, MTA/transit entities, housing authorities, park districts, universities, regional bodies, fire/water and other special districts, and private providers as target employers. County names remain geography context only. This is especially important in New York, where city, town, village, county, authority, and district employers can share place names or service areas.

## Selection buckets

| Bucket | Count | Role |
|---|---:|---|
| `claim_register_anchor` | 5 | Buffalo, Rochester, Syracuse, Yonkers, and Albany—the next five untouched high-priority manifest targets. |
| `large_city_state_anchor` | 3 | New York, New Rochelle, and Mount Vernon for very-large and downstate city-employer contrast. |
| `mid_city_comparison_candidate` | 6 | Utica, Schenectady, White Plains, Troy, Niagara Falls, and Binghamton. |
| `regional_diversity_candidate` | 7 | Poughkeepsie, Newburgh, Middletown, Ithaca, Saratoga Springs, Watertown, and Kingston. |
| `clean_municipal_employer_candidate` | 4 | Jamestown, Elmira, Rome, and Auburn as smaller city-government comparisons. |
| **Total** | **25** | |

Selection favored population and administrative importance; plausible police/fire/ordinary-civilian comparison value; geographic and county diversity; likely source discoverability as an unverified scouting hypothesis; safety/non-safety wage-gap and bargaining-mechanism relevance; and a mix of large, medium, and smaller city employers. The population range is 23,777 in Kingston to 8,258,035 in New York City. Every employer is a city; no town/township or village required an exception.

## Ordered batch

The locked order is: Buffalo, Rochester, Syracuse, Yonkers, Albany, New York, Utica, Schenectady, White Plains, New Rochelle, Mount Vernon, Troy, Niagara Falls, Binghamton, Poughkeepsie, Newburgh, Middletown, Ithaca, Saratoga Springs, Watertown, Kingston, Jamestown, Elmira, Rome, and Auburn.

Each row asks for police, fire, one ordinary general-municipal/civilian non-safety agreement, and public arbitration/factfinding/impasse or other wage-setting mechanism material where available. Because no selected city has local canonical or queued source-cycle context, the prompt asks for visibly supported, mutually overlapping 2014–2024 cycles rather than pretending that a canonical repair anchor exists. Non-overlap and weak year evidence must remain labeled, and an empty candidate list is acceptable.

## Reproducibility and stage boundaries

`scripts/build_national_batch01_ny25_scout_input.py` rebuilds the input from the four authoritative planning tables plus the queue. It asserts the exact order, controlled bucket counts, municipal/place/city identity, unique IDs, untouched coverage state, zero failed attempts, no queue row, no canonical overlap, and complete county counts before writing and parsing the CSV back.

All future output remains unverified scout-stage lead data. If a separately authorized live run later occurs, preserve every raw/failure/usage artifact, add candidates to the durable queue without opening every URL, count parseable empty responses as discovery coverage, exclude failure-only attempts, and rebuild municipality/state/county scout accounting. Verification, ingestion, codification, and claim use remain separate later stages.
