# Future Live Verification Commands — VERIFICATION-SCALE-ROUND2-3X1000-REMAINDER-2026-07-24

**Do not run these commands without separate explicit live authorization.**
Run each lane only after its dry run passes. Keep concurrency conservative,
write only lane-local artifacts, and stop before any ledger merge.

## Lane 1

```bash
python scripts/verify_candidate_sources.py \
  --input-csv docs/analysis/verification_rounds/VERIFICATION-SCALE-ROUND2-3X1000-REMAINDER-2026-07-24/lane_1_verification_input.csv \
  --output-dir tmp/verification_rounds/VERIFICATION-SCALE-ROUND2-3X1000-REMAINDER-2026-07-24/lane_1_live_attempt1 \
  --candidate-artifact-dir tmp/verification_rounds/VERIFICATION-SCALE-ROUND2-3X1000-REMAINDER-2026-07-24/lane_1_live_attempt1/candidate_artifacts \
  --timeout 20 \
  --connect-timeout 8 \
  --read-timeout 15 \
  --max-redirects 5 \
  --max-bytes 10485760 \
  --concurrency 8 \
  --no-write-content-samples \
  --respect-robots-note
```

## Lane 2

```bash
python scripts/verify_candidate_sources.py \
  --input-csv docs/analysis/verification_rounds/VERIFICATION-SCALE-ROUND2-3X1000-REMAINDER-2026-07-24/lane_2_verification_input.csv \
  --output-dir tmp/verification_rounds/VERIFICATION-SCALE-ROUND2-3X1000-REMAINDER-2026-07-24/lane_2_live_attempt1 \
  --candidate-artifact-dir tmp/verification_rounds/VERIFICATION-SCALE-ROUND2-3X1000-REMAINDER-2026-07-24/lane_2_live_attempt1/candidate_artifacts \
  --timeout 20 \
  --connect-timeout 8 \
  --read-timeout 15 \
  --max-redirects 5 \
  --max-bytes 10485760 \
  --concurrency 8 \
  --no-write-content-samples \
  --respect-robots-note
```

## Lane 3

```bash
python scripts/verify_candidate_sources.py \
  --input-csv docs/analysis/verification_rounds/VERIFICATION-SCALE-ROUND2-3X1000-REMAINDER-2026-07-24/lane_3_verification_input.csv \
  --output-dir tmp/verification_rounds/VERIFICATION-SCALE-ROUND2-3X1000-REMAINDER-2026-07-24/lane_3_live_attempt1 \
  --candidate-artifact-dir tmp/verification_rounds/VERIFICATION-SCALE-ROUND2-3X1000-REMAINDER-2026-07-24/lane_3_live_attempt1/candidate_artifacts \
  --timeout 20 \
  --connect-timeout 8 \
  --read-timeout 15 \
  --max-redirects 5 \
  --max-bytes 10485760 \
  --concurrency 8 \
  --no-write-content-samples \
  --respect-robots-note
```

The bounded live path is implemented, but these commands require a
separate explicit live-verification authorization. They never ingest,
codify, extract wages, or calculate gaps.
