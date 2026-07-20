# GABRIEL URL / `base_url` No-Live Audit

Date: 2026-07-17 (audit performed 2026-07-20)
Scope: local code, installed-client source, local Git history, and preserved artifacts only; no GABRIEL/model/API call, research scout, source retrieval, ingestion, codification, remote inspection, or push

## Plain-English summary

No local `base_url` or duplicated-path bug was found in the code that ran the successful Texas scout and later failed for Massachusetts. The scout hardcodes the Harvard proxy base as:

`https://go.apis.huit.harvard.edu/ais-openai-direct/v2`

The installed GABRIEL package routes ordinary text and web-search requests through the OpenAI **Responses API**, and the installed OpenAI SDK appends `/responses`. The exact effective request URL is therefore:

`https://go.apis.huit.harvard.edu/ais-openai-direct/v2/responses`

It is not `/v2/v2`, does not omit `v2`, does not contain `/responses/responses`, and is not malformed by a trailing slash. `OPENAI_BASE_URL` is absent from the ambient process and project `.env`; more importantly, `run_live_batch()` overwrites it temporarily and also passes the hardcoded `base_url` explicitly, so a local `OPENAI_BASE_URL` value could not silently redirect this call even if one existed.

The exact `run_live_batch()` body is byte-for-byte unchanged from the code at commit `31189a5df9f0a8493f612de9c5a9d0191ac70a2f`, the commit from which the successful Texas live run was executed. Both versions hash to `65e6634a36f822042e00f781b475ddd083b5ce9feffe861f0e08f22ca9edfe8f` when the function block is extracted. Later changes affected prompt/scoring fields and row-level success metadata, not URL construction, model selection, client construction, headers, or request routing.

The strongest remaining explanation is therefore an external or server-side change/failure affecting the already-established `POST …/v2/responses` route, proxy authentication/routing, the upstream `gpt-5.4-nano` backend, or Responses/web-search-tool support. The same local request family and settings succeeded for all three Texas rows at 16:45 EDT and failed for all Massachusetts rows at 18:32 EDT on 2026-07-16. The later no-search synthetic tests also failed, so web search is not required to reproduce the failure.

One real but secondary client concern was found: GABRIEL 1.1.8 performs a preliminary rate-limit probe against `{base_url}/responses` and then `{base_url}/chat/completions` using `Authorization` but not the supplied `Ocp-Apim-Subscription-Key` extra header. That probe silently tolerates failure; the actual model request does receive the subscription header. This omission should be fixed upstream or bypassed for a proxy, but it does not explain why the actual request path worked for Texas and then uniformly stopped working without a local code change.

## Starting state and relay integrity

- Latest local commit before work: `4a33388083ae5818b779c953e9aaaa3404e44be7` (`Package GABRIEL proxy code for HUIT`).
- Working tree before work: only pre-existing untracked `.claude/`; it was not touched.
- Source-of-truth relay: `tmp/gabriel_huit_code_packet_2026-07-17_relay_4a33388.zip`.
- ZIP inventory: 23 files and 5 directory entries.
- Relay/workspace reconciliation before edits: all 23 carried files matched the corresponding workspace files by SHA-256; no file was missing or different.
- No Git remote command was run. Only local `git status`, `git log`, `git show`, and `git diff` were used.

## Exact live-call code path

The production path is:

1. `main()` builds prompts and calls `run_live_batch()` in `scripts/gabriel_state_source_scout.py` (current lines 1589-1600).
2. `run_live_batch()` checks `ROOT/.env` first, then `ROOT.parent/.env`, and calls `load_dotenv()` on the first existing file (lines 1361-1366). `python-dotenv` defaults to `override=False`.
3. It reads `HARVARD_SUBSCRIPTION_KEY` and refuses the live call if absent (lines 1368-1371).
4. It imports GABRIEL, saves the pre-existing `OPENAI_API_KEY` and `OPENAI_BASE_URL`, then temporarily assigns both to the Harvard credential/base configuration (lines 1373-1386).
5. It constructs `base_kwargs` and passes them to `gabriel.whatever(...)` (lines 1393-1418):
   - `model=<CLI/default>`; default `gpt-5.4-nano`;
   - `web_search=True`;
   - `search_context_size=<CLI/default>`; default `low`;
   - `reasoning_effort="low"`;
   - `api_key=<HARVARD_SUBSCRIPTION_KEY>`;
   - `base_url=HARVARD_PROXY_BASE_URL`;
   - `extra_headers={"Ocp-Apim-Subscription-Key": <HARVARD_SUBSCRIPTION_KEY>}`;
   - `max_retries=1`;
   - `timeout=90`, `max_timeout=90`, `dynamic_timeout=False` at defaults;
   - `background_mode=False`.
