# Stage 1 Retry Recommendation

Date: 2026-07-21

Decision: **prepare workers in parallel, but run all smoke and live API work sequentially through one coordinator-controlled lane**

## Recommendation

Do not retry Stage 1 as two parallel live workers. Do not move to Stage 2. Keep the same locked CA25.2 and NJ25 batches, but recover them in a later separately authorized task using serialized live execution:

1. Worker 1 and Worker 2 may complete Gate 0, locked-input checks, and dry-run review concurrently in isolated worktrees.
2. The coordinator grants an exclusive API lane to Worker 1. The lane covers its fresh no-search smoke, its full live process if smoke passes, final artifact writes, review/stop note, and relay completion.
3. If Worker 1 smoke fails or the live batch collapses, stop the recovery wave. Do not grant Worker 2 a live lane in the same task. Preserve evidence and diagnose before more research calls.
4. If Worker 1 completes with a merge-eligible result, release the lane and wait at least five minutes.
5. Grant Worker 2 the exclusive lane. Run its fresh smoke and, only after success, its full live process. No API interval may overlap Worker 1.
6. Run the coordinator merge only if both worker relays contain parseable research outcomes and pass every existing scope/artifact gate.

The live-lane grant should be represented by coordinator scheduling or a non-git local lease. Workers must not create a tracked lock file in a worker branch, mutate national accounting to claim the lane, or infer permission merely because another process appears idle.

## Keep unchanged

- Same exact locked CA25.2 and NJ25 25-row inputs.
- Direct-SDK backend.
- `gpt-5.4-nano`.
- HUIT `/v2` base and SDK `/responses` resource.
- Bearer plus `Ocp-Apim-Subscription-Key` header names.
- Fresh one-call `Reply with OK.` smoke per worker.
- No tools/search in smoke.
- `n_parallels=1` inside every live scout.
- 15-second spacing between municipality calls.
- Zero SDK retries.
- 30-second smoke timeout and 90-second live timeout.
- Batch-specific output and cost-log paths.
- No worker queue/coverage rebuild.
- No source verification, ingestion, codification, or claim promotion.

## Do not change yet

### Do not increase timeouts

The failed calls ended in 0.014–0.245 seconds. They were not 30- or 90-second timeouts. A larger timeout would not repair immediate connection establishment failure and would make real hangs more expensive.

### Do not reduce to 10-row chunks yet

NJ failed on its first two requests. That does not implicate the 25-row batch length. Earlier serial 25-row direct-SDK runs completed successfully. Reducing batch size would add more smoke/launch boundaries without addressing the observed initiating failure.

If a future serialized worker passes smoke but again fails immediately on its first two hosted-search requests, a separately authorized 10-row diagnostic chunk could become reasonable. That is a later fallback, not the next action.

### Do not change key, model, route, or headers

The same credential and request shape succeeded from all three locations. Five sequential calls passed 5/5. There is no local evidence supporting a key rotation, `/v1`, Chat Completions, a different model, or removal of either established header.

### Do not treat heavier staggering as parallel safety

A 15-minute worker-start stagger can still overlap two long 25-row live runs. The control needed is exclusivity, not merely a wider launch offset. The second worker's API lane starts only after the first worker is fully complete and a five-minute quiet period has passed.

## Why this mode is safest

- The same credential works in main, Worker 1, and Worker 2.
- All Python and package versions match.
- Worktree location is not a persistent cause: both workers succeeded twice in the sequential diagnostic.
- Five sequential calls were stable, including an immediate main-to-Worker-1 transition and delayed repeat samples.
- The two failed worker waves are the only evidence about multi-agent live operation, and both were non-mergeable.
- A serialized lane retains the organizational benefits of isolated workers without exercising unproven concurrent same-key sessions.
- Earlier national 25-row runs already show that a serial worker can deliver acceptable throughput and parse rates.

## Stage classification

This operating mode is a **serialized recovery gate**, not Stage 1 success. Even if both locked batches complete and the coordinator merge validates, the result proves only:

- worker isolation;
- sequential direct-SDK stability;
- complete relay quality; and
- coordinator merge/accounting safety.

It does not prove two-worker live concurrency. Stage 2 therefore remains blocked. After a clean serialized recovery, the project may decide whether to request a separately designed concurrency test, seek HUIT guidance on same-key parallel sessions, or retain serialized live execution as the production operating mode.

## Stop and escalation rules

Stop the entire recovery wave if:

- a fresh smoke fails;
- two consecutive live calls return connection errors without response IDs, text, or tokens;
- `execution_status` is not a valid completed state;
- a worker returns zero parseable outcomes;
- command and artifact counts disagree;
- the API lane overlaps another worker;
- protected global/canonical files change; or
- secret-safe logging cannot be guaranteed.

If a serialized worker passes smoke but the hosted-search live path immediately fails, preserve exact timestamps and ask HUIT to determine whether the `/v2/responses` request arrived and whether the connection ended at local DNS/TLS, gateway/subscription routing, model routing, or the hosted-search upstream. Do not speculate by changing the established request shape.

## Next move

Create one later coordinator-controlled recovery task using fresh attempt labels and the same locked inputs. Run CA25.2 first, then—only after a complete merge-eligible CA relay and at least five quiet minutes—run NJ25. Do not merge or update coverage unless both relays pass the coordinator's eligibility gates. Do not retry within this diagnosis task.
