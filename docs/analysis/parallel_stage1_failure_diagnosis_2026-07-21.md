# Stage 1 Parallel Scout Failure Diagnosis

Date: 2026-07-21
Disposition: no candidate import, no queue/coverage rebuild, no Stage 2 promotion

## Plain-English conclusion

The first two-worker Stage 1 attempt did not produce a mergeable scout batch. Worker 1 stopped correctly when its synthetic direct-SDK smoke could not connect. Worker 2 passed its smoke and launched the live command, but the live directory contains only the rendered prompt preview. There is no evidence showing whether the live process reached a model request, returned a response, failed during dependency/client setup, was externally terminated, or exited for another reason.

The coordinator must not run the queue/coverage merge. There are no worker candidate rows to import, no parseable empty outputs to count, and no row-level transport ledger from either locked batch. CA25.2 and NJ25 therefore remain wholly unresolved for this Stage 1 attempt. None of their 50 municipalities gains scout coverage, and the current attempt does not qualify as a completed Stage 1 stability test.

## Source reconciliation

The two exact ZIPs were absent from the main coordinator repository's `tmp/` at the start of diagnosis. Read-only search located them in the two local worker worktrees; unchanged copies were placed at the requested coordinator paths before inspection. No worker worktree was modified.

| Worker | Relay | SHA-256 |
| --- | --- | --- |
| Worker 1 CA25.2 | `tmp/parallel_worker_01_ca25_retry2_preflight_stop_2026-07-21_relay_a00cb19.zip` | `cc6f58e6f0d8455fad5496f2f518d84bf5449d4ecfa795c364c060ed0f591c3b` |
| Worker 2 NJ25 | `tmp/parallel_worker_02_nj25_fresh_retry_incomplete_2026-07-21_relay_7f9db4e.zip` | `4e745fab70fff4566d3aeb52004cb58937a551f996bd4a9c7c938b7f425e4d1a` |

Neither narrow worker relay contains `AGENTS.md`, `PROGRESS.md`, the main handoff, the scout script, or the two scout tests. Their batch-specific workflow and worker prompts are present. The omitted shared files were read from coordinator commit `11c92e71f445e9f061a4c11dcdaf84f687040fc0`, which is the prompt-template checkpoint on which the workers were based. The omissions are relay-packaging gaps, not result artifacts.

## Worker 1: CA25.2

### Dry-run result

The fresh retry dry run passed. It rendered the exact 25 locked CA municipal prompts under:

`tmp/gabriel_state_source_scout/CA/parallel_worker_01_ca25_retry2_filter_contract_dry_run_2026-07-21/`

The metadata records `mode=dry_run`, `municipalities_requested=25`, and `live_attempted=false`. The dry review confirms the exact employer/Census identifiers, prohibited-employer exclusions, ordinary civilian comparator rule, safety-not-non-safety rule, context/access/year/duplicate fields, allowed empty output, public-records prohibition, and unverified-stage boundary.

### Smoke result

The local `.env` existed and the required subscription-key variable was present after loading; the worker did not print the value. The one-request direct-SDK smoke then failed.

Exact sanitized error:

```text
APIConnectionError: Connection error.
```

The smoke produced no response text, no response ID, no input/reasoning/total-token record, and zero output tokens. Its raw row reports `Successful=False`; diagnostic metadata reports `success=false` and `response_id_present=false`. The observed elapsed time was approximately 0.245 seconds.

### Live and merge disposition

- CA25.2 research live command launched: **no**.
- Locked municipality requests attempted: **0**.
- Parseable municipality outcomes: **0**.
- Candidate rows: **0**.
- Candidate handoff CSV: **absent**.
- Mergeable output: **none**.
- Discovery coverage increment: **0**.

The smoke's own `raw_outputs.csv` and `parsed_candidates.csv` are synthetic preflight artifacts. They are not CA25.2 research outputs and must never enter the national candidate queue or coverage accounting.

## Worker 2: NJ25

### Dry-run result

The fresh retry dry run passed for the exact 25 locked NJ municipalities. It wrote a 25-prompt preview and dry-run metadata under:

`tmp/gabriel_state_source_scout/NJ/parallel_worker_02_nj25_filter_contract_dry_run_2026-07-21/`

The review records the full employer/unit/filtering contract and `live_attempted=false`. The requested `.venv/bin/python` was absent in this worker copy; the worker used a functioning system Python 3.11.7 and confirmed the `openai` import. The relay does not preserve a full package-version preflight.

### Smoke result

The direct-SDK smoke passed:

- response text `OK.`;
- response ID present;
- 10 input, 0 reasoning, 6 output, and 16 total tokens;
- one request;
- no tools or search;
- zero retries; and
- no connection error.

### Live-command result

The worker review states that the exact locked NJ25 live direct-SDK command launched once with `--n-parallels 1`, 15-second spacing, zero SDK retries, and a batch-specific cost-log path. It then returned without preserved console output.

The live output directory contains exactly one file:

```text
prompt_preview.md
```

Present live artifact:

- `prompt_preview.md` — 202,054 bytes, containing the rendered 25 prompts.

Missing live artifacts:

- `run_metadata.json`;
- `raw_outputs.csv`;
- `parsed_candidates.csv`;
- `failed_parses.csv` or another row-level failure ledger;
- `cost_summary.json` and `cost_summary.csv`;
- batch-specific cost log;
- sanitized live console/command log;
- recorded live exit code; and
- normalized candidate handoff CSV.

