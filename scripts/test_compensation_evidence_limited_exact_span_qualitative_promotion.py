#!/usr/bin/env python3
"""Adversarial tests for the hardened limited qualitative promotion."""

from __future__ import annotations

import copy
import csv
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import run_compensation_evidence_limited_exact_span_qualitative_promotion as runner


OUTPUT = runner.DEFAULT_OUTPUT_DIR


class PromotionGuardrailTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.material = runner.validate_material_inputs()
        cls.sample = cls.material["exact"][0]

    def test_output_guard_rejects_tmp(self):
        with self.assertRaisesRegex(RuntimeError, "docs/analysis"):
            runner.output_guard(ROOT / "tmp/promotion")

    def test_future_prompt_requires_all_boundaries(self):
        with self.assertRaisesRegex(RuntimeError, "missing constraints"):
            runner.validate_future_prompt("review only")

    def test_future_prompt_validation_is_case_insensitive(self):
        runner.validate_future_prompt("\n".join(value.upper() for value in runner.FUTURE_PROMPT_REQUIRED))

    def test_relay_missing_metadata_fails(self):
        with self.assertRaisesRegex(RuntimeError, "incomplete"):
            runner.validate_relay_metadata({"commit_hash": "abc"})

    def test_relay_complete_metadata_passes(self):
        runner.validate_relay_metadata({key: "recorded" for key in runner.RELAY_REQUIRED})

    def test_dashboard_true_global_readiness_fails(self):
        with self.assertRaisesRegex(RuntimeError, "readiness true"):
            runner.validate_dashboard_state({"analysis_readiness": True, "limited_usage_review_allowed_next": True})

    def test_dashboard_false_global_readiness_passes(self):
        runner.validate_dashboard_state({"analysis_readiness": False, "limited_usage_review_allowed_next": True})

    def test_partial_checkpoint_fails(self):
        with self.assertRaisesRegex(RuntimeError, "Partial"):
            runner.validate_checkpoint({"status": "partial", "processed": 700, "expected": 759})

    def test_complete_checkpoint_passes(self):
        runner.validate_checkpoint({"status": "complete", "processed": 759, "expected": 759})

    def test_exact_row_span_hash_corruption_fails(self):
        row = copy.deepcopy(self.sample); row["span_sha256"] = "0" * 64
        with self.assertRaisesRegex(RuntimeError, "SHA-256"):
            runner.validate_exact_row(row)

    def test_exact_row_span_offset_corruption_fails(self):
        row = copy.deepcopy(self.sample); row["span_end"] = str(int(row["span_end"]) + 1)
        with self.assertRaisesRegex(RuntimeError, "offset"):
            runner.validate_exact_row(row)

    def test_exact_row_blank_page_pointer_fails(self):
        row = copy.deepcopy(self.sample); row["bounded_evidence_pointer"] = ""
        with self.assertRaisesRegex(RuntimeError, "missing"):
            runner.validate_exact_row(row)

    def test_exact_row_missing_provenance_fails(self):
        row = copy.deepcopy(self.sample); row["source_review_id"] = ""
        with self.assertRaisesRegex(RuntimeError, "missing"):
            runner.validate_exact_row(row)

    def test_inactive_exact_row_fails(self):
        row = copy.deepcopy(self.sample); row["current_active"] = "false"
        with self.assertRaisesRegex(RuntimeError, "Inactive"):
            runner.validate_exact_row(row)

    def test_ambiguous_tier_in_exact_input_fails(self):
        row = copy.deepcopy(self.sample); row["evidence_contract_tier"] = "ambiguous_exact_span_navigation"
        with self.assertRaisesRegex(RuntimeError, "Non-exact"):
            runner.validate_exact_row(row)

    def test_historical_mixed_is_not_limited_eligible(self):
        row = copy.deepcopy(self.sample)
        row["current_qa_status"] = "provisional_unverified"
        row["mixed_membership_status"] = "historical_inactive"
        self.assertEqual(runner.eligibility_for(row)["eligible_for_limited_qualitative_use"], "false")

    def test_needs_review_is_not_limited_eligible(self):
        row = copy.deepcopy(self.sample); row["current_qa_status"] = "needs_review"
        self.assertEqual(runner.eligibility_for(row)["eligible_for_limited_qualitative_use"], "false")

    def test_other_is_not_typed_eligible(self):
        row = copy.deepcopy(self.sample); row["mechanism_type"] = "other"
        self.assertEqual(runner.eligibility_for(row)["eligible_for_typed_mechanism_analysis"], "false")

    def test_missing_detail_is_not_typed_eligible(self):
        row = copy.deepcopy(self.sample)
        row["mechanism_type"] = "comparability_or_market_study"
        row["current_qa_status"] = "provisional_unverified"
        row["mixed_membership_status"] = "none"
        for field in runner.DETAIL_FIELDS:
            row[field] = ""
        self.assertEqual(runner.eligibility_for(row)["eligible_for_typed_mechanism_analysis"], "false")

    def test_cycle_flag_requires_exact_cycle(self):
        row = copy.deepcopy(self.sample); row["followup_cycle_bridge_status"] = "quarantined_no_exact_full_date_pair"
        self.assertEqual(runner.eligibility_for(row)["eligible_for_cycle_analysis"], "false")

    def test_occupation_flag_requires_controlled_class(self):
        row = copy.deepcopy(self.sample); row["controlled_occupation_class"] = ""
        self.assertEqual(runner.eligibility_for(row)["eligible_for_occupation_comparison"], "false")

    def test_matched_flag_requires_exact_period_match(self):
        row = copy.deepcopy(self.sample); row["analysis_matching_status"] = "exact_period_unmatched"
        self.assertEqual(runner.eligibility_for(row)["eligible_for_exact_period_matched_set"], "false")

    def test_primary_flag_requires_all_design_gates(self):
        row = copy.deepcopy(self.sample); row["controlled_occupation_class"] = ""
        self.assertEqual(runner.eligibility_for(row)["eligible_for_primary_matched_city_cycle_design"], "false")

    def test_forbidden_payload_field_fails(self):
        with self.assertRaisesRegex(RuntimeError, "Forbidden"):
            runner.validate_no_forbidden_fields(["qualitative_observation_id", "full_page_text"])


class ImmutableAndScopeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hashes = runner.verify_inputs()
        cls.material = runner.validate_material_inputs()
        cls.promoted, cls.eligibility, cls.quarantine, cls.navigation, cls.scopes = runner.derive_rows(cls.material)

    def test_authorized_baseline_is_ancestor(self):
        result = subprocess.run(["git", "merge-base", "--is-ancestor", runner.BASELINE_COMMIT, "HEAD"], cwd=ROOT)
        self.assertEqual(result.returncode, 0)

    def test_all_required_tracked_inputs_verified(self):
        self.assertEqual(len(self.hashes), len(runner.required_paths()))

    def test_exact_input_count_is_759(self):
        self.assertEqual(len(self.material["exact"]), 759)

    def test_tiers_reconcile_to_1954(self):
        self.assertEqual((len(self.material["exact"]), len(self.material["ambiguous"]), len(self.material["unavailable"])), (759, 614, 581))

    def test_no_cross_tier_identity_contamination(self):
        exact = {row["qualitative_observation_id"] for row in self.promoted}
        nav = {row["qualitative_observation_id"] for row in self.navigation}
        self.assertFalse(exact & nav)

    def test_scope_counts_match_frozen_contract(self):
        self.assertEqual(self.scopes, runner.EXPECTED_SCOPE_COUNTS)

    def test_promoted_view_retains_every_exact_row(self):
        self.assertEqual(len(self.promoted), 759)
        self.assertEqual({row["qualitative_observation_id"] for row in self.promoted}, {row["qualitative_observation_id"] for row in self.material["exact"]})

    def test_restricted_exact_count_is_116(self):
        self.assertEqual(len(self.quarantine), 116)

    def test_navigation_count_is_1195(self):
        self.assertEqual(len(self.navigation), 1195)

    def test_historical_mixed_never_limited_eligible(self):
        self.assertFalse(any(row["eligible_for_limited_qualitative_use"] == "true" and row["mixed_membership_status"].startswith("historical") for row in self.promoted))

    def test_other_never_typed_eligible(self):
        self.assertFalse(any(row["eligible_for_typed_mechanism_analysis"] == "true" and row["mechanism_type"] == "other" for row in self.promoted))

    def test_span_values_are_preserved(self):
        source = {row["qualitative_observation_id"]: row for row in self.material["exact"]}
        for row in self.promoted:
            prior = source[row["qualitative_observation_id"]]
            self.assertEqual((row["literal_verbatim_evidence_span"], row["span_start"], row["span_end"], row["span_length"], row["span_sha256"], row["bounded_evidence_pointer"]), (prior["literal_verbatim_evidence_span"], prior["span_start"], prior["span_end"], prior["span_length"], prior["span_sha256"], prior["bounded_evidence_pointer"]))

    def test_dry_run_writes_nothing(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "docs/analysis") as tmp:
            out = Path(tmp) / "promotion"
            result = subprocess.run([sys.executable, str(Path(runner.__file__)), "--dry-run", "--output-dir", str(out)], cwd=ROOT, capture_output=True, text=True, check=True)
            self.assertFalse(out.exists())
            self.assertEqual(json.loads(result.stdout)["writes"], 0)


class MaterializedPromotionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.decision = runner.read_json(OUTPUT / "limited_exact_span_qualitative_promotion_decision.json")
        cls.manifest = runner.read_json(OUTPUT / "limited_exact_span_qualitative_promotion_manifest.json")
        cls.audit = runner.read_json(OUTPUT / "limited_exact_span_qualitative_promotion_audit.json")
        cls.invariants = runner.read_json(OUTPUT / "limited_exact_span_qualitative_promotion_invariant_checks.json")
        cls.promoted_fields, cls.promoted = runner.read_csv(OUTPUT / "limited_exact_span_qualitative_promoted_view.csv")
        cls.eligibility_fields, cls.eligibility = runner.read_csv(OUTPUT / "limited_exact_span_qualitative_row_eligibility.csv")
        cls.quarantine_fields, cls.quarantine = runner.read_csv(OUTPUT / "limited_exact_span_qualitative_quarantine_ledger.csv")
        cls.nav_fields, cls.navigation = runner.read_csv(OUTPUT / "ambiguous_unavailable_qualitative_navigation_preserved.csv")

    def test_decision_allows_only_limited_usage_review(self):
        self.assertEqual(self.decision["decision"], runner.DECISION)
        self.assertTrue(self.decision["limited_usage_review_allowed_next"])
        self.assertFalse(self.decision["global_analysis_readiness"])
        self.assertFalse(self.decision["global_analysis_facing_promotion"])

    def test_promoted_schema_contains_explicit_eligibility(self):
        self.assertTrue(set(runner.PROMOTION_FIELDS) <= set(self.promoted_fields))

    def test_materialized_counts_reconcile(self):
        self.assertEqual((len(self.promoted), len(self.eligibility), len(self.quarantine), len(self.navigation)), (759, 759, 116, 1195))
        self.assertEqual(self.decision["scope_counts"], runner.EXPECTED_SCOPE_COUNTS)

    def test_only_exact_rows_in_promoted_view(self):
        self.assertTrue(all(row["evidence_contract_tier"] == "exact_span_coded_candidate" for row in self.promoted))

    def test_navigation_is_never_coded_eligible(self):
        self.assertTrue(all(row["eligible_for_limited_qualitative_use"] == "false" and row["navigation_only"] == "true" for row in self.navigation))

    def test_eligibility_flags_match_counts(self):
        pairs = {
            "limited_contract_eligible": "eligible_for_limited_qualitative_use",
            "cycle_analysis_eligible": "eligible_for_cycle_analysis",
            "occupation_comparison_eligible": "eligible_for_occupation_comparison",
            "matched_set_eligible": "eligible_for_exact_period_matched_set",
            "primary_matched_city_cycle_eligible": "eligible_for_primary_matched_city_cycle_design",
            "typed_mechanism_eligible": "eligible_for_typed_mechanism_analysis",
        }
        for key, field in pairs.items():
            self.assertEqual(sum(row[field] == "true" for row in self.promoted), runner.EXPECTED_SCOPE_COUNTS[key])

    def test_quarantine_ids_equal_restricted_ids(self):
        restricted = {row["qualitative_observation_id"] for row in self.promoted if row["eligible_for_limited_qualitative_use"] == "false"}
        self.assertEqual(restricted, {row["qualitative_observation_id"] for row in self.quarantine})

    def test_span_hashes_remain_valid(self):
        self.assertTrue(all(hashlib.sha256(row["literal_verbatim_evidence_span"].encode()).hexdigest() == row["span_sha256"] for row in self.promoted))

    def test_no_forbidden_payload_fields(self):
        self.assertFalse(set(self.promoted_fields) & runner.FORBIDDEN_FIELDS)
        self.assertFalse(set(self.nav_fields) & runner.FORBIDDEN_FIELDS)

    def test_carried_quantitative_manifest_is_separate(self):
        data = runner.read_json(OUTPUT / "quantitative_candidates_carried_forward_manifest.json")
        self.assertEqual((data["candidate_rows"], data["exception_rows"]), (862, 1045))
        self.assertTrue(data["separate_from_qualitative_promotion"])

    def test_non_base_reference_conflict_manifest_is_separate(self):
        data = runner.read_json(OUTPUT / "non_base_reference_conflict_carried_forward_manifest.json")
        self.assertEqual((data["non_base_companion_rows"], data["reference_control_rows"], data["unresolved_conflict_groups"], data["unresolved_conflict_observations"]), (4733, 345, 2, 5))
        self.assertTrue(data["non_base_companion_only"] and data["reference_control_only"] and data["conflicts_quarantined"])

    def test_invariants_pass(self):
        self.assertTrue(self.invariants["all_invariants_passed"])
        self.assertTrue(self.audit["all_invariants_passed"])

    def test_manifest_records_no_forbidden_actions(self):
        self.assertEqual(self.manifest["forbidden_actions_performed"], [])
        self.assertEqual((self.manifest["pdf_pages_accessed"], self.manifest["ocr_later_accessed"]), (0, 0))

    def test_failure_mode_matrix_has_30_adversarial_modes(self):
        _, rows = runner.read_csv(OUTPUT / "limited_exact_span_qualitative_promotion_failure_mode_matrix.csv")
        self.assertEqual(len(rows), 30)

    def test_dashboard_phase_and_readiness_are_fail_closed(self):
        calibration = runner.read_json(ROOT / "docs/dashboard/data/text_table_calibration_status_summary.json")
        readiness = runner.read_json(ROOT / "docs/dashboard/data/analysis_readiness.json")
        self.assertIn(
            calibration["calibration_phase"],
            {
                "compensation_extraction_limited_exact_span_qualitative_promotion_completed_usage_review_allowed",
                "compensation_extraction_limited_exact_span_qualitative_usage_review_completed_usage_layer_prompt_allowed",
                "compensation_extraction_limited_qualitative_usage_layer_materialized_qa_review_allowed",
                "compensation_extraction_limited_qualitative_usage_layer_qa_review_pass_acceptance_prompt_allowed",
                "compensation_extraction_limited_qualitative_usage_layer_acceptance_registered_registry_review_prompt_allowed",
            },
        )
        self.assertFalse(calibration["limited_exact_span_qualitative_global_analysis_readiness"])
        self.assertIn("global_analysis_closed", readiness["overall_status"])
        self.assertFalse(readiness["stage_availability"]["wage_extraction_stage"]["analysis_facing_promotion_allowed"])

    def test_manifest_output_hashes_match(self):
        for name, expected in self.manifest["output_sha256"].items():
            self.assertEqual(runner.sha256(OUTPUT / name), expected)

    def test_future_prompt_contract_passes(self):
        runner.validate_future_prompt((OUTPUT / "next_limited_qualitative_usage_review_prompt.md").read_text())

    def test_resume_is_idempotent(self):
        before = {name: runner.sha256(OUTPUT / name) for name in runner.REQUIRED_OUTPUTS}
        result = subprocess.run([sys.executable, str(Path(runner.__file__)), "--resume"], cwd=ROOT, capture_output=True, text=True, check=True)
        after = {name: runner.sha256(OUTPUT / name) for name in runner.REQUIRED_OUTPUTS}
        self.assertEqual(before, after)
        self.assertEqual(json.loads(result.stdout)["writes"], 0)

    def test_partial_output_cannot_masquerade_as_complete(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "docs/analysis") as tmp:
            out = Path(tmp) / "partial"; out.mkdir()
            (out / "limited_exact_span_qualitative_promotion_decision.json").write_text("{}\n")
            with self.assertRaisesRegex(RuntimeError, "missing"):
                runner.validate_complete_output(out, "wrong")


if __name__ == "__main__":
    unittest.main(verbosity=2)
