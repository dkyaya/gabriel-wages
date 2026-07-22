# Wave 2 Three-Worker 50-Row Batch Plan

Date: 2026-07-22

Disposition: **three locked offline-preparation batches are ready; no smoke, live scout, API/model call, source access, verification, ingestion, codification, or accounting update is authorized or performed**

## Plan in plain English

Three persistent workers will prepare and dry-review 50 municipalities each: California, Texas, and Illinois. Workers may work in parallel because prompt construction and validation are local-only. They do not smoke or live-scout. After three complete prep relays pass, a later main-coordinator task will combine the inputs in worker order and, under separate authorization, operate one 150-row direct-SDK lane with `n_parallels=1`.

The operating sequence is:

parallel offline worker preparation → one coordinator 150-row dry audit → one coordinator smoke → one coordinator serialized live queue → one eligible queue/coverage merge → dashboard JSON refresh.

## Chosen states

- **Worker 1 — CA50:** California’s 90/94 candidate-positive rate and 234 candidate rows make it the strongest proven scaled expansion. The batch is the next 50 eligible places by population after current coverage and failures.
- **Worker 2 — TX50:** Texas has only 53/1,224 municipalities covered and remains central to the institutional safety/non-safety source-gap question. Its lower positive rate is a known limitation, not a reason to abandon the contrast.
- **Worker 3 — IL50:** Illinois is preferred over New York because 68/74 successful municipalities are candidate-positive, with 2.932 rows per covered municipality. Its yield evidence is broader and stronger than NY’s 21/25 and 2.280 rows per covered.

New Jersey is not repeated: 31 of 77 successful NJ results are parseable-empty and the positive rate is only 59.7%. Pennsylvania is promising but has only 25 covered observations; Massachusetts has only eight. New York remains the strongest deferred alternate for a later nationally tiered wave.

## Batch geometry and safeguards

Each batch contains exactly 50 `active_status=Y`, `government_type=municipal`, `geography_type=place` rows from the authoritative universe. All IDs, formal government names, population, county counts, multi-county flags, and complete county contexts are preserved. Every row is currently not scouted, absent from the queue by ID/exact name, absent from canonical context, and free of failed-connection history.

The shared future queue ID is `COORD-SERIAL150-WAVE2-2026-07-22`. Across all three files there are 150 unique municipality IDs and 150 unique Census IDs. Bloomington, Oakland, Stockton, Oxnard, Redding, Fairfield, Princeton, and Moreno Valley are absent. Counties, schools, authorities, township governments, special/industrial districts, universities, and private providers are not selected.

The four common buckets contain 10 largest remaining employers, 15 high-population expansion rows, 15 regional expansion rows, and 10 smaller-place diversity rows per state. Equal 50-row inputs keep worktree setup and 50/50 prompt audits efficient while giving the coordinator an exact 150-row merge boundary.

## Why Wave 2 follows the successful coordinator run

The first coordinator 150-row run proved that offline parallel preparation plus one sequential live lane can scale: 150/150 were attempted, 149 parsed, 112 were candidate-positive, and 246 URL-bearing leads entered scout-stage accounting. It also showed that state yield differs: CA was high, TX was moderate, and NJ was substantially more empty-heavy. Wave 2 uses that evidence directly rather than mechanically repeating the same states.

The 150-row workflow maintains one lifecycle, one stop guard, one timing ledger, one usage/cost family, and one accounting boundary. It avoids the unstable concurrent-live pattern and prevents a worker from mutating national outputs.

## Pace and resumability changes

The runner now defaults to five-second inter-row spacing, records `row_timing.csv`, summarizes timing/throughput in metadata, rejects non-empty output directories, and supports exact-hash resume planning from terminal post-patch parents. The future command still states `--sleep-between-prompts 5` explicitly.

The prior run took 1h55m37s: 4,693.886 seconds of summed backend time plus 37m15s of scheduled sleep. Holding backend latency fixed, five-second spacing reduces scheduled sleep to 12m25s and projects about 1h30m47s, saving 24m50s. Selection composition can change request latency, so plan for roughly 1.5–2.0 hours rather than treating the projection as a guarantee.

If the process stops gracefully, the coordinator preserves the parent and first generates a dry resume plan in a different fresh directory. It skips prior parseable IDs or retries only reviewed failure categories; it never overwrites the parent, uses fuzzy names, counts skipped rows as new, or rebuilds accounting before complete reconciliation.

## Expected source-discovery value

Straight-line state averages imply approximately:

| State | Candidate-positive municipalities | Candidate rows |
|---|---:|---:|
| CA | ~48 | ~124 |
| TX | ~35 | ~80 |
| IL | ~46 | ~147 |
| Total | ~129 | ~351 |

Those point estimates likely overstate yield because Wave 2 moves down each population distribution, particularly in Illinois. Use 108–132 positive municipalities and 260–360 candidate rows as a cautious planning range. Candidate volume is a later verification workload, not evidence quality. An empty exact-employer result is valid scout coverage; a wrong-employer substitution is not.

## Risks and stop conditions

- Stop a worker prep if input structure, ID uniqueness, type, eligibility, or any 50/50 prompt check fails.
- Stop the coordinator before smoke if a relay is incomplete, an input hash/order changed, a row became covered/queued/canonical/failure-only, or any protected file changed.
- Stop if the one no-search smoke fails.
- Stop live on two consecutive no-ID/no-text/no-token connection/timeout failures, repeated transport collapse, systematic parser/schema failure, lifecycle/timing/artifact loss, protected mutation, or secret exposure.
- If five-second pacing appears unstable, retain `n_parallels=1` and consider 8–10 seconds, then 15 seconds; do not add concurrent live workers.
- Illinois villages may surface special-district fire sources; Texas may surface institutional non-CBA or advisory material; California may surface contracted safety providers. These must not be attributed to the selected city.
- No source is verified, downloaded, ingested, codified, promoted, or used for claims in prep or live discovery.

## Position before national priority tiering

Wave 2 is a final evidence-informed expansion before a separate national priority-tiering step. After its eligible accounting merge, the project should compare state-level positive rates, candidate quality/triage buckets, employer scale, parseable-empty rates, verification burden, timing, and failure patterns. That later tiering should decide whether to continue deep state expansion, add New York/Pennsylvania/Massachusetts, or shift toward bounded verification. Wave 2 itself does not pre-commit that decision.
