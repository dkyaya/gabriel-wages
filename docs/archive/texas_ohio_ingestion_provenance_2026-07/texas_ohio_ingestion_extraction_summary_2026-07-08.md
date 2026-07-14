# Texas/Ohio Ingestion and Extraction Summary — 2026-07-08

This summary covers the first controlled live Texas/Ohio source acquisition run. It fetched only the nine dry-run rows marked `ready_for_live_fetch` and `approved_first_batch`. No GABRIEL, Harvard Proxy, model/API scoring, PRR/FOIA, context-only source ingestion, budget/pay-plan ingestion, statute ingestion, wage-panel build, or final PDF/DOCX artifact generation occurred.

## Scope And Fetch Results

- Sources selected for live fetch: 9
- Sources fetched and stored: 9
- Failed fetches: 0
- Held-out/proposed-but-not-added dry-run rows recorded in metadata additions file: 11
- Files added under `corpus/`: 9 PDFs

## Metadata Results

- Rows added to `data/contracts.csv`: 9
- Rows added to `data/city_coverage.csv`: 9, because repo convention requires coverage rows for added contracts and validation/audit use that table.
- Corpus count changed from 32 contracts / 32 coverage rows to 41 contracts / 41 coverage rows.
- `source_type=cba` was used for CBAs and meet-and-confer agreements because the schema has no separate meet-and-confer value.
- Broad non-safety agreements were kept as `occupation_class=other` after recognition-clause-first review.

## Recognition-Clause-First Findings

- `tx_houston_other_2024`: recognition/classification text indicates broad mixed municipal coverage; conservative `occupation_class=other`. Overlap noted: clerical/admin; public works/DPW; custodial/facilities; technical/general municipal; health/nurse; library possible but not separately itemized in excerpt; excludes classified police/fire
- `oh_columbus_other_2024`: recognition/classification text indicates broad mixed municipal coverage; conservative `occupation_class=other`. Overlap noted: clerical/admin; building/zoning; technical/general municipal; dispatcher/public-safety civilian; public works/DPW possible through Appendix A but not isolated here
- `oh_cleveland_other_2022`: recognition/classification text indicates broad mixed municipal coverage; conservative `occupation_class=other`. Overlap noted: clerical/admin; public works/utilities; building/facilities; technical/general municipal; public health; dispatcher/public-safety civilian; airport/ARFF-adjacent titles

## Mechanism Excerpt Findings

- Mechanism extraction is recorded in `texas_ohio_mechanism_excerpt_extraction_2026-07-08.md` and `.csv` as source-text evidence only.
- Recurring extracted categories include classification/wage schedules, overtime/callback rules, training/certification provisions, premium/differential pay, benefits, no-strike/management-rights language, and public-safety/safety language where present.
- Generic grievance arbitration text was marked `unclear` where it did not plainly establish a wage-setting/impasse backstop.

## Remaining URL-Confirmation Targets

- Houston fire full-CBA target.
- Austin fire cycle-specific target.
- Austin pay-plan URL.
- Cleveland budget/pay-plan URL.
- Ohio SERB archive path.

## Validation And Coverage Audit

- `python scripts/validate.py`: passed; 41 contracts, 0 discourse rows, 41 coverage rows, 3 city attributes.
- `python ingest/audit_coverage.py`: 41 contracts, 15 healthy matched pairs, 2 exploratory adjacent matches, 4 unmatched safety units.
- Newly relevant unmatched/adjacent status: Austin police remains unmatched; Cleveland police/fire have adjacent, not healthy, non-safety matches because Local 100 ends in 2025 while safety cycles begin in 2025.

## Recommended Next Step

Confirm the remaining held-out Texas/Ohio URL targets before any second live acquisition. The highest-value next acquisition is Austin fire/non-safety confirmation to avoid leaving Austin police as unmatched dead weight; separately confirm Houston fire if the project wants a full Houston police/fire/non-safety trio. Codex can run the bounded URL-confirmation/acquisition pass after explicit user approval.
