# Dashboard status repair lane

The dashboard contract now requires the accelerator decision, blocker counts, invariants, and `analysis_readiness=false`. Repair, prompt, and simulation stages cannot mark global readiness true. The phase is a limited-promotion prompt authorization, not data promotion or analysis readiness.
