# Parallel live rating execution

Four independently resumable OS worker lanes used the standard T+0/T+8/T+16/T+24 schedule (actual start offsets in minutes: {'rating_lane_001': 0.0, 'rating_lane_002': 8.57, 'rating_lane_003': 16.36, 'rating_lane_004': 24.92}). Adjacent controlled overlap achieved: true. Workers wrote only isolated lane directories; the coordinator merged outcomes after all lanes completed.
