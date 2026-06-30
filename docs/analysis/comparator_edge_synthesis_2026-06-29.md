# Comparator Edge Synthesis

**Date:** 2026-06-29

## 1. Purpose

This memo consolidates the two already-tested comparator extraction artifacts into one side-by-side scaffold: the Somerville v9 causal arbitration edges and the Boston BTU mechanism-proxy bargaining-page edges. It is for validation and visualization planning only. It does not create the production comparator dataset.

## 2. Inputs used

- [Comparator Network Design Memo](/Users/joachimjohnson/Documents/RA_2026/Pol_Fire/gabriel-wages/docs/analysis/comparator_network_design_2026-06-29.md)
- [Comparator Edges From v9 Verified Excerpts](/Users/joachimjohnson/Documents/RA_2026/Pol_Fire/gabriel-wages/docs/analysis/comparator_edges_from_v9_verified_excerpts_2026-06-29.md)
- [Comparator Edges From Boston BTU Table](/Users/joachimjohnson/Documents/RA_2026/Pol_Fire/gabriel-wages/docs/analysis/comparator_edges_from_boston_btu_table_2026-06-29.md)
- [Comparator Stub CSV](/Users/joachimjohnson/Documents/RA_2026/Pol_Fire/gabriel-wages/docs/analysis/comparator_mentions_stub_2026-06-29.csv)

## 3. Stub CSV status

`docs/analysis/comparator_mentions_stub_2026-06-29.csv` is a **non-production stub**. It exists under `docs/analysis/` rather than `data/` to make clear that it is a scaffold assembled only from already-reviewed memos. It must not be treated as `data/comparator_mentions.csv`.

## 4. Side-by-side summary

### Somerville police arbitration edges

- Source lane: `causal`
- Source type: `arbitration_award`
- Home city: Somerville
- Occupation: `police`
- Safety flag: `1`
- Edge count: `10`
- Pattern: all named-city causal edges currently come from two Somerville police arbitration awards

### Boston BTU bargaining-page edges

- Source lane: `discourse`
- Source type: `bargaining_update`
- Home city: Boston
- Occupation: `teacher`
- Safety flag: `0`
- Edge count: `8`
- Pattern: all Boston edges come from a verified public salary-comparison table on a bargaining page and remain mechanism-proxy evidence

## 5. Summary table

| summary item | value |
|---|---|
| total edges | `18` |
| edges by source_corpus | `causal = 10`, `discourse = 8` |
| edges by safety_flag | `1 = 10`, `0 = 8` |
| edges by source_type | `arbitration_award = 10`, `bargaining_update = 8` |
| edges by home_city | `Somerville = 10`, `Boston = 8` |
| unique comparator cities | `15` |

Unique comparator cities in the stub:

- Arlington
- Boston
- Brookline
- Cambridge
- Dedham
- Lowell
- Malden
- Melrose
- Milton
- Needham
- Newton
- Quincy
- Waltham
- Watertown
- Wellesley

## 6. Interpretation for H1

The current named-city **causal** comparator evidence remains concentrated in safety-side arbitration material. All 10 causal named-city edges in the stub come from Somerville police awards.

At the same time, named-city **non-safety** comparator evidence now exists in a tested extraction format. But it currently sits in the discourse/mechanism-proxy lane, not in a causal reasoning document. That means the stub strengthens the document-production caveat: explicit comparator structure is visible in both safety and non-safety materials, but not yet in the same source lane or document type.

This supports caution against a simple occupation-only story. The cleaner current contrast is safety/causal/arbitration versus non-safety/discourse-lane/mechanism-proxy.

## 7. Recommended next step

Recommended next step: build lightweight validation/visualization scripts for the comparator stub later, rather than jumping straight to v10 attribute design.

Why:

- the stub now has enough rows to test basic network summaries and plotting logic;
- the file is still intentionally non-production, which makes it a safe scaffold for iterative QA;
- visualization and validation may clarify what additional evidence is needed before creating `data/comparator_mentions.csv`.

If the team prefers to stay in design mode instead, the strongest next attribute candidate remains `arbitration_or_impasse_backstop`, but the stub now makes comparator-structure validation a practical alternative.
