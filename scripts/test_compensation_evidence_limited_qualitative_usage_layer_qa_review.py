#!/usr/bin/env python3
"""Adversarial tests for the limited qualitative usage-layer QA review."""

from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import run_compensation_evidence_limited_qualitative_usage_layer_qa_review as runner


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = runner.DEFAULT_OUTPUT_DIR


class ReviewPreflightTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hashes = runner.verify_inputs()
        cls.material = runner.build_review_material()

    def test_all_20_review_inputs_verified(self):
        self.assertEqual(len(self.hashes), 20)

    def test_authorized_commit_is_ancestor(self):
        result = subprocess.run(
            ["git", "merge-base", "--is-ancestor", runner.BASELINE_COMMIT, "HEAD"],
            cwd=ROOT,
        )
        self.assertEqual(result.returncode, 0)

    def test_layer_count_is_643(self):
        self.assertEqual(len(self.material["rows"]), 643)

    def test_layer_ids_are_unique(self):
        self.assertEqual(len(self.material["ids"]), 643)

    def test_candidate_id_hash_matches_authorization(self):
        self.assertEqual(self.material["id_hash"], runner.AUTHORIZED_ID_HASH)

    def test_layer_file_hash_matches_manifest(self):
        self.assertEqual(
            runner.sha256(runner.LAYER / "limited_qualitative_mechanism_usage_layer.csv"),
            self.material["manifest"]["output_sha256"],
        )

    def test_schema_hash_matches_manifest(self):
        self.assertEqual(
            runner.schema_sha256(self.material["fields"]),
            self.material["manifest"]["schema_sha256"],
        )

    def test_schema_exactly_matches_approved_fields(self):
        self.assertEqual(self.material["fields"], list(runner.layer.OUTPUT_FIELDS))

    def test_every_row_validates(self):
        for row in self.material["rows"]:
            runner.validate_row(row)

    def test_restricted_contamination_zero(self):
        self.assertEqual(self.material["restricted_overlap"], 0)

    def test_navigation_contamination_zero(self):
        self.assertEqual(self.material["navigation_overlap"], 0)

    def test_primary_count_is_56(self):
        self.assertEqual(len(self.material["primary_ids"]), 56)

    def test_cycle_count_is_453(self):
        self.assertEqual(len(self.material["cycle_ids"]), 453)

    def test_occupation_count_is_438(self):
        self.assertEqual(len(self.material["occupation_ids"]), 438)

    def test_matched_count_is_77(self):
        self.assertEqual(len(self.material["matched_ids"]), 77)

    def test_provenance_coverage_is_complete(self):
        self.assertTrue(all(count == 643 for count in self.material["provenance_counts"].values()))

    def test_carried_counts_are_stable(self):
        self.assertEqual(self.material["carried"]["quantitative_candidates"]["row_count"], 862)
        self.assertEqual(self.material["carried"]["quantitative_exceptions"]["row_count"], 1045)
        self.assertEqual(self.material["carried"]["non_base_companion"]["row_count"], 4733)
        self.assertEqual(self.material["carried"]["reference_control"]["row_count"], 345)
        self.assertEqual(self.material["carried"]["unresolved_conflicts"]["row_count"], 5)

    def test_unresolved_groups_are_two(self):
        self.assertEqual(self.material["carried"]["unresolved_conflicts"]["group_count"], 2)

    def test_dry_run_writes_nothing(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "docs/analysis") as tmp:
            out = Path(tmp) / "review"
            result = subprocess.run(
                [sys.executable, str(Path(runner.__file__)), "--dry-run", "--output-dir", str(out)],
                cwd=ROOT, capture_output=True, text=True, check=True,
            )
            payload = json.loads(result.stdout)
            self.assertEqual(payload["writes"], 0)
            self.assertFalse(out.exists())


class ReviewGuardrailTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _, rows = runner.read_csv(runner.LAYER / "limited_qualitative_mechanism_usage_layer.csv")
        cls.good = rows[0]

    def changed(self, field, value):
        row = copy.deepcopy(self.good)
        row[field] = value
        return row

    def test_good_row_passes(self):
        runner.validate_row(self.good)

    def test_missing_literal_span_fails(self):
        with self.assertRaisesRegex(RuntimeError, "missing"):
            runner.validate_row(self.changed("literal_verbatim_evidence_span", ""))

    def test_span_hash_corruption_fails(self):
        with self.assertRaisesRegex(RuntimeError, "SHA-256"):
            runner.validate_row(self.changed("span_sha256", "0" * 64))

    def test_span_offset_corruption_fails(self):
        with self.assertRaisesRegex(RuntimeError, "offsets"):
            runner.validate_row(self.changed("span_end", str(int(self.good["span_end"]) + 1)))

    def test_multiline_span_fails(self):
        row = self.changed("literal_verbatim_evidence_span", self.good["literal_verbatim_evidence_span"] + "\nextra")
        row["span_length"] = str(len(row["literal_verbatim_evidence_span"]))
        row["span_end"] = str(int(row["span_start"]) + len(row["literal_verbatim_evidence_span"]))
        row["span_sha256"] = hashlib.sha256(row["literal_verbatim_evidence_span"].encode()).hexdigest()
        with self.assertRaisesRegex(RuntimeError, "single-line"):
            runner.validate_row(row)

    def test_blank_page_pointer_fails(self):
        with self.assertRaisesRegex(RuntimeError, "missing"):
            runner.validate_row(self.changed("bounded_evidence_pointer", ""))

    def test_zero_page_number_fails(self):
        with self.assertRaisesRegex(RuntimeError, "page pointer"):
            runner.validate_row(self.changed("page_number", "0"))

    def test_missing_case_id_fails(self):
        with self.assertRaisesRegex(RuntimeError, "missing"):
            runner.validate_row(self.changed("extraction_case_id", ""))

    def test_missing_source_review_id_fails(self):
        with self.assertRaisesRegex(RuntimeError, "missing"):
            runner.validate_row(self.changed("source_review_id", ""))

    def test_missing_historical_qa_fails(self):
        with self.assertRaisesRegex(RuntimeError, "missing"):
            runner.validate_row(self.changed("qa_status", ""))

    def test_inactive_row_fails(self):
        with self.assertRaisesRegex(RuntimeError, "Inactive"):
            runner.validate_row(self.changed("current_active", "false"))

    def test_historical_mixed_membership_fails(self):
        with self.assertRaisesRegex(RuntimeError, "Historical"):
            runner.validate_row(self.changed("mixed_membership_status", "historical_inactive"))

    def test_ambiguous_tier_fails(self):
        with self.assertRaisesRegex(RuntimeError, "Non-exact"):
            runner.validate_row(self.changed("evidence_contract_tier", "ambiguous_exact_span_navigation"))

    def test_non_unique_span_status_fails(self):
        with self.assertRaisesRegex(RuntimeError, "exact unique"):
            runner.validate_row(self.changed("span_qa_status", "span_ambiguous"))

    def test_not_limited_eligible_fails(self):
        with self.assertRaisesRegex(RuntimeError, "limited-use"):
            runner.validate_row(self.changed("eligible_for_limited_qualitative_mechanism_use", "false"))

    def test_analysis_completed_status_fails(self):
        with self.assertRaisesRegex(RuntimeError, "completed analysis"):
            runner.validate_row(self.changed("analysis_status", "analysis_complete"))

    def test_open_causal_status_fails(self):
        with self.assertRaisesRegex(RuntimeError, "causal"):
            runner.validate_row(self.changed("causal_claim_status", "causal_claims_allowed"))

    def test_missing_prohibited_use_fails(self):
        with self.assertRaisesRegex(RuntimeError, "prohibited-use"):
            runner.validate_row(self.changed("prohibited_usage", "statistics|wage_gaps"))

    def test_forbidden_analysis_field_fails(self):
        with self.assertRaisesRegex(RuntimeError, "Forbidden"):
            runner.validate_no_forbidden_fields(["qualitative_observation_id", "regression_result"])

    def test_full_page_text_field_fails(self):
        with self.assertRaisesRegex(RuntimeError, "Forbidden"):
            runner.validate_no_forbidden_fields(["full_page_text"])

    def test_output_guard_rejects_tmp(self):
        with self.assertRaisesRegex(RuntimeError, "docs/analysis"):
            runner.output_guard(ROOT / "tmp" / "bad-output")

    def test_dashboard_true_readiness_fails(self):
        with self.assertRaisesRegex(RuntimeError, "readiness"):
            runner.validate_dashboard_state({"global_analysis_readiness": True, "analysis_facing_promotion_allowed": False})

    def test_dashboard_true_promotion_fails(self):
        with self.assertRaisesRegex(RuntimeError, "promotion"):
            runner.validate_dashboard_state({"global_analysis_readiness": False, "analysis_facing_promotion_allowed": True})

    def test_dashboard_closed_passes(self):
        runner.validate_dashboard_state({"global_analysis_readiness": False, "analysis_facing_promotion_allowed": False})

    def test_future_prompt_requires_constraints(self):
        with self.assertRaisesRegex(RuntimeError, "missing"):
            runner.validate_future_prompt("acceptance/registration only")

    def test_future_prompt_is_case_insensitive(self):
        text = "\n".join(runner.FUTURE_PROMPT_REQUIRED).upper()
        runner.validate_future_prompt(text)

    def test_relay_missing_metadata_fails(self):
        with self.assertRaisesRegex(RuntimeError, "missing"):
            runner.validate_relay_metadata({"commit_hash": "x"})

    def test_relay_complete_metadata_passes(self):
        runner.validate_relay_metadata({field: "present" for field in runner.RELAY_REQUIRED})

    def test_partial_checkpoint_fails(self):
        with self.assertRaisesRegex(RuntimeError, "Partial"):
            runner.validate_checkpoint({"status": "partial", "processed": 642, "expected": 643})

    def test_complete_checkpoint_passes(self):
        runner.validate_checkpoint({"status": "complete", "processed": 643, "expected": 643})


