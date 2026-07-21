# Parallel Worker API Stability Diagnosis

Date: 2026-07-21

Disposition: no candidate import, no national queue/coverage rebuild, no CA25.2 or NJ25 scout coverage, and no Stage 2 promotion

## Plain-English conclusion

The Harvard credential and direct-SDK no-search request shape are currently valid from the main coordinator repository and from both worker worktrees. Five of five bounded sequential synthetic calls returned `OK` or `OK.`, a response ID, and positive output tokens. The three locations use the same `.env` Harvard credential, Python version, and relevant package versions. None has an `OPENAI_BASE_URL`, `OPENAI_API_KEY`, or standard proxy-variable override.

The failed worker attempts therefore do not look like a persistent bad key, wrong worktree, missing package, wrong base URL, wrong model, or wrong dual-header configuration. The strongest supported diagnosis is intermittent connection establishment or execution-context/proxy instability. Near-concurrent worker sessions may contribute, but this task intentionally did not send simultaneous calls, so concurrency causation is not proven. The current hosted-web-search path was also not retested because the authorization allowed no-search prompts only.

Parallel preparation remains useful, but parallel live execution should be paused. The safest current operating mode is to prepare and dry-run workers concurrently, then serialize each worker's smoke and full 25-row live run through one coordinator-controlled API lane. Keep the established 25-row batch size, 30-second smoke timeout, 90-second live timeout, `n_parallels=1`, and zero retries. The observed failures occurred in 0.014–0.245 seconds, so increasing timeouts would not address them. Splitting to 10 rows would not address a failure that occurs on the first request.

## Source relays and reconciliation

The two named relays were absent from the coordinator repo's `tmp/` when this task began. Read-only search found the exact ZIPs in the two local worker worktrees; unchanged copies were placed at the requested coordinator paths. No worker worktree was modified.

| Worker | Relay | SHA-256 |
| --- | --- | --- |
| Worker 1 CA25.2 | `tmp/parallel_worker_01_ca25_retry3_20260721_1605_relay_2026-07-21.zip` | `67a69db2859eb990f155caf104ed1d61d4d956394ccc3d4fc8f90f9574e61400` |
| Worker 2 NJ25 | `tmp/parallel_worker_02_nj25_retry3_stopped_connection_2026-07-21_relay_12f7293.zip` | `ffb20e1d5b9c04c4ae3e50beebc5290c1170c4d77d3b8422d77f8061a406fb3c` |

Worker 1's narrow relay does not carry the shared project instructions, progress/handoff, workflow/templates, backend documentation, or scout/test source. Worker 2 carries some of those files but not the main progress/handoff. The omitted shared files were read from coordinator commit `b47ff3b2a72e06d286ab907e7aa1a2375bf8a3d6`, the hardening commit used by the retry. The batch-specific worker artifacts take precedence for the actual attempt outcomes.

## Worker 1: CA25.2 retry 3

### Gate 0 and dry run

Gate 0 passed before any model/API action:

- preparation and hardening relays: present;
- worker-local `.env`: present;
- `HARVARD_SUBSCRIPTION_KEY` after `.env` load: present, value not recorded;
- interpreter: `/Users/joachimjohnson/Documents/RA_2026/Pol_Fire/parallel_worktrees/gabriel-worker-1/.venv/bin/python`;
- Python: 3.11.7;
- `openai`: 2.43.0;
- `httpx`: 0.28.1;
- `pandas`: 3.0.3;
- attempt-specific output parents: recorded writable in the originating worker run;
- fresh dry/smoke/live/log/relay paths: confirmed absent before execution; and
- protected national, canonical, corpus, progress, and handoff files: baselined and later unchanged.

The dry run passed. Its metadata records 25 requested California rows, `mode=dry_run`, and `live_attempted=false`. The preview contains the exact locked municipal employers and Census IDs and retains the required wrong-employer, ordinary-civilian comparator, safety-not-non-safety, context, blocked/dead, visible-year, duplicate, empty-output, public-records, and unverified-stage controls.

The dry-run command did not explicitly set `--n-parallels`, so its metadata displays the harmless dry-run default of 3. No backend was selected or called. The prospective live command correctly specified `--n-parallels 1`.

### Smoke and stop

The worker ran exactly one synthetic direct-SDK request:

