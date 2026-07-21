# National Scout Coverage Status Methodology

Date: 2026-07-20

Status: national source-discovery execution accounting, last rebuilt 2026-07-21. This is separate from verified-source, ingestion, canonical-contract, codified, and claim coverage.

## Authoritative population denominator

`docs/analysis/national_municipality_universe.csv` is the denominator. It contains 35,589 functionally active Census municipal and township governments across the 50 states and DC. Ordinary counties, Census-designated places, school districts, and special districts are outside this universe.

`docs/analysis/national_municipality_county_crosswalk.csv` preserves every known municipality-county relationship. County coverage counts associations, not unique governments: a multi-county municipality appears in every associated county, so county rows are deliberately non-additive.

`scripts/build_scout_coverage.py` remains the Census universe/crosswalk builder and top-level orchestrator. Its historical carry-forward table contains PA only, so it no longer writes that legacy table over the national status outputs. After rebuilding the universe locally, it delegates current status generation to `scripts/build_national_scout_coverage_status.py`.

## Scout coverage taxonomy

`scout_coverage_status` has four mutually exclusive values:

- `not_scouted`: no successful discovery response and no retained failure-only attempt;
- `scouted_with_candidates`: a live model response succeeded, parsed, and produced one or more candidate rows;
- `scouted_no_candidates`: a live model response succeeded and parsed with an empty candidate list;
- `scout_attempt_failed_connection`: one or more live attempts failed at the connection/transport/timeout layer and no later successful discovery response exists.

A connection-only or zero-response timeout failure is not discovery coverage. Massachusetts produced 16 connection-error request rows across eight unique municipalities on 2026-07-16. Those attempts are preserved in failure-count/run-ID columns and excluded. The successful 2026-07-20 rerun is what makes the eight municipalities scout-covered. Bloomington IL later timed out without text, response ID, or tokens and remains a failure-only municipality. If a future municipality has only this kind of transport failure, it remains visibly `scout_attempt_failed_connection`, not `not_scouted` and not source-covered.

Parseable empty output counts as coverage because the model completed the discovery prompt; it does not prove that no source exists. Austin TX, two PA municipalities, Champaign, Granite City, O'Fallon, Freeport, Elk Grove Village, and Kankakee IL, Yonkers, Schenectady, Mount Vernon, and Newburgh NY, and San Jose CA are current `scouted_no_candidates` examples.

## Queue, verification, and ingestion fields

Scout execution status is not asked to carry every downstream meaning. Separate columns record:

- `queue_status=queued_for_later_verification` when at least one candidate is in a high/medium/low later-verification bucket;
- `verification_coverage_status=calibration_verified` only for municipalities touched by the already-completed TX/MA calibration passes;
- `later_ingestion_status=verified_later_ingest_candidate` when a calibration row recommended later ingestion review;
- `canonical_overlap_status=already_ingested_canonical` when the municipality already has at least one row in the canonical corpus;
- `already_ingested_canonical_candidate_count` when a specific scout-returned URL is already canonical or a calibration-confirmed duplicate.

These statuses are deliberately orthogonal. A municipality can already have canonical contracts and still need verification of a new repeat-cycle candidate. A calibration-verified candidate can remain un-ingested. A scout-covered municipality can have no verification at all. None of these fields assert that documents have been codified or support a claim.

## Successful runs represented

The current accounting includes:

- PA pilot/batch-25 final coverage: 25 municipalities;
- TX national batch 01: San Antonio, Austin, and Houston;
- MA national batch 01 successful rerun: Somerville, Newton, Boston, Worcester, Arlington, Georgetown, Franklin, and Seekonk;
- NJ national batch 01 direct-SDK run: Newark, Jersey City, and Camden;
- IL national batch 01 state-scale direct-SDK run: 24 successful municipalities from the locked IL25 input; Champaign returned a parseable empty result and Bloomington is retained as a failure-only timeout.
- IL national batch 01 IL25.2 direct-SDK run: all 25 locked municipalities returned parseable responses; 22 produced candidates and Granite City, O'Fallon, and Freeport returned empty candidate lists.
- IL national batch 01 IL25.3 direct-SDK run: all 25 locked municipalities returned parseable responses; 23 produced candidates and Elk Grove Village and Kankakee returned empty candidate lists. One parsed Rolling Meadows row lacks a source URL and remains in the batch handoff but outside the source-candidate queue.
- NY national batch 01 state-scale direct-SDK run: all 25 locked city rows; 21 returned candidates and four returned parseable empty lists.
- CA25 direct-SDK run: 21 of 25 locked municipal rows returned parseable responses; 20 produced candidates and San Jose returned a parseable empty list. Oakland, Stockton, Oxnard, and Redding timed out without text, IDs, or tokens and remain failure-only rows excluded from successful discovery coverage.

That produces 159 scout-covered municipalities: 145 with candidate rows and 14 with parseable empty outputs. The failed MA connection-only runs, Bloomington timeout, and four CA25 timeouts are retained separately and do not add coverage.

## Outputs

`docs/analysis/national_scout_coverage_municipality_2026-07-20.csv` contains one row for every municipality in the universe and is the detailed status source.

`docs/analysis/national_scout_coverage_state.csv` aggregates unique municipalities. It reports the full denominator, successful coverage, candidate-positive and empty results, failed transport attempts excluded, queued candidate counts, calibration counts, canonical overlap, and successful-run usage/cost where available. Direct-SDK NJ, IL, and NY billed costs are unavailable and remain blank rather than estimated.

`docs/analysis/national_scout_coverage_county.csv` aggregates municipality-county associations and repeats the non-additivity warning on every row.

## Build procedure

The candidate queue must be current before coverage is built:

```bash
python scripts/build_national_scout_candidate_queue.py
python scripts/build_national_scout_coverage_status.py
```

When the Census universe itself needs rebuilding and the public Census archives are already cached locally, the canonical orchestration command is:

```bash
python scripts/build_scout_coverage.py
```

That command refreshes the county/municipality universe and crosswalk, validates the historical PA carry-forward, and then calls the current national status builder. It does not run a model or inspect a source URL. If a Census cache is absent, the older universe builder may download that public Census input; such a download is not needed for routine post-scout status updates.

After every successful live scout batch:

1. Add the original candidate file to the national queue builder.
2. Add the full successful input slice and run metadata to the coverage builder, including municipalities with empty candidate lists.
3. Add connection-only attempts to failure accounting without treating them as coverage.
4. Rebuild queue first, then municipality/state/county status.
5. Reconcile candidate totals, successful municipality totals, state totals, and the 35,589 national denominator.
6. Keep calibration, later-ingestion, canonical, codified, and claim statuses separate.

## Why this matters

The project does not need to inspect every one of roughly 35,589 governments. The universe supplies a denominator; the manifest and claim register select strategically useful slices; the scout records whether those municipalities were actually searched; and the queue ranks matched-set and mechanism leads. Later verification can therefore sample the strongest cross-occupation sets, institutional contrasts, and geographic gaps rather than opening every result or every government website.
