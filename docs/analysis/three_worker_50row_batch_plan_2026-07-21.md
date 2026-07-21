# Three-Worker 50-Row Batch Plan

Date: 2026-07-21

Disposition: **three locked offline-preparation batches are ready; no live/API action is authorized or performed**

## Plain-English plan

Three persistent workers will prepare and dry-review independent 50-municipality batches in parallel: California, New Jersey, and Texas. They will not smoke-test or live-scout. Once the main coordinator has three complete prep relays and all 150 prompts pass the filtering checklist, the coordinator will combine the inputs, lock their order, run one synthetic direct-SDK smoke, and—under separate live authorization—run one sequential 150-prompt live process with `n_parallels=1`. National queue and discovery coverage will be rebuilt once after the complete run is audited.

This separates the safe part of concurrency (data preparation, prompt generation, and checklist review) from the unstable part (API-bearing hosted-search execution).

## Why the operating model changed

The prior concurrent-live worker attempt was unstable: one CA smoke failed and the NJ live lane collapsed after two no-ID/no-text/no-token connection errors. A bounded sequential diagnostic then passed 5/5 synthetic calls. The serialized recovery completed CA25.2 and NJ25 with 24/25 parseable outcomes apiece, no repeated connection collapse, and one clean accounting rebuild.

That evidence validates parallel/offline preparation plus one coordinator-controlled API lane. It does not validate concurrent live workers. Running three worker-owned live lanes would reintroduce the failure mode without adding research value. A single coordinator process also makes stop-guard behavior, artifact completeness, usage accounting, and one-time national rebuilding easier to audit.

## State and batch rationale

- **Worker 1 — CA50.** California already has 45 successful scout-covered municipalities but still has 433 `not_scouted` municipalities. The original manifest anchors are covered, so the batch extends to the 50 largest eligible untouched city governments. It excludes Oakland, Stockton, Oxnard, Redding, and Fairfield, all current failure-only timeouts.
- **Worker 2 — NJ50.** New Jersey has only 27 covered municipalities, and the serialized NJ25 batch produced 12 parseable-empty outcomes, making broader exact-employer discovery useful. Covered/canonical rows and Princeton are excluded. The remaining unscouted manifest rows Edison, Woodbridge, and Lakewood are township governments, so the hard employer-type rule excludes them. The batch uses the 50 largest eligible place governments instead.
- **Worker 3 — TX50.** Texas is preferred over an alternative state because only three of 1,224 municipalities are covered, while Dallas, Fort Worth, El Paso, Arlington, and Corpus Christi are untouched manifest priorities. Those five anchor the batch; the next 45 highest-population eligible municipal employers extend the institutional safety-versus-civilian wage-setting contrast. The source-of-truth data contain no reason to replace Texas.

Every batch contains exactly 50 active Census `municipal` / `place` governments, with preserved municipality/Census IDs and all county relationships. Counties, schools, authorities, districts, township governments, and private providers are excluded. Across all batches there are 150 unique municipality IDs and 150 unique Census government IDs.

## Why 50 rows per worker

Fifty rows are large enough to amortize worktree setup, schema/eligibility reconciliation, prompt review, and relay packaging while remaining inspectable as one state-specific checklist. Three equal batches also make omissions and duplicate detection simple: each prep relay must reconcile to 50/50 prompts and the future locked input to 150/150.

The worker size is a preparation unit, not a live-concurrency unit. No worker gets API authority. Increasing the offline dry-run size does not imply that the previous parallel-live scaling ladder has passed.

## Why one coordinator-controlled 150-row live queue

One process guarantees a single ordered queue, one active API client, `n_parallels=1`, one stop guard, one cost/usage artifact family, and one national merge boundary. It avoids inter-worker API overlap and the ambiguity of deciding whether partial worker batches should be merged. The input order will remain Worker 1 CA ranks 1–50, Worker 2 NJ ranks 1–50, then Worker 3 TX ranks 1–50.

There are two mandatory code gates before a future live run. The current scout:

1. filters the municipalities CSV to a single `--state`; and
2. clips live execution at `LIVE_HARD_CAP=25`.

A future coordinator must implement and no-network-test explicit mixed-state input support and a reviewed cap of at least 150. The enhancement must preserve row-state prompts/identifiers, dry-run behavior, serial ordering, lifecycle checkpoints, stop-guard evidence, and all existing tests. Merely passing `--max-prompts 150` to the present code would silently run at most 25 rows; using one state flag on the mixed input would silently drop the other 100. Either condition is a hard preflight stop. This task intentionally does not change the runner.

## Runtime, usage, and estimate-only cost

The best recent 25-row planning evidence spans roughly 24–35 minutes per serialized run. The recovered CA25.2 and NJ25 service averages were 37.94 and 29.59 seconds per successful request, with 15-second inter-prompt spacing and one 90-second timeout apiece. Six 25-row equivalents therefore imply roughly **2.4–3.5 hours** for 150 prompts, before any manual artifact review.

Recent 25-row runs used about 0.70–1.03 million input tokens, 27,000–49,000 reasoning tokens, and 37,755–79,974 output tokens. Linear planning for 150 rows is therefore approximately:

- 4.2–6.2 million input tokens;
- 162,000–294,000 reasoning tokens;
- 227,000–480,000 output tokens; and
- roughly 4.4–6.7 million total tokens.

The serialized CA/NJ reference estimates were `$0.1874` and `$0.2384` per 25 rows. A simple six-batch token-only extrapolation is about **$1.12–$1.43**; using the higher-input/output Illinois envelopes suggests retaining a broader planning ceiling around **$1.8**. These are explicitly estimate-only standard OpenAI text-token references. Actual HUIT billing is unavailable, and hosted-search/tool fees, cached-input treatment, taxes, credits, and enterprise adjustments are excluded.

## Risks and stop conditions

- Stop before smoke if any prep relay is missing, any dry review is not 50/50, any input changed/reordered, any row became covered/queued/canonical/failure-only, any prohibited employer type appears, or the 150 IDs are not unique.
- Stop before smoke unless mixed-state input and a live cap of at least 150 are implemented, tested, reviewed, and committed.
- Stop if the synthetic one-request no-search smoke fails, lacks `OK`/`OK.`, a response ID when exposed, positive output tokens, or explicit success.
- Stop the live queue on connection collapse: two consecutive no-ID/no-text/no-token connection or timeout failures, or another repeated transport pattern that indicates service instability. Preserve partial/stopped evidence and do not retry or substitute rows.
- Stop on systematic parser/schema failure, loss of lifecycle/command evidence, unexpected protected/global changes, or any secret exposure.
- Parseable empty output counts as discovery coverage; connection-only, malformed, absent, and stopped-before-request output does not.
- Do not verify sources, open/download URLs, ingest, codify, edit canonical contracts/city coverage/corpus, or use leads for claims during preparation or the future live/accounting task.

After an eligible complete live run, add unverified candidates and outcome metadata to the builders, then rebuild the candidate queue and municipality/state/county scout coverage exactly once. If the run stops on collapse or is not merge-eligible, preserve the evidence and leave national accounting unchanged pending a separately authorized recovery decision.
