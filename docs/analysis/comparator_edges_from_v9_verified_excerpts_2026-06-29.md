# Comparator Edges From v9 Verified Excerpts

**Date:** 2026-06-29

## 1. Purpose

This memo tests the comparator-network extraction rules on already quote-audited **causal-corpus** GABRIEL v9 evidence. It extracts a memo-only comparator edge list from verified relevant v9 excerpts that explicitly name comparator municipalities. It does not create `data/comparator_mentions.csv`, does not ingest documents, and does not make causal claims.

## 2. Source files reviewed

- [PROGRESS.md](/Users/joachimjohnson/Documents/RA_2026/Pol_Fire/gabriel-wages/PROGRESS.md)
- [docs/schema.md](/Users/joachimjohnson/Documents/RA_2026/Pol_Fire/gabriel-wages/docs/schema.md)
- [docs/hypotheses.md](/Users/joachimjohnson/Documents/RA_2026/Pol_Fire/gabriel-wages/docs/hypotheses.md)
- [docs/analysis/comparator_network_design_2026-06-29.md](/Users/joachimjohnson/Documents/RA_2026/Pol_Fire/gabriel-wages/docs/analysis/comparator_network_design_2026-06-29.md)
- [analysis/gabriel_pilot/results_v9.csv](/Users/joachimjohnson/Documents/RA_2026/Pol_Fire/gabriel-wages/analysis/gabriel_pilot/results_v9.csv)
- [analysis/gabriel_pilot/results_v9_quote_audit.csv](/Users/joachimjohnson/Documents/RA_2026/Pol_Fire/gabriel-wages/analysis/gabriel_pilot/results_v9_quote_audit.csv)
- [docs/acquisition/ma_boston_btu_salary_comparison_deep_dive_2026-06-29.md](/Users/joachimjohnson/Documents/RA_2026/Pol_Fire/gabriel-wages/docs/acquisition/ma_boston_btu_salary_comparison_deep_dive_2026-06-29.md)
- [reports/6_25/v2/GABRIELv9_preliminary.pdf](/Users/joachimjohnson/Documents/RA_2026/Pol_Fire/gabriel-wages/reports/6_25/v2/GABRIELv9_preliminary.pdf)

## 3. Eligibility rules

An excerpt was eligible for edge extraction only if all of the following held:

1. The source row is in the **causal corpus**.
2. The quote-audit status is `supporting_relevant`.
3. The excerpt is not marked failed, irrelevant, or ambiguous.
4. The excerpt explicitly names one or more comparator municipalities.
5. The named municipality is functioning as a comparator, not merely as the home city or a generic placeholder.

Applied here, that means:

- Somerville superior-officers award excerpt listing Arlington, Brookline, Cambridge, Lowell, Malden, Melrose, Newton, Quincy, and Waltham is eligible.
- Somerville patrol-officers award excerpt naming Boston is eligible.
- Arlington fire outside-detail language is **not** edge-eligible even though it is quote-audit accepted, because it refers to "that city's or Town's" current rate and includes the home municipality name only as part of "Town of Arlington," not as a named comparator city.

For this memo:

- `extraction_method = gabriel_verified_excerpt`
- `confidence = high` only when the comparator city is explicit in a verified relevant excerpt
- `verification_date = 2026-06-25` for v9 excerpt verification, based on the v9 run and quote-audit session recorded in `PROGRESS.md`
- `document_date = not_available` unless the underlying award date is established directly in the reviewed materials

## 4. Extracted comparator-edge table

