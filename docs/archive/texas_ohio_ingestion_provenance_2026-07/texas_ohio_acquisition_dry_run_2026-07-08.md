# Texas/Ohio Acquisition Dry Run

**Date:** 2026-07-08
**Type:** controlled acquisition dry-run and recognition-clause-first audit. No live acquisition.

## 1. Purpose and scope

This dry-run prepares the next Texas/Ohio acquisition step for Houston, Austin, Columbus, and Cleveland. It verifies whether the approved source targets are specific enough to fetch later, records expected fetch and metadata actions, and applies the new recognition-clause-first classification rule to broad non-safety sources.

No documents were downloaded, stored, ingested, copied into `corpus/`, copied into `inbox/`, or added to any production metadata table. This run did not edit `data/contracts.csv` or `data/city_coverage.csv`.

## 2. Inputs reviewed

- `AGENTS.md`
- `PROGRESS.md`
- `docs/schema.md`
- `data/contracts.csv`
- `data/city_coverage.csv`
- `docs/analysis/chatgpt_handoff_latest.md`
- `docs/analysis/texas_ohio_final_pre_ingestion_audit_2026-07-08.md`
- `docs/analysis/texas_ohio_approved_source_plan_2026-07-08.csv`
- `docs/analysis/texas_ohio_source_ingestion_audit_2026-07-08.csv`
- `docs/analysis/texas_ohio_multicity_pre_ingestion_scan_2026-07-08.md`
- `docs/analysis/texas_ohio_multicity_source_targets_2026-07-08.csv`
- `docs/analysis/texas_ohio_legal_followup_source_audit_2026-07-08.md`
- `docs/analysis/texas_ohio_state_comparison_institutional_scan_2026-07-07.md`
- `docs/analysis/texas_ohio_candidate_source_targets_2026-07-07.csv`
- `docs/analysis/texas_ohio_legal_source_audit_2026-07-07.csv`
- Project synthesis/source-needs files listed in the task, including the Harvard Proxy context files for context only. No Harvard Proxy script was run.

## 3. Approved first-batch summary

The companion dry-run CSV has 20 rows: 15 `approved_first_batch` rows plus 5 `context_only` legal/source-discovery rows needed to interpret the batch.

Counts:

| field | counts |
|---|---|
| state | TX: 10; OH: 10 |
| city | Houston: 4; Austin: 3; Columbus: 4; Cleveland: 4; statewide: 5 |
| source_role | fire: 4; police: 4; non_safety_general: 3; budget_pay_plan: 4; legal_institutional: 4; source_discovery: 1 |
| proposed_corpus | causal: 11; context_only: 9 |
| approval_status | approved_first_batch: 15; context_only: 5 |
| dry_run_status | ready_for_live_fetch: 9; needs_url_confirmation: 5; context_only: 6 |

## 4. Fetchability check

Header-only checks were used for exact URLs where safe. No source document was downloaded or stored. The first sandboxed network attempt failed with DNS/network restriction; the same header-only checks were then run with user-approved network access.

| city | role | source target | dry-run assessment | later destination | caveat |
|---|---|---|---|---|---|
| Houston | fire | HPFFA/IAFF Local 341 CBA | Official Houston page returns HTTP 200, but the target still needs confirmation that the page links to the full executed CBA rather than only a settlement/summary page. | `corpus_direct` through open-source fetcher convention | Needs URL/document confirmation before live fetch. |
| Houston | police | HPOU Meet & Confer Agreement | Official Houston PDF returns HTTP 200 and is specific enough for later acquisition. | `corpus_direct` | Confirm final cycle metadata from document text. |
| Houston | non_safety_general | HOPE/AFSCME Local 123 meet-and-confer agreement | Official Houston PDF returns HTTP 200 and is specific enough for later acquisition. | `corpus_direct` | Recognition-clause-first review required before any narrower occupation class. |
| Houston | budget_pay_plan | Houston classification/compensation page | Official Houston page returns HTTP 200. | `context_only_no_corpus` | Context only, not a causal CBA row. |
| Austin | fire | Austin Firefighters Association Local 975 agreement | Corrected official Austin page returns HTTP 200, but the old deep link was stale and the live page now surfaces a Dec. 18, 2025 agreement link. | `corpus_direct` only after exact cycle confirmation | Needs URL/cycle confirmation for the 2014-2024 observation window. |
| Austin | police | Austin Police Association meet-and-confer agreement | Corrected official Austin page returns HTTP 200 and exposes the fully executed 2024-2029 agreement link. | `corpus_direct` | Specific enough for dry-run; confirm document metadata before writing rows. |
| Austin | budget_pay_plan | Austin classification/compensation pages | Only a general HR lookup path is confirmed. | `context_only_no_corpus` | Needs specific compensation/pay-plan URL confirmation. |
| Columbus | police | FOP Capital City Lodge No. 9 CBA | Official Columbus PDF returns HTTP 200 and is specific enough. | `corpus_direct` | Confirm metadata from document text. |
| Columbus | fire | IAFF Local 67 CBA | Official Columbus PDF returns HTTP 200 and is specific enough. | `corpus_direct` | Confirm metadata from document text. |
| Columbus | non_safety_general | AFSCME Local 1632 CBA | Official Columbus PDF returns HTTP 200 and is specific enough. | `corpus_direct` | Recognition-clause-first review required before any narrower occupation class. |
| Columbus | budget_pay_plan | HACP | Official Columbus PDF returns HTTP 200. | `context_only_no_corpus` | Context only, not a causal CBA row. |
| Cleveland | police | CPPA CBA | Official Cleveland PDF returns HTTP 200 and is specific enough. | `corpus_direct` | Confirm metadata from document text. |
| Cleveland | fire | IAFF Local 93 CBA | Official Cleveland PDF returns HTTP 200 and is specific enough. | `corpus_direct` | Confirm metadata from document text. |
| Cleveland | non_safety_general | AFSCME Ohio Council 8 Local 100 CBA | Official Cleveland PDF returns HTTP 200 and is specific enough. | `corpus_direct` | Recognition-clause-first review required before any narrower occupation class. |
| Cleveland | budget_pay_plan | Cleveland budget/pay-plan documentation | Specific URL remains unlocated. | `context_only_no_corpus` | Needs URL confirmation before any context fetch. |
| Statewide TX | legal_institutional | Texas Chapters 174, 146, 142 | Official statute pages return HTTP 200. | `context_only_no_corpus` | Legal context only; never a CBA row. |
| Statewide OH | legal_institutional | Ohio Revised Code Chapter 4117 | Official statute page returns HTTP 200. | `context_only_no_corpus` | Legal context only; never a CBA row. |
| Statewide OH | source_discovery | Ohio SERB archive | Prior archive URL returns HTTP 404. | `context_only_no_corpus` | Current archive path needs confirmation before use. |

