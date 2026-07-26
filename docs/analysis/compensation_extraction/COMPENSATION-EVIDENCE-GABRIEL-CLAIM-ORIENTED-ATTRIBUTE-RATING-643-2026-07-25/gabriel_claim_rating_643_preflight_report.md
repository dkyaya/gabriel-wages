# GABRIEL claim-rating preflight

- Result: **passed**.
- Representative input rows: 8.
- Strict-schema and exact-quote valid: 8.
- Quarantined/invalid: 0.
- Backend/model: `huit_openai_responses_direct_sdk` / `gpt-5.4-nano`.
- Raw prompts saved: 0. Raw responses saved: 0.
- Global analysis readiness: false.

## Coverage

The deterministic selector covered automatic raises, bargaining/settlement, market/comparability, rank/specialization, implementation timing, fiscal constraints when present, parity/equity, strike/no-strike language when present, and one difficult/short row. Absence of a corpus match is recorded rather than fabricated.

```json
{
  "automatic_raise": {
    "present_in_manifest": true,
    "selected_evidence_id": "qualitative:lobs_01fde53ca68eab05b472dac3"
  },
  "bargaining_settlement": {
    "present_in_manifest": true,
    "selected_evidence_id": "qualitative:lobs_002c1605061ebac04849affa"
  },
  "difficult_weak": {
    "present_in_manifest": true,
    "selected_evidence_id": "qualitative:lobs_420384d7d8c13d1f4c3f1cf6"
  },
  "fiscal_constraint": {
    "present_in_manifest": true,
    "selected_evidence_id": "qualitative:lobs_20851a55680ee9e68dda3ab1"
  },
  "implementation_timing": {
    "present_in_manifest": true,
    "selected_evidence_id": "qualitative:lobs_0061e768a4924ce0613c5725"
  },
  "market_comparability": {
    "present_in_manifest": true,
    "selected_evidence_id": "qualitative:lobs_0243e0cd2d60f9c9fd4c0959"
  },
  "parity_equity": {
    "present_in_manifest": true,
    "selected_evidence_id": "qualitative:lobs_4b7fa2ac4dc2c0441ed90118"
  },
  "rank_specialization": {
    "present_in_manifest": true,
    "selected_evidence_id": "qualitative:lobs_028611b71918af6461eeb646"
  },
  "strike_no_strike": {
    "present_in_manifest": false,
    "selected_evidence_id": null
  }
}
```

Live rating is authorized by this preflight gate.
