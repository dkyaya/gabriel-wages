# GABRIEL Working-vs.-Broken Scout Comparison

Date label: 2026-07-17 (audit performed 2026-07-20)
Scope: preserved local artifacts, installed-client files, current sanitized configuration, and local Git history only; no model/API call, scout, source retrieval, ingestion, codification, remote inspection, or push

## Plain-English summary

The model, proxy base URL, request family, headers, timeout, serial execution settings, and `run_live_batch()` implementation did **not** change between the last working Pennsylvania/Texas scouts and the failed Massachusetts/synthetic runs. The current local client still constructs exactly:

`POST https://go.apis.huit.harvard.edu/ais-openai-direct/v2/responses`

with model `gpt-5.4-nano`, an OpenAI bearer credential plus `Ocp-Apim-Subscription-Key`, and—only for research scouts—the Responses API web-search tool. The two synthetic tests used the same GABRIEL/OpenAI construction with web search disabled and still failed. The stricter Massachusetts row-aware/filter-contract changes altered prompt text and parsing fields, not the client or URL.

The strongest **local** explanation is a difference in the command's execution environment, specifically network authorization/sandboxing. This execution environment restricts network access by default. The successful Texas command is preserved in the local execution approval state as an exact network-approved command; no corresponding persistent approval is present for the Massachusetts or synthetic commands. The failed calls returned in roughly 1–2 seconds after invocation, before any HTTP status, response ID, reasoning token, output token, or web-search source existed. That is consistent with DNS/socket/TLS egress being blocked before the request reached HUIT. Repository artifacts do not preserve per-invocation sandbox/escalation metadata, so this is strongly supported but not proven.

The next most plausible local family is a machine/network-path change—VPN, DNS, TLS trust, firewall, or another egress intermediary—between Texas at 16:45 EDT and Massachusetts at 18:32 EDT. A historical ambient `HARVARD_SUBSCRIPTION_KEY` override is also possible because `load_dotenv()` uses `override=False`, but it is less supported: the project `.env` file predates every run and has not changed on disk, the current ambient key is absent, and HUIT reports that the key works on its side.

The evidence rules out a post-Texas `run_live_batch()` regression, a model-name change, a switch from Responses to chat completions, a duplicated `/v2` or `/responses` path, web search as a necessary trigger, concurrency, and the Massachusetts input shape as primary causes. It does not yet reveal the swallowed low-level exception cause or prove whether the failed process had outbound network permission.

## Starting state and evidence boundary

- Latest local commit before this audit: `3c0d37fc081e9c14fe5573be1387391f5fab2eec` (`Audit GABRIEL proxy URL construction`).
- Source-of-truth relay: `tmp/gabriel_url_baseurl_audit_2026-07-17_relay_3c0d37f.zip`.
- Relay reconciliation: 17 carried files; all 17 matched the corresponding workspace files by SHA-256 before edits.
- Initial working tree: only pre-existing untracked `.claude/`; it was not touched.
- No Git remote command was run. Local `git status`, `log`, `show`, and `diff` were used.
- Historical shell sandbox/escalation decisions are not written into scout `run_metadata.json`; the execution-context finding below uses the current local execution policy/approved-command state plus the preserved timing/error signatures. It is therefore a ranked diagnosis, not a claim of definitive proof.

## Exact production request path

The current code path is `main()` → `run_live_batch()` → `gabriel.whatever()` → GABRIEL `Whatever.run()` → `get_all_responses()` → `get_response()` → cached `openai.AsyncOpenAI` → `client.responses.create()`.

In `scripts/gabriel_state_source_scout.py`:

1. `HARVARD_PROXY_BASE_URL` is hardcoded to `https://go.apis.huit.harvard.edu/ais-openai-direct/v2` (line 61).
2. `run_live_batch()` searches project `.env`, then parent `.env`, loads the first existing file with the default `override=False`, and reads `HARVARD_SUBSCRIPTION_KEY` (lines 1361–1370).
3. It temporarily sets `OPENAI_API_KEY` from that subscription key and sets `OPENAI_BASE_URL` to the hardcoded base (lines 1383–1386).
4. It also passes explicit `api_key`, explicit `base_url`, and `extra_headers={"Ocp-Apim-Subscription-Key": ...}` to `gabriel.whatever()` (lines 1393–1418).
5. The research scout passes `web_search=True`, requested `search_context_size`, `reasoning_effort="low"`, `max_retries=1`, timeout/max-timeout, `dynamic_timeout`, and `background_mode=False`.
6. Installed GABRIEL 1.1.8 selects the OpenAI Responses API for this non-audio task. Installed OpenAI SDK 2.41.0 appends resource `/responses`, yielding one and only one `/v2/responses` path.
7. The project parser runs only after GABRIEL returns response text. The failed MA/smoke rows have no text to parse.
8. The prior OpenAI environment values are restored in `finally`.

