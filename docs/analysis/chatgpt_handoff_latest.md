# ChatGPT Handoff

**Date:** 2026-06-29  
**Current commit before this run:** `6c6a571`  
**Working-tree note:** this handoff was updated in the same run that created the v10 gold set; check `git status` or the latest local commit for final file state.

## Current corpus snapshot

- Contracts: 32
- Discourse rows: 0
- Coverage rows: 32
- Cities: 9
- Healthy matched pairs: 12
- Exact-cycle matched pairs: 9
- Overlap-cycle matched pairs: 3
- Unmatched safety rows: 3
- Unmatched safety obs_ids: `ma_somerville_police_spsoa_2012`, `ma_somerville_police_spea_2012`, `ma_newton_police_2015`

## Current main research interpretation

- H1 remains plausible but underidentified in the current corpus.
- GABRIEL v9 found its clearest `comparability_emphasis` signal in safety-side arbitration/award-style documents, especially the Somerville police awards.
- The strongest non-safety peer-wage comparison found so far is the official Boston BTU bargaining page, but that source is mechanism-proxy/discourse-lane evidence rather than a causal-corpus reasoning document.
- The central caveat is still source type and document production: explicit reasoning is visible where institutions force it onto the page, not necessarily wherever it matters in bargaining.

## Key completed artifacts

- v9 preliminary report: `reports/6_25/v2/GABRIELv9_preliminary.pdf`
- Public-source strategy note: `docs/hypotheses_public_source_strategy_2026-06-24.md`
- Mechanism-source summary: `docs/analysis/mechanism_source_summary_2026-06-26.md`
- Boston BTU deep dive: `docs/acquisition/ma_boston_btu_salary_comparison_deep_dive_2026-06-29.md`
- Comparator network design memo: `docs/analysis/comparator_network_design_2026-06-29.md`
- Comparator synthesis memo: `docs/analysis/comparator_edge_synthesis_2026-06-29.md`
- Comparator stub CSV: `docs/analysis/comparator_mentions_stub_2026-06-29.csv`
- v10 design memo: `docs/analysis/gabriel_v10_arbitration_impasse_design_2026-06-29.md`
- v10 gold set CSV: `docs/analysis/gabriel_v10_gold_set_2026-06-29.csv`
- v10 gold set memo: `docs/analysis/gabriel_v10_gold_set_memo_2026-06-29.md`

## Current next-step recommendation

Do a prompt dry-run on the small v10 gold set before any broader `arbitration_or_impasse_backstop` pass. The main implementation risk is false positives from ordinary grievance-arbitration boilerplate in CBAs.

## Files changed in this run

- `docs/analysis/gabriel_v10_gold_set_2026-06-29.csv`
- `docs/analysis/gabriel_v10_gold_set_memo_2026-06-29.md`
- `docs/analysis/gabriel_v10_arbitration_impasse_design_2026-06-29.md`
- `docs/analysis/chatgpt_handoff_latest.md`
- `docs/acquisition/ma_newton_somerville_boston_mechanism_source_plan_2026-06-26.md`
- `PROGRESS.md`

## Open decisions for the user or PI

- Whether the v10 attribute should stay causal-corpus-only for its first run, or whether a separate mechanism-proxy lane should be scored later.
- Whether the current 11-row gold set is enough for prompt tuning, or whether a second-round set should add ambiguous edge cases.
- Whether the next empirical priority is a v10 pilot, more comparator extraction, or broader mechanism-source acquisition.

## Suggested next Codex run

Use the gold set to draft and test exact v10 prompt language against the 11 hand-coded rows, with special attention to keeping grievance-arbitration boilerplate near `0` to `1_25` and keeping Boston BTU negative for this attribute despite its strong peer-wage content.
