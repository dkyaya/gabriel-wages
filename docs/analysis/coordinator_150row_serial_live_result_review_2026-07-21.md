# Coordinator 150-row serialized live result review — 2026-07-21

## Decision

Run `all_2026-07-21_193524` is complete and merge-eligible for scout-stage queue and discovery-coverage accounting. It is not source verification, ingestion, codification, canonical evidence, or claim support.

## Gates and execution

- Starting commit: `264ebd56d2e95cc07ae8e3e030c9cb2ce00ac2a7` (`Fix scout prompt identity and 150-row safety`). The tracked worktree was clean; untracked `package-lock.json` was reported and left untouched.
- Worker evidence: CA50 and TX50 relay reviews passed; the original NJ50 relay failure is paired with the coordinator-regenerated 50/50 municipality-ID rereview and therefore passed the corrected gate.
- Locked input: 150 rows in CA50, NJ50, TX50 order, SHA-256 `e53db4698b5dba439ad4d31fca79be1242808960d1a8d6809d31b1b915de62fc`.
- Corrected-code dry run: 150/150 prompts passed the complete row-identity and filter contract; no backend call occurred.
- Smoke: exactly one direct-SDK no-search request used `Reply with OK.`, a 30-second timeout, and zero retries. It returned `OK`, a response ID, and five output tokens.
- Live: exactly one coordinator process used direct SDK, mixed-state mode, `max_prompts=150`, `live_hard_cap=150`, `n_parallels=1`, 15-second spacing, a 90-second timeout, and zero retries. It started at `2026-07-21T23:35:17Z`, ended at `2026-07-22T01:30:54Z`, and exited 0. No concurrent or worker live process ran.

## Outcome accounting

| Measure | Total | CA | NJ | TX |
|---|---:|---:|---:|---:|
| Attempted/raw rows | 150 | 50 | 50 | 50 |
| Parseable rows | 149 | 49 | 50 | 50 |
| Candidate-positive municipalities | 112 | 46 | 31 | 35 |
| Parseable-empty municipalities | 37 | 3 | 19 | 15 |
| Timeout/failure-only municipalities | 1 | 1 | 0 | 0 |
| URL-bearing candidate rows | 246 | 105 | 62 | 79 |

All 150 raw identifiers are unique and preserve the locked input order. All 149 successful rows contain nonempty response text, a response ID, and positive output tokens. The candidate-positive, parseable-empty, and failed identity sets are disjoint and account for all 150 input municipalities.

The only failure was Moreno Valley, California (`cog_2025_161238`): one `APITimeoutError` at approximately 90 seconds with no response text, ID, or tokens. The next row succeeded, so this isolated failure did not meet the two-consecutive collapse threshold. There were no `stopped_before_request` rows, repeated transport pattern, JSON/schema failures, lifecycle loss, or artifact loss.

## Usage and cost

- Input tokens: `4,482,102`
- Reasoning tokens: `180,985`
- Output tokens: `282,372`
- Total tokens: `4,764,474`
- Mean successful request time: approximately `30.898` seconds
- Actual billed cost: unavailable
- Estimate-only standard text-token calculation: `$1.2493854`

The estimate excludes Harvard HUIT adjustments, cached-input treatment, hosted web-search/tool fees, taxes, credits, enterprise discounts, and other billing adjustments. It must not be reported as actual cost. The durable state-usage allocation records CA `$0.40900085`, NJ `$0.40128725`, and TX `$0.43909730` as estimate-only components summing to the same value.

## Merge eligibility and limitations

The run is eligible for the one national scout queue/coverage merge because all 150 rows were attempted exactly once, the artifact lifecycle completed, 149 rows are fully evidenced, the one failure is isolated and explicitly excluded, and no protected file changed during live execution. Moreno Valley is recorded as failure-only and is excluded from successful discovery coverage.

All 246 candidate rows remain raw model-described, unverified scout leads. No candidate URL was independently opened, downloaded, verified, ingested, codified, promoted to canonical data, or used to support a claim. Later verification must still establish exact employer, bargaining unit, official provenance, execution/completeness, dates, wage content, duplicate status, access status, and matched city-cycle overlap.

## Validation

All six requested compile targets passed. Prompt-contract tests passed 9/9, and the fully mocked/no-network direct-SDK suite passed 11/11. Schema validation passed at 64 contracts; ingestion pipeline tests passed 60/60; the canonical audit remains 28 healthy pairs (10 exact, 18 overlap), two exploratory adjacent matches, and six unmatched safety units. Four dashboard JSON files parsed, and `git diff --check` passed.
