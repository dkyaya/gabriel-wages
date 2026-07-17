# HUIT-shareable GABRIEL Code Packet

Date: 2026-07-17

## Purpose

HUIT asked to see the actual code returning the current GABRIEL error `['Connection error.']`. This packet provides the smallest useful implementation and sanitized returned artifacts for the one-prompt synthetic no-search diagnostic. It is a packaging/documentation task only; no GABRIEL/model/API call, scout, source verification, ingestion, codification, or canonical data/corpus operation occurred.

## Included

The packet ZIP contains only:

- the exact diagnostic script run: `gabriel_proxy_smoke_test.py`;
- the actual project scout runner: `scripts/gabriel_state_source_scout.py`;
- the runner's no-network prompt/outcome helper test: `scripts/test_gabriel_state_source_scout_prompt.py`;
- a README and short email-ready error summary;
- sanitized smoke metadata and console output; and
- the raw one-row GABRIEL output, which contains no secret values.

The two copied code files preserve their project-relative `scripts/` paths. The smoke script preserves its retest-relative path. No other project-local Python module is directly imported by the scout runner for the proxy call path; its other dependencies are external packages.

## Excluded for security and scope

The packet deliberately excludes `.env`, all credential/subscription-key values, tokens, cookies, local key files, shell history, cache files, the full repository, corpus/data files, research inputs/results, and all unrelated documentation. The copied metadata and console log are named with `_redacted` because absolute local filesystem/cache paths were removed. No credential value occurred in the originals or was included.

## Sending to HUIT

Send the ZIP as an attachment with the `ERROR_SUMMARY.txt` content in the email body. The README identifies the exact `gabriel.whatever(...)` call path and records only configuration presence/absence—not secret values. Ask HUIT to trace the listed endpoint/model request and check proxy routing/transport, proxy-side subscription-key authentication, and upstream model availability; the client receives no HTTP/provider-specific error.

Exact ZIP path:

`tmp/gabriel_huit_code_packet_2026-07-17.zip`