At the working default/recommended configuration, the effective request is:

```text
request family: OpenAI Responses API
method/path: POST /ais-openai-direct/v2/responses
model: gpt-5.4-nano
timeout/max_timeout: 90/90 seconds
dynamic_timeout: false
max_retries: 1
headers: Authorization; Ocp-Apim-Subscription-Key
research tool: web_search, search_context_size=low
```

## Successful live scout inventory

The table below includes every preserved `gabriel_state_source_scout` live run with at least one nonempty/parseable response. All used model `gpt-5.4-nano`, search context `low`, `web_search=True`, and the same Harvard proxy/Responses request family. “IDs” means raw rows with a recorded response ID; an ID did not always imply usable text in early GABRIEL runs. Token counts are input / reasoning / output. Timestamps are EDT and come from the run ID.

| Run | Execution/artifact commits | Configuration | Input shape | IDs; usage; cost | Parse result and error log |
|---|---|---|---|---|---|
| PA pilot `pa_2026-07-14_203532` | base `86519f8`; artifacts `d3006ff` | full; `n=3`; no spacing; 90/90 historical hardcoded defaults | 10 rows, 6 columns (3 required plus planning context) | 10/10 IDs; 116,922 / 5,234 / 7,475; `$0.03927065` | 3/10 (30%); 4 capacity/timeout rows and 3 empty-with-response-ID rows |
| PA retry `pa_2026-07-14_223544` | base `d3006ff`; artifacts `f08d614` | full; `n=1`; no spacing; 90/90 historical hardcoded defaults | 7 rows, 7 columns (pilot fields plus retry reason) | 7/7 IDs; 27,955 / 1,156 / 2,186; `$0.00976850` | 1/7 (14%); 6 capacity/timeout rows |
| PA timeout stress `pa_2026-07-15_101602` | base `f08d614`; artifacts/fix `6c041ca` | minimal; `n=2`; 5 sec; 180/240, dynamic | 6 selected from the 10-row/6-column pilot input | 6/6 unique IDs; 124,494 / 5,168 / 7,240; `$0.04040880` | corrected 3/6 (50%); 3 limiter-capacity failures; original 12-row checkpoint echo superseded by corrected files |
| PA dedup confirmation `pa_2026-07-15_104013` | base `6c041ca`; artifacts `7fd2e68` | minimal; `n=1`; 15 sec; 90/90 | 3 retry-filtered rows from the 10-row/6-column pilot input | 3/3 IDs; 120,543 / 4,927 / 6,785; `$0.03874860` | 3/3 (100%); no error rows |
| PA concurrency micro-test `pa_2026-07-15_104359` | base `6c041ca`; artifacts `7fd2e68` | minimal; `n=2`; 15 sec; 90/90 | same 3 rows | 3/3 IDs; 30,344 / 1,170 / 2,667; `$0.01086505` | 2/3 (67%); Lancaster limiter-capacity failure |
| PA matrix cell 1 `pa_2026-07-15_110146` | base `7fd2e68`; artifacts `e53d87e` | minimal; `n=1`; 10 sec; 90/90 | same 3 rows | 3/3 IDs; 95,517 / 4,310 / 5,968; `$0.03195090` | 3/3 (100%); no error rows |
| PA matrix cell 2 `pa_2026-07-15_110349` | base `7fd2e68`; artifacts `e53d87e` | minimal; `n=1`; 20 sec; 90/90 | same 3 rows | 3/3 IDs; 92,405 / 3,847 / 5,777; `$0.03051100` | 3/3 (100%); no error rows |
| PA matrix cell 3 `pa_2026-07-15_110557` | base `7fd2e68`; artifacts `e53d87e` | minimal; `n=2`; 20 sec; 90/90 | same 3 rows | 3/3 IDs; 64,138 / 3,031 / 4,582; `$0.02234385` | 2/3 (67%); Lancaster limiter-capacity failure |
| PA matrix cell 4 `pa_2026-07-15_110810` | base `7fd2e68`; artifacts `e53d87e` | full; `n=1`; 20 sec; 90/90 | same 3 rows | 3/3 IDs; 108,175 / 3,534 / 5,733; `$0.03321875` | 3/3 (100%); no error rows |
| PA batch-25 main `pa_2026-07-15_114435` | base `e53d87e`; artifacts `325bef6` | minimal; `n=1`; 15 sec; 90/90 | 25 rows, 7 columns | 20/25 actual `resp_` IDs; 667,744 / 30,021 / 38,145; `$0.21875630` | 20/25 (80%); 4 final `Connection error.` rows plus 1 final timeout row |
| PA batch-25 retry `pa_2026-07-15_120857` | base `e53d87e`; artifacts `325bef6` | identical to main | 5 failed IDs selected from same 25-row/7-column file | 5/5 IDs; 146,569 / 6,954 / 9,646; `$0.05006380` | 5/5 (100%); no errors; combined PA batch 25/25 |
| TX `tx_2026-07-16_164549` | base `31189a5`; artifacts `4824117` | minimal; `n=1`; 15 sec; 90/90 | 3 rows, 22 columns | 3/3 IDs; 95,158 / 5,521 / 7,002; `$0.03468535` | 3/3 (100%); no errors |

