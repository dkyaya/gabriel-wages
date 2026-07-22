# Tier 1 One-Row Scout Probe Result — 2026-07-22

## Result

The optional diagnostic-only Oklahoma City probe passed through the actual production scout runner after Category A was established by the bounded transport suite.

- Input: `tmp/tier1_oklahoma_city_one_row_probe_input_2026-07-22.csv`
- Input SHA-256: `2fbb3337da53a3f46e01048b991cc6351beb99d41856c143e23e692965dcb560`
- Municipality: Oklahoma City, OK
- Locked municipality ID: `cog_2025_209170`
- Run ID: `all_2026-07-22_161413`
- Output: `tmp/tier1_oklahoma_city_one_row_probe_direct_sdk_2026-07-22/`
- Backend/settings: direct SDK, hosted search `low`, `n_parallels=1`, cap/max 1, five-second setting, 90-second timeout, zero retries
- Requests attempted: 1
- Response ID: present
- Response text: present
- Usage: 42,214 input / 1,549 reasoning / 2,381 output / 44,595 total tokens
- Request elapsed: 59.409 seconds
- Parseable municipalities: 1
- Parse failures: 0
- Diagnostic candidate rows: 2
- Estimate-only token cost: USD 0.011419; actual/HUIT billing unavailable

This result demonstrates that the production runner can currently complete and parse one search-enabled, row-aware municipality prompt. It rejects a persistent prompt/parse defect for the first locked row. It does not verify either returned lead and does not prove that a 150-row run will remain stable.

## Accounting disposition

**Do not count this probe in scout accounting.** It is diagnostic-only, so Oklahoma City remains `not_scouted` in the national coverage layer. The two parsed rows remain unverified and unmerged.

The runner normally emits a dated candidate handoff under `docs/analysis`. To enforce this task's diagnostic boundary, that untracked generated file was moved without alteration into the probe directory as `diagnostic_candidate_handoff_unmerged.csv`. The runner's own `parsed_candidates.csv`, raw output, prompt preview, timing, metadata, failure ledger, and cost files are preserved in the same directory. The original metadata path therefore records where the runner initially emitted the handoff; this note records its deliberate quarantine relocation.

No candidate queue/coverage builder, dashboard builder, priority builder, verification, ingestion, codification, URL opening, corpus edit, or claim-stage promotion followed the probe.