| mention_id | source_obs_id | source_corpus | source_type | home_state | home_city | comparator_state | comparator_city | occupation_class | safety_flag | cycle_start | cycle_end | document_date | verification_date | comparison_dimension | quote | page_or_section | extraction_method | confidence | notes |
|---|---|---|---|---|---|---|---|---|---:|---|---|---|---|---|---|---|---|---|---|
| `v9_som_spsoa_arlington` | `ma_somerville_police_spsoa_2012` | `causal` | `arbitration_award` | `MA` | `Somerville` | `MA` | `Arlington` | `police` | 1 | `2012-07-01` | `2018-06-30` | `not_available` | `2026-06-25` | `general_comparability` | "Those communities chosen in the Collins Center classification study were Arlington, Brookline, Cambridge, Lowell, Malden, Melrose, Newton, Quincy, and Waltham." | `estimated_page=55` | `gabriel_verified_excerpt` | `high` | Separate edge created from one verified list excerpt. |
| `v9_som_spsoa_brookline` | `ma_somerville_police_spsoa_2012` | `causal` | `arbitration_award` | `MA` | `Somerville` | `MA` | `Brookline` | `police` | 1 | `2012-07-01` | `2018-06-30` | `not_available` | `2026-06-25` | `general_comparability` | "Those communities chosen in the Collins Center classification study were Arlington, Brookline, Cambridge, Lowell, Malden, Melrose, Newton, Quincy, and Waltham." | `estimated_page=55` | `gabriel_verified_excerpt` | `high` | Separate edge created from one verified list excerpt. |
| `v9_som_spsoa_cambridge` | `ma_somerville_police_spsoa_2012` | `causal` | `arbitration_award` | `MA` | `Somerville` | `MA` | `Cambridge` | `police` | 1 | `2012-07-01` | `2018-06-30` | `not_available` | `2026-06-25` | `general_comparability` | "Those communities chosen in the Collins Center classification study were Arlington, Brookline, Cambridge, Lowell, Malden, Melrose, Newton, Quincy, and Waltham." | `estimated_page=55` | `gabriel_verified_excerpt` | `high` | Separate edge created from one verified list excerpt. |
| `v9_som_spsoa_lowell` | `ma_somerville_police_spsoa_2012` | `causal` | `arbitration_award` | `MA` | `Somerville` | `MA` | `Lowell` | `police` | 1 | `2012-07-01` | `2018-06-30` | `not_available` | `2026-06-25` | `general_comparability` | "Those communities chosen in the Collins Center classification study were Arlington, Brookline, Cambridge, Lowell, Malden, Melrose, Newton, Quincy, and Waltham." | `estimated_page=55` | `gabriel_verified_excerpt` | `high` | Separate edge created from one verified list excerpt. |
| `v9_som_spsoa_malden` | `ma_somerville_police_spsoa_2012` | `causal` | `arbitration_award` | `MA` | `Somerville` | `MA` | `Malden` | `police` | 1 | `2012-07-01` | `2018-06-30` | `not_available` | `2026-06-25` | `general_comparability` | "Those communities chosen in the Collins Center classification study were Arlington, Brookline, Cambridge, Lowell, Malden, Melrose, Newton, Quincy, and Waltham." | `estimated_page=55` | `gabriel_verified_excerpt` | `high` | Separate edge created from one verified list excerpt. |
| `v9_som_spsoa_melrose` | `ma_somerville_police_spsoa_2012` | `causal` | `arbitration_award` | `MA` | `Somerville` | `MA` | `Melrose` | `police` | 1 | `2012-07-01` | `2018-06-30` | `not_available` | `2026-06-25` | `general_comparability` | "Those communities chosen in the Collins Center classification study were Arlington, Brookline, Cambridge, Lowell, Malden, Melrose, Newton, Quincy, and Waltham." | `estimated_page=55` | `gabriel_verified_excerpt` | `high` | Separate edge created from one verified list excerpt. |
| `v9_som_spsoa_newton` | `ma_somerville_police_spsoa_2012` | `causal` | `arbitration_award` | `MA` | `Somerville` | `MA` | `Newton` | `police` | 1 | `2012-07-01` | `2018-06-30` | `not_available` | `2026-06-25` | `general_comparability` | "Those communities chosen in the Collins Center classification study were Arlington, Brookline, Cambridge, Lowell, Malden, Melrose, Newton, Quincy, and Waltham." | `estimated_page=55` | `gabriel_verified_excerpt` | `high` | Separate edge created from one verified list excerpt. |
| `v9_som_spsoa_quincy` | `ma_somerville_police_spsoa_2012` | `causal` | `arbitration_award` | `MA` | `Somerville` | `MA` | `Quincy` | `police` | 1 | `2012-07-01` | `2018-06-30` | `not_available` | `2026-06-25` | `general_comparability` | "Those communities chosen in the Collins Center classification study were Arlington, Brookline, Cambridge, Lowell, Malden, Melrose, Newton, Quincy, and Waltham." | `estimated_page=55` | `gabriel_verified_excerpt` | `high` | Separate edge created from one verified list excerpt. |
| `v9_som_spsoa_waltham` | `ma_somerville_police_spsoa_2012` | `causal` | `arbitration_award` | `MA` | `Somerville` | `MA` | `Waltham` | `police` | 1 | `2012-07-01` | `2018-06-30` | `not_available` | `2026-06-25` | `general_comparability` | "Those communities chosen in the Collins Center classification study were Arlington, Brookline, Cambridge, Lowell, Malden, Melrose, Newton, Quincy, and Waltham." | `estimated_page=55` | `gabriel_verified_excerpt` | `high` | Separate edge created from one verified list excerpt. |
| `v9_som_spea_boston` | `ma_somerville_police_spea_2012` | `causal` | `arbitration_award` | `MA` | `Somerville` | `MA` | `Boston` | `police` | 1 | `2012-07-01` | `2015-06-30` | `not_available` | `2026-06-25` | `wages` | "The Union contends that Boston should be considered as comparable due to its close proximity, its population density, and the fact that it is faced with similar urban policing concerns. The Union argues that a review of its comparable communities shows that wages and benefits of Somerville Patrol Officers lag behind what is provided in these other communities." | `estimated_page=58` | `gabriel_verified_excerpt` | `high` | The excerpt names one comparator city directly and ties it to wage-and-benefit comparison. |

