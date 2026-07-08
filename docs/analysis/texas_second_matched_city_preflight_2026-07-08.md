# Texas Second Matched-City Preflight — 2026-07-08

**Type:** preflight review only. Confirms repo state and scopes this run before any bounded web search (Task B/C) or fetch (Task D). No document downloaded or stored in this task.

## 1. Repo state at session start

- `git status`: clean except untracked `tmp/` (expected — holds prior sessions' relay bundles).
- Latest commit: `4cd7550 Resolve Houston fire source` (confirmed via `git log --oneline -5`), matching the task's stated starting point.
- `data/contracts.csv`: 43 data rows.
- `data/city_coverage.csv`: 43 data rows.
- These counts match the "around 43 contracts / 43 coverage rows" expectation. No unexpected uncommitted changes. Proceeding.

## 2. Current Texas rows in `data/contracts.csv`

| obs_id | city_id | occupation_class | safety_flag | cycle | source_type |
|---|---|---|---|---|---|
| `tx_houston_police_2024` | tx_houston | police | 1 | 2024-07-01 to 2025-06-30 | cba |
| `tx_houston_other_2024` | tx_houston | other | 0 | 2024-11-01 to 2027-06-30 | cba |
| `tx_houston_fire_2024` | tx_houston | fire | 1 | 2024-07-01 to 2029-06-30 | arbitration_award |
| `tx_austin_police_2024` | tx_austin | police | 1 | 2024-10-29 to 2029-09-30 | cba |
| `tx_austin_fire_2023` | tx_austin | fire | 1 | 2023-09-24 to 2025-09-30 | cba |

## 3. Current Ohio rows in `data/contracts.csv`

| obs_id | city_id | occupation_class | safety_flag | cycle | source_type |
|---|---|---|---|---|---|
| `oh_columbus_police_2023` | oh_columbus | police | 1 | 2023-12-09 to 2026-12-08 | cba |
| `oh_columbus_fire_2023` | oh_columbus | fire | 1 | 2023-11-01 to 2026-10-31 | cba |
| `oh_columbus_other_2024` | oh_columbus | other | 0 | 2024-04-01 to 2027-03-31 | cba |
| `oh_cleveland_police_2025` | oh_cleveland | police | 1 | 2025-04-01 to 2028-03-31 | cba |
| `oh_cleveland_fire_2025` | oh_cleveland | fire | 1 | 2025-04-01 to 2028-03-31 | cba |
| `oh_cleveland_other_2022` | oh_cleveland | other | 0 | 2022-04-01 to 2025-03-31 | cba |

## 4. Matched-city status by state

- **Houston, TX — matched.** Police + fire, both healthy overlap-cycle matches against the non-safety HOPE/AFSCME Local 123 row (2024-2027), per the last `ingest/audit_coverage.py` run.
- **Austin, TX — NOT matched.** Police (2024-2029) and fire (2023-2025), but **no non-safety row exists**. `ingest/audit_coverage.py` currently lists both Austin safety units as fully unmatched (no exact, overlap, or adjacent non-safety comparison). Prior session (`texas_ohio_heldout_source_resolution_2026-07-08.csv`) confirmed Austin's AFSCME Local 1624 document is a City Council consultation-policy resolution (Res. No. 20260122-049), not a wage-setting CBA — it was deliberately **not** ingested as causal. This is the target of Task B in this run.
- **Columbus, OH — matched.** Police + fire, both healthy overlap-cycle matches against AFSCME Local 1632 (other, 2024-2027).
- **Cleveland, OH — matched** (adjacent, not exact/overlap). Police (2025-2028) and fire (2025-2028) currently show only "exploratory adjacent" matches against AFSCME Local 100 (other, 2022-2025) per `ingest/audit_coverage.py` — the non-safety cycle ends in 2025 while the safety cycles start in 2025, so this is flagged adjacent rather than healthy overlap. Still counts as Ohio's second matched city per this run's task framing (the task explicitly lists Cleveland as an already-matched second Ohio city), but the adjacency is worth noting for later report language.
- **Backup Texas cities already scoped in planning files:**
  - **Fort Worth** (`texas_ohio_multicity_source_targets_2026-07-08.csv`): Ch.174 full bargaining for fire (Fort Worth Professional Firefighters Association), Ch.142 meet-and-confer for police (FWPOA). Non-safety channel: **"None confirmed (Pay for Performance Program for non-civil-service employees instead)"** — i.e., the prior scan found no negotiated non-safety wage-setting mechanism at all, only a unilateral city pay-for-performance program. Current-cycle full CBA text for both police and fire was not directly located in the prior session (only referenced via city event pages). Marked `backup`, `priority=useful`.
  - **San Antonio** (`texas_ohio_multicity_source_targets_2026-07-08.csv`): Ch.174 full bargaining for both police (SAPOA) and fire (SAFD), non-compulsory. Non-safety channel: **"None identified."** Police/fire CBAs are hosted on a dedicated `sanantonio.gov/City-Attorney/CollectiveBargaining` portal (source_availability=medium-high). Marked `backup`, `priority=useful`.
  - Both backup cities' prior planning notes are consistent with Texas Government Code Chapter 617's general prohibition on public-sector bargaining outside statutorily carved-out channels — Houston's Chapter 146 non-safety channel is population-gated to Houston alone among the cities scanned so far, so it is a real possibility that neither Fort Worth nor San Antonio has *any* non-safety wage-setting CBA to find, not merely an unsearched one. This is treated as a genuine open question to test in Task C, not a foregone conclusion.

## 5. Why a second Texas matched city is required before GABRIEL

The project's design (per `CLAUDE.md`) is a cross-occupation comparison holding city × time fixed: every safety unit needs at least one matched non-safety unit in the same city and bargaining cycle. For a controlled state-comparison pilot, the project wants **two matched cities per comparison state** so that within-state city variation can be distinguished from state-level institutional effects, mirroring Ohio's current Columbus+Cleveland pair. Texas currently has only one fully matched city (Houston); Austin is "two-thirds" there (both safety tiers present, no non-safety partner) and is dead weight for the matched-comparison design until resolved, per `AGENTS.md`'s coverage-discipline rule.

## 6. Exact source-resolution criteria for this run

A non-safety source is eligible for `fetch_and_ingest` only if it is an actual wage-setting agreement: a CBA, labor agreement, meet-and-confer agreement, or another public municipal agreement containing real negotiated wage/compensation terms for non-safety employees. It is **not** eligible if it is only a consultation policy without wage terms, an employee handbook, an HR classification/pay-plan page, a city budget, an ordinance summary, a city webpage, a news story, or a source-discovery page — these may be recorded as context/source-discovery but must not enter `data/contracts.csv`.

Priority order for this run: (1) Austin non-safety; (2) Fort Worth matched set (police + fire + non-safety, if a non-safety source can be found); (3) San Antonio matched set. At most one backup city will be ingested, and only the minimum sources needed to establish a matched pair (at most 3 causal sources unless one additional document is clearly required for identity/coverage). If no valid non-safety source is found in Austin, Fort Worth, or San Antonio, this run will document the search and recommend either continuing the search in another Texas city or proceeding to a smaller GABRIEL/codify pilot with Houston as Texas's sole fully matched city — not force a lower-quality source into the causal corpus.
