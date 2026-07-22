# Tier 1 Coordinator Retry Parent Audit

Date: 2026-07-22

Disposition: **PASS — parent lineage is complete, contains no successful municipality outcome, and supports one fresh full-input retry under the separate live gates.**

## Repository and locked input

- Starting commit: `c6b3664fee3bcfebd6ed3b7d8eddc0cedea004fb` (`Run Tier 1 serialized 150-row scout`).
- Required ancestors `bbb4dfa1a0836bf3fefe4e52c5f538ee59b08714`, `364fd9d`, and `c6b3664` are present in local history.
- The tracked worktree was clean. The pre-existing untracked root `package-lock.json` was reported and left untouched.
- Locked input: `docs/analysis/tier1_coordinator_150row_serial_live_input_2026-07-22.csv`.
- Locked SHA-256: `77b66569bcc2803e5067f84ad20b63e595f8c0611beb87820166b1a3a9de112b` — exact match.
- Current eligibility recheck: 150 rows; 150 unique municipality IDs; 150 unique Census IDs; ranks 1–150; Worker 1/2/3 each 50; one queue ID; exact expected 37-state/DC distribution; all Tier 1, future eligible, non-retry, non-failure-only, `not_scouted`, noncanonical municipal/place rows. Current queue, successful coverage, and canonical overlaps are all zero. The ten segregated failure-retry municipalities remain absent.

## Stopped parent

- Parent commit: `c6b3664`.
- Parent output: `tmp/tier1_coordinator_150row_serial_live_direct_sdk_2026-07-22`.
- Parent run ID: `all_2026-07-22_152105`.
- Parent input hash: exact locked hash above.
- Actually attempted rows: 2.
- Oklahoma City, OK: `connection_error`, 0.198 seconds, no response text, response ID, or token usage.
- Phoenix, AZ: `connection_error`, 0.005 seconds, no response text, response ID, or token usage.
- Stopped before request: 148 rows.
- Parseable outcomes: 0.
- Candidate rows: 0.
- Terminal status: `completed_no_parseable_outcome`, exit code 2, `model_response_succeeded=false`.

The preserved filenames are `run_metadata.json`, `row_timing.csv`, `failed_parses.csv`, `raw_outputs.csv`, `parsed_candidates.csv`, and `batch_cost_log.csv`. The requested generic names `failure_ledger.csv`, `scout_outputs_raw.jsonl`, and `scout_outputs_parsed.csv` are not this runner's artifact names; their functional equivalents were inspected instead.

The 148 raw/failure placeholders maintain row order but are explicitly `stopped_before_request` in the timing ledger. They are not attempted municipality failures. Oklahoma City and Phoenix also remain ordinary `not_scouted` targets because their parent outcomes were infrastructure-only and were never merged.

## Merge and retry decision

The parent is not merge-eligible because it contains no parseable municipality outcome and 148 rows were never requested. National queue/coverage/dashboard/priority outputs remain at their post-Wave-2 state: 1,009 queue rows; 504 successfully scouted municipalities; 391 candidate-positive; 113 parseable-empty; ten failure-only. No accounting builder was run for the parent.

A fresh full 150-row retry is appropriate. There are zero completed IDs to skip, so resume semantics would select the complete locked input anyway. The retry will use the fresh directory `tmp/tier1_coordinator_150row_serial_live_retry_direct_sdk_2026-07-22_attempt1`; the parent directory remains immutable.

The runner does not support a standalone `--lineage-note`, and its `--resume-lineage-note` is correctly rejected outside resume mode. It also refuses a non-empty output directory. Therefore the lineage text is prepared before live in a sibling staging file and copied unchanged into the newly created retry directory after process exit. This preserves both lineage evidence and the runner's fresh-output safety contract without a runner edit.

No remote, URL, verification, ingestion, codification, canonical/corpus, queue/coverage, dashboard, or priority mutation occurred during this audit.
