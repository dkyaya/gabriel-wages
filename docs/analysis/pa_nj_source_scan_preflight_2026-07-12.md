# PA/NJ Source Scan Preflight — 2026-07-12

## Repo state at start

- Working directory: `/Users/joachimjohnson/Documents/RA_2026/Pol_Fire/gabriel-wages`
- Latest commit at start: `a1f2dc8 Plan national claim-driven corpus expansion`
- `git status`: working tree clean except untracked `.claude/` and `tmp/` (pre-existing, unrelated to this run)
- `data/contracts.csv`: 53 rows (unchanged going into this run)
- `data/city_coverage.csv`: 53 rows (unchanged going into this run)
- Baseline coverage: MA/TX/OH only. This is the first source-availability scan for Pennsylvania and New Jersey, per `docs/analysis/national_state_priority_rubric_2026-07-12.csv` (both tier_1) and `docs/analysis/two_week_claim_driven_expansion_plan_2026-07-12.md` (Week 1, item 1: "Run source-availability scans for tier-1 states in this order: Pennsylvania, New Jersey, Illinois, New York").

## Scope

- **States:** Pennsylvania and New Jersey only. Illinois and New York are explicitly deferred to a later scan (see Task D recommendation).
- **Cities (fixed list, per task instructions):**
  - Pennsylvania: Philadelphia, Pittsburgh, Allentown, Erie, Reading
  - New Jersey: Newark, Jersey City, Paterson, Elizabeth, Trenton
  - Note: this list differs from `national_source_targets_2026-07-12.csv`'s PA/NJ rows (which used Scranton and Camden instead of Reading and Elizabeth). This scan follows the task-specified city list; the national target CSV is updated in Task E to reflect what was actually scanned, without deleting the prior Scranton/Camden planning rows.
- **This is a source-availability scan only.** No documents are downloaded. No files are added to `corpus/`. No rows are added to `data/contracts.csv` or `data/city_coverage.csv`.
- **No GABRIEL/codify, Harvard Proxy, model, or API calls** of any kind in this run.
- **No FOIA/OPRA/RTKL/PRR** routes are used or recorded as viable in this scan. Access-restricted or paywalled sources are not bypassed.

## Source criteria

A candidate is recorded as a **causal_candidate = yes** only if it plausibly is, or points to, one of:
- A police CBA / FOP agreement / arbitration award / Act 111 award (PA).
- A fire CBA / IAFF agreement / interest-arbitration award (PA Act 111; NJ interest arbitration).
- A general municipal / AFSCME / CWA / clerical / public works / library / sanitation agreement (the non-safety comparator).
- A factfinding or arbitration award, if publicly posted.

Sources must be public and findable without bypassing login/paywall/access restrictions: official city sites, state labor-relations bodies (PA PLRB / PA Act 111 award repositories; NJ PERC), union locals (FOP lodges, IAFF locals, AFSCME councils/locals, CWA locals), or other reliable public repositories (e.g., municipal legislative/council document portals, state archives). Sources that are only about wages/contracts (news coverage, budget narratives) but do not appear to host or link the actual agreement/award text are marked `source_type_candidate=context_only` and `causal_candidate=no`, per task instructions — never `causal_candidate=yes`.

## Stop rules

- **Row cap:** stop recording candidate rows at 60 total across both states.
- **Per-city stop:** for any city where, after a reasonable public search, no findable safety CBA/award and no findable non-safety comparator emerge, log what was found (even if only context_only), mark `selection_priority=reject` or `needs_review`, and move on — do not exhaustively re-search.
- **No download/ingest/codify under any circumstance** in this run, regardless of how strong a candidate looks. Ingestion is a separate, later, reviewed step.
- **No FOIA/OPRA/RTKL/PRR routes** are recorded as the primary path for any row; if a city's only visible route is a public-records request, mark it `source_type_candidate=unknown` / `causal_candidate=no` / `selection_priority=reject` with a note, not as a viable candidate.
- **Stop scanning a state** once enough evidence exists to rank PA vs. NJ and to identify the strongest 2-4 candidate cities per state — this is a ranking exercise, not exhaustive coverage of all 10 cities to the same depth.

## Deliverables (this run)

1. `docs/analysis/pa_nj_source_scan_preflight_2026-07-12.md` (this file)
2. `docs/analysis/pa_nj_candidate_sources_2026-07-12.csv`
3. `docs/analysis/pennsylvania_source_scan_2026-07-12.md`
4. `docs/analysis/new_jersey_source_scan_2026-07-12.md`
5. `docs/analysis/pa_nj_source_scan_summary_2026-07-12.md`
6. Updated `docs/analysis/national_source_targets_2026-07-12.csv` (PA/NJ rows only — scan status and candidate notes)
7. Updated `PROGRESS.md` and `docs/analysis/chatgpt_handoff_latest.md`
8. Local commit only (no push, no remote inspection/configuration)
9. Relay bundle under `tmp/agent_relay_bundle_2026-07-12_HHMMSS/`
