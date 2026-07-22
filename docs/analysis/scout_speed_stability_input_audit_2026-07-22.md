# Scout Speed/Stability Input Audit — 2026-07-22

## Repository and boundary

- Starting commit: `b6bd6b390e415771dd7f7537be33bc2f46a50e3c` (`Run Tier 1 scout after hosted search diagnostic`).
- Required ancestors confirmed: `b74e82d`, `25445fe`, and `c6b3664`.
- Tracked worktree at start: clean. The unrelated untracked root `package-lock.json` was reported and left untouched.
- This audit and implementation are offline. They do not run a smoke, SDK/model request, hosted search, scout, URL check, verification, ingestion, codification, queue/coverage build, or priority-tier build.

## Inputs used

- `AGENTS.md`, `PROGRESS.md`, and `docs/analysis/chatgpt_handoff_latest.md`.
- Tier 1 after-diagnostic result and accounting reviews.
- Hosted-search diagnostic results and recommendation.
- Prior pace analysis/settings recommendation and tier scouting strategy.
- Current scout runner, transport diagnostic, smoke helper, prompt/direct-SDK tests, queue/coverage builders, dashboard builder, and unchanged priority-tier builder.
- Current national state/municipality coverage and candidate queue outputs referenced by those builders.
- Current dashboard JSON: state, candidate queue, funnel, readiness, priority, state priority, and top targets.

## Current runner behavior before this package

- Production live policy is one coordinator-controlled sequential lane (`n_parallels=1`) with direct SDK for mixed-state runs.
- Fixed sleep defaults to five seconds and is configurable; there is no outcome-sensitive backoff.
- The direct-SDK stop gate halts before further requests after two consecutive no-ID/no-text/no-token connection/timeout failures.
- Every run requires a fresh output directory. Post-patch terminal parents with exact input hashes and row timing support immutable resume planning.
- Per-row timing already records start/finish, backend elapsed time, actual before/after sleep, response-ID presence, usage, parse status, and failure type. Metadata summarizes wall time, average/median row time, total actual sleep, throughput, and failure counts.
- `minimal` is the production row-aware prompt. It preserves locked municipality/government/Census/county/expected-unit/verification context, strict employer/unit/document controls, exact schema, duplicate handling, no-candidate behavior, blocked/dead separation, public-records prohibition, and unverified-stage boundary. Repeated explanatory prose remains substantial.
- The canonical smoke helper tests one no-search `Reply with OK.` call. The bounded transport diagnostic separately established that no-search, hosted-search trivial, municipality-style, and production one-row paths could pass, but full-run prompts did not yet have one reusable composite gate.

## Current operational evidence

| Wave | Attempted | Parseable | Positive municipalities | Empty | Failures | Candidate rows | Runtime | Rows/hour | Candidate rows/parseable |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Wave 1 CA/NJ/TX | 150 | 149 | 112 | 37 | 1 | 246 | 6,937.000s | 77.843 | 1.651 |
| Wave 2 CA/TX/IL | 150 | 148 | 98 | 50 | 2 | 223 | 6,149.884s | 87.807 | 1.507 |
| Tier 1 Wave 1 cross-state | 150 | 142 | 99 | 43 | 8 | 268 | 6,723.519s | 80.315 | 1.887 |

Tier 1 actual sleep was 745.208 seconds. Its direct-SDK usage was 4,258,356 input, 196,927 reasoning, 309,071 output, and 4,567,427 total tokens. The run’s 268 candidates equaled 143.496 candidate rows/hour. Eight isolated timeouts did not trigger the consecutive-collapse gate, but they motivate adaptive recovery without concurrency.

## State-yield data available

The current state coverage file supplies successful scouts, candidate-positive and parseable-empty counts, failure-only municipalities, excluded failed attempts, candidate rows, unit-category presence, likely triads, candidate priorities, and token totals for all 50 states plus DC. These fields support transparent state yield rates and confidence based on sample size. They do not establish verified source quality, unionization, department existence, or matched-cycle completeness.

Current national discovery accounting is 646 successful scout-covered municipalities, 490 candidate-positive, 156 parseable-empty, 18 failure-only, and 1,277 unverified candidate queue rows. Priority-specific JSON still reflects the pre-Tier-1-Wave-1 priority build and is intentionally not recomputed here.

## Dashboard inputs before implementation

Seven static JSON files cover geography, queue, funnel, readiness, and priority layers. There was no dedicated JSON for preflight posture, runtime trends, candidate rows/hour, adaptive pacing, or confidence-labeled state-yield learning.

## Risks and constraints

- A no-search smoke alone is not sufficient evidence that hosted search is healthy.
- Lower fixed sleep can save time but cannot prevent proxy/transport outages; backoff must preserve the two-consecutive-failure stop.
- Prompt compression can silently remove identity or source-stage controls unless guarded by exact tests.
- State yield is highly unstable at small samples; 42 states/DC currently have fewer than 10 successful scouts.
- Query hints are search starting phrases, not discovered sources. They must be deterministic and must never be described as verified URLs.
- Dashboard operations counts are scout-stage and priority counts can lag until the next unchanged tier rebuild.
