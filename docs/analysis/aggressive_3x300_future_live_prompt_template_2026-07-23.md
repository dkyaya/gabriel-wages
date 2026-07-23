# Conditional Future Prompt Template — Aggressive 3 × 300 Collection

**Not currently live-authorized.** Use only after the 3 × 150 live collection and
its separate serial accounting merge both pass.

## Preconditions

- Official project docs show all three 150-row lanes completed and were merged
  through one serial rebuild.
- No unresolved partial lane, export mismatch, completed-ID overlap, diagnostic
  contamination, or protected-file mutation remains.
- Current official scout coverage is still below the approximately 2,000 checkpoint.
- The coordinator explicitly chooses `aggressive_300` instead of the more cautious
  `aggressive_250` after reviewing timeout, transport, backoff, and throughput rates.
- A fresh planner run reconciles the feasibility inputs against then-current coverage,
  failures, canonical status, priority ordering, and the checkpoint.

The current feasibility artifact is
`POST-PI-PARALLEL-AGGRESSIVE-3X300-FEASIBILITY-2026-07-23`. It proves offline
selection capacity only; do not treat it as a durable future live input without
revalidation.

## Required execution pattern

Run one stronger preflight, quarantine the one-row probe, and pass three exact
300-row dry runs. Launch only three isolated, internally serialized lanes. Use
compact prompts, exact hints, adaptive sleep/backoff, the 90-second outer timeout,
zero SDK retries, distinct cost logs, and lane-local candidate exports.

Start Lane 1, then stagger Lane 2 and Lane 3 by eight minutes each. Increase the
stagger to ten minutes when the preceding 3 × 150 run showed any meaningful
transport contention. Never parallelize shared accounting.

After all lanes terminate, run the three-lane auditor and stop. Preserve partial
artifacts and use fresh lane-specific resume directories when needed. A later
explicit serial task may merge all lanes only when every lane passes; a
completed-only subset requires direct user approval.

## Checkpoint warning

Three fully parseable 300-row lanes add up to 900 possible coverage outcomes. From
the current 1,091 official total, that would approach 1,991 before allowing for
failures; depending on the coverage count after 3 × 150, it is likely to reach or
exceed the approximately 2,000 checkpoint. The serial merge must update official
accounting once, then broad scouting must stop at the checkpoint. Proceed to
verification, extraction, ingestion, rating, descriptive wage-growth-gap analysis,
mechanism-correlation documentation, and the planned dashboard layer. Regressions
remain deferred.
