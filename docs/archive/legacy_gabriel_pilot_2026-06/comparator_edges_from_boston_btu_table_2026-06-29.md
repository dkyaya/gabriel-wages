# Comparator Edges From Boston BTU Table

**Date:** 2026-06-29

## 1. Purpose

This memo extracts a memo-only comparator edge list from the verified Boston Public Schools / School Committee BTU negotiations page. The goal is to test **mechanism-proxy** comparator extraction rules after the v9 causal extraction memo. It does not create `data/comparator_mentions.csv`, does not ingest documents, and does not make causal claims.

## 2. Source and provenance

- **Source page:** Boston Public Schools / School Committee, `BTU Contract Negotiations`
- **URL:** `https://www.bostonpublicschools.org/school-committee/btu-contract-negotiations`
- **Source owner:** Boston Public Schools / Boston School Committee
- **Source lane:** `discourse` in the current comparator design, with a note that this is mechanism-proxy evidence rather than ordinary discourse commentary
- **Source type:** `bargaining_update`
- **Home city:** Boston, MA
- **Occupation focus:** teacher
- **Verification date:** `2026-06-29`
- **Page metadata visible in source HTML:** `page-published = 2025-04-30T18:47:54Z`

Verified table title:

`Minimum and Maximum Teacher Salary with a Masters Comparisons to Surrounding Districts / School Year 24-25`

Verified comparator districts visible in the table:

- Cambridge
- Wellesley
- Brookline
- Newton
- Watertown
- Milton
- Dedham
- Needham

The table also contains Boston rows, which are the **home city reference rows**, not comparator edges.

## 3. Extraction rules

1. Extract one row per comparator district explicitly listed in the verified table.
2. Use `source_obs_id = boston_bps_btu_negotiations_page`.
3. Use `source_corpus = discourse` and note that the evidence is mechanism-proxy.
4. Use `source_type = bargaining_update`.
5. Use `home_state = MA`, `home_city = Boston`, `occupation_class = teacher`, `safety_flag = 0`.
6. Use `document_date = 2025-04-30` because the source HTML visibly provides a page publication date.
7. Use `verification_date = 2026-06-29`.
8. Use `cycle_start` and `cycle_end` as `not_available` because the table is keyed to school year 24-25 and the page discusses a 2024-2027 contract, but the table itself does not provide exact cycle boundary dates.
9. Use `comparison_dimension = salary_schedule`.
10. Use `extraction_method = manual_review`.
11. Use `confidence = high` only for districts explicitly visible in the verified table.
12. Use the table title as the supporting quote because it is the shortest verified table-specific text that applies uniformly across all extracted rows.

## 4. Extracted Boston mechanism-proxy comparator-edge table

