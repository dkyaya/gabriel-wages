# Dashboard Priority Layer Handoff

Date: 2026-07-22

## Data delivered

`scripts/build_dashboard_data.py` now reads the national tier, state-priority, and top-target CSVs and writes three additive static files:

- `docs/dashboard/data/priority_summary.json`
- `docs/dashboard/data/state_priority_summary.json`
- `docs/dashboard/data/top_priority_targets.json`

The existing geographic map, tile grid, coverage funnel, candidate queue, readiness JSON, and frontend behavior are unchanged. The priority layer requires no runtime backend, map token, API, or source request.

`priority_summary.json` supplies the 35,589-row universe, 504 successfully covered municipalities, 35,079 future-scout-eligible rows, eligible Tier 1–5 counts, ten failure-only retry targets, and high/medium/low score-confidence counts.

`state_priority_summary.json` supplies one row for every state/DC with universe, covered, eligible, Tier 1–5 remaining, Tier 1+2 remaining, high-priority coverage rate, smoothed state yield score, state-score confidence, observed candidate-positive rate when a state sample exists, and recommended next-wave status.

`top_priority_targets.json` supplies the top 500 future-scout-eligible municipalities with rank, identity, employer type, population, score, tier, confidence, retry flag, and recommended wave band.

## Recommended low-risk dashboard components

1. Add five small national count cards for eligible Tier 1–5 municipalities, with Tier 1 and Tier 2 visually prominent.
2. Add a map metric selector for:
   - Tier 1 remaining;
   - Tier 1 coverage rate; and
   - Tier 1 + Tier 2 remaining.
3. Add a sortable top-target table with state, municipality, population, score, tier, confidence, and retry flag.
4. Show state confidence next to state-yield score, especially where there are fewer than 15 successful scouts.
5. Keep retry targets visually separate from ordinary new-scout targets.

No frontend work is included in this task; these are follow-up suggestions.

## Required disclaimer

Use language equivalent to:

> Priority scores are transparent research-operational heuristics for choosing source-discovery order. They do not establish unionization, department existence, bargaining coverage, source availability, wage gaps, or causal effects. Candidate and likely-matched-set signals remain unverified.

The map must not label higher priority as higher unionization, larger safety wage growth, stronger labor power, better source access, or greater evidentiary support. Safe metrics are counts and coverage rates for operational tiers only.
