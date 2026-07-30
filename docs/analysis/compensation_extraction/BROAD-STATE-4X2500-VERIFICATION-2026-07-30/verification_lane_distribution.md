# Verification lane distribution

All 5,768 verification-ready rows are locked exactly once.

| lane | high | medium | low | total | stagger |
|---|---:|---:|---:|---:|---:|
| verification_lane_001 | 1,071 | 338 | 33 | 1,442 | T+0 min |
| verification_lane_002 | 1,070 | 338 | 34 | 1,442 | T+8 min |
| verification_lane_003 | 1,070 | 338 | 34 | 1,442 | T+16 min |
| verification_lane_004 | 1,070 | 338 | 34 | 1,442 | T+24 min |

Within each lane, stable proportional interleaving disperses all three priority classes.
