#!/usr/bin/env python3
"""Adversarial tests for the limited qualitative usage-layer materialization."""

from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import run_compensation_evidence_limited_qualitative_usage_layer as runner


OUTPUT = runner.DEFAULT_OUTPUT_DIR


class UsageLayerGuardrailTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.material = runner.validate_material_inputs()
        cls.sample = cls.material["authorized"][0]

    def test_output_guard_rejects_tmp(self):
        with self.assertRaisesRegex(RuntimeError, "docs/analysis"):
            runner.output_guard(ROOT / "tmp/usage-layer")

    def test_future_prompt_requires_boundaries(self):
        with self.assertRaisesRegex(RuntimeError, "missing constraints"):
            runner.validate_future_prompt("QA review only")

    def test_future_prompt_is_case_insensitive(self):
        runner.validate_future_prompt("\n".join(x.upper() for x in runner.FUTURE_PROMPT_REQUIRED))

    def test_relay_missing_metadata_fails(self):
        with self.assertRaisesRegex(RuntimeError, "incomplete"):
            runner.validate_relay_metadata({"commit_hash": "abc"})

    def test_relay_complete_metadata_passes(self):
        runner.validate_relay_metadata({key: "recorded" for key in runner.RELAY_REQUIRED})

    def test_dashboard_true_readiness_fails(self):
        with self.assertRaisesRegex(RuntimeError, "readiness true"):
            runner.validate_dashboard_state({"analysis_readiness": True, "usage_layer_qa_review_allowed_next": True})

    def test_dashboard_false_readiness_passes(self):
        runner.validate_dashboard_state({"analysis_readiness": False, "usage_layer_qa_review_allowed_next": True})

    def test_partial_checkpoint_fails(self):
        with self.assertRaisesRegex(RuntimeError, "Partial"):
            runner.validate_checkpoint({"status": "partial", "processed": 642, "expected": 643})

    def test_complete_checkpoint_passes(self):
        runner.validate_checkpoint({"status": "complete", "processed": 643, "expected": 643})

    def test_forbidden_effect_field_fails(self):
        with self.assertRaisesRegex(RuntimeError, "Forbidden"):
            runner.validate_no_forbidden_fields(["qualitative_observation_id", "effect_size"])

    def test_full_page_text_field_fails(self):
        with self.assertRaisesRegex(RuntimeError, "Forbidden"):
            runner.validate_no_forbidden_fields(["full_page_text"])

    def test_restricted_row_fails(self):
        row = copy.deepcopy(self.sample); row["eligible_for_limited_qualitative_use"] = "false"
        with self.assertRaisesRegex(RuntimeError, "Restricted"):
            runner.validate_source_row(row)

    def test_ambiguous_row_fails(self):
        row = copy.deepcopy(self.sample); row["evidence_contract_tier"] = "ambiguous_exact_span_navigation"
        with self.assertRaisesRegex(RuntimeError, "Ambiguous or unavailable"):
            runner.validate_source_row(row)

    def test_unavailable_row_fails(self):
        row = copy.deepcopy(self.sample); row["evidence_contract_tier"] = "unavailable_span_navigation"
        with self.assertRaisesRegex(RuntimeError, "Ambiguous or unavailable"):
            runner.validate_source_row(row)

    def test_span_hash_corruption_fails(self):
        row = copy.deepcopy(self.sample); row["span_sha256"] = "0" * 64
        with self.assertRaisesRegex(RuntimeError, "SHA-256"):
            runner.validate_source_row(row)

    def test_span_offset_corruption_fails(self):
        row = copy.deepcopy(self.sample); row["span_end"] = str(int(row["span_end"]) + 1)
        with self.assertRaisesRegex(RuntimeError, "offset"):
            runner.validate_source_row(row)

    def test_blank_page_pointer_fails(self):
        row = copy.deepcopy(self.sample); row["bounded_evidence_pointer"] = ""
        with self.assertRaisesRegex(RuntimeError, "missing"):
            runner.validate_source_row(row)

    def test_missing_provenance_fails(self):
        row = copy.deepcopy(self.sample); row["source_cite_bridge"] = ""
        with self.assertRaisesRegex(RuntimeError, "missing"):
            runner.validate_source_row(row)

    def test_inactive_row_fails(self):
        row = copy.deepcopy(self.sample); row["current_active"] = "false"
        with self.assertRaisesRegex(RuntimeError, "Inactive"):
            runner.validate_source_row(row)

    def test_historical_mixed_row_fails(self):
        row = copy.deepcopy(self.sample); row["mixed_membership_status"] = "historical_inactive"
        with self.assertRaisesRegex(RuntimeError, "Historical"):
            runner.validate_source_row(row)

    def test_usage_flags_never_open_analysis(self):
        fields = runner.usage_fields_for(self.sample)
        self.assertEqual(fields["analysis_status"], "not_analyzed_limited_evidence_layer_only")
        self.assertEqual(fields["causal_claim_status"], "no_causal_claims_authorized")
        self.assertIn("no_wage_gaps", fields["usage_restrictions"])

    def test_non_cycle_row_gets_explicit_restriction(self):
        row = copy.deepcopy(self.sample); row["eligible_for_cycle_analysis"] = "false"
        self.assertIn("not_cycle_aware_eligible", runner.usage_fields_for(row)["usage_restrictions"])

    def test_compact_manifest_contains_no_rows(self):
        record = runner.compact_manifest("scope", {"a"}, "0" * 64, "navigation", ["restricted"])
        self.assertFalse(record["contains_observation_rows"])
        self.assertFalse(record["analysis_results_computed"])

    def test_dry_run_writes_nothing(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "docs/analysis") as tmp:
            out = Path(tmp) / "usage-layer"
            result = subprocess.run(
                [sys.executable, str(Path(runner.__file__)), "--dry-run", "--output-dir", str(out)],
                cwd=ROOT, capture_output=True, text=True, check=True,
            )
            self.assertFalse(out.exists())
            payload = json.loads(result.stdout)
            self.assertEqual(payload["writes"], 0)
            self.assertEqual(payload["usage_layer_rows"], 643)


class ImmutableAndAuthorizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hashes = runner.verify_inputs()
        cls.material = runner.validate_material_inputs()
        cls.rows = runner.derive_usage_rows(cls.material)

    def test_authorized_baseline_is_ancestor(self):
        result = subprocess.run(["git", "merge-base", "--is-ancestor", runner.BASELINE_COMMIT, "HEAD"], cwd=ROOT)
        self.assertEqual(result.returncode, 0)

    def test_all_24_required_inputs_verified(self):
        self.assertEqual(len(self.hashes), 24)

    def test_candidate_count_is_643(self):
        self.assertEqual(len(self.material["authorized_ids"]), 643)

    def test_authorized_id_hash_matches_frozen_value(self):
        self.assertEqual(self.material["authorized_id_hash"], "0365d38babf9d4000295a3326c8cfc77b92f8a7ad1f2f1117d0cb40f1613b91b")

    def test_derived_rows_are_643_unique(self):
        ids = [row["qualitative_observation_id"] for row in self.rows]
        self.assertEqual((len(ids), len(set(ids))), (643, 643))

    def test_derived_id_hash_matches_authorization(self):
        self.assertEqual(runner.id_set_sha256({row["qualitative_observation_id"] for row in self.rows}), self.material["authorized_id_hash"])

    def test_restricted_count_is_116(self):
        self.assertEqual(len(self.material["restricted_ids"]), 116)

    def test_navigation_count_is_1195(self):
        self.assertEqual(len(self.material["navigation_ids"]), 1195)

    def test_no_restricted_contamination(self):
        self.assertFalse(self.material["authorized_ids"] & self.material["restricted_ids"])

    def test_no_navigation_contamination(self):
        self.assertFalse(self.material["authorized_ids"] & self.material["navigation_ids"])

    def test_primary_count_is_56(self):
        self.assertEqual(len(self.material["primary_ids"]), 56)

    def test_cycle_count_is_453(self):
        self.assertEqual(len(self.material["cycle_ids"]), 453)

    def test_occupation_count_is_438(self):
        self.assertEqual(len(self.material["occupation_ids"]), 438)

    def test_matched_count_is_77(self):
        self.assertEqual(len(self.material["matched_ids"]), 77)

    def test_primary_is_authorized_subset(self):
        self.assertTrue(self.material["primary_ids"] <= self.material["authorized_ids"])

    def test_all_rows_preserve_literal_span_and_provenance(self):
        self.assertTrue(all(row["literal_verbatim_evidence_span"] and row["bounded_evidence_pointer"] and row["source_review_id"] for row in self.rows))

    def test_output_schema_has_explicit_usage_fields(self):
        self.assertTrue(set(runner.USAGE_FIELDS) <= set(runner.OUTPUT_FIELDS))

    def test_output_schema_excludes_analysis_fields(self):
        self.assertFalse(set(runner.OUTPUT_FIELDS) & runner.FORBIDDEN_FIELDS)


class MaterializedUsageLayerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.decision = runner.read_json(OUTPUT / "limited_qualitative_usage_layer_decision.json")
        cls.manifest = runner.read_json(OUTPUT / "limited_qualitative_mechanism_usage_layer_manifest.json")
        cls.audit = runner.read_json(OUTPUT / "limited_qualitative_usage_eligibility_audit.json")
        cls.invariants = runner.read_json(OUTPUT / "limited_qualitative_usage_layer_invariant_checks.json")
        cls.fields, cls.rows = runner.read_csv(OUTPUT / "limited_qualitative_mechanism_usage_layer.csv")

    def test_decision_allows_qa_review_only(self):
        self.assertEqual(self.decision["decision"], runner.DECISION)
        self.assertTrue(self.decision["usage_layer_qa_review_allowed_next"])
        self.assertTrue(self.decision["usage_layer_qa_review_requires_separate_authorization"])
        self.assertFalse(self.decision["global_analysis_readiness"])
        self.assertFalse(self.decision["analysis_results_computed"])

    def test_layer_has_643_rows(self):
        self.assertEqual(len(self.rows), 643)

    def test_layer_ids_are_unique(self):
        self.assertEqual(len({row["qualitative_observation_id"] for row in self.rows}), 643)

    def test_materialized_id_hash_matches_manifest(self):
        ids = {row["qualitative_observation_id"] for row in self.rows}
        self.assertEqual(runner.id_set_sha256(ids), self.manifest["authorized_candidate_id_set_sha256"])
        self.assertTrue(self.manifest["id_set_hash_match"])

    def test_output_sha_matches_manifest(self):
        self.assertEqual(runner.sha256(OUTPUT / "limited_qualitative_mechanism_usage_layer.csv"), self.manifest["output_sha256"])

    def test_schema_sha_matches_manifest(self):
        self.assertEqual(runner.schema_sha256(tuple(self.fields)), self.manifest["schema_sha256"])

    def test_all_rows_exact_and_active(self):
        self.assertTrue(all(row["evidence_contract_tier"] == "exact_span_coded_candidate" and row["current_active"] == "true" for row in self.rows))

    def test_all_rows_are_usage_eligible(self):
        self.assertTrue(all(row["eligible_for_limited_qualitative_mechanism_use"] == "true" for row in self.rows))

    def test_no_analysis_or_causal_status(self):
        self.assertTrue(all(row["analysis_status"] == "not_analyzed_limited_evidence_layer_only" for row in self.rows))
        self.assertTrue(all(row["causal_claim_status"] == "no_causal_claims_authorized" for row in self.rows))

    def test_span_hashes_remain_valid(self):
        self.assertTrue(all(hashlib.sha256(row["literal_verbatim_evidence_span"].encode()).hexdigest() == row["span_sha256"] for row in self.rows))

    def test_strict_primary_manifest_count(self):
        data = runner.read_json(OUTPUT / "strict_primary_matched_city_cycle_usage_manifest.json")
        self.assertEqual(data["row_count"], 56)
        self.assertFalse(data["analysis_results_computed"])

    def test_restricted_manifest_count(self):
        self.assertEqual(runner.read_json(OUTPUT / "restricted_exact_span_usage_quarantine_manifest.json")["row_count"], 116)

    def test_navigation_manifest_counts(self):
        data = runner.read_json(OUTPUT / "navigation_only_qualitative_usage_manifest.json")
        self.assertEqual((data["row_count"], data["ambiguous_rows"], data["unavailable_rows"]), (1195, 614, 581))

    def test_carried_manifest_counts(self):
        names = {
            "quantitative_candidates_carried_forward_manifest.json": 862,
            "quantitative_exceptions_carried_forward_manifest.json": 1045,
            "non_base_companion_carried_forward_manifest.json": 4733,
            "reference_control_carried_forward_manifest.json": 345,
            "unresolved_conflict_quarantine_carried_forward_manifest.json": 5,
        }
        for name, count in names.items():
            self.assertEqual(runner.read_json(OUTPUT / name)["row_count"], count)

    def test_conflict_manifest_preserves_two_groups(self):
        self.assertEqual(runner.read_json(OUTPUT / "unresolved_conflict_quarantine_carried_forward_manifest.json")["group_count"], 2)

    def test_audit_has_zero_contamination(self):
        self.assertEqual((self.audit["restricted_contamination_count"], self.audit["navigation_contamination_count"]), (0, 0))

    def test_invariants_pass(self):
        self.assertTrue(self.invariants["all_invariants_passed"])
        self.assertTrue(all(self.invariants["checks"].values()))

    def test_no_forbidden_payload_fields(self):
        self.assertFalse(set(self.fields) & runner.FORBIDDEN_FIELDS)

    def test_no_pdf_network_or_model_calls(self):
        self.assertEqual((self.decision["pdf_pages_accessed"], self.decision["ocr_later_accessed"], self.decision["network_calls"], self.decision["model_calls"]), (0, 0, 0, 0))
        self.assertEqual(self.decision["forbidden_actions_performed"], [])

    def test_future_prompt_contract_passes(self):
        prompt = (OUTPUT / "next_limited_qualitative_usage_layer_qa_review_prompt.md").read_text()
        runner.validate_future_prompt(prompt)
        self.assertIn("Do not inspect remotes", prompt)
        self.assertIn("Do not configure remotes", prompt)

    def test_failure_inventory_has_35_modes(self):
        self.assertEqual(runner.read_json(OUTPUT / "limited_qualitative_usage_layer_regression_test_inventory.json")["failure_modes"], 35)

    def test_dashboard_phase_and_readiness_are_fail_closed(self):
        calibration = runner.read_json(ROOT / "docs/dashboard/data/text_table_calibration_status_summary.json")
        readiness = runner.read_json(ROOT / "docs/dashboard/data/analysis_readiness.json")
        self.assertIn(calibration["calibration_phase"], {
            "compensation_extraction_limited_qualitative_usage_layer_materialized_qa_review_allowed",
            "compensation_extraction_limited_qualitative_usage_layer_qa_review_pass_acceptance_prompt_allowed",
        })
        self.assertFalse(calibration["limited_qualitative_usage_layer_global_analysis_readiness"])
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
            out = Path(tmp) / "partial"; out.mkdir()
            (out / "limited_qualitative_usage_layer_decision.json").write_text("{}\n")
            with self.assertRaisesRegex(RuntimeError, "missing"):
                runner.validate_complete_output(out, "wrong")


if __name__ == "__main__":
    unittest.main(verbosity=2)