The PA batch-25 evidence is especially important. Four connection-error rows and one timeout failed during the main process, yet all five succeeded minutes later with the same executable, base URL, key-loading logic, request family, model, prompt mode, concurrency, spacing, and timeout. Thus GABRIEL's generic `Connection error.` has already been demonstrated to be a transport-state symptom, not a deterministic prompt/path/configuration verdict.

## Priority working commands

The Texas command is preserved verbatim in its review:

```bash
MPLCONFIGDIR=/tmp/gabriel-wages-mpl-cache python scripts/gabriel_state_source_scout.py \
  --state TX \
  --municipalities-csv docs/analysis/national_batch01_tx_scout_input_2026-07-16.csv \
  --output-dir tmp/gabriel_state_source_scout/TX/national_batch01_tx_live_2026-07-16 \
  --prompt-mode minimal \
  --max-prompts 3 \
  --n-parallels 1 \
  --sleep-between-prompts 15 \
  --search-context-size low \
  --live
```

The exact PA shell text was not saved as a single command line, but metadata, paths, logs, and `PROGRESS.md` reconstruct its effective invocation without ambiguity:

```bash
python scripts/gabriel_state_source_scout.py \
  --state PA \
  --municipalities-csv docs/analysis/gabriel_state_source_scout_pa_batch25_municipalities_2026-07-15.csv \
  --output-dir tmp/gabriel_state_source_scout/PA/2026-07-15_batch25_main \
  --prompt-mode minimal --max-prompts 25 \
  --n-parallels 1 --sleep-between-prompts 15 \
  --timeout 90 --max-timeout 90 \
  --search-context-size low --model gpt-5.4-nano --live

python scripts/gabriel_state_source_scout.py \
  --state PA \
  --municipalities-csv docs/analysis/gabriel_state_source_scout_pa_batch25_municipalities_2026-07-15.csv \
  --retry-failed-from tmp/gabriel_state_source_scout/PA/2026-07-15_batch25_main/failed_parses.csv \
  --output-dir tmp/gabriel_state_source_scout/PA/2026-07-15_batch25_retry \
  --prompt-mode minimal --max-prompts 5 \
  --n-parallels 1 --sleep-between-prompts 15 \
  --timeout 90 --max-timeout 90 \
  --search-context-size low --model gpt-5.4-nano --live
```

The older PA commands use the same common prefix and the per-run configuration shown in the inventory table. Where the early metadata predates explicit timeout/prompt fields, the contemporaneous methodology and code establish the then-hardcoded 90/90 timeout and full prompt.

## Failed run inventory

