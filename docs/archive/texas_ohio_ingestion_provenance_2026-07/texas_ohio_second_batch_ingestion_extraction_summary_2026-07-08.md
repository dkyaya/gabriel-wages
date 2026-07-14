# Texas/Ohio Second-Batch Ingestion/Extraction Summary — 2026-07-08

Controlled follow-up run resolving the held-out Texas/Ohio targets left open by the first-batch live acquisition (commit `4134f45`). Bounded public web checks only — no GABRIEL, Harvard Proxy, or model/API calls.

## Held-out targets reviewed

1. Houston fire full-CBA target — **unresolved**.
2. Austin fire cycle-specific target — **resolved and ingested**.
3. Austin non-safety source — **resolved as context-only** (not a matched CBA).
4. Austin budget/pay-plan URL — **resolved, context-only**.
5. Cleveland budget/pay-plan URL — **resolved, context-only**.
6. Ohio SERB archive path — **resolved, context-only** (URL now returns HTTP 200; previously 404).

Full detail: `docs/analysis/texas_ohio_heldout_source_resolution_2026-07-08.csv`.

## Newly resolved sources

One causal agreement source was resolved and fetched: the Austin Firefighters Association Local 975 CBA (2023-2025), confirmed via the official austintexas.gov labor-relations page's own "Current Agreement" label and a full 100-page clean-text read (`ingest/extract_text.py`, text_layer method).

Three context-only sources were resolved but intentionally not fetched/stored, per task scope (budget/pay-plan and source-discovery material is recorded as a citation, not downloaded): Austin's civil-service compensation pages, Cleveland's 2025 Budget Book, and the Ohio SERB document archive.

One target (Austin AFSCME Local 1624) was resolved to a specific document (City Council Resolution No. 20260122-049, a consultation-policy resolution) but confirmed **not** to qualify as a wage-setting CBA, closing an open design question from prior sessions.

One target (Houston fire) remains unresolved: no official houstontx.gov copy of the full executed HPFFA/IAFF Local 341 CBA was located this session, only a City Council presentation slide deck and a non-official news mirror.

## Fetched sources

- `corpus/tx_austin/tx_austin_afa975_fire_cba_2023_2025.pdf` (697,381 bytes, sha256 `637bb2b1...`, clean text quality).

## Rows added to `data/contracts.csv`

- `tx_austin_fire_2023` — Austin Firefighters Association Local 975, `occupation_class=fire`, cycle 2023-09-24 to 2025-09-30. `interest_arbitration_flag=1` and `no_strike_clause_flag=1`, both with verbatim-captured text; `longevity_pay_flag=1` with detail captured.

Contracts count: 41 → **42**.

## Rows added to `data/city_coverage.csv`

- One row for `tx_austin_fire_2023` (city_id `tx_austin`, occupation_class `fire`, safety_flag 1, cycle_window `2023-2025`, have_contract 1), per the repo's established convention of a coverage row per new contract.

Coverage count: 41 → **42**.

## Austin matching status after this run

Austin now has **two** unmatched safety units: `tx_austin_police_2024` (already unmatched before this run) and the newly added `tx_austin_fire_2023`. Austin still has **no** matched non-safety comparison unit — the AFSCME Local 1624 consultation agreement was confirmed not to qualify, and the civil-service pay-plan pages are context-only, not a bargaining-unit CBA. **Austin remains dead weight for the matched-comparison design until a genuine non-safety CBA/meet-and-confer agreement is located** (per `AGENTS.md`'s coverage-discipline rule, this is flagged rather than left silent).

## Houston matching status after this run

Unchanged from the first batch: Houston police (`tx_houston_police_2024`) and Houston non-safety (`tx_houston_other_2024`) remain a healthy overlap-cycle matched pair. Houston fire remains unresolved and not ingested, so Houston's three-tier institutional structure (compulsory-arbitration fire, meet-and-confer police, meet-and-confer non-safety) is still only two-thirds represented in the corpus.

## Remaining unresolved/context-only targets

- Houston fire full-CBA target (highest remaining priority — see `docs/analysis/texas_ohio_heldout_source_resolution_2026-07-08.csv` row 1 for the specific next-search leads: houstontx.gov HR/legal document folders were checked and did not surface a full-text copy this session).
- Austin non-safety CBA/meet-and-confer equivalent (still entirely unidentified; the consultation agreement does not substitute for it).
- Austin, Cleveland budget/pay-plan pages and the Ohio SERB archive remain context-only citations by design, not acquisition targets.

## Recognition-clause findings

Not applicable to a new broad non-safety row this session (none was fetched). The one newly fetched row (`tx_austin_fire_2023`) is a single-occupation fire unit; its recognition clause was still read and confirmed unambiguous (`occupation_class=fire`, final not provisional). See `docs/analysis/texas_ohio_second_batch_recognition_clause_extraction_2026-07-08.md`/`.csv`.

## Mechanism-excerpt highlights

- **Arbitration/impasse backstop, present:** the Austin fire CBA's own effective date is tied to "the date of the award in the interest arbitration proceeding that implements this Agreement," and a successor impasse extends the Agreement pending mutually-agreed "mediation or interest arbitration" — the general (non-compulsory-for-Austin) Chapter 174 model, contrasted with Houston Fire's population-triggered compulsory arbitration under §174.1535.
- **Overtime/staffing, present:** overtime is explicitly tied to "staffing levels established by the Fire Department's staffing policies."
- **Training/certification and premium pay, present:** Education Incentive Pay/Firefighter Certification Pay, and Bilingual Translation Pay/Staff Schedule Pay as distinct special-pay categories.
- **Peer-wage comparability and subcontracting, not_found.**

Full table: `docs/analysis/texas_ohio_second_batch_mechanism_excerpt_extraction_2026-07-08.csv`.

## Validation/audit results

```text
python scripts/validate.py
VALIDATION PASSED — all rows conform to docs/schema.md
  contracts: 42 | discourse: 0 | coverage: 42 | city_attributes: 3

python ingest/audit_coverage.py
contracts: 42 | discourse: 0 | coverage: 42 | city_attributes: 3 | cities: 13
healthy matched pairs: 15
  exact-cycle: 9
  overlap-cycle: 6
exploratory adjacent matches: 2
safety units unmatched: 5
unmatched safety obs_ids: ma_somerville_police_spsoa_2012, ma_somerville_police_spea_2012,
  ma_newton_police_2015, tx_austin_police_2024, tx_austin_fire_2023
```

**No GABRIEL calls. No Harvard Proxy calls. No model/API calls from project scripts. No PRRs/FOIA. No statutes, budgets, pay plans, or SERB archive pages were ingested as causal rows. No meet-and-confer or consultation agreement was classified as `arbitration_award`. No wage panels or final PDF/DOCX artifacts were built. `docs/schema.md` was not modified.**

## Recommended next step

Prioritize a dedicated search for an official houstontx.gov full-text copy of the HPFFA/IAFF Local 341 CBA (check HR/legal/city-attorney document folders beyond the HR/hrfiles paths already searched, or the City Secretary's contract records index) before any further Texas/Ohio acquisition. Separately, Austin's non-safety comparison gap is now the more analytically consequential hole: with two Austin safety units in the corpus and no non-safety partner, Austin is the least-matched of the four first-batch cities and should be the next city-specific source-discovery target — specifically, confirming whether any actual wage-negotiating body exists for Austin municipal employees beyond the civil-service classification system and the newly confirmed (non-wage-setting) consultation agreement.
