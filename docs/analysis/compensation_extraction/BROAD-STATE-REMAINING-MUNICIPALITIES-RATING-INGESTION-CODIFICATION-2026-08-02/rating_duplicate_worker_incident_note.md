# Preserved rating orchestration incident

The rating phase recorded `duplicate_worker_execution_after_supervisor_ownership_loss` in `gabriel_rating_lane_004`. **290** already-accepted packets were redundantly executed after supervisor ownership was lost. The canonicalization rule retained the earliest schema-valid terminal result per locked packet and removed duplicate outputs. The locked queue did not change, no accepted canonical output was discarded, and the final canonical source/span IDs are unique.

This ingestion used only those canonical merged ledgers. It did not repeat rating or ingest duplicate worker outputs.
