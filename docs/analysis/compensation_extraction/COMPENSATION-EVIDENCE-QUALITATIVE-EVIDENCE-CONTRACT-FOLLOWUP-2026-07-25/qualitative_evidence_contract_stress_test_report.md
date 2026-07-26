# Qualitative evidence-contract stress-test report

The focused suite exercises wrong tier counts, duplicate IDs, exact-row hash and offset corruption, ambiguous/unavailable candidate leakage, historical-QA overwrite, forbidden page-text columns, carried-file drift, wrong future-prompt selection, output-boundary violations, and analysis-readiness promotion. All failures are required to stop closed.

Evidence-contract tests: 37/37 passed. Predecessor span-disambiguation tests: 32/32 passed. Materialization-time and complete-output invariants passed.

The hardening loop caught one orchestration defect: complete-output prompt validation ran before prompt creation. The partial task-only output was discarded, validation was made phase-aware, two regression tests were added, and clean rematerialization passed without weakening any evidence or readiness guard.
