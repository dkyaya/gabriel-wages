# GABRIEL v9 Preliminary Descriptive Report

**Date:** 2026-06-25  
**Scope:** descriptive comparability-only GABRIEL pass over the 32-row causal corpus. No new attributes, no new data ingestion, no PRRs, and no causal claims.

## 1. Executive summary

GABRIEL v9 scores the expanded public-source causal corpus on `comparability_emphasis` only. The run is useful as a descriptive baseline, not as a clean test of H1. The corpus has 32 scored rows, mean score 10.41, median 5.0, and 3 rows with verified relevant supporting excerpts.

The main pattern remains source-type sensitive. Arbitration-style safety documents carry the strongest explicit comparability language, while ordinary CBAs usually record outcomes and clauses rather than bargaining reasoning. H1 remains plausible but underidentified because comparable non-safety reasoning documents are still thin.

## 2. Corpus and match-tier status

- Contracts: 32 causal rows.
- Cities: 9.
- Healthy matched safety rows: 12.
- Exact-cycle matches: 9.
- Overlap-cycle matches: 3.
- Unmatched safety rows: 3, all Somerville/Newton.

## 3. GABRIEL method and v9 safeguards

v9 reuses the v8 runner's full-text input, verbatim quote verification, bounded one-call retry for failed excerpts, and relevance filtering. The v9 wrapper adds an explicit exclusion for generic health-insurance "comparable plan" language unless it is tied to peer-community compensation comparability.

The run counts peer wage, pay, salary, compensation, longevity-pay, stipend, detail-rate, or benefit comparisons only when the passage clearly compares compensation to external employers, jurisdictions, or peer communities. It excludes CPI/COLA references, generic market adjustments, internal step schedules, recognition language, grievance/arbitration boilerplate, and generic insurance-plan equivalence.

## 4. Main descriptive results

| summary   | group   |   n_rows |   mean_score |   median_score |   max_score |   rows_score_gt_0 |   rows_with_verified_relevant_excerpts |
|:----------|:--------|---------:|-------------:|---------------:|------------:|------------------:|---------------------------------------:|
| overall   | all     |       32 |        10.41 |              5 |          88 |                24 |                                      3 |

Top-scoring documents:

| obs_id                          | city_name   | occupation_class   | source_type       |   score |   excerpt_count |
|:--------------------------------|:------------|:-------------------|:------------------|--------:|----------------:|
| ma_somerville_police_spsoa_2012 | Somerville  | police             | arbitration_award |      88 |               5 |
| ma_somerville_police_spea_2012  | Somerville  | police             | arbitration_award |      85 |               4 |
| ma_arlington_fire_2021          | Arlington   | fire               | cba               |      25 |               1 |
| ma_wayland_other_2021           | Wayland     | other              | cba               |      10 |               0 |
| ma_wayland_fire_2020            | Wayland     | fire               | cba               |      10 |               0 |
| ma_franklin_other_2022          | Franklin    | other              | cba               |      10 |               0 |
| ma_franklin_public_works_2022   | Franklin    | public_works       | cba               |      10 |               0 |
| ma_boston_clerical_admin_2023   | Boston      | clerical_admin     | cba               |       8 |               0 |

## 5. Source-type split

| summary        | source_type       |   n_rows |   mean_score |   median_score |   max_score |   rows_score_gt_0 |   rows_with_verified_relevant_excerpts |
|:---------------|:------------------|---------:|-------------:|---------------:|------------:|------------------:|---------------------------------------:|
| by_source_type | arbitration_award |        3 |        57.67 |             85 |          88 |                 2 |                                      2 |
| by_source_type | cba               |       29 |         5.52 |              5 |          25 |                22 |                                      1 |

This split is central. Award-style rows remain safety-side only in the current corpus, so pooled safety/non-safety comparisons remain confounded by source type.

## 6. Safety vs non-safety split

| summary        |   safety_flag |   n_rows |   mean_score |   median_score |   max_score |   rows_score_gt_0 |   rows_with_verified_relevant_excerpts |
|:---------------|--------------:|---------:|-------------:|---------------:|------------:|------------------:|---------------------------------------:|
| by_safety_flag |             0 |       17 |         4.76 |              5 |          10 |                12 |                                      0 |
| by_safety_flag |             1 |       15 |        16.8  |              5 |          88 |                12 |                                      3 |

This table is descriptive only. It should not be read as an occupation effect because source types and reasoning-document availability differ sharply by safety status.

## 7. Matched-city and match-tier results

Matched-pair summary:

