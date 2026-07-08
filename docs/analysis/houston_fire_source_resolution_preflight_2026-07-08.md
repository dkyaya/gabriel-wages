# Houston Fire Source-Resolution Preflight — 2026-07-08

**Type:** preflight review only. Confirms repo state and scopes this narrow, single-target run before any bounded web search (Task B) or fetch (Task C). No document downloaded or stored in this task.

## 1. Repo state at session start

- `git status`: clean except untracked `tmp/` (expected — holds prior sessions' relay bundles).
- Latest commit: `6ce5080 Resolve Texas and Ohio held-out sources` (confirmed via `git log --oneline -5`), matching the task's stated starting point.
- `data/contracts.csv`: 42 data rows.
- `data/city_coverage.csv`: 42 data rows.
- These counts match the "around 42 contracts / 42 coverage rows" expectation. No unexpected uncommitted changes. Proceeding.

## 2. Existing Houston rows in `data/contracts.csv`

| obs_id | occupation_class | safety_flag | cycle | source_type | full_text_path |
|---|---|---|---|---|---|
| `tx_houston_police_2024` | police | 1 | 2024-07-01 to 2025-06-30 | cba | `corpus/tx_houston/tx_houston_hpou_police_meet_confer_2024.pdf` |
| `tx_houston_other_2024` | other | 0 | 2024-11-01 to 2027-06-30 | cba | `corpus/tx_houston/tx_houston_hope_afscme123_meet_confer_2024.pdf` |

No Houston fire row exists yet. The immediately preceding session (`texas_ohio_heldout_source_resolution_2026-07-08.csv`) found this target `unresolved`: the only houstontx.gov PDF linked from the press-release page was confirmed via direct text extraction to be a City Council presentation slide deck (2024-04-30), not the executed CBA; the only full-CBA-text copy located anywhere was a non-official news mirror (interactive.khou.com), which repo convention flags as unsuitable without an official replacement.

## 3. Why Houston Fire matters for the design

Houston is the richest single-city case in the Texas/Ohio comparison: a Chapter 174 police meet-and-confer unit (ingested), a Chapter 146 non-safety meet-and-confer unit (HOPE/AFSCME Local 123, ingested), and — uniquely among Texas cities — a fire department subject to Texas Local Government Code §174.1535's population-triggered (≥1.9 million) *mandatory* arbitration provision. Houston Fire is the closest Texas analogue to Massachusetts's JLMC compulsory-arbitration mechanism found anywhere in this project's corpus so far. Without it, Houston's three-tier institutional structure is only two-thirds represented, and this project has no Texas example of a compulsory-arbitration safety mechanism at all.

## 4. Exact source-resolution criteria

A Houston Fire source is eligible for ingestion as a causal row only if **all** of the following hold:
1. It contains the actual operative wage-setting agreement, settlement, or arbitration-award text (numbered articles/sections covering recognition, wages, hours, and/or a settlement's specific negotiated terms) — not a press release, presentation slide deck, docket summary, or news article about the agreement.
2. It is hosted by an official/high-quality source: the City of Houston, HPFFA/IAFF Local 341, a court/arbitration record, or another public repository of comparable reliability — not a news outlet's PDF mirror of unconfirmed provenance, unless no better copy exists and the mirror's content can be independently verified against official secondary confirmation (in which case it would still be flagged `official_or_high_quality_source=unclear` and require explicit caution, per the hard boundary preferring official-source replacement).
3. Its source_type maps cleanly to an existing schema value (`cba`, `arbitration_award`, `factfinding`) without needing a schema change — a settlement agreement would be recorded as `cba` only if that is consistent with existing project convention and the caveat is documented; it would not be labeled `arbitration_award` unless it is an actual arbitration award.

## 5. What will and will not be ingested

**Will ingest (if found):** exactly one Houston Fire wage-setting document (CBA, labor agreement, settlement agreement, or arbitration award) meeting the criteria above, as one new `data/contracts.csv` row and one matching `data/city_coverage.csv` row.

**Will not ingest under any circumstance:**
- Texas Local Government Code Chapter 174 or §174.1535 (context/legal only).
- Houston city pages, HPFFA/union pages, or court dockets that do not themselves contain the operative agreement text (source-discovery/context only).
- News articles or press releases about the agreement (context only).
- Budget/pay-plan documents (context only, out of scope for this run).
- A substitute document if no exact source is found — this run will document the search and freeze the target as unresolved rather than force a lower-quality source into the causal corpus.
