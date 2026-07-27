# Stress-test report

- Missing, wrong-size, or hash-drifted files stop before inspection.
- Malformed, locked, empty, oversized, and weak files fail into explicit defer/review lanes.
- PDF text signals are capped at three pages, counted numerically, and discarded; HTML reads are capped at 256 KiB.
- The octet-stream row is routed only by an unambiguous local header and keeps its recorded content type.
- Prior exclusions, non-retained rows, and Tier A/B/D rows cannot enter the lock.
- Missing map date, unsafe dashboard readiness, readiness errors, or partial outputs prevent completion.
- A completed `--resume` performs validation only and writes nothing.
