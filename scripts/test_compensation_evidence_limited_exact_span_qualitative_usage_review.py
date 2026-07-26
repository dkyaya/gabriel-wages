#!/usr/bin/env python3
"""Adversarial tests for the limited exact-span qualitative usage review."""

from __future__ import annotations

import copy
import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import run_compensation_evidence_limited_exact_span_qualitative_usage_review as runner


OUTPUT = runner.DEFAULT_OUTPUT_DIR


class UsageReviewGuardrailTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.material = runner.validate_material_inputs()

    def test_output_guard_rejects_tmp(self):
        with self.assertRaisesRegex(RuntimeError, "docs/analysis"):
            runner.output_guard(ROOT / "tmp/usage-review")

    def test_future_prompt_requires_boundaries(self):
        with self.assertRaisesRegex(RuntimeError, "missing constraints"):
            runner.validate_future_prompt("limited qualitative usage layer only")

    def test_future_prompt_is_case_insensitive(self):
        runner.validate_future_prompt("\n".join(x.upper() for x in runner.FUTURE_PROMPT_REQUIRED))

    def test_relay_missing_metadata_fails(self):
        with self.assertRaisesRegex(RuntimeError, "incomplete"):
            runner.validate_relay_metadata({"commit_hash": "abc"})

    def test_relay_complete_metadata_passes(self):
        runner.validate_relay_metadata({key: "recorded" for key in runner.RELAY_REQUIRED})

    def test_dashboard_true_readiness_fails(self):
        with self.assertRaisesRegex(RuntimeError, "readiness true"):
            runner.validate_dashboard_state({"analysis_readiness": True, "limited_usage_layer_prompt_allowed_next": True})

    def test_dashboard_false_readiness_passes(self):
        runner.validate_dashboard_state({"analysis_readiness": False, "limited_usage_layer_prompt_allowed_next": True})

    def test_partial_checkpoint_fails(self):
        with self.assertRaisesRegex(RuntimeError, "Partial"):
            runner.validate_checkpoint({"status": "partial", "processed": 758, "expected": 759})

    def test_complete_checkpoint_passes(self):
        runner.validate_checkpoint({"status": "complete", "processed": 759, "expected": 759})

    def test_forbidden_analysis_field_fails(self):
        with self.assertRaisesRegex(RuntimeError, "Forbidden"):
            runner.validate_no_forbidden_fields(["qualitative_observation_id", "wage_gap"])

    def test_full_page_text_field_fails(self):
        with self.assertRaisesRegex(RuntimeError, "Forbidden"):
            runner.validate_no_forbidden_fields(["full_page_text"])

    def test_id_set_hash_is_order_invariant(self):
        self.assertEqual(runner.id_set_sha256({"b", "a"}), runner.id_set_sha256({"a", "b"}))

    def test_manifest_contains_no_observation_rows(self):
        record = runner.manifest_for("scope", {"a", "b"}, allowed_use="navigation", restrictions=["none"], source_hash="0" * 64)
        self.assertFalse(record["contains_observation_rows"])
        self.assertFalse(record["analysis_results_computed"])
        self.assertEqual(record["row_count"], 2)

    def test_dry_run_writes_nothing(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "docs/analysis") as tmp:
            out = Path(tmp) / "review"
            result = subprocess.run(
                [sys.executable, str(Path(runner.__file__)), "--dry-run", "--output-dir", str(out)],
                cwd=ROOT, capture_output=True, text=True, check=True,
            )
            self.assertFalse(out.exists())
            payload = json.loads(result.stdout)
            self.assertEqual(payload["writes"], 0)
            self.assertFalse(payload["global_analysis_readiness"])


class ImmutableAndScopeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hashes = runner.verify_inputs()
        cls.material = runner.validate_material_inputs()

    def test_authorized_baseline_is_ancestor(self):
        result = subprocess.run(["git", "merge-base", "--is-ancestor", runner.BASELINE_COMMIT, "HEAD"], cwd=ROOT)
        self.assertEqual(result.returncode, 0)

    def test_all_required_inputs_verified(self):
        self.assertEqual(len(self.hashes), len(runner.REQUIRED_INPUTS))

    def test_counts_match_frozen_contract(self):
        self.assertEqual(self.material["scopes"], runner.EXPECTED_COUNTS)

    def test_promoted_count_759(self):
        self.assertEqual(len(self.material["promoted"]), 759)

    def test_limited_count_643(self):
        self.assertEqual(len(self.material["limited_ids"]), 643)

    def test_restricted_count_116(self):
        self.assertEqual(len(self.material["restricted_ids"]), 116)

    def test_navigation_count_1195(self):
        self.assertEqual(len(self.material["navigation"]), 1195)

    def test_strict_primary_count_56(self):
        self.assertEqual(len(self.material["primary_ids"]), 56)

    def test_cycle_count_453(self):
        self.assertEqual(len(self.material["cycle_ids"]), 453)

    def test_occupation_count_438(self):
        self.assertEqual(len(self.material["occupation_ids"]), 438)

    def test_matched_count_77(self):
        self.assertEqual(len(self.material["matched_ids"]), 77)

    def test_typed_equals_limited(self):
        self.assertEqual(self.material["typed_ids"], self.material["limited_ids"])

    def test_restricted_not_candidate(self):
        self.assertFalse(self.material["restricted_ids"] & self.material["limited_ids"])

    def test_navigation_not_candidate(self):
        nav = {row["qualitative_observation_id"] for row in self.material["navigation"]}
        self.assertFalse(nav & self.material["limited_ids"])

    def test_primary_is_limited_subset(self):
        self.assertTrue(self.material["primary_ids"] <= self.material["limited_ids"])

    def test_cycle_is_limited_subset(self):
        self.assertTrue(self.material["cycle_ids"] <= self.material["limited_ids"])

    def test_occupation_is_limited_subset(self):
        self.assertTrue(self.material["occupation_ids"] <= self.material["limited_ids"])

    def test_matched_is_limited_subset(self):
        self.assertTrue(self.material["matched_ids"] <= self.material["limited_ids"])

    def test_ambiguous_unavailable_never_eligible(self):
        self.assertTrue(all(row["eligible_for_limited_qualitative_use"] == "false" for row in self.material["navigation"]))

    def test_historical_mixed_never_candidate(self):
        self.assertFalse(any(
            row["qualitative_observation_id"] in self.material["limited_ids"]
            and row.get("mixed_membership_status", "").startswith("historical")
            for row in self.material["promoted"]
        ))

    def test_other_never_typed(self):
        self.assertFalse(any(
            row.get("mechanism_type") == "other"
            and row["qualitative_observation_id"] in self.material["typed_ids"]
            for row in self.material["promoted"]
        ))


class MaterializedUsageReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.decision = runner.read_json(OUTPUT / "limited_exact_span_qualitative_usage_review_decision.json")
        cls.audit = runner.read_json(OUTPUT / "limited_exact_span_qualitative_usage_eligibility_audit.json")
        cls.invariants = runner.read_json(OUTPUT / "limited_exact_span_qualitative_usage_review_invariant_checks.json")

    def test_decision_allows_prompt_only(self):
        self.assertEqual(self.decision["decision"], runner.DECISION)
        self.assertTrue(self.decision["limited_usage_layer_prompt_allowed_next"])
        self.assertTrue(self.decision["limited_usage_layer_requires_separate_authorization"])
        self.assertFalse(self.decision["global_analysis_readiness"])
        self.assertFalse(self.decision["global_analysis_facing_promotion"])
        self.assertFalse(self.decision["analysis_results_computed"])

    def test_decision_counts_reconcile(self):
        self.assertEqual(self.decision["scope_counts"], runner.EXPECTED_COUNTS)

    def test_candidate_manifest_is_643(self):
        data = runner.read_json(OUTPUT / "limited_qualitative_mechanism_usage_candidate_manifest.json")
        self.assertEqual(data["row_count"], 643)
        self.assertFalse(data["contains_observation_rows"])

    def test_primary_manifest_is_56(self):
        data = runner.read_json(OUTPUT / "strict_primary_matched_city_cycle_usage_candidate_manifest.json")
        self.assertEqual(data["row_count"], 56)

    def test_restricted_manifest_is_116(self):
        data = runner.read_json(OUTPUT / "restricted_exact_span_usage_quarantine_manifest.json")
        self.assertEqual(data["row_count"], 116)

    def test_navigation_manifest_is_1195(self):
        data = runner.read_json(OUTPUT / "navigation_only_qualitative_usage_manifest.json")
        self.assertEqual((data["row_count"], data["ambiguous_rows"], data["unavailable_rows"]), (1195, 614, 581))

    def test_manifests_do_not_claim_analysis_results(self):
        for name in runner.USAGE_MANIFESTS:
            data = runner.read_json(OUTPUT / name)
            self.assertFalse(data["analysis_results_computed"])
            self.assertFalse(data["global_analysis_readiness"])

    def test_audit_has_zero_contamination(self):
        self.assertEqual(self.audit["candidate_restricted_overlap"], 0)
        self.assertEqual(self.audit["candidate_navigation_overlap"], 0)
        self.assertEqual(self.audit["restricted_navigation_overlap"], 0)

    def test_invariants_pass(self):
        self.assertTrue(self.invariants["all_invariants_passed"])
        self.assertTrue(all(self.invariants["checks"].values()))

    def test_no_pdf_network_model_calls(self):
        self.assertEqual((self.decision["pdf_pages_accessed"], self.decision["ocr_later_accessed"], self.decision["network_calls"], self.decision["model_calls"]), (0, 0, 0, 0))
        self.assertEqual(self.decision["forbidden_actions_performed"], [])

    def test_scope_matrix_contains_no_analysis_results(self):
        fields, rows = runner.read_csv(OUTPUT / "limited_exact_span_qualitative_usage_scope_matrix.csv")
        self.assertNotIn("wage_gap", fields)
        self.assertNotIn("treatment_effect", fields)
        self.assertEqual(len(rows), 8)

    def test_future_prompt_contract_passes(self):
        runner.validate_future_prompt((OUTPUT / "next_limited_qualitative_usage_layer_prompt.md").read_text())

    def test_stress_inventory_has_28_modes(self):
        data = runner.read_json(OUTPUT / "limited_exact_span_qualitative_usage_review_regression_test_inventory.json")
        self.assertEqual(data["new_failure_modes"], 28)

    def test_dashboard_phase_and_readiness_are_fail_closed(self):
        calibration = runner.read_json(ROOT / "docs/dashboard/data/text_table_calibration_status_summary.json")
        readiness = runner.read_json(ROOT / "docs/dashboard/data/analysis_readiness.json")
        self.assertIn(
            calibration["calibration_phase"],
            {
                "compensation_extraction_limited_exact_span_qualitative_usage_review_completed_usage_layer_prompt_allowed",
                "compensation_extraction_limited_qualitative_usage_layer_materialized_qa_review_allowed",
            },
        )
        self.assertFalse(calibration["limited_exact_span_qualitative_usage_review_global_analysis_readiness"])
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
            (out / "limited_exact_span_qualitative_usage_review_decision.json").write_text("{}\n")
            with self.assertRaisesRegex(RuntimeError, "missing"):
                runner.validate_complete_output(out, "wrong")


if __name__ == "__main__":
    unittest.main(verbosity=2)
