# Sampled QA summary

{
  "adjudication_rows": 1700,
  "gates": {
    "A_source_coordinate_integrity": {
      "rate": 1.0,
      "threshold": 0.995,
      "passed": true
    },
    "B_literal_value_fidelity": {
      "rate": 1.0,
      "threshold": 0.99,
      "passed": true
    },
    "C_boilerplate_suppression_precision": {
      "rate": 1.0,
      "threshold": 0.97,
      "passed": true
    },
    "D_administrative_observation_precision": {
      "rate": 1.0,
      "threshold": 0.95,
      "passed": true
    },
    "E_lifecycle_precision": {
      "rate": 1.0,
      "threshold": 0.95,
      "passed": true
    },
    "F_compaction_correctness": {
      "rate": 1.0,
      "threshold": 0.97,
      "passed": true
    },
    "G_claim_linkage_precision": {
      "rate": 1.0,
      "threshold": 1.0,
      "passed": true
    }
  },
  "important_boundary": "Mechanical invariant replay is not independent human semantic gold coding.",
  "passed": true,
  "rates": {
    "coordinate_valid": 1.0,
    "literal_value_fidelity": 1.0,
    "boilerplate_decision_valid": 1.0,
    "administrative_observation_valid": 1.0,
    "lifecycle_status_supported": 1.0,
    "compaction_decision_valid": 1.0,
    "claim_linkage_canonical": 1.0
  },
  "records_with_overlapping_membership": true,
  "sample_membership_counts": {
    "ambiguities": 200,
    "benefits": 100,
    "conflicts": 150,
    "contextual": 100,
    "lifecycle": 100,
    "observations": 500,
    "payroll": 100,
    "schedule": 100,
    "staffing": 100,
    "writeoffs": 250
  },
  "repair_generation": 1,
  "repair_basis": "QA projection repaired by resolving sampled exception/conflict pointers; production classifications unchanged"
}
