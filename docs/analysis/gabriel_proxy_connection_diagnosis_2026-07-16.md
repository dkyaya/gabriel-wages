# GABRIEL / Harvard Proxy Connection Diagnosis

Date: 2026-07-16  
Scope: infrastructure diagnosis only; no research scout, source verification, ingestion, codification, or claim use

## Result in plain English

The Massachusetts scout failed before GABRIEL received a usable model response. The same failure occurred in a one-prompt synthetic smoke test that had no municipality, labor-source, or web-search content. This rules out the Massachusetts prompts, target municipalities, source-search behavior, and parser as the cause.

The best-supported diagnosis is an unresolved external transport/proxy/API-path failure at the time of the Massachusetts calls. Local imports work, the runner's `.env` loading path supplies a credential to the smoke test without exposing it, and the successful Texas scout used the same model and relevant runner settings earlier that day. GABRIEL records only the generic `Connection error.` string, so this evidence cannot distinguish a transient Harvard proxy outage/network path failure from an upstream proxy authentication/backend/model availability issue. It does not support a source-absence inference for any Massachusetts municipality.

## Massachusetts evidence

The primary run (`ma_2026-07-16_183246`) attempted all eight locked MA rows. It returned 8 rows, but none contained a model response:

- Primary attempts: 8
- Bounded retries: 8 total, split into a 3-row and a 5-row retry run
- Total charged failed calls: 16
- Failure ledger type: `empty_response_no_response_id` for every row
- GABRIEL row error: `['Connection error.']` for every row
- Response IDs: none
- Nonempty responses: none
- Output tokens: none
- Web-search sources: none
- Primary cost/tokens: `$0.0012828`; 6,414 input, 0 reasoning, 0 output
- Retry cost/tokens: `$0.0004592` + `$0.0008236`; 6,414 additional input, 0 reasoning, 0 output
- Combined recorded cost/tokens: `$0.0025656`; 12,828 input, 0 reasoning, 0 output

The runner records `live_succeeded=true` when `gabriel.whatever` returns a dataframe, even if all rows inside it failed. That is process completion, not model-response success. The runner now also writes backward-compatible row-level outcome metadata for future runs: `live_process_completed`, `n_gabriel_successful_rows`, `n_nonempty_response_rows`, and `model_response_succeeded`.

## Why this is not prompt, parser, or source behavior

The primary MA rows were accepted into GABRIEL's returned dataframe and charged small input-token amounts, but had no response text, response ID, web result, reasoning token, or output token. A parser failure would require model response text to parse; there was none. A prompt or municipal-target problem would still ordinarily result in a model response, empty candidate list, refusal, or structured error—not a uniform client-side `Connection error.` before any response ID.

The completed bounded retries used the same serial settings and failed uniformly across all eight municipalities. This pattern is inconsistent with a particular city, unit target, or prompt length.

## Comparison with the successful Texas scout

The successful Texas live run (`tx_2026-07-16_164549`) used the same relevant configuration:

| Setting | Texas success | Massachusetts failure |
|---|---|---|
| Model | `gpt-5.4-nano` | `gpt-5.4-nano` |
| Prompt mode | `minimal` | `minimal` |
| Search context | `low` | `low` |
| Parallelism | 1 | 1 |
| Sleep between prompts | 15 seconds | 15 seconds |
| Timeout / max timeout | 90 / 90 seconds | 90 / 90 seconds |
| Parseability | 3 of 3 | 0 of 8 primary; 0 of 8 retries |
| Response IDs/output | present / 7,002 output tokens | absent / 0 output tokens |
| Error logs | no failed rows | `Connection error.` on every row |

Texas produced 3 parseable responses, 6 quarantined scout candidates, and 95,158 input / 5,521 reasoning / 7,002 output tokens. The same configuration working earlier and the no-search smoke test failing later make a prompt or runner-flag regression unlikely.

## Non-live diagnostics

- The runner has no built-in healthcheck, synthetic ping, or connectivity-test CLI. Its non-live modes are dry-run, run comparison, and coverage building.
- `python scripts/gabriel_state_source_scout.py --help` shows no healthcheck option.
- `gabriel`, `dotenv`, and `pandas` import successfully.
- The project-local `.env` exists. The subscription key is not pre-exported in the shell, which is expected: the runner loads it only inside its live path. The smoke test confirmed that a credential became available after that local load without printing its value.
- The runner's configured Harvard proxy endpoint is present in source as `https://go.apis.huit.harvard.edu/ais-openai-direct/v2`.
- No remote or credential content was inspected, printed, or written.

## Authorized synthetic smoke test

Because no built-in healthcheck exists, one infrastructure-only GABRIEL smoke test was run. It used one synthetic JSON-only prompt, one parallel worker, no web search, low search-context setting, model `gpt-5.4-nano`, and the same proxy/key-loading path as the runner. It did not name a municipality or search for sources.

Result: failed. The returned row had 13 input tokens and a `$0.0000026` charge, but empty response text, no response ID, no output/reasoning token, and `['Connection error.']`. The preserved artifacts are under `tmp/gabriel_proxy_connection_diagnosis_2026-07-16/`.

This confirms that the problem persists for a minimal, no-search proxy request. It is not safe to resume research scouting now.

## What to do next

1. Treat this as an external connectivity/proxy-path incident until the Harvard API/proxy service or local network path can be checked by the appropriate service owner. The generic GABRIEL error does not safely establish whether the subcause is transient availability, authentication, or upstream model availability.
2. Do not rerun the Massachusetts scout, another state slice, source verification, ingestion, codification, or claim work yet.
3. After connectivity is restored, run a new one-prompt synthetic smoke test first. A successful smoke test should show a nonempty response and a response ID. It should not automatically resume research work.
4. Only after separate authorization, use a fresh output directory for the exact MA rerun:

```bash
python scripts/gabriel_state_source_scout.py \
  --state MA \
  --municipalities-csv docs/analysis/national_batch01_ma_scout_input_2026-07-16.csv \
  --output-dir tmp/gabriel_state_source_scout/MA/national_batch01_ma_live_rerun_2026-07-16 \
  --prompt-mode minimal \
  --max-prompts 8 \
  --n-parallels 1 \
  --sleep-between-prompts 15 \
  --search-context-size low \
  --live
```

That future rerun must remain scout-stage only, must not treat the earlier failure as source absence, and must preserve its own raw, parsed, failure, and cost artifacts.
