# Comparator Network Design Memo

**Date:** 2026-06-29

## 1. Purpose

This memo defines a future design for a municipality-to-municipality comparator dataset built from verified comparability excerpts and closely related mechanism-source documents. It is a scaffolding memo only. It does not create `data/comparator_mentions.csv`, does not ingest new documents, and does not make causal claims.

## 2. Why comparator networks matter for H1

H1 asks whether safety-side wage-setting relies more heavily on peer-community comparability than non-safety wage-setting. A comparator network would not answer that by itself, but it would make the mechanism more concrete by showing:

- which municipalities are named as comparators;
- whether those comparator mentions are concentrated in police/fire versus non-safety materials;
- whether the pattern is driven by arbitration/award-style reasoning documents versus ordinary CBAs;
- whether certain municipalities recur as benchmark nodes across occupations, cycles, or document types.

In short, the network would move the project from "comparability language exists" to "here is the observed structure of who cites whom."

## 3. How this extends GABRIEL v9

GABRIEL v9 established a descriptive pattern: explicit peer-community comparability language is concentrated in safety-side arbitration or award-style documents, while most ordinary CBAs record outcomes with little explicit reasoning. A comparator network would extend that result by converting verified text into directed edges:

- `home_city -> comparator_city`
- one row per distinct comparator mention
- with occupation, source type, cycle, and comparison dimension attached

This keeps GABRIEL v9 as the discovery layer while adding a transparent extraction layer for named comparator geography.

## 4. Current evidence types available for future extraction

High-confidence evidence currently falls into five tiers:

1. **Verified GABRIEL excerpts from causal documents.**
   These are the strongest current extraction source because the quote audit already distinguishes relevant verified excerpts from irrelevant or ambiguous text.

2. **Arbitration/JLMC award excerpts.**
   In practice, these overlap heavily with the strongest verified GABRIEL material. They remain analytically distinct because award-style reasoning documents are the main place where comparator cities are explicitly named.

3. **Boston BTU salary-comparison table.**
   This is verified high-confidence mechanism-proxy evidence for a non-safety peer-wage comparison, but it is not a causal-corpus document.

4. **Mechanism-source queue leads.**
   These are useful for prioritizing later manual review, but they are not extraction-ready unless the underlying source is manually re-opened and the comparator evidence is verified.

5. **Regex candidates.**
   These should be treated as leads only. A regex hit can suggest where named comparators may appear, but it should never become a final comparator edge without quote-level verification.

## 5. Candidate data source hierarchy

The extraction hierarchy for a future comparator dataset should be:

1. verified GABRIEL excerpts;
2. arbitration/JLMC awards reviewed directly;
3. verified mechanism-source memos that quote or describe a visible comparator table or excerpt;
4. manually reviewed bargaining presentations/pages;
5. regex candidates only as leads.

If two sources conflict, the more direct and more document-native source wins. A verified quote from a causal document outranks a memo summary. A manually reviewed original table outranks a queue label.

## 6. Proposed production dataset path

Future production file:

`data/comparator_mentions.csv`

Recommended unit of observation:

- one row = one verified `home_city -> comparator_city` mention in one source observation

This means a single source can generate multiple rows if it names multiple comparator municipalities.

## 7. Proposed schema

Planned columns for future `data/comparator_mentions.csv`:

| field | role |
|---|---|
| `mention_id` | primary key for the comparator mention row |
| `source_obs_id` | source observation or source-document key that produced the mention |
| `source_corpus` | whether the source is `causal` or `discourse`/proxy-style material if the project later permits it |
| `source_type` | source document type |
| `home_state` | state of the municipality making the comparison |
| `home_city` | municipality making the comparison |
| `comparator_state` | state of named comparator municipality |
| `comparator_city` | named comparator municipality |
| `occupation_class` | occupation associated with the source observation |
| `safety_flag` | derived from `occupation_class` |
| `cycle_start` | source cycle start if applicable |
| `cycle_end` | source cycle end if applicable |
| `document_date` | date of award, presentation, page, or document |
| `verification_date` | date the project verified or reviewed the source/excerpt |
| `comparison_dimension` | what is being compared |
| `quote` | exact supporting quote or exact table-title snippet |
| `page_or_section` | page number, slide, section header, or table label |
| `extraction_method` | how the mention was extracted |
| `confidence` | confidence in the edge |
| `notes` | constrained free text for caveats |

## 8. Controlled vocabularies

Recommended controlled values:

### `comparison_dimension`

- `wages`
- `salary_schedule`
- `benefits`
- `total_compensation`
- `staffing`
- `cost_of_living`
- `ability_to_pay`
- `general_comparability`
- `other`