6. Installed GABRIEL 1.1.8 receives those keyword arguments through `gabriel.api.whatever()` → `gabriel.tasks.whatever.Whatever.run()` → `gabriel.utils.openai_utils.get_all_responses()` → `get_response()`.
7. `get_all_responses()` resolves `base_url = base_url or os.getenv("OPENAI_BASE_URL")`, but the explicit function argument is truthy and wins. It passes that URL into `get_response()` and `_get_client()`.
8. `_get_client()` constructs and caches `openai.AsyncOpenAI(base_url=url)`. The cache key is the URL. The API key is already present in `OPENAI_API_KEY`; the per-request subscription key is carried in `extra_headers`.
9. For non-audio prompts, `get_response()` builds a Responses API payload. With this scout it adds `tools=[{"type":"web_search","search_context_size":"low"}]`, includes web-search sources, and calls `client_async.responses.create(...)`.
10. OpenAI Python SDK 2.41.0 defines `responses.create()` as `POST "/responses"`. Its URL joiner normalizes the client base to a trailing slash and appends the relative resource path. The offline SDK join therefore resolves to `https://go.apis.huit.harvard.edu/ais-openai-direct/v2/responses`.
11. On a response, GABRIEL converts the SDK response to text, extracts web-search source information and usage, and returns a dataframe. The scout writes `raw_outputs.csv`, then `parse_response_to_candidates()` extracts a balanced JSON object and maps it to candidate rows. The current connection failures occur before that project parser: the preserved rows have no response text or response ID.
12. In `finally`, `run_live_batch()` restores the process's prior `OPENAI_API_KEY` and `OPENAI_BASE_URL` values (lines 1454-1462).

## Sanitized effective configuration

The no-network helper output is preserved at `tmp/gabriel_url_baseurl_audit_2026-07-17/sanitized_config_output.txt`.

| Item | Sanitized finding |
|---|---|
| Project `.env` | present |
| Parent-of-project `.env` | absent |
| Selected `.env` | project root |
| Ambient `HARVARD_SUBSCRIPTION_KEY` before load | absent |
| Project `.env` `HARVARD_SUBSCRIPTION_KEY` | present |
| Effective `HARVARD_SUBSCRIPTION_KEY` after load | present |
| Ambient/project/effective `OPENAI_API_KEY` before scout override | absent / absent / absent |
| Ambient/project/effective `OPENAI_BASE_URL` before scout override | absent / absent / absent |
| `HTTP_PROXY`, `HTTPS_PROXY`, `ALL_PROXY`, `NO_PROXY` | absent in ambient process and selected `.env` |
| Hardcoded/effective `base_url` | `https://go.apis.huit.harvard.edu/ais-openai-direct/v2` |
| SDK-normalized base | `https://go.apis.huit.harvard.edu/ais-openai-direct/v2/` |
| Actual request family | OpenAI Responses API |
| SDK-appended resource | `/responses` |
| Effective model request URL | `https://go.apis.huit.harvard.edu/ais-openai-direct/v2/responses` |
| Model | `gpt-5.4-nano` |
| Timeout / maximum | 90 / 90 seconds |
| Dynamic timeout | false at defaults |
| Web-search tool | enabled in the research scout; low context |
| Synthetic retest web search | disabled, yet it failed identically |
| Authentication header names | `Authorization`; `Ocp-Apim-Subscription-Key` |
| GABRIEL / OpenAI SDK | 1.1.8 / 2.41.0 |

No credential value, token, cookie, or general environment dump was printed or saved.

## `base_url` and environment precedence

`base_url` is **hardcoded**, not sourced from `.env`:

```python
HARVARD_PROXY_BASE_URL = "https://go.apis.huit.harvard.edu/ais-openai-direct/v2"
```

The `.env` search exists to obtain `HARVARD_SUBSCRIPTION_KEY`. Immediately before the GABRIEL call, the runner does both of the following:

```python
os.environ["OPENAI_BASE_URL"] = HARVARD_PROXY_BASE_URL
...
base_url=HARVARD_PROXY_BASE_URL
```

The explicit `base_url` has precedence inside GABRIEL (`base_url or os.getenv("OPENAI_BASE_URL")`). Thus:

- `OPENAI_BASE_URL` cannot redirect this `run_live_batch()` invocation;
- another script-specific base URL environment variable does not exist;
- the selected project `.env` contains no `OPENAI_BASE_URL` anyway;
- the packet README's environment-status description agrees with the local `.env`/process state;
- a pre-exported `HARVARD_SUBSCRIPTION_KEY` could override the `.env` credential because `load_dotenv()` uses `override=False`, but the audited ambient process did not have that variable set.

## URL/path bug checklist