| Run | Commit/context | Configuration | Input shape | IDs; usage; cost | Result and error |
|---|---|---|---|---|---|
| MA primary `ma_2026-07-16_183246` | execution base `94ac4e9`; artifacts `7ce744b` | `gpt-5.4-nano`; minimal; `n=1`; 15 sec; 90/90; low; web search on | 8 rows, 22 columns | 0/8 IDs; 6,414 / 0 / 0; `$0.00128280` | 0/8 parseable; all empty, all `Connection error.` |
| MA retry 1 `ma_2026-07-16_183405` | same process session/code | same | first 3 failed IDs selected from primary failure ledger | 0/3 IDs; 2,296 / 0 / 0; `$0.00045920` | 0/3; all `Connection error.` |
| MA remaining/retry 2 `ma_2026-07-16_183534` | same process session/code | same | 5-row/22-column pending projection | 0/5 IDs; 4,118 / 0 / 0; `$0.00082360` | 0/5; all `Connection error.` |
| Synthetic diagnosis, 2026-07-16 19:01:04 | base `7ce744b`; artifacts `6c7c766` | same model/base/header/GABRIEL wrapper; `n=1`; 90/90; web search off | one 13-token JSON-only prompt; no CSV | 0/1 IDs; 13 / 0 / 0; `$0.00000260` | no response; `Connection error.` |
| Synthetic retest, 2026-07-17 14:11:02 | base `6c7c766`; artifacts `85a8dd` | same as diagnosis | one 13-token JSON-only prompt | 0/1 IDs; 13 / 0 / 0; `$0.00000260` | no response; `Connection error.`; `model_response_succeeded=false` |

Combined MA research attempts: 16/16 failed calls, 12,828 input tokens, zero reasoning/output tokens, no response IDs, and `$0.00256560` recorded cost. These are transport failures, not source-absence results.

The exact primary shell wrapper was not recorded verbatim, but all effective arguments are fixed by metadata/artifacts:

```bash
python scripts/gabriel_state_source_scout.py \
  --state MA \
  --municipalities-csv docs/analysis/national_batch01_ma_scout_input_2026-07-16.csv \
  --output-dir tmp/gabriel_state_source_scout/MA/national_batch01_ma_live_2026-07-16 \
  --prompt-mode minimal --max-prompts 8 \
  --n-parallels 1 --sleep-between-prompts 15 \
  --search-context-size low --live
```

The first bounded retry used the primary 8-row input plus `--retry-failed-from tmp/gabriel_state_source_scout/MA/national_batch01_ma_live_2026-07-16/failure_ledger_pre_retry.csv`, `--max-prompts 3`, and the `_retry_failed` output directory. The second used `tmp/gabriel_state_source_scout/MA/national_batch01_ma_live_2026-07-16_pending_first_attempt.csv`, `--max-prompts 5`, and the `_remaining_first_attempt` output directory. Both retained the primary settings.

Both synthetic commands are preserved directly:

```bash
python tmp/gabriel_proxy_connection_diagnosis_2026-07-16/gabriel_proxy_smoke_test.py
python tmp/gabriel_proxy_connection_retest_2026-07-17/gabriel_proxy_smoke_test.py
```

The first synthetic metadata says `sleep_between_prompts=15`, but the script makes one prompt in one `gabriel.whatever()` call and does not pass a sleep parameter. The field is descriptive and has no request effect.

## Working-versus-broken configuration comparison

| Dimension | PA batch-25 / TX working | MA / synthetic broken | Finding |
|---|---|---|---|
| `run_live_batch()` | same 118-line function | same | exact extracted SHA-256 `fa85ec21193251a0878aa9fcae87e1688f4903cc2a87d0aa957f88a135c6690e` at `325bef6`, `31189a5`, `94ac4e9`, `7ce744b`, and current HEAD |
| Base URL | hardcoded `…/ais-openai-direct/v2` | same | no code/config difference |
| Effective resource | SDK `/responses` | same | no request-family/path change |
| Model | `gpt-5.4-nano` | same | unchanged |
| Headers | bearer + subscription-key header | same | unchanged |
| GABRIEL/OpenAI client | GABRIEL 1.1.8 / OpenAI 2.41.0 global Python environment | same installed files | relevant files have June 8 mtimes, before all compared runs |
| Prompt mode | PA main/TX minimal | MA minimal; synthetic tiny JSON | synthetic failure rules prompt content out |
| Input | PA 25×7; TX 3×22 | MA 8×22; smoke no CSV | TX proves 22-column row-aware input works; smoke rules CSV shape out |
| Web search | on | on for MA; off for smoke | smoke rules web-search payload out as a necessary cause |
| Concurrency | 1 | 1 | unchanged; not concurrency pressure |
| Spacing | 15 sec | 15 sec MA; irrelevant single smoke | unchanged for scouts |
| Timeout | 90/90 | 90/90 | failures occur before timeout ceiling |
| Interpreter evidence | PA log references global pyenv Python 3.11 site-packages; TX command uses `python` | MA retry log references the same global site-packages; smoke uses `python` | no observed interpreter/package switch; an unrecorded activated environment remains theoretically possible |
| Matplotlib cache environment | Texas explicitly sets `MPLCONFIGDIR` | MA retries/smoke show unwritable-cache warnings | harmless import/cache difference; requests execute after the warning and fail separately |
| Execution network context | Texas exact command is locally retained as an approved network command | no matching persistent MA/smoke approval is retained | strongest local operational difference; historical one-time escalation remains unknown |

