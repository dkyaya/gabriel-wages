# Claim Consolidation Summary — 2026-07-12

## 1. Purpose

This run shifts the project from a mechanism inventory toward claim-centered reporting. The next report should be organized around claims, evidence, reasoning, counterevidence/limits, what would change our mind, and source needs. The mechanism inventory remains useful, but it should now serve the claim register rather than define the report structure.

## 2. Evidence Base Used

- Durable evidence layer: `docs/analysis/gabriel_codify_evidence_layer.csv`.
- Evidence rows: 781 total; 293 present; 488 not_found.
- Primary support filter: 284 verified-present rows (`evidence_status=present` and `viewer_verified=1`).
- Flagged/unverified present rows excluded from primary support: 9.
- Codified contracts: 37 of 53 contract rows.
- States/cities in codified layer: Massachusetts (Boston, Franklin, Georgetown, Seekonk, Somerville, Wayland), Texas (Austin, Houston, San Antonio), Ohio (Cincinnati, Cleveland, Columbus, Toledo).
- Supporting report assets used: source inventory, city mechanism matrix, state/occupation mechanism-presence tables, top-mechanisms table, report scaffold, appendix, graph audit, and codify audits.

## 3. Candidate Claims Overview

| claim_id | short claim | status | strength | report_ready |
|---|---|---|---|---|
| CLM-2026-07-12-01 | Ohio matched triads | supported_provisional | moderate | yes |
| CLM-2026-07-12-02 | Texas institutional unevenness | supported_provisional | moderate | yes |
| CLM-2026-07-12-03 | Massachusetts cross-occupation base | supported_provisional | moderate | maybe |
| CLM-2026-07-12-04 | Safety pressure conversion channels | supported_provisional | moderate | maybe |
| CLM-2026-07-12-05 | Non-safety classification/admin channel | supported_provisional | moderate | maybe |
| CLM-2026-07-12-06 | Arbitration distinction | supported_provisional | strong | yes |
| CLM-2026-07-12-07 | Comparator wage evidence gap | needs_more_evidence | low | no |
| CLM-2026-07-12-08 | Texas non-safety outside Houston gap | needs_more_evidence | low | no |

## 4. Strongest Current Claims

- **CLM-2026-07-12-06 — Arbitration distinction** is strongest because the San Antonio police contract contains both formal impasse and grievance-arbitration language and codify separated them correctly; other Texas/Ohio/MA rows reinforce the distinction.
- **CLM-2026-07-12-01 — Ohio matched triads** is strongest as a substantive design claim because Ohio has four codified police/fire/non-safety city triads under the same statewide bargaining framework.
- **CLM-2026-07-12-02 — Texas institutional unevenness** is strong as a source/design claim, not as a substantive wage-gap claim: Houston is matched, Austin is safety-adjacent, and San Antonio is police/fire-only.

## 5. Claims That Need More Evidence

- **CLM-2026-07-12-07 — Comparator wage evidence gap** is not report-ready as a substantive mechanism claim. The evidence layer has one verified Somerville row, while the expanded Texas/Ohio audit documents a San Antonio false negative.
- **CLM-2026-07-12-08 — Texas non-safety outside Houston gap** is intentionally not report-ready. It needs public, in-window general municipal non-safety sources in Austin or San Antonio, or a documented reason they are unavailable.
- **CLM-2026-07-12-04 and CLM-2026-07-12-05** are maybe-ready: both are useful interpretive claims, but binary codify and curated windows mean they should be stated as evidence patterns, not as causal wage explanations.

## 6. Counterevidence / Limits

- **Texas non-safety limitation outside Houston:** Houston HOPE is the only genuine Texas non-safety comparator currently codified.
- **Austin safety-adjacent caveat:** Austin EMS/nurse_health is public-safety-adjacent and should not be treated as a general non-safety municipal comparator.
- **San Antonio unmatched police/fire-only issue:** San Antonio contributes police and fire contracts but no matched non-safety row in the current corpus.
- **Binary codify limitation:** GABRIEL/codify detects present/not_found in curated windows; it does not estimate effect size, intensity, causality, or full-document absence.
- **San Antonio comparator false negative:** the expanded Texas/Ohio audit documents genuine comparator wage language in San Antonio police, but codify returned `not_found`; the register treats this as a limitation, not model support.
- **Flagged/unverified rows excluded:** nine present rows with `viewer_verified=0` were excluded from primary support, including the previously flagged Cleveland fire interest-arbitration row.

## 7. Recommended Next Source-Expansion Priorities

Prioritize expansion that tests claims rather than generic accumulation:

1. **Texas non-safety sources if available** — especially San Antonio and Austin general municipal units, because they directly test CLM-2026-07-12-02 and CLM-2026-07-12-08.
2. **Additional matched triads in public-CBA states** — states that can supply police, fire, and at least one non-safety unit in overlapping cycles will test whether Ohio’s pattern travels.
3. **States with impasse/arbitration contrast** — Pennsylvania/New Jersey-style environments, pending source verification, would test the arbitration distinction and safety conversion-channel claims.
4. **Repeat cycles for current cities** — Columbus, Cleveland, Cincinnati, Toledo, Franklin, Seekonk, and Houston repeat cycles would test whether current patterns persist within cities over time.
5. **Comparator-specific sources** — arbitration awards, factfinding reports, and wage studies should be prioritized for peer/comparator wage language because base CBA windows under-detect it.

## 8. Next Recommended Report Format

Use a repeating structure for each major report claim:

- Claim.
- Evidence.
- Reasoning.
- Counterevidence/limits.
- What would change our mind.
- Source needs.

The accompanying files are `claim_register_2026-07-12.csv`, `claim_evidence_matrix_2026-07-12.csv`, and `claim_readiness_table_2026-07-12.csv`.