| Candidate bug | Finding | Evidence |
|---|---|---|
| Duplicated version path (`/v2/v2`) | ruled out | Offline SDK resolution is `/ais-openai-direct/v2/responses`; no adjacent duplicate component. |
| Missing version path | ruled out locally | The hardcoded base contains exactly one `v2`. |
| Base already contains `/responses`, SDK appends it again | ruled out | Base ends in `/v2`, not `/responses`; final path contains one `/responses`. |
| Base already contains `/chat/completions` | ruled out | Base ends in `/v2`. |
| Trailing slash malformed the URL | ruled out | Source constant has no trailing slash; SDK normalizes to one slash before appending. |
| `OPENAI_BASE_URL` silently overrides intended endpoint | ruled out for this function | Ambient and `.env` variable absent; function also overwrites the env var and passes explicit `base_url`. |
| Base includes too much endpoint path for the SDK | not observed | It contains proxy route plus version only; SDK correctly appends `/responses`. |
| Proxy expects `/v1` while code uses `/v2` | not supported by local evidence | All established project proxy clients use `/ais-openai-direct/v2`; raw `/responses` and GABRIEL `/responses` tests succeeded on 2026-07-01; Texas succeeded on 2026-07-16. HUIT should nevertheless confirm the current server contract. |
| Proxy expects chat completions, not Responses | unlikely historically, still worth server-side confirmation | Direct chat calls are used elsewhere, but the archived 2026-07-01 raw Responses web-search and native GABRIEL web-search tests both succeeded, and Texas later succeeded through native GABRIEL. |
| HUIT route or Responses compatibility changed server-side | plausible | Identical local function/config succeeded for Texas and failed later for MA plus two no-search smoke tests. |
| GABRIEL rate-limit probe omits subscription header | confirmed secondary concern | `_get_rate_limit_headers()` constructs only `Authorization` and `Content-Type`; actual `responses.create()` receives the supplied `extra_headers`. |

## Comparison with the successful Texas run

The successful run is `tx_2026-07-16_164549` under `tmp/gabriel_state_source_scout/TX/national_batch01_tx_live_2026-07-16/`.

- Execution base commit: `31189a5df9f0a8493f612de9c5a9d0191ac70a2f` (`Make Texas scout prompt row-aware`). This is recorded as the starting commit in the progress/handoff entry for the live run.
- Artifact commit: `48241178f7f2a90d1fb873bc82ec3258e33f35f0` (`Record Texas live scout candidates`).
- Current pre-audit commit: `4a33388083ae5818b779c953e9aaaa3404e44be7`.
- `run_live_batch()` extracted-function SHA-256 at execution commit: `65e6634a36f822042e00f781b475ddd083b5ce9feffe861f0e08f22ca9edfe8f`.
- Current extracted-function SHA-256 before this audit's edits: the same hash.
- Installed GABRIEL `api.py`, `tasks/whatever.py`, `utils/openai_utils.py`, and `_version.py`, plus OpenAI `_base_client.py`, all have local modification timestamps of 2026-06-08, predating both Texas and Massachusetts. There is no local filesystem evidence of an installed-client change between the runs.

Changes after the Texas execution commit are:

- `f24771f...`: prompt/filtering contract, candidate schema, normalization, and scoring changes;
- `6c7c766...`: row-level live-outcome metadata and its no-network test;
- intervening data/review/package commits: artifacts and documentation.

None changes `run_live_batch()`, `HARVARD_PROXY_BASE_URL`, model default, OpenAI/GABRIEL initialization, headers, timeouts, web-search argument construction, or request family/path.

### Artifact comparison

| Evidence | Texas success | Massachusetts failure |
|---|---:|---:|
| Model | `gpt-5.4-nano` | `gpt-5.4-nano` |
| Search context | low | low |
| Parallelism | 1 | 1 |
| Timeout / maximum | 90 / 90 | 90 / 90 |
| Inter-prompt delay | 15 sec | 15 sec |
| Rows | 3 | 8 primary |
| Successful rows | 3 | 0 |
| Nonempty responses | 3 | 0 |
| Rows with response IDs | 3 | 0 |
| Connection-error rows | 0 | 8 |
| Input / reasoning / output tokens | 95,158 / 5,521 / 7,002 | 6,414 / 0 / 0 |

The 2026-07-17 synthetic retest used the same base/model/header/client route with `web_search=False` and still produced one empty `['Connection error.']` row with no response ID. This substantially lowers the likelihood that the web-search tool payload is the root cause.

## Suspected failure points, ranked