## 5. Non-edge comparability excerpts

Verified relevant comparability excerpts that did **not** produce edges:

| source_obs_id | quote_index | page_or_section | why it is not an edge | short note |
|---|---:|---|---|---|
| `ma_somerville_police_spsoa_2012` | 1 | `estimated_page=52` | comparator municipalities not named | General statement that Somerville superior officers compare well with counterparts in comparable communities. |
| `ma_somerville_police_spsoa_2012` | 3 | `estimated_page=56` | comparator municipalities not named | General total-compensation comparability statement. |
| `ma_somerville_police_spsoa_2012` | 4 | `estimated_page=62` | comparator municipalities not visible in excerpt | Chart heading refers to comparable communities but the municipalities themselves are not shown in the quote-audit excerpt. |
| `ma_somerville_police_spsoa_2012` | 5 | `estimated_page=54` | comparator municipalities not named | Defines the benchmark as comparable superior police officers in other places, but does not name cities. |
| `ma_somerville_police_spea_2012` | 2 | `estimated_page=60` | comparator municipalities not named | Refers to wage adjustments in surrounding communities without listing them. |
| `ma_somerville_police_spea_2012` | 3 | `estimated_page=76` | comparator municipalities not visible in excerpt | Longevity-pay chart heading is relevant but does not display named cities in the quoted text. |
| `ma_somerville_police_spea_2012` | 4 | `estimated_page=75` | comparator municipalities not named | Refers to other police departments in the comparable-community list without naming them in the excerpt. |
| `ma_arlington_fire_2021` | 1 | `estimated_page=20` | no explicit comparator municipality | Verified relevant comparability language for outside-detail rates, but it uses a generic other-city/other-town placeholder and does not yield a named city edge. |

## 6. Coverage summary

- v9 rows reviewed: `32`
- verified relevant excerpts in the causal quote-audit file: `10`
- verified relevant excerpts with named comparator municipalities: `2`
- extracted edges: `10`
- `source_obs_id` values contributing edges: `ma_somerville_police_spsoa_2012`, `ma_somerville_police_spea_2012`

## 7. Interpretation

The current v9 **causal** corpus supports a small but concrete named-city comparator edge list. At present, that support comes entirely from two Somerville police arbitration awards. One excerpt supplies a named Massachusetts comparator set for Somerville superior officers. Another explicitly identifies Boston as a comparator for Somerville patrol officers.

That means the named-city evidence in the causal v9 excerpt set is currently concentrated in **safety-side arbitration rows**, not in ordinary CBAs and not in non-safety causal rows. The broader v9 comparability signal is larger than this edge list, because several additional verified relevant excerpts discuss comparability, surrounding communities, or comparable departments without naming municipalities in the quoted text.

Boston BTU differs in two ways. First, it is **not** part of this causal-corpus edge list. Second, its strongest evidence is a verified mechanism-proxy bargaining page rather than an arbitration award or other causal reasoning document. It remains an important contrast case, but not part of the v9 causal extraction memo.

## 8. Recommended next step

Recommended next step: **manual extraction from the Boston BTU table**, using the cleaned date-field rules from the comparator-network design memo.

Why:

- the causal v9 edge list is now explicit and bounded;
- Boston is the clearest non-safety named-comparator case, but it sits in a mechanism-proxy lane;
- comparing the Somerville causal edges to a separately extracted Boston proxy table is the most informative next test before creating any stub CSV.

A tiny stub CSV can wait until both of those pieces are side by side. v10 design is not the immediate bottleneck for this extraction-specific step.
