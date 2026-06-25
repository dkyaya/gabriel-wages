# Progress Log

Reverse-chronological session log. Newest entry on top. Records **decisions, surprises, and next steps** — not keystroke-level changes (git has those). Pair each entry with the git commits from that session.

Convention per entry: what we did, decisions made (and why), surprises/breakage, corpus snapshot (from `python ingest/audit_coverage.py`), next steps.

---

## 2026-06-24 - Coverage audit match-tier update

**Did**
- Updated `ingest/audit_coverage.py` so coverage health is tiered into exact-cycle, overlap-cycle, adjacent-cycle, and unmatched safety rows using `cycle_start` and `cycle_end` from `data/contracts.csv`.
- Preserved exact-cycle reporting while adding overlap-cycle healthy matches and a separate exploratory adjacent section.
- Added self-contained tests for exact, overlap, adjacent, unmatched, and Seekonk-like match cases in `ingest/test_pipeline.py`.
- Added methodological notes to `docs/hypotheses.md` and `docs/hypotheses_public_source_strategy_2026-06-24.md`.

**Decisions and why**
- Counted exact-cycle and overlap-cycle safety/non-safety comparisons as healthy because both keep city and bargaining period sufficiently fixed for H1 text/mechanism comparison.
- Kept adjacent-cycle matches out of healthy counts because they are useful for exploratory context but weaker for city x time identification.
- Left schema fields, controlled vocabularies, data rows, corpus files, and GABRIEL code/output unchanged.

**Surprises/breakage**
- The updated logic also moves Boston police 2020-2025 into overlap-cycle matched status because the Boston clerical/admin 2023-2027 CBA overlaps by date.
- No adjacent-only exploratory matches appear in the current corpus.

**Validation/test results**
```text
python ingest/test_pipeline.py
40 passed, 0 failed

python scripts/validate.py
VALIDATION PASSED - all rows conform to docs/schema.md
contracts: 20 | discourse: 0 | coverage: 20 | city_attributes: 3
```

**Corpus snapshot**
```text
contracts: 20 | discourse: 0 | coverage: 20 | city_attributes: 3 | cities: 7
healthy matched pairs: 6
  exact-cycle: 3
  overlap-cycle: 3
exploratory adjacent matches: 0
safety units unmatched: 3
```

**Next steps**
1. Exact-cycle matched cities: Worcester, Arlington, and Georgetown.
2. Overlap-cycle matched cities: Boston and Seekonk; Seekonk police and fire are now matched to overlapping administrative secretaries, teachers, public works, and library CBAs.
3. Adjacent-only exploratory matches: none in the current corpus.
4. Remaining unmatched safety units: Somerville police superior officers 2012-2018, Somerville police patrol 2012-2015, and Newton police 2015-2018.
5. v9 GABRIEL remains premature until the overlap-tier framing and source-type caveats are reviewed.
6. Discuss with the PI whether to add a historical-institutionalization caveat: low CBA/MOA comparability language may reflect settled-document opacity rather than absence of comparability in bargaining.

## 2026-06-24 - Seekonk official contract archive ingestion

**Did**
- Used only the RA-verified official Seekonk Archive Center routes, with no broad search, no PRRs, and no GABRIEL run.
- Downloaded and first-page/entity-checked six public CBA PDFs: police, fire, administrative secretaries, educators, public works, and library.
- Added explicit `inbox/manifest.csv` rows and ingested six Seekonk rows through `python ingest/process_inbox.py`: `ma_seekonk_police_2022`, `ma_seekonk_fire_2022`, `ma_seekonk_clerical_admin_2021`, `ma_seekonk_teacher_2021`, `ma_seekonk_public_works_2023`, and `ma_seekonk_library_2023`.
- Updated the school-committee recon and StateReference triage notes to treat Seekonk as an official public CBA/MOA matched-pair candidate rather than a meeting-agenda target.

**Decisions and why**
- Ingested all six listed clean documents because public works and library were easy official PDF downloads with clear unit, employer, and term metadata.
- Left wage fields blank because wage increases were not needed for this pass and should not be manually judged during metadata ingestion.
- Did not ingest Comms & Clerical, aides, custodians, maintenance, agendas, or minutes because those were outside the first-pass boundaries or classification decisions.

**Surprises/breakage**
- The administrative secretaries PDF was image-only, but local OCR succeeded well enough for entity and term verification; it was ingested with `text_quality=ocr_messy`.
- `audit_coverage.py` still flags Seekonk police and fire as unmatched because the current audit requires exact cycle-window matches. Seekonk now has overlapping same-city safety and non-safety CBAs, but not a healthy exact-cycle pair under the audit.
- No Seekonk document required manual browser download once the official archive item IDs were used.

**Validation/test results**
```text
python ingest/process_inbox.py
ingested=6 quarantined=0 missing_file=0 skipped_duplicate=11
VALIDATION PASSED - all rows conform to docs/schema.md
contracts: 20 | discourse: 0 | coverage: 20 | city_attributes: 3

python scripts/validate.py
VALIDATION PASSED - all rows conform to docs/schema.md
contracts: 20 | discourse: 0 | coverage: 20 | city_attributes: 3

python ingest/test_pipeline.py
35 passed, 0 failed
```

**Corpus snapshot**
```text
contracts: 20 | cities: 7
healthy matched pairs: 3
safety units unmatched: 6
```

**Next steps**
1. Seekonk became a clean overlapping public CBA batch, but not a healthy exact-cycle matched pair under the current coverage audit.
2. No Seekonk documents from this pass need manual download; future manual review should only revisit skipped mixed or unreviewed units if the team wants them.
3. School committee meeting packets remain lower priority for Seekonk because the contract archive was more valuable and the agenda route looked like ordinary agendas, not wage-comparison exhibits.
4. StateReference/city-portal ingestion can resume with this lesson: prioritize official portals that expose both safety and clean non-safety CBAs before StateReference-only follow-ons.
5. H1 remains viable without PRRs for one more public-only expansion pass, but the exact-cycle matching problem still matters.
6. v9 GABRIEL remains premature and was not rerun.

## 2026-06-24 - MA school committee materials recon pass

**Did**
- Reviewed the existing H1 strategy docs, schema, StateReference triage notes, and current corpus tables before doing any new work.
- Ran a narrow public-only recon pass on official school committee and district materials routes for Somerville, Newton, Boston, Georgetown, and an optional quick Seekonk route check.
- Created `docs/acquisition/ma_school_committee_meeting_materials_recon_2026-06-24.md` and added short follow-up notes to `docs/acquisition/ma_non_prr_public_source_expansion_2026-06-24.md` and `docs/hypotheses_public_source_strategy_2026-06-24.md`.

**Decisions and why**
- Treated school committee materials as proxy reasoning evidence rather than automatic contract evidence because packets, presentations, and minutes usually do not by themselves establish a causal contract row.
- Recommended one tightly scoped Newton-first packet review because Newton exposed the cleanest public archive structure and an explicit `Negotiations 2023-2024` route.
- Kept StateReference ingestion paused because this route looks more promising for the missing non-safety reasoning evidence than another immediate CBA/MOA-only ingestion pass.

**Surprises/breakage**
- Somerville’s official school committee route is stronger than expected: it exposes a public meeting-materials drive plus archived presentations, not just agendas and minutes.
- Boston’s BTU negotiations page is public and substantively useful, but the checked material looked more like bargaining narrative than explicit peer-city comparability exhibits.
- Georgetown’s school committee archives were reportedly lost during a town website change, which sharply limits its value as a packet route.
- The optional Seekonk official route failed at the TLS handshake level, so it was marked for manual browser review rather than pursued further.

**Corpus snapshot**
```text
contracts: 14 | discourse: 0 | coverage: 14 | city_attributes: 3
healthy matched pairs: 3
safety units unmatched: 4
```

**Next steps**
1. School committee materials look promising enough for one targeted public packet review, but mainly as proxy/discourse evidence rather than immediate causal-corpus ingestion.
2. The next municipality/source to test should be Newton school committee materials, especially the `Negotiations 2023-2024` archive.
3. Expected evidence split: Newton/Somerville/Boston meeting materials are more likely discourse or proxy mechanism evidence; only a final adopted agreement with clear provenance would be a causal-corpus candidate.
4. StateReference ingestion should remain paused until the Newton-first packet test shows whether public non-safety reasoning evidence is actually recoverable.
5. H1 remains viable without PRRs for one more public-only pass, but still underidentified if this packet route yields no explicit comparability materials.
6. v9 GABRIEL remains premature.

## 2026-06-24 - MA non-PRR public-source strategy pass

**Did**
- Reviewed the current H1 status, the StateReference seed/queue/triage notes, the non-safety factfinding recon, and the existing source-inventory notes.
- Ran a narrow live public-source check across StateReference, DLR Public Information Search, JLMC/DLR Mass.gov pages, Boston/Worcester/Newton public portals, Newton school committee materials, MuckRock, Internet Archive, and a public contract-archive route.
- Created `docs/acquisition/ma_non_prr_public_source_expansion_2026-06-24.md` and `docs/hypotheses_public_source_strategy_2026-06-24.md`, and added a short non-PRR update near the top of the StateReference triage note.

**Decisions and why**
- Kept H1 alive for one more structured public-only pass because public sources can still scale matched CBA/MOA pairs and may yield proxy reasoning evidence through meeting packets/exhibits even if final non-safety factfinding reports remain scarce.
- Did not recommend PRRs, per the PI preference and task boundary.
- Treated school committee meeting-materials pages as the main alternate proxy route for non-safety wage-comparability reasoning if DLR factfinding reports remain absent from the public web.

**Surprises/breakage**
- The live Newton city HR union-contracts route returned a permission block, while the Newton school contract page and school committee meeting-materials page remained public. That reinforces the need to distinguish “public in principle” from “reliably reachable.”
- The statewide MTA contracts route checked here did not expose a stable public contracts index, so local teacher-union pages remain a weaker fallback than district HR pages.
- The labor-contract archive route is public, but it visibly leans toward police/public-safety content and is less disciplined than official portals or StateReference for Massachusetts matched-pair work.

**Corpus snapshot**
```text
contracts: 14 | discourse: 0 | coverage: 14 | city_attributes: 3
healthy matched pairs: 3
safety units unmatched: 4
```

**Next steps**
1. Next public-source families to investigate beyond StateReference: DLR Public Information Search exact-route checks, school committee meeting-materials archives, and large-city labor portals.
2. Most promising family for non-safety reasoning documents: school committee meeting materials and bargaining exhibits; DLR factfinding remains conceptually ideal but publicly thin.
3. More CBA/MOA pair ingestion is justified only after a short pre-download verification pass, with Seekonk still the best remaining candidate.
4. H1 remains viable without PRRs, but only as a public-only structured pass rather than an immediate measurement run.
5. Pivot hypotheses to keep alive: source-type/document-production, arbitration-backstop, wage-MOA opacity, and public-availability selection.
6. v9 GABRIEL remains premature.

## 2026-06-24 - MA StateReference triage pass

**Did**
- Paused live StateReference ingestion work and reviewed the saved seed memo, follow-on queue note, schema, current corpus tables, manifest, and staged `inbox/foia` PDFs.
- Added a staged-file disposition section to `docs/acquisition/ma_phase1_statereference_ingestion_queue_2026-06-23.md` for the Hanover and Peabody follow-on PDFs that were downloaded but never ingested.
- Created `docs/acquisition/ma_statereference_phase1_triage_2026-06-23.md` with a municipality-level classification table, a capped next-wave list, and a separate large-municipality queue.

**Decisions and why**
- Shifted from candidate-by-candidate ingestion attempts to classification-first triage because the last follow-on wave showed too many failure modes: wrong jurisdiction, no same-cycle counterpart, dispatcher ambiguity, and mixed units.
- Kept Georgetown as the proof-of-concept clean pair but treated its `other` comparator as analytically secondary; the next wave should prioritize cleaner `clerical_admin`, `public_works`, or `teacher` targets where possible.
- Left staged PDFs in place because the repo has no established StateReference scratch/review convention beyond a one-off `DISCARD_` prefix for confirmed rejects.