@unittest.skipUnless(OUTPUT.is_dir(), "materialized QA-review output not present")
class MaterializedReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.decision = runner.read_json(OUTPUT / "limited_qualitative_usage_layer_qa_review_decision.json")
        cls.hash_audit = runner.read_json(OUTPUT / "limited_qualitative_usage_layer_hash_audit.json")
        cls.schema_audit = runner.read_json(OUTPUT / "limited_qualitative_usage_layer_schema_audit.json")
        cls.provenance = runner.read_json(OUTPUT / "limited_qualitative_usage_layer_provenance_audit.json")
        cls.restrictions = runner.read_json(OUTPUT / "limited_qualitative_usage_layer_restriction_audit.json")
        cls.contamination = runner.read_json(OUTPUT / "limited_qualitative_usage_layer_contamination_audit.json")
        cls.invariants = runner.read_json(OUTPUT / "limited_qualitative_usage_layer_qa_invariant_checks.json")

    def test_decision_is_acceptance_prompt_only(self):
        self.assertEqual(self.decision["decision"], runner.DECISION)
        self.assertTrue(self.decision["acceptance_registration_prompt_allowed_next"])
        self.assertFalse(self.decision["global_analysis_readiness"])

    def test_reviewed_rows_are_643(self):
        self.assertEqual(self.decision["qa_reviewed_usage_layer_rows"], 643)

    def test_hash_audit_passes(self):
        self.assertTrue(self.hash_audit["all_hash_checks_passed"])
        self.assertEqual(self.hash_audit["observed_candidate_id_set_sha256"], runner.AUTHORIZED_ID_HASH)

    def test_schema_audit_passes(self):
        self.assertTrue(self.schema_audit["all_schema_checks_passed"])
        self.assertEqual(self.schema_audit["duplicate_header_count"], 0)

    def test_provenance_audit_passes_643(self):
        self.assertTrue(self.provenance["all_provenance_checks_passed"])
        self.assertEqual(self.provenance["literal_span_hash_pass_count"], 643)
        self.assertEqual(self.provenance["identity_provenance_complete_count"], 643)

    def test_restrictions_close_analysis_and_causality(self):
        self.assertTrue(self.restrictions["all_restriction_checks_passed"])
        self.assertEqual(self.restrictions["analysis_status_not_analyzed_count"], 643)
        self.assertEqual(self.restrictions["causal_claims_closed_count"], 643)

    def test_contamination_is_zero(self):
        keys = (
            "restricted_exact_span_contamination_count", "ambiguous_or_unavailable_contamination_count",
            "quantitative_contamination_count", "non_base_contamination_count",
            "reference_control_contamination_count", "unresolved_conflict_contamination_count",
        )
        self.assertTrue(all(self.contamination[key] == 0 for key in keys))

    def test_strict_primary_manifest_is_56(self):
        self.assertEqual(self.restrictions["strict_primary_manifest_rows"], 56)

    def test_carried_lane_counts(self):
        self.assertEqual(self.contamination["quantitative_manifest_rows"], 862)
        self.assertEqual(self.contamination["quantitative_exception_manifest_rows"], 1045)
        self.assertEqual(self.contamination["non_base_manifest_rows"], 4733)
        self.assertEqual(self.contamination["reference_control_manifest_rows"], 345)
        self.assertEqual(self.contamination["unresolved_conflict_manifest_rows"], 5)

    def test_invariants_pass(self):
        self.assertTrue(self.invariants["all_invariants_passed"])
        self.assertTrue(all(self.invariants["checks"].values()))

    def test_scope_reconciliation_all_passes(self):
        _, rows = runner.read_csv(OUTPUT / "limited_qualitative_usage_layer_scope_reconciliation.csv")
        self.assertEqual(len(rows), 14)
        self.assertTrue(all(row["reconciliation_status"] == "pass" for row in rows))

    def test_future_prompt_contract_passes(self):
        prompt = (OUTPUT / "next_limited_qualitative_usage_layer_acceptance_prompt.md").read_text()
        runner.validate_future_prompt(prompt)
        self.assertIn("Do not run extraction", prompt)
        self.assertIn("Do not select new documents", prompt)

    def test_failure_inventory_has_40_modes(self):
        inventory = runner.read_json(OUTPUT / "limited_qualitative_usage_layer_qa_regression_test_inventory.json")
        self.assertEqual(inventory["failure_modes"], 40)

    def test_dashboard_phase_is_fail_closed(self):
        calibration = runner.read_json(ROOT / "docs/dashboard/data/text_table_calibration_status_summary.json")
        readiness = runner.read_json(ROOT / "docs/dashboard/data/analysis_readiness.json")
        self.assertIn(calibration["calibration_phase"], {
            "compensation_extraction_limited_qualitative_usage_layer_qa_review_pass_acceptance_prompt_allowed",
            "compensation_extraction_limited_qualitative_usage_layer_acceptance_registered_registry_review_prompt_allowed",
            "compensation_extraction_limited_qualitative_usage_registry_review_pass_registry_acceptance_prompt_allowed",
            "compensation_extraction_limited_qualitative_usage_registry_acceptance_registered_strategy_prompt_allowed",
            "compensation_extraction_final_qa_categorization_phase_closed_gabriel_attribute_analysis_ready",
            "compensation_extraction_claim_oriented_phase_closed_gabriel_claim_rating_ready",
        })
        self.assertFalse(calibration["limited_qualitative_usage_layer_qa_global_analysis_readiness"])
        self.assertIn("global_analysis_closed", readiness["overall_status"])
        self.assertFalse(readiness["stage_availability"]["wage_extraction_stage"]["analysis_facing_promotion_allowed"])

    def test_resume_is_idempotent(self):
        before = {name: runner.sha256(OUTPUT / name) for name in runner.REQUIRED_OUTPUTS}
        result = subprocess.run([sys.executable, str(Path(runner.__file__)), "--resume"], cwd=ROOT, capture_output=True, text=True, check=True)
        after = {name: runner.sha256(OUTPUT / name) for name in runner.REQUIRED_OUTPUTS}
        self.assertEqual(before, after)
        self.assertEqual(json.loads(result.stdout)["writes"], 0)

    def test_partial_output_cannot_masquerade_as_complete(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "docs/analysis") as tmp:
            out = Path(tmp) / "partial"
            out.mkdir()
            (out / "limited_qualitative_usage_layer_qa_review_decision.json").write_text("{}\n")
            with self.assertRaisesRegex(RuntimeError, "missing"):
                runner.validate_complete_output(out, "wrong")


if __name__ == "__main__":
    unittest.main(verbosity=2)
