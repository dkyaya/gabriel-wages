# Future source-review/download parallel-lane standard

Large retrieval runs use four isolated, checkpointed, resumable workers with 0/8/16/24-minute staggered starts. Workers never update shared dashboard state; a coordinator merges terminal outputs and updates status once. Completed lanes are never rerun.
