# Boston Graduated GABRIEL Built-In Web Retry

**Date:** 2026-07-01
**Scope:** Boston-only graduated retry; no ingestion and no production data changes.

## Purpose

Isolate whether the earlier Boston built-in web failure was caused by prompt size, output size, source include behavior, domain/filter request shape, timeout, or transient connection issues.

## Why This Was Run

Minimal proxy diagnostics succeeded for raw OpenAI non-web, GABRIEL non-web, GABRIEL tiny web-search, and raw Responses API web-search. The larger Boston smoke test still had failed with connection errors, so the next step was a smaller Boston-only retry sequence.

## Attempt Sequence

| Attempt | Name | Ran | Success | Source rows | Extraction rows | Notes |
| ---: | --- | --- | --- | ---: | ---: | --- |
| 1 | tiny_boston_report | yes | no | 0 | 0 | No reportable evidence from this attempt. |
| 2 | source_discovery_only | yes | yes | 1 | 1 | Succeeded with non-empty response and source signal; later attempts skipped. |
| 3 | small_attribute_extraction | no | no | 0 | 0 | Not run because an earlier attempt produced reportable evidence. |

## Result

Attempts run: 1, 2.
Succeeded attempt: 2.
Source URLs/citations returned: yes.
Boston BTU/BPS material rediscovered: yes.
Source row count: 1.
Extraction row count: 1.

## Interpretation

Most likely category: **prompt-size/output-size issue or transient connection issue**.

The graduated retry succeeded on the second small Boston source-discovery query, so the earlier larger failure is not reproduced by a smaller Boston-specific built-in web prompt. Attempt 1 still hit a connection error, which leaves transient connection behavior in the mix. Larger structured extraction still needs tuning before any broader live pilot.

## Thursday Recommendation

Report that built-in GABRIEL web mode works on a small Boston query, URLs/citations were parseable in the working output, and larger structured extraction should be tuned incrementally before any five-city live run. No ingestion was performed.
