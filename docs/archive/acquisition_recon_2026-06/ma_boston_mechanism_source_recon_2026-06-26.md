# Boston Mechanism-Source Recon

**Date:** 2026-06-26  
**Scope:** bounded public-only review of Boston non-safety wage-reasoning sources. No PRRs, licensed sources, broad crawling, or GABRIEL runs.

## Purpose

Assess whether Boston public education-labor sources contain non-safety wage-reasoning documents, especially peer/surrounding-district comparisons, settlement summaries, fiscal-impact materials, or public presentations.

## Research Value

Boston is high value because BPS and BTU publish bargaining updates, public presentations, salary grids, and CBA links. Unlike most ordinary CBA portals, the BPS BTU negotiations page includes an explicit surrounding-district salary-comparison table, making Boston the strongest public non-safety peer-wage lead found in this bounded pass.

## Priority Source Routes Checked

| route | status | notes |
|---|---:|---|
| `https://www.bostonpublicschools.org/school-committee/btu-contract-negotiations` | checked | Public BPS negotiations page with compensation rationale, proposal-cost discussion, and surrounding-district teacher salary comparison. |
| `https://resources.finalsite.net/images/v1744817505/bostonpublicschoolsorg/xur4pktuwowr7kgoeiow/FINALApril162025BTUCBAPresentation.pdf` | checked | Public direct PDF presentation to School Committee for the April 2025 BTU CBA. |
| `https://btu.org/contract-bargaining-updates/` | checked | Public BTU bargaining-update index. Targeted pages fetched but did not expose much clean body text via simple public HTML fetch. |
| `https://btu.org/contracts/` | checked | Public BTU contracts route. |
| `https://ohr.bostonpublicschools.org/careers1/salary-grids-cbas` | checked | Public BPS OHR salary-grid and CBA index for BTU and other non-safety units. |

## Search Terms Used

`comparable`, `comparison`, `peer`, `market`, `salary`, `wage`, `compensation`, `lowest-paid workers`, `paraprofessionals`, `market rate adjustment`, `fiscal impact`, `supplemental appropriation`, `collective bargaining reserve`, `contract cost`, `inclusion`, `staffing`, `retention`, `bargaining summary`, `tentative agreement`, `memorandum of agreement`

## Candidate Evidence Table

| candidate | source owner | date/cycle | type | access | wage reasoning | comparability signal | recommendation |
|---|---|---:|---|---|---|---|---|
| BPS BTU contract-negotiations page | BPS | 2024-2025 | bargaining update | public HTML | high | peer wage comparison | Mechanism proxy; strongest public non-safety peer-wage lead found. |
| April 16 2025 BTU CBA School Committee presentation | BPS | 2025-04-16 | school committee presentation | direct PDF | high | general wage rationale | Mechanism proxy; do not ingest. |
| BTU bargaining-updates index | BTU | 2024-2025 | bargaining update | public HTML | medium | general wage rationale | Mechanism proxy / lead only. |
| BTU contracts page | BTU | current public page | CBA index | public HTML | low | none | Acquisition lead only for final agreements. |
| BPS OHR salary grids and CBAs page | BPS | current public page | salary schedule / CBA index | public HTML | medium | contract cost only | Acquisition lead for future CBA expansion, not current mechanism evidence. |
| BPS non-safety CBA links: cafeteria, custodians, bus monitors, administrative guild | BPS | multiple cycles | CBA index | public Google Drive / public HTML | low | none | Future causal candidates only if the project expands Boston non-safety rows. |

## Evidence Classification

Boston produced the clearest explicit peer-wage evidence in this pass. The BPS negotiations page includes a table comparing Boston teacher salaries with surrounding districts for school year 2024-2025. This is a mechanism proxy rather than a causal row because it is a public bargaining/negotiations page, not a final CBA, MOA, award, stipulated award, or factfinding report.

The April 2025 School Committee presentation gives wage and implementation rationale for the BTU CBA, including low-wage worker increases and supplemental-appropriation next steps. It does not appear to be an award or final agreement and should not be forced into `contracts.csv`.

## Corpus-Handling Recommendation

Do not ingest Boston materials in this pass. The strongest evidence is public bargaining-page and presentation material, which belongs in a future discourse/proxy mechanism system if the repo adds one. BPS OHR CBA links can support future causal-corpus expansion but would not solve the immediate non-safety reasoning gap by themselves.

## Stop-Rule Notes

The pass stopped after the named BPS/BTU routes, one direct PDF presentation, and a few targeted public HTML bargaining-update pages. No broad crawl was run, and no agenda-only, video-only, login, or blocked materials were collected.

## Recommended Next Action

Prioritize Boston for a future mechanism-proxy coding pass because it supplies the strongest explicit public peer-wage comparison. If additional public-only work is authorized, inspect City Council supplemental-appropriation materials for BTU contract-cost memos and retain them as mechanism proxies unless they include a final agreement.