All future live fetching still requires user approval.

## 5. Recognition-clause-first implications

Broad non-safety sources remain provisionally `occupation_class=other` until the later extraction pass reads unit coverage first.

- **Houston HOPE / AFSCME Local 123:** inspect recognition clause, bargaining-unit description, department coverage, covered classifications, wage schedule, and appendices/classification lists before any narrower classification. Provisional class: `other`.
- **Columbus AFSCME Local 1632:** inspect recognition/coverage article and classification/wage appendices before assigning a narrower class. Provisional class: `other`.
- **Cleveland AFSCME Ohio Council 8 Local 100:** inspect recognition clause, department/classification coverage, wage schedule, and appendices before assigning a narrower class. Provisional class: `other`.
- **Austin AFSCME Local 1624 backup, if later promoted:** first determine whether the consultation agreement is usable under this project's CBA standard, then inspect unit coverage before classification. Provisional class: `other`.
- **CWA/technical units, if later promoted:** do not infer class from union name. Inspect recognition and classification text first. Provisional class: `other` unless the text clearly supports a schema value.

## 6. Proposed fetch sequence

Recommended next live run, if user/PI approval is given:

1. Confirm context/legal lookup paths as needed, context-only. Do not write statutes or SERB archive pages as corpus rows.
2. Houston safety/non-safety: HPOU and HOPE are ready for a live header-checked fetch; HPFFA fire needs exact full-CBA confirmation first.
3. Austin: fetch police only after final dry-run confirmation; confirm Austin fire's exact desired cycle URL before fetching; keep Austin pay-plan as URL-confirmation work, not corpus work.
4. Columbus safety/non-safety: police, fire, and AFSCME Local 1632 are ready for controlled live fetch; HACP remains context-only.
5. Cleveland safety/non-safety: police, fire, and AFSCME Local 100 are ready for controlled live fetch; budget/pay-plan needs URL confirmation first.

A safer first live batch would fetch only the 9 `ready_for_live_fetch` agreement rows, leaving the 5 URL-confirmation rows for a short follow-up.

## 7. Guardrails for live acquisition

- Use the repo convention for open public sources: implement/confirm fetchers, dry-run them first, and only then fetch. The task's conservative "inbox first unless conventions clearly say otherwise" rule is satisfied here because `ingest/README.md` clearly routes open public portals through `ingest/fetchers/`, while licensed/FOIA material goes through `inbox/`.
- Do not write `data/contracts.csv` until source files, metadata, cycle dates, text quality, and recognition-clause classification are audited.
- Do not add budgets, pay plans, civil-service classification pages, statutes, or archive landing pages to the causal corpus.
- Do not treat legal statutes or SERB archive pages as CBAs.
- Do not classify meet-and-confer agreements as arbitration awards.
- Preserve source URLs and retrieval dates.
- Compute and store checksums if the active fetcher/pipeline convention supports it.
- Run `python scripts/validate.py` and `python ingest/audit_coverage.py` after any eventual metadata edit.
- No PRRs.
- No GABRIEL, Harvard Proxy, model/API calls, or scoring during acquisition.

## 8. Bottom-line recommendation

The project is ready for a controlled live source acquisition run after user/PI approval, but not every row should be fetched at once. The exact suggested next step is a fetcher dry-run against the 9 `ready_for_live_fetch` agreement rows, while separately confirming the Houston fire full-CBA target, Austin fire cycle-specific target, Austin pay-plan URL, Cleveland budget/pay-plan URL, and current SERB archive path.

Codex is the appropriate tool for the next mechanical fetcher dry-run and source-header verification. Claude or Codex can perform the later recognition-clause close-read, but the classification rule is now fixed: read unit coverage first, then assign any specific non-safety `occupation_class`.
