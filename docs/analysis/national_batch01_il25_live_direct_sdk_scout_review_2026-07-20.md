# Illinois National Batch 01 IL25 Direct-SDK Live Scout Review

Date: 2026-07-20

Stage: live source discovery and light triage only. Every returned row remains an unverified scout candidate. No source URL was independently opened, no PDF was downloaded, and no source was verified, ingested, codified, added to canonical coverage, or used as claim evidence.

## Plain-English result

The mandatory synthetic direct-SDK preflight passed, so the locked 25-municipality Illinois batch ran once through the direct-SDK backend. Connectivity held for 24 of 25 prompts. Those 24 responses were nonempty, had response IDs, and parsed successfully; Champaign returned a valid empty candidate list. Bloomington timed out after roughly 90 seconds with no response text, response ID, or tokens. It was not retried because the authorization allowed only the smoke action and one live batch, and there was no real model response to diagnose.

The successful responses produced 76 candidate rows: 31 police, 24 fire, 20 ordinary non-safety, and one unclear/context-only police-management row. The output contains promising apparent matched sets, especially Rockford, Springfield, Joliet, Bolingbrook, and Decatur, but these descriptions are model output rather than source facts. The queue builder added all 76 rows without verification. Coverage counts 24 Illinois municipalities as successfully scouted, records Bloomington as a failure-only attempt, and therefore does not claim all 25 as source-discovery covered.

## Source-of-truth reconciliation

The supplied relay `tmp/national_batch01_il25_filter_contract_dry_run_2026-07-20_relay_014f24d.zip` passed integrity inspection. Local `HEAD` before work was `d25dc067ac55f731eb9794263fdd503994616790`, an amended dry-run checkpoint newer than the relay's `014f24d` checkpoint. Shared files matched except for three documentation additions that supplied the later cost-planning paragraph; the narrow relay also omitted the two named test scripts. This is clear evidence that the relay is stale/incomplete relative to the repository, so the newer repository versions were preserved. No Git remote was inspected.

## Preflight gate

Artifacts: `tmp/direct_sdk_scout_backend_preflight/IL/national_batch01_il25_2026-07-20/`

- Prompt: exactly `Reply with OK.`
- Backend/resource: OpenAI Responses API through the direct-SDK backend and Harvard `/v2` base
- Model: `gpt-5.4-nano`
- Tools/search: none; `web_search=false`
- Requests/retries/timeout: one request, zero retries, 30 seconds
- Result: `OK.` with a response ID; 10 input, 0 reasoning, and 6 output tokens
- Gate: `success=true` and `model_response_succeeded=true`; no connection error

The live batch proceeded only after all required gate conditions passed.

## Locked live execution

The full-context input resolved before execution to exactly this ordered list: Chicago, Aurora, Rockford, Springfield, Naperville, Joliet, Elgin, Peoria, Champaign, Waukegan, Bloomington, Decatur, Evanston, Schaumburg, Bolingbrook, Palatine, Skokie, Des Plaines, Orland Park, Tinley Park, Normal, Belleville, Moline, Carbondale, and Quincy.

Exact command used:

```bash
.venv/bin/python scripts/gabriel_state_source_scout.py \
  --state IL \
  --municipalities-csv docs/analysis/national_batch01_il25_scout_input_2026-07-20.csv \
  --output-dir tmp/gabriel_state_source_scout/IL/national_batch01_il25_live_direct_sdk_2026-07-20 \
  --prompt-mode minimal \
  --max-prompts 25 \
  --n-parallels 1 \
  --sleep-between-prompts 15 \
  --search-context-size low \
  --live \
  --live-backend direct-sdk \
  --direct-sdk-max-retries 0
```

The project virtual-environment interpreter was required because the shell's `python` and `python3` shims were not usable. Run ID was `il_2026-07-20_184849`. The process completed normally after about 28 minutes. It recorded 1,028,386 input, 49,032 reasoning, and 79,974 output tokens. Average model-response time among successful requests was about 50.04 seconds. The direct SDK exposed usage but not billed dollars, so cost remains unavailable rather than estimated.

## Municipality and unit results

| Municipality | Police | Fire | Non-safety | Unclear | Total | Scout outcome |
|---|---:|---:|---:|---:|---:|---|
| Chicago | 2 | 1 | 1 | 0 | 4 | candidates |
| Aurora | 0 | 1 | 0 | 1 | 2 | candidates |
| Rockford | 1 | 1 | 1 | 0 | 3 | candidates |
| Springfield | 2 | 1 | 1 | 0 | 4 | candidates |
| Naperville | 1 | 1 | 1 | 0 | 3 | candidates |
| Joliet | 2 | 1 | 1 | 0 | 4 | candidates |
| Elgin | 1 | 1 | 1 | 0 | 3 | candidates |
| Peoria | 2 | 2 | 1 | 0 | 5 | candidates |
| Champaign | 0 | 0 | 0 | 0 | 0 | parseable empty response |
| Waukegan | 2 | 1 | 1 | 0 | 4 | candidates |
| Bloomington | 0 | 0 | 0 | 0 | 0 | timeout; no model response |
| Decatur | 1 | 2 | 1 | 0 | 4 | candidates |
| Evanston | 1 | 1 | 1 | 0 | 3 | candidates |
| Schaumburg | 2 | 1 | 1 | 0 | 4 | candidates |
| Bolingbrook | 2 | 2 | 2 | 0 | 6 | candidates |
| Palatine | 1 | 1 | 1 | 0 | 3 | candidates |
| Skokie | 2 | 2 | 0 | 0 | 4 | candidates |
| Des Plaines | 0 | 0 | 1 | 0 | 1 | candidates |
| Orland Park | 1 | 0 | 1 | 0 | 2 | candidates |
| Tinley Park | 1 | 0 | 0 | 0 | 1 | candidates |
| Normal | 1 | 1 | 0 | 0 | 2 | candidates |
| Belleville | 1 | 1 | 1 | 0 | 3 | candidates |
| Moline | 1 | 1 | 1 | 0 | 3 | candidates |
| Carbondale | 2 | 1 | 1 | 0 | 4 | candidates |
| Quincy | 2 | 1 | 1 | 0 | 4 | candidates |
| **Total** | **31** | **24** | **20** | **1** | **76** | **24 parsed responses; 1 timeout** |

