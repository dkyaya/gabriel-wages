# Future stage dashboard state contract

Dashboard phase must equal the validated decision and must distinguish partial, blocked, prompt-allowed, promoted, and analysis-ready states. Repair, simulation, prompt-prep, and limited-promotion tasks must keep global analysis readiness false. A dashboard build must fail if counts, decision, invariants, or scope disagree, or if an upstream stage attempts to claim a downstream status.
