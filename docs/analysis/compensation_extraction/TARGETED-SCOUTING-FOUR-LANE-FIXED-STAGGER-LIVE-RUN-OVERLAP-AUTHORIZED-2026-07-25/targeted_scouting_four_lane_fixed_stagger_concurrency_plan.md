# Fixed-stagger controlled-overlap plan

- Lane 1: T+0 minutes.
- Lane 2: no earlier than T+8 minutes.
- Lane 3: no earlier than T+16 minutes.
- Lane 4: no earlier than T+24 minutes.
- Controlled overlap after each delayed start: explicitly authorized and used when an earlier lane remained active.
- Maximum orchestrated lane workers: four.
- Intra-lane parallelism: one sequential request at a time.
- SDK retries: zero; two consecutive transport failures stop the affected lane gracefully.
- No target movement, cross-lane queue use, or mid-run target addition is allowed.
- Prompts and raw responses remain in memory only and are discarded after parsing.
