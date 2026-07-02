# City-by-City Public-Source Discovery and Extraction with GABRIEL Web Mode

**Date:** 2026-07-01  
**Status:** PDF-ready abbreviated report updated after the Boston graduated retry

## 1. Executive summary

- The seed scaffold is ready: 5 city responses, 15 source rows, 34 extraction rows.
- `openai-gabriel` is installed/imported locally at version `1.1.8`.
- The built-in path is confirmed as `gabriel.whatever(..., web_search=True)`.
- A larger Boston prompt failed with connection errors.
- Minimal diagnostics all succeeded.
- A graduated Boston retry succeeded on attempt 2, returning one parseable BPS `BTU Contract Negotiations` source URL and one working extraction row.
- No ingestion was performed.

## 2. Thursday message

Built-in GABRIEL web mode works on a bounded Boston source-discovery query through the Harvard proxy, but larger structured extraction prompts need incremental tuning for stability.

## 3. Compact results table

| Stage | Result | Interpretation |
| --- | --- | --- |
| Seed scaffold | 5 city responses, 15 source rows, 34 extraction rows | schema and calibration harness ready |
| Package install | `openai-gabriel` 1.1.8 installed/imported | built-in GABRIEL available |
| Large Boston prompt | connection errors | too large or unstable request shape |
| Minimal diagnostics | all succeeded | proxy/web basics work |
| Graduated Boston retry | attempt 2 succeeded | built-in web source discovery works when bounded |

## 4. Boston bounded retry

| Attempt | Result |
| --- | --- |
| 1 | failed |
| 2 | succeeded |
| 3 | skipped |

Observed output:

- source rows: 1
- extraction rows: 1
- returned source: BPS `BTU Contract Negotiations`
- URL preserved: yes
- Boston BTU/BPS material rediscovered: yes
- ingestion: no

## 5. Interpretation

This is no longer a blocked result. The successful bounded retry shows that built-in web source discovery can work in this environment. The remaining issue is stability for larger structured extraction requests, not basic package availability or basic proxy/web connectivity.

## 6. Recommended next step

Boston-only structured extraction tuning, one dimension at a time:

1. prompt size
2. output cap
3. source metadata handling
4. timeout behavior

Do not create plots from the live retry outputs; `n=1` is too small for a numeric chart. Keep the existing Mermaid workflow diagram only.

## 7. Guardrails

- No ingestion
- No production data creation
- No five-city live pilot
- No all-32 v10 run
- No PRRs
- No causal claims

## 8. Bottom line

The Thursday package should present the Boston bounded retry as a narrow success: built-in GABRIEL web source discovery works when the request is kept small, and structured extraction should be tuned incrementally before any broader live run.
