# Boston BTU Salary-Comparison Recon Seed

Date: 2026-06-29  
Status: Recon seed for lightweight Codex verification  
Scope: Boston Public Schools / Boston Teachers Union 2024-2027 bargaining materials

## Purpose

This note is a seed document for a lightweight follow-up on the strongest public non-safety peer-wage comparison lead in the Newton/Somerville/Boston mechanism-source queue.

The goal is not to rerun broad acquisition. The goal is to verify and document one specific Boston lead: the public Boston Public Schools / Boston Teachers Union salary-comparison material.

## Working hypothesis

Boston appears to provide the clearest public non-safety peer-wage comparison lead found so far.

The relevant evidence appears to be an official Boston Public Schools public bargaining page that includes a salary comparison table for teachers with master’s degrees across surrounding districts.

This should probably be classified as:

- `comparability_signal`: `peer_wage_comparison`
- `likely_corpus_destination`: `mechanism_proxy`
- `document_type`: likely `bargaining_update` or public bargaining page, not a final causal-corpus document
- `source_owner`: Boston Public Schools / School Committee
- `unit`: Boston Teachers Union

## Specific source to verify

Primary source route:

- Boston Public Schools / School Committee page titled “Boston Teachers Union Contract Negotiations”

Specific item to verify on that page:

- Table titled “Minimum and Maximum Teacher Salary with a Masters Comparisons to Surrounding Districts / School Year 24-25”

Districts visible in the table include:

- Boston
- Cambridge
- Wellesley
- Brookline
- Newton
- Watertown
- Milton
- Dedham
- Needham

The table appears to compare minimum and maximum teacher salaries with a master’s degree, plus notes about time to top step and differences in work year/day structure.

## Why this matters for H1

This is valuable because it is public non-safety wage-comparison evidence.

GABRIEL v9 showed explicit peer-community comparability language concentrated in safety-side arbitration/award-style documents. This Boston lead shows that non-safety bargaining materials can also contain peer-wage comparison, but in a different document type: public bargaining communication rather than arbitration or factfinding.

This helps clarify the distinction between:

1. occupation-specific wage-setting differences; and
2. document-production differences.

It does not, by itself, prove that non-safety wage-setting relies on peer comparisons in the same way police/fire Joint Labor-Management Committee awards do. It does show that peer-wage comparison can appear in non-safety bargaining materials when the public record is rich enough.

## Evidence classification hypothesis

Recommended classification before Codex verification:

| Field | Proposed value | Reason |
|---|---|---|
| wage_reasoning_signal | high | The page contains wage proposals, salary amounts, and settlement context. |
| comparability_signal | peer_wage_comparison | The page includes surrounding-district teacher salary comparisons. |
| likely_corpus_destination | mechanism_proxy | It is bargaining-context evidence, not a final CBA/MOA/award/factfinding report. |
| causal_candidate? | no | The public page explains bargaining context; it is not itself a final agreement. |
| discourse_candidate? | possible | Could be useful if the repo later supports discourse/proxy ingestion. |
| priority | P1 | It is the strongest public non-safety peer-wage comparison lead currently identified. |

## Nearby supporting sources

The Boston Teachers Union bargaining-updates page may be useful for context because it links to:

- Memorandum of Agreement
- Plain Language Summary
- One Page Summary
- Frequently Asked Questions
- bargaining summaries

The April 2025 Boston Public Schools / Boston Teachers Union Collective Bargaining Agreement presentation is useful for wage context, especially the emphasis on higher increases for paraprofessionals and ABA specialists. It may be a supporting mechanism-proxy document, but the surrounding-district comparison appears to be on the BPS negotiations page rather than in the presentation.

The Boston Municipal Research Bureau research update is useful as third-party context on contract costs and wage increases, but it should not be treated as primary mechanism evidence.

## What Codex should do

Codex should not run a broad search. It should:

1. open the existing queue;
2. identify the Boston row with `comparability_signal = peer_wage_comparison`;
3. verify whether that row corresponds to the BPS BTU negotiations page;
4. confirm the table title and whether it is text-readable;
5. classify the evidence as mechanism-proxy unless a stronger source is found in the existing queue;
6. create a short deep-dive memo;
7. update the queue only if current classification is inaccurate;
8. run validate and audit;
9. update PROGRESS.md;
10. commit.

## Stop rules

Stop without broad acquisition if:

- the BPS page confirms the surrounding-district comparison;
- the existing queue already captures the source route;
- the evidence is sufficient for a mechanism-proxy memo.

Do not:

- search broadly for more Boston materials;
- ingest rows;
- download more than one source for inspection;
- run GABRIEL;
- modify data/contracts.csv;
- modify corpus/ or inbox/;
- treat the BPS public bargaining page as a causal-corpus document.

## Suggested memo output

Create:

`docs/acquisition/ma_boston_btu_salary_comparison_deep_dive_2026-06-29.md`

The memo should answer:

1. What document/page contains the comparison?
2. Who authored or hosted it?
3. What unit does it concern?
4. What exactly is being compared?
5. Is it peer-wage comparison, general wage rationale, contract-cost-only, or unclear?
6. Why is it mechanism-proxy rather than causal-corpus evidence?
7. How does it affect interpretation of H1?
8. What should happen next?