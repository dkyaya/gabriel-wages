# Scout Speed/Stability Design — 2026-07-22

## 1. Stronger preflight gate

`scripts/run_scout_preflight_gate.py` composes the existing bounded transport diagnostic with an optional explicit one-row production-runner probe. Plan-only is credential-free and makes zero external calls. An executed gate is capped at three transport calls or four calls with the probe. It passes only when no-search and both hosted-search calls return IDs, text, and tokens, and the optional probe parses. It fails closed on baseline failure, hosted-search failure, secret exposure, or two consecutive transport failures. Probe output is quarantined and cannot enter national accounting.

## 2. Adaptive pacing

Adaptive pacing is opt-in and currently applies to direct-SDK live execution; fixed pacing is unchanged otherwise.

- Start at base 5 seconds.
- After 25 stable rows, reduce one second toward the 3-second minimum.
- On one timeout/connection failure, increase to at least the 10-second backoff.
- On two consecutive transport failures, increase to the 15-second maximum and preserve the existing stop-before-more-requests rule.
- Record planned and actual sleep, pacing mode, current level, and event on each timing row. Record configured parameters, planned/actual totals, observed levels, and event counts in metadata.

The deterministic controller is unit-tested without sleeping or calling a backend. `n_parallels=1` remains mandatory.

## 3. Compact prompt mode

`--prompt-mode compact` keeps the same row identity, target context, source/unit/document rules, no-candidate permission, duplicate controls, public-records prohibition, output keys/enums, blocked/dead distinction, and unverified-stage boundary as `minimal`, while collapsing repeated prose. On the representative Austin row used by the tests, compact is 3,792 characters versus 5,933 for minimal: 36.09% shorter (a rough four-characters-per-token proxy is 948 versus 1,483 tokens). Actual API tokenization must be measured on the next authorized run.

`minimal` and `full` remain available and unchanged for existing commands.

## 4. Deterministic query hints

`scripts/build_municipality_search_hints.py` emits five reproducible phrases for every authoritative municipality ID using only government name and state. No URL or source is invented. `--search-hints-csv` joins exact IDs and fails if a row-aware ID lacks a hint; legacy no-ID inputs remain compatible. Hints appear explicitly as starting phrases, not discovered evidence.

## 5. Yield-learning loop

`scripts/build_scout_yield_learning_report.py` uses current accounting and the three reviewed wave metrics. It computes state positive/density/empty/failure rates and assigns confidence from successful sample size: high at 25+, medium at 10–24, low below 10. Wave outputs include runtime, rows/hour, candidates/hour, and candidate density. Tier rank remains the primary selector; state yield is a secondary learning signal. Rebuild after each wave and refresh the unchanged priority system after 300–600 successful scouts.

## 6. Dashboard operations JSON

The dashboard builder adds:

- `scout_operations_summary.json` for current totals, latest runtime/yield, preflight posture, and tier-refresh note;
- `scout_yield_by_state.json` for confidence-labeled state metrics and a 10+ sample leaderboard;
- `scout_runtime_trends.json` for Wave 1, Wave 2, and Tier 1 trends.

No frontend or deployment behavior changes. Candidate and priority caveats remain explicit.

## Safety invariants

- No API/model call occurs merely by importing a script or building reports.
- Plan-only preflight never loads credential values.
- No concurrency is authorized.
- Every live/probe directory must be fresh and lineage-preserving.
- No output is verified, ingested, codified, canonical, or claim-supporting.
- Queue, coverage, priority methodology, contracts, city coverage, and corpus remain outside this implementation.