| mention_id | source_obs_id | source_corpus | source_type | home_state | home_city | comparator_state | comparator_city | occupation_class | safety_flag | cycle_start | cycle_end | document_date | verification_date | comparison_dimension | quote | page_or_section | extraction_method | confidence | notes |
|---|---|---|---|---|---|---|---|---|---:|---|---|---|---|---|---|---|---|---|---|
| `btu_boston_cambridge` | `boston_bps_btu_negotiations_page` | `discourse` | `bargaining_update` | `MA` | `Boston` | `MA` | `Cambridge` | `teacher` | 0 | `not_available` | `not_available` | `2025-04-30` | `2026-06-29` | `salary_schedule` | "Minimum and Maximum Teacher Salary with a Masters Comparisons to Surrounding Districts / School Year 24-25" | `table title / District row` | `manual_review` | `high` | Mechanism-proxy evidence from an official bargaining page; Cambridge appears as an explicit comparator district in the table. |
| `btu_boston_wellesley` | `boston_bps_btu_negotiations_page` | `discourse` | `bargaining_update` | `MA` | `Boston` | `MA` | `Wellesley` | `teacher` | 0 | `not_available` | `not_available` | `2025-04-30` | `2026-06-29` | `salary_schedule` | "Minimum and Maximum Teacher Salary with a Masters Comparisons to Surrounding Districts / School Year 24-25" | `table title / District row` | `manual_review` | `high` | Mechanism-proxy evidence from an official bargaining page; Wellesley appears as an explicit comparator district in the table. |
| `btu_boston_brookline` | `boston_bps_btu_negotiations_page` | `discourse` | `bargaining_update` | `MA` | `Boston` | `MA` | `Brookline` | `teacher` | 0 | `not_available` | `not_available` | `2025-04-30` | `2026-06-29` | `salary_schedule` | "Minimum and Maximum Teacher Salary with a Masters Comparisons to Surrounding Districts / School Year 24-25" | `table title / District row` | `manual_review` | `high` | Mechanism-proxy evidence from an official bargaining page; Brookline appears as an explicit comparator district in the table. |
| `btu_boston_newton` | `boston_bps_btu_negotiations_page` | `discourse` | `bargaining_update` | `MA` | `Boston` | `MA` | `Newton` | `teacher` | 0 | `not_available` | `not_available` | `2025-04-30` | `2026-06-29` | `salary_schedule` | "Minimum and Maximum Teacher Salary with a Masters Comparisons to Surrounding Districts / School Year 24-25" | `table title / District row` | `manual_review` | `high` | Mechanism-proxy evidence from an official bargaining page; Newton appears as an explicit comparator district in the table. |
| `btu_boston_watertown` | `boston_bps_btu_negotiations_page` | `discourse` | `bargaining_update` | `MA` | `Boston` | `MA` | `Watertown` | `teacher` | 0 | `not_available` | `not_available` | `2025-04-30` | `2026-06-29` | `salary_schedule` | "Minimum and Maximum Teacher Salary with a Masters Comparisons to Surrounding Districts / School Year 24-25" | `table title / District row` | `manual_review` | `high` | Mechanism-proxy evidence from an official bargaining page; Watertown appears as an explicit comparator district in the table. |
| `btu_boston_milton` | `boston_bps_btu_negotiations_page` | `discourse` | `bargaining_update` | `MA` | `Boston` | `MA` | `Milton` | `teacher` | 0 | `not_available` | `not_available` | `2025-04-30` | `2026-06-29` | `salary_schedule` | "Minimum and Maximum Teacher Salary with a Masters Comparisons to Surrounding Districts / School Year 24-25" | `table title / District row` | `manual_review` | `high` | Mechanism-proxy evidence from an official bargaining page; Milton appears as an explicit comparator district in the table. |
| `btu_boston_dedham` | `boston_bps_btu_negotiations_page` | `discourse` | `bargaining_update` | `MA` | `Boston` | `MA` | `Dedham` | `teacher` | 0 | `not_available` | `not_available` | `2025-04-30` | `2026-06-29` | `salary_schedule` | "Minimum and Maximum Teacher Salary with a Masters Comparisons to Surrounding Districts / School Year 24-25" | `table title / District row` | `manual_review` | `high` | Mechanism-proxy evidence from an official bargaining page; Dedham appears as an explicit comparator district in the table. |
| `btu_boston_needham` | `boston_bps_btu_negotiations_page` | `discourse` | `bargaining_update` | `MA` | `Boston` | `MA` | `Needham` | `teacher` | 0 | `not_available` | `not_available` | `2025-04-30` | `2026-06-29` | `salary_schedule` | "Minimum and Maximum Teacher Salary with a Masters Comparisons to Surrounding Districts / School Year 24-25" | `table title / District row` | `manual_review` | `high` | Mechanism-proxy evidence from an official bargaining page; Needham appears as an explicit comparator district in the table. |

## 5. Coverage summary

- table verified: `yes`
- comparator districts extracted: `Cambridge`, `Wellesley`, `Brookline`, `Newton`, `Watertown`, `Milton`, `Dedham`, `Needham`
- number of edges: `8`
- source type and corpus lane: `bargaining_update` in the `discourse` lane, with notes preserving that it is mechanism-proxy evidence
- CSV created: `no`

## 6. Interpretation

This Boston extraction differs from the Somerville v9 edge memo in three ways.

First, the Boston rows come from a **public bargaining page**, not a causal-corpus arbitration award. Second, the Boston edges are **non-safety teacher** edges, while the current Somerville named-city causal edges are all **safety-side police** edges. Third, the Boston extraction is based on a visible salary-comparison table rather than quote-audited award excerpts.

It matters for H1 because it shows that explicit named-city comparator structure is not limited to safety documents. The current public non-safety evidence can also produce city-to-city edges. But it remains mechanism-proxy rather than causal evidence because the source is a management-side bargaining update page, not a final agreement, arbitration award, or factfinding report.

## 7. Recommended next step

Recommended next step: compare the Somerville causal edges and the Boston mechanism-proxy edges side by side.

After that:

1. decide whether the project now has enough tested structure to create a tiny comparator stub CSV;
2. if not, keep working memo-first and extract one or two additional mechanism-proxy or award-style cases before productionizing;
3. leave v10 attribute design for later, because the immediate open question is now extraction comparability across causal and mechanism-proxy lanes.
