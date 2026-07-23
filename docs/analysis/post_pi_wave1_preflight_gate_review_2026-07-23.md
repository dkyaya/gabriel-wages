# Post-PI Wave 1 Stronger Preflight Gate Review

Date: 2026-07-23

Disposition: **PASS — the fresh 150-row dry-run gate may proceed.**

## Plan-only gate

- Output: `tmp/post_pi_wave1_preflight_gate_plan_only_2026-07-23_attempt1`
- Mode: `plan_only`.
- Planned diagnostics: three, beneath the hard cap of four.
- External calls attempted: zero.
- Credential values written: false.
- Scout accounting changed: false.

The plan covered one no-search control and two hosted-search diagnostics. It confirmed the expected pass criteria before any live diagnostic was attempted.

## Single stronger live gate

- Output: `tmp/post_pi_wave1_preflight_gate_live_2026-07-23_attempt1`
- Result: **PASSED**.
- Model/search/timeout: `gpt-5.4-nano`, low search context, 30 seconds.
- Calls attempted: three transport diagnostics plus one quarantined scout probe; hard cap four.
- Stop reason: none.
- Secret exposure detected: false.
- Credential values logged: false.
- URLs independently opened: false.
- Queue, coverage, dashboard, corpus, and contract accounting changed: false.
- Consecutive transport failures: zero.

| Diagnostic | Status | Response ID | Nonempty text | Token usage | Input / output / total tokens | Elapsed |
|---|---|---|---|---|---:|---:|
| No-search control | passed | present | present | present | 10 / 6 / 16 | 3.626 s |
| Hosted-search trivial public query | passed | present | present | present | 8,738 / 81 / 8,819 | 5.862 s |
| Hosted-search municipality-style query | passed | present | present | present | 17,246 / 719 / 17,965 | 15.817 s |

Response content and credential/client configuration are intentionally not reproduced here.

## One-row scout probe

- Input: `tmp/post_pi_wave1_one_row_probe_input_2026-07-23_attempt1.csv`
- Input SHA-256: `b1147174819694b98c7ef2e8f674ce022d1f536e36a68be2570780962cdac2b6`
- Locked row: rank 1, municipality ID `cog_2025_133204`.
- Output: `tmp/post_pi_wave1_one_row_probe_direct_sdk_2026-07-23_attempt1`
- Result: one attempted row; one response; one parseable row; zero failed parses.
- Response ID, nonempty response text, and token usage are present.
- Usage summary: 31,473 input, 3,422 output, 1,236 reasoning, and 34,895 total tokens.
- Elapsed row time: 38.690 seconds.
- The generated candidate handoff was moved into the probe directory as `quarantined_candidate_handoff.csv`; no diagnostic candidate file remains in `docs/analysis/`.

The probe is diagnostic-only. Its raw output and six parsed scout-stage leads are quarantined under the probe output directory. They are excluded from the national candidate queue, municipality coverage, dashboard, yield learning, canonical evidence, verification, ingestion, codification, and claims.

## Authorization decision

All required stronger-preflight components passed with response lifecycle and usage evidence intact, no transport-failure sequence, and no secret exposure. The preflight gate therefore authorizes the fresh 150-row offline dry run. It does not by itself authorize the full live run; that remains conditional on the locked-input and fresh dry-run reviews passing.
