# Scout pace settings recommendation — 2026-07-21

## Decision

Set the runner's default `--sleep-between-prompts` value to five seconds and keep the flag fully configurable. Long-run coordinator prompts should state `--sleep-between-prompts 5` explicitly for auditability. This is a sequential pace experiment backed by one successful 150-row run and earlier evidence that concurrency, rather than spacing alone, was the more important instability driver.

The pre-patch CLI code default was actually zero seconds; the successful production command overrode it with 15 seconds. This patch therefore aligns the code-level default and the successor long-run prompts at five seconds, rather than silently depending on either the old zero-second fallback or the historical explicit 15-second command.

The change does not authorize live scouting, concurrent live workers, `n_parallels>1`, automatic retries, source verification, ingestion, or codification.

## Why 15 seconds was conservative

Fifteen-second spacing was selected while the project was diagnosing Harvard-proxy capacity failures and GABRIEL checkpoint behavior. Small earlier tests at 10, 15, and 20 seconds were all stable when `n_parallels=1`; the clearest controlled failure occurred when concurrency rose to two. The project therefore retained 15 seconds as a cautious operational setting while scaling from three rows to 25-row and then 150-row sequential batches.

The coordinator 150-row run then completed 149/150 parseable with only one isolated timeout and no repeated connection collapse. Its recorded request time plus the 15-second gaps nearly exhausts total wall time, showing that spacing is now a large, measurable runtime cost.

## Why five seconds is the next default test setting

Five seconds keeps an explicit pause between every single-flight request while removing ten seconds from each inter-row gap. For 150 rows, the scheduled sleep falls from 2,235 seconds to 745 seconds. The estimated saving is 1,490 seconds, or 24 minutes 50 seconds. If the underlying request-time distribution remains similar, projected runtime falls from about 115 minutes 37 seconds to about 90 minutes 47 seconds.

Five seconds is deliberately a test setting, not a universal reliability finding. Future artifacts now record actual per-row starts, finishes, elapsed time, sleep, tokens, response-ID presence, parse status, failures, total elapsed time, median/average duration, sleep total, and effective rows/hour so the next run can evaluate it directly.

## Stop and fallback policy

Keep all live work in one coordinator-controlled sequential lane with `n_parallels=1` and zero SDK retries. Stop the run when any existing safety condition occurs, including:

- two consecutive connection/timeout rows with no response ID, no response text, and no output tokens;
- a repeated transport pattern suggesting connection collapse;
- systematic malformed output or parser/schema failure;
- missing/corrupt lifecycle, timing, raw, or failure artifacts;
- unexpected protected-file mutation; or
- any secret exposure.

After a transport-related stop, preserve the terminal parent directory and review its timing/failure ledger. Do not rerun into it. If a separately authorized recovery proceeds, use a fresh output directory and consider sequential spacing of 8–10 seconds. Return to 15 seconds if the intermediate fallback is unstable. Do not respond to instability by adding concurrent live workers.

## Resumability boundary

Safe resume requires a post-patch parent directory containing terminal `run_metadata.json`, exact `input_csv_sha256`, and `row_timing.csv`. The input hash must match unless an explicit mismatch override follows a documented row-identity audit. Resume planning prioritizes `municipality_id`, then Census government ID, then an exact unique state+municipality legacy identity; fuzzy name matching is never used.

The successful 2026-07-21 150-row run predates these artifacts and cannot be resumed through the new fail-closed mode. Its Moreno Valley failure remains historical evidence and is not automatically retried.
