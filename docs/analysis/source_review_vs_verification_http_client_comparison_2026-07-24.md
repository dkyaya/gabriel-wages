# Source-Review versus URL-Verification HTTP Client Comparison

Date: 2026-07-24

## Identity-controlled comparison

The comparison is not between unrelated samples. All 150 Pilot 1
`candidate_queue_row_id` values match cumulative URL-routing ledger rows:

- prior verification status `reachable_pdf_or_document`: 150;
- prior HTTP status 200: 150;
- prior observed base content type `application/pdf`: 150;
- source-review `source_locator` equals the routing ledger `final_url`: 150;
- source-review `final_url` equals the routing ledger `final_url`: 150;
- redirected during verification: 22;
- no redirect during verification: 128.

The live source-review result on those same locators was 149 connection errors,
one forbidden response, and zero retained bodies.

## Pre-fix implementation comparison

| Behavior | Working URL verifier | Pilot 1 source reviewer before fix | Assessment |
|---|---|---|---|
| Client library | `httpx.AsyncClient` | custom synchronous `urllib.request` opener | Material mismatch; leading suspect |
| Concurrency | asyncio semaphore, eight per lane in routing | thread pool, four per lane | Not an explanation for near-universal connection failure |
| Environment proxy inheritance | `trust_env=False` | `ProxyHandler({})` | Both disabled environment proxies |
| Timeout configuration | `httpx.Timeout` with total/connect/read/write/pool values | opener connect timeout plus socket mutation and manual elapsed check | Different implementation and exception behavior |
| Redirects | `follow_redirects=True`, maximum five | custom redirect handler, maximum five | Same policy; different implementation |
| TLS/certificates | `httpx` defaults | `ssl.create_default_context()` via `urllib` | Both verify TLS, but use different stacks and error surfaces |
| Method | streamed GET | streamed/chunked GET | No HEAD/GET mismatch |
| User agent | project verifier user agent | project source-review user agent | Both nonblank and explicit |
| Accept header | `*/*` | document-oriented list plus low-priority wildcard | Unlikely to explain connection establishment failures |
| Live URL field | verifier `candidate_url`; this sample's result recorded as `final_url` | first nonblank of `source_locator`, `final_url`, `candidate_url` | Input audit proves source review used the prior raw final URL |
| URL sanitization | after response, for verifier artifacts/errors as applicable | after response for recorded access URL | Sanitized display URL was not used for the request |
| Read strategy | `response.aiter_bytes()` to the cap | repeated `response.read()` chunks to the cap | Both bounded, but different transport stack |
| Byte cap | 10 MiB in routing | 25 MiB in review | Higher review cap cannot cause pre-response connection errors |
| Retry behavior | none | none | Equivalent |
| Artifact write | response metadata; no full document | intended lane-local body plus response metadata | The local artifact path is reached only after HTTP response handling |
| Exception detail | sanitized `httpx` class/message | typed category collapsed to generic `connection_error` | Source review discarded the evidence needed to diagnose 149 failures |

## Findings

The URL fields are not the defect: all 150 `source_locator` values are raw
absolute HTTPS URLs and equal the verifier's successful recorded final URLs.
The source reviewer did not use `sanitize_url()` until after its client
returned. It also performed GET, not HEAD, and its artifact writer could not
have converted a pre-response exception into a connection error because the
connection category was raised inside the transport.

Proxy behavior was equivalent in policy. The verifier used
`trust_env=False`; the source reviewer built an empty `ProxyHandler`. Enabling
environment proxies by default would therefore diverge from the proven
verifier and is not supported by the available evidence.

The strongest code-level cause is the unvalidated switch from the successful
`httpx` transport to a separate custom `urllib` transport. The 149 failures
occurred across 94 hosts with a median terminal time below one second, while
the identical URLs previously produced HTTP 200 through `httpx`. The original
source-review ledger retained only the generic category, so the precise
low-level cause—such as DNS/socket behavior or a protocol-stack incompatibility—
cannot be recovered from that attempt.

## Patch

`scripts/source_review_sources.py` now uses a bounded synchronous
`httpx.Client` path aligned with the verifier:

- explicit connect/read/write/pool timeout configuration;
- streamed GET;
- redirect following with a maximum of five;
- TLS verification through the same client family;
- bounded decompressed reads and the existing 25 MiB ceiling;
- `trust_env=False` by default;
- optional `--trust-env-proxy` opt-in, never implicit;
- the raw locator is used for access and only the recorded final URL is
  sanitized; and
- a new `transport_exception_type` field retains only a sanitized exception
  class token while response messages remain generic.

No retry, OCR, PDF parsing, content sample, corpus write, ingestion,
codification, wage extraction, or rating-boundary relaxation was added.

## Confidence and proof gate

The client-stack mismatch is a high-confidence likely cause, not yet a proven
complete explanation. Seventeen offline tests, including an
`httpx.MockTransport` end-to-end artifact success, pass. A single diverse
ten-row diagnostic probe is the bounded empirical gate. Material HTTP
responses or artifacts from that probe would confirm that source access now
works; continued near-universal connection failure would instead require an
environment-level diagnosis and an immediate stop.
