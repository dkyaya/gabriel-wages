# Final provisional merge prompt-prep validation - 2026-07-25

## Authority and input checks

- Starting tracked commit contains independent review pass: pass
- Authority decision is `independent_review_pass_final_provisional_merge_prompt_allowed`: pass
- Authority still says final provisional merge is not authorized: pass
- Five corrected shadow ledgers exist: pass
- Current SHA-256 values equal the independent-review record: pass
- Analysis readiness before prompt preparation is false: pass

## Future prompt contract checks

- Exactly five corrected shadow ledgers are named as merge-data inputs: pass
- No sixth data ledger or document source is allowed: pass
- All five exact SHA-256 values are embedded: pass
- SHA-256 verification is required before output-directory creation: pass
- Dry-run and in-memory reconciliation are required first: pass
- Rollback-safe staging and atomic publication are required: pass
- Five output schemas remain separate: pass
- Output ledgers must be byte-for-byte copies of approved inputs: pass
- Observation/case/original IDs and duplicate/canonical links are preserved: pass
- Active/inactive flags and all duplicate provenance rows are preserved: pass
- Bounded page pointers and mixed join keys are preserved: pass
- Source-review, text-table detection, content hash, unit/state/source metadata are preserved: pass
- Both explicitly unresolved groups and their observation IDs are named and must remain unresolved: pass
- OCR-later documents are explicitly excluded: pass
- Output is prohibited from `data/`, `corpus/`, ingestion, codified, and analysis locations: pass
- Stop-before-ingestion and stop-before-codification rules are explicit: pass
- Analysis readiness must remain false: pass
- A separate future user authorization is required before execution: pass

## Prompt-prep action checks

- Final provisional merge executed: no
- Final provisional package created: no
- GABRIEL/API/model call: no
- New extraction or document selection: no
- URL/search/download/OCR/scout/source review/verification: no
- Ingestion or `gabriel.codify`: no
- Wage-gap calculation, regression, or causal analysis: no
- Corrected shadow or durable ledger mutation: no
- Full document/page text, full tables, raw model prompts/responses, or image copies saved: no

## Focused and repository-wide validation

- `.venv/bin/python -m py_compile scripts/build_dashboard_data.py`: pass
- `.venv/bin/python scripts/build_dashboard_data.py`: pass; 51 states/DC,
  35,589 municipalities, 2,436 scout-covered municipalities, and 4,726
  candidate rows
- `npm --prefix docs/dashboard run build`: pass; Vite build completed (the
  existing large-chunk advisory remains non-fatal)
- focused prompt-contract check: pass; exactly five allowed input names, all
  five SHA-256 values, both unresolved IDs, five separated schemas, provenance
  fields, stop rules, absent final output directory, and false analysis
  readiness
- `.venv/bin/python scripts/validate.py`: pass; 64 contracts, 0 discourse,
  64 coverage rows, and 3 city-attribute rows
- `.venv/bin/python ingest/test_pipeline.py`: pass; 60 passed, 0 failed
- `.venv/bin/python ingest/audit_coverage.py`: pass; 19 cities, 28 healthy
  matched pairs (10 exact and 18 overlap), 2 exploratory adjacent matches, and
  6 unmatched safety units
- `git diff --check`: pass
- post-work hashes for all five corrected inputs: pass, 5 / 5 unchanged
- protected durable/prior/corrected ledgers changed: no
- final provisional output directory or merged package created: no
- prompt-prep output scope: pass; three Markdown/JSON prompt metadata files
  only
- secret/auth-bearing artifact scan: pass; no matches

## Dashboard validation

- Phase: `compensation_extraction_final_provisional_merge_prompt_prepared`
- Future prompt prepared: true
- Final provisional merge ran: false
- Final provisional merge currently allowed: false
- Next recommendation:
  `await_separate_authorization_to_run_final_provisional_merge_prompt`
- Wage/qualitative stage:
  `provisional_final_merge_prompt_prepared_not_run_not_analysis_ready`
- Analysis readiness: false
