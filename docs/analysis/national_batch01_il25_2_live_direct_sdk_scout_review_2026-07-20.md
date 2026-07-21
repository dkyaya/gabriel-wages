# Illinois IL25.2 Direct-SDK Live Scout Review

Date: 2026-07-20

Stage: unverified scout output only. No returned URL was opened independently, verified, downloaded, ingested, codified, added to canonical coverage, or used as claim evidence.

## Plain-English result

The required direct-SDK smoke preflight passed, so the locked 25-municipality Illinois batch ran. Connectivity held for all 25 rows: every call returned nonempty text and a response ID, every response parsed, and no retry was needed. The run produced 72 unverified candidate rows from 22 municipalities. Granite City, O'Fallon, and Freeport returned valid empty candidate lists and therefore count as successful source-discovery coverage without adding queue rows.

The output is promising as a discovery map, especially for Glenview, Wheaton, DeKalb, Carpentersville, Oak Lawn, Oak Park, Pekin, Rock Island, and Galesburg. It is not source verification. Employer, unit, execution/completeness, dates, wage-setting content, duplicates, and matched-cycle claims remain for a later coordinated verification wave.

## Commands and smoke gate

Smoke command:

```bash
.venv/bin/python scripts/diagnose_direct_sdk_scout_backend_smoke_test.py --output-dir tmp/direct_sdk_scout_backend_preflight/IL/national_batch01_il25_2_2026-07-20
```

The exact prompt was `Reply with OK.` using `gpt-5.4-nano`, the Harvard HUIT `/v2` base, no tools/search, one request, 30-second timeout, and zero retries. It returned `OK`, a response ID, five output tokens, explicit success metadata, and no connection error.

Live command:

```bash
.venv/bin/python scripts/gabriel_state_source_scout.py \
  --state IL \
  --municipalities-csv docs/analysis/national_batch01_il25_2_scout_input_2026-07-20.csv \
  --output-dir tmp/gabriel_state_source_scout/IL/national_batch01_il25_2_live_direct_sdk_2026-07-20 \
  --prompt-mode minimal \
  --max-prompts 25 \
  --n-parallels 1 \
  --sleep-between-prompts 15 \
  --search-context-size low \
  --live \
  --live-backend direct-sdk \
  --direct-sdk-max-retries 0
```

Run ID: `il_2026-07-20_205824`. Results: 25 responses, 25 backend-successful rows, 25 parseable rows, 0 failed parses, and 72 candidate rows. Usage was 950,865 input, 48,614 reasoning, and 78,927 output tokens; average successful response time was 44.61 seconds. The proxy did not expose billed dollar cost.

## Candidate counts

| Municipality | Police | Fire | Ordinary non-safety | Unclear | Total |
|---|---:|---:|---:|---:|---:|
| Arlington Heights | 2 | 2 | 0 | 0 | 4 |
| Oak Lawn | 1 | 1 | 1 | 0 | 3 |
| Berwyn | 1 | 0 | 1 | 0 | 2 |
| Mount Prospect | 2 | 0 | 0 | 0 | 2 |
| Wheaton | 2 | 2 | 1 | 0 | 5 |
| Oak Park | 1 | 1 | 1 | 0 | 3 |
| Hoffman Estates | 1 | 1 | 1 | 0 | 3 |
| Downers Grove | 3 | 1 | 1 | 0 | 5 |
| Plainfield | 1 | 0 | 0 | 0 | 1 |
| Glenview | 2 | 1 | 1 | 0 | 4 |
| Elmhurst | 0 | 1 | 0 | 0 | 1 |
| Romeoville | 1 | 1 | 1 | 0 | 3 |
| Crystal Lake | 1 | 1 | 1 | 0 | 3 |
| DeKalb | 2 | 2 | 1 | 0 | 5 |
| Carpentersville | 2 | 2 | 1 | 0 | 5 |
| Oswego | 1 | 0 | 0 | 0 | 1 |
| Pekin | 2 | 1 | 1 | 0 | 4 |
| Danville | 1 | 2 | 2 | 1 | 6 |
| Granite City | 0 | 0 | 0 | 0 | 0 |
| Urbana | 1 | 1 | 1 | 0 | 3 |
| Rock Island | 2 | 1 | 1 | 0 | 4 |
| O'Fallon | 0 | 0 | 0 | 0 | 0 |
| Loves Park | 1 | 0 | 1 | 0 | 2 |
| Galesburg | 1 | 1 | 1 | 0 | 3 |
| Freeport | 0 | 0 | 0 | 0 | 0 |
| **Total** | **31** | **22** | **18** | **1** | **72** |

