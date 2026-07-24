# Source-Review Pilot 1 Connection-Failure Diagnostic Result

Date: 2026-07-24

## Outcome

The diagnosis succeeded. Replacing the source reviewer's custom `urllib`
transport with a bounded verifier-compatible `httpx` path reduced connection
errors from 149/150 in the original attempt to 0/10 in the locked diagnostic
probe.

Nine of ten diagnostic rows returned bounded PDF bodies, which were retained
lane-locally with matching SHA-256 hashes. The tenth row—the same Tempe row
that was forbidden in the original attempt—again returned forbidden. Source
access now works for the diagnostic sample.

This result supports a separately authorized fresh-directory retry of the
locked 150-row pilot. It does not support scaling beyond 150 and does not
authorize that retry in this task.

## Likely root cause

The practical root cause was the source-review-only transport mismatch:

- the successful URL verifier used `httpx`;
- the first source-review implementation used a separately written
  `urllib.request` opener;
- all 150 source locators exactly equaled prior HTTP-200 verifier final URLs;
- failures crossed 94 hosts; and
- the verifier-compatible diagnostic client reached nine of ten diverse
  hosts with no connection errors.

The original implementation collapsed the low-level exception into a generic
connection category, so the exact internal `urllib` failure class is not
recoverable from the preserved ledgers. The causal claim here is therefore
limited to the implementation path: the custom source-review transport was
incompatible in this environment, while the verifier-compatible path
materially succeeds on the controlled probe.

Environment proxy inheritance was not the cause supported by the comparison.
Both the working verifier and repaired source reviewer use `trust_env=False`.
The new `--trust-env-proxy` flag is explicit opt-in only and was not used in
the diagnostic probe.

## Code changes

`scripts/source_review_sources.py` now:

- uses a bounded synchronous `httpx.Client`;
- aligns connect/read/write/pool timeout handling, redirects, TLS behavior,
  streamed reads, and `trust_env=False` with the URL verifier;
- continues using the raw `source_locator`/`final_url` for access;
- sanitizes only the URL written to the ledger;
- retains the 25 MiB cap and no-sample default;
- records a sanitized `transport_exception_type` without exception messages,
  URLs, credentials, headers, or cookies; and
- preserves every fail-closed gate and all no-OCR/no-extraction/no-corpus
  boundaries.

## Tests

Seventeen offline tests pass. Four diagnosis-specific areas were added:

1. raw source locators, including sensitive-looking query fields, are passed
   to the injected transport while only a redacted final URL is recorded;
2. environment proxy inheritance is disabled by default and requires an
   explicit flag;
3. connection failures retain only a sanitized exception class/category; and
4. an end-to-end `httpx.MockTransport` response writes a bounded PDF artifact
   and matching hash without a real socket.

The existing authorization, download-mode, byte-cap, timeout, HTTP-error,
artifact-locality, output-reuse, auditor, and protected-file tests remain
green.

## Probe

Input:
`docs/analysis/source_review_pilot1_diagnostic_probe_input_2026-07-24.csv`

Input SHA-256:
`9eb4057e979209b7adbb1bdad51601c69a76fe4050682a519dd2d0bcde3b2540`

The dry run completed 10/10 planned rows with zero URL opens, network calls,
downloads, parses, OCR runs, or artifacts.

The one authorized live command was:

```bash
.venv/bin/python scripts/source_review_sources.py \
  --input-csv docs/analysis/source_review_pilot1_diagnostic_probe_input_2026-07-24.csv \
  --output-dir tmp/source_review_pilots/SOURCE-REVIEW-PILOT1-150-2026-07-24/diagnostic_probe_live_attempt1 \
  --candidate-artifact-dir tmp/source_review_pilots/SOURCE-REVIEW-PILOT1-150-2026-07-24/diagnostic_probe_live_attempt1/candidate_artifacts \
  --review-mode source_rating_live \
  --download-mode bounded \
  --allow-live-content-access \
  --concurrency 2 \
  --timeout 30 \
  --connect-timeout 8 \
  --read-timeout 20 \
  --max-redirects 5 \
  --max-bytes 26214400 \
  --no-write-content-samples
```

`--trust-env-proxy` was deliberately omitted to match the earlier successful
verifier.

## Probe results

- selected / ledger / terminal rows: 10 / 10 / 10;
- original-lane split: 5 / 5;
- distinct states and hosts: 10 / 10;
- logical URL opens / network calls: 10 / 10;
- `reviewed_metadata_and_artifact_saved`: 9;
- `download_forbidden`: 1;
- connection errors: 0;
- access reached / forbidden: 9 / 1;
- artifact saved / forbidden: 9 / 1;
- observed `application/pdf` / `unknown`: 9 / 1;
- content artifacts: 9;
- rows with matching content hashes: 9;
- total retained content bytes: 12,536,566;
- maximum retained content artifact: 3,328,197 bytes;
- metadata artifacts: 10 totaling 10,675 bytes;
- content samples: 0;
- documents/PDFs parsed: 0 / 0;
- OCR runs: 0.

All nine retained files begin with the PDF signature. Artifact sizes are
436,326; 525,803; 579,959; 679,741; 1,596,461; 1,608,505; 1,755,870;
2,025,704; and 3,328,197 bytes. Every content and metadata path resolves
inside the diagnostic output directory, and every recorded content hash
matches the retained bytes.

Preliminary technical ratings remain bounded:

- official state repository: 5;
- official municipal: 3;
- uncertain officialness: 1;
- unknown officialness: 1;
- possible relevance: 9; unknown: 1;
- `cba_candidate`: 9; unknown document type: 1; and
- medium technical extraction readiness: 9; not ready: 1.

No PDF text, pages, wage tables, wage values, or mechanism language were
parsed or extracted. These are still preliminary access/artifact signals, not
final source ratings.

## Disposition of the original 150-row attempt

Preserve the original attempt and its audit as immutable diagnostic history,
but do not merge it into a durable source-review ledger now. Its 149
connection outcomes reflect the superseded client path and would misstate
current source accessibility if treated as the operative review result.

The next authorized live action should be a fresh-directory retry of the same
locked 150 identities with the repaired client and the original two-lane
limits. After that retry, audit the new lanes and decide whether the original
attempt remains provenance-only or is linked as a superseded attempt in a
future merge design.

## Recommendation

- Prepare, but do not run here, a bounded 150-row retry.
- Do not scale to 500, 750, or 1,000.
- Require fresh dry runs and fresh output directories.
- Keep concurrency four per lane, the 30/8/20-second timeouts, five
  redirects, 25 MiB, proxy inheritance off, and content samples off.
- Stop before a durable merge.

No full retry, merge, scaling, scout accounting, routing/triage-ledger
mutation, ingestion, codification, wage extraction, wage-gap work, causal
claim, or regression occurred in this diagnosis.
