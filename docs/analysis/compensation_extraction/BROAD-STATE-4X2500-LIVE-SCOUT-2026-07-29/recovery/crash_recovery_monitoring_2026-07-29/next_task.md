# Next task

Monitor the four existing BROAD-STATE-4X2500 live-scout worker PIDs; do not launch duplicate workers while their checkpoints advance.

If every lane reaches `completed` with exactly 2,500 unique accepted terminal outcomes, run the existing coordinator with the same passed preflight-attempt-2 directory, validate the merged outputs, rebuild the dashboard using parseable completed-lane outcomes only, keep global analysis readiness false, and create the normal final live-scout relay.

If workers stop first, rerun this recovery audit. Resume only lanes whose checkpoint is incomplete and integrity-valid, beginning at each lane's then-current next unaccepted target. Do not run candidate review, verification, downloads, source inspection, extraction, rating, ingestion, or codification.

Current snapshot next targets:

- `scout_lane_001`: `B4X2500-20260729-01993`
- `scout_lane_002`: `B4X2500-20260729-04452`
- `scout_lane_003`: `B4X2500-20260729-06973`
- `scout_lane_004`: `B4X2500-20260729-09450`
