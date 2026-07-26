#!/usr/bin/env python3
"""Adversarial tests for the claim-oriented compensation phase close."""

from __future__ import annotations

import copy
import json
import tempfile
import unittest
from collections import Counter
from pathlib import Path

import run_compensation_evidence_claim_oriented_phase_close as runner


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class ClaimPhasePreflightTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hashes, cls.signature = runner.verify_inputs()
        cls.rows, cls.manifests = runner.categorize()

    def test_authorized_descendant_and_inputs(self):
        self.assertGreater(len(self.hashes), 20)

    def test_input_signature_is_sha256(self):
        self.assertEqual(len(self.signature), 64)

    def test_considered_records_8939(self):
        self.assertEqual(len(self.rows), 8939)

    def test_evidence_ids_unique(self):
        self.assertEqual(len({row["evidence_id"] for row in self.rows}), 8939)

    def test_all_primary_categories_controlled(self):
        self.assertTrue(all(row["claim_oriented_primary_category"] in runner.PRIMARY_CATEGORIES for row in self.rows))

    def test_primary_counts_reconcile(self):
        counts = Counter(row["claim_oriented_primary_category"] for row in self.rows)
        self.assertEqual({key: counts.get(key, 0) for key in runner.PRIMARY_CATEGORIES}, runner.EXPECTED_PRIMARY_COUNTS)

    def test_manifest_counts_reconcile(self):
        self.assertEqual({name: len(rows) for name, rows in self.manifests.items()}, runner.EXPECTED_MANIFEST_COUNTS)

    def test_claim_ready_aggregate_1505(self):
        self.assertEqual(len(self.manifests["claim_ready_evidence_manifest.csv"]), 1505)

    def test_quantitative_direct_count_862(self):
        self.assertEqual(len(self.manifests["quantitative_direct_text_claim_ready_manifest.csv"]), 862)

    def test_qualitative_mechanism_count_643(self):
        self.assertEqual(len(self.manifests["qualitative_mechanism_claim_ready_manifest.csv"]), 643)

    def test_causal_candidate_count_zero_before_rating(self):
        self.assertEqual(self.manifests["causal_candidate_supporting_evidence_manifest.csv"], [])

    def test_gabriel_rating_count_643(self):
        self.assertEqual(len(self.manifests["gabriel_claim_rating_ready_evidence_manifest.csv"]), 643)

    def test_navigation_count_614(self):
        self.assertEqual(len(self.manifests["navigation_only_evidence_manifest.csv"]), 614)

    def test_companion_count_5078(self):
        self.assertEqual(len(self.manifests["companion_context_evidence_manifest.csv"]), 5078)

    def test_quarantine_count_121(self):
        self.assertEqual(len(self.manifests["quarantined_evidence_manifest.csv"]), 121)

    def test_writeoff_count_1621(self):
        self.assertEqual(len(self.manifests["write_off_this_phase_manifest.csv"]), 1621)

    def test_rating_manifest_exact_span_only(self):
        rows = self.manifests["gabriel_claim_rating_ready_evidence_manifest.csv"]
        self.assertTrue(all(row["direct_text_support_type"] == "exact_verified_span" for row in rows))
        self.assertTrue(all(row["source_lane"] == "qualitative_exact" for row in rows))

    def test_quantitative_values_explicit(self):
        rows = self.manifests["quantitative_direct_text_claim_ready_manifest.csv"]
        self.assertTrue(all(row["direct_text_value_fields"] for row in rows))
        self.assertTrue(all(row["claim_reason_code"] in {"explicit_wage_value", "explicit_raise_value"} for row in rows))

    def test_quantitative_support_is_structured_not_inferred(self):
        rows = self.manifests["quantitative_direct_text_claim_ready_manifest.csv"]
        self.assertTrue(all(row["direct_text_support_type"] == "accepted_structured_extracted_value" for row in rows))

    def test_weak_evidence_written_off(self):
        rows = self.manifests["write_off_this_phase_manifest.csv"]
        self.assertEqual(Counter(row["claim_reason_code"] for row in rows), Counter({"quant_exception": 1040, "span_unavailable": 581}))

    def test_ambiguous_evidence_navigation_only(self):
        rows = self.manifests["navigation_only_evidence_manifest.csv"]
        self.assertTrue(all(row["claim_reason_code"] == "ambiguous_span" for row in rows))

    def test_conflicts_and_restricted_quarantined(self):
        rows = self.manifests["quarantined_evidence_manifest.csv"]
        self.assertEqual(Counter(row["claim_reason_code"] for row in rows), Counter({"restricted_review_status": 116, "unresolved_conflict": 5}))

    def test_non_base_and_reference_context_only(self):
        rows = self.manifests["companion_context_evidence_manifest.csv"]
        self.assertEqual(Counter(row["claim_reason_code"] for row in rows), Counter({"non_base_companion": 4733, "reference_control": 345}))

    def test_excluded_categories_not_claim_ready(self):
        excluded = {"navigation_only", "quarantined", "write_off_this_phase"}
        self.assertTrue(all(row["claim_ready_aggregate_eligible"] == "false" for row in self.rows if row["claim_oriented_primary_category"] in excluded))

    def test_all_causal_language_provisional(self):
        self.assertTrue(all(row["provisional_causal_candidate_only"] == "true" for row in self.rows))

    def test_no_final_claim_permissions(self):
        self.assertTrue(all("final_wage_gap_claim" in row["not_supported_claim_types"] for row in self.rows))

    def test_reason_codes_nonblank(self):
        self.assertTrue(all(row["claim_reason_code"] for row in self.rows))

    def test_no_vague_reason_codes(self):
        self.assertFalse({row["claim_reason_code"].casefold() for row in self.rows}.intersection({"null", "no_good"}))


class ClaimPhaseGuardrailTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows, cls.manifests = runner.categorize()

    def test_output_guard_rejects_tmp(self):
        with self.assertRaisesRegex(RuntimeError, "docs/analysis"):
            runner.output_guard(runner.ROOT / "tmp/forbidden")

    def test_output_guard_rejects_existing(self):
        with tempfile.TemporaryDirectory(dir=runner.ROOT / "docs/analysis") as name:
            with self.assertRaises(FileExistsError):
                runner.output_guard(Path(name))

    def test_duplicate_evidence_id_fails(self):
        rows = copy.deepcopy(self.rows)
        rows[1]["evidence_id"] = rows[0]["evidence_id"]
        with self.assertRaisesRegex(RuntimeError, "unique evidence ID"):
            runner.validate_rows(rows)

    def test_unknown_primary_category_fails(self):
        rows = copy.deepcopy(self.rows)
        rows[0]["claim_oriented_primary_category"] = "no_good"
        with self.assertRaisesRegex(RuntimeError, "counts"):
            runner.validate_rows(rows)

    def test_navigation_claim_ready_fails(self):
        rows = copy.deepcopy(self.rows)
        row = next(item for item in rows if item["claim_oriented_primary_category"] == "navigation_only")
        row["claim_ready_aggregate_eligible"] = "true"
        with self.assertRaisesRegex(RuntimeError, "Excluded"):
            runner.validate_rows(rows)

    def test_rating_wrong_lane_fails(self):
        rows = copy.deepcopy(self.rows)
        row = next(item for item in rows if item["gabriel_claim_rating_eligible"] == "true")
        row["source_lane"] = "quantitative_candidate"
        with self.assertRaisesRegex(RuntimeError, "GABRIEL"):
            runner.validate_rows(rows)

    def test_rating_non_exact_support_fails(self):
        rows = copy.deepcopy(self.rows)
        row = next(item for item in rows if item["gabriel_claim_rating_eligible"] == "true")
        row["direct_text_support_type"] = "paraphrase"
        with self.assertRaisesRegex(RuntimeError, "GABRIEL"):
            runner.validate_rows(rows)

    def test_quantitative_missing_direct_values_fails(self):
        rows = copy.deepcopy(self.rows)
        row = next(item for item in rows if item["claim_oriented_primary_category"] == "quantitative_direct_text_claim_ready")
        row["direct_text_value_fields"] = ""
        with self.assertRaisesRegex(RuntimeError, "Quantitative"):
            runner.validate_rows(rows)

    def test_nonprovisional_causal_boundary_fails(self):
        rows = copy.deepcopy(self.rows)
        rows[0]["provisional_causal_candidate_only"] = "false"
        with self.assertRaisesRegex(RuntimeError, "provisional"):
            runner.validate_rows(rows)

    def test_blank_reason_fails(self):
        rows = copy.deepcopy(self.rows)
        rows[0]["claim_reason_code"] = ""
        with self.assertRaisesRegex(RuntimeError, "reason"):
            runner.validate_rows(rows)

    def test_vague_reason_fails(self):
        rows = copy.deepcopy(self.rows)
        rows[0]["claim_reason_code"] = "no_good"
        with self.assertRaisesRegex(RuntimeError, "reason"):
            runner.validate_rows(rows)

    def test_taxonomy_passes(self):
        runner.validate_taxonomy(runner.taxonomy_payload())

    def test_taxonomy_has_v1(self):
        self.assertEqual(runner.taxonomy_payload()["attribute_taxonomy_version"], "v1")

    def test_taxonomy_has_13_attributes(self):
        self.assertEqual(len(runner.taxonomy_payload()["attributes"]), 13)

    def test_taxonomy_missing_attribute_fails(self):
        payload = runner.taxonomy_payload()
        payload["attributes"].pop()
        with self.assertRaisesRegex(RuntimeError, "taxonomy"):
            runner.validate_taxonomy(payload)

    def test_taxonomy_duplicate_attribute_fails(self):
        payload = runner.taxonomy_payload()
        payload["attributes"][-1] = copy.deepcopy(payload["attributes"][0])
        with self.assertRaisesRegex(RuntimeError, "taxonomy"):
            runner.validate_taxonomy(payload)

    def test_taxonomy_wrong_version_fails(self):
        payload = runner.taxonomy_payload()
        payload["attribute_taxonomy_version"] = "v2"
        with self.assertRaisesRegex(RuntimeError, "v1"):
            runner.validate_taxonomy(payload)

    def test_taxonomy_incomplete_definition_fails(self):
        payload = runner.taxonomy_payload()
        payload["attributes"][0]["exclusion_rule"] = ""
        with self.assertRaisesRegex(RuntimeError, "Incomplete"):
            runner.validate_taxonomy(payload)

    def test_taxonomy_required_fields_drift_fails(self):
        payload = runner.taxonomy_payload()
        payload["required_rating_fields"].remove("claim_boundary")
        with self.assertRaisesRegex(RuntimeError, "fields"):
            runner.validate_taxonomy(payload)

    def test_rating_schema_has_required_continuous_fields(self):
        required = set(runner.rating_schema()["properties"]["attribute_ratings"]["items"]["required"])
        self.assertTrue({"attribute_present", "direction_of_pressure", "evidence_strength", "claim_relevance", "reason_code", "supporting_quote", "claim_boundary"}.issubset(required))

    def test_rating_schema_forbids_final_causality(self):
        self.assertFalse(runner.rating_schema()["invariants"]["final_causal_claims_allowed"])

    def test_claim_bridge_allows_direct_text(self):
        status = {row["claim_type"]: row["current_status"] for row in runner.claim_bridge_rows()}
        self.assertEqual(status["direct_text_claim"], "allowed_now")

    def test_claim_bridge_keeps_causal_provisional(self):
        status = {row["claim_type"]: row["current_status"] for row in runner.claim_bridge_rows()}
        self.assertEqual(status["causal_candidate_claim"], "allowed_only_as_provisional_scaffold")

    def test_claim_bridge_forbids_final_claim(self):
        status = {row["claim_type"]: row["current_status"] for row in runner.claim_bridge_rows()}
        self.assertEqual(status["forbidden_final_claim"], "forbidden")

    def test_future_prompt_complete(self):
        runner.validate_prompt("\n".join(runner.FUTURE_PROMPT_REQUIRED))

    def test_future_prompt_missing_constraint_fails(self):
        with self.assertRaisesRegex(RuntimeError, "missing"):
            runner.validate_prompt("\n".join(runner.FUTURE_PROMPT_REQUIRED[:-1]))

    def test_complete_checkpoint_passes(self):
        runner.validate_checkpoint({"status": "complete", "processed": 8939, "expected": 8939})

    def test_partial_checkpoint_fails(self):
        with self.assertRaisesRegex(RuntimeError, "Partial"):
            runner.validate_checkpoint({"status": "partial", "processed": 100, "expected": 8939})

    def test_relay_metadata_passes(self):
        runner.validate_relay_metadata({key: "x" for key in runner.RELAY_REQUIRED})

    def test_relay_missing_push_fails(self):
        record = {key: "x" for key in runner.RELAY_REQUIRED}
        record.pop("push_status")
        with self.assertRaisesRegex(RuntimeError, "push_status"):
            runner.validate_relay_metadata(record)

    def test_repo_inventory_never_authorizes_deletion(self):
        rows, summary = runner.build_repo_inventory()
        self.assertTrue(rows)
        self.assertTrue(all(row["deletion_authorized"] == "false" for row in rows))
        self.assertFalse(summary["deletion_authorized"])


