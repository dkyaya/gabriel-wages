# Claim-Centered Corpus Expansion Strategy — 2026-07-10

Purpose: set direction for the next phase of this project. This memo does not change data, corpus, codify outputs, or the final report. It is a planning document only.

## 1. Why the project is ready to shift

The foundational layer is now in place:

- **Schema discipline** (`docs/schema.md`) — a stable, validated causal/discourse two-corpus design with controlled vocabularies enforced by `scripts/validate.py`.
- **Corpus discipline** — verbatim-only capture, provenance required on every row, matched-comparison tracking via `data/city_coverage.csv`.
- **Source hygiene** — a documented CBA source-verification standard (findable source, safety contract present, matched non-safety present) applied before collection, plus a licensed-vs-public intake separation (`ingest/fetchers/` vs. `inbox/` + manifest) that keeps ToS-sensitive sources out of scrapers.
- **Recognition-clause-first classification** — units are classified from the contract's own recognition clause, not inferred.
- **GABRIEL/codify pipeline** — a working, capped, grounding-checked codify pass (`scripts/gabriel_codify_pilot.py`) has now run across Massachusetts, Texas, and Ohio sources, producing a 781-row evidence layer (293 present, 284 verified present) with anti-paraphrase and contamination checks built in.
- **Local evidence viewer** — `docs/analysis/gabriel_codify_excerpt_browser_latest.html`, letting a reader inspect every coded excerpt against its source.
- **A first mechanism-evidence report** — exported as DOCX/PDF (`docs/final_reports/deeper_look_safety_non_safety_wage_mechanisms_2026-07-10.*`), organized around mechanism categories (interest arbitration, comparability clauses, me-too clauses, etc.) surfaced city-by-city and state-by-state.

That first report did its job: it proved the mechanism categories are codeable and the pipeline is trustworthy (grounded, contamination-checked, verbatim-sourced). But it is organized as a **mechanism inventory** — what mechanisms appear, scattered across cities and states — rather than as **claims backed by evidence and reasoning**. A reader finishes it knowing what exists in the corpus, not what the corpus supports arguing.

**Future reports should not be organized as mechanism inventories scattered across cities/states.** The next phase should shift the unit of reporting from "mechanism, by geography" to "claim, with its evidence and limits made explicit."

## 2. New report standard

Every future report section (and ultimately the report itself) should be organized around:

1. **Claim** — a specific, falsifiable statement.
2. **Evidence** — which coded excerpts / contracts / cities support it.
3. **Reasoning** — why this evidence supports this claim, spelled out, not implied.
4. **Counterevidence / limits** — what cuts against the claim, or what the claim does not cover.
5. **What would change our mind** — the evidence that would weaken or overturn the claim.
6. **Source needs** — what additional sourcing would strengthen or test the claim.

Reports should make claims only at the level the evidence supports. Claims can be provisional or bounded — that is expected and fine — but they must be **explicit** about their own scope, not implicitly broad.

## 3. What "claim-centered" means here

**Acceptable claim forms** (bounded, scoped, evidence-anchored):

- "In the currently coded Ohio matched triads, police and fire agreements more consistently show wage-conversion channels than non-safety agreements."
- "Texas evidence suggests safety wage-setting channels are more institutionally specialized than non-safety channels, but the non-safety comparison remains weaker outside Houston."
- "Across the current corpus, the strongest evidence pattern is not generic job difficulty, but the combination of occupational pressure with bargaining/impasse/premium-pay conversion mechanisms."

**Avoid:**

- "The wage gap is caused by X" — unless a future research design (not just coded-text pattern matching) actually supports causal language.
- Broad state or national claims before corpus scale supports them.
- Claims resting on a single vivid excerpt rather than a pattern across multiple matched units.

## 4. Corpus expansion goals

The next expansion should be substantially larger and more systematic than the MA/TX/OH build-out:

- More matched city triads (safety + matched non-safety, same city, overlapping cycle).
- More states, chosen deliberately (see Section 6).
- More non-safety comparisons — the current corpus's weakest point is non-safety depth outside a few anchor cities (e.g., Houston in Texas).
- Stronger coverage of ordinary civilian municipal units (clerical, public works), not just the "easy" comparison classes.
- More repeated bargaining cycles per unit where possible, to see within-unit change over time, not just cross-sectional snapshots.
- Better source-type balance: CBAs, interest-arbitration/factfinding awards, and final agreements, rather than leaning on whichever type is easiest to find in a given state.

## 5. Suggested expansion design

A staged design, each stage gated on the prior one:

- **Stage 1 — Consolidate current MA/TX/OH evidence into claim candidates.** Mine the existing 781-row evidence layer for patterns strong enough to state as provisional claims (see Task D template and Section 8 below). This requires no new sourcing or codify work.
- **Stage 2 — Source-availability scan for next states.** Before collecting anything, verify (per the existing CBA source-verification standard) that candidate states actually have findable, public safety-and-matched-non-safety sources in the 2014–2024 window. Do not commit to a state on institutional-relevance grounds alone.
- **Stage 3 — Add 3–5 new states**, chosen for institutional contrast and confirmed public source availability (not availability alone — contrast matters, or the expansion just re-confirms what MA/TX/OH already show).
- **Stage 4 — Codify the expanded corpus** using the existing pipeline, with the same grounding/contamination checks.
- **Stage 5 — Produce a claim-centered report**, structured per Section 2, drawing on the full expanded evidence layer.

## 6. Candidate next states

Provisional candidates, pending Stage 2 source-availability scans — none of these are committed yet:

- **Pennsylvania** — Act 111 gives a distinct, well-documented public-safety interest-arbitration regime; strong potential for a clean safety/non-safety institutional contrast (safety units arbitrate under Act 111, non-safety units typically bargain under separate PERA rules).
- **New Jersey** — active interest-arbitration and municipal-bargaining environment; likely comparable institutional richness to Massachusetts.
- **Illinois** — large-city and suburban municipal bargaining with plausible source availability (Chicago plus a deep suburban bench), though it needs verification.
- **New York** — a rich bargaining environment (Taylor Law), but flagged as likely to carry a heavier source-management burden (large number of jurisdictions, varied hosting) — worth scanning but not assuming.
- **California** — strong bargaining activity and likely source availability, but very broad and institutionally complex (hundreds of charter cities, varied civil-service rules) — higher scoping cost per unit of evidence gained.
- **Florida, North Carolina, or Tennessee** — potential **contrast cases**: weaker or different public-safety bargaining channels (several are more restrictive on public-sector bargaining generally), useful if source availability supports a real comparison rather than mostly absent data.

**The next step is a source-availability scan (Stage 2), not a commitment to any of these states.** A state should only advance to collection once it passes the same three-part verification standard (findable source, safety contract present, matched non-safety present) already used for MA/TX/OH.

## 7. Evidence management

To support claim-centered reporting going forward, recommend building:

- **A claim register** (CSV) — one row per candidate claim, its scope, its supporting/counter evidence, and its status. Template created this run: `docs/analysis/claim_register_template_2026-07-10.csv`.
- **A source inventory by claim** — which sources underlie which claim, so a claim's evidentiary weight can be audited directly rather than re-derived.
- **A claim-to-evidence matrix** — a mapping table (claim_id × obs_id / evidence_id) making explicit which coded excerpts back which claims, so evidence reuse across claims is visible and gaps are visible too.
- **A minimum evidence threshold for report claims** — e.g., a claim should not appear in a final report as more than "needs more evidence" until it is backed by a specified minimum number of matched units/cities, to prevent single-excerpt overclaiming.
- **Explicit counterevidence tracking** — every claim register row should have a real counterevidence_ids field, not left blank by default; a claim with no counterevidence considered is a claim that hasn't been stress-tested.
- **Viewer filters organized around claims as well as mechanisms** — the existing HTML evidence viewer is organized by mechanism/attribute; a claim-oriented filter view (or a second viewer mode) would let a reader jump straight to "show me everything behind claim C3."

## 8. Next recommended prompt

Recommend the next coding-agent prompt should:

1. Create a claim register from the current 781-row evidence layer (using the template in `docs/analysis/claim_register_template_2026-07-10.csv` as the schema, replacing its illustrative draft rows with real candidates).
2. Identify 5–8 candidate claims directly from patterns already visible in the coded evidence (e.g., mechanism co-occurrence patterns by state/occupation), each scoped to what the current corpus actually supports.
3. Map each claim to its supporting evidence (contract IDs, evidence-layer row IDs) and explicitly flag its gaps — what would need to be true, or what would need to be added, for the claim to move from `draft` to `supported_provisional`.
4. Only after that consolidation is done, run a source-availability scan (Stage 2 above) for candidate next states, starting with Pennsylvania and New Jersey given their institutional-contrast potential.

This ordering matters: consolidating existing evidence into claims first will likely sharpen exactly which kind of new-state evidence is actually needed, rather than expanding the corpus first and hoping the right comparisons fall out of it.