| safety_obs_id                     | city_name   | source_type       | match_tier    |   safety_score | matched_non_safety_classes                  |   n_matched_non_safety |   matched_non_safety_mean_score |
|:----------------------------------|:------------|:------------------|:--------------|---------------:|:--------------------------------------------|-----------------------:|--------------------------------:|
| ma_worcester_fire_2017            | Worcester   | cba               | exact_cycle   |              8 | clerical_admin;public_works                 |                      2 |                            5    |
| ma_boston_police_2020             | Boston      | cba               | overlap_cycle |              5 | clerical_admin                              |                      1 |                            8    |
| ma_somerville_police_spsoa_2012   | Somerville  | arbitration_award | unmatched     |             88 |                                             |                      0 |                                 |
| ma_somerville_police_spea_2012    | Somerville  | arbitration_award | unmatched     |             85 |                                             |                      0 |                                 |
| ma_arlington_fire_2021            | Arlington   | cba               | exact_cycle   |             25 | public_works                                |                      1 |                            0    |
| ma_newton_police_2015             | Newton      | cba               | unmatched     |              6 |                                             |                      0 |                                 |
| ma_georgetown_police_2020         | Georgetown  | cba               | exact_cycle   |              0 | other                                       |                      1 |                            5    |
| ma_seekonk_police_2022            | Seekonk     | cba               | overlap_cycle |              5 | clerical_admin;library;public_works;teacher |                      4 |                            3.25 |
| ma_seekonk_fire_2022              | Seekonk     | cba               | overlap_cycle |              5 | clerical_admin;library;public_works;teacher |                      4 |                            3.25 |
| ma_franklin_fire_2022             | Franklin    | cba               | exact_cycle   |              0 | library;other;public_works                  |                      3 |                            6.67 |
| ma_franklin_police_2022           | Franklin    | cba               | exact_cycle   |              5 | library;other;public_works                  |                      3 |                            6.67 |
| ma_franklin_police_sergeants_2022 | Franklin    | cba               | exact_cycle   |              5 | library;other;public_works                  |                      3 |                            6.67 |

Safety vs non-safety within exact-or-overlap matched sets:

| summary                                                   |   safety_flag |   n_rows |   mean_score |   median_score |   max_score |   rows_score_gt_0 |   rows_with_verified_relevant_excerpts |
|:----------------------------------------------------------|--------------:|---------:|-------------:|---------------:|------------:|------------------:|---------------------------------------:|
| safety_vs_non_safety_within_exact_or_overlap_matched_sets |             0 |       14 |         4.71 |              5 |          10 |                10 |                                      0 |
| safety_vs_non_safety_within_exact_or_overlap_matched_sets |             1 |       12 |         6.08 |              5 |          25 |                 9 |                                      1 |

City-level aggregation:

| summary                |   safety_flag |   n_rows |   mean_score |   median_score |   max_score |   rows_score_gt_0 |   rows_with_verified_relevant_excerpts |
|:-----------------------|--------------:|---------:|-------------:|---------------:|------------:|------------------:|---------------------------------------:|
| city_level_aggregation |             0 |        7 |         5.18 |              5 |         8   |                 7 |                                      0 |
| city_level_aggregation |             1 |        9 |        15.98 |              5 |        86.5 |                 8 |                                      2 |

## 8. Sensitivity checks

| summary                              | group   |   n_rows |   mean_score |   median_score |   max_score |   rows_score_gt_0 |   rows_with_verified_relevant_excerpts |
|:-------------------------------------|:--------|---------:|-------------:|---------------:|------------:|------------------:|---------------------------------------:|
| exact_cycle_only                     | all     |       18 |         5.72 |              5 |          25 |                13 |                                      1 |
| exact_plus_overlap_healthy_matches   | all     |       26 |         5.35 |              5 |          25 |                19 |                                      1 |
| cba_only_sample                      | all     |       29 |         5.52 |              5 |          25 |                22 |                                      1 |
| arbitration_award_sample             | all     |        3 |        57.67 |             85 |          88 |                 2 |                                      2 |
| excluding_somerville_police_awards   | all     |       30 |         5.33 |              5 |          25 |                22 |                                      1 |
| excluding_all_arbitration_award_rows | all     |       29 |         5.52 |              5 |          25 |                22 |                                      1 |

The most important sensitivities are CBA-only and excluding all `arbitration_award` rows. If the gap narrows sharply there, the descriptive signal is mostly about source type rather than occupation.

## 9. Quote audit and examples

Quote audit output: `analysis/gabriel_pilot/results_v9_quote_audit.csv`

- Verified relevant supporting excerpts: 10
- Verbatim but irrelevant or ambiguous flagged excerpts: 3
- The report intentionally avoids long source excerpts. The audit file preserves row-level quote provenance for internal review.

Examples by type:

- Somerville police awards: explicit discussion of comparable-town wages and benefits.
- Ordinary CBAs: mostly fixed wage schedules, grievance/arbitration clauses, or internal terms with little external wage reasoning.
- Wayland/other CBA false-positive risk: generic health-insurance comparable-plan language is treated as non-evidence for peer-wage comparability.

## 10. Interpretation

v9 is descriptive, not causal. It supports the view that explicit comparability language is recoverable in the public corpus, but it does not isolate an occupation effect. H1 remains plausible but underidentified because source-type confounding remains central: the strongest reasoning documents are safety-side awards, while non-safety rows are mostly CBAs.

Low CBA scores should be interpreted cautiously. CBAs and MOAs may understate bargaining mechanisms because they often preserve final terms without the parties' reasoning. The main evidence gap is still public non-safety reasoning material comparable to Somerville and Wayland safety-side award documents.

## 11. Next steps

1. Decide whether v10 should add `arbitration_or_impasse_backstop` after this comparability-only baseline.
2. Continue official-portal expansion only if more matched CBA/MOA scale is needed for robustness.
3. Prioritize Newton, Somerville, and Boston mechanism materials for public reasoning evidence.
4. Keep PRRs deferred unless the PI changes preference.

## Output files

- `analysis/gabriel_pilot/results_v9.csv`
- `analysis/gabriel_pilot/results_v9_quote_audit.csv`
- `analysis/gabriel_pilot/results_v9_summary_*.csv`
- `analysis/gabriel_pilot/figures_v9/`
