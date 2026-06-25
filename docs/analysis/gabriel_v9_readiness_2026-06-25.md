# GABRIEL v9 Readiness Audit

**Date:** 2026-06-25
**Scope:** corpus-readiness, measurement-risk, and reporting-plan audit for the current 32-row causal corpus. This memo does not run GABRIEL, change scoring code, add rows, or recommend PRRs.

## Current corpus snapshot

- Contracts: 32 causal rows.
- Cities: 9.
- Healthy matched pairs: 12 safety rows with at least one healthy same-city non-safety comparator.
- Exact-cycle matches: 9 safety rows.
- Overlap-cycle matches: 3 safety rows.
- Unmatched safety units: 3.

Unmatched safety rows:

- `ma_somerville_police_spsoa_2012`
- `ma_somerville_police_spea_2012`
- `ma_newton_police_2015`

## Source-type composition

### Rows by `source_type`

| source_type | rows |
|---|---:|
| `cba` | 29 |
| `arbitration_award` | 3 |

### Rows by `occupation_class`

| occupation_class | rows |
|---|---:|
| `police` | 9 |
| `public_works` | 7 |
| `fire` | 6 |
| `clerical_admin` | 3 |
| `library` | 3 |
| `other` | 3 |
| `teacher` | 1 |

### Rows by `safety_flag`

| safety_flag | rows |
|---|---:|
| `1` | 15 |
| `0` | 17 |

### Rows by city

| city | rows |
|---|---:|
| Arlington | 4 |
| Boston | 2 |
| Franklin | 6 |
| Georgetown | 2 |
| Newton | 1 |
| Seekonk | 6 |
| Somerville | 2 |
| Wayland | 6 |
| Worcester | 3 |

## Match-tier summary

### Exact-cycle matched cities and units

| city | safety unit | obs_id | matched non-safety classes |
|---|---|---|---|
| Worcester | fire | `ma_worcester_fire_2017` | `clerical_admin`, `public_works` |
| Arlington | fire | `ma_arlington_fire_2021` | `public_works` |
| Georgetown | police | `ma_georgetown_police_2020` | `other` |
| Franklin | fire | `ma_franklin_fire_2022` | `library`, `other`, `public_works` |
| Franklin | police | `ma_franklin_police_2022` | `library`, `other`, `public_works` |
| Franklin | police | `ma_franklin_police_sergeants_2022` | `library`, `other`, `public_works` |
| Wayland | police | `ma_wayland_police_2020` | `library`, `public_works` |
| Wayland | fire | `ma_wayland_fire_2020` | `library`, `public_works` |
| Wayland | fire | `ma_wayland_fire_jlmc_2020` | `library`, `public_works` |

### Overlap-cycle matched cities and units

| city | safety unit | obs_id | overlap comparators |
|---|---|---|---|
| Boston | police | `ma_boston_police_2020` | `clerical_admin` |
| Seekonk | police | `ma_seekonk_police_2022` | `clerical_admin`, `teacher`, `public_works`, `library` |
| Seekonk | fire | `ma_seekonk_fire_2022` | `clerical_admin`, `teacher`, `public_works`, `library` |

### Unmatched safety units

| city | safety unit | obs_id | cycle |
|---|---|---|---|
| Somerville | police | `ma_somerville_police_spsoa_2012` | `2012-2018` |
| Somerville | police | `ma_somerville_police_spea_2012` | `2012-2015` |
| Newton | police | `ma_newton_police_2015` | `2015-2018` |

## Franklin and Wayland contribution

Franklin and Wayland moved the corpus from 20 to 32 rows and from 6 to 12 healthy matched safety rows.

### Franklin

- Rows added: 6.
- Safety rows added: 3 (`fire`, `police`, `police` sergeants).
- Exact-cycle contribution: 3 new exact-cycle healthy safety rows.
- Source-type caveat: all six Franklin rows are `cba`, so Franklin improves matched structure more than reasoning-document balance.
- Artifact note: Franklin's public `30 Mile Radius - Police / Fire` item looks like a comparability/proxy lead, but it is not a contract and was correctly kept out of the corpus.

### Wayland

