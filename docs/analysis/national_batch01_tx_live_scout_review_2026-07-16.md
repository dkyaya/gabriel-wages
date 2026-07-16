# National Batch 01 Texas Live Scout Review — 2026-07-16

## Plain-English outcome

The authorized live scout sent exactly three row-aware prompts: San Antonio, Austin, and Houston. All three calls returned successfully and all three responses parsed as JSON. The run produced six unverified candidate rows: two for San Antonio, none for Austin, and four for Houston. No retry was run because there were no failed rows.

This was lead generation only. No returned URL was opened or independently checked after the scout. Nothing was verified, ingested, codified, or added to canonical contract, coverage, corpus, claim, or evidence data.

Houston produced the clearest next-stage leads: a City-hosted 2015–2018 HOPE ordinary-municipal agreement, a later HOPE agenda record, an older police meet-and-confer PDF on a third-party host, and a City-hosted firefighter settlement/impasse document. San Antonio produced institutional-context leads rather than an ordinary civilian comparator agreement. Austin returned an empty candidate list.

## Exact authorized command

The command below was used with one minor local-only environment adjustment: `MPLCONFIGDIR` points Matplotlib's import cache to a writable temporary directory. It does not change the scout model, prompt, search, input, or municipality scope.

```bash
MPLCONFIGDIR=/tmp/gabriel-wages-mpl-cache python scripts/gabriel_state_source_scout.py \
  --state TX \
  --municipalities-csv docs/analysis/national_batch01_tx_scout_input_2026-07-16.csv \
  --output-dir tmp/gabriel_state_source_scout/TX/national_batch01_tx_live_2026-07-16 \
  --prompt-mode minimal \
  --max-prompts 3 \
  --n-parallels 1 \
  --sleep-between-prompts 15 \
  --search-context-size low \
  --live
```

Preflight loaded exactly these full-context rows, in this order:

1. San Antonio — `tx_san_antonio`, Census government ID `175988`, `CITY OF SAN ANTONIO`.
2. Austin — `tx_austin`, Census government ID `176394`, `CITY OF AUSTIN`.
3. Houston — `tx_houston`, Census government ID `176169`, `CITY OF HOUSTON`.

## Run metadata and cost

```text
run_id=tx_2026-07-16_164549
mode=live
model=gpt-5.4-nano
search_context_size=low
n_parallels=1
sleep_between_prompts=15
municipalities_requested=3
responses=3
parseable=3
failed_parses=0
candidate_rows=6
live_attempted=true
live_succeeded=true
live_failure_reason=null
```

Recorded usage:

```text
total_cost=$0.03468535
average_cost_per_prompt=$0.01156178
input_tokens=95,158
reasoning_tokens=5,521
output_tokens=7,002
total_recorded_tokens=107,681
average_successful_call_time=28.7101 seconds
```

These figures come from GABRIEL's run output. They include reported model/search usage but should still be treated as the runner's accounting rather than an independently reconciled invoice.

## Candidate count by city and unit type

| Municipality | Police | Fire | Non-safety | Unknown | Total |
|---|---:|---:|---:|---:|---:|
| San Antonio | 0 | 0 | 2 | 0 | 2 |
| Austin | 0 | 0 | 0 | 0 | 0 |
| Houston | 1 | 1 | 2 | 0 | 4 |
| **Total** | **1** | **1** | **4** | **0** | **6** |

Every parsed runner row has `verification_status=unverified` and `promotion_status=raw_model_output`. The quarantined task summary uses `scout_stage_status=unverified_scout_candidate` for all six rows.

## San Antonio review

San Antonio did **not** return an ordinary civilian CBA or authoritative civilian wage schedule. It returned two contextual rows:

1. A San Antonio municipal-code page that the model says may show collective bargaining is not authorized for non-covered groups. This could help document an institutional non-availability mechanism, but the model's broad legal/scope characterization is unverified. The page is hosted on Municode even though the model labeled the owner type `city`.
2. A San Antonio Fire Department collective-bargaining document whose stated relevance is that civilian personnel are excluded from the fire bargaining unit. This is the correct city employer, but it is a fire document labeled as a `non_safety` candidate. It is therefore wrong-unit contextual leakage and must not count as an ordinary civilian comparator.

Conclusion: the scout found possible civilian-pathway context, not a usable non-safety comparator lead. Verification should check the actual ordinance scope and search City personnel, compensation, pay-plan, and civilian employee-relations records. The fire document is low priority and useful only if its exact language helps establish why a civilian CBA is absent.

## Austin review

Austin parsed successfully and returned an empty `candidates` list. It therefore found no qualifying ordinary general-municipal, non-EMS comparator lead.

The raw GABRIEL web-search trace includes City compensation pages and AFSCME-related pages, but the model did not select them as candidate output. They remain raw search traces, not candidate rows, and were not opened or verified in this task.

Conclusion: Austin's requested gap remains unresolved. Because this was a parseable empty response rather than a failed row, the failed-row-only retry authorization does not apply. Verification should manually evaluate the strongest City/AFSCME traces or design a separately authorized, narrower Austin-only prompt after diagnosing why the model rejected them.

