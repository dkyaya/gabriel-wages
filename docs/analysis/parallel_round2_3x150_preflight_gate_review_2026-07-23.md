# Parallel Round 2 — 3 × 150 Preflight Gate Review

Date: 2026-07-23
Round: `POST-PI-PARALLEL-ROUND2-3X150-2026-07-23`

## Result

**PASS. The three-lane dry-run gate may proceed.**

## Plan-only gate

- Planned calls: three.
- External calls attempted: zero.
- Model: `gpt-5.4-nano`.
- Diagnostic timeout: 30 seconds.
- Search context: low.
- No credential value was written.
- No scout accounting changed.

## One stronger live gate

Exactly four authorized calls were attempted:

| Call | Search | Result | Response ID | Text | Tokens | Seconds |
|---|---|---|---|---|---|---:|
| No-search control | no | passed | present | present | present | 1.242 |
| Trivial public hosted search | yes | passed | present | present | present | 4.625 |
| Municipality-style hosted search | yes | passed | present | present | present | 13.428 |
| One-row Wausau production probe | yes | passed | present | present | present | 30.614 |

The transport diagnostic classification is `A`: the no-search control and both
hosted-search diagnostics passed. No secret exposure, consecutive transport
failure, independent URL opening, or accounting write was reported.

The Wausau probe completed with one parseable municipality outcome, zero failed
parses, and three unverified candidate leads. Its total token usage was 30,071
(27,654 input; 1,322 reasoning; 2,417 output). The preflight helper moved the
timestamped handoff into:

`tmp/parallel_scout_rounds/POST-PI-PARALLEL-ROUND2-3X150-2026-07-23/one_row_probe_direct_sdk_attempt1/quarantined_candidate_handoff.csv`

The probe, its three leads, raw response, timing, and cost/usage artifacts are
diagnostic only. They must not enter queue, coverage, yield, dashboard,
project-phase, priority, corpus, verification, ingestion, claims, or the later
lane merge.

## Authorization boundary

This review authorizes the three offline lane dry runs required by the user’s
gate sequence. Live lane processes remain conditional on all three dry-run
audits passing.
