#!/usr/bin/env python3
"""Adversarial tests for final QA categorization and GABRIEL readiness."""

from __future__ import annotations

import copy
import csv
import json
import tempfile
import unittest
from collections import Counter
from pathlib import Path

import run_compensation_evidence_final_qa_categorization_gabriel_readiness as runner


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class PhaseClosePreflightTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hashes, cls.source = runner.verify_inputs()
        cls.master, cls.by_category, cls.lanes = runner.classify_rows()

    def test_authorized_commit_is_ancestor(self):
        self.assertTrue(self.hashes)

    def test_14_acceptance_inputs_plus_7_data_inputs(self):
        self.assertEqual(len(runner.ACCEPTANCE_INPUTS) + len(runner.DIRECT_DATA_INPUTS), 21)

    def test_input_contract_includes_package_and_dashboard(self):
        self.assertEqual(len(self.hashes), 28)

    def test_acceptance_decision_authorizes_close(self):
        self.assertEqual(self.source["decision"]["decision"], runner.acceptance.DECISION)

    def test_candidate_id_hash_matches_accepted_registry(self):
        ids = {row["row_document_id"] for row in self.by_category["gabriel_attribute_ready"]}
        self.assertEqual(runner.id_set_sha256(ids), runner.acceptance.AUTHORIZED_ID_HASH)

    def test_five_package_hashes_in_contract(self):
        expected = {path.resolve().relative_to(runner.ROOT.resolve()).as_posix() for path, _ in runner.accelerator.PACKAGE_LEDGER_HASHES.values()}
        self.assertTrue(expected.issubset(self.hashes))

    def test_lane_counts_exact(self):
        self.assertEqual(self.lanes, runner.EXPECTED_LANE_COUNTS)

    def test_master_count_8939(self):
        self.assertEqual(len(self.master), 8939)

    def test_evidence_ids_unique(self):
        ids = [row["evidence_id"] for row in self.master]
        self.assertEqual(len(ids), len(set(ids)))

    def test_exactly_six_primary_categories(self):
        self.assertEqual(set(row["primary_category"] for row in self.master), set(runner.PRIMARY_CATEGORIES))

    def test_category_counts_exact(self):
        self.assertEqual(dict(Counter(row["primary_category"] for row in self.master)), runner.EXPECTED_CATEGORY_COUNTS)

    def test_gabriel_ready_count_643(self):
        self.assertEqual(len(self.by_category["gabriel_attribute_ready"]), 643)

    def test_limited_documentary_count_862(self):
        self.assertEqual(len(self.by_category["limited_documentary_claim_ready"]), 862)

    def test_navigation_count_614(self):
        self.assertEqual(len(self.by_category["navigation_only"]), 614)

    def test_companion_count_5078(self):
        self.assertEqual(len(self.by_category["companion_context_only"]), 5078)

    def test_quarantine_count_121(self):
        self.assertEqual(len(self.by_category["quarantined"]), 121)

    def test_writeoff_count_1621(self):
        self.assertEqual(len(self.by_category["write_off_this_phase"]), 1621)

    def test_gabriel_ready_exact_span_only(self):
        rows = self.by_category["gabriel_attribute_ready"]
        self.assertTrue(all(row["source_lane"] == "qualitative_exact" for row in rows))
        self.assertTrue(all(row["reason_code"] == "exact_span_verified" for row in rows))
        self.assertTrue(all(row["evidence_span_or_summary_pointer"] for row in rows))

    def test_restricted_exact_spans_quarantined(self):
        rows = [row for row in self.master if row["reason_code"] == "restricted_review_status"]
        self.assertEqual(len(rows), 116)
        self.assertTrue(all(row["primary_category"] == "quarantined" for row in rows))

    def test_ambiguous_spans_navigation_only(self):
        rows = [row for row in self.master if row["reason_code"] == "ambiguous_span"]
        self.assertEqual(len(rows), 614)
        self.assertTrue(all(row["primary_category"] == "navigation_only" for row in rows))

    def test_unavailable_spans_written_off(self):
        rows = [row for row in self.master if row["reason_code"] == "span_unavailable"]
        self.assertEqual(len(rows), 581)
        self.assertTrue(all(row["primary_category"] == "write_off_this_phase" for row in rows))

    def test_quant_candidates_limited_documentary_only(self):
        rows = self.by_category["limited_documentary_claim_ready"]
        self.assertTrue(all(row["source_lane"] == "quantitative_candidate" for row in rows))
        self.assertTrue(all("no_quantitative_wage_claim" in row["secondary_tags"] for row in rows))

    def test_quant_exceptions_written_off_except_conflicts(self):
        rows = [row for row in self.master if row["source_lane"] == "quantitative_exception"]
        self.assertEqual(Counter(row["primary_category"] for row in rows), Counter({"write_off_this_phase": 1040, "quarantined": 5}))

    def test_two_groups_five_conflicts_quarantined(self):
        rows = [row for row in self.master if row["reason_code"] == "unresolved_conflict"]
        self.assertEqual(len(rows), 5)
        self.assertEqual(len({row["secondary_tags"].split("conflict_group:", 1)[1] for row in rows}), 2)

    def test_non_base_companion_only(self):
        rows = [row for row in self.master if row["source_lane"] == "non_base_companion"]
        self.assertEqual(len(rows), 4733)
        self.assertTrue(all(row["primary_category"] == "companion_context_only" for row in rows))

    def test_reference_control_companion_only(self):
        rows = [row for row in self.master if row["source_lane"] == "reference_control"]
        self.assertEqual(len(rows), 345)
        self.assertTrue(all(row["primary_category"] == "companion_context_only" for row in rows))

    def test_reference_keys_unique(self):
        rows = runner.read_csv(runner.REFERENCE_PATH)
        keys = [runner.reference_key(row) for row in rows]
        self.assertEqual(len(keys), len(set(keys)))

    def test_all_exclude_causal_claims(self):
        self.assertTrue(all(row["exclude_from_causal_claims"] == "true" for row in self.master))

    def test_no_full_page_or_model_payload_columns(self):
        self.assertFalse({"full_page_text", "full_text", "raw_page_payload", "raw_model_response"}.intersection(self.master[0]))

    def test_gabriel_rows_get_attribute_set_only(self):
        self.assertTrue(all(row["allowed_attribute_set"] == runner.ATTRIBUTE_SET for row in self.by_category["gabriel_attribute_ready"]))
        nonready = [row for row in self.master if row["primary_category"] != "gabriel_attribute_ready"]
        self.assertTrue(all(not row["allowed_attribute_set"] for row in nonready))

    def test_no_wage_gap_or_causal_claim_permission(self):
        allowed = "|".join(row["allowed_claim_types"] for row in self.master)
        self.assertNotIn("wage_gap_claim", allowed)
        self.assertNotIn("causal_claim", allowed)


class PhaseCloseGuardrailTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.master, _, _ = runner.classify_rows()

    def test_output_guard_rejects_tmp(self):
        with self.assertRaisesRegex(RuntimeError, "under docs/analysis"):
            runner.output_guard(runner.ROOT / "tmp/forbidden")

    def test_output_guard_rejects_existing(self):
        with tempfile.TemporaryDirectory(dir=runner.ROOT / "docs/analysis") as name:
            with self.assertRaises(FileExistsError):
                runner.output_guard(Path(name))

    def test_wrong_acceptance_decision_fails(self):
        record = {"decision": "wrong"}
        with self.assertRaisesRegex(RuntimeError, "did not pass"):
            runner.validate_acceptance(record)

    def test_acceptance_readiness_true_fails(self):
        record = {
            "decision": runner.acceptance.DECISION, "record_type": "registry_acceptance_only",
            "registered_accepted_rows": 643, "restricted_navigation_external_contamination_count": 0,
            "global_analysis_readiness": True,
        }
        with self.assertRaisesRegex(RuntimeError, "readiness"):
            runner.validate_acceptance(record)

    def test_baseline_dashboard_passes(self):
        runner.validate_dashboard_state(
            {"calibration_phase": "compensation_extraction_limited_qualitative_usage_registry_acceptance_registered_strategy_prompt_allowed", "analysis_facing_promotion_allowed": False},
            {"overall_status": "limited_qualitative_usage_registry_acceptance_registered_strategy_only_global_analysis_closed"},
        )

    def test_descendant_dashboard_passes(self):
        runner.validate_dashboard_state(
            {"calibration_phase": "compensation_extraction_final_qa_categorization_phase_closed_gabriel_attribute_analysis_ready", "analysis_facing_promotion_allowed": False},
            {"overall_status": "final_qa_categorization_closed_gabriel_attribute_ready_global_analysis_closed"},
        )

    def test_dashboard_phase_jump_fails(self):
        with self.assertRaisesRegex(RuntimeError, "phase"):
            runner.validate_dashboard_state(
                {"calibration_phase": "analysis_ready", "analysis_facing_promotion_allowed": False},
                {"overall_status": "limited_qualitative_usage_registry_acceptance_registered_strategy_only_global_analysis_closed"},
            )

    def test_dashboard_promotion_true_fails(self):
        with self.assertRaisesRegex(RuntimeError, "promotion"):
            runner.validate_dashboard_state(
                {"calibration_phase": "compensation_extraction_limited_qualitative_usage_registry_acceptance_registered_strategy_prompt_allowed", "analysis_facing_promotion_allowed": True},
                {"overall_status": "limited_qualitative_usage_registry_acceptance_registered_strategy_only_global_analysis_closed"},
            )

    def test_dashboard_global_readiness_true_fails(self):
        with self.assertRaisesRegex(RuntimeError, "global"):
            runner.validate_dashboard_state(
                {"calibration_phase": "compensation_extraction_limited_qualitative_usage_registry_acceptance_registered_strategy_prompt_allowed", "analysis_facing_promotion_allowed": False},
                {"overall_status": "limited_qualitative_usage_registry_acceptance_registered_strategy_only_global_analysis_closed", "global_analysis_readiness": True},
            )

    def test_duplicate_evidence_id_fails(self):
        rows = copy.deepcopy(self.master)
        rows[1]["evidence_id"] = rows[0]["evidence_id"]
        with self.assertRaisesRegex(RuntimeError, "unique evidence ID"):
            runner.validate_category_rows(rows)

    def test_missing_category_fails(self):
        rows = copy.deepcopy(self.master)
        rows[0]["primary_category"] = ""
        with self.assertRaisesRegex(RuntimeError, "primary category"):
            runner.validate_category_rows(rows)

    def test_unknown_category_fails(self):
        rows = copy.deepcopy(self.master)
        rows[0]["primary_category"] = "no_good"
        with self.assertRaisesRegex(RuntimeError, "primary category"):
            runner.validate_category_rows(rows)

    def test_gabriel_ready_wrong_lane_fails(self):
        rows = copy.deepcopy(self.master)
        candidate = next(row for row in rows if row["primary_category"] == "gabriel_attribute_ready")
        candidate["source_lane"] = "quantitative_candidate"
        with self.assertRaisesRegex(RuntimeError, "GABRIEL-ready"):
            runner.validate_category_rows(rows)

    def test_gabriel_ready_missing_span_fails(self):
        rows = copy.deepcopy(self.master)
        candidate = next(row for row in rows if row["primary_category"] == "gabriel_attribute_ready")
        candidate["evidence_span_or_summary_pointer"] = ""
        with self.assertRaisesRegex(RuntimeError, "span"):
            runner.validate_category_rows(rows)

    def test_navigation_with_attribute_set_fails(self):
        rows = copy.deepcopy(self.master)
        candidate = next(row for row in rows if row["primary_category"] == "navigation_only")
        candidate["allowed_attribute_set"] = runner.ATTRIBUTE_SET
        with self.assertRaisesRegex(RuntimeError, "Excluded category"):
            runner.validate_category_rows(rows)

    def test_causal_flag_false_fails(self):
        rows = copy.deepcopy(self.master)
        rows[0]["exclude_from_causal_claims"] = "false"
        with self.assertRaisesRegex(RuntimeError, "causal"):
            runner.validate_category_rows(rows)

    def test_taxonomy_passes(self):
        runner.validate_taxonomy(runner.taxonomy_payload())

    def test_taxonomy_missing_attribute_fails(self):
        payload = runner.taxonomy_payload()
        payload["attributes"].pop()
        with self.assertRaisesRegex(RuntimeError, "taxonomy"):
            runner.validate_taxonomy(payload)

    def test_taxonomy_duplicate_fails(self):
        payload = runner.taxonomy_payload()
        payload["attributes"][-1] = copy.deepcopy(payload["attributes"][0])
        with self.assertRaisesRegex(RuntimeError, "taxonomy"):
            runner.validate_taxonomy(payload)

    def test_vague_null_taxonomy_fails(self):
        payload = runner.taxonomy_payload()
        payload["attributes"][-1]["attribute_id"] = "null"
        with self.assertRaisesRegex(RuntimeError, "taxonomy|Vague"):
            runner.validate_taxonomy(payload)

    def test_not_useful_without_reason_requirement_fails(self):
        payload = runner.taxonomy_payload()
        payload["required_reason_code_when_not_useful"] = False
        with self.assertRaisesRegex(RuntimeError, "reason"):
            runner.validate_taxonomy(payload)

    def test_claim_registry_passes(self):
        runner.validate_claim_registry(runner.claim_rows())

    def test_missing_claim_type_fails(self):
        rows = runner.claim_rows()[:-1]
        with self.assertRaisesRegex(RuntimeError, "seven"):
            runner.validate_claim_registry(rows)

    def test_wage_gap_claim_opened_fails(self):
        rows = runner.claim_rows()
        next(row for row in rows if row["claim_type"] == "wage_gap_claim")["current_status"] = "allowed_now"
        with self.assertRaisesRegex(RuntimeError, "wage_gap_claim"):
            runner.validate_claim_registry(rows)

    def test_causal_claim_opened_fails(self):
        rows = runner.claim_rows()
        next(row for row in rows if row["claim_type"] == "causal_claim")["current_status"] = "allowed_now"
        with self.assertRaisesRegex(RuntimeError, "causal_claim"):
            runner.validate_claim_registry(rows)

    def test_future_prompt_complete(self):
        text = "\n".join(runner.FUTURE_PROMPT_REQUIRED)
        runner.validate_prompt(text)

    def test_future_prompt_missing_constraint_fails(self):
        text = "\n".join(runner.FUTURE_PROMPT_REQUIRED[:-1])
        with self.assertRaisesRegex(RuntimeError, "missing"):
            runner.validate_prompt(text)

    def test_complete_checkpoint_passes(self):
        runner.validate_checkpoint({"status": "complete", "processed": 8939, "expected": 8939})

    def test_partial_checkpoint_fails(self):
        with self.assertRaisesRegex(RuntimeError, "Partial"):
            runner.validate_checkpoint({"status": "partial", "processed": 100, "expected": 8939})

    def test_complete_relay_metadata_passes(self):
        runner.validate_relay_metadata({key: "x" for key in runner.RELAY_REQUIRED})

    def test_relay_missing_field_fails(self):
        payload = {key: "x" for key in runner.RELAY_REQUIRED}
        payload.pop("push_status")
        with self.assertRaisesRegex(RuntimeError, "push_status"):
            runner.validate_relay_metadata(payload)


