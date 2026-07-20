# Illinois 25-Municipality State-Scaling Scout Batch — Selection Methodology

Date: 2026-07-20

Stage: scout-input selection and dry-run preparation only. This method does not establish source availability, verify a document, ingest a contract, update canonical coverage, codify text, or support a claim.

## Purpose

`national_batch01_il25_scout_input_2026-07-20.csv` replaces the earlier three-city Illinois preparation as the proposed first 25-row state-scale discovery batch. It keeps the three already prepared claim-register targets at the head of the batch and widens the scan across municipal labor markets before any coordinated verification wave.

The input is a bounded discovery sample, not an Illinois representative sample or a verified source inventory. A successful future model response would only mean that a bounded discovery prompt completed; it would not establish the returned URL's employer, unit, ownership, execution, dates, wage content, or comparator value.

## Authoritative inputs and exclusion rule

1. `national_municipality_universe.csv` is the authoritative employer universe. The batch draws only Illinois records where `government_type=municipal` and `geography_type=place`.
2. `national_scout_coverage_municipality_2026-07-20.csv` is the source-discovery accounting input. Every selected municipality has `scout_coverage_status=not_scouted`; none is already counted as scout-covered.
3. `national_municipality_county_crosswalk.csv` supplies all municipal-county relationships. The input preserves the complete county-context summary rather than selecting only a primary county.
4. `next_wave_municipality_scout_manifest_2026-07-16.csv` supplies claim-driven priority context. Its five Illinois targets—Chicago, Aurora, Rockford, Springfield, and Naperville—are retained, but the batch is deliberately not limited to the 100-row national manifest.
5. The existing national queue and canonical contract table were checked only for city-level duplicate context. No selected Illinois municipality has a current queue row or canonical contract row; no source URL was opened.

Township governments are excluded even when they share a place name with a selected city. Counties, school districts, park districts, transit agencies, housing authorities, special districts, universities, regional bodies, airport/transit police, and private providers are excluded as substitute employers. The input's prompt context repeats these boundaries for each row.

## Selection criteria

The 25 rows use five controlled selection buckets:

| Bucket | Count | Selection role |
|---|---:|---|
| `claim_register_anchor` | 5 | The five Illinois manifest targets, led by the already prepared Chicago/Aurora/Rockford trio. |
| `large_city_state_anchor` | 7 | Large unscouted municipal employers in central, northern, lakeshore, Fox Valley, and Will County settings. |
| `mid_city_comparison_candidate` | 6 | Mid-sized incorporated city/village employers that broaden the Chicago-region administrative comparison set. |
| `regional_diversity_candidate` | 5 | Central, south-suburban, Metro East, Quad Cities, and southern Illinois settings. |
| `clean_municipal_employer_candidate` | 2 | Smaller western/southern city governments for scale and potentially cleaner employer-boundary contrast. |

Within those buckets, selection favored: population and administrative importance; plausible police/fire/ordinary-civilian comparability given the government scale; county and regional diversity; likely public municipal labor-document availability as a scouting hypothesis; relevance to the safety/non-safety wage-gap design; and a mix of large, medium, and smaller municipal employers. These are selection heuristics, not source-verification findings.

The final batch has 25 distinct municipal employers, including 15 distinct primary counties and multi-county governments where the Census crosswalk records them. Its population range is 21,592 (Carbondale) to 2,664,452 (Chicago). `TOWN OF NORMAL` is retained because Census classifies it as a `municipal` `place` government; it is not a township government.

## Ordered batch

The first three rows preserve the prior Illinois checkpoint exactly in employer identity and priority: Chicago, Aurora, and Rockford. The remaining rows are: Springfield, Naperville, Joliet, Elgin, Peoria, Champaign, Waukegan, Bloomington, Decatur, Evanston, Schaumburg, Bolingbrook, Palatine, Skokie, Des Plaines, Orland Park, Tinley Park, Normal, Belleville, Moline, Carbondale, and Quincy.

Each row requests police, fire, and one ordinary municipal/civilian non-safety agreement, plus public impasse/arbitration/factfinding material where available. Because no selected municipality has a canonical anchor cycle in the current repository, the prompt asks for an internally matched police/fire/non-safety set with visibly supported overlapping operative cycles in 2014–2024. It labels non-overlap or unclear evidence rather than asserting a completed repair.

## Stage boundaries and future handling

All expected output remains unverified scout-stage lead data. A future live run may produce candidates, a parseable empty list, or an infrastructure failure; these are different discovery-accounting outcomes. It must not be interpreted as verification, ingestion, canonical coverage, codification, or claim support.

After a separately authorized and successful live batch:

1. Preserve the raw run, prompt preview, metadata, parsed candidates, failure ledger, and usage artifacts.
2. Add only the returned candidate CSV and run metadata to the national queue/coverage builders; do not open every URL.
3. Treat a parseable empty output as scout coverage, not proof of source absence, and keep connection-only failures excluded from successful coverage.
4. Rebuild the durable candidate queue first, then municipality/state/county discovery coverage.
5. Defer source verification to a later coordinated matched-set wave; defer ingestion, codification, and claim use further still.
