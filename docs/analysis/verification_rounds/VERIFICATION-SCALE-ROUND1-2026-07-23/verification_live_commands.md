# Future Live Verification Commands — VERIFICATION-SCALE-ROUND1-2026-07-23

**Do not run these commands without separate explicit live authorization.**
Run each lane only after its dry run passes. Keep concurrency conservative,
write only lane-local artifacts, and stop before any ledger merge.

## Lane 1

```bash
python scripts/verify_candidate_sources.py \
  --input-csv docs/analysis/verification_rounds/VERIFICATION-SCALE-ROUND1-2026-07-23/lane_1_verification_input.csv \
  --output-dir tmp/verification_rounds/VERIFICATION-SCALE-ROUND1-2026-07-23/lane_1_live_attempt1 \
  --timeout 30 \
  --concurrency 3 \
  --respect-robots-note
```

## Lane 2

```bash
python scripts/verify_candidate_sources.py \
  --input-csv docs/analysis/verification_rounds/VERIFICATION-SCALE-ROUND1-2026-07-23/lane_2_verification_input.csv \
  --output-dir tmp/verification_rounds/VERIFICATION-SCALE-ROUND1-2026-07-23/lane_2_live_attempt1 \
  --timeout 30 \
  --concurrency 3 \
  --respect-robots-note
```

## Lane 3

```bash
python scripts/verify_candidate_sources.py \
  --input-csv docs/analysis/verification_rounds/VERIFICATION-SCALE-ROUND1-2026-07-23/lane_3_verification_input.csv \
  --output-dir tmp/verification_rounds/VERIFICATION-SCALE-ROUND1-2026-07-23/lane_3_live_attempt1 \
  --timeout 30 \
  --concurrency 3 \
  --respect-robots-note
```

The current runner intentionally fails closed in live mode until the
separately authorized live-verification implementation task completes.
These commands never ingest, codify, extract wages, or calculate gaps.
