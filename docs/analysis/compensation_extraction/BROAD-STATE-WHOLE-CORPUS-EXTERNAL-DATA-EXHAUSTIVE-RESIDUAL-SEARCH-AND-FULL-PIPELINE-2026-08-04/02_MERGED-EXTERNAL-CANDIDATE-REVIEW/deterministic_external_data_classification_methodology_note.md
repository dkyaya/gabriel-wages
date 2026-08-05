# Deterministic external-data classification methodology

New administrative records will not automatically receive GABRIEL scores. Explicit structured values—including payroll amounts, overtime, headcount, vacancies, salary schedules, dates, contribution rates, and structured government tables—will be classified through deterministic and locally auditable rules. Ambiguous narrative records will be routed to manual review or `pending_gabriel_or_manual_narrative_review`.

New external administrative evidence was classified through deterministic and locally auditable rules rather than GABRIEL scoring because hosted-search/API capacity became unavailable. Explicit structured values were processed directly; ambiguous narrative evidence was retained for manual or future model-assisted review.

This approach changes the confidence and completeness of the external administrative layer; it does not change the validity of documentary mechanism claims already supported by the existing corpus. Deterministic labels are not GABRIEL scores and must never be represented as equivalent. Rule versions, source fields, evidence locations, and QA decisions must remain available for audit.