**Surprises/breakage**
- The Hanover school-side staged PDF was easy to rule out once re-read locally: the first page names the Dresden and Hanover School Districts, confirming the wrong-jurisdiction failure without any new web work.
- The staged Peabody Local 365 OCR confirms a broad all-non-teaching school unit, which strengthens the case for classifying Peabody as mixed rather than merely incomplete.
- No pipeline/test runs were needed because no ingestion logic or data rows changed.

**Corpus snapshot**
```text
contracts: 14 | discourse: 0 | coverage: 14 | city_attributes: 3
healthy matched pairs: 3
safety units unmatched: 4
```

**Next steps**
1. Top candidates for a future targeted ingestion prompt: Seekonk first; Woburn, Marlborough, Reading, and Great Barrington only after counterpart verification.
2. Ambiguous or mixed-unit candidates: Peabody, Georgetown DPW/clerical, Boxford, Millis, Gloucester, and any dispatcher-adjacent Lexington/Danvers records.
3. Large-city candidates needing separate handling: Springfield, Cambridge, Boston, Worcester, and Lynn.
4. Staged PDFs needing manual disposition: Hanover fire keep-only-if-paired later; Hanover school files discard after confirmation; Peabody files retain only for manual class/entity review.
5. PRRs still deferred.
6. v9 GABRIEL still premature.

## 2026-06-23 - MA StateReference follow-on batch

**Did**
- Continued the StateReference public-source pass after Georgetown and reviewed the current Georgetown rows in `data/contracts.csv` and `data/city_coverage.csv`.
- Verified Hanover, Peabody, Reading, Marlborough, and Danvers using targeted StateReference item pages and search results.
- Downloaded and locally staged Hanover and Peabody originals/OCRs for verification; no new rows were ingested.
- Updated `docs/acquisition/ma_phase1_statereference_ingestion_queue_2026-06-23.md` with this wave’s attempted municipalities, statuses, and classification lessons.

**Decisions and why**
- Rejected Hanover because the school-side record is for the Dresden and Hanover School Districts in New Hampshire, so it is not a same-Massachusetts-municipality comparator.
- Rejected Reading and Marlborough because clean safety or non-safety singles exist, but not a same-cycle matched pair.
- Rejected Danvers because the targeted search surfaced only AFSCME units and dispatchers, not a police/fire contract; dispatchers remain outside the safety classes in this schema.
- Treated Peabody as ambiguous rather than cleanly ingestable: the police contract is fine, but the available school comparator is a mixed school-unit record covering cafeteria, clerks, and transportation, which is public and relevant but not a preferred single occupation class.
- Kept Georgetown's `other` comparator as acceptable but secondary. It is valid for coverage and pair formation, but the next batch should prefer cleaner `clerical_admin`, `public_works`, or `teacher` comparators when available.

**Surprises/breakage**
- The first Peabody/Reading search attempts hit sandbox DNS failures and had to be retried with approved public `curl` access.
- No ingestion pipeline run was needed because nothing new passed the clean-pair threshold.

**Corpus snapshot**
```text
contracts: 14 | discourse: 0 | coverage: 14 | city_attributes: 3
healthy matched pairs: 3
safety units unmatched: 4
```

**Next steps**
1. Clean StateReference candidates still ready for targeted verification: none from the attempted top five; only later candidates if the team relaxes the stop rule.
2. Ambiguous candidates needing manual review: Peabody.
3. PRR-only targets remain deferred.
4. v9 GABRIEL remains premature.

## 2026-06-23 - MA StateReference Georgetown pilot

**Did**
- Read and preserved `docs/acquisition/ma_statereference_phase1_seed_2026-06-23.md`.
- Verified three Georgetown StateReference DLR Contracts records and confirmed each had a visible public document attachment plus DLR Public Information Search original-source route.
- Downloaded original plus StateReference OCR PDFs for police command staff, DPW/clerical, and school custodians:
  - `inbox/foia/ma_georgetown_police_command_staff_2020_2023.pdf`
  - `inbox/foia/ma_georgetown_police_command_staff_2020_2023_ocr.pdf`
  - `inbox/foia/ma_georgetown_afscme_dpw_clerical_2020_2023.pdf`
  - `inbox/foia/ma_georgetown_afscme_dpw_clerical_2020_2023_ocr.pdf`
  - `inbox/foia/ma_georgetown_afscme_custodians_2020_2023.pdf`
  - `inbox/foia/ma_georgetown_afscme_custodians_2020_2023_ocr.pdf`
- Added explicit `obs_id` values to `inbox/manifest.csv` so `process_inbox.py` does not reprocess existing arbitration-award manifest rows under inferred duplicate IDs.
- Ingested two Georgetown rows through `python ingest/process_inbox.py`: `ma_georgetown_police_2020` and `ma_georgetown_other_2020`.
- Added processed OCR PDFs to:
  - `corpus/ma_georgetown/ma_georgetown_police_command_staff_2020_2023_ocr.pdf`
  - `corpus/ma_georgetown/ma_georgetown_afscme_custodians_2020_2023_ocr.pdf`
- Created `docs/acquisition/ma_phase1_statereference_ingestion_queue_2026-06-23.md`.
- Ran `python scripts/validate.py`, `python ingest/audit_coverage.py`, and `python ingest/test_pipeline.py`.

**Decisions and why**
- Coded Georgetown police command staff as `police` because the recognition clause covers Lieutenant, Sergeant, and Detective Sergeant and excludes patrolmen, dispatchers, chief, confidential, managerial, and other town employees.
- Coded Georgetown school custodians as `other` because the current controlled vocabulary has no custodial or school maintenance class; the recognition clause cleanly identifies custodians, matrons, and maintenance employees.
- Did not ingest Georgetown DPW/clerical because the recognition clause mixes Fire or Police Signal Operators, highway/DPW titles, and clerical/admin titles, so it is not a clean single occupation-class observation.
- Did not attempt Seekonk in this pass because Georgetown produced a new healthy matched pair and the task was deliberately narrow.

**Surprises/breakage**
- The original StateReference Georgetown PDFs were image-only. StateReference OCR PDFs were downloaded and used for ingestion; originals remain staged locally for provenance review.
- `process_inbox.py --dry-run` showed that old Somerville arbitration-award rows would be treated as new without explicit manifest `obs_id` values. The manifest metadata was tightened before the real run.
- The final `git status --short` still includes unrelated pre-existing changes outside this StateReference pilot, including GABRIEL files, graph deletions, prior docs, and logs. The StateReference-scoped changes are the Georgetown data/coverage/manifest rows, Georgetown corpus and inbox PDFs, the new queue note, and this PROGRESS entry.

**Validation**
```text
python ingest/process_inbox.py
ingested=2 quarantined=0 missing_file=0 skipped_duplicate=9
VALIDATION PASSED - all rows conform to docs/schema.md
contracts: 14 | discourse: 0 | coverage: 14 | city_attributes: 3

python scripts/validate.py
VALIDATION PASSED - all rows conform to docs/schema.md
contracts: 14 | discourse: 0 | coverage: 14 | city_attributes: 3

python ingest/test_pipeline.py
35 passed, 0 failed
```

**Corpus snapshot**
```text
contracts: 14 | discourse: 0 | coverage: 14 | city_attributes: 3
healthy matched pairs: 3
safety units unmatched: 4
```

**Next steps**
1. More public StateReference candidates ready for targeted verification: Hanover, Peabody, Reading, Marlborough, Danvers, Lexington, Springfield, Woburn, Manchester, and Great Barrington.
2. Candidates needing manual verification: Georgetown DPW/clerical mixed unit; any dispatcher or signal-operator record; any school committee comparator whose occupation class is not obvious from the recognition clause.
3. PRR-only targets remain deferred; no PRRs were drafted or submitted.
4. v9 GABRIEL remains premature unless the team explicitly wants a CBA-panel run after reviewing the new Georgetown pair.

## 2026-06-23 — MA non-safety factfinding records-request packet

**Did**
- Confirmed `docs/acquisition/ma_non_safety_factfinding_recon_2026-06-23.md` exists and preserved it without substantive edits.
- Added a concise "Targeted recon follow-up" section to `docs/acquisition/ma_non_safety_awards_2026-06-23.md`.
- Created `docs/records_requests/ma_non_safety_factfinding_packet_2026-06-23.md` with DLR, Somerville, Boston, and Newton public-records request drafts; a manual DLR exact-search checklist; an intake checklist; and a request tracking table.
- Ran `python scripts/validate.py` and `python ingest/audit_coverage.py`.

**Decisions and why**
- Kept this as documentation/request prep only. No PDFs were downloaded, no corpus files were staged, and no data rows were added because no final non-safety factfinding report or interest-arbitration award is ready for ingestion.
- Put DLR first in the request sequence because the concrete docket leads and no-record confirmations are the cheapest way to distinguish final reports from petitions, strike rulings, ULP decisions, and representation decisions.
- Put Somerville first among city/school RAO targets because its two high-scoring police awards remain the most important current document-type confound.

**Surprises/breakage**
- None. The recon memo was present, so no fallback search or reconstruction was needed.
- `ingest/test_pipeline.py` was not run because no code or ingestion logic changed.

**Corpus snapshot**
```text
contracts: 12 | discourse: 0 | coverage: 12 | city_attributes: 3
healthy matched pairs: 2
safety units unmatched: 4
```

**Next steps**
1. Submit manually first: DLR master request, then Somerville city/school request, then Boston BTU `PS-17-5987` and Newton custodians/NTA verification requests.
2. Process returned records only after full documents are local: save under `inbox/foia/`, complete manifest metadata, first-page/entity-check the source, verify `source_type`, then use the ingestion pipeline.
3. v9 GABRIEL is still not justified until at least one genuine non-safety factfinding or interest-arbitration document is ingested and validated.

---

## 2026-06-23 — MA non-safety factfinding acquisition queue

**Did**
- Ran the required schema and coverage checks before editing: `scripts/validate.py` passed, and `ingest/audit_coverage.py` still reports 12 contracts, 5 cities, 2 healthy matched pairs, and 4 unmatched safety observations.
- Audited the current Massachusetts gap: Somerville, Boston, and Newton are the highest-value non-safety factfinding targets because their current safety rows are award-heavy and not same-cycle matched to non-safety award-style documents.
- Created `docs/acquisition/ma_non_safety_awards_2026-06-23.md` with a priority gap table, candidate/search-lead table, source-route notes, and manual-download/metadata instructions.
- Checked targeted official/public routes: Mass.gov JLMC decisions, Mass.gov DLR search/API results, and FY2015/FY2016/FY2024 DLR annual reports.

**Decisions and why**
- Did not add `contracts.csv` rows. No genuine non-safety factfinding or arbitration PDF was locally present, source-type verified, and ready for ingestion.
- Treated the Mass.gov JLMC page as safety-only. It is useful for future police/fire award targets, but it cannot provide non-safety comparators.
- Prioritized Somerville first because two police observations remain unmatched and a teacher/clerical factfinding report would directly test whether high Gabriel language is driven by safety status or award-document form.
- Treated the Newton Teachers Association 2023-2024 impasse trail as a future Newton-2025 pairing lead, not a comparator for the current 2015-2018 Newton police row.

**Surprises/breakage**
- Mass.gov search is a JavaScript app, but its official search API was usable with the public site referrer.
- Official hits were mostly DLR hearing-officer, CERB, prohibited-practice, representation, or strike-petition records rather than wage factfinding reports.
- DuckDuckGo HTML returned an anti-bot challenge during exact searches, so it was not used as an acquisition route.
- Three DLR annual-report PDFs were downloaded to `/tmp` for audit only; no source PDFs were staged in the corpus or inbox.

**Corpus snapshot**
```text
contracts: 12 | discourse: 0 | coverage: 12 | city_attributes: 3
healthy matched pairs: 2
safety units unmatched: 4
```

**Next steps**
1. Manual downloads still needed: Somerville teacher/SMEA DLR factfinding if it exists; Newton NTA 2023-2024 factfinding or binding-arbitration output if produced; Boston SENA/BTU non-safety factfinding if available.
2. Documents ready for ingestion: none.
3. v9 rerun: not justified until at least one genuine non-safety factfinding/arbitration document is ingested and validated.

---

## 2026-06-23 — GABRIEL v8 quote-quality hardening for comparability

