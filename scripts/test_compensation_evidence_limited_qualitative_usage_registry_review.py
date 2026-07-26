#!/usr/bin/env python3
"""Adversarial tests for the limited qualitative usage registry review."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import run_compensation_evidence_limited_qualitative_usage_registry_review as runner


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = runner.DEFAULT_OUTPUT_DIR


class RegistryReviewPreflightTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hashes, cls.source = runner.verify_inputs()

    def test_14_direct_input_contract_entries(self):
        self.assertEqual(len(self.hashes), 14)

    def test_12_immutable_acceptance_inputs(self):
        self.assertEqual(len(runner.ACCEPTANCE_INPUTS), 12)

    def test_two_dashboard_contract_inputs(self):
        self.assertEqual(len(runner.DASHBOARD_INPUTS), 2)

    def test_authorized_commit_is_ancestor(self):
        result = subprocess.run(
            ["git", "merge-base", "--is-ancestor", runner.BASELINE_COMMIT, "HEAD"], cwd=ROOT,
        )
        self.assertEqual(result.returncode, 0)

    def test_acceptance_decision_authorizes_review(self):
        runner.validate_acceptance_authorization(self.source["decision"])

    def test_acceptance_manifest_registration_only(self):
        self.assertTrue(self.source["manifest"]["registration_only"])
        self.assertFalse(self.source["manifest"]["contains_evidence_rows"])

    def test_candidate_id_hash_authorized(self):
        self.assertEqual(self.source["hash_audit"]["observed_candidate_id_set_sha256"], runner.AUTHORIZED_ID_HASH)

    def test_layer_hash_authorized(self):
        self.assertEqual(self.source["hash_audit"]["observed_layer_sha256"], runner.AUTHORIZED_LAYER_HASH)

    def test_schema_hash_authorized(self):
        self.assertEqual(self.source["hash_audit"]["observed_schema_sha256"], runner.AUTHORIZED_SCHEMA_HASH)

    def test_scope_counts_stable(self):
        self.assertEqual(self.source["scope_audit"]["observed_counts"], runner.EXPECTED)

    def test_contamination_zero(self):
        self.assertEqual(self.source["scope_audit"]["restricted_navigation_external_contamination_count"], 0)

    def test_acceptance_created_no_evidence(self):
        self.assertEqual(self.source["scope_audit"]["evidence_rows_created"], 0)

    def test_acceptance_created_no_analysis(self):
        self.assertEqual(self.source["scope_audit"]["analysis_outputs_created"], 0)

    def test_dashboard_registry_state_is_closed(self):
        runner.validate_dashboard_state(self.source["calibration"], self.source["readiness"])

    def test_source_future_prompt_is_complete(self):
        text = (runner.ACCEPTANCE_DIR / "next_limited_qualitative_usage_registry_review_prompt.md").read_text(encoding="utf-8")
        runner.validate_prompt(text, runner.SOURCE_PROMPT_REQUIRED)

    def test_dry_run_writes_nothing(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "docs/analysis") as tmp:
            out = Path(tmp) / "registry-review"
            result = subprocess.run(
                [sys.executable, str(Path(runner.__file__)), "--dry-run", "--output-dir", str(out)],
                cwd=ROOT, capture_output=True, text=True, check=True,
            )
            payload = json.loads(result.stdout)
            self.assertEqual(payload["writes"], 0)
            self.assertEqual(payload["evidence_rows_created"], 0)
            self.assertEqual(payload["analysis_outputs_created"], 0)
            self.assertFalse(out.exists())


class RegistryReviewGuardrailTests(unittest.TestCase):
    def good_decision(self):
        return {
            "decision": runner.acceptance.DECISION,
            "record_type": "acceptance_registration_only",
            "registry_review_prompt_allowed_next": True,
            "evidence_rows_created": 0, "analysis_outputs_created": 0,
            "global_analysis_readiness": False,
        }

    def good_hash(self):
        return {
            "observed_candidate_id_set_sha256": runner.AUTHORIZED_ID_HASH,
            "observed_layer_sha256": runner.AUTHORIZED_LAYER_HASH,
            "observed_schema_sha256": runner.AUTHORIZED_SCHEMA_HASH,
            "candidate_id_set_hash_match": True, "layer_sha256_match": True,
            "schema_sha256_match": True,
        }

    def good_scope(self):
        return {
            "observed_counts": copy.deepcopy(runner.EXPECTED),
            "restricted_navigation_external_contamination_count": 0,
            "evidence_rows_created": 0, "analysis_outputs_created": 0,
        }

    def changed(self, record, key, value):
        altered = copy.deepcopy(record)
        altered[key] = value
        return altered

    def test_good_authorization_passes(self):
        runner.validate_acceptance_authorization(self.good_decision())

    def test_wrong_acceptance_decision_fails(self):
        with self.assertRaisesRegex(RuntimeError, "does not authorize"):
            runner.validate_acceptance_authorization(self.changed(self.good_decision(), "decision", "hold"))

    def test_non_registration_acceptance_fails(self):
        with self.assertRaisesRegex(RuntimeError, "registration-only"):
            runner.validate_acceptance_authorization(self.changed(self.good_decision(), "record_type", "evidence"))

    def test_prompt_not_allowed_fails(self):
        with self.assertRaisesRegex(RuntimeError, "did not allow"):
            runner.validate_acceptance_authorization(self.changed(self.good_decision(), "registry_review_prompt_allowed_next", False))

    def test_acceptance_evidence_rows_fail(self):
        with self.assertRaisesRegex(RuntimeError, "evidence rows"):
            runner.validate_acceptance_authorization(self.changed(self.good_decision(), "evidence_rows_created", 1))

    def test_acceptance_analysis_outputs_fail(self):
        with self.assertRaisesRegex(RuntimeError, "analysis outputs"):
            runner.validate_acceptance_authorization(self.changed(self.good_decision(), "analysis_outputs_created", 1))

    def test_acceptance_global_readiness_fails(self):
        with self.assertRaisesRegex(RuntimeError, "readiness"):
            runner.validate_acceptance_authorization(self.changed(self.good_decision(), "global_analysis_readiness", True))

    def test_good_hash_contract_passes(self):
        runner.validate_hash_contract(self.good_hash())

    def test_candidate_hash_drift_fails(self):
        with self.assertRaisesRegex(RuntimeError, "Candidate ID-set"):
            runner.validate_hash_contract(self.changed(self.good_hash(), "observed_candidate_id_set_sha256", "0" * 64))

    def test_layer_hash_drift_fails(self):
        with self.assertRaisesRegex(RuntimeError, "Layer"):
            runner.validate_hash_contract(self.changed(self.good_hash(), "observed_layer_sha256", "0" * 64))

    def test_schema_hash_drift_fails(self):
        with self.assertRaisesRegex(RuntimeError, "Schema"):
            runner.validate_hash_contract(self.changed(self.good_hash(), "observed_schema_sha256", "0" * 64))

    def test_false_hash_flag_fails(self):
        with self.assertRaisesRegex(RuntimeError, "failed hash"):
            runner.validate_hash_contract(self.changed(self.good_hash(), "layer_sha256_match", False))

    def test_good_scope_passes(self):
        runner.validate_scope_contract(self.good_scope())

    def test_accepted_count_drift_fails(self):
        bad = self.good_scope(); bad["observed_counts"]["accepted_usage_layer_rows"] = 642
        with self.assertRaisesRegex(RuntimeError, "scope counts"):
            runner.validate_scope_contract(bad)

    def test_navigation_count_drift_fails(self):
        bad = self.good_scope(); bad["observed_counts"]["navigation_only_rows"] = 1194
        with self.assertRaisesRegex(RuntimeError, "scope counts"):
            runner.validate_scope_contract(bad)

    def test_strict_primary_count_drift_fails(self):
        bad = self.good_scope(); bad["observed_counts"]["strict_primary_manifest_rows"] = 55
        with self.assertRaisesRegex(RuntimeError, "scope counts"):
            runner.validate_scope_contract(bad)

    def test_carried_lane_count_drift_fails(self):
        bad = self.good_scope(); bad["observed_counts"]["non_base_companion"] = 4732
        with self.assertRaisesRegex(RuntimeError, "scope counts"):
            runner.validate_scope_contract(bad)

    def test_contamination_fails(self):
        with self.assertRaisesRegex(RuntimeError, "contamination"):
            runner.validate_scope_contract(self.changed(self.good_scope(), "restricted_navigation_external_contamination_count", 1))

    def test_registry_evidence_rows_fail(self):
        with self.assertRaisesRegex(RuntimeError, "evidence rows"):
            runner.validate_scope_contract(self.changed(self.good_scope(), "evidence_rows_created", 1))

    def test_registry_analysis_outputs_fail(self):
        with self.assertRaisesRegex(RuntimeError, "analysis outputs"):
            runner.validate_scope_contract(self.changed(self.good_scope(), "analysis_outputs_created", 1))

    def test_baseline_dashboard_passes(self):
        runner.validate_dashboard_state(
            {"calibration_phase": "compensation_extraction_limited_qualitative_usage_layer_acceptance_registered_registry_review_prompt_allowed", "analysis_facing_promotion_allowed": False},
            {"overall_status": "limited_qualitative_usage_layer_acceptance_registered_registry_review_only_global_analysis_closed"},
        )

    def test_descendant_dashboard_passes(self):
        runner.validate_dashboard_state(
            {"calibration_phase": "compensation_extraction_limited_qualitative_usage_registry_review_pass_registry_acceptance_prompt_allowed", "analysis_facing_promotion_allowed": False},
            {"overall_status": "limited_qualitative_usage_registry_review_pass_registry_acceptance_prompt_allowed_global_analysis_closed"},
        )

    def test_registry_acceptance_dashboard_passes(self):
        runner.validate_dashboard_state(
            {"calibration_phase": "compensation_extraction_limited_qualitative_usage_registry_acceptance_registered_strategy_prompt_allowed", "analysis_facing_promotion_allowed": False},
            {"overall_status": "limited_qualitative_usage_registry_acceptance_registered_strategy_only_global_analysis_closed"},
        )

    def test_final_qa_phase_close_dashboard_passes(self):
        runner.validate_dashboard_state(
            {"calibration_phase": "compensation_extraction_final_qa_categorization_phase_closed_gabriel_attribute_analysis_ready", "analysis_facing_promotion_allowed": False},
            {"overall_status": "final_qa_categorization_closed_gabriel_attribute_ready_global_analysis_closed"},
        )

    def test_wrong_dashboard_phase_fails(self):
        with self.assertRaisesRegex(RuntimeError, "phase"):
            runner.validate_dashboard_state(
                {"calibration_phase": "analysis_ready", "analysis_facing_promotion_allowed": False},
                {"overall_status": "limited_qualitative_usage_layer_acceptance_registered_registry_review_only_global_analysis_closed"},
            )

    def test_dashboard_promotion_fails(self):
        with self.assertRaisesRegex(RuntimeError, "promotion"):
            runner.validate_dashboard_state(
                {"calibration_phase": "compensation_extraction_limited_qualitative_usage_layer_acceptance_registered_registry_review_prompt_allowed", "analysis_facing_promotion_allowed": True},
                {"overall_status": "limited_qualitative_usage_layer_acceptance_registered_registry_review_only_global_analysis_closed"},
            )

    def test_dashboard_overall_status_fails(self):
        with self.assertRaisesRegex(RuntimeError, "overall"):
            runner.validate_dashboard_state(
                {"calibration_phase": "compensation_extraction_limited_qualitative_usage_layer_acceptance_registered_registry_review_prompt_allowed", "analysis_facing_promotion_allowed": False},
                {"overall_status": "analysis_ready"},
            )

    def test_dashboard_embedded_global_readiness_true_fails(self):
        with self.assertRaisesRegex(RuntimeError, "global"):
            runner.validate_dashboard_state(
                {"calibration_phase": "compensation_extraction_limited_qualitative_usage_layer_acceptance_registered_registry_review_prompt_allowed", "analysis_facing_promotion_allowed": False},
                {"overall_status": "limited_qualitative_usage_layer_acceptance_registered_registry_review_only_global_analysis_closed", "global_analysis_readiness": True},
            )

    def test_future_prompt_case_insensitive_passes(self):
        runner.validate_prompt("\n".join(runner.FUTURE_PROMPT_REQUIRED).upper(), runner.FUTURE_PROMPT_REQUIRED)

    def test_future_prompt_missing_constraint_fails(self):
        with self.assertRaisesRegex(RuntimeError, "missing"):
            runner.validate_prompt("registry acceptance only", runner.FUTURE_PROMPT_REQUIRED)

    def test_relay_complete_fields_pass(self):
        runner.validate_relay_metadata({field: "present" for field in runner.RELAY_REQUIRED})

    def test_relay_missing_field_fails(self):
        with self.assertRaisesRegex(RuntimeError, "missing"):
            runner.validate_relay_metadata({"commit_hash": "x"})

    def test_complete_checkpoint_passes(self):
        runner.validate_checkpoint({"status": "complete", "processed": 643, "expected": 643})

    def test_partial_checkpoint_fails(self):
        with self.assertRaisesRegex(RuntimeError, "Partial"):
            runner.validate_checkpoint({"status": "partial", "processed": 642, "expected": 643})

    def test_output_guard_rejects_tmp(self):
        with self.assertRaisesRegex(RuntimeError, "docs/analysis"):
            runner.output_guard(ROOT / "tmp" / "bad-registry-review-output")


@unittest.skipUnless(OUTPUT.is_dir(), "registry-review output not materialized")
class MaterializedRegistryReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hashes, _ = runner.verify_inputs()
        cls.signature = runner.input_signature(cls.hashes)
        runner.validate_complete_output(OUTPUT, cls.signature)
        cls.decision = runner.read_json(OUTPUT / "limited_qualitative_usage_registry_review_decision.json")
        cls.hash_audit = runner.read_json(OUTPUT / "limited_qualitative_usage_registry_hash_audit.json")
        cls.scope = runner.read_json(OUTPUT / "limited_qualitative_usage_registry_scope_audit.json")
        cls.invariants = runner.read_json(OUTPUT / "limited_qualitative_usage_registry_review_invariant_checks.json")

    def test_all_required_outputs_exist(self):
        self.assertTrue(all((OUTPUT / name).is_file() for name in runner.REQUIRED_OUTPUTS))

    def test_decision_is_pass(self):
        self.assertEqual(self.decision["decision"], runner.DECISION)

    def test_output_is_registry_review_only(self):
        self.assertEqual(self.decision["record_type"], "registry_review_only")

    def test_candidate_hash_verified(self):
        self.assertEqual(self.hash_audit["observed_candidate_id_set_sha256"], runner.AUTHORIZED_ID_HASH)

    def test_layer_hash_verified(self):
        self.assertEqual(self.hash_audit["observed_layer_sha256"], runner.AUTHORIZED_LAYER_HASH)

    def test_schema_hash_verified(self):
        self.assertEqual(self.hash_audit["observed_schema_sha256"], runner.AUTHORIZED_SCHEMA_HASH)

    def test_registered_rows_643(self):
        self.assertEqual(self.decision["registered_accepted_rows"], 643)

    def test_contamination_zero(self):
        self.assertEqual(self.scope["restricted_navigation_external_contamination_count"], 0)

    def test_strict_primary_56(self):
        self.assertEqual(self.decision["strict_primary_manifest_rows"], 56)

    def test_carried_counts_stable(self):
        self.assertEqual(self.decision["counts"]["quantitative_candidates"], 862)
        self.assertEqual(self.decision["counts"]["quantitative_exceptions"], 1045)
        self.assertEqual(self.decision["counts"]["non_base_companion"], 4733)
        self.assertEqual(self.decision["counts"]["reference_control"], 345)
        self.assertEqual(self.decision["counts"]["unresolved_conflict_observations"], 5)

    def test_no_evidence_rows_created(self):
        self.assertEqual(self.decision["evidence_rows_created"], 0)

    def test_no_analysis_outputs_created(self):
        self.assertEqual(self.decision["analysis_outputs_created"], 0)

    def test_readiness_and_promotion_closed(self):
        self.assertFalse(self.decision["global_analysis_readiness"])
        self.assertFalse(self.decision["full_qualitative_readiness"])
        self.assertFalse(self.decision["analysis_facing_promotion_allowed"])

    def test_all_invariants_passed(self):
        self.assertTrue(self.invariants["all_invariants_passed"])

    def test_future_prompt_complete(self):
        text = (OUTPUT / "next_limited_qualitative_usage_registry_acceptance_prompt.md").read_text(encoding="utf-8")
        runner.validate_prompt(text, runner.FUTURE_PROMPT_REQUIRED)

    def test_resume_is_idempotent(self):
        before = {name: runner.sha256(OUTPUT / name) for name in runner.REQUIRED_OUTPUTS}
        result = subprocess.run(
            [sys.executable, str(Path(runner.__file__)), "--resume"], cwd=ROOT,
            capture_output=True, text=True, check=True,
        )
        self.assertEqual(json.loads(result.stdout)["writes"], 0)
        after = {name: runner.sha256(OUTPUT / name) for name in runner.REQUIRED_OUTPUTS}
        self.assertEqual(before, after)

    def test_no_forbidden_payload_extensions(self):
        forbidden = {".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".webp"}
        self.assertFalse(any(path.suffix.casefold() in forbidden for path in OUTPUT.rglob("*")))


if __name__ == "__main__":
    unittest.main(verbosity=2)