The smoke directory has its own complete synthetic artifacts, but those cannot substitute for the missing live evidence.

### Live and merge disposition

- Live command launched: **yes, according to the worker review**.
- Live exit code: **unknown**.
- Backend-successful responses recorded: **0**.
- Parseable outputs recorded: **0**.
- Candidate rows: **0**.
- Whether any API request actually left the process: **unknown**.
- Mergeable output: **none**.
- Discovery coverage increment: **0**.

NJ25 cannot be classified as 25 connection failures, 25 stopped-before-request rows, or 25 parseable empty results. The evidence supports only an incomplete run with no classifiable municipality outcome.

## Why the coordinator merge must not run

The coordinator merge is an accounting operation over auditable model outcomes. It requires row-level evidence that each municipality either produced a parseable candidate list, produced a parseable empty list, or experienced a preserved failure. Neither relay supplies such evidence for its research batch:

- Worker 1 stopped before the research batch because smoke failed.
- Worker 2 has no run metadata, raw outputs, parsed-output file, or failure ledger.

Running the merge would require inventing outcomes. Marking rows covered would overstate discovery. Marking them as connection failures would also be unsupported for Worker 2. Adding smoke artifacts to the candidate queue would confuse synthetic infrastructure output with research scouting. The only valid coordinator action is to preserve the relays, document the failed Stage 1 attempt, harden the protocol, and leave national queue/coverage unchanged.

## Likely failure modes and evidence

| Possible failure mode | Worker | Evidence | Assessment |
| --- | --- | --- | --- |
| Transient proxy/network connection failure | 1 | Generic `APIConnectionError`, no ID/text/tokens, failure after about 0.245 seconds; Worker 2 passed the same style of smoke shortly afterward | Plausible; exact DNS/TLS/proxy layer unknown |
| Worker-local network, proxy, TLS, or process-environment difference | 1 | Credential variable was present, yet connection failed in only one worker | Plausible; relay lacks lower-level exception cause and environment comparison |
| Invalid/missing credential | 1 | Earlier attempt had setup trouble, but retry confirmed variable presence; error was connection rather than an HTTP authentication response | Less supported for retry; value correctness was intentionally not printed or independently validated |
| Missing live-only Python package, especially `pandas`, or incompatible package versions | 2 | Dry run avoids live imports; smoke proves an SDK path but the scout live function imports `httpx`, `pandas`, and `openai` before its internal exception handler; relay confirms only Python and `openai` import | Plausible and currently untested |
| Unhandled exception before the scout's existing failure handler | 2 | The pre-hardening script used by the worker wrote `prompt_preview.md` before invoking the backend but wrote `run_metadata.json` only after the backend returned or returned a handled failure | Plausible; stderr/exit code missing |
| External termination, session loss, interrupt, or process kill during the live batch | 2 | Prompt preview exists, but no post-backend artifact or console/exit record exists | Plausible; impossible to distinguish from an unhandled setup error |
| Worker packaged the relay before the live process fully completed | 2 | No lifecycle/exit record was captured | Possible; relay alone cannot confirm process state at packaging time |
| Valid model run with lost candidate files | 2 | No response IDs, raw rows, token usage, or metadata exist | Unsupported; must not be assumed |

## What remains unknown

- Worker 1's underlying DNS, TLS, proxy, socket, or routing cause.
- Whether Worker 1's credential would have been accepted if transport had reached the API.
- Worker 2's live exit code and stdout/stderr.
- The exact Python executable used for Worker 2's live command.
- Worker 2's `openai`, `httpx`, and `pandas` versions and whether all imports succeeded in that process.
- Whether Worker 2 reached client construction, sent any requests, received any responses, or was killed before the first request.
- Whether an external agent/session timeout ended Worker 2 while the serial 25-row process was still active.

## Required hardening before the same-stage retry

1. Do not advance to Stage 2. Stage 1 has not been proven.
2. Retry only the same locked CA25.2 and NJ25 batches, under new explicit live authorization, after this hardening is committed.
3. Give every dry, smoke, live, command-log, and relay directory a unique timestamped or retry-labeled path. Never reuse either failed/incomplete directory.
4. Before dry/smoke/live execution, confirm the preparation relay, local `.env`, key-variable presence without value disclosure, writable parents, exact Python executable, and `openai`/`httpx`/`pandas` versions.
5. Record protected global queue/coverage hashes or a scoped starting diff so a worker can prove it did not mutate national accounting.
6. Write `run_metadata.json` before entering the live backend and update it on handled failure, unhandled exception, zero-row return, and successful completion.
7. Capture the exact launched command, exit code, and sanitized stdout/stderr at the command-wrapper level. If no output exists, record that absence explicitly.
8. On any nonzero exit or incomplete artifact set, create a stop note listing present/missing artifacts and the mergeability decision. Do not retry inside that worker task.
9. Stagger the two worker starts by 5–10 minutes. Keep direct SDK, `--n-parallels 1`, 15-second prompt spacing, and zero SDK retries.
10. If either smoke fails, stop that worker and do not launch its live scout.
11. Do not start the coordinator merge until both workers produce complete relays with parseable model-output evidence. A preflight-stop or prompt-preview-only relay is a Stage 1 failure, not a partial merge input.

These changes improve evidence preservation; they do not claim to fix the underlying HUIT/proxy instability. The retry remains a bounded Stage 1 infrastructure and throughput test, not permission to scale or to verify/ingest any source.