**Did**
- Updated `analysis/gabriel_pilot/run_gabriel.py` for v8: default output is now `results_v8.csv`; v7 outputs are untouched.
- Added one bounded retry call per document for initially verbatim-failed excerpts. Retry replacements must pass the same `_verify_verbatim` guard before relevance classification.
- Tightened relevance handling: only verbatim + relevant excerpts enter `supporting_quotes`/`estimated_pages`; verbatim-but-irrelevant excerpts remain in `flagged_quotes`/`flagged_pages` as audit trail.
- Added v8 count columns: `excerpts_retry_attempted`, `excerpts_retry_recovered`. Existing v7 count columns are preserved; `excerpts_failed` now means final unrecovered verbatim failures after retry.
- Codified the wage-specific boundary in prompt/rules/tests/docs: wage/salary/pay/total-comp/benefit/longevity-pay peer comparisons can count; generic non-wage provision charts and generic cross-community variation are flagged/ignored.
- Added synthetic relevance-helper tests to `ingest/test_pipeline.py`.
- Ran GABRIEL v8 on 12 documents. Output: `analysis/gabriel_pilot/results_v8.csv`.

**V7 → V8 quote-count comparison (SPSOA/SPEA)**
| doc_id | v7 score | v8 score | v7 sub/rel/flag/fail | v8 sub/rel/flag/fail | v8 retry attempted/recovered |
|---|---:|---:|---:|---:|---:|
| `ma_somerville_police_spsoa_2012` | 92 | 92 | 4 / 2 / 2 / 0 | 6 / 4 / 2 / 0 | 0 / 0 |
| `ma_somerville_police_spea_2012` | 82 | 85 | 5 / 2 / 2 / 1 | 5 / 2 / 3 / 0 | 1 / 1 |

**Decisions (and why)**
- Retry does not change scores. It only repairs quote provenance, because scores should reflect the original document-level judgment, not whether a support quote was recovered.
- Relevance failures are explicit audit records, not support. This keeps irrelevant-but-real text out of verified support counts while preserving traceability.
- The longevity-pay boundary is wage-specific: prose comparing pay levels across communities can support H1; generic charts/tables that merely show variation are not support.

**Surprises / breakage**
- The first v8 command failed under sandboxed network access with connection errors and wrote an all-error `results_v8.csv`; reran with approved network access and overwrote it with the completed v8 run.
- After final helper tightening, reran v8 again so `results_v8.csv` matches the final code.
- Retry recovered 1 of 1 attempted Somerville failed excerpts in the final run, eliminating unrecovered verbatim failures there; this is useful but too small to prove retries solve persistent long-form award paraphrases.
- SPEA produced one additional flagged/ignored excerpt under the stricter boundary while preserving 2 relevant support excerpts and a high score.

**Tests / validation**
- `python ingest/test_pipeline.py` — 35 passed, 0 failed.
- `python scripts/validate.py` — passed.
- `python ingest/audit_coverage.py` — passed and produced the snapshot below.

**Corpus snapshot**
```
contracts: 12 | discourse: 0 | coverage: 12 | city_attributes: 3
healthy matched pairs: 2
safety units unmatched: 4
```

**Next steps**
1. Acquire non-safety arbitration awards; this remains the primary H1 gap needed to separate occupation effects from document-type effects.
2. Treat persistent Somerville long-form award paraphrase failures as a known quote-recovery limitation unless future runs show retries materially improve relevant support.
3. If v8 outputs are used in downstream summaries, report `excerpts_relevant` as verified support and `excerpts_flagged`/`flagged_quotes` only as audit evidence.

---

## 2026-06-22 — Port LLM fallback to OpenAI/Harvard; add AGENTS.md for Codex

**Did**
- Added `AGENTS.md` at repo root — identical copy of `CLAUDE.md`. Both files coexist so either Claude Code or Codex can read project instructions.
- Rewrote `ingest/extract_spans.py` `llm_pass()` to use the Harvard HUIT OpenAI proxy instead of the Anthropic API. Changes: env var `ANTHROPIC_API_KEY` → `HARVARD_SUBSCRIPTION_KEY`; `import anthropic` → `from openai import OpenAI`; Harvard endpoint + header pattern (same as `run_gabriel.py`); `client.chat.completions.create()` + `resp.choices[0].message.content`; `max_completion_tokens` (required by gpt-5.4-nano as a reasoning model); default model `claude-sonnet-4-6` → `gpt-5.4-nano`. Prompt content and `_verify_verbatim` anti-paraphrase guard left exactly unchanged.
- Updated `ingest/README.md` "LLM fallback setup" section: replaced `ANTHROPIC_API_KEY` / `claude-sonnet-4-6` with `HARVARD_SUBSCRIPTION_KEY` / `gpt-5.4-nano`; noted that the fallback now uses the same credential as the GABRIEL scripts.
- Updated root `README.md` "Added dependencies" section: replaced `anthropic` package / `ANTHROPIC_API_KEY` with `openai` / `HARVARD_SUBSCRIPTION_KEY`.
- Updated `requirements.txt`: removed `anthropic>=0.39`; added `openai>=1.0` (was already installed for GABRIEL scripts but not listed here).
- Confirmed no remaining `anthropic` / `ANTHROPIC_API_KEY` references outside of the historical 2026-06-15 PROGRESS.md entry (correct — not edited).

**Decisions (and why)**
- Unified credential: the project previously needed two separate API keys (`ANTHROPIC_API_KEY` for ingest, `HARVARD_SUBSCRIPTION_KEY` for GABRIEL). The fallback was already optional and off-by-default; porting it to the same Harvard endpoint removes the only remaining Anthropic dependency, simplifying setup and keeping all LLM calls on the institutional proxy.
- `gpt-5.4-nano` chosen for consistency with `run_gabriel.py` (same model in active use; same proxy; same pricing). The model is a reasoning model so `max_completion_tokens` replaces `max_tokens`.
- AGENTS.md is a verbatim copy of CLAUDE.md — no content divergence between the two agent instruction files.

**Surprises / breakage**
- None. `reportlab` was not installed in the active environment (needed by `test_pipeline.py` to build synthetic PDFs); installed it and all 26 tests passed. `scripts/validate.py` passed clean (corpus unchanged).

**Corpus snapshot** (unchanged)
```
contracts: 12 | discourse: 0 | coverage: 12 | city_attributes: 3
healthy matched pairs: 2
safety units unmatched: 4
```

**Next steps**
- (Unchanged from session 9.)

---

## 2026-06-19 (session 9) — v7 run: prompt exclusions + relevance re-check; DPW 2018 fixed

**Did**
- Added three new exclusion rules to `run_gabriel.py` PROMPT_TEMPLATE, extending the COLA/CPI note:
  1. "market adjustment" does not count as comparability unless text explicitly states the adjustment is based on wages paid by OTHER employers/jurisdictions.
  2. Bargaining unit names/abbreviations (e.g. "AFSCME: MC", "Local 490") are NOT peer jurisdictions.
  3. Award-outcome sentences (e.g. "the Panel awards X% for FY2014") are NOT comparability reasoning unless the same sentence also states the comparative justification.
- Added two-stage relevance check on verbatim-verified excerpts:
  - Stage 1 (rule-based): `_is_clearly_relevant` (keyword list) → pass; `_is_clearly_irrelevant` (award-outcome/market-adj/ruling-conclusion patterns) → flag; else ambiguous.
  - Stage 2 (model): ambiguous excerpts sent to model for binary yes/no relevance judgment.
  - Flagged excerpts (verbatim-pass, relevance-fail) go to `flagged_quotes`/`flagged_pages`; they are NOT silently discarded. New output columns: `excerpts_relevant`, `excerpts_flagged`.
- Fixed `max_completion_tokens`: raised 2000 → 4000 after first run failed on SPEA (SPEA at 256K chars + longer prompt exhausted the 2000-token cap).
- Fixed `_RELEVANCE_STRONG`: added curly-apostrophe variant of `"that city's or town's"` to catch the Arlington fire "outside detail rate" clause (PDF used curly apostrophes; the keyword was a straight apostrophe → match failed on first run).
- Updated `docs/hypotheses.md` H1 measurement boundary: documented that verbatim verification confirms quotes are REAL but not RELEVANT; described both failure modes found in v6 (market-adjustment label + award-outcome sentence).
- Ran GABRIEL v7 on 12 documents (second clean run after fixes). Output: `results_v7.csv`.

**V6 → V7 comparison**
| doc_id | v6 score | v7 score | Δ | sub | rel | flag | fail |
|--------|---------|---------|---|-----|-----|------|------|
| worcester_fire_2017 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| worcester_clerical_admin_2017 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| worcester_public_works_2017 | 5 | 10 | +5 | 2 | 0 | 1 | 1 |
| boston_police_2020 | 0 | 6 | +6 | 0 | 0 | 0 | 0 |
| boston_clerical_admin_2023 | 8 | 5 | −3 | 0 | 0 | 0 | 0 |
| **somerville_police_spsoa_2012** | **88** | **92** | **+4** | **4** | **2** | **2** | **0** |
| somerville_police_spea_2012 | 82 | 82 | 0 | 5 | 2 | 2 | 1 |
| arlington_fire_2021 | 25 | 30 | +5 | 1 | 1 | 0 | 0 |
| arlington_public_works_2015 | 0 | 8 | +8 | 0 | 0 | 0 | 0 |
| **arlington_public_works_2018** | **25** | **10** | **−15** | **0** | **0** | **0** | **0** | ← FIXED |
| arlington_public_works_2021 | 0 | 5 | +5 | 0 | 0 | 0 | 0 |
| newton_police_2015 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

**Arlington DPW 2018 — false positive fixed**
Score dropped 25 → 10. The model submitted 0 excerpts: the new exclusion rules ("market adjustment" without explicit external employer reference; bargaining unit abbreviations are not peer jurisdictions) caused the model not to treat the "AFSCME: MC market adjustment" passages as comparability evidence. Score 10 is in the 0–15 "no comparability" band — plausible; the document has internal salary schedule changes only. The v4 score (12) and v5 score (10) bracketed this same range; v6's 25 was the anomaly.

**SPSOA — 2 confirmed relevant excerpts; 2 correctly flagged**
Score increased 88 → 92 (still firmly in the 71–100 "primary justification" range). 4 submitted, 2 verbatim-pass + relevant, 2 verbatim-pass + flagged:
- RELEVANT [1]: "In the Police Arbitration Award the Panel decided to review a listing of comparable communities that was utilized by the Collins Center..." (genuine comparability frame)
- RELEVANT [2]: "The evidence further demonstrates that the overall compensation (including wages and benefits) provided to Somerville Police Superiors, although not the same, is comparable to what is provided to poli[ce in other communities]" (direct wage comparison)
- FLAGGED [1]: "The parties' proposals on wages and duration are as follows: CITY'S POSITION..." (proposals table, not comparability reasoning) → escalated to model, flagged
- FLAGGED [2]: "AWARD – DURATION & WAGE INCREASES... FY 2013 – 2.5%, FY 2014 – 2%..." → caught by `_is_award_outcome` rule (FY-year + percentage pattern with no comparability keywords)
The v6 run had 6 verified excerpts; v7 has 2 relevant + 2 flagged from 4 submitted. The model selected different excerpts this run (expected variance). The primary finding — high score, genuine comparability justification — is unaffected.

**SPEA — 2 confirmed relevant excerpts; 2 correctly flagged; 1 verbatim-fail**
Score: 82 (unchanged from v6).
- RELEVANT [1]: "wages and benefits of comparable towns" (criterion citation in panel reasoning)
- RELEVANT [2]: "when reviewing longevity payments in other communities the longevity pay for Somerville Police is lower than that provided in other communities, such as Boston, and Lynn." (cross-community comparison, wages tangential but present)
- FLAGGED [1]: "The chart demonstrates that longevity payments vary from community to community..." (cross-community comparison but about payment structure, not wage levels → model escalated, flagged)
- FLAGGED [2]: "As the chart shows alcohol testing for public safety officers is not an unusual contract provision: Community / Alcohol Testing / Arlington / Yes..." (comparison of non-wage contract provisions → model escalated, flagged)
The v6 padding excerpts (FY wage announcement; longevity ruling conclusion) were not submitted in v7 — the new prompt exclusions changed the model's excerpt selection.