### `extraction_method`

- `gabriel_verified_excerpt`
- `manual_review`
- `mechanism_source_queue`
- `regex_candidate`

### `confidence`

- `high`
- `medium`
- `low`

Additional recommended controls:

- `occupation_class`: reuse the repo vocabulary from [docs/schema.md](/Users/joachimjohnson/Documents/RA_2026/Pol_Fire/gabriel-wages/docs/schema.md)
- `safety_flag`: derived, never hand-entered
- `source_corpus`: `causal` or `discourse` if the project later permits proxy/discourse treatment
- `source_type`: should be expanded for this file to cover both causal and mechanism-proxy documents, but final values should be locked only when the production CSV is created

## 9. Extraction rules

1. Extract one row per named comparator municipality, not one row per quote blob.
2. Do not create a row unless the comparator city is explicitly named in a verified quote, visible table, or clearly documented source note.
3. Do not infer comparator cities from phrases such as "surrounding communities" unless the actual municipalities are visible elsewhere in the verified source.
4. Preserve the exact supporting quote or exact table title in `quote`.
5. Keep document-native scope. If a document compares multiple dimensions, create separate rows only when the dimension is distinguishable from the source.
6. Use `gabriel_verified_excerpt` only when the quote passed quote-audit verification and relevance screening.
7. Use `manual_review` for reviewed original tables, pages, slides, or awards not coming from the GABRIEL quote-audit file.
8. Use `mechanism_source_queue` only for triage or staging notes, not for final high-confidence extraction unless the underlying source was manually verified.
9. Use `regex_candidate` only for lead generation. These rows should not enter production unchanged.
10. When a source names a comparator set and then discusses that set collectively, create a separate row for each named city and repeat the quote.
11. If a source is clearly mechanism-proxy rather than causal, preserve that distinction in `source_corpus` or `notes`; do not collapse it into causal evidence.
12. If a quote is verified but ambiguous about the comparison dimension, code `general_comparability` or `other` rather than over-claiming.
13. Keep `document_date` separate from `verification_date`; a project review date is never a substitute for the source document's own date.

## 10. Validation rules

Recommended validation for a future comparator file:

1. `mention_id` must be unique.
2. `home_state`, `comparator_state` must be valid USPS abbreviations.
3. `home_city` and `comparator_city` cannot be blank.
4. `home_city` cannot equal `comparator_city`.
5. `occupation_class` must use the repo-controlled vocabulary.
6. `safety_flag` must equal 1 only for `police` or `fire`.
7. `comparison_dimension`, `extraction_method`, and `confidence` must come from controlled lists.
8. `quote` cannot be blank for `high` confidence rows.
9. `page_or_section` cannot be blank for `high` confidence rows unless the source is a single verified HTML table and the section label is used instead.
10. `regex_candidate` rows cannot be `high` confidence.
11. `mechanism_source_queue` rows cannot be `high` confidence unless the underlying source was re-opened and manually verified, in which case `manual_review` should usually replace the method.
12. If `source_obs_id` points to an existing causal row, `home_city`, `home_state`, `occupation_class`, `cycle_start`, and `cycle_end` should match that source row exactly.

## 11. Example rows using only verified/high-confidence evidence

These are illustrative markdown examples only. No production CSV is created in this session.

