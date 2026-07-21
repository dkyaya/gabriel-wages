# Illinois IL25.3 Direct-SDK Live Scout Review

Date: 2026-07-20

Stage: scout-stage source discovery, light filtering, queueing, and discovery-coverage accounting only. Nothing in this note is source verification, ingestion approval, codified evidence, or claim support.

## Plain-English result

The required direct-SDK smoke passed, so the locked Illinois IL25.3 batch ran. Connectivity held for all 25 municipalities: every call returned nonempty text and a response ID, all 25 responses parsed, and no retry ran. The scout produced 70 parsed rows across 23 candidate-positive municipalities; Elk Grove Village and Kankakee returned valid empty candidate lists.

The normalized handoff preserves all 70 parsed rows as `unverified_scout_candidate`. One Rolling Meadows fire row has no returned `source_url`; it remains visible in the handoff but is not promoted into the durable source-candidate queue and no URL was inferred for it. The queue therefore adds 69 IL25.3 source rows and now contains 387 rows nationally. All 25 municipalities count as successful source-discovery coverage, raising the national count to 138 and Illinois to 74. No source URL was independently opened, verified, downloaded, or ingested.

## Authorized calls and execution

The synthetic preflight used exactly `Reply with OK.`, `gpt-5.4-nano`, the Harvard HUIT `/v2` base, no tools or search, one request, a 30-second timeout, and zero retries. It returned `OK`, a response ID, five output tokens, explicit success metadata, and no connection error. Artifacts are under `tmp/direct_sdk_scout_backend_preflight/IL/national_batch01_il25_3_2026-07-20/`.

Only after that gate passed, the project `.venv/bin/python` ran:

```bash
.venv/bin/python scripts/gabriel_state_source_scout.py \
  --state IL \
  --municipalities-csv docs/analysis/national_batch01_il25_3_scout_input_2026-07-20.csv \
  --output-dir tmp/gabriel_state_source_scout/IL/national_batch01_il25_3_live_direct_sdk_2026-07-20 \
  --prompt-mode minimal \
  --max-prompts 25 \
  --n-parallels 1 \
  --sleep-between-prompts 15 \
  --search-context-size low \
  --live \
  --live-backend direct-sdk \
  --direct-sdk-max-retries 0
```

Run `il_2026-07-20_215904` recorded 25 backend-successful, nonempty responses; 25 parseable responses; zero failed parses; and 70 parsed rows. Usage was 864,202 input tokens, 43,236 reasoning tokens, and 72,784 output tokens. Average successful model time was 39.61 seconds. The Responses API did not expose billed dollars, so cost remains unavailable rather than estimated.

## Candidate counts

| Municipality | Police | Fire | Ordinary non-safety | Unclear | Total |
|---|---:|---:|---:|---:|---:|
| Lombard | 2 | 2 | 2 | 0 | 6 |
| Buffalo Grove | 1 | 1 | 0 | 0 | 2 |
| Park Ridge | 1 | 1 | 0 | 0 | 2 |
| Streamwood | 0 | 1 | 0 | 0 | 1 |
| Wheeling | 1 | 1 | 1 | 0 | 3 |
| Calumet City | 1 | 0 | 0 | 0 | 1 |
| Northbrook | 1 | 1 | 1 | 0 | 3 |
| St. Charles | 1 | 1 | 1 | 1 | 4 |
| Mundelein | 1 | 1 | 1 | 0 | 3 |
| Elk Grove Village | 0 | 0 | 0 | 0 | 0 |
| North Chicago | 1 | 1 | 1 | 0 | 3 |
| Highland Park | 2 | 1 | 1 | 0 | 4 |
| Batavia | 1 | 1 | 1 | 0 | 3 |
| Edwardsville | 1 | 1 | 1 | 0 | 3 |
| Belvidere | 1 | 1 | 1 | 0 | 3 |
| Kankakee | 0 | 0 | 0 | 0 | 0 |
| Ottawa | 1 | 1 | 1 | 0 | 3 |
| Jacksonville | 0 | 1 | 1 | 0 | 2 |
| Marion | 2 | 1 | 1 | 0 | 4 |
| East Peoria | 1 | 1 | 1 | 0 | 3 |
| East Moline | 1 | 1 | 1 | 0 | 3 |
| Sycamore | 2 | 2 | 2 | 0 | 6 |
| Alton | 1 | 1 | 1 | 0 | 3 |
| Rolling Meadows | 1 | 2 | 1 | 0 | 4 |
| Mattoon | 0 | 1 | 0 | 0 | 1 |
| **Total** | **24** | **25** | **20** | **1** | **70** |

