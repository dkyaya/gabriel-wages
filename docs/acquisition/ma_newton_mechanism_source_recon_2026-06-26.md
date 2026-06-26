# Newton Mechanism-Source Recon

**Date:** 2026-06-26  
**Scope:** bounded public-only review of Newton non-safety wage-reasoning sources. No PRRs, licensed sources, broad crawling, or GABRIEL runs.

## Purpose

Assess whether Newton public sources contain non-safety wage-reasoning evidence comparable to safety-side arbitration or award materials, with priority on bargaining proposals, mediation materials, school-committee packets, settlement summaries, and only secondarily final CBAs/MOAs.

## Research value

Newton is valuable because the teacher strike and 2023-2024 bargaining cycle left a unusually public trail of proposals, mediation materials, settlement summaries, and final 2024-2027 educator agreements. These sources can help distinguish contract outcomes from bargaining logic, but most are mechanism proxies rather than causal-corpus rows.

## Priority Source Routes Checked

| route | status | notes |
|---|---:|---|
| `https://www.newteach.org/copy-of-negotiations-team` | checked | Public NTA bargaining archive with direct PDFs for proposals, counterproposals, mediation materials, MOA, and settlement summary. |
| `https://www.newton.k12.ma.us/human-resources/collective-bargaining-agreements` | checked | Public NPS CBA page with Google Drive folders for Unit A/B/C/D/E and NESA materials. |
| `https://www.newton.k12.ma.us/sc-meetings` | checked | Public School Committee meeting index. Useful as a route, but not itself evidence. |
| `https://www.newteach.org/contracts` | checked | Public NTA contracts page with 2024-2027 Unit A/B/C/D/E agreements and salary schedules. |

## Search Terms Used

`comparable`, `comparison`, `peer districts`, `peer communities`, `market`, `salary`, `wage`, `compensation`, `settlement`, `fiscal impact`, `contract cost`, `mediation`, `factfinding`, `proposal`, `counterproposal`, `memorandum of agreement`, `negotiations update`

## Candidate Evidence Table

| candidate | source owner | date/cycle | type | access | wage reasoning | comparability signal | recommendation |
|---|---|---:|---|---|---|---|---|
| January 30 package comparison | NTA | 2024-01-30 | bargaining update | direct PDF | high | general wage rationale | Mechanism proxy; do not ingest. |
| NPS mediation package cover sheet | Newton Public Schools | 2024-01-30 | proposal | direct PDF | high | general wage rationale | Mechanism proxy; do not ingest. |
| NTA proposed MOA on all proposals | NTA | 2024-01-28 | proposal | direct PDF | high | general wage rationale | Mechanism proxy unless later verified as final; do not ingest now. |
| School Committee mediation outline | School Committee | 2024-01-19 | proposal | direct PDF | high | general wage rationale | Mechanism proxy; do not ingest. |
| NTA/NPS School Committee MOA | NTA / School Committee | 2024-02-02 | MOA | direct PDF | high | general wage rationale | Causal candidate only after manual unit-scope/signature verification. |
| NTA strike victory summary | NTA | 2024 | settlement summary | direct PDF | high | general wage rationale | Mechanism proxy; do not ingest. |
| 2024-2027 Unit A/B/C/D/E contracts and salary schedules | NTA / NPS | 2024-2027 | CBA / salary schedule | direct PDF / public index | medium | contract cost only | Causal candidates for future educator expansion, not priority mechanism evidence. |
| NESA CBA folder | Newton Public Schools | current public folder | CBA index | public Google Drive folder | unclear | unclear | Acquisition lead only; needs bounded manual review if Newton non-safety CBA expansion becomes a priority. |

## Evidence Classification

The Newton route produced rich public bargaining-process evidence but no inspected document showed a clean peer-district wage comparison table or award-style non-safety reasoning equivalent to the Somerville police awards. The evidence is strongest for general wage rationale, proposal movement, mediation posture, settlement terms, and contract-cost structure.

The February 2024 MOA is the only inspected causal-corpus candidate, but it appears to cover multiple educator units and needs careful unit mapping and final-signature verification before any future `process_inbox.py` ingestion.

## Corpus-Handling Recommendation

Do not ingest Newton materials in this pass. Treat the proposals, mediation outlines, package comparisons, and strike-summary materials as `mechanism_proxy` or `discourse_candidate` leads. The repo does not currently have a clear discourse/proxy ingestion path, and these documents should not be forced into `contracts.csv`.

If Newton educator contracts become a later causal-corpus expansion target, use `process_inbox.py` only after verifying unit scope, term, source type, and provenance for each final CBA/MOA.

## Stop-Rule Notes

The pass stopped after the named public routes and six high-priority public PDFs. No public-records route was drafted or recommended. Meeting indexes were not crawled broadly, and agenda/video-only materials were not collected.

## Recommended Next Action

Use Newton as a high-value public mechanism-proxy case, not as a clean non-safety award/factfinding case. If more work is authorized, do a narrow manual review of specific School Committee packets from July 2023 through February 2024 for attached fiscal-impact or wage-comparison exhibits.