## Claim anchors and useful-looking sets

- **Chicago:** the model returned a police/fire/civilian set described as 2012-2017 plus a police interest-arbitration award. The agreement rows overlap the 2014-2024 observation window only at 2014-2017, and all three base-agreement links were flagged blocked. This is a legacy locator set, not a current matched set or verified source.
- **Aurora:** one apparent fire agreement and one context-only police-management record were returned. No ordinary civilian leg was returned, so Aurora did not produce a three-unit set.
- **Rockford:** the apparent 2023-2025 police, 2022-2026 fire, and 2022-2025 AFSCME rows form one of the strongest model-described overlaps, concentrated in 2023-2025. It still requires later employer, unit, execution, document, and date verification.
- **Other promising apparent matched sets:** Springfield (roughly 2022-2025, plus a police mechanism lead), Joliet (roughly 2020-2024), Bolingbrook (roughly 2020-2023), and Decatur (2023-2024, plus a later fire-award lead). Schaumburg, Belleville, Carbondale, and Quincy also produced potential partial/repeat-cycle groups, but their overlap is narrower, near or beyond the 2024 boundary, or dependent on mechanism material.
- **Incomplete municipalities:** Skokie and Normal lack an ordinary non-safety row; Des Plaines returned only non-safety; Orland Park lacks fire; Tinley Park returned only police. Elgin and Palatine returned multiple units whose model-described cycles do not form a clean mutually overlapping set. Waukegan's apparent mutual overlap is after the target window.

These are scheduling observations only. No source content was inspected to establish that a document exists, opens, is complete, binds the intended unit, or supports the dates claimed.

## Filtering and leakage review

- **Canonical/queue duplicates:** there is no exact URL overlap with the canonical corpus or pre-Illinois queue. Two Joliet police locators describe the same apparent agreement, unit, and cycle through separate Granicus/Legistar paths while both say duplicate risk `none`; this is likely within-run duplicate-locator leakage and should be deduplicated during later verification.
- **Wrong employer:** every employer field names the intended municipality. No county, school, transit, park, housing, township, or other special-district substitution is visible. Fifty-six rows retain model-level `possible` wrong-employer risk; those warnings mean later confirmation is required, not that 56 substitutions occurred.
- **Wrong unit:** no clear wrong-unit row was promoted as an ordinary candidate. Aurora's police-management item is `unclear` and context-only; Evanston's shift MOU and Moline's agenda packet are insufficient/context boundary items. Their exact unit and wage-setting role remain unverified.
- **Safety as non-safety:** no clear safety agreement is labeled non-safety. Naperville's MAP Chapter 582 row is model-described as civilian records specialists in the police department, so its non-sworn scope needs later confirmation. Springfield's municipal-utility/IUOE row also needs later confirmation that it is an appropriate ordinary municipal comparator.
- **Context and insufficiency:** 73 rows are marked qualifying, one context-only, and two insufficient. Five awards and five MOA/settlement rows remain mechanism or successor-material leads rather than automatic base-CBA substitutes.
- **Blocked versus dead:** no row is labeled dead. Six rows have `blocked_or_unreadable_flag=yes`; all six nevertheless remain labeled qualifying, including three Chicago rows marked full document. The blocked flag preserves the right distinction, but the qualifying/full labels may overstate accessibility. Queue triage therefore holds blocked rows as insufficient until later access review.
- **Parser/failure accounting:** all 24 returned responses parsed. There were no JSON/parser failures. Bloomington's failure is transport/capacity timeout with no response, not a failed parse and not a no-candidate result.

## Queue and coverage update

The normalized handoff contains 76 rows, all with `scout_stage_status=unverified_scout_candidate`. The durable national queue now contains 189 rows: PA 75, TX 6, MA 24, NJ 8, and IL 76. Illinois triage assigns 58 high, 10 medium, 2 context holds, and 6 insufficient holds; 68 Illinois rows are queued for later verification. Those scores are scheduling aids, not verification findings.

National successful scout coverage rises from 39 to 63 municipalities. Illinois has 24 successful discovery outcomes: 23 with candidates and one parseable empty response. Bloomington is recorded as `scout_attempt_failed_connection` and excluded from source-discovery coverage. The Illinois universe contains 2,719 municipal/township governments; 2,695 are not successfully covered, comprising 2,694 untouched rows plus Bloomington's failure-only row. No Illinois row is calibration-verified, later-ingest approved, canonicalized, codified, or claim-supporting.

## What should happen next

Do not retry Bloomington or open all 76 URLs automatically. Continue state-scale national scouting only under separate authorization and after a fresh direct-SDK smoke preflight. Later coordinated verification should select municipality-level sets rather than isolated high-scoring URLs, beginning with the most coherent apparent Illinois triads while explicitly resolving access, Joliet duplication, exact municipal employer and unit, executed/full-document status, visible operative dates, wage-setting content, target-window overlap, and canonical duplication. Ingestion must remain deferred until that verification gate is complete.