## Strongest apparent leads, still unverified

The cleanest metadata-level matched-cycle leads are:

- Sycamore: apparent police/fire/AFSCME sets for both 2015-2019 and 2023-2025;
- Lombard: two police, two fire, and two SEIU rows, with apparent common coverage around 2019 and additional successor-cycle material;
- Belvidere: apparent police/fire/public-works rows all labeled 2022-2026;
- Alton: apparent police/fire/ordinary Teamsters rows all labeled 2022-2026, though the civilian item is titled as an MOU and needs binding/completeness review;
- East Moline: apparent police 2021-2023, fire 2021-2024, and AFSCME 2022-2024 rows;
- Ottawa: apparent police 2022-2025, fire 2021-2024, and AFSCME 2024-2027 rows, giving a possible common 2024 boundary;
- St. Charles: apparent 2024-era police/fire/Teamsters set, but the fire lead is blocked/unreadable;
- Mundelein and North Chicago: apparent overlapping sets, but key rows are blocked/unreadable and need access work later.

Several other municipalities produced useful two-leg or mechanism leads: Buffalo Grove, Park Ridge, and Wheeling have apparent current safety agreements; Mattoon and Calumet City returned arbitration awards; Jacksonville returned fire and civilian rows. Highland Park has all three unit types but the reported cycles are sequential rather than mutually overlapping. Batavia, Edwardsville, East Peoria, and Marion have apparent triad-shaped metadata with blocked, partial, or non-overlap concerns. These are scheduling observations from scout output only.

## Leakage and parser review

- **Exact duplicate leakage:** zero returned IL25.3 URLs exactly match the pre-run national queue, canonical `contracts.csv` URLs, or another URL in this run. One St. Charles mechanism row self-labels `duplicate_risk=possible`; it is held as context. String comparison is not source verification.
- **Wrong employer:** no visible employer string points to a county, school, township, transit, park, housing, special-district, or private substitute. Sixty-three rows conservatively carry `wrong_employer_risk=possible`, seven carry `none`, and none carries `high`; exact employer identity remains unverified.
- **Wrong unit:** no obvious wrong-unit substitution is visible. The single unclear row is a St. Charles police-related technology MOA and is correctly staged as unclear mechanism context rather than forced into police, fire, or non-safety.
- **Safety as non-safety:** no ordinary non-safety row is visibly a safety agreement. The Alton civilian employer text says “non-police unit”; the safety word is an exclusion, not a substituted unit.
- **Blocked versus dead:** ten rows are marked blocked/unreadable and zero is marked dead/unreachable. Four blocked rows still say `qualifying_candidate` in the raw model output, but queue precedence places every blocked row in `insufficient_hold`; no blocked lead is treated as a dead source. Later access review must resolve the inconsistency.
- **Parser failures:** zero. The missing-URL Rolling Meadows row is a parsed but non-queueable locator failure, not a JSON/parser failure.

## Queue and coverage update

The normalized candidate CSV contains all 70 parsed rows with `scout_stage_status=unverified_scout_candidate`. The durable queue takes 69 URL-bearing rows: 53 high-priority, 3 medium-priority, 2 low-priority, 10 insufficient holds, and 1 context-only hold. The missing-locator row is preserved only in the handoff/raw artifacts.

The national queue now has 387 rows, 297 scheduled for later coordinated verification and 90 holds/rejections. Illinois contributes 217 queue rows, of which 182 are scheduled for later verification.

Discovery coverage now counts 138 municipalities nationally: 125 candidate-positive and 13 parseable-empty. Illinois counts 74 successful municipalities: 68 candidate-positive and 6 parseable-empty. Bloomington remains a separate failure-only timeout; it was not retried. Elk Grove Village and Kankakee are the new Illinois empty-result municipalities. The 16 historical MA failed requests and Bloomington remain 17 excluded failed attempts nationally.

## What should happen next

Do not open or ingest these links one by one. Continue national scaling with another separately prepared locked state batch; California is a strong untouched-state contrast. Any future live batch needs separate authorization and a fresh successful direct-SDK no-search smoke. Later coordinated verification should begin with coherent municipality bundles such as Sycamore, Lombard, Belvidere, Alton, East Moline, and Ottawa, then resolve blocked access and exact cycle overlap before any ingestion decision. Employer, unit, provenance, execution, completeness, operative dates, wage content, duplicates, and mutual overlap all remain unverified.