@unittest.skipUnless(runner.DEFAULT_OUTPUT_DIR.exists(), "materialized claim-oriented output not present")
class MaterializedClaimPhaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hashes, cls.signature = runner.verify_inputs()
        cls.output = runner.DEFAULT_OUTPUT_DIR

    def test_complete_output_passes(self):
        runner.validate_complete_output(self.output, self.signature)

    def test_decision_passes(self):
        decision = read_json(self.output / "claim_oriented_phase_close_decision.json")
        self.assertEqual(decision["decision"], runner.DECISION)

    def test_global_readiness_false(self):
        self.assertFalse(read_json(self.output / "claim_oriented_phase_close_decision.json")["global_analysis_readiness"])

    def test_manifest_counts(self):
        for name, count in runner.EXPECTED_MANIFEST_COUNTS.items():
            self.assertEqual(len(runner.read_csv(self.output / name)), count)

    def test_invariants_pass(self):
        self.assertTrue(read_json(self.output / "claim_oriented_phase_close_invariant_checks.json")["all_invariants_passed"])

    def test_prompt_passes(self):
        runner.validate_prompt((self.output / "next_gabriel_claim_oriented_attribute_rating_prompt.md").read_text(encoding="utf-8"))

    def test_no_forbidden_payload_columns(self):
        rows = runner.read_csv(self.output / "claim_oriented_evidence_category_registry.csv")
        self.assertFalse({"full_page_text", "full_text", "raw_page_payload", "raw_model_response"}.intersection(rows[0]))

    def test_resume_validation_is_idempotent(self):
        before = {path.name: runner.sha256(path) for path in self.output.iterdir() if path.is_file()}
        runner.validate_complete_output(self.output, self.signature)
        after = {path.name: runner.sha256(path) for path in self.output.iterdir() if path.is_file()}
        self.assertEqual(before, after)

    def test_dashboard_phase_is_claim_rating_ready_only(self):
        calibration = read_json(runner.ROOT / "docs/dashboard/data/text_table_calibration_status_summary.json")
        self.assertIn(calibration["calibration_phase"], {
            "compensation_extraction_claim_oriented_phase_closed_gabriel_claim_rating_ready",
            "compensation_extraction_gabriel_claim_rating_643_completed_summary_review_allowed",
            "compensation_extraction_gabriel_claim_rating_643_completed_with_quarantine",
            "compensation_extraction_gabriel_claim_rating_643_repaired_summary_review_allowed",
            "compensation_extraction_gabriel_claim_rating_643_repaired_with_remaining_quarantine_summary_review_allowed",
            "compensation_extraction_gabriel_claim_rating_summary_review_636_completed_provisional_claim_review_allowed",
            "compensation_extraction_provisional_claim_review_636_completed_targeted_scouting_restart_recommended",
        })
        self.assertTrue(calibration["gabriel_claim_rating_ready"])
        self.assertFalse(calibration["analysis_facing_promotion_allowed"])

    def test_dashboard_global_analysis_remains_closed(self):
        readiness = read_json(runner.ROOT / "docs/dashboard/data/analysis_readiness.json")
        self.assertIn(readiness["overall_status"], {
            "claim_oriented_phase_closed_gabriel_claim_rating_ready_global_analysis_closed",
            "gabriel_claim_rating_643_completed_summary_review_allowed_global_analysis_closed",
            "gabriel_claim_rating_643_completed_with_quarantine_global_analysis_closed",
            "gabriel_claim_rating_643_repaired_summary_review_allowed_global_analysis_closed",
            "gabriel_claim_rating_643_repaired_with_remaining_quarantine_summary_review_allowed_global_analysis_closed",
            "gabriel_claim_rating_summary_review_636_completed_provisional_claim_review_allowed_global_analysis_closed",
            "provisional_claim_review_636_completed_targeted_scouting_restart_recommended_global_analysis_closed",
        })
        self.assertNotIn('"global_analysis_readiness": true', json.dumps(readiness, sort_keys=True).casefold())


if __name__ == "__main__":
    unittest.main(verbosity=2)
