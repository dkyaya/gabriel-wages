# Claim-Testing Source-Wave Methodology

**Type:** durable project standard (like `source_planning_csv_hygiene_standard_2026-07-08.md` and `recognition_clause_first_classification_standard_2026-07-08.md`). No "as of" freeze — update in place if the sequence itself changes; do not fork a new dated copy for routine use.

**Status:** first saved 2026-07-12, generalized from the MA/TX/OH build-out and the Pennsylvania/New Jersey pilot source-availability scan (`pa_nj_source_scan_preflight_2026-07-12.md` through `pa_nj_source_scan_summary_2026-07-12.md`).

## 1. Purpose

This project's early work (through the 2026-07-10 final report) was organized as a **mechanism inventory**: what clauses exist, surfaced city-by-city and state-by-state. That proved the pipeline works — grounded, contamination-checked, verbatim-sourced — but it does not, by itself, tell a reader what the corpus supports arguing.

Starting with the 2026-07-12 claim-centered consolidation (`claim_centered_corpus_expansion_strategy_2026-07-10.md`, `claim_register_2026-07-12.csv`), the project shifted to **claim-driven** work: every expansion wave should exist to test, strengthen, weaken, or bound a specific claim or hypothesis — not to accumulate sources for their own sake. This document is the repeatable procedure for running one of those waves. **Future agents should follow this sequence by default** rather than re-deriving a source-expansion process from scratch each session.

## 2. Repeatable source-wave lifecycle

Run these 13 steps in order for every expansion wave. A wave does not have to complete all 13 steps in one session — but later steps should not start until earlier ones for that wave are done, and each step's output should be a named, dated artifact another agent can pick up from.

1. **Choose claims/hypotheses served.** Start from `claim_register_2026-07-12.csv` and `hypothesis_tracker_2026-07-12.csv`, not from a list of states. A wave that cannot name which claim_id(s)/hypothesis_id(s) it serves is not yet scoped.
2. **Choose 1-2 states.** Use `national_state_priority_rubric_2026-07-12.csv` (tier and institutional-contrast value) plus the claim's own `suggested_states` field in `claim_driven_source_needs_2026-07-12.csv`. Prefer states offering genuine institutional contrast over states that would just re-confirm an existing pattern.
3. **Scan around 5 cities per state.** A bounded, public-web, non-download source-availability scan — see `pa_nj_source_scan_preflight_2026-07-12.md` for a worked example of scope/stop rules. This step never downloads or ingests.
4. **Mark candidates: `ingest_next` / `needs_review` / `hold` / `reject`.** Record every candidate in a `csv.writer`-built, parse-back-validated CSV per `source_planning_csv_hygiene_standard_2026-07-08.md`. A row that is only a union/agency homepage or a news item confirming a contract exists, without a document link, is `context_only`/`needs_review`, never `ingest_next`.
5. **Promote only sources with clear provenance and claim value.** Prefer city-government, state-labor-board, or union-local domains over third-party document hosts (e.g., Scribd). A source with unclear jurisdiction (e.g., a same-named county vs. city, or a same-named city in a different state) must be resolved before promotion — see the Erie County NY and Passaic County exclusions in `pa_nj_candidate_sources_2026-07-12.csv` for worked examples of this failure mode.
6. **Ingest 6-12 sources.** A reviewed, bounded ingestion batch — never a single state's entire candidate list at once. Prioritize completing matched triads (police + fire + non-safety) over adding more safety-only sources.
7. **Validate contracts/coverage/corpus.** `python scripts/validate.py` must exit 0; `data/city_coverage.csv` must reflect the new rows; full-text files must be correctly pointed to in `corpus/`.
8. **Extract deterministic mechanism excerpts.** Before any GABRIEL/codify call, run the project's deterministic extraction step so codify has a grounded evidence window to work from, not raw full documents.
9. **Codify 8-15 sources.** Run GABRIEL/codify in a capped, controlled wave against the newly ingested sources, using the existing 19-attribute codebook.
10. **Audit grounding.** Every `present` row must pass the source-grounding check (verbatim substring match against the source window). Flag, do not silently include, anything that fails. Unverified/flagged rows are excluded from primary claim support (see `claim_consolidation_summary_2026-07-12.md` Section 6 for the standing precedent: 9 flagged rows currently excluded).
11. **Rebuild viewer.** Regenerate `docs/analysis/gabriel_codify_excerpt_browser_latest.html` so the new evidence is inspectable against its source.
12. **Update claim register.** After every codify wave, propagate results into `claim_register_2026-07-12.csv`, `claim_evidence_matrix_2026-07-12.csv`, `claim_readiness_table_2026-07-12.csv`, `hypothesis_tracker_2026-07-12.csv`, and `claim_driven_source_needs_2026-07-12.csv` (see Section 5 below).
13. **Decide next source gap.** Close the loop: which claim is still weakest, which state/city gap is now most binding, and what should the next wave's Step 1 be. Write this down explicitly (a "next steps" section is not optional) so the next agent does not have to re-derive it.