## Code-history answer

### Did `run_live_batch()` change after the last successful run?

No. Local `git log -L :run_live_batch:scripts/gabriel_state_source_scout.py` shows its last edits at `6c041ca` on 2026-07-15, before PA batch 25 and Texas. An AST-bounded extraction is identical at:

- PA artifact commit `325bef67e9a994ef9882fbf86e69c1dc90b156f4`;
- Texas execution commit `31189a5df9f0a8493f612de9c5a9d0191ac70a2f`;
- MA execution-base commit `94ac4e980b8da4d9e17847b818c6c04989ac1a6d`;
- MA artifact commit `7ce744b32f1b8d235d5d1ea918914a2902479ad1`;
- current pre-audit HEAD `3c0d37fc081e9c14fe5573be1387391f5fab2eec`.

Every extraction has the same 118 lines and the same SHA-256 shown above.

### What did change between Texas and Massachusetts?

Commit `f24771f25c3648f082cafb2c4236b1c43cfb235b` tightened the **minimal prompt and output contract**: new unit/document/stage distinctions, six candidate-stage fields, parser normalization, and deterministic scoring changes. Commit `94ac4e9` added the MA input/dry-run artifacts. Neither changed base URL, client initialization, headers, model, tool construction, timeout behavior, request family, or `run_live_batch()`.

Prompt changes can alter token length or model behavior after connection, but they cannot explain the synthetic no-search/no-municipality failure and do not plausibly produce a client-side connection error before a response ID.

### Did dependency versions or wrapper behavior change?

No repository dependency change was found. `requirements.txt` has no change from the PA execution base through current HEAD and only specifies `openai>=1.0`; GABRIEL is not pinned there. The actual global environment used in preserved PA/MA logs contains GABRIEL 1.1.8 and OpenAI SDK 2.41.0. Relevant installed files have creation/modification timestamps of 2026-06-08, more than a month before PA/TX/MA, and no later filesystem modification is present.

The repo-local `.venv` contains OpenAI 2.43.0, but the live PA and MA retry logs point to the global pyenv site-packages, not `.venv`. No artifact shows a live-run switch to the repo-local version. Historical process provenance was not explicitly saved, so this is strong filesystem/log evidence rather than a cryptographic runtime manifest.

### Did the smoke diagnostic use the same request construction as the scout?

Substantially yes, but it was not an independent raw-SDK test. Both smoke scripts call `gabriel.whatever()` with the same hardcoded base, model, explicit API key, subscription-key extra header, `max_retries=1`, 90/90 timeout, `dynamic_timeout=False`, low reasoning, and background disabled. Installed GABRIEL therefore uses the same AsyncOpenAI Responses route.

Differences are intentional and diagnostic:

- one tiny synthetic prompt instead of municipality prompts;
- `web_search=False` instead of true;
- `reset_files=True` instead of false;
- one call and no project parser/candidate scoring.

Because it still goes through GABRIEL, it does not isolate raw OpenAI SDK transport from GABRIEL orchestration. A future raw-SDK-versus-GABRIEL A/B remains the cleanest component isolation.

## Sanitized environment/config findings

The no-network helper reports:

