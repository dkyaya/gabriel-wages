# Four-lane fixed-stagger live scouting summary

Decision: `targeted_scouting_four_lane_fixed_stagger_live_completed_candidate_review_ready`.

All four immutable 500-target queues passed hash and scope checks. Lane starts used T+0/T+8/T+16/T+24 minimum offsets with explicitly authorized controlled overlap, one sequential request stream per lane, and no uncontrolled fanout. The live scout retained 4228 candidate-only source leads: {'lane_1': 1002, 'lane_2': 754, 'lane_3': 1260, 'lane_4': 1212}. 549 skip/duplicate records were preserved. Candidates remain unverified, unextracted, unrated, and non-causal. Global analysis readiness remains false.
