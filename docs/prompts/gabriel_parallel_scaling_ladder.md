# Gabriel Parallel Scout Scaling Ladder

This ladder limits service concurrency and prevents a successful-looking partial run from becoming automatic permission to scale. Each worker remains serial (`--n-parallels 1`) in its own worktree/repo copy, uses a fresh direct-SDK smoke preflight, a batch-specific cost log, zero retries, and a later coordinator-only merge.

| Stage | Concurrent workers | Locked batch per worker | Purpose |
| --- | ---: | ---: | --- |
| Stage 1 | 2 | 25 rows | Establish two-worker stability and merge safety. |
| Stage 2 | 3 | 25 rows | Establish three-worker stability and merge safety. |
| Stage 3 | Parallel workers | 50 rows | Increase batch size only after Stage 2 is proven and the hard cap is separately raised. |

## Promotion criteria

Advance only when every applicable criterion is met:

- every independent smoke preflight passes;
- live runs complete without connection collapse or stop-guard truncation;
- parseable municipality-outcome rate is at least 90%, using the full locked input as denominator (at least 23/25 for every 25-row worker);
- no major candidate, queue, coverage, or prompt/schema failure occurs;
- candidate volume is manageable for review and preserves unique worker/run/municipality provenance;
- the coordinator imports the relays cleanly, preserves all prior rows, and rebuilds queue/coverage once; and
- the required validation suite passes after the merge.

Also require failures to be isolated and manageable, not a repeated transport/proxy or malformed-output pattern. Parseable empty output counts as a valid outcome; connection-only, malformed, absent, and stopped-before-request outcomes do not.

## Stage-specific rules

### Stage 1 — two parallel 25-row live scouts

Run exactly two disjoint locked 25-row workers. Promotion to Stage 2 requires both workers individually to clear the 90% rate and the pooled 50-row result to clear it as well. A worker with more than two non-collapse failures normally fails the stability test unless the coordinator documents why the failure is demonstrably non-systemic.

The first CA25.2/NJ25 attempt on 2026-07-21 did not complete Stage 1: CA25.2 stopped on a failed smoke, and NJ25 preserved only a live prompt preview. Do not promote. The next attempt remains Stage 1 and must reuse the same two locked inputs only after execution hardening is committed and live use is separately authorized.

For that same-stage retry:

- use new unique timestamped/retry-labeled dry, smoke, live, log, and relay paths;
- complete worker readiness checks for relay, `.env`/key presence without disclosure, interpreter, package versions, writable paths, and protected global files;
- stagger worker starts by 5–10 minutes rather than launching both gates simultaneously;
- keep direct SDK, `--n-parallels 1`, 15-second prompt spacing, and zero SDK retries;
- stop a worker if its fresh smoke fails; do not launch or retry its live batch;
- require command-level exit/sanitized-log evidence and crash-safe lifecycle metadata; and
- do not start a coordinator merge unless both workers return complete, merge-eligible relays with parseable research-batch model outputs.

A preflight-stop relay or a prompt-preview-only live relay fails Stage 1. Neither counts as discovery coverage, and neither can be used to compute a favorable parse rate by shrinking the denominator.

### Stage 2 — three parallel 25-row live scouts

Run exactly three disjoint locked 25-row workers only after a clean Stage 1 coordinator merge. Promotion to Stage 3 requires every worker and the pooled 75-row result to meet the same 90% threshold, with no concurrency-collapse pattern and a clean single coordinator rebuild.

### Stage 3 — parallel 50-row live scouts

Run 50-row workers only after Stage 2 passes and a separate reviewed, tested, committed change raises the scout's live hard cap from 25 to 50. Do not bypass or silently alter the cap in a prompt. Keep each worker serial and retain all Stage 1/2 isolation, smoke, relay, and coordinator-only accounting rules.

## Do not promote when

Any failed smoke, connection collapse, systematic parser/schema defect, prompt-preview-only run, missing lifecycle/exit evidence, unmanaged candidate volume, missing provenance, worker mutation of shared/canonical files, dirty coordinator merge, or validation failure blocks promotion. Stay at the current stage and recommend a bounded diagnostic or another same-stage trial; do not retry failure-only municipalities without separate authorization.

## Profile guidance

Use Heavy / GPT-5.6 Sol for ladder design, promotion decisions, debugging, architecture, selection methodology, and prompt/filter-contract changes. Use Routine / GPT-5.6 Terra for locked worker runs, deterministic rebuilds, and relay packaging. Use Low / GPT-5.4 only for tiny documentation cleanup.