Steps 1-5 are **source-availability scanning** (this project's current PA/NJ pilot stage). Steps 6-11 are **ingestion and codify** (not yet authorized for PA/NJ as of this writing). Step 12-13 apply after every codify wave, not just the first one.

## 3. Promotion rules

- **Matched triads are highest value.** A city offering police + fire + at least one genuine non-safety/general-municipal unit in overlapping cycles should be prioritized over any single-occupation source, regardless of how well-documented that single source is.
- **Non-safety sources are bottlenecks and high priority.** Every wave to date (MA/TX/OH, and now the PA/NJ pilot) has found non-safety sources harder to locate than police/fire sources. Search for the non-safety leg early in a city scan, not last.
- **Interest-arbitration/factfinding/impasse sources are high value for conversion-channel claims.** These source types directly serve the arbitration-distinction claim (`CLM-2026-07-12-06`) and the comparator-evidence hypothesis (`H5`), both of which are underpowered in the current evidence layer.
- **Safety-only sources are allowed only when serving a specific claim.** A police-only or fire-only source is not disqualified outright, but it must be justified by name against a claim_id/hypothesis_id (e.g., testing the interest-vs-grievance arbitration distinction) rather than added as generic accumulation.
- **No FOIA/PRR/OPRA/RTKL requests unless explicitly reauthorized by the PI/user.** This applies to every wave by default. A source reachable only through a public-records request is `reject` for the causal corpus unless a future task explicitly reauthorizes that route.
- **Do not add context-only sources to the causal corpus.** News coverage, budget narratives, court decisions about a contract, and agency program-description pages are useful for locating the real document but are never themselves `causal_candidate=yes`.
- **Recognition-clause-first classification.** Per `recognition_clause_first_classification_standard_2026-07-08.md`, a broad non-safety agreement's `occupation_class` stays provisional `other` until the recognition/coverage clause is actually read — do not infer a specific class from a union's name (e.g., do not assume "Teamsters" means sanitation/public-works without reading the document).

## 4. Evidence and scoring rules

- **Deterministic extraction before GABRIEL.** Mechanism-evidence windows are built with deterministic extraction first; GABRIEL/codify scores against that window, it does not freely search the full document.
- **Codify in controlled waves.** Cap each codify run (historically 4-10 live calls per wave); never run an open-ended batch.
- **Binary present/not_found for now.** Codify has no native confidence/unclear field. A `not_found` result means "not found in this curated window," not "proven absent from the full document" — see the documented San Antonio comparator false negative in `claim_consolidation_summary_2026-07-12.md`.
- **Strict source-grounding audit.** Every `present` excerpt must be a verbatim substring of the source window (anti-paraphrase check). This guard is never relaxed, per `AGENTS.md`.
- **Flagged/unverified rows excluded from primary support.** A row with `viewer_verified=0` may remain in the evidence layer for transparency, but must not be cited as primary support for any claim.

## 5. Claim update rules

After every codify wave, update all four of the following together — they are meant to stay in sync, not drift independently:

- `claim_register_2026-07-12.csv` — full claim record (scope, status, evidence, reasoning, counterevidence, what-would-change-our-mind, source needs).
- `claim_evidence_matrix_2026-07-12.csv` — claim_id × evidence_id mapping, using only verified-present rows as primary support.
- `hypothesis_tracker_2026-07-12.csv` — support level, best evidence, counterevidence, and the explicit strengthen/weaken decision rules for each hypothesis.
- `claim_driven_source_needs_2026-07-12.csv` — updated source-need priority and specific-sources-needed fields per claim.

Each claim should end the update as one of: **stronger** (more/better evidence, status may move toward `supported_provisional` → closer to a stable finding), **weaker** (new counterevidence or a documented false negative), **more bounded** (scope narrowed to what the evidence actually supports), or **explicitly marked as needing more evidence** (`needs_more_evidence`, `report_ready=no`). A claim that is touched by a wave and ends in exactly the same state it started in should be flagged as a sign the wave did not actually test anything.

## 6. Report standard

- **Reports are not mechanism inventories.** Do not default to a report structured as "mechanism, by geography." That structure was appropriate for the pipeline-validation phase and is no longer the default.
- **Reports should make bounded claims with evidence and reasoning.** Every reported finding should follow the six-part structure from `claim_centered_corpus_expansion_strategy_2026-07-10.md` Section 2: **Claim → Evidence → Reasoning → Counterevidence/limits → What would change our mind → Source needs.**
- **Avoid national/causal overclaims until design supports them.** Claims stay scoped to what is actually coded (e.g., "in the currently coded Ohio matched triads...") rather than generalized to a state, region, or the nation. A claim resting on source-availability information alone (not yet codified) must be explicitly labeled a hypothesis, not evidence — see `pa_nj_state_city_claim_notes_2026-07-12.md` and `state_city_claim_map_2026-07-12.csv` for the PA/NJ application of this rule.

## 7. Pointer

Future agents doing source expansion or report planning should read this document first, then `claim_register_2026-07-12.csv` / `hypothesis_tracker_2026-07-12.csv` to pick Step 1, before starting a new state scan. See also the concise pointer in `AGENTS.md`.