| Name/item | Current sanitized status |
|---|---|
| Project `.env` | present |
| Parent `.env` | absent |
| Ambient `HARVARD_SUBSCRIPTION_KEY` before load | absent |
| Project `.env` `HARVARD_SUBSCRIPTION_KEY` | present |
| Effective subscription-key variable after load | present |
| `OPENAI_API_KEY` before scout override | absent ambient and in selected `.env` |
| `OPENAI_BASE_URL` before scout override | absent ambient and in selected `.env` |
| `HTTP_PROXY`, `HTTPS_PROXY`, `ALL_PROXY`, `NO_PROXY` | absent ambient and in selected `.env` |
| Effective hardcoded base | `https://go.apis.huit.harvard.edu/ais-openai-direct/v2` |
| Effective path | `/ais-openai-direct/v2/responses` |

The project `.env` has a filesystem modification timestamp of 2026-06-18 16:11 EDT, predating PA, TX, MA, and both smoke tests. No value was printed or compared. This rules out an on-disk `.env` edit between Texas and MA, but not a historical exported process variable: because `load_dotenv()` does not override an existing value, a stale ambient `HARVARD_SUBSCRIPTION_KEY` would win. The retest explicitly recorded `OPENAI_API_KEY` and `OPENAI_BASE_URL` absent before override, but did not record whether `HARVARD_SUBSCRIPTION_KEY` was ambient before `.env` load.

## Ranked suspected local causes

1. **Failed runs executed without outbound-network approval in a network-restricted command sandbox.** The successful Texas command is the exact command retained in local approved-command state; the failed MA/smoke commands are not. All failures occur before an HTTP response/ID and, in detailed MA retry/smoke logs, about 1–2 seconds after each call begins. A blocked DNS/socket/TLS connection fits this perfectly. The repository does not retain historical one-time escalation metadata, so confirm against the platform execution transcript before calling this proven.
2. **Local network path changed: VPN, DNS, TLS trust, firewall, security agent, or egress intermediary.** This is the broader local transport explanation if the commands were all properly network-approved. HUIT's working-key report and the abrupt TX-to-MA transition support checking whether the failed request ever reached HUIT.
3. **Historical ambient `HARVARD_SUBSCRIPTION_KEY` overrode the unchanged project `.env`.** Mechanically possible because `override=False`; not evidenced in current state. If HUIT tested the exact local effective credential rather than merely the account's intended key, this drops sharply.
4. **Different Python environment or locally modified installed package at invocation.** Low likelihood. PA and MA logs reference the same global pyenv site-packages; global GABRIEL/OpenAI files predate all runs and are unmodified. The repo `.venv` does contain a different OpenAI minor version, but no live artifact points to its use.
5. **GABRIEL custom-proxy behavior, especially its rate-limit probe omitting the subscription extra header.** This is a real wrapper concern found in the prior audit, but actual Responses calls receive the header and the same GABRIEL version worked for PA/TX. It may add noise but does not explain the abrupt all-call failure by itself.
6. **URL/model/prompt/tool configuration.** Lowest likelihood and contradicted by direct code/history/artifact evidence. `/v2/responses`, `gpt-5.4-nano`, and serial 90/90 execution all worked; web-search-off smoke fails too.

## What is ruled out

- A change to `run_live_batch()` after PA/TX.
- A change in hardcoded base URL, request resource, header names, model default, timeout defaults, or web-search parameter construction.
- Duplicated `/v2/v2`, missing version, `/responses/responses`, or a trailing-slash join defect.
- An `OPENAI_BASE_URL` override of this function: the runner sets it and passes explicit `base_url`.
- The Massachusetts 22-column input shape: Texas used the same 22-column schema successfully.
- The row-aware/filter-contract changes as request-construction changes: they touch prompt/parser/scoring only.
- Web search as a necessary trigger: both no-search synthetic calls fail identically.
- Excess concurrency: all broken runs use `n_parallels=1`.
- Ordinary 90-second response timeout: failed connection attempts terminate well before 90 seconds.
- A parser bug: there is no response text to parse.

## What remains unknown

- Whether each failed command was actually launched with outbound-network escalation/approval or only authorized at the research-task level.
- The nested OpenAI/httpx exception cause (`DNS`, `ConnectError`, TLS verification, connection reset, proxy refusal, etc.); GABRIEL reduced it to `Connection error.`.
- Whether HUIT received any failed request. A server-side “no matching request” finding would strongly confirm a local egress problem.
- Whether a historical ambient `HARVARD_SUBSCRIPTION_KEY` was present before `.env` load.
- The exact interpreter executable and package hashes for TX/MA at invocation; current files/log paths strongly suggest the same global environment, but the run metadata did not record them.
- Whether a raw `AsyncOpenAI.responses.create()` call would fail in the same explicitly network-approved context; both prior smoke tests still used GABRIEL.

