# National Scout Candidate Queue Methodology

Date: 2026-07-20

Status: durable scout-stage queue standard. This methodology does not verify sources, ingest documents, run codification, alter canonical coverage, or establish claim evidence.

## Purpose

National scouting should discover and preserve plausible municipal labor-source leads before the project spends time opening every source. The durable queue at `docs/analysis/national_scout_candidate_queue_2026-07-20.csv` combines completed live-scout outputs, applies light deterministic triage, and holds stronger leads for later coordinated verification waves.

The queue solves two practical problems:

1. A successful model response can produce a useful locator without proving that the URL opens, that the document is complete, or that the employer, unit, dates, and wage content are correct.
2. Verifying every small scout batch immediately makes national discovery proceed one document at a time. That is inefficient relative to scouting multiple bounded slices, ranking the combined queue, and verifying matched sets in planned waves.

The queue is therefore a discovery and scheduling artifact. It is not a source inventory with final verification status and is not part of either canonical corpus.

## Included source sets

The 2026-07-20 build contains 189 candidate rows:

- Pennsylvania pilot/batch-25 final output: 75 rows from the successful main and five-row retry outputs on 2026-07-15;
- Texas national batch 01: 6 rows from 2026-07-16;
- Massachusetts national batch 01 successful rerun: 24 rows from 2026-07-20;
- New Jersey national batch 01 direct-SDK run: 8 rows from 2026-07-20.
- Illinois national batch 01 state-scale direct-SDK run: 76 rows from 24 successful responses on 2026-07-20. Champaign returned a parseable empty candidate list, and Bloomington timed out without a response; neither adds a queue row.

The original candidate files are read-only inputs. The builder does not rewrite them. Pennsylvania's two files are combined because the retry filled the five connection-failed municipalities from the same final 25-municipality batch; their candidate totals reconcile exactly to the existing PA municipality coverage ledger.

## One row and stable identity

One queue row remains one scout-returned candidate document for one municipality and one scout-labeled unit type. `queue_id` is deterministic within state and build date. `source_candidate_file`, `scout_run_id`, `raw_response_ref`, and `calibration_verification_id` preserve the path back to the original scout and calibration artifacts.

The queue preserves scout wording in title, union, employer, years, type, completeness, risk, relevance, and verification-reason fields. Missing fields on older Pennsylvania/Texas schemas are recorded as `not_available_from_legacy_scout`; they are not inferred from source URLs.

## Stage taxonomy

Rows without an existing Texas or Massachusetts calibration finding remain:

```text
scout_stage_status=unverified_scout_candidate
```

Existing calibration findings are carried with explicit prefixes such as:

- `calibration_verified_candidate`
- `calibration_partially_verified_candidate`
- `calibration_context_only`
- `calibration_unreachable`
- `calibration_rejected_or_insufficient`
- `calibration_already_canonical`

Those labels report what the bounded TX/MA calibration passes found. They are not a fresh verification, do not convert rows into final project-wide verified data, and do not authorize ingestion. The original scout metadata remains visible even where calibration corrected it; the calibration fields explain the correction.

`later_ingestion_queue_status=verified_later_ingest_candidate` also means "identified by a prior calibration pass as suitable for a later pre-ingestion review." It does not mean ingested. `already_ingested_canonical` means an exact canonical URL or a calibration-confirmed duplicate is held only for deduplication and scout-quality accounting.

## Light triage buckets

The controlled buckets are:

- `high_priority_later_verify`
- `medium_priority_later_verify`
- `low_priority_later_verify`
- `context_only_hold`
- `likely_duplicate_hold`
- `insufficient_hold`
- `rejected_from_calibration`
- `already_canonical_hold`

High, medium, and low rows form the later-verification queue. Holds and calibration rejections remain in the durable CSV so the project does not repeatedly rediscover or re-review them.

Precedence matters. Exact canonical sources and calibration-confirmed duplicates are held first. Calibration-confirmed wrong-unit and insufficient rows are rejected; unreachable rows are held as insufficient; verified context stays context-only. A verified or partially verified calibration finding overrides a scout's incorrect context/dead/partial label. For uncalibrated rows, context flags, probable duplicates, wrong-employer risk, blocked state, and completeness metadata determine holds before score thresholds apply.

## Triage score

`triage_score` is a deterministic 0-100 scheduling aid, not a probability or evidence-quality estimate. It rewards:

- city, state-labor-board, or union ownership;
- apparent CBA, MOA, award, fact-finding, compensation-plan, or other wage-setting document type;
- apparent full-document status;
- police/fire/non-safety coverage within the same municipality;
- model-reported anchor-cycle overlap;
- visible operative-year evidence;
- specific titles and higher scout confidence;
- prior calibration findings that recommended later ingestion review.

It penalizes:

- context pages, minutes, agenda covers, and index pages;
- missing/partial/blocked/dead document states;
- non-overlap with an anchor cycle;
- possible or exact duplicates;
- possible/high wrong-employer risk;
- calibration rejection, unreachable status, or canonical duplication;
- candidate periods wholly after 2024 or wholly before 2014.

Scores of 70 or more normally map to high priority, 50-69 to medium, and below 50 to low, after hold/rejection precedence. The code, not the prose note, is authoritative for exact point values and is regression-checked through row-count, schema, URL, ID, calibration-join, and controlled-vocabulary assertions.

## Calibration use

Texas and Massachusetts verification passes were calibration exercises. They taught the project how the prompt leaked wrong-unit context, confused cover sheets with agreements, misread document access/completeness, returned already canonical sources, and sometimes misstated cycles. The queue uses only their already-recorded ledgers; it does not reopen a URL.

Calibration is used to:

- hold seven Massachusetts duplicate/superseded rows already in the canonical corpus;
- reject the San Antonio safety-as-non-safety row and insufficient Municode assertion;
- keep verified context separate from causal wage-setting documents;
- identify eight prior calibration `later_ingest_candidate` recommendations for later coordinated pre-ingestion review;
- correct triage when direct calibration showed that a scout's context/dead/partial label was wrong.

Future states, including all Illinois rows, should normally remain uncalibrated in the queue until a later coordinated verification wave is selected. Calibration findings should never be copied into canonical verification or ingestion fields without that later workflow's explicit decision.

## Rebuild procedure

The local-only builder is:

```bash
python scripts/build_national_scout_candidate_queue.py
```

Before adding a future live batch:

1. Preserve the original raw run artifacts and a task-level candidate CSV with one row per returned candidate.
2. Keep every row scout-stage and retain parseable empty results at municipality coverage level even though they add no queue row.
3. Add the new candidate CSV and run/wave metadata to `SOURCE_SPECS` in the builder.
4. Add calibration input only if a bounded calibration pass already exists; never create calibration labels by inference.
5. Rebuild and review state counts, triage counts, unique IDs, and source-file provenance.
6. Run `scripts/build_national_scout_coverage_status.py` so candidate and municipality coverage totals reconcile.

No source URL needs to be opened during this process. Opening sources belongs to later verification waves selected from high-value matched sets, not routine queue maintenance.

## Downstream gate

Before ingestion, a separately authorized verification/pre-ingestion pass must establish URL access, authoritative ownership, exact municipality employer, exact bargaining unit, executed/binding status, document completeness, visible operative dates, wage-setting content, duplicates, and within-city overlap. Only then can the normal ingestion pipeline create one bargaining-unit/cycle row, preserve full text and verbatim spans, validate provenance, and update canonical coverage. Codification and claim use remain later, separate stages.
