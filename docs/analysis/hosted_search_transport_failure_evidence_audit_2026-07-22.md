# Hosted-Search Transport Failure Evidence Audit — 2026-07-22

## Conclusion

Two independent Tier 1 Wave 1 coordinator attempts stopped at the same boundary: the first two hosted-search requests failed almost immediately with `APIConnectionError: Connection error.`, and neither request returned a response ID, response text, or token usage. Both runs then preserved the remaining 148 rows as `stopped_before_request`. Neither run produced a parseable municipality outcome or candidate row, so neither is merge-eligible and neither is municipality-level source-yield evidence.

The locked 150-row Tier 1 input remains valid and unmerged. Its current SHA-256 is `77b66569bcc2803e5067f84ad20b63e595f8c0611beb87820166b1a3a9de112b`, matching both run metadata files and the locked-input audit.

## Evidence used

- Locked input: `docs/analysis/tier1_coordinator_150row_serial_live_input_2026-07-22.csv`
- Parent review: `docs/analysis/tier1_coordinator_150row_serial_live_result_review_2026-07-22.md`
- Retry parent audit: `docs/analysis/tier1_coordinator_150row_serial_live_retry_parent_audit_2026-07-22.md`
- Retry review: `docs/analysis/tier1_coordinator_150row_serial_live_retry_result_review_2026-07-22.md`
- Parent artifacts: `tmp/tier1_coordinator_150row_serial_live_direct_sdk_2026-07-22/`
- Retry artifacts: `tmp/tier1_coordinator_150row_serial_live_retry_direct_sdk_2026-07-22_attempt1/`

The actual artifact names are `run_metadata.json`, `row_timing.csv`, `failed_parses.csv`, `raw_outputs.csv`, `parsed_candidates.csv`, and `batch_cost_log.csv`. The runner did not create a separately named `failure_ledger.csv` or JSONL raw-output file; `failed_parses.csv` is the functional failure ledger and `raw_outputs.csv` is the raw-response ledger.

## Parent attempt

| Item | Evidence |
|---|---|
| Commit | `c6b3664` |
| Run ID | `all_2026-07-22_152105` |
| Output directory | `tmp/tier1_coordinator_150row_serial_live_direct_sdk_2026-07-22` |
| Locked input hash | `77b66569bcc2803e5067f84ad20b63e595f8c0611beb87820166b1a3a9de112b` |
| First failed row | Oklahoma City, OK (`cog_2025_209170`) |
| Second failed row | Phoenix, AZ (`cog_2025_207536`) |
| Failure type | `connection_error` for both; raw error `APIConnectionError: Connection error.` |
| Timing | 0.198 seconds and 0.005 seconds; 5.001 seconds recorded between calls |
| Response IDs | none |
| Response text | none |
| Token usage | none |
| Remaining rows | 148 `stopped_before_request` |
| Parseable outcomes | 0 |
| Candidate rows | 0 |
| Stop reason | repeated connection collapse after two consecutive no-ID/no-text/no-token failures |

The metadata records `attempted_row_count=2`, `n_backend_successful_rows=0`, `n_parseable=0`, and `n_candidate_rows=0`. The 148 stop rows are lifecycle records, not attempted source-discovery failures.

## Fresh retry attempt

| Item | Evidence |
|---|---|
| Commit | `25445fe` |
| Run ID | `all_2026-07-22_155934` |
| Output directory | `tmp/tier1_coordinator_150row_serial_live_retry_direct_sdk_2026-07-22_attempt1` |
| Locked input hash | `77b66569bcc2803e5067f84ad20b63e595f8c0611beb87820166b1a3a9de112b` |
| First failed row | Oklahoma City, OK (`cog_2025_209170`) |
| Second failed row | Phoenix, AZ (`cog_2025_207536`) |
| Failure type | `connection_error` for both; raw error `APIConnectionError: Connection error.` |
| Timing | 0.196 seconds and 0.005 seconds; 5.001 seconds recorded between calls |
| Response IDs | none |
| Response text | none |
| Token usage | none |
| Remaining rows | 148 `stopped_before_request` |
| Parseable outcomes | 0 |
| Candidate rows | 0 |
| Stop reason | repeated connection collapse after two consecutive no-ID/no-text/no-token failures |

The retry metadata likewise records `attempted_row_count=2`, `n_backend_successful_rows=0`, `n_parseable=0`, and `n_candidate_rows=0`.

## Merge and accounting status

Both result reviews explicitly classify their runs as non-mergeable. The parent and retry candidate files contain zero data rows. The national queue, scout coverage, dashboard JSON, priority layer, canonical contract data, city coverage, and corpus were not rebuilt or changed from either stopped run. Oklahoma City and Phoenix therefore remain transport-failure retries, not municipality source failures.

## Diagnostic hypotheses

1. **Primary hypothesis:** the no-search direct-SDK request shape is healthy, but adding the hosted `web_search` tool currently fails at or before transport/proxy routing.
2. A broader transient HUIT/proxy/outbound-network failure could affect both request shapes, despite the two earlier successful no-search preflights.
3. The search route may return transport successfully but fail downstream content/schema handling. The preserved failed runs currently provide no support for this because no ID, text, or tokens returned.
4. A model-specific problem is less likely: the same documented `gpt-5.4-nano` model and search call path completed prior coordinator runs. No alternate low-cost model is documented as supported on this HUIT route, so this diagnostic will not guess one.

The bounded diagnostic separates these possibilities with one no-search control followed by two small search-enabled calls. It does not scout the 150-row input or change research accounting.