- Rows added: 6.
- Safety rows added: 3 (`police`, base `fire`, `fire` JLMC award).
- Exact-cycle contribution: 3 new exact-cycle healthy safety rows.
- Source-type caveat: Wayland adds both ordinary CBAs and one safety-side `arbitration_award`, so it improves matched structure while also reinforcing source-type imbalance.
- JLMC note: `ma_wayland_fire_jlmc_2020` is useful mechanism evidence because it adds an explicit impasse/backstop document in the same town-cycle as the base fire CBA.

## Measurement risks before v9

- Generic "comparable plan" health-insurance language is not peer-wage comparability. The Wayland fire and mixed AFSCME rows include verbatim insurance-plan language that the regex extractor correctly captured, but it should remain excluded from substantive peer-wage interpretation.
- CBAs and MOAs often record wage outcomes without bargaining reasoning. Low scores in these documents may reflect document-production opacity rather than true absence of comparability in bargaining.
- Arbitration, JLMC, and factfinding-like documents are more likely to contain explicit reasoning. High scores may therefore be driven by source type as much as by occupation.
- Safety versus non-safety comparisons should be stratified by `source_type`. A pooled occupation comparison would still be vulnerable to the same confounding seen in the pilot because the only award-style reasoning documents remain safety-side.
- Franklin and Wayland now create multiple same-town safety rows in the same cycle. City-level reporting should avoid treating Franklin's two police units or Wayland's base-fire plus fire-JLMC rows as if they were independent city observations.
- `other` comparators are valid for corpus structure, but analytically they are secondary to cleaner `clerical_admin`, `public_works`, `teacher`, and `library` comparators. Georgetown and some Franklin/Wayland matches should therefore be reported separately from cleaner occupation-class pairs.

## Recommended v9 design

### Which rows to run

- Run all 32 causal rows at the row level.
- Keep row-level scoring broad, but separate every downstream panel by `source_type`, match tier, and existing schema quality fields.
- The repo does not have a `source_quality` field; the closest current panel is `text_quality` (`clean`, `ocr_messy`, `partial`). Treat `text_quality` as the practical source-quality split unless the schema changes later.
- Use pair-based and city-based summaries only with explicit labels:
  - all rows
  - healthy exact + overlap safety-match subset
  - exact-only subset
  - overlap subset
  - unmatched safety rows shown separately, not folded into matched-pair claims

### Outputs to create

- Row-level scores.
- Quote audit table.
- City-level aggregation.
- Matched-pair aggregation.
- Source-type aggregation.
- Leave-one-city-out sensitivity, or at minimum an exclude-Somerville-awards sensitivity.
- Exclude-`arbitration_award` sensitivity.
- Exact-only versus exact+overlap comparison.

### Figures to create

- Score by `source_type`.
- Score by `safety_flag`.
- Score by `occupation_class`.
- Score by city.
- Top documents by score.
- Score distribution with and without arbitration/JLMC awards.
- Exact versus overlap matched-pair comparison.

### Preliminary interpretation wording

- Results should be described as descriptive, not causal.
- H1 remains plausible but underidentified.
- Source-type confounding remains central.
- Public-source CBAs and MOAs may understate bargaining mechanisms because they often preserve outcomes rather than reasoning.

## Attribute expansion recommendation

### Recommendation

Use a comparability-only v9 for the first 32-row reporting pass, with report scaffolding designed to accommodate later attributes.

### Why

- `comparability_emphasis` is the only attribute that is already mature enough to support a disciplined rerun and a quote-audit workflow.
- The main current problem is not lack of possible attributes; it is the need to separate occupation effects from document-type effects in a still-thin reasoning corpus.
- Adding a second attribute now would increase interpretation complexity before the first descriptive reporting pass establishes the current corpus baseline.

### Candidate follow-on

If one low-cost pilot attribute is added after the first descriptive pass, `arbitration_or_impasse_backstop` is the strongest next candidate because Somerville and Wayland already provide clear safety-side examples. `settlement_opacity_or_moa_thinness` is conceptually useful but reads more like a document-production attribute than a bargaining-mechanism attribute and may be better handled first in reporting stratification rather than scoring.

## Bottom line

The corpus is now large enough for a first useful descriptive GABRIEL/reporting pass, but not for a clean occupation-level claim. v9 should be treated as a carefully stratified comparability audit of the 32-row public-source corpus, not as a decisive test of H1.
