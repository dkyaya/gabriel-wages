# Tier 1 Wave 2 preflight gate review — 2026-07-22

## Decision

PASS. The plan-only inspection and the single bounded four-call live preflight gate both completed successfully. The Tier 1 Wave 2 coordinator run may proceed to its locked 150-row dry-run audit. This gate does not by itself authorize the full live run; the dry-run audit must also pass.

## Commands and artifacts

The plan-only gate used `gpt-5.4-nano`, a 30-second timeout, low search context, and a four-call ceiling. Its artifacts are in:

`tmp/tier1_wave2_preflight_gate_plan_only_2026-07-22_attempt1/`

The bounded live gate used the same model, timeout, search context, and call ceiling, plus a one-row production-runner probe. Its artifacts are in:

`tmp/tier1_wave2_preflight_gate_live_2026-07-22_attempt1/`

The diagnostic-only probe input is:

`tmp/tier1_wave2_one_row_probe_input_2026-07-22_attempt1.csv`

Its SHA-256 is `87fc7602089f47566f00a956b24b98943fe67c9bc83ad61c13279a56802f00b5`. The probe output is in:

`tmp/tier1_wave2_one_row_probe_direct_sdk_2026-07-22_attempt1/`

## Plan-only result

- Status: `plan_only_not_executed`.
- Planned calls: three gate diagnostics plus one optional production-runner probe.
- External/API/model calls attempted: 0.
- No credential values or secret-like content appeared in the plan artifacts.

## Live preflight result

- Overall gate status: PASS.
- External calls attempted: 4, exactly the bounded maximum.
- No-search control: PASS; response ID, response text, and token usage were present; elapsed time 2.345 seconds.
- Hosted-search trivial public query: PASS; response ID, response text, and token usage were present; elapsed time 6.228 seconds.
- Hosted-search municipality-style query: PASS; response ID, response text, and token usage were present; elapsed time 17.759 seconds.
- One-row production-runner probe: PASS; the Coral Springs, Florida row completed parseably and returned three candidate rows.
- Transport-collapse rule: not triggered.
- Secret-exposure rule: not triggered.
- Independent URL opening or verification: none.

Response identifiers, response content, and credential-bearing configuration are intentionally not reproduced in this review. The gate artifacts retain only the sanitized evidence needed to establish ID/text/token presence and terminal status.

## Probe quarantine and accounting

The one-row Coral Springs probe is diagnostic-only. It is not official scout evidence and must not be merged into the national candidate queue or coverage accounting. Its candidate handoff was moved to:

`tmp/tier1_wave2_one_row_probe_direct_sdk_2026-07-22_attempt1/quarantined_candidate_handoff.csv`

The probe must not be used to mark Coral Springs candidate-positive, parseable-empty, failure-only, or scout-covered. The official 150-row run, if it passes every remaining gate and completes merge-eligibly, is the only Wave 2 output eligible for accounting.

## Authorization state

The stronger preflight requirement is satisfied. The full live run remains conditional on a passing fresh 150-row compact-prompt, search-hint, adaptive-sleep dry-run audit.
