# H1 Public-Source Strategy

**Date:** 2026-06-24

## Current H1 status

H1 remains plausible but underidentified.

The strongest mechanism evidence still comes from the Somerville police arbitration awards, where comparability reasoning is explicit and central. Worcester, Arlington, Georgetown, Franklin, and Wayland now provide matched structure, but they do not yet provide the same kind of public non-safety reasoning text. StateReference and official municipal portals help scale public CBA/MOA pairs, but they may not solve the core non-safety reasoning-document gap.

The 2026-06-24 school-committee recon slightly improves the public-only outlook because Newton, Somerville, and Boston all expose public meeting-materials routes that could contain bargaining or wage-setting proxy evidence. That does not change the pivot threshold yet, but it does justify one targeted packet-review pass before concluding that the non-safety reasoning-document gap is insurmountable in public sources.

The 2026-06-25 Franklin/Wayland official-portal ingestion strengthens the public-only CBA/MOA panel: the corpus reached 32 contracts across 9 cities, with 12 healthy matched safety rows in the coverage audit. Franklin adds a clean 2022-2025 exact-cycle portal batch. Wayland adds a 2020-2023 exact-cycle police/fire/DPW/library set plus a fire JLMC stipulated award, while also illustrating a source-type caveat: safety-side award evidence can still grow faster than comparable non-safety reasoning evidence.

This leaves the project closer to a first descriptive GABRIEL/reporting pass, but not to a clean causal test. Non-safety reasoning evidence remains thin, so any v9 run should be stratified at minimum by `source_type` and match tier rather than presented as a pooled safety-versus-non-safety result.

The 2026-06-25 GABRIEL v9 descriptive run confirms that caution. The overall safety mean exceeds the non-safety mean, but the high scores come from safety-side arbitration awards. The CBA-only and excluding-award samples have low comparability scores, so v9 strengthens the source-type/document-production caveat more than it strengthens an occupation-only H1 claim.

The 2026-06-26 Newton/Somerville/Boston mechanism-source recon improves the public-only route but does not close the identification gap. Boston produced the clearest public non-safety peer-wage lead: the BPS BTU negotiations page includes surrounding-district teacher salary comparisons. Newton and Somerville produced useful public bargaining-process, settlement-summary, and wage-rationale materials, but the inspected documents were mostly proposals, presentations, summaries, CBA indexes, or final CBAs rather than non-safety awards/factfinding reports. No new causal rows were ingested, and PRRs remain deferred.

## What would count as support for H1 without PRRs

- Public non-safety factfinding or arbitration-like reports that show wage-setting reasoning and can be compared directly to safety awards.
- Public meeting packets or bargaining exhibits showing that non-safety wage-setting relies less heavily on peer-community comparability than safety awards do.
- A larger matched CBA/MOA panel showing that safety documents more often contain comparability clauses, peer-community wage references, parity references, or arbitration-backstop language than non-safety documents from the same cities and cycles.

## Match-tier note

For the public CBA/MOA panel, exact-cycle matches remain the strongest evidence for wage-outcome comparisons. Overlapping-cycle matches should count as valid H1 text/mechanism comparisons because they keep city and period approximately fixed, even if contract start and end dates differ. Adjacent-cycle matches within roughly one to two years should be reported as exploratory rather than healthy.

The CBA/MOA panel also needs a source-type caveat: weak or absent comparability language in a final agreement does not prove comparability was absent from bargaining. CBAs and MOAs often preserve outcomes, not the parties' reasoning. Arbitration awards, factfinding reports, meeting packets, and bargaining exhibits are more useful for recovering explicit wage-comparison reasoning.

## What would weaken H1

- Public non-safety reasoning documents show comparability language that is as strong as or stronger than the safety-side award language.
- Safety CBAs/MOAs do not differ much from non-safety CBAs/MOAs once award documents are excluded.
- Comparability language appears to be mainly a property of arbitration/factfinding document type rather than occupation.

## Pivot hypotheses if H1 cannot be cleanly tested

### H2: Document-production / source-type hypothesis

Explicit comparability reasoning appears mainly in arbitration or factfinding documents, while ordinary CBAs and MOAs of all occupations suppress the reasoning that produced the final wage terms.

### H3: Arbitration-backstop / bargaining-friction hypothesis

Police and fire wage growth may reflect stronger impasse institutions and a more arbitration-centered bargaining environment even when final settled CBAs do not contain explicit comparability text.

### H4: Wage-MOA opacity hypothesis

Safety settlements may more often be recorded as short MOAs that preserve wage outcomes but omit mechanism clauses, while non-safety units more often appear as full restated CBAs. That document pattern itself may reveal different bargaining friction or institutional treatment.

### H5: Public-availability / selection hypothesis

The public corpus may overrepresent certain document types, employers, or disputes. Observed comparability language may therefore reflect which documents become public and durable online, not only how bargaining actually works.

## Recommendation

Use GABRIEL v9 as a descriptive baseline, not a causal test. Continue public-source H1 work for one more structured pass, with official municipal portals and mechanism-source searches as complementary routes.

Do not use PRRs unless the PI later reauthorizes them. Use the next pass to test whether public non-safety reasoning evidence can be found through DLR route checks, school-committee meeting materials, large-city labor portals, and capped official-portal candidates such as North Andover, Duxbury, Norwood, Ludlow, and Westwood. A v10 attribute such as `arbitration_or_impasse_backstop` should wait until the team reviews the v9 baseline.

If that pass still yields mostly CBA/MOA growth and no credible non-safety reasoning set, preserve H1 as suggestive and pivot the framing toward document type, arbitration backstops, and public-availability selection rather than forcing a clean occupation-only claim.