- prompt: `Reply with OK.`;
- model: `gpt-5.4-nano`;
- base: `https://go.apis.huit.harvard.edu/ais-openai-direct/v2`;
- effective route: `/responses`;
- web search/tools: omitted;
- timeout: 30 seconds;
- retries: 0; and
- header names: `Authorization` and `Ocp-Apim-Subscription-Key`.

Exact sanitized result:

```text
APIConnectionError: Connection error.
```

The request returned no text, no response ID, no token-usage record, and zero output tokens. The smoke diagnostic reports `success=false`. The synthetic preflight artifact set is complete, including metadata, raw row, cost summary, empty parsed/failure CSVs, and sanitized console output.

### Live and merge disposition

- CA25.2 live command launched: no.
- Municipality research requests attempted: 0.
- Parseable municipality outcomes: 0.
- Candidate rows: 0.
- Mergeable output: none.
- Discovery coverage increment: 0.

There is no live directory because the worker correctly obeyed the smoke stop gate. Synthetic smoke files are infrastructure evidence and cannot enter the candidate queue or discovery coverage.

## Worker 2: NJ25 retry 3

### Gate 0 and dry run

Gate 0 passed:

- preparation and hardening relays: present;
- worker-local `.env`: present;
- `HARVARD_SUBSCRIPTION_KEY` after `.env` load: present, value not recorded;
- interpreter: `/Users/joachimjohnson/.pyenv/versions/3.11.7/bin/python3.11` via the worker `.venv/bin/python`;
- Python: 3.11.7;
- `openai`: 2.43.0;
- `httpx`: 0.28.1;
- `pandas`: 3.0.3;
- unique retry paths: fresh;
- attempt parents: recorded writable in the worker run; and
- protected national/canonical/corpus files: unchanged.

The dry run passed for the exact 25 locked NJ municipal employers. Metadata records `execution_status=dry_run_completed`, 25 requested rows, and no live attempt. The prompt review confirms all filtering and stage controls.

### Smoke success

The no-search smoke used the same configuration as Worker 1 and succeeded:

- response: `OK.`;
- response ID: present;
- input/reasoning/output/total tokens: 10 / 0 / 6 / 16;
- no tools or web search;
- timeout: 30 seconds; and
- retries: 0.

The smoke completed at approximately 16:02:34 EDT. The live process started at 16:02:47 EDT, about 13 seconds later.

### Live stop

The exact live command used the locked NJ25 CSV, direct SDK, `n_parallels=1`, 15-second prompt spacing, low hosted-search context, a 90-second timeout, zero SDK retries, and a batch-specific cost log.

The first two actual request outcomes were:

| Request | Elapsed | Exact sanitized error | Text | Response ID | Tokens |
| ---: | ---: | --- | --- | --- | --- |
| 1 | 0.218 s | `APIConnectionError: Connection error.` | empty | absent | none |
| 2 | 0.014 s | `APIConnectionError: Connection error.` | empty | absent | none |

The consecutive-error stop guard then created 23 explicit `stopped_before_request_after_repeated_connection_errors` ledger rows without issuing those calls.

Present artifacts:

- Gate 0 readiness note;
- 25-prompt dry preview and dry metadata;
- complete successful smoke artifacts;
- live `prompt_preview.md`;
- live `run_metadata.json`;
- 25-row `raw_outputs.csv`;
- header-only `parsed_candidates.csv`;
- 25-row `failed_parses.csv`;
- `cost_summary.json` and `cost_summary.csv`;
- batch-only `batch_cost_log.csv`;
- sanitized direct-SDK console;
- exact command, start/finish timestamps, stdout, empty stderr, and exit-code files;
- stop note; and
- validation outputs.

Absent by design or because no model output exists:

- no candidate handoff CSV;
- no candidate rows;
- no response IDs;
- no response text;
- no token usage; and
- no HTTP status or lower-level server trace for the two connection exceptions.

The pre-hardening runner returned process exit code 0 because its historic `live_succeeded` field meant only that the backend returned a dataframe. The same metadata correctly records zero backend successes, zero nonempty responses, `model_response_succeeded=false`, zero parseable outcomes, and 25 failed parses. That zero exit code was operationally misleading even though the stop note correctly rejected the result.

### Merge disposition

- Locked municipalities in ledger: 25.
- Actual requests: 2.
- Explicitly uncalled after stop: 23.
- Successful model responses: 0.
- Parseable outcomes: 0.
- Candidates: 0.
- Mergeable output: none.
- Discovery coverage increment: 0.

The 25 empty parser failures are not parseable `candidates=[]` results. They cannot count as discovery coverage.

