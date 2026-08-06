# AGG-TIER

Scope: primary tier assignment.

```json
[
  {
    "rule_id": "TIER-1",
    "value": "tier_1_strict_claim_safe",
    "basis": "all strict compatibility and traceability gates"
  },
  {
    "rule_id": "TIER-2",
    "value": "tier_2_bounded_analytically_usable",
    "basis": "compatible value with explicit bounded caveat"
  },
  {
    "rule_id": "TIER-3",
    "value": "tier_3_directional_or_mechanism_supporting",
    "basis": "direction/mechanism supported; not a clean point estimate"
  },
  {
    "rule_id": "TIER-4",
    "value": "tier_4_context_only",
    "basis": "context retained; insufficient for claim calculation"
  },
  {
    "rule_id": "REJECT",
    "value": "rejected",
    "basis": "wrong subject/unit, incompatible, duplicate-only, conflict, or unsupported"
  }
]
```
