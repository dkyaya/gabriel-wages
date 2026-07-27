# Validation report — live dashboard content audit/fix

## Required command results

- `.venv/bin/python -m py_compile scripts/build_dashboard_data.py scripts/run_live_dashboard_content_audit_fix.py scripts/test_live_dashboard_content_audit_fix.py` — passed.
- `.venv/bin/python scripts/test_dashboard_fix_and_tier_c_source_review_download_556.py` — 26/26 passed.
- `.venv/bin/python scripts/test_targeted_tier_c_verification_from_bounded_memo_gaps.py` — 15/15 passed.
- `.venv/bin/python scripts/test_bounded_internal_mechanism_linkage_claim_memo.py` — 17/17 passed.
- `.venv/bin/python scripts/test_live_dashboard_content_audit_fix.py` — 11/11 passed.
- `.venv/bin/python scripts/build_dashboard_data.py` — passed; 51 states/DC, 35,589 municipalities, 2,436 scout-covered, 4,726 historical candidate rows.
- `npm --prefix docs/dashboard run build` — passed; Vite production bundle generated (non-blocking chunk-size advisory only).
- `.venv/bin/python scripts/validate.py` — passed; contracts 64, discourse 0, coverage 64, city attributes 3.
- `.venv/bin/python ingest/test_pipeline.py` — 60 passed, 0 failed.
- `git diff --check` — passed.

## Deterministic invariants

- completed source-review inputs present;
- 556 source-review results reconcile to 463 retained files plus 93 exclusions/deferred outcomes;
- all 463 retained files exist locally;
- no download rerun or retained-file content access occurred;
- generated dashboard data contains 463/556 and memo scope 268/208/90;
- exactly one current dashboard report exists and links to the bounded memo;
- discovery-era sections are explicitly historical;
- the post-fix local bundle contains current phase/readiness strings and no forbidden stale current-facing markers;
- global analysis readiness remains false.
