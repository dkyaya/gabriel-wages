# Future Coordinator Prompt — Source-Review Pilot 1 Bounded HTTPX Retry

Use only under separate explicit authorization to reopen the locked 150 Pilot
1 source locators. This prompt is not authorization by itself.

Work only in the main coordinator repository. Do not inspect remotes or push.

## Objective

Retry exactly the two locked 75-row inputs for
`SOURCE-REVIEW-PILOT1-150-2026-07-24` with the verifier-compatible `httpx`
source-review client. Preserve the original failed attempt as immutable
history and stop before any durable source-review merge.

Require ancestry from the connection-diagnosis commit and read:

- `source_review_pilot1_connection_failure_diagnostic_result_2026-07-24.md`;
- `source_review_vs_verification_http_client_comparison_2026-07-24.md`;
- `source_review_pilot1_diagnostic_probe_plan_2026-07-24.md`; and
- the locked pilot manifest, input audits, and two input CSVs.

Recompute and require:

- Lane 1: 75 rows,
  `0253cba7ecf358e16679f64273466c239e296caf214e44a110813eeebfec6de3`;
- Lane 2: 75 rows,
  `a5baa87593057a49c0b1e9adfff40051725ede45618c6f0d58f90f40b2630b6e`;
- 150 unique source-review and candidate-queue identities; and
- no identities outside the locked pilot.

## Gates

Run the offline/mock suite and fresh dry runs before live access. Require
10/10 preserved diagnostic evidence: nine hashed PDFs, one forbidden, and
zero connection errors. Confirm the default client is
`httpx_verifier_compatible` with `trust_env_proxy = false`.

Refuse to reuse or overwrite:

- `lane_1_live_attempt1`;
- `lane_2_live_attempt1`; or
- `diagnostic_probe_live_attempt1`.

Use fresh outputs:

- `lane_1_live_attempt2_httpx`;
- `lane_2_live_attempt2_httpx`.

## Bounded live settings

Run exactly two lanes, 75 rows each:

- review mode: `source_rating_live`;
- download mode: `bounded`;
- explicit `--allow-live-content-access`;
- concurrency: 4 per lane;
- total/connect/read timeouts: 30 / 8 / 20 seconds;
- maximum redirects: 5;
- maximum bytes: 26,214,400;
- content samples: off;
- environment proxy inheritance: off; do not pass `--trust-env-proxy`;
- lane-local `candidate_artifacts/`;
- no PDF parse, OCR, extraction, corpus write, ingestion, or codification.

Launch Lane 2 only after Lane 1 establishes its checkpointed ledger, summary,
timing, and artifact directory. Do not run a third lane. Do not retry failed
rows again in this task.

## Audit and stop

After both lanes terminate, audit the fresh retry outputs. Compare them with
the original attempt and the ten-row diagnostic:

- terminal status and access distributions;
- content artifacts, hashes, sizes, and observed types;
- artifact locality and secret checks;
- preliminary ratings and manual-review burden;
- connection, forbidden, not-found, timeout, TLS, and too-large outcomes; and
- runtime and storage.

Create a retry result review, dashboard note, local commit, and relay. Stop
before durable source-review merge regardless of the audit recommendation.
Do not scale to 500 or more within the retry task.

Do not update scout accounting or durable routing/metadata-triage ledgers. Do
not ingest, run `gabriel.codify`, extract wages, calculate wage gaps, make
wage-gap or causal claims, or run regressions.
