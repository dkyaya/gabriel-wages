# Future text-extraction parallel-lane standard

Large local text passes use four isolated, resumable workers at T+0, T+8, T+16, and T+24 minutes with controlled overlap. Workers may write full text only to ignored artifact storage and never mutate shared dashboard or summary outputs.