**Arlington fire 2021 — outside-detail rate excerpt fixed**
Score: 25 → 30 (minor; still in 16–40 "mentioned in passing" band). The outside-detail rate excerpt ("paid at that city's or Town's outside detail rate") is now correctly classified as RELEVANT. In v7 run 1 it was incorrectly flagged because the PDF uses curly apostrophes (') while `_RELEVANCE_STRONG` only had a straight apostrophe ('). Fixed by adding both variants to the keyword list.

**Relevance check — 4 model escalations (clean run)**
4 excerpts across the 12 documents were ambiguous (not caught by rule-based positive or negative checks) and escalated to the model: 1 from SPSOA (proposals table → flagged), 1 from SPEA (longevity chart → flagged), 1 from SPEA (alcohol testing table → flagged), 1 from Worcester public works (new salary step → flagged). All 4 model escalations returned "no" (not peer-wage comparability). No escalations returned "yes" in this run — the ambiguous excerpts were genuinely borderline-to-irrelevant.

**Spend (v7)**
```
v7 run 1 (failed, SPEA max_tokens): 16 calls, 241,076p + 2,326c = $0.0511
v7 run 2 (clean):                   16 calls, 241,089p + 2,731c = $0.0516
──────────────────────────────────────────────────────────────────────────
v7 total (both runs):                           482,165p + 5,057c = $0.1028

Cumulative (v3–v7, all runs): ~$0.2999  [ESTIMATE — public list pricing; Harvard billed rate may differ]
```
The doubled cost for v7 (two runs) reflects the debugging run needed when SPEA hit the 2000-token cap. The clean run alone ($0.0516) is the marginal cost per 12-document pass.

**Corpus snapshot** (unchanged)
```
contracts: 12 | discourse: 0 | coverage: 12 | city_attributes: 3
healthy matched pairs: 2
safety units unmatched: 4
```

**Next steps**
1. The verbatim-fail rate for SPSOA and SPEA is persistent (model submits paraphrases for some excerpts). Consider whether to add a "re-submit failed excerpts with stricter verbatim instruction" retry loop, or accept that long-form awards will have some verbatim-fail excerpts alongside genuine ones.
2. SPEA's RELEVANT [2] (longevity pay in other communities) and FLAGGED [1] (longevity chart) are both legitimate cross-community observations but differ in whether they reference wages specifically. The current rule (model escalation) flagged the chart but passed the prose version — that distinction seems right but is model-dependent.
3. Non-safety arbitration awards remain the primary corpus gap for the H1 test.

---

## 2026-06-19 (session 8) — v6 run: multi-excerpt schema; SPSOA breakthrough; DPW 2018 flag

**Did**
- Rewrote `run_gabriel.py` SYSTEM prompt to request a list of up to 10 independent verbatim excerpts rather than a single quote. Each excerpt is 1-2 consecutive sentences from a single contiguous passage; excerpts may come from different parts of the document. Each verified separately via `_verify_verbatim`. Output columns changed from `supporting_quote`/`estimated_page` (strings) to `supporting_quotes`/`estimated_pages` (JSON-encoded lists) plus `excerpts_submitted`/`excerpts_verified`/`excerpts_failed` counts.
- Added correction note to session 5 PROGRESS.md entry for v3 cost ($0.036 → $0.048180).
- Ran GABRIEL v6 on 12 documents. Output: `results_v6.csv`.

**V6 excerpt counts (submitted → verified)**
| doc_id | v5 score | v6 score | Δ | submitted | verified | failed |
|--------|---------|---------|---|-----------|----------|--------|
| worcester_fire_2017 | 0 | 0 | 0 | 0 | 0 | 0 |
| worcester_clerical_2017 | 0 | 0 | 0 | 0 | 0 | 0 |
| worcester_public_works_2017 | 0 | 5 | +5 | 0 | 0 | 0 |
| boston_police_2020 | 5 | 0 | −5 | 0 | 0 | 0 |
| boston_clerical_2023 | 5 | 8 | +3 | 0 | 0 | 0 |
| **somerville_spsoa_2012** | 80 | **88** | +8 | **6** | **6** | **0** |
| somerville_spea_2012 | 75 | 82 | +7 | 9 | 7 | 2 |
| arlington_fire_2021 | 25 | 25 | 0 | 1 | 1 | 0 |
| arlington_dpw_2015 | 0 | 0 | 0 | 0 | 0 | 0 |
| **arlington_dpw_2018** | 10 | **25** | **+15** | **2** | **2** | **0** | ← FLAG |
| arlington_dpw_2021 | 0 | 0 | 0 | 0 | 0 | 0 |
| newton_police_2015 | 12 | 0 | −12 | 0 | 0 | 0 |

**SPSOA: breakthrough — 6 verified, all genuine**
All 6 excerpts passed verification and are substantively distinct comparability passages. Pages 51, 52, 56, 57, 60 — spread across the comparability analysis section. Example:
- p.52: *"The City argues that the wages and benefits of Somerville Superior Officers compare well with their counterparts in other comparable communities, and that Somerville Superior Officers rank at the top in terms of total compensation."*
- p.57: *"The Union's wage proposal for the last three years... is well above the base wage increases that have been agreed to in comparable communities. There is, therefore, no justification for increases of this magnitude..."*

No padding. Each excerpt covers a distinct analytical point (city argument vs. union argument vs. rank differential vs. award reasoning). Score increase 80→88 reflects the model now reading the full comparability section and registering how heavily it dominates the award's reasoning.

**SPEA: 7 verified, 2 padding detected**
7 of 9 submitted excerpts passed verification. Of the 7 verified, 5 are genuine comparability language. Two are padding:
- p.64 excerpt: *"The Panel Awards wage increases for the three-year period: FY 2013 – 2.5%, FY 2014 – 2%, FY 2015 – 2%"* — This is the award outcome, not comparability reasoning. Verbatim and verifiable, but not evidence of comparability language.
- p.77 excerpt: *"Accordingly, based on totality of facts there is insufficient justification to change the current longevity payments at this time."* — A ruling conclusion about longevity, not peer-wage comparison language.
Score (82) is still supported by the 5 genuine excerpts. Padding doesn't change the score, but it dilutes excerpt quality if used for annotation.

**Arlington DPW 2018: FLAG — score increase likely false positive**
Score jumped 10→25 with 2 verified excerpts about "market adjustment of 35 cents / 20 cents to the top step of AFSCME: MC, Office Administrative." These passages are NOT peer-wage comparability:
- "AFSCME: MC" is the bargaining unit abbreviation (AFSCME Municipal Council), not a reference to another municipality or peer wages.
- "Market adjustment" here means an internal salary table correction, not a comparison to wages paid elsewhere.
- The v5 score (10, BACPI-adjacent) and the v4 score (12) are more plausible than 25.
**Do not treat the v6 score of 25 for Arlington DPW 2018 as validated.** The model correctly extracted verbatim text but misread "market adjustment" as peer-wage comparability. The excerpts should be reviewed before use.

**Low-scoring documents — no padding problem**
All 8 documents scoring 0–8 returned 0 excerpts. The anti-padding instruction held: worcester fire, clerical, dpw (5, 0 excerpts), boston police, boston clerical (8, 0 excerpts), arlington dpw 2021, newton police all returned empty excerpt lists. None of these showed the 3+ excerpt inflation the task specified as the failure mode.

**v5 vs v6 cost**
```
v5: 237,891 prompt + 1,504 completion = $0.0495
v6: 238,923 prompt + 2,207 completion = $0.0505  (+703 completion tokens, +47%)
Difference: +$0.0010 for 12 documents
```
Completion tokens increased 47% (expected — model now writes multiple excerpts per document). Cost increase is negligible (~$0.001 per run). The 2,000-token `max_completion_tokens` cap was not hit.

**Corrected cumulative spend (v3–v6, all scripts):**
```
v3 (backfill, corrected): $0.048180
v4 (live):                $0.049001
v5 (live):                $0.049458
v6 (live):                $0.050543
────────────────────────────────────
Total:                    $0.1972  [ESTIMATE — public list pricing; Harvard billed rate may differ]
```

**Corpus snapshot** (unchanged)
```
contracts: 12 | discourse: 0 | coverage: 12 | city_attributes: 3
healthy matched pairs: 2
safety units unmatched: 4
```

**Next steps**
1. Arlington DPW 2018 excerpt review: confirm whether "AFSCME market adjustment" language qualifies as comparability. If not, add "market adjustment" to the COLA/non-comparability note in the prompt.
2. SPEA padding: consider adding a filter to strip excerpts that are purely award-outcome sentences (no comparability language in the text itself).
3. Non-safety arbitration awards remain the primary corpus gap for the H1 test.

---

## 2026-06-19 (session 7) — v5 run: contiguous quote constraint + COLA clarification; spend log backfill

**Did**
- Task 1: Tightened quote request in `run_gabriel.py` SYSTEM prompt from open-ended "sentence(s)" to "ONE to TWO consecutive sentences from a SINGLE CONTIGUOUS PASSAGE." Blocks the synthesis failure mode where the model stitches non-adjacent fragments.
- Task 2: Added explicit COLA/CPI boundary to `PROMPT_TEMPLATE`: "cost-of-living index adjustments (CPI, BACPI, or similar) are NOT comparability language — they reference a price index, not other workers' wages." Also added the same clarification to `docs/hypotheses.md` under H1 as a permanent measurement boundary note.
- Task 3: Backfilled v3 run to `logs/api_spend_log.csv` as a manually-flagged row (`run_gabriel.py[v3-backfill]`). Recomputed cost at correct pricing: $0.048180 (v3 PROGRESS.md had reported $0.036 using the old $0.15/$0.60 rate; correct rate is $0.20/$1.25).
- Ran GABRIEL v5 on 12 documents. Output: `results_v5.csv`.

**V4 vs V5 comparison**

| doc_id | v4 score | v5 score | Δ | v4 quote | v5 quote | v5 page |
|--------|---------|---------|---|---------|---------|---------|
| worcester_fire_2017 | 0 | 0 | 0 | N | N | — |
| worcester_clerical_2017 | 0 | 0 | 0 | N | N | — |
| worcester_public_works_2017 | 0 | 0 | 0 | N | N | — |
| boston_police_2020 | 10 | 5 | −5 | N | N | — |
| boston_clerical_2023 | 0 | 5 | +5 | N | FAIL | — |
| somerville_spsoa_2012 | 80 | 80 | 0 | FAIL | FAIL | — |
| somerville_spea_2012 | 78 | 75 | −3 | Y | Y | p.60 |
| arlington_fire_2021 | 10 | 25 | +15 | N | Y | p.20 |
| arlington_dpw_2015 | 5 | **0** | **−5** | Y (BACPI) | N | — |
| arlington_dpw_2018 | 12 | 10 | −2 | Y (BACPI) | N | — |
| arlington_dpw_2021 | 0 | 0 | 0 | N | N | — |
| newton_police_2015 | 10 | 12 | +2 | N | N | — |

**COLA clarification effect (Task 2):**
- Arlington DPW 2015: 5 → 0. The v4 quote was the BACPI sentence ("adjusted to reflect the change in this Boston Adjusted Consumer Price Index"); with the explicit CPI boundary, the model correctly scores it 0 and leaves the quote blank.
- Arlington DPW 2018: 12 → 10 (minor). Notes now explicitly name BACPI as the reason for the low score. Quote dropped.
- No other documents were affected. Nothing that was scoring high due to CPI language — confirming the model was largely already making this distinction, and the clarification only tightened the edge case.

**Quote verification — did the contiguous constraint fix the SPSOA failure?**
No. SPSOA (score=80) failed verification again in v5. The constraint helps in principle (blocks stitching from different parts of the text) but SPSOA's comparability reasoning is distributed across many pages of a 256K-char document; the model cannot find a single 1–2 sentence passage that is both verbatim AND representative. The score (80) is correct — the failure is that the model produces a synthesized summary rather than lifting a verbatim excerpt. Mitigation to consider: cap the quote to a single sentence only, or accept that long-form arbitration awards with multi-page reasoning sections will consistently fail quote verification and treat the score alone as authoritative for those documents.

