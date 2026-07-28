# Validation report

Coordinator invariants passed for the locked queue, four completed lanes, artifact integrity, controlled statuses, ignored storage, controlled overlap, and prohibited-action boundaries. Repository test/build command results are added after execution.

## Completed command results

- Python compilation for the dashboard builder, extraction runner, and extraction tests: PASS.
- Retained-source storage/history repair regression suite: PASS.
- Combined broad PDF/text-layer readiness 4,961 regression suite: PASS.
- Combined broad source-review/download 5,589 regression suite: PASS.
- Dashboard declutter/map-correction/Tier C text-span regression suite: PASS.
- Combined broad text extraction 4,051 fail-closed suite: PASS.
- Dashboard data build: PASS; 6,919 scout-covered municipalities and 13,041 candidate rows preserved.
- Dashboard frontend production build: PASS.
- Repository schema validation: PASS.
- Ingestion pipeline suite: PASS, 60 tests and 0 failures.
- Git whitespace validation: PASS.
- Git artifact policy checks: PASS; no retained-source or extracted-text artifact paths are tracked.

The live checkpoint audit found an over-broad fixed-width spacing heuristic. Workers were stopped,
519 already-saved ignored text artifacts were deterministically reclassified, and workers resumed
against the original absolute stagger schedule. The repair performed zero source re-extractions.
Final start offsets are within one second of 0/480/960/1,440 at second-resolution timestamps, and
all adjacent lanes overlapped.
