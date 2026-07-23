# Direct-SDK Outer-Timeout Failure Audit

Date: 2026-07-23

Disposition: **CONFIRMED — the stopped run contains no terminal row outcome and cannot enter official accounting or resume.**

## Repository and evidence state

- Latest local commit before this task: `bd5e2590ec01c7e0e8883b4299686f331af2c095`.
- Required ancestry: `bd5e259`, `6db14f0`, and `bef5077` are all ancestors of current `HEAD`.
- Tracked worktree at start: clean.
- Unrelated untracked local file: root `package-lock.json`; preserved and excluded.
- Stopped-run commit: `bd5e259` (`Run Post-PI Wave 1 compact adaptive scout`).
- Stopped output: `tmp/post_pi_wave1_coordinator_150row_serial_live_direct_sdk_2026-07-23_attempt1`.
- Run ID: `all_2026-07-23_105131`.
- Locked input SHA-256: `56e592291f1dbac83836acddcf0065df40141b51f9e93bfb548a040f52b8e700`.

## Stopped request

- First in-flight row: rank 1, Lake Oswego, OR.
- Locked municipality ID: `cog_2025_133204`.
- Census government ID: `133204`.
- Configured SDK/client timeout: 90 seconds.
- Started: `2026-07-23T10:51:31-0400`.
- Coordinator SIGINT: approximately `2026-07-23T10:57:20-0400`.
- Observed wall time before interruption: approximately 5 minutes 49 seconds.
- Response ID: absent.
- Response text: absent.
- Input/output/reasoning/total token usage: absent.
- Candidate artifact: absent.
- Failed-parse ledger: absent.
- Cost artifact: absent.
- Console output: empty.

The runner had written its prompt preview, initial `run_metadata.json`, and a 150-row planned `row_timing.csv`. All 150 timing records remained `success_status=pending_live_attempt` and `parse_status=pending`; none had started/finished timestamps or elapsed time.

## Evidence and accounting disposition

- Completed/checkpointed row attempts: zero.
- Parseable rows: zero.
- Candidate-positive rows: zero.
- Parseable-empty rows: zero.
- Official failure-only rows: zero.
- Merge eligibility: `false`.
- Queue/coverage/dashboard/yield/priority rebuild: none.
- Official scout coverage: unchanged at 794 municipalities.

The first request was known to be in flight operationally, but the immutable runner ledger has no terminal row evidence. Treating that row as an official timeout after the fact would invent lifecycle data that the process never checkpointed.

## Why merge and resume are blocked

The stopped directory cannot be merged because no row reached a terminal backend or parse state. It cannot be resumed under the safe resume contract because `run_metadata.json` remains `execution_status=live_started`; the resume loader accepts only terminal parent statuses and deliberately rejects possible artifact/lifecycle loss. Even if that terminal gate were bypassed, zero completed municipality IDs means `--skip-completed-municipality-ids` would select the entire input and constitute a new full run, not a bounded continuation.

The stopped directory therefore remains immutable, quarantined non-evidence. A future run must use a fresh output directory.

## Failure hypothesis

The direct backend configured `httpx.Timeout(90)` on `AsyncOpenAI`, but the hosted-search Responses API lifecycle remained pending far beyond that value. The evidence is consistent with the SDK/httpx timeout not bounding the complete hosted-tool lifecycle, or with a layer in that lifecycle not responding to the transport deadline. The direct call had no independent outer wall-clock guard, so the runner could not synthesize a terminal timeout row, update row timing, feed adaptive pacing, increment the consecutive-transport-failure gate, or return control to final artifact writing.

The appropriate implementation fix is an outer per-row async deadline around each `client.responses.create(...)` awaitable while retaining the existing SDK/httpx timeout.

## Files used

- `AGENTS.md`
- `PROGRESS.md`
- `docs/analysis/chatgpt_handoff_latest.md`
- `docs/analysis/post_pi_wave1_coordinator_150row_serial_live_result_review_2026-07-23.md`
- `docs/analysis/post_pi_wave1_coordinator_150row_serial_live_queue_coverage_update_2026-07-23.md`
- `docs/analysis/post_pi_wave1_dashboard_yield_checkpoint_refresh_2026-07-23.md`
- `docs/analysis/post_pi_wave1_priority_refresh_decision_2026-07-23.md`
- `docs/analysis/post_pi_wave1_coordinator_validation_2026-07-23.md`
- `tmp/post_pi_wave1_coordinator_150row_serial_live_direct_sdk_2026-07-23_attempt1/run_metadata.json`
- `tmp/post_pi_wave1_coordinator_150row_serial_live_direct_sdk_2026-07-23_attempt1/row_timing.csv`
- `tmp/post_pi_wave1_coordinator_150row_serial_live_direct_sdk_2026-07-23_attempt1/stop_note.txt`
- `tmp/post_pi_wave1_coordinator_150row_serial_live_direct_sdk_2026-07-23_attempt1/exit_code.txt`
- `tmp/post_pi_wave1_coordinator_150row_serial_live_direct_sdk_2026-07-23_attempt1/coordinator_console_output.log`
- `docs/analysis/post_pi_wave1_coordinator_150row_serial_live_input_2026-07-23.csv`
- `docs/analysis/post_pi_wave1_coordinator_150row_serial_live_input_audit_2026-07-23.md`

No live call, diagnostic, hosted search, source access, verification, ingestion, codification, or accounting mutation occurred in this audit.