## Sanitized environment and API-key comparison

Credential values were compared in memory only. No value, length, prefix, suffix, fingerprint, or hash was logged.

| Field | Main coordinator | Worker 1 | Worker 2 |
| --- | --- | --- | --- |
| `.env` exists | true | true | true |
| Harvard key present after load | true | true | true |
| `.env` Harvard key equal across all lanes | true | true | true |
| `OPENAI_API_KEY` present | false | false | false |
| `OPENAI_BASE_URL` present | false | false | false |
| `HTTP_PROXY` present | false | false | false |
| `HTTPS_PROXY` present | false | false | false |
| `ALL_PROXY` present | false | false | false |
| `NO_PROXY` present | false | false | false |
| Python version | 3.11.7 | 3.11.7 | 3.11.7 |
| `openai` | 2.43.0 | 2.43.0 | 2.43.0 |
| `httpx` | 0.28.1 | 0.28.1 | 0.28.1 |
| `pandas` | 3.0.3 | 3.0.3 | 3.0.3 |
| `python-dotenv` | 1.2.2 | 1.2.2 | 1.2.2 |
| `.venv/bin/python` exists | true | true | true |
| Worker-origin Gate 0 says `tmp/` writable | n/a | true | true |
| Current main-only coordinator probe says target `tmp/` writable | true | false | false |

The last row is a task-sandbox boundary, not a worker defect: this coordinator task was restricted to writing the main repo, so its audit process could not write the adjacent worker worktrees. It did not create a sentinel there. Each source worker's Gate 0, executed in its own authorized worker context, separately recorded its output parents as writable and did create the preserved artifacts.

Exact executable and working-directory paths:

| Lane | Python executable | Current working directory during diagnostic |
| --- | --- | --- |
| Main | `/Users/joachimjohnson/Documents/RA_2026/Pol_Fire/gabriel-wages/.venv/bin/python` | `/Users/joachimjohnson/Documents/RA_2026/Pol_Fire/gabriel-wages` |
| Worker 1 | `/Users/joachimjohnson/Documents/RA_2026/Pol_Fire/parallel_worktrees/gabriel-worker-1/.venv/bin/python` | `/Users/joachimjohnson/Documents/RA_2026/Pol_Fire/parallel_worktrees/gabriel-worker-1` |
| Worker 2 | `/Users/joachimjohnson/Documents/RA_2026/Pol_Fire/parallel_worktrees/gabriel-worker-2/.venv/bin/python` | `/Users/joachimjohnson/Documents/RA_2026/Pol_Fire/parallel_worktrees/gabriel-worker-2` |

## Request-shape confirmation

The production direct-SDK backend and the diagnostic use:

- base URL `https://go.apis.huit.harvard.edu/ais-openai-direct/v2`;
- SDK resource `/responses`, yielding `https://go.apis.huit.harvard.edu/ais-openai-direct/v2/responses`;
- model `gpt-5.4-nano`;
- `Authorization` bearer authentication supplied by the OpenAI SDK;
- `Ocp-Apim-Subscription-Key` supplied as a default header;
- zero SDK retries for these workers; and
- redaction plus explicit secret scans before diagnostic artifacts are accepted.

The current smoke payload contains only `model` and `input`. It does not include reasoning settings, tools, web search, or source inclusion. The research backend adds low reasoning effort and the hosted web-search tool only for separately authorized scouts.

This matches the successful 2026-07-17 request-shape diagnosis. The older diagnosis used OpenAI SDK 2.41.0; all current lanes use 2.43.0. Both versions succeed with the same `/v2/responses` route, model, and dual-header names. There is no evidence supporting a switch to `/v1`, Chat Completions, a different model, or subscription-only authentication.

## Bounded sequential synthetic diagnostic

The new helper is `scripts/diagnose_parallel_worker_api_stability.py`. It defaults to a no-network audit. Each explicit `--smoke` invocation sends one call, and a persistent ledger reserves the call before network execution and refuses a seventh call. It never prints or stores credential values or fingerprints.

Five calls ran in the authorized order. The optional sixth main call was unnecessary and was not sent.