## Houston review

Houston returned one police, one fire, and two non-safety rows:

1. **HOPE 2015–2018 ordinary-municipal meet-and-confer agreement** — model-reported City-hosted PDF, ordinary municipal scope, and high confidence. This is the strongest matched-comparison lead and the highest verification priority.
2. **Firefighter settlement/impasse document** — model-reported City-hosted 2017–2024 backpay/settlement material with court/arbitration context. This is a strong mechanism lead. The model labeled it `factfinding`, while its returned title describes a settlement/interoffice memorandum, so document type must be corrected only after reading it.
3. **Police 2015–2018 meet-and-confer agreement** — apparent repeat-cycle police agreement, but on a third-party S3 host. It needs authenticity, completeness, source-owner, and date checks and ideally an official City or HPOU copy.
4. **Later HOPE agenda cover sheet ending in 2024** — useful for locating a successor non-safety agreement, but the cover sheet alone is context rather than a verified contract. Verification should retrieve the actual attachment and confirm its scope and dates.

Conclusion: Houston met the requested police/fire/non-safety and impasse/repeat-cycle lead-generation purpose at scout stage. It did not itself establish a verified matched cycle.

## Wrong-employer and prompt leakage

- **Parsed candidate rows:** no wrong-employer substitution. All six rows name the target City of San Antonio or City of Houston employer. No county, school, transit, hospital/health, regional, special-district, or private EMS/fire employer appears as a parsed candidate.
- **Wrong-unit leakage:** one San Antonio fire document was returned under `unit_type=non_safety`. It remains clearly marked contextual and low-priority in the quarantined summary.
- **Raw search trace leakage:** GABRIEL's web-search source lists contain many irrelevant third-party, Reddit, wrong-jurisdiction, and non-target pages. The model filtered these from the candidate JSON, so they are preserved only in raw artifacts and are not candidate leads.
- **Source/document labels:** Municode may be a third-party host despite the San Antonio row's `city` owner label; Houston's firefighter settlement may not be a `factfinding` document despite the model-returned type. Both require verification-stage correction, not scout-stage recoding.

The leakage did not justify expanding or retrying the batch. The run stopped after the three authorized prompts.

## Parser and failure review

All three responses parsed. `failed_parses.csv` contains only its header, and every recorded failure-type count is zero:

```text
timeout_or_capacity=0
empty_response_with_response_id=0
empty_response_no_response_id=0
json_parse_error=0
other=0
```

Austin's empty candidate list is not a parser failure. No retry was run.

## Promising but still unverified

Verification order:

1. Houston 2015–2018 HOPE meet-and-confer agreement — best ordinary-municipal comparison lead.
2. Houston firefighter settlement/impasse document — best mechanism lead, with document-type caution.
3. Houston police 2015–2018 agreement — potentially useful repeat cycle, but third-party-hosted.
4. Houston later HOPE agenda record — locate and verify the actual successor agreement attachment.
5. San Antonio municipal-code context — test the institutional non-availability claim and look for an authoritative civilian pay-plan pathway.
6. San Antonio fire scope document — low-priority context only; never count as the non-safety unit.

Austin has no parsed candidate to rank.

## What verification should do next

Verification—not ingestion—should now:

1. Open only the strongest City/union candidate links and confirm the exact city employer, source owner, title, document completeness, agreement parties, unit, and effective dates.
2. For Houston, determine whether the 2015–2018 HOPE and police agreements form a same-cycle comparison and how the fire settlement/underlying agreement maps to a comparable cycle. Retrieve the actual later HOPE attachment before treating the agenda cover sheet as an agreement.
3. For San Antonio, test the model's ordinance interpretation and identify an authoritative civilian compensation/pay-plan or employee-relations pathway. Keep the fire scope document out of the non-safety count.
4. For Austin, manually inspect the strongest City compensation and AFSCME traces, then decide whether a separately authorized Austin-only scout revision is warranted. Do not call the empty response evidence that no comparator exists.
5. Record URL reachability, provenance, dates, and match status in a verification ledger. Keep every row unverified until those checks pass.

Do not ingest, codify, modify canonical coverage, or mark any municipality verified based on this live scout alone.

## Preserved live artifacts

The complete live output is under:

`tmp/gabriel_state_source_scout/TX/national_batch01_tx_live_2026-07-16/`

It includes:

- `prompt_preview.md`
- `run_metadata.json`
- `raw_outputs.csv`
- `parsed_candidates.csv`
- `failed_parses.csv`
- `cost_summary.json`
- `cost_summary.csv`
- `gabriel_save_dir/gabriel_whatever_raw.csv`
- `gabriel_save_dir/gabriel_whatever_raw_run_metadata.json`

The runner also wrote its timestamped unverified candidate CSV and appended one run-accounting row to the persistent cost log. The task-level quarantined summary is `docs/analysis/national_batch01_tx_live_scout_candidates_2026-07-16.csv`.