**New findings in v5:**
- Arlington fire (arlington_fire_2021) scored 25 (+15 from v4) and yielded a verified quote at p.20: "Any outside detail assignment outside the borders of the Town of Arlington shall be paid at that city's or Town's outside detail rate consistent with current practice..." This is a real comparability reference (pay set by reference to another jurisdiction's rate), though for outside details only, not base wages. Score 25 (within the 16–40 "mentioned in passing" band) is plausible. This is the first document outside the Somerville awards to produce a verified non-trivial quote.
- Two new quote failures: SPSOA (persistent) and Boston clerical (score went 0→5, a noise-level shift; the failure means the model tried but couldn't find a verbatim passage, consistent with genuinely low comparability language in that document).

**Qualitative quote quality (v4 vs v5):**
v4 had 3 verified quotes, but 2 were BACPI (CPI-index citations, now correctly excluded). v5 has 2 verified quotes, both genuine comparability language (SPEA's "wages and benefits of comparable towns" at p.60; Arlington fire's outside-detail-rate clause at p.20). Fewer verifications in v5, but higher-quality ones.

**Spend log — corrected total (as of v5):**
```
v3 run (backfill, 2026-06-18): 235,995 prompt + 785 completion = $0.048180  [corrected from $0.036 in session 5 log — used old pricing]
v4 run (live-logged):          236,859 prompt + 1,304 completion = $0.049001
v5 run (live-logged):          237,891 prompt + 1,504 completion = $0.049458
─────────────────────────────────────────────────────────────────────────────
Total (v3–v5):                 710,745 prompt + 3,593 completion = $0.1466

NOTE: All cost figures are ESTIMATES based on public OpenAI list pricing ($0.20/1M input,
$1.25/1M output for gpt-5.4-nano). Harvard's actual billed rate may differ.
```

**Corpus snapshot** (unchanged from session 6)
```
contracts: 12 | discourse: 0 | coverage: 12 | city_attributes: 3
healthy matched pairs: 2
safety units unmatched: 4
```

**Next steps**
1. Decide on SPSOA strategy: single-sentence cap, or accept score-only for dense award documents.
2. Non-safety arbitration awards (JLMC, manual download) remain the primary corpus gap.
3. Consider updating v3 cost note in PROGRESS.md session 5 with the corrected figure.

---

## 2026-06-19 (session 6) — Verbatim quote + page extraction; local spend tracker

**Did**
- Added `page_number_at(text, offset)` helper to `ingest/extract_text.py`. Counts form-feed characters (`\x0c`) before `offset` in pdftotext output and returns a 1-based page number. Only meaningful for text-layer extractions (OCR output has no page markers and always returns 1).
- Added `test_page_number_at()` to `ingest/test_pipeline.py` using a 2-page synthetic PDF with forced `PageBreak()`. Confirmed page 1 and page 2 phrases return correct page numbers. Suite now 26/26 (was 22/22).
- Modified `analysis/gabriel_pilot/run_gabriel.py` to request a verbatim supporting quote alongside the score. Quote is verified using `_verify_verbatim` (same whitespace-normalized substring check as `ingest/extract_spans.py`). On failure: score kept, quote discarded, `gabriel_notes` flagged `[quote_verification_failed]`.
- Added `supporting_quote` and `estimated_page` columns to results output. Page number computed from quote's byte offset in the source text (only populated when `\x0c` page markers are present).
- Created `scripts/log_api_spend.py`. Appends one row per API call to `logs/api_spend_log.csv` (timestamp, script, model, prompt tokens, completion tokens, estimated cost). Also exposes `print_totals()` for end-of-run summaries. Pricing hardcoded as `gpt-5.4-nano: $0.20/1M input, $1.25/1M output` (verified 2026-06-19 via OpenRouter). **All cost figures are estimates based on public list pricing — Harvard's actual billed rate may differ due to institutional terms.**
- Ran GABRIEL v4 on 12 documents. Output: `results_v4.csv` (adds `supporting_quote`, `estimated_page` to v3 schema).

**V4 results**
- 3 documents returned verified quotes with page numbers.
- 1 quote verification failure: `ma_somerville_police_spsoa_2012` (score=80, quote discarded — model paraphrased rather than quoting verbatim; score retained).
- 8 documents scored 0–12 with empty or discarded quotes (correct: no comparability language → no meaningful quote to extract).

**Example verified quote (Somerville SPEA, p.53, score=78):**
> "In reaching the conclusions in the present award, the Arbitration Panel has considered the criteria set forth in the statute including the municipality's ability to pay, wages and benefits of comparable [communities]..."

**Example low-score quote (Arlington DPW, p.9, score=5):**
> "Hereafter the car allowance shall be adjusted to reflect the change in this Boston Adjusted Consumer Price Index (BACPI)." — Correctly low: a price index, not peer wage comparability.

**Spend log (first session):**
```
run_gabriel.py: 12 API calls
  prompt tokens:     236,859
  completion tokens: 1,304
  estimated cost:    $0.0490  [ESTIMATE — list pricing, not Harvard billed rate]
```

**Surprises**
- Quote verification failure on SPSOA (the longer of the two Somerville awards). The document has extensive comparability language but the model synthesized rather than copied verbatim. This is expected for dense, multi-paragraph comparability sections — the model finds it easier to paraphrase a long passage than to select and copy a single sentence. A possible mitigation: ask for a single sentence (≤50 words) rather than "sentence(s)". Not fixed this session.
- Both Arlington DPW 2015 and 2018 returned the exact same quote (the BACPI car-allowance sentence from p.9). This is verbatim and correctly verified — but it reveals that the model is anchoring on the same passage across documents, likely because it's the only quasi-external benchmark in both contracts. The `[quote_verification_failed]` flag is not tripped because the quote is real; it just isn't strong evidence of comparability.

**Corpus snapshot** (unchanged from session 5)
```
contracts: 12 | discourse: 0 | coverage: 12 | city_attributes: 3
healthy matched pairs: 2
  - Worcester, MA: fire 2017-2020  vs  [clerical_admin, public_works]
  - Arlington, MA: fire 2021-2024  vs  [public_works]
safety units unmatched: 4
  - Boston police 2020-2025
  - Somerville SPSOA 2012-2018 / SPEA 2012-2015
  - Newton police 2015-2018 (est.)
```

**Next steps**
1. Tighten quote prompt to request a single sentence (≤50 words) to reduce paraphrase failures.
2. Backfill v3 spend data into `api_spend_log.csv` (current log starts from v4 only — v3 cost was $0.036).
3. Non-safety arbitration awards (JLMC, manual download) remain the primary corpus gap.

---

## 2026-06-18 (session 5) — Harvard API wired; GABRIEL v3 full-text run; report_v3.md

**Did**
- Wired Harvard HUIT OpenAI proxy into `run_gabriel.py`. Credential: `HARVARD_SUBSCRIPTION_KEY` (single env var, stored in `.env` at repo root — added to `.gitignore`). The subscription key serves as both the `api_key` and the `Ocp-Apim-Subscription-Key` header; no separate OpenAI key is needed. Added `python-dotenv` to handle `.env` loading. Added `.env.example` documenting required variables. Scanned repo for hardcoded `sk-` strings — none found.
- Confirmed Harvard endpoint works: `gpt-5.4-nano` responded correctly (base_url and header confirmed in use).
- Raised `MAX_TEXT_CHARS` from 12,000 to 300,000 to send full document text. All 12 docs fit within 300K chars (largest: Somerville SPEA at 256K chars / ~64K tokens, ~16% of model's 400K-token context window).
- Ran GABRIEL v3 on 12 documents. Actual cost: $0.036 (235,995 prompt + 785 completion tokens). *(Corrected in session 7: $0.036 used old pricing $0.15/$0.60; correct rate $0.20/$1.25 gives $0.048180 — spend log updated.)*
- Generated v3 PNGs (`graph1_v3`, `graph2_v3`, `graph3_v3`). Fixed y-axis auto-scaling in `plot_results.py` so bars are not clipped when scores exceed 35.
- Wrote `analysis/gabriel_pilot/report_v3.md` (attribute definition, comparison table, captioned figures, summary with honest read on results).

**V1 / V2 / V3 comparison**

| Version | Model | Truncation | Score range | Safety mean | Non-safety mean | arbitration_award mean | cba mean |
|---------|-------|------------|-------------|-------------|-----------------|------------------------|----------|
| v1 | gpt-4o-mini | 12,000 chars | 10–20 | 16.7 | 13.3 | 15.0 | 14.3 |
| v2 | gpt-5.4-nano | 12,000 chars | 0–10 | 0.8 | 2.5 | 2.5 | 1.5 |
| v3 | gpt-5.4-nano | 300,000 chars | 0–85 | 28.8 | 3.3 | 81.5 | 3.0 |

**V3 produced real score spread.** The two Somerville police arbitration awards (2012) scored 78 and 85 — highest in the batch. The remaining 10 CBAs/MOAs scored 0–15. This is the expected pattern: arbitration awards contain the arbitrator's written reasoning (which cites named peer communities to justify the wage decision); CBAs record the agreed outcome without the reasoning.

**Surprises / results**
- **The truncation bug was the entire story.** At 12K chars, the arbitration awards were being read in their procedural header only (parties, stipulated facts, submission). The comparability analysis — which runs 10–50 pages deep in these documents — never reached the model. Raising to full text immediately produced the expected high scores.
- **Safety vs. non-safety gap (28.8 vs. 3.3) is confounded with document type.** The safety sample has two arbitration awards; the non-safety sample has zero. This is not a clean test of the safety hypothesis. To isolate occupation class from document type, the next run needs non-safety arbitration awards (e.g., JLMC awards for teacher or clerical units in the same cities).
- **CBA mean near-zero (3.0) is coherent, not a floor artifact.** CBAs for all five cities contain wage schedules, step tables, and COLA provisions but no explicit comparability reasoning. If anything, this is the baseline: the comparability text lives in the award documents, and whether it translates into CBA language that persists contract-to-contract is an open empirical question.

**Corpus snapshot** (unchanged from session 4)
```
contracts: 12 | discourse: 0 | coverage: 12 | city_attributes: 3
healthy matched pairs: 2
  - Worcester, MA: fire 2017-2020  vs  [clerical_admin, public_works]
  - Arlington, MA: fire 2021-2024  vs  [public_works]
safety units unmatched: 4
  - Boston police 2020-2025
  - Somerville SPSOA 2012-2018 / SPEA 2012-2015
  - Newton police 2015-2018 (est.)
```

**Next steps**
1. **More documents — JLMC awards.** Manual browser download from mass.gov (still Akamai-blocked from CLI). Priority: arbitration awards for non-safety units to allow document-type-controlled comparison.
2. **Discuss safety/non-safety confound with Andrei.** The right specification (CBA-only, award-only, or mixed) affects what the attribute measures and how to interpret it.
3. **Scale to other states.** Massachusetts JLMC is the starting point. Pennsylvania PLRB, New York PERB, Michigan MERC next.
4. **Attribution spot-check.** Before scaling to >50 documents, do a 5-doc manual verification that scores are tracking comparability text, not document length or complexity.

---

## 2026-06-18 (session 4) — OCR install, model fix, anchored attribute, GABRIEL v2

**Did**
- Installed `pytesseract` + `pdf2image` Python wrappers (Tesseract 5.5.2 and poppler were already present system-wide). All 3 previously-skipped rows now OCR successfully: Worcester fire (9,808 chars, ocr_messy), Boston police MOA (14,832 chars, ocr_messy), Newton police CBA (127,200 chars, ocr_messy). input.csv rebuilt with 12/12 rows having real text.
- Corrected model: `gpt-5.4-nano` (released 2026-03-17) confirmed live via API. V1's substitution of `gpt-4o-mini` was wrong. Reasoning model differences: no `temperature` param, use `max_completion_tokens` not `max_tokens`, `reasoning_effort` is supported.
- Replaced vague attribute prompt with explicit behavioral anchors (0–15 / 16–40 / 41–70 / 71–100), requiring the model to cite specific textual evidence rather than picking a default bucket. Updated `run_gabriel.py`; added `--output` flag to write `results_v2.csv` without overwriting v1.
- Added `--results` / `--suffix` flags to `plot_results.py`; generated 3 v2 PNGs alongside v1 originals for side-by-side comparison.
- Cost v2: $0.0050 (30,108 prompt + 836 completion tokens, includes reasoning tokens).

**V1 vs V2 score comparison**

| | V1 (gpt-4o-mini, vague prompt) | V2 (gpt-5.4-nano, anchored) |
|---|---|---|
| Rows scored | 9/12 (3 skipped — no text) | 12/12 (OCR recovered) |
| Score range | 10–20 only | 0–10 only |
| Non-safety mean | 13.3 | 2.5 |
| Safety mean | 16.7 | 0.8 |
| Notes quality | Near-identical boilerplate | Specific clause citations per doc |

V2 is clearly reading more carefully — every note cites specific contract language. But scores collapsed toward zero rather than spreading across the 0–100 range. See "Surprises" below.

**Surprises / results**
- **Scores still near-floor in v2, but for a different and diagnosable reason.** V1's flat 10/20 scores were model laziness (vague prompt → default anchors). V2's near-zero scores are structurally correct: the first 12,000 chars of a CBA or arbitration award are invariably recognition clauses, management rights, grievance procedures — not the wage articles. The model correctly finds no comparability language because we're not feeding it the right section. This is a text-extraction problem, not a scoring problem.
- **Safety mean LOWER than non-safety in v2 (0.8 vs 2.5).** Counterintuitive if the hypothesis is that safety wages are comparability-driven. But both are near-zero and the difference is noise at n=6. Not a finding; artifact of which sections land in the first 12K chars of each document.
- **Arbitration awards scored the same as CBAs (2.5 vs 1.5).** The two Somerville SPEA/SPSOA awards are 230K+ chars; their comparability reasoning is deep in the body and not captured at 12K truncation. This is the strongest evidence that MAX_TEXT_CHARS is the binding constraint.

**Root cause and fix needed**
The 12,000-char truncation (`MAX_TEXT_CHARS`) cuts off before wage articles in long documents. Fix options in priority order:
1. **Smarter section targeting** — extract the last N chars of the document (or a middle window), or use keyword search to locate "wage"/"salary"/"comparab" sections before sending to the model.
2. **Raise MAX_TEXT_CHARS for awards** — the Somerville awards at 230K+ would be expensive at full length (~57K tokens each), but targeting 50K chars would land in the reasoning sections at reasonable cost.
3. **Chunk and max-score** — split each doc into 12K windows, score each, take the max. Adds ~5-10x API calls per long document.
Option 1 is the right next step before adding JLMC awards.

**Corpus snapshot** (unchanged from session 3)
```
contracts: 12 | discourse: 0 | coverage: 12 | city_attributes: 3
healthy matched pairs: 2
  - Worcester, MA: fire 2017-2020  vs  [clerical_admin, public_works]
  - Arlington, MA: fire 2021-2024  vs  [public_works]
safety units unmatched: 4
  - Boston police 2020-2025
  - Somerville SPSOA 2012-2018 / SPEA 2012-2015
  - Newton police 2015-2018 (est.)
```

**Next steps**
1. **Fix text window in `run_gabriel.py`** — implement tail-window extraction (e.g., last 15K chars or a wage-section keyword scan) before re-running. This is the prerequisite before adding more documents.
2. **Add JLMC awards via browser download** — all 11 mass.gov URLs blocked from CLI; manual browser download needed. Once in corpus, rebuild input.csv and run v3.
3. **Newton + Arlington police** — manual downloads still needed (Akamai-blocked). 

---

## 2026-06-18 (session 3) — GABRIEL pilot: end-to-end scoring run + graphs

**Did**
- Confirmed Task 1 (obs_id dedup fix in `ingest/pipeline.py` + `process_inbox.py`) was already completed in the prior session — `_existing_obs_ids()` guard is live and green.
- Built `analysis/gabriel_pilot/` with `build_input.py`, `run_gabriel.py`, and `plot_results.py`. Input assembled from all 12 `contracts.csv` rows (text via `extract_text.py`). JLMC award downloads attempted but mass.gov returned 403 for all 11 URLs in `ma_award_inventory.csv` (Akamai block — requires browser session). Proceeded with 12 rows.
- Ran GABRIEL scoring: model `gpt-4o-mini`, temperature=0, `reasoning_effort` N/A (not a reasoning model), `response_format=json_object`. Attribute: `comparability_emphasis` (0–100). Previous run had all 401s from bad API key; re-ran with valid key. 9/12 rows scored; 3 skipped (Worcester fire, Boston police, Newton police — zero extractable text).
- Cost: $0.0032 (20,073 prompt + 234 completion tokens).
- Generated 3 graphs saved as PNGs in `analysis/gabriel_pilot/`: safety vs non-safety average, by source type, score-by-year scatter. Validator passes (12/0/12/3).

**Decisions (and why)**
- **Proceeded with 12 rows instead of target ~35–40.** mass.gov JLMC PDFs are Akamai-blocked from CLI for all 11 award URLs. Pilot's purpose is workflow practice, not statistical power — 12 rows is sufficient to exercise the end-to-end pipeline.
- **Used `gpt-4o-mini` instead of "gpt-5.4-nano" (no such model).** Cheapest production OpenAI chat model; no reasoning-effort parameter on chat completions. Noted in script header.

**Surprises / results**
- **Scores are flat: all 10 or 20.** Notes are nearly identical ("minimal references to comparability"). This is plausible for negotiated CBAs — comparability language appears prominently in arbitration *reasoning*, less so in CBAs which are concluded agreements. Two Somerville police awards (arbitration_award source_type) scored 10 and 20 — same range as CBAs. The model may be correct that explicit comparability language is sparse in these documents. Escalating to `reasoning=medium` or expanding to true JLMC awards with actual arbitrator reasoning sections would test whether the attribute is estimable at all.
- **Graph results (not findings — workflow practice only):** safety mean = 16.7, non-safety mean = 13.3 (n=3 vs n=6). arbitration_award mean = 15.0, cba mean = 14.3 (n=2 vs n=7). Differences are within noise at this scale.

**Corpus snapshot**
```
contracts: 12 | discourse: 0 | coverage: 12 | city_attributes: 3
healthy matched pairs: 2
  - Worcester, MA: fire 2017-2020  vs  [clerical_admin, public_works]
  - Arlington, MA: fire 2021-2024  vs  [public_works]
safety units unmatched: 4
  - Boston police 2020-2025
  - Somerville SPSOA 2012-2018
  - Somerville SPEA 2012-2015
  - Newton police 2015-2018 (est.)
```

**Next steps**
1. **Get JLMC awards via browser** — all 11 mass.gov URLs in `ma_award_inventory.csv` need manual browser download (curl/requests blocked). Download to `inbox/`, add manifest rows, run `process_inbox.py` to add to corpus. This will bring arbitration awards with actual comparability reasoning into the GABRIEL run.
2. **Re-run GABRIEL with awards** — once JLMC PDFs are in `scratch_pdfs/`, rebuild `input.csv` and re-score. If all scores remain flat (10–20), revisit the attribute definition or switch to a more discriminating attribute (e.g., "arbitrator explicitly cites neighboring-city wage tables").
3. **Newton + Arlington police** — manual downloads still needed (Akamai-blocked). Priority: NPA FY19-FY21 + AFSCME 3092 FY20-FY24 to close Newton matched-pair gap.
4. **OCR install** (deferred) — Worcester fire and Boston police have ~0 extractable text; those rows will remain unscored until Tesseract is installed.

---

## 2026-06-17 (session 2) — Arlington IA collection + Newton portal mapping

**Did**
- Discovered the previous session's `ma_arlington_police_cba_2020_2022.pdf` was a wrong-jurisdiction file — Revize CMS path `revize/arlington` serves **Arlington Heights, IL** (Village, Metropolitan Alliance of Police Chapter 510), not Arlington, MA (Town). Renamed with `DISCARD_` prefix.
- Found Arlington MA's full document archive on Internet Archive (`Arlington_MA_ShowDocument_Id_*` collection). Identified all CBA-related items (fire, AFSCME, SEIU, RLPA). RLPA = Robbins Library Professional Association (library employees).
- Downloaded 3 Arlington CBAs from IA: IAFF Local 1297 fire FY2022-2024 (Jul 2021–Jun 2024, 44 pp, IA OCR); AFSCME Local 680 FY2018-2021 (Jul 2018–Jun 2021, 31 pp, clean); AFSCME Local 680 FY2021-2024 (Jul 2021–Jun 2024, 35 pp, poor OCR). FY2016-2018 AFSCME already in inbox from previous session.
- Extracted wage rates from AFSCME FY2018-2021: FY2019 = 2% + $0.35 market adj (Jan 2019), FY2020 = 2% + $0.20 market adj (Jan 2020), FY2021 = 1%. Fire FY2022-2024: Step 7 comparison gives ~4.84% (FY2023) and ~4.46% (FY2024).
- Wrote 5 manifest rows (Arlington fire, AFSCME ×3, Newton police LRIS), ran `process_inbox.py`, deduplicated re-ingested rows from contracts.csv and city_coverage.csv (pipeline has no skip-already-processed guard — see breakage note below).
- Mapped the full Newton union roster via IA snapshot of newtonma.gov (Dec 2025): identified AFSCME Local 3092 City Hall Associates (clerical, folder 445), Teamsters Local 25 DPW (folder 452), Newton Police Association (folder 450). Found document IDs for priority Newton downloads.
- **Git commits:** this session

**Decisions (and why)**
- **`occupation_class = public_works` for Arlington AFSCME Local 680.** The recognition clause covers "Labor Service including foremen" (DPW, custodians) as the primary unit, plus clerical grades. Labor Service is the larger portion; `public_works` is more accurate for the GABRIEL comparator than `clerical_admin`. Note in total_comp_note that the unit also includes clerical grades.
- **Fire (not police) as Arlington safety unit for now.** JLMC award JLMC-22-9174 for Arlington Police (APPA, May 2023, neutral Bonnie J. McSpiritt) is blocked by Akamai on mass.gov. The fire IAFF Local 1297 CBA is fully accessible via IA and creates a valid matched pair with the AFSCME FY2021-2024 (exact same Jul 2021–Jun 2024 cycle). Police can be added once mass.gov is reachable.
- **Newton police LRIS file logged as `partial` with estimated cycle dates.** The 43 MB scanned PDF has ~0 extractable text and an unknown cycle. File creation date (March 2018) suggests FY15-FY18. Flagged as ESTIMATED in total_comp_note. Portal confirms the correct document is NPA CBA FY15-FY18 (doc 65551) — same file, more reliable dates once OCR is available.

**Surprises / breakage**
- **Revize CMS namespace collision.** `cms2.revize.com/revize/arlington` is Arlington Heights, IL — not Arlington, MA. The URL appeared in a Google search result labeled "2020-2022 Police Contract" and was believable. Verified by reading the PDF text (Village, MAP union). Always read the first page of any document before writing a manifest row.
- **`process_inbox.py` re-ingests all manifest rows on every run.** No "processed" flag or archive mechanism exists. Running it a second time after adding new rows recreated all prior rows as duplicates, breaking validation. Fixed manually by deduplicating contracts.csv and city_coverage.csv. **Long-term fix needed:** either move processed manifest rows to `inbox/manifest_archive.csv` after each run, or add an obs_id existence check in `ingest/pipeline.py` before writing.
- **Newton portal documents are not individually archived on IA.** The newtonma.gov folder pages (AFSCME 3092 folder 445, NPA folder 450, Teamsters folder 452) ARE archived in December 2025 IA snapshots, and these reveal document IDs. But each showpublisheddocument URL resolves to an Akamai-blocked direct download with no IA copy. Manual browser download from newtonma.gov is the only route.
- **Arlington fire wage increases are high (~4.65% avg FY2023-FY2024).** Not a data error — this covers Jul 2021–Jun 2024, the high-inflation period. Cross-check against Newton and other cities when available.

**Corpus snapshot**
```
contracts: 12 | discourse: 0 | coverage: 12 | city_attributes: 3
healthy matched pairs: 2
  - Worcester, MA: fire 2017-2020  vs  [clerical_admin, public_works]
  - Arlington, MA: fire 2021-2024  vs  [public_works]
safety units unmatched: 4
  - Boston police 2020-2025          [cycle gap vs SENA 2023-2027]
  - Somerville SPSOA 2012-2018       [no non-safety collected]
  - Somerville SPEA 2012-2015        [no non-safety collected]
  - Newton police 2015-2018 (est.)   [no non-safety collected]
```

**Next steps**
1. **Newton — manual browser download required** (all Akamai-blocked from CLI):
   - NPA Police CBA FY19-FY21: `https://www.newtonma.gov/home/showpublisheddocument/119347`
   - AFSCME 3092 FY20-FY24 MOA: `https://www.newtonma.gov/home/showpublisheddocument/78310`
   - Teamsters Local 25 FY20-24 MOA: `https://www.newtonma.gov/home/showpublisheddocument/77786`
   - The FY19-FY21 police + FY20-FY24 AFSCME pair would close Newton's matched-pair gap.
2. **Arlington police** — manual browser download of JLMC-22-9174 award: `https://www.mass.gov/doc/jlmc-22-9174-arlington-police-award/download`
3. **Fix process_inbox.py re-ingestion.** Add obs_id existence check or archive processed manifest rows.
4. **Install pytesseract + tesseract + poppler** (`pip install pytesseract pdf2image` + `brew install tesseract poppler`) before next OCR-heavy batch (Newton police LRIS, Boston BPPA MOA).
5. **Somerville non-safety (SMEA/SMEU)** — FOIA still the only route (unchanged).
6. **Boston clerical ~2019-2023** — predecessor SENA or SEIU 888 cycle to close Boston matched-pair gap (unchanged).
7. **Worcester c.66 FOIA** — still pending PI/RA submission (unchanged).

---

## 2026-06-17 — MA source inventory verification + Boston/Somerville ingest

**Did**
- Verified all 6 city URLs from `docs/ma_source_inventory.md`. Found 4 usable public sources; 2 cities (Quincy, Somerville HR) have no portal-hosted PDFs; 2 cities (Arlington, Newton) return HTTP 403 to automated fetchers.
- Downloaded 4 PDFs from confirmed-public sources (Boston OLR portal, Somerville MuckRock FOIA release). Inspected each with `pdftotext` + `pdfimages` before writing any manifest row.
- Ingested all 4 via `process_inbox.py` → `data/contracts.csv` + `data/city_coverage.csv`. Fixed a post-ingest duplicate obs_id. Added `city_attributes` rows for Worcester, Boston, Somerville. Validate and audit clean.
- **Git commit:** 9b9cc22

**Decisions (and why)**
- **`source_type = arbitration_award` for both Somerville docs.** The MuckRock release is an integrated document — base CBA (1997/2004) with all successive JLMC arbitration awards appended. The terminal document governing wages is the award, not the base CBA, so that's the type we record. This keeps the schema-type aligned with what GABRIEL will score.
- **Separate obs_ids for SPSOA and SPEA.** Both Somerville police units have `cycle_start = 2012-07-01`, so the pipeline's auto-generated key (`{city_id}_{occ}_{year}`) collided. Fixed by patching obs_ids to `ma_somerville_police_spsoa_2012` and `ma_somerville_police_spea_2012`. Future mitigation: pass explicit `obs_id` in the manifest (the pipeline already accepts it from meta).
- **Included the BPPA MOA despite partial quality and no mechanism clauses.** A wage MOA is still valid for the dependent variable (pct_increase_annual). It creates the Boston safety row needed for the matched-pair structure. Mechanism fields are empty — correct for an MOA — and the `total_comp_note` says so explicitly.
- **pct_increase_annual on multi-year variable-rate awards:** used simple average — SPSOA 0.0225 (rates of 2.5/2/2/2/2.5/2.5% over 6 years), SPEA 0.022 (2.5/2/2% over 3 years). Same approach as prior Worcester rows.
- **Boston non-safety: chose SENA Local 9158 over SEIU 888 or AFSCME.** SENA is the most cleanly `clerical_admin`-typed unit; the portal name is explicit. SEIU 888 at Boston covers a wider range of occupations and would require more classification judgment.

**Surprises / breakage**
- **Boston portal posts MOAs for all safety units, full CBAs for non-safety.** BPPA (2020-2025) and IAFF Local 718 (2021-2024) are both explicitly labeled "MOA" in filenames and are 6-page scanned documents. Non-safety units (SENA, SEIU 888, AFSCME, OPEIU 6) all have 40–50-page full CBAs on the same portal. This is the same gap as Worcester: safety wages are negotiable but mechanism clauses are in older unreachable base CBAs. The SENA CBA keywords confirmed: `arbitration`, `binding arbitration` — non-safety has mechanism content that the safety MOA lacks.
- **BPPA PDF is entirely scanned phone-photos** (6 pages, all JPEG images at 150–300 dpi), not even scanner-grade. `pdftotext` → 0 chars; `extract_text.py` → 0 OCR chars (pytesseract not installed). Filed as `text_quality=partial`. Cycle dates estimated from portal title (2020-2025).
- **Somerville SPEA has a "parity" clause keyword** — distinct from the SPSOA, which doesn't. Parity clauses are a core GABRIEL measurement target; worth flagging for the analyst as a candidate for the comparability referent field.
- **Somerville SPSOA 6-year award.** One arbitration decision (May 2018, Gary D. Altman neutral) settled two consecutive 3-year cycles (2012-2015 and 2015-2018) in a single award, because the patrolmen's SPEA award was adopted by reference for the first period. Represented as one row spanning 2012-2018 rather than splitting — GABRIEL will score it from the single document.
- **Boston matched pair cycle gap.** BPPA safety unit (2020-2025) and SENA non-safety (2023-2027) have different `cycle_window` keys, so `audit_coverage.py` counts Boston police as unmatched even though the two contracts overlap 2023-2025. Fixing this requires a Boston clerical CBA for the ~2019-2023 predecessor cycle (not on the current portal — likely in the legacy archive at `cityofboston.gov/images_documents/`).
- **Quincy HR page is a directory, not a portal.** Lists union reps and phone numbers only; no PDFs linked. Must use the JLMC award for police and file a targeted FOIA for QPEA matching unit.

**Corpus snapshot**
```
contracts: 7 | discourse: 0 | coverage: 7 | city_attributes: 3
healthy matched pairs: 1  (Worcester fire 2017-2020 vs clerical_admin + public_works)
safety units unmatched: 3
  - Boston police 2020-2025  [cycle gap vs SENA 2023-2027]
  - Somerville SPSOA 2012-2018  [no non-safety collected]
  - Somerville SPEA 2012-2015   [no non-safety collected]
```

**Next steps**
1. **Somerville non-safety (SMEA/SMEU)** — not on city HR or Clerk pages. File a low-cost FOIA to Somerville (smaller ask than Worcester; would close two matched pairs at once).
2. **Boston clerical ~2019-2023** — find the SENA or SEIU 888 predecessor cycle in the legacy archive (`cityofboston.gov/images_documents/`) to match BPPA 2020-2025.
3. **Boston BPPA base CBA** — full mechanism clauses require the base agreement (not the MOA). Contact BPPA directly, check the legacy archive, or file c.66.
4. **Arlington + Newton** — manual browser download required (both 403 to fetchers). Arlington HR page explicitly says CBAs are attached. Newton city HR page same. Download Police + AFSCME (Arlington) and Police + clerical/DPW (Newton).
5. **Quincy** — verify JLMC award in `ma_award_inventory.csv` is sufficient for police mechanism clauses; then FOIA for QPEA CBA as the non-safety match.
6. **Install pytesseract + pdf2image** (`pip install pytesseract pdf2image` + `brew install tesseract poppler`) before the next batch that includes scanned documents.
7. **Worcester c.66 still pending** — no action this session; waiting on PI/RA submission.

---

## 2026-06-16 — Validator range-check + finalized Worcester records request

**Did**
- **Added a `pct_increase_annual` range-check to `scripts/validate.py`** (new generic `check_numeric_range` helper, written in the same style as `check_dates`/`check_enum`): rejects any value outside `0 ≤ x ≤ 0.25` or non-numeric, with a row-located error that names the offending value and explains the decimal convention. Blank still passes (field is optional). This closes the validator gap that let last session's `2.0` (=200%) slip through.
- **Documented the range** in `docs/schema.md` (`pct_increase_annual` row now states "valid range 0–0.25 … catches percent-vs-decimal slips like 2.0").
- **Added a test** to `ingest/test_pipeline.py` (`test_validator_pct_range`): `0.02` accepted, `2.0` rejected, blank passes, non-numeric rejected. Suite now **22/22 green** (was 18).
- **Finalized the Worcester c. 66 request** (`docs/records_requests/worcester_c66_2026-06.md`): deleted the entire "Internal notes" section (it referenced GABRIEL/pipeline/inbox internals — inappropriate for a government office). Re-verified the RAO from worcesterma.gov/public-records-requests — **unchanged** (Michael Manning, Law Dept, 455 Main St Room 301, RAO@worcesterma.gov). Requester block left as fillable blanks. **Not sent.**

**Decisions (and why)**
- **Made the helper generic, not pct-specific.** `check_numeric_range(table, rows, field, lo, hi, required, hint)` mirrors the existing helpers so future numeric fields (e.g. `years_to_top`) can reuse it; the pct-specific guidance lives in the `hint` passed at the call site.
- **Range cap 0.25 (25%).** Comfortably above any realistic single-year municipal raise, so legitimate values pass while any percent-as-whole-number slip (2.0, 3.0…) trips immediately.
- **Test targets the validator function directly** (imports `validate`, clears `validate.errors`, asserts) rather than building a CSV fixture — fast, hermetic, and consistent with the suite's no-pytest style.
- **Kept the request's DRAFT/NOT-SENT banner and the "Clarifying scope" MOA explanation** — the MOA-vs-base-CBA distinction is exactly what the records office needs to fulfill the request correctly; only the project-internal notes were removed.

**Surprises / breakage**
- None. Current corpus (all three rows at `0.02`) still validates clean; leak-check confirms no GABRIEL/pipeline/inbox/corpus references remain in the finalized request.

**Corpus snapshot**
- contracts: 3 | discourse: 0 | matched pairs: 1 (Worcester fire 2017–2020 vs clerical_admin + public_works). validate.py green; test_pipeline.py 22/22.

**Next steps**
- Submit the Worcester c. 66 request (PI/RA action); ingest returned base CBAs via `inbox/foia/` with `retrieval_method=foia` to capture the missing mechanism clauses.
- Extend matched collection to Boston (template) and the other verified cities.

---

## 2026-06-16 — Worcester wage backfill, inbox cleanup, base-CBA records request

**Did**
- **Backfilled** the Worcester fire row `pct_increase_annual` = `0.02` (OCR-recovered: 2% eff. July 1 2017/2018/2019, excl. Step 1) and updated its note to record the OCR reading.
- **Cleared the verified Worcester batch** to prevent re-ingestion duplicates: archived the 3 Worcester manifest rows from `inbox/manifest.csv` to a new `inbox/processed_manifest.csv`, and deleted the 3 staged originals from `inbox/foia/`. The `corpus/ma_worcester/` copies remain as the source of record. `inbox/manifest.csv` is back to header-only.
- **Drafted** a Massachusetts c. 66 public-records request for the full base CBAs (not just MOAs) for Local 1009 (fire), Local 490 (clerical), Local 170 (DPW), 2014–2024 window → `docs/records_requests/worcester_c66_2026-06.md`. **Not sent** — left for PI/RA review and self-submission.
- Re-ran `validate.py` (green) and `audit_coverage.py` (1 healthy matched pair intact) after every change.

**Decisions (and why)**
- **Found and fixed a 100× unit error.** `docs/schema.md` defines `pct_increase_annual` as a decimal (0.03 = 3%). The fire backfill of `0.02` is schema-correct — but it exposed that last session's clerical and DPW rows stored `2.0` (= 200%). Since this column is the analytical spine and the same 2% raise must encode identically, I corrected **both** to `0.02` (a spec-conformance fix, git-reversible), not just the fire row the task named. The validator doesn't range-check this field, so the error had passed silently — flagging that as a validator gap.
- **Archived rather than deleted manifest rows.** Moving processed rows to `inbox/processed_manifest.csv` (vs. commenting them out) keeps `manifest.csv` clean for the next batch while preserving a real, parseable record of what was ingested. Normalized the archived `pct` values to `0.02` too, so the wrong unit doesn't survive anywhere it could be copied back.
- **Records request recipient verified, not guessed:** Michael Manning, RAO, Worcester Law Dept, 455 Main St Room 301 / RAO@worcesterma.gov / GovQA portal (confirmed from worcesterma.gov, 2026-06-16). Request explicitly distinguishes the full base CBAs from the successor wage MOAs already collected, and cites M.G.L. c. 66 §10 + c. 4 §7(26).

**Surprises / breakage**
- The unit-convention bug above (2.0 vs 0.02) — caught only because the backfill forced a direct comparison. Worth a validator rule: range-check `pct_increase_annual` (e.g. 0 ≤ x ≤ 0.25) to catch percent-vs-decimal slips.
- `process_inbox.py` copies (doesn't move) inbox→corpus, so this manual archive+delete step is currently the de-dup mechanism. Candidate pipeline improvement: have `process_inbox.py` move processed files and auto-archive their manifest rows on success.

**Corpus snapshot**
- contracts: 3 | discourse: 0 | matched pairs: 1 (Worcester fire 2017–2020 vs clerical_admin + public_works). All three `pct_increase_annual` now `0.02`. inbox/manifest.csv: header-only (3 rows archived). validate.py green.

**Next steps**
- Submit the Worcester c. 66 request (PI/RA action); on receipt, ingest base CBAs via `inbox/foia/` with `retrieval_method=foia` to capture the mechanism clauses currently missing.
- Add a validator range-check for `pct_increase_annual` to catch unit slips.
- Extend matched collection to Boston (template) and the other verified cities.

---

## 2026-06-16 — Worcester matched collection (first real ingest)

**Did**
- Collected Worcester's first matched document set from the verified city HR portal (`worcesterma.gov/human-resources/collective-bargaining-agreements`), all 2017–2020 cycle (the one cycle all three units share — clean overlap inside 2014–2024):
  - **Safety:** Worcester Firefighters Local 1009, IAFF — `local-1009-moa-2017-2020.pdf`
  - **Non-safety:** NAGE Local 490 (clerical) — `local-490-moa-2017-2020.pdf`; Teamsters Local 170 (DPW) — `local-170-moa-2017-2020.pdf`
- Automated download worked (HTTP 200, browser User-Agent) — **no 403** this time, despite the inventory note; no manual grab needed. Files staged in `inbox/foia/`, described in `inbox/manifest.csv`, ingested via `process_inbox.py`.
- **All 3 ingested, 0 quarantined.** Copied to `corpus/ma_worcester/`. `validate.py` passes; `audit_coverage.py` shows 1 healthy matched pair (Worcester fire 2017–2020 vs [clerical_admin, public_works]).

**Decisions (and why)**
- **Occupation classes:** Local 490 → `clerical_admin`, Local 170 → `public_works` (DPW). Local 170 is technically the "DPW Clerks" Teamsters local, but classed as public_works to keep the two non-safety comparisons distinct (the design wants occupational variety, not two clerical rows). Noted in the row's `total_comp_note`.
- **Left `text_quality` blank in the manifest** so the extractor auto-tags it — correctly produced `clean` for the two text-layer MOAs and `ocr_messy` for the scanned fire doc.
- **Did not pre-fill clause spans** (per the verbatim rule); let the pipeline capture them. Filled only readily-visible wage structure: 2%/yr for the two MOAs. Left fire wages blank at manifest time (scanned) — now known post-OCR (see below).
- **Did not hand-edit `contracts.csv`** to backfill the fire wage (append-only discipline) — flagged as a backfill next step instead.

**Surprises / breakage**
- **These are successor *wage MOAs*, not full base CBAs.** All three explicitly state they supplement/supersede the prior agreement "pending the drafting of a new contract document." They carry wage/health terms only — **none contains interest-arbitration, comparability, me-too, or no-strike articles**, which live in the base CBA incorporated by reference. So all clause flags came back 0 across all three units. This is **correct pipeline behavior, not a regex gap** — there is genuinely no mechanism-clause text in these documents to capture.
- **No regex tuning needed from this batch.** The only `arbitrat` hit (clerical MOA) was *grievance* arbitration ("...not be subject to a grievance or arbitration..."), which the regex correctly did **not** capture as interest-arbitration. The grievance-vs-interest distinction held up.
- **The real gap is collection scope, not extraction:** to get the causal mechanism clauses GABRIEL needs (arbitration/comparability/no-strike), we must obtain the **full base CBAs**, which Worcester's portal may not post separately (the portal hosts successor MOAs). Likely a records request, or sourcing an older full agreement that the MOAs amend.
- Fire CBA had **no embedded text layer** (scanned) → OCR fired automatically (0 → ~1,962 chars/page) and produced clean, readable output; `ocr_messy` is the conservative auto-tag. Confirmed fire wages = **2% effective July 1 2017/2018/2019, excluding Step 1** (FY18–FY20). This value is not yet in `contracts.csv` (fire row `pct_increase_annual` left blank at ingest) — backfill candidate.
- Pipeline **copies** (not moves) inbox files to `corpus/`, so originals remain in `inbox/foia/`. Since `process_inbox.py` re-processes every manifest row each run, leaving them will duplicate these rows on the next batch — clear the staged originals or prune their manifest rows before the next run. (Left in place this session at request.)

**Corpus snapshot**
- contracts: 3 | discourse: 0 | matched pairs: 1 (Worcester fire 2017–2020 vs clerical_admin + public_works). cities with a safety contract: 1 (Worcester); no safety unit lacking a comparison.

**Next steps**
- Decide whether successor wage MOAs are sufficient for the wage-trajectory measure, or whether to pull **full base CBAs** (likely c.66 request) so the mechanism clauses are present for GABRIEL.
- Backfill the fire row `pct_increase_annual` = 2.0 (FY18–FY20, excl. Step 1) read from OCR; consider whether the timing difference (fire July 1 vs non-safety Jan 1 increases) matters for alignment.
- Resolve the inbox/manifest re-ingestion footgun before the next batch (clear staged originals or mark processed rows).
- Extend the same matched-collection pattern to Boston (template) and the other verified cities.

---

## 2026-06-16 — CBA source verification (MA award cities)

**Did**
- Established and recorded in `CLAUDE.md` the **"verified" standard** for a city's CBA sources: a city counts as verified only when all three hold, each logged in the inventory — (1) a *findable source* (central portal, union local, or a documented FOIA route), (2) a *safety CBA present* in the 2014–2024 window, and (3) a *matched non-safety CBA* from the same city overlapping the same cycle. A city with safety but no in-window comparison is flagged dead weight, not collected.
- Used **Boston as the template**: verified via the city's central Office of Labor Relations (OLR) portal (`boston.gov/departments/labor-relations`), which hosts ~21 bargaining units' CBAs as PDFs (safety + BTU teachers + clerical).
- Verified the other 5 award cities against the standard and updated `data/ma_award_inventory.csv` (added a `cba_source_url` column distinct from the JLMC `award_url`; set `safety_cba_status`, refined `matched_nonsafety_target`, logged source route + quirks). All 5 came back **verified**:
  - **Newton** — verified_portal. City HR union-contracts portal hosts safety + non-safety CBAs; NTA teachers via Newton Public Schools HR.
  - **Quincy** — verified_portal. Safety via JLMC arbitration awards on mass.gov; QEA teacher CBAs posted (quincypublicschools.com / quincyeducationassociation.org).
  - **Arlington** — verified_portal (town). Fire CBA on town HR page; police arbitration-prone (JLMC award); AEA teacher contracts on massteacher.org.
  - **Somerville** — verified_portal. No central city portal; police CBAs via a *completed* MuckRock FOIA release + MA DLR repository; SEU teachers posted. City verified on police.
  - **Worcester** — verified_portal. Single central HR portal hosts fire + police + clerical + DPW CBAs across multiple in-window cycles.
- Moved nothing: the inventory was already at `data/ma_award_inventory.csv` (untracked); it's now tracked.

**Decisions (and why)**
- **`award_url` ≠ CBA source.** The existing `award_url` points to JLMC interest-arbitration awards on mass.gov; those are not the signed CBAs. Added a separate `cba_source_url` so the *source of the contract text* is recorded explicitly, per the verification standard.
- **Worcester matched non-safety switched from teachers (EAW) to clerical/DPW.** EAW teacher contracts are not on the city HR portal (separate school employer, member-gated union site) and would need a c.66 request; NAGE Local 490 (clerical) and Teamsters Local 170 (DPW) are on the *same* portal as the fire CBA across overlapping cycles — a cleaner matched pair, so the target was changed.
- **All 5 logged as `verified_portal`** even where the cleanest safety text is an arbitration award (Quincy, Arlington police) or a FOIA-released PDF (Somerville police): a findable, obtainable in-window source exists for each. Caveats (signed-CBA-vs-award, fire-needs-c.66, scanned→OCR) are written into the row notes, not hidden behind the status.

**Surprises / breakage**
- **No outright FOIA-only or dead-weight cities** among the five — better than expected. The nuance is in *route*, not existence: Somerville has no city CBA portal at all (relies on MuckRock + MA DLR), and Quincy's signed police CBAs (vs. the awards) would still need a records request.
- City/town HR sites (Newton, Arlington) return **HTTP 403 to automated fetchers** — anti-bot. Documents are real and browser-downloadable, so collection will be manual `public_download`, consistent with the no-scraping discipline.
- Heavy **false-positive noise** from same-named places (Quincy IL; Arlington VA/TX/IL) — excluded; only the MA sources retained.
- Somerville police PDFs are scanned scanner output → expect `text_quality = ocr_messy` at collection.

**Corpus snapshot**
- contracts: 0 | discourse: 0 | matched pairs: 0 — unchanged; this was source *verification* only, no downloads. Inventory: 6 MA cities, all 6 `verified_portal` (Boston template + 5 verified this session).

**Next steps**
- Begin **matched collection** from verified sources, safety + its matched non-safety per city, starting with the cleanest single-portal case (Worcester) and Boston.
- For Somerville fire and Quincy signed police CBAs, queue **c.66 records requests** if the award/FOIA-release text proves insufficient.
- Route the first real documents through `inbox/` + `inbox/manifest.csv` + `python ingest/process_inbox.py`; then re-run `python ingest/audit_coverage.py` and update `data/city_coverage.csv`.

---

## 2026-06-15 — Project setup

**Did**
- Stood up the corpus-construction pipeline: schema (`docs/schema.md`), validator (`scripts/validate.py`), and ingestion layer (`ingest/`).
- Created Python venv, installed `requirements.txt`, installed system deps (poppler, tesseract).
- Initialized local git (no remote for now).
- Verified environment: `ingest/test_pipeline.py` → 18/18 passing; `scripts/validate.py` → passes on empty corpus.

**Decisions (and why)**
- `corpus/` stays **local**, not pushed — licensed (Westlaw/Lexis) and FOIA material can't be redistributed. If a GitHub remote is added later, uncomment `corpus/` in `.gitignore` *before* first push.
- Repo kept local for now; no GitHub remote yet.
- LLM span fallback: using an **Anthropic** key for `llm_pass()` only (Option C); GABRIEL toolchain stays on OpenAI separately. Two keys coexist.
- Clarified scope: this pipeline *builds the corpus*; GABRIEL is the *later* measurement layer that scores it. Distinct stages.

**Surprises / breakage**
- venv creation failed because the parent folder `Pol/Fire` was stored on disk as `Pol:Fire` (Finder shows `/`, filesystem uses `:`, which is the PATH separator). Renamed parent to a colon-free name to fix.

**Corpus snapshot**
- contracts: 0 | discourse: 0 | matched pairs: 0 — empty baseline, environment verified.

**Next steps**
- Run one real CBA through `inbox/foia/` + `inbox/manifest.csv` + `python ingest/process_inbox.py`.
- Inspect the unresolved-spans report to see whether the regex patterns match real contract language (arbitration / comparability / me-too phrasing varies by jurisdiction).
- Begin matched collection: for each safety unit, grab at least one non-safety unit in the same city + cycle.

---

<!-- Template for new entries — copy above this line:

## YYYY-MM-DD — <short title>

**Did**
-

**Decisions (and why)**
-

**Surprises / breakage**
-

**Corpus snapshot**
- contracts: N | discourse: N | matched pairs: N | gaps: ...

**Next steps**
-

-->