1. **Harvard proxy route, proxy authentication, or upstream backend failure after the Texas run.** This best fits the abrupt same-day transition from 3/3 success to uniform connection errors without a local call-path change, and the repeated no-search synthetic failures. HUIT should trace the exact `POST /ais-openai-direct/v2/responses` route and report the proxy/upstream status category.
2. **Server-side contract or routing change for the Responses endpoint, model, or tool-capable backend.** Local construction is internally correct, but only HUIT can confirm that `/v2/responses` remains the supported OpenAI-compatible route and that `gpt-5.4-nano` is still routed. The no-search failure shows that hosted web search is not necessary to trigger the incident.
3. **Credential rejected or no longer mapped correctly by the proxy.** The variable is present, passed as both Bearer API key and `Ocp-Apim-Subscription-Key`, and was not changed by local base-URL logic. The generic `APIConnectionError` does not surface an HTTP status, so an intermediary closing the connection could hide an authentication or gateway-policy rejection.
4. **GABRIEL's headerless rate-limit probe causing avoidable proxy errors or interference.** This is a concrete implementation defect for custom subscription-header proxies, but the actual request still has the correct header and the same package previously succeeded. It is a secondary cleanup/diagnostic item rather than the leading root cause.
5. **Local `base_url`/path or environment override bug.** Low likelihood and specifically contradicted by the exact function hash, sanitized environment state, offline SDK URL resolution, July 1 raw/native Responses successes, and Texas success.

## Recommended next diagnostic or fix

Do not change `/v2` to `/v1`, switch to chat completions, or remove `/responses` based on the current evidence. Those would be speculative runtime changes that contradict known successful runs.

The next move should be:

1. Give HUIT the exact effective route and request family: `POST https://go.apis.huit.harvard.edu/ais-openai-direct/v2/responses`, model `gpt-5.4-nano`, header names `Authorization` and `Ocp-Apim-Subscription-Key`, and (for the scout) a Responses payload with `tools=[{"type":"web_search","search_context_size":"low"}]`.
2. Ask HUIT to compare server/proxy logs around Texas `2026-07-16 16:45-16:47 EDT` with the Massachusetts failure beginning around `18:32 EDT` and the synthetic retest at `2026-07-17 14:11 EDT`. Ask specifically whether the request arrived, which route handled it, and whether the failure was subscription authentication, proxy routing/TLS, backend/model availability, or an upstream response reset.
3. Ask HUIT to state the currently supported base and resource contract explicitly: whether clients should use base `…/v2` plus resource `/responses`, base `…/v2` plus `/chat/completions`, or a different version. The local client demonstrably appends `/responses`.
4. In GABRIEL upstream, change `_get_rate_limit_headers()` to accept/forward caller `extra_headers`, or disable that probe for custom proxy bases. Do not patch the installed package ad hoc in this repository.
5. Only after HUIT confirms the expected route and a future live test is separately authorized, use a tiny direct Responses no-search request as a go/no-go check, followed—only if needed—by the equivalent GABRIEL no-search call. That A/B isolates raw SDK/proxy behavior from GABRIEL orchestration. No such call was made in this audit.

## Code changes made by this audit

- Added `scripts/diagnose_gabriel_config.py`, a no-network helper that reports fixed environment-variable names with present/absent status, the hardcoded/effective URL, locally resolved SDK routes, model/timeout/tool family, and duplicate-path checks. It refuses to emit output if a loaded credential value appears in the rendered text.
- Added this report.
- Did **not** modify `scripts/gabriel_state_source_scout.py` or any live runtime behavior.
- Did **not** edit `data/contracts.csv`, `data/city_coverage.csv`, or any corpus file.

## Evidence paths

- Production runner: `scripts/gabriel_state_source_scout.py`
- Safe helper output: `tmp/gabriel_url_baseurl_audit_2026-07-17/sanitized_config_output.txt`
- Texas metadata/logs: `tmp/gabriel_state_source_scout/TX/national_batch01_tx_live_2026-07-16/`
- Massachusetts metadata/logs: `tmp/gabriel_state_source_scout/MA/national_batch01_ma_live_2026-07-16/`
- Synthetic retest: `tmp/gabriel_proxy_connection_retest_2026-07-17/`
- Prior diagnosis/retest notes: `docs/analysis/gabriel_proxy_connection_diagnosis_2026-07-16.md`, `docs/analysis/gabriel_proxy_connection_retest_2026-07-17.md`
- Archived successful direct/native route test: `docs/archive/legacy_gabriel_pilot_2026-06/gabriel_proxy_web_connectivity_diagnostic_2026-07-01.md`
- Source-of-truth relay: `tmp/gabriel_huit_code_packet_2026-07-17_relay_4a33388.zip`

## Limitations

This was intentionally a no-live audit. It proves the local URL that the installed SDK would construct and shows the relevant code did not change, but it cannot observe the actual failed HTTP exchange, status code, TLS/proxy reset, or HUIT server logs. It therefore cannot distinguish among proxy routing, proxy authentication, backend/model availability, and server-side endpoint-policy changes without HUIT evidence or a later separately authorized A/B request.
