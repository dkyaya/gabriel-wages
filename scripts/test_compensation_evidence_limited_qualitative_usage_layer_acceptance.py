#!/usr/bin/env python3
"""Adversarial tests for limited qualitative usage-layer acceptance."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import run_compensation_evidence_limited_qualitative_usage_layer_acceptance as runner


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = runner.DEFAULT_OUTPUT_DIR


class AcceptancePreflightTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hashes, cls.source = runner.verify_inputs()
        cls.material = cls.source["material"]

    def test_all_32_acceptance_inputs_verified(self):
        self.assertEqual(len(self.hashes), 32)

    def test_authorized_commit_is_ancestor(self):
        result = subprocess.run(
            ["git", "merge-base", "--is-ancestor", runner.BASELINE_COMMIT, "HEAD"], cwd=ROOT,
        )
        self.assertEqual(result.returncode, 0)

    def test_qa_decision_authorizes_acceptance(self):
        runner.validate_qa_authorization(self.source["qa_decision"])

    def test_candidate_id_hash_is_authorized(self):
        self.assertEqual(self.material["id_hash"], runner.AUTHORIZED_ID_HASH)

    def test_usage_layer_has_643_rows(self):
        self.assertEqual(len(self.material["rows"]), 643)

    def test_usage_layer_has_643_unique_ids(self):
        self.assertEqual(len(self.material["ids"]), 643)

    def test_layer_hash_matches_qa_audit(self):
        audit = self.source["hash_audit"]
        self.assertEqual(runner.sha256(runner.LAYER_FILE), audit["recorded_layer_sha256"])

    def test_schema_hash_matches_qa_audit(self):
        audit = self.source["hash_audit"]
        self.assertEqual(runner.qa.schema_sha256(self.material["fields"]), audit["recorded_schema_sha256"])

    def test_contamination_audit_passes(self):
        self.assertTrue(self.source["contamination"]["all_contamination_checks_passed"])

    def test_restricted_contamination_is_zero(self):
        self.assertEqual(self.source["contamination"]["restricted_exact_span_contamination_count"], 0)

    def test_navigation_contamination_is_zero(self):
        self.assertEqual(self.source["contamination"]["ambiguous_or_unavailable_contamination_count"], 0)

    def test_external_contamination_is_zero(self):
        audit = self.source["contamination"]
        keys = ("quantitative_contamination_count", "non_base_contamination_count",
                "reference_control_contamination_count", "unresolved_conflict_contamination_count")
        self.assertTrue(all(audit[key] == 0 for key in keys))

    def test_strict_primary_is_56(self):
        self.assertEqual(self.source["restrictions"]["strict_primary_manifest_rows"], 56)

    def test_strict_primary_is_non_analytic(self):
        self.assertFalse(self.source["restrictions"]["analysis_results_computed"])

    def test_carried_counts_are_stable(self):
        carried = self.source["contamination"]
        self.assertEqual(carried["quantitative_manifest_rows"], 862)
        self.assertEqual(carried["quantitative_exception_manifest_rows"], 1045)
        self.assertEqual(carried["non_base_manifest_rows"], 4733)
        self.assertEqual(carried["reference_control_manifest_rows"], 345)
        self.assertEqual(carried["unresolved_conflict_manifest_rows"], 5)

    def test_dry_run_writes_nothing(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "docs/analysis") as tmp:
            out = Path(tmp) / "acceptance"
            result = subprocess.run(
                [sys.executable, str(Path(runner.__file__)), "--dry-run", "--output-dir", str(out)],
                cwd=ROOT, capture_output=True, text=True, check=True,
            )
            payload = json.loads(result.stdout)
            self.assertEqual(payload["writes"], 0)
            self.assertEqual(payload["evidence_rows_created"], 0)
            self.assertEqual(payload["analysis_outputs_created"], 0)
            self.assertFalse(out.exists())


class AcceptanceGuardrailTests(unittest.TestCase):
    def good_decision(self):
        return {
            "decision": runner.qa.DECISION,
            "acceptance_registration_prompt_allowed_next": True,
            "analysis_results_computed": False,
            "global_analysis_readiness": False,
        }

    def good_hash(self):
        return {
            "observed_candidate_id_set_sha256": runner.AUTHORIZED_ID_HASH,
            "candidate_id_set_hash_match": True,
            "layer_sha256_match": True,
            "schema_sha256_match": True,
        }

    def good_scope(self):
        return {
            "observed_counts": copy.deepcopy(runner.EXPECTED),
            "restricted_navigation_external_contamination_count": 0,
            "evidence_rows_created": 0,
            "analysis_outputs_created": 0,
        }

    def good_registration(self):
        return {
            "record_type": "acceptance_registration_only",
            "accepted_usage_layer_rows": 643,
            "candidate_id_set_sha256": runner.AUTHORIZED_ID_HASH,
            "evidence_rows_created": 0,
            "analysis_outputs_created": 0,
            "global_analysis_readiness": False,
            "full_qualitative_readiness": False,
        }

    def changed(self, record, key, value):
        altered = copy.deepcopy(record)
        altered[key] = value
        return altered

    def test_good_qa_authorization_passes(self):
        runner.validate_qa_authorization(self.good_decision())

    def test_wrong_qa_decision_fails(self):
        with self.assertRaisesRegex(RuntimeError, "does not authorize"):
            runner.validate_qa_authorization(self.changed(self.good_decision(), "decision", "hold"))

    def test_qa_prompt_not_allowed_fails(self):
        with self.assertRaisesRegex(RuntimeError, "did not allow"):
            runner.validate_qa_authorization(self.changed(self.good_decision(), "acceptance_registration_prompt_allowed_next", False))

    def test_qa_analysis_result_fails(self):
        with self.assertRaisesRegex(RuntimeError, "analysis"):
            runner.validate_qa_authorization(self.changed(self.good_decision(), "analysis_results_computed", True))

    def test_qa_global_readiness_fails(self):
        with self.assertRaisesRegex(RuntimeError, "readiness"):
            runner.validate_qa_authorization(self.changed(self.good_decision(), "global_analysis_readiness", True))

    def test_good_hash_contract_passes(self):
        runner.validate_hash_contract(self.good_hash())

    def test_candidate_hash_drift_fails(self):
        with self.assertRaisesRegex(RuntimeError, "ID-set hash"):
            runner.validate_hash_contract(self.changed(self.good_hash(), "observed_candidate_id_set_sha256", "0" * 64))

    def test_layer_hash_failure_fails(self):
        with self.assertRaisesRegex(RuntimeError, "Layer SHA"):
            runner.validate_hash_contract(self.changed(self.good_hash(), "layer_sha256_match", False))

    def test_schema_hash_failure_fails(self):
        with self.assertRaisesRegex(RuntimeError, "Schema SHA"):
            runner.validate_hash_contract(self.changed(self.good_hash(), "schema_sha256_match", False))

    def test_good_scope_passes(self):
        runner.validate_scope_contract(self.good_scope())

    def test_scope_count_drift_fails(self):
        bad = self.good_scope()
        bad["observed_counts"]["accepted_usage_layer_rows"] = 642
        with self.assertRaisesRegex(RuntimeError, "scope counts"):
            runner.validate_scope_contract(bad)

    def test_scope_contamination_fails(self):
        with self.assertRaisesRegex(RuntimeError, "contamination"):
            runner.validate_scope_contract(self.changed(self.good_scope(), "restricted_navigation_external_contamination_count", 1))

    def test_evidence_rows_created_fails(self):
        with self.assertRaisesRegex(RuntimeError, "evidence rows"):
            runner.validate_scope_contract(self.changed(self.good_scope(), "evidence_rows_created", 1))

    def test_analysis_output_created_fails(self):
        with self.assertRaisesRegex(RuntimeError, "analysis outputs"):
            runner.validate_scope_contract(self.changed(self.good_scope(), "analysis_outputs_created", 1))

    def test_good_registration_record_passes(self):
        runner.validate_registration_record(self.good_registration())

    def test_non_registration_record_fails(self):
        with self.assertRaisesRegex(RuntimeError, "registration-only"):
            runner.validate_registration_record(self.changed(self.good_registration(), "record_type", "evidence_output"))

    def test_registration_row_count_fails(self):
        with self.assertRaisesRegex(RuntimeError, "row count"):
            runner.validate_registration_record(self.changed(self.good_registration(), "accepted_usage_layer_rows", 642))

    def test_registration_hash_fails(self):
        with self.assertRaisesRegex(RuntimeError, "hash"):
            runner.validate_registration_record(self.changed(self.good_registration(), "candidate_id_set_sha256", "bad"))

    def test_registration_evidence_rows_fails(self):
        with self.assertRaisesRegex(RuntimeError, "evidence"):
            runner.validate_registration_record(self.changed(self.good_registration(), "evidence_rows_created", 1))

    def test_registration_analysis_output_fails(self):
        with self.assertRaisesRegex(RuntimeError, "analysis"):
            runner.validate_registration_record(self.changed(self.good_registration(), "analysis_outputs_created", 1))

    def test_registration_global_readiness_fails(self):
        with self.assertRaisesRegex(RuntimeError, "readiness"):
            runner.validate_registration_record(self.changed(self.good_registration(), "global_analysis_readiness", True))

    def test_dashboard_global_readiness_fails(self):
        with self.assertRaisesRegex(RuntimeError, "readiness"):
            runner.validate_dashboard_state({"global_analysis_readiness": True, "analysis_facing_promotion_allowed": False})

    def test_dashboard_promotion_fails(self):
        with self.assertRaisesRegex(RuntimeError, "promotion"):
            runner.validate_dashboard_state({"global_analysis_readiness": False, "analysis_facing_promotion_allowed": True})

    def test_dashboard_closed_passes(self):
        runner.validate_dashboard_state({"global_analysis_readiness": False, "analysis_facing_promotion_allowed": False})

    def test_future_prompt_missing_constraints_fails(self):
        with self.assertRaisesRegex(RuntimeError, "missing"):
            runner.validate_future_prompt("registry review only")

    def test_future_prompt_case_insensitive_passes(self):
        runner.validate_future_prompt("\n".join(runner.FUTURE_PROMPT_REQUIRED).upper())

    def test_relay_missing_fields_fails(self):
        with self.assertRaisesRegex(RuntimeError, "missing"):
            runner.validate_relay_metadata({"commit_hash": "x"})

    def test_relay_complete_fields_passes(self):
        runner.validate_relay_metadata({field: "present" for field in runner.RELAY_REQUIRED})

    def test_partial_checkpoint_fails(self):
        with self.assertRaisesRegex(RuntimeError, "Partial"):
            runner.validate_checkpoint({"status": "partial", "processed": 642, "expected": 643})

    def test_complete_checkpoint_passes(self):
        runner.validate_checkpoint({"status": "complete", "processed": 643, "expected": 643})

    def test_output_guard_rejects_tmp(self):
        with self.assertRaisesRegex(RuntimeError, "docs/analysis"):
            runner.output_guard(ROOT / "tmp" / "bad-acceptance-output")


@unittest.skipUnless(OUTPUT.is_dir(), "acceptance output not materialized")
class MaterializedAcceptanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hashes, _ = runner.verify_inputs()
        cls.signature = runner.input_signature(cls.hashes)
        cls.decision = runner.read_json(OUTPUT / "limited_qualitative_usage_layer_acceptance_decision.json")
        cls.manifest = runner.read_json(OUTPUT / "limited_qualitative_usage_layer_registration_manifest.json")
        cls.hash_audit = runner.read_json(OUTPUT / "limited_qualitative_usage_layer_acceptance_hash_audit.json")
        cls.scope = runner.read_json(OUTPUT / "limited_qualitative_usage_layer_acceptance_scope_audit.json")
        cls.forbidden = runner.read_json(OUTPUT / "limited_qualitative_usage_layer_acceptance_forbidden_action_audit.json")
        cls.invariants = runner.read_json(OUTPUT / "limited_qualitative_usage_layer_acceptance_invariant_checks.json")

    def test_decision_is_registered(self):
        self.assertEqual(self.decision["decision"], runner.DECISION)

    def test_decision_is_registration_only(self):
        runner.validate_registration_record(self.decision)

    def test_manifest_is_registration_only(self):
        runner.validate_registration_record({"record_type": "acceptance_registration_only", **self.manifest})

    def test_all_hashes_pass(self):
        runner.validate_hash_contract(self.hash_audit)
        self.assertTrue(self.hash_audit["all_hash_checks_passed"])

    def test_scope_passes(self):
        runner.validate_scope_contract(self.scope)
        self.assertTrue(self.scope["all_scope_checks_passed"])

    def test_forbidden_actions_are_zero(self):
        self.assertTrue(self.forbidden["all_forbidden_action_checks_passed"])
        numeric = [value for key, value in self.forbidden.items()
                   if key not in {"task_id", "schema_version", "global_analysis_readiness", "all_forbidden_action_checks_passed"}]
        self.assertTrue(all(value == 0 for value in numeric))

    def test_invariants_pass(self):
        self.assertTrue(self.invariants["all_invariants_passed"])
        self.assertTrue(all(self.invariants["checks"].values()))

    def test_scope_matrix_reconciles(self):
        with (OUTPUT / "limited_qualitative_usage_layer_registered_scope_matrix.csv").open(newline="", encoding="utf-8") as handle:
            rows = list(__import__("csv").DictReader(handle))
        self.assertEqual(len(rows), 11)
        self.assertTrue(all(row["reconciliation_status"] == "pass" for row in rows))

    def test_registry_prompt_contract_passes(self):
        prompt = (OUTPUT / "next_limited_qualitative_usage_registry_review_prompt.md").read_text(encoding="utf-8")
        runner.validate_future_prompt(prompt)

    def test_inventory_has_36_modes(self):
        inventory = runner.read_json(OUTPUT / "limited_qualitative_usage_layer_acceptance_regression_test_inventory.json")
        self.assertEqual(inventory["failure_modes"], 36)

    def test_complete_output_passes(self):
        runner.validate_complete_output(OUTPUT, self.signature)

    def test_dashboard_records_registration_but_not_readiness(self):
        calibration = runner.read_json(ROOT / "docs/dashboard/data/text_table_calibration_status_summary.json")
        readiness = runner.read_json(ROOT / "docs/dashboard/data/analysis_readiness.json")
        self.assertIn(
            calibration["calibration_phase"],
            {
                "compensation_extraction_limited_qualitative_usage_layer_acceptance_registered_registry_review_prompt_allowed",
                "compensation_extraction_limited_qualitative_usage_registry_review_pass_registry_acceptance_prompt_allowed",
                "compensation_extraction_limited_qualitative_usage_registry_acceptance_registered_strategy_prompt_allowed",
                "compensation_extraction_final_qa_categorization_phase_closed_gabriel_attribute_analysis_ready",
                "compensation_extraction_claim_oriented_phase_closed_gabriel_claim_rating_ready",
            },
        )
        self.assertTrue(calibration["limited_qualitative_usage_layer_acceptance_registered"])
        self.assertFalse(calibration["limited_qualitative_usage_layer_acceptance_global_analysis_readiness"])
        self.assertIn("global_analysis_closed", readiness["overall_status"])
        self.assertFalse(readiness["stage_availability"]["wage_extraction_stage"]["analysis_facing_promotion_allowed"])

    def test_resume_is_idempotent(self):
        before = {name: runner.sha256(OUTPUT / name) for name in runner.REQUIRED_OUTPUTS}
        result = subprocess.run(
            [sys.executable, str(Path(runner.__file__)), "--resume"], cwd=ROOT,
            capture_output=True, text=True, check=True,
        )
        after = {name: runner.sha256(OUTPUT / name) for name in runner.REQUIRED_OUTPUTS}
        self.assertEqual(before, after)
        self.assertEqual(json.loads(result.stdout)["writes"], 0)

    def test_partial_output_cannot_masquerade_as_complete(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "docs/analysis") as tmp:
            out = Path(tmp) / "partial"
            out.mkdir()
            (out / "limited_qualitative_usage_layer_acceptance_decision.json").write_text("{}\n")
            with self.assertRaisesRegex(RuntimeError, "missing"):
                runner.validate_complete_output(out, "wrong")


if __name__ == "__main__":
    unittest.main(verbosity=2)
