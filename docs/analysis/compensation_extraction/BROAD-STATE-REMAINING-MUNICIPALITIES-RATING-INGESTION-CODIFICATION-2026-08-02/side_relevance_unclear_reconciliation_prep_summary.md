# Full unclear side-relevance reconciliation preparation

All **13,180** spans whose current side-relevance rating is `unclear` are in the locked reconciliation queue. The queue is tiered for execution order but is not filtered; weak, local-context, navigation/reference, manual-review, and write-off records remain included.

No reconciliation or relabeling occurred in this ingestion task. The next task must inspect every unclear item and assign police, fire, safety-combined, non-safety, mixed, or not-applicable only when the bounded metadata and context support that result. Unrecoverable items must remain unclear or be written off with a documented reason.

Tier counts: `{"tier_1_high_value_downstream": 6516, "tier_2_manual_or_strong_support": 2175, "tier_3_local_context_or_directional": 1665, "tier_4_weak_reference_or_writeoff": 2824}`. Rows missing one or more required reconciliation fields: **0**.