| mention_id | source_obs_id | source_corpus | source_type | home_state | home_city | comparator_state | comparator_city | occupation_class | safety_flag | cycle_start | cycle_end | document_date | verification_date | comparison_dimension | quote | page_or_section | extraction_method | confidence | notes |
|---|---|---|---|---|---|---|---|---|---:|---|---|---|---|---|---|---|---|---|---|
| `ex_som_spsoa_arlington` | `ma_somerville_police_spsoa_2012` | `causal` | `arbitration_award` | `MA` | `Somerville` | `MA` | `Arlington` | `police` | 1 | `2012-07-01` | `2018-06-30` | `not_available` | `2026-06-25` | `general_comparability` | "Those communities chosen in the Collins Center classification study were Arlington, Brookline, Cambridge, Lowell, Malden, Melrose, Newton, Quincy, and Waltham." | `p.55` | `gabriel_verified_excerpt` | `high` | Named comparator extracted from verified Somerville superior-officers award excerpt; quote-audit page number is available, but document date is not established here. |
| `ex_som_spsoa_cambridge` | `ma_somerville_police_spsoa_2012` | `causal` | `arbitration_award` | `MA` | `Somerville` | `MA` | `Cambridge` | `police` | 1 | `2012-07-01` | `2018-06-30` | `not_available` | `2026-06-25` | `general_comparability` | "Those communities chosen in the Collins Center classification study were Arlington, Brookline, Cambridge, Lowell, Malden, Melrose, Newton, Quincy, and Waltham." | `p.55` | `gabriel_verified_excerpt` | `high` | Same verified excerpt, separate comparator-city row; document date remains unconfirmed in this memo. |
| `ex_som_spea_boston` | `ma_somerville_police_spea_2012` | `causal` | `arbitration_award` | `MA` | `Somerville` | `MA` | `Boston` | `police` | 1 | `2012-07-01` | `2015-06-30` | `not_available` | `2026-06-25` | `wages` | "The Union contends that Boston should be considered as comparable due to its close proximity, its population density, and the fact that it is faced with similar urban policing concerns." | `p.58` | `gabriel_verified_excerpt` | `high` | Comparator city is directly named in a verified relevant excerpt; the project review date is distinct from the underlying award date. |
| `ex_boston_btu_cambridge` | `boston_bps_btu_negotiations_page` | `discourse` | `bargaining_update` | `MA` | `Boston` | `MA` | `Cambridge` | `teacher` | 0 |  |  | `not_available` | `2026-06-29` | `salary_schedule` | "Minimum and Maximum Teacher Salary with a Masters Comparisons to Surrounding Districts / School Year 24-25" | `salary comparison table` | `manual_review` | `high` | Verified mechanism-proxy page lists Cambridge among surrounding districts in the visible salary-comparison table; the deep-dive memo establishes a verification date but not a source-page publication date. |
| `ex_boston_btu_newton` | `boston_bps_btu_negotiations_page` | `discourse` | `bargaining_update` | `MA` | `Boston` | `MA` | `Newton` | `teacher` | 0 |  |  | `not_available` | `2026-06-29` | `salary_schedule` | "Minimum and Maximum Teacher Salary with a Masters Comparisons to Surrounding Districts / School Year 24-25" | `salary comparison table` | `manual_review` | `high` | Verified mechanism-proxy page lists Newton among surrounding districts in the visible salary-comparison table; `2026-06-29` is a verification date, not a document date. |

Only five example rows are shown because current high-confidence evidence is still narrow. The existing Wayland JLMC document does not currently provide a verified named-city comparator excerpt in the reviewed materials, so it is not included here.

## 12. Visualization ideas

- Directed municipality network with arrows from `home_city` to `comparator_city`.
- Edge color by `safety_flag` to separate safety and non-safety comparator use.
- Edge style by `source_type`, especially award-style versus bargaining-update/proxy material.
- Node size by frequency of being cited as a comparator.
- Small multiples by `occupation_class`.
- Separate safety and non-safety comparator maps.
- Time-sliced network panels by cycle window or document date.
- A two-layer view that separates causal-document edges from mechanism-proxy/discourse edges.

## 13. Recommended next step

Recommended next task: **2. extract from v9 verified excerpts.**

Why:

- it uses the cleanest existing evidence base;
- it stays inside already verified causal-document excerpts;
- it will produce the first disciplined comparator edges without forcing a production CSV yet;
- it clarifies how many real named-city safety-side edges exist before expanding into manual Boston or queue-based extraction.

Recommended sequencing after that:

1. extract a memo-only edge list from verified v9 excerpts;
2. manually extract the Boston BTU table and any similarly verified Somerville follow-ups;
3. only then decide whether a tiny `comparator_mentions_stub` CSV is worth creating.

Deferring until after v10 design is not necessary for this comparator-specific scaffold, but productionizing the CSV should wait until the quote-based extraction pass is complete.

See also:

- [Comparator Edges From v9 Verified Excerpts](/Users/joachimjohnson/Documents/RA_2026/Pol_Fire/gabriel-wages/docs/analysis/comparator_edges_from_v9_verified_excerpts_2026-06-29.md)
- [Comparator Edges From Boston BTU Table](/Users/joachimjohnson/Documents/RA_2026/Pol_Fire/gabriel-wages/docs/analysis/comparator_edges_from_boston_btu_table_2026-06-29.md)
- [Comparator Stub CSV](/Users/joachimjohnson/Documents/RA_2026/Pol_Fire/gabriel-wages/docs/analysis/comparator_mentions_stub_2026-06-29.csv)
- [Comparator Edge Synthesis](/Users/joachimjohnson/Documents/RA_2026/Pol_Fire/gabriel-wages/docs/analysis/comparator_edge_synthesis_2026-06-29.md)