## Recommended next diagnostic

Do not change the scout runtime, base URL, model, or request family based on this evidence.

1. First inspect the platform's historical command-execution audit—not Git or remotes—to determine whether the MA primary/retries and both smoke tests had outbound network escalation. Compare that field with the Texas invocation. This is the highest-value, zero-API diagnostic.
2. Ask HUIT whether requests with the recorded failure timestamps reached its edge. Use Texas `2026-07-16 16:45:51–16:46:53 EDT`, MA `2026-07-16 18:32–18:36 EDT`, diagnosis `2026-07-16 19:01:04 EDT`, and retest `2026-07-17 14:11:26 EDT`. Do not send a credential value.
3. If a future diagnostic is separately authorized, make the execution context explicit: run outside the restricted network sandbox. Start with non-secret DNS/TCP/TLS reachability to the proxy origin, then one raw OpenAI Responses no-search request, then the equivalent GABRIEL no-search request only if needed. Capture sanitized exception class and nested cause, effective Python executable, and package versions/hashes.
4. Interpret that A/B mechanically: both raw and GABRIEL fail before HTTP → local egress/TLS/DNS; raw succeeds but GABRIEL fails → wrapper/client construction; both reach HUIT and receive a status → route/auth/backend diagnosis from the status; HUIT sees no request → local path confirmed.
5. Only after the synthetic path succeeds, and only with separate authorization, consider a fresh MA research run. Never reuse the failed output directory or treat failed rows as source absence.

## Changes made by this audit

- Added this comparison report.
- Updated `PROGRESS.md` and `docs/analysis/chatgpt_handoff_latest.md`.
- Did not modify `scripts/gabriel_state_source_scout.py`, `scripts/diagnose_gabriel_config.py`, dependency files, canonical data, coverage data, or corpus files.
- Made no live/model/API call and ran no scout.

## Primary evidence paths

- Production runner: `scripts/gabriel_state_source_scout.py`
- Sanitized helper/output: `scripts/diagnose_gabriel_config.py`; `tmp/gabriel_url_baseurl_audit_2026-07-17/sanitized_config_output.txt`
- PA batch summary and artifacts: `docs/analysis/gabriel_state_source_scout_pa_batch25_summary_2026-07-15.md`; `tmp/gabriel_state_source_scout/PA/2026-07-15_batch25_main/`; `tmp/gabriel_state_source_scout/PA/2026-07-15_batch25_retry/`
- PA tuning methodology/results: `docs/analysis/gabriel_state_source_scout_rate_limit_tuning_summary_2026-07-15.md`; `docs/analysis/gabriel_state_source_scout_tuning_matrix_summary_2026-07-15.md`; `docs/analysis/gabriel_state_source_scout_timeout_test_summary_2026-07-15.md`
- Texas review/artifacts: `docs/analysis/national_batch01_tx_live_scout_review_2026-07-16.md`; `docs/analysis/national_batch01_tx_live_scout_candidates_2026-07-16.csv`; `tmp/gabriel_state_source_scout/TX/national_batch01_tx_live_2026-07-16/`
- Massachusetts review/artifacts: `docs/analysis/national_batch01_ma_live_scout_review_2026-07-16.md`; `tmp/gabriel_state_source_scout/MA/national_batch01_ma_live_2026-07-16/`; its `_retry_failed/` and `_remaining_first_attempt/` siblings
- Synthetic diagnosis/retest: `tmp/gabriel_proxy_connection_diagnosis_2026-07-16/`; `tmp/gabriel_proxy_connection_retest_2026-07-17/`
- Prior URL audit: `docs/analysis/gabriel_url_baseurl_audit_2026-07-17.md`

## Limitations

This is intentionally a no-live audit. It can establish code identity, local URL resolution, current sanitized configuration, artifact outcomes, installed-file history, and the likely importance of the execution sandbox. It cannot retrospectively recover an unsaved tool escalation flag, observe the swallowed network exception cause, or prove whether HUIT received the requests. Those are the precise remaining diagnostics.
