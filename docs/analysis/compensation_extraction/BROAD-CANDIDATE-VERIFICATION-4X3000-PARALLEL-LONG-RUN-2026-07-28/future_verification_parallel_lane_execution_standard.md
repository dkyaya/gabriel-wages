# Future parallel verification lane standard

Large verification runs use four isolated, independently locked lanes with T+0/T+8/T+16/T+24 starts, durable per-row checkpoints, bounded HEAD-only transport, no shared worker writes, coordinator-only merge/dashboard updates, and no rerun of valid completed lanes. Every live worker must confirm escalated network permission with a lane-local smoke before processing its queue. A lane-wide uniform `ConnectError` pattern must stop and quarantine the attempt; sandbox-denied rows must never be counted as live verification outcomes.