## Scout-stage quality review

- Apparent full matched sets: Glenview has model-described 2023-2027 police/fire plus a 2020-2026 civilian agreement, suggesting a 2023-2026 overlap. DeKalb has apparent police 2016-2019, fire 2017-2020, and AFSCME 2017-2020 material, suggesting a 2017-2019 overlap. Carpentersville has apparent 2023-2025 police, 2023-2026 fire MOA, and a 2022-2024 non-safety-labeled row, suggesting 2023-2024 overlap if unit scope is confirmed.
- Other useful-looking groups: Wheaton provides repeat safety cycles and a later 2021-2026 civilian agreement, but not a clear three-way contemporaneous overlap. Oak Lawn suggests only a narrow 2022 police/fire/civilian boundary. Oak Park suggests a 2024 overlap but all three URLs were marked blocked. Pekin has current police/fire material but unclear non-safety years. Rock Island suggests police/fire 2024-2026 and civilian 2025-2027, yielding an apparent 2025-2026 overlap. Galesburg's fire/civilian rows align in 2021-2023, while its police row begins in 2024.
- Mechanism leads: Downers Grove and Elmhurst returned state-labor-board arbitration awards. These may be useful for later mechanism analysis even where a complete matched set is not yet visible.
- Duplicate leakage: no exact URL was duplicated within this run, matched the pre-run national queue, or matched a canonical contract URL. Three rows self-report `duplicate_risk=possible`; those model labels remain unresolved.
- Wrong-employer risk: 59 rows carry `wrong_employer_risk=possible` and 13 carry `none`. This is conservative scout metadata, not proof of 59 substitutions. No title/employer field visibly identifies a county, school district, park district, transit agency, housing authority, township, or other substitute employer, but every row still requires exact-employer verification.
- Wrong-unit and safety-as-non-safety risk: no clear safety agreement is labeled `non_safety`. Danville has one `unclear` police-command index/MOU locator. Carpentersville's purported non-safety MAP Chapter 390 row, Danville's Laborers row mentioning a police mechanic, and Galesburg's PSEO scope need later unit-specific review. They are not promoted as clean comparators here.
- Blocked versus dead: 15 rows are marked blocked/unreadable; none is labeled dead/unreachable. The queue holds blocked/insufficient material without treating it as proof that a source is dead. Romeoville's fire locator is explicitly `blocked_or_unreadable`; DeKalb, Oak Park, Danville, Urbana, and several other rows require access/completeness review later.
- Context and parser behavior: three rows are context-only, 12 are insufficient, one is explicitly blocked/unreadable, and 59 are model-labeled qualifying candidates. There were no parser failures. These model stages are triage inputs, not verified dispositions.

## Queue and coverage update

The normalized handoff contains 72 rows, all with `scout_stage_status=unverified_scout_candidate`. The national queue now has 318 rows: PA 75, TX 6, MA 24, NJ 8, Illinois 148 across IL25 and IL25.2, and NY 57. Of those, 239 are scheduled for later verification and 79 are holds/rejections/already-canonical rows.

National successful scout coverage is now 113 municipalities. Illinois contributes 49 successful municipalities: 45 with candidates and four with parseable empty output. Bloomington remains the single Illinois failure-only municipality and is not counted as successful coverage. The 25 IL25.2 municipalities all count as covered because all produced parseable responses; Granite City, O'Fallon, and Freeport are `scouted_no_candidates`.

## What should happen next

Do not verify all 72 links or ingest anything automatically. Continue national state-scale discovery under a separate authorization, always preceded by a fresh direct-SDK smoke. Later coordinated verification should prioritize municipality-level bundles—first Glenview and DeKalb, then the plausible Carpentersville, Rock Island, Oak Lawn/Oak Park, and mechanism-focused Downers Grove/Elmhurst groups—and confirm exact employer, unit, provenance, execution/completeness, dates, wage content, duplicate status, and mutual cycle overlap before any ingestion decision.