@unittest.skipUnless(runner.DEFAULT_OUTPUT_DIR.exists(), "materialized phase-close output not present")
class MaterializedPhaseCloseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hashes, _ = runner.verify_inputs()
        cls.signature = runner.input_signature(cls.hashes)
        cls.output = runner.DEFAULT_OUTPUT_DIR

    def test_complete_output_passes(self):
        runner.validate_complete_output(self.output, self.signature)

    def test_decision_phase_closed(self):
        decision = read_json(self.output / "final_qa_categorization_phase_close_decision.json")
        self.assertEqual(decision["decision"], runner.DECISION)
        self.assertTrue(decision["phase_closed"])

    def test_global_readiness_remains_false(self):
        decision = read_json(self.output / "final_qa_categorization_phase_close_decision.json")
        self.assertFalse(decision["global_analysis_readiness"])

    def test_manifest_counts_reconcile(self):
        for category, filename in {
            "gabriel_attribute_ready": "gabriel_attribute_ready_evidence_manifest.csv",
            "limited_documentary_claim_ready": "limited_documentary_claims_evidence_manifest.csv",
            "navigation_only": "navigation_only_evidence_manifest.csv",
            "companion_context_only": "companion_context_evidence_manifest.csv",
            "quarantined": "quarantined_evidence_manifest.csv",
            "write_off_this_phase": "write_off_this_phase_manifest.csv",
        }.items():
            self.assertEqual(len(runner.read_csv(self.output / filename)), runner.EXPECTED_CATEGORY_COUNTS[category])

    def test_gabriel_manifest_no_contamination(self):
        rows = runner.read_csv(self.output / "gabriel_attribute_ready_evidence_manifest.csv")
        self.assertTrue(all(row["primary_category"] == "gabriel_attribute_ready" for row in rows))
        self.assertTrue(all(row["source_lane"] == "qualitative_exact" for row in rows))

    def test_taxonomy_is_13_attributes(self):
        payload = read_json(self.output / "gabriel_attribute_taxonomy_machine_readable.json")
        self.assertEqual(len(payload["attributes"]), 13)

    def test_claim_registry_remains_closed(self):
        runner.validate_claim_registry(runner.read_csv(self.output / "evidence_claim_type_registry.csv"))

    def test_invariants_pass(self):
        self.assertTrue(read_json(self.output / "final_qa_categorization_invariant_checks.json")["all_invariants_passed"])

    def test_future_prompt_passes(self):
        runner.validate_prompt((self.output / "next_gabriel_attribute_analysis_prompt.md").read_text(encoding="utf-8"))

    def test_resume_is_idempotent(self):
        before = {path.name: runner.sha256(path) for path in self.output.iterdir() if path.is_file()}
        self.assertEqual(len(before), len(runner.REQUIRED_OUTPUTS))
        runner.validate_complete_output(self.output, self.signature)
        after = {path.name: runner.sha256(path) for path in self.output.iterdir() if path.is_file()}
        self.assertEqual(before, after)

    def test_no_forbidden_payload_columns(self):
        rows = runner.read_csv(self.output / "compensation_evidence_final_category_registry.csv")
        self.assertFalse({"full_page_text", "full_text", "raw_page_payload", "raw_model_response"}.intersection(rows[0]))

    def test_dashboard_phase_is_closed_not_globally_ready(self):
        calibration = read_json(runner.DASHBOARD_INPUTS[0])
        readiness = read_json(runner.DASHBOARD_INPUTS[1])
        runner.validate_dashboard_state(calibration, readiness)


if __name__ == "__main__":
    unittest.main(verbosity=2)