| Call | Lane | Minimum scheduled gap | Result | ID | Input / reasoning / output / total | Elapsed |
| ---: | --- | --- | --- | --- | --- | ---: |
| 1 | Main | initial | `OK.` completed | present | 10 / 0 / 6 / 16 | 1.558 s |
| 2 | Worker 1 | immediate sequential | `OK.` completed | present | 10 / 0 / 6 / 16 | 1.094 s |
| 3 | Worker 2 | after 2 minutes | `OK` completed | present | 10 / 0 / 5 / 15 | 4.163 s |
| 4 | Worker 1 | after at least 5 minutes | `OK` completed | present | 10 / 0 / 5 / 15 | 1.141 s |
| 5 | Worker 2 | after at least 2 minutes | `OK` completed | present | 10 / 0 / 5 / 15 | 1.265 s |

Totals: 5/5 success, 50 input tokens, 0 reasoning tokens, 27 output tokens, and 77 total tokens. Every response ID was present, every output-token count was positive, and every exception field was empty.

Sanitized evidence is under `tmp/parallel_worker_api_stability_2026-07-21/`.

## Causal assessment

| Hypothesis | Assessment | Evidence |
| --- | --- | --- |
| Invalid Harvard key | Ruled out as a current/persistent cause | Same key succeeds from all three lanes; 5/5 current calls pass. |
| Different worker key | Ruled out | The three `.env` Harvard values compare equal in memory. |
| Missing `.env` or packages | Ruled out | All lanes have `.env`, `.venv`, and identical imports/versions. |
| Worktree path/location defect | Not supported | Both worktrees succeed twice in the current diagnostic. |
| Wrong base, route, model, or headers | Ruled out for current no-search use | Same request shape succeeds 5/5 and previously succeeded in the request-shape diagnosis and national batches. |
| Timeout too short | Strongly contradicted | Failures occurred in 0.014–0.245 seconds, far below 30/90 seconds. |
| Batch too large | Not supported as the initiating cause | NJ failed on requests 1 and 2; earlier serial 25-row runs succeeded. |
| Hosted-search payload/path | Still unknown, but a static defect is less likely | Not authorized in this diagnostic; earlier IL/NY/CA/NJ direct-SDK hosted-search runs succeeded. Current failures surfaced as connection errors before any HTTP response. |
| Concurrent or near-concurrent same-key sessions | Plausible but unproven | Worker attempts were running in parallel lanes and failures clustered around nearby activity; no simultaneous A/B call was authorized here. |
| Transient local network, execution authorization, HUIT proxy, TLS, or upstream transport | Strongest supported family | Generic `APIConnectionError`, no HTTP status/ID/tokens, sub-quarter-second failures, followed by 5/5 explicitly authorized sequential success. |
| Command/process logging defect | Confirmed secondary issue | Worker 2's fully failed run exited 0 under the old dataframe-return convention despite explicit metadata showing no successful/parseable output. |

The prior 2026-07-17 diagnosis also found that explicit outbound-network authorization distinguished a successful low-level control from earlier generic connection failures. These worker relays do not record a machine-readable network-execution authorization flag. Future readiness/command logs should record only whether outbound execution was explicitly authorized—not any credential or platform token.

## Code and protocol hardening from this diagnosis

The scout now treats a completed dataframe with zero parseable municipality outcomes as a failed process outcome:

- preserves raw output, failed parses, cost/usage, and sanitized logs;
- writes `execution_status=completed_no_parseable_outcome`;
- records `failure_stage=post_response_parse`;
- returns exit code 2;
- does not create a durable candidate handoff; and
- continues to count a successful parseable `candidates=[]` response as a valid discovery outcome.

The worker, coordinator, workflow, scaling ladder, locked CA/NJ prompts, and direct-SDK backend documentation now require parallel preparation but serialized smoke/live execution under one coordinator-controlled lane. A clean serialized recovery is not treated as proof of parallel-live Stage 1 stability.

## Limitations

- No simultaneous call was sent, so same-key concurrent-session behavior remains unmeasured.
- No hosted web search or municipality prompt was sent, so current tool-enabled service health remains unmeasured.
- The OpenAI SDK's generic `APIConnectionError` does not expose an HTTP status or HUIT request ID for the failed worker calls.
- The current successes prove present sequential health, not uninterrupted historical health.
- Only HUIT or network-layer logs can distinguish DNS, TLS, gateway reset, subscription routing, upstream model availability, and tool-backend transport when no HTTP response reaches the client.

## Accounting boundary

Neither relay contains a parseable municipality model output. The coordinator did not modify the national candidate queue, national scout coverage, global cost log, canonical contracts, canonical city coverage, or corpus. CA25.2 and NJ25 remain unscouted for this attempt.
