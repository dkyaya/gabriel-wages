#!/usr/bin/env python3
"""Adversarial tests for bounded GABRIEL claim rating over 643 rows."""

from __future__ import annotations

import copy
import csv
import json
import tempfile
import unittest
from pathlib import Path

import run_compensation_evidence_gabriel_claim_rating_643 as runner
import build_dashboard_data as dashboard
import run_compensation_evidence_limited_qualitative_usage_registry_review as registry_review


def good_rating(row: dict[str, str], *, primary: str = "automatic_raise_mechanism") -> dict:
    quote = row["evidence_span_or_summary_pointer"][: min(12, len(row["evidence_span_or_summary_pointer"]))]
    ratings = {}
    for attribute in runner.ATTRIBUTE_IDS:
        present = attribute == primary
        is_weak = present and attribute == "weak_or_no_claim_support"
        ratings[attribute] = {
            "attribute_present": present,
            "direction_of_pressure": "neutral_or_unclear" if present else "not_applicable",
            "evidence_strength": "weak" if is_weak else "moderate" if present else "not_supported",
            "claim_relevance": "not_claim_ready" if is_weak else "documentary_mechanism_claim" if present else "not_claim_ready",
            "reason_code": "insufficient_evidence" if is_weak else "exact_span_support" if present else "not_present_in_supplied_span",
            "supporting_quote": quote if present else "",
            "claim_boundary": "Supports only a bounded documentary statement; it does not establish wage effects or causality.",
        }
    return {
        "evidence_id": row["evidence_id"],
        "attribute_taxonomy_version": runner.TAXONOMY_VERSION,
        "attribute_ratings": ratings,
        "primary_attribute": primary,
        "overall_evidence_quality": "medium",
        "scout_priority_signal": "medium",
        "no_wage_gap_claim": True,
        "no_final_causal_claim": True,
    }


class InputContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows, cls.audit = runner.verify_inputs()

    def test_input_count_643(self):
        self.assertEqual(len(self.rows), 643)

    def test_unique_evidence_ids(self):
        self.assertEqual(len({row["evidence_id"] for row in self.rows}), 643)

    def test_authorized_id_hash(self):
        self.assertEqual(runner.id_set_sha256(row["row_document_id"] for row in self.rows), runner.AUTHORIZED_ID_HASH)

    def test_manifest_hash_matches_prior_summary(self):
        self.assertEqual(self.audit["manifest_sha256"], "5993d89931fc9e816b60e607f4acb8a467bb587a3bf28390ed1922aae65c6fb6")

    def test_required_summary_resolved_read_only(self):
        self.assertIn(self.audit["required_input_resolutions"]["category_specific_manifest_summaries.json"], {"primary_input_directory", "verified_prior_lite_relay_fallback_no_upstream_mutation"})

    def test_all_rows_exact_qualitative(self):
        self.assertTrue(all(row["source_lane"] == "qualitative_exact" for row in self.rows))

    def test_all_rows_rating_ready(self):
        self.assertTrue(all(row["primary_category"] == "gabriel_attribute_ready" and row["gabriel_claim_rating_eligible"] == "true" for row in self.rows))

    def test_all_rows_have_exact_span(self):
        self.assertTrue(all(row["direct_text_support_type"] == "exact_verified_span" and row["evidence_span_or_summary_pointer"] for row in self.rows))

    def test_non_ready_lane_rejected(self):
        rows = copy.deepcopy(self.rows); rows[0]["source_lane"] = "navigation_only"
        with self.assertRaisesRegex(RuntimeError, "non-ready lane"):
            runner.validate_input_rows(rows)

    def test_non_ready_category_rejected(self):
        rows = copy.deepcopy(self.rows); rows[0]["primary_category"] = "navigation_only"
        with self.assertRaisesRegex(RuntimeError, "non-ready primary"):
            runner.validate_input_rows(rows)

    def test_ineligible_row_rejected(self):
        rows = copy.deepcopy(self.rows); rows[0]["gabriel_claim_rating_eligible"] = "false"
        with self.assertRaisesRegex(RuntimeError, "ineligible"):
            runner.validate_input_rows(rows)

    def test_duplicate_evidence_id_rejected(self):
        rows = copy.deepcopy(self.rows); rows[1]["evidence_id"] = rows[0]["evidence_id"]
        with self.assertRaisesRegex(RuntimeError, "unique"):
            runner.validate_input_rows(rows)

    def test_missing_span_rejected(self):
        rows = copy.deepcopy(self.rows); rows[0]["evidence_span_or_summary_pointer"] = ""
        with self.assertRaisesRegex(RuntimeError, "lacks supplied"):
            runner.validate_input_rows(rows)


class TaxonomySchemaTests(unittest.TestCase):
    def test_version_is_v1_1(self):
        self.assertEqual(runner.taxonomy_payload()["attribute_taxonomy_version"], "v1.1")

    def test_exactly_14_attributes(self):
        self.assertEqual(len(runner.ATTRIBUTE_IDS), 14)

    def test_strike_attribute_is_thirteenth(self):
        self.assertEqual(runner.ATTRIBUTE_IDS[12], "strike_or_no_strike_constraint")

    def test_no_attribute_drift(self):
        self.assertEqual(runner.ATTRIBUTE_IDS[-1], "weak_or_no_claim_support")

    def test_schema_requires_all_attributes(self):
        self.assertEqual(runner.response_schema()["properties"]["attribute_ratings"]["required"], list(runner.ATTRIBUTE_IDS))

    def test_schema_requires_all_rating_fields(self):
        required = set(runner.attribute_object_schema()["required"])
        self.assertEqual(required, set(runner.RATING_FIELDS))

    def test_taxonomy_missing_attribute_rejected(self):
        payload = runner.taxonomy_payload(); payload["attributes"].pop()
        with self.assertRaisesRegex(RuntimeError, "14 attributes"):
            runner.validate_taxonomy(payload)

    def test_taxonomy_rename_rejected(self):
        payload = runner.taxonomy_payload(); payload["attributes"][0]["attribute_id"] = "renamed"
        with self.assertRaisesRegex(RuntimeError, "14 attributes"):
            runner.validate_taxonomy(payload)

    def test_taxonomy_wrong_version_rejected(self):
        payload = runner.taxonomy_payload(); payload["attribute_taxonomy_version"] = "v2"
        with self.assertRaisesRegex(RuntimeError, "v1.1"):
            runner.validate_taxonomy(payload)

    def test_strike_direction_instruction_present(self):
        text = runner.prompt_template_markdown().casefold()
        self.assertIn("do not assume direction", text)
        self.assertIn("neutral_or_unclear", text)


class StrictRatingValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.row = runner.verify_inputs()[0][0]

    def changed(self, mutator):
        value = good_rating(self.row); mutator(value); return value

    def test_good_rating_passes(self):
        self.assertEqual(runner.validate_rating(good_rating(self.row), self.row)["evidence_id"], self.row["evidence_id"])

    def test_attributes_not_mutually_exclusive(self):
        value = good_rating(self.row)
        second = "bargaining_power_signal"; quote = self.row["evidence_span_or_summary_pointer"][:8]
        value["attribute_ratings"][second].update({"attribute_present": True, "direction_of_pressure": "neutral_or_unclear", "evidence_strength": "weak", "claim_relevance": "documentary_mechanism_claim", "reason_code": "exact_span_support", "supporting_quote": quote})
        self.assertEqual(runner.validate_rating(value, self.row)["primary_attribute"], "automatic_raise_mechanism")

    def test_missing_attribute_rejected(self):
        value = good_rating(self.row); value["attribute_ratings"].pop("fiscal_constraint_signal")
        with self.assertRaisesRegex(ValueError, "attribute_set"):
            runner.validate_rating(value, self.row)

    def test_unknown_attribute_rejected(self):
        value = good_rating(self.row); value["attribute_ratings"]["unknown"] = value["attribute_ratings"].pop("fiscal_constraint_signal")
        with self.assertRaisesRegex(ValueError, "attribute_set"):
            runner.validate_rating(value, self.row)

    def test_quote_must_be_exact_substring(self):
        value = good_rating(self.row); value["attribute_ratings"]["automatic_raise_mechanism"]["supporting_quote"] = "fabricated paraphrase not in span"
        with self.assertRaisesRegex(ValueError, "not_exact_substring"):
            runner.validate_rating(value, self.row)

    def test_positive_quote_cannot_be_empty(self):
        value = good_rating(self.row); value["attribute_ratings"]["automatic_raise_mechanism"]["supporting_quote"] = ""
        with self.assertRaisesRegex(ValueError, "not_exact_substring"):
            runner.validate_rating(value, self.row)

    def test_positive_reason_code_required(self):
        value = good_rating(self.row); value["attribute_ratings"]["automatic_raise_mechanism"]["reason_code"] = ""
        with self.assertRaisesRegex(ValueError, "reason_code"):
            runner.validate_rating(value, self.row)

    def test_absent_attribute_quote_rejected(self):
        value = good_rating(self.row); value["attribute_ratings"]["fiscal_constraint_signal"]["supporting_quote"] = self.row["evidence_span_or_summary_pointer"][:4]
        with self.assertRaisesRegex(ValueError, "absent_attribute_controls"):
            runner.validate_rating(value, self.row)

    def test_absent_attribute_strength_rejected(self):
        value = good_rating(self.row); value["attribute_ratings"]["fiscal_constraint_signal"]["evidence_strength"] = "weak"
        with self.assertRaisesRegex(ValueError, "absent_attribute_controls"):
            runner.validate_rating(value, self.row)

    def test_weak_attribute_overuse_rejected(self):
        value = good_rating(self.row); quote = self.row["evidence_span_or_summary_pointer"][:6]
        value["attribute_ratings"]["weak_or_no_claim_support"].update({"attribute_present": True, "direction_of_pressure": "neutral_or_unclear", "evidence_strength": "weak", "claim_relevance": "not_claim_ready", "reason_code": "insufficient_evidence", "supporting_quote": quote})
        with self.assertRaisesRegex(ValueError, "weak_attribute_overused"):
            runner.validate_rating(value, self.row)

    def test_weak_only_rating_passes(self):
        value = good_rating(self.row, primary="weak_or_no_claim_support")
        self.assertEqual(runner.validate_rating(value, self.row)["primary_attribute"], "weak_or_no_claim_support")

    def test_weak_attribute_must_remain_not_claim_ready(self):
        value = good_rating(self.row, primary="weak_or_no_claim_support")
        value["attribute_ratings"]["weak_or_no_claim_support"]["claim_relevance"] = "documentary_mechanism_claim"
        with self.assertRaisesRegex(ValueError, "weak_attribute_controls_invalid"):
            runner.validate_rating(value, self.row)

    def test_weak_attribute_accepts_not_supported_not_applicable(self):
        value = good_rating(self.row, primary="weak_or_no_claim_support")
        weak = value["attribute_ratings"]["weak_or_no_claim_support"]
        weak["evidence_strength"] = "not_supported"
        weak["direction_of_pressure"] = "not_applicable"
        self.assertEqual(runner.validate_rating(value, self.row)["primary_attribute"], "weak_or_no_claim_support")

    def test_primary_must_be_present(self):
        value = good_rating(self.row); value["primary_attribute"] = "fiscal_constraint_signal"
        with self.assertRaisesRegex(ValueError, "primary_attribute_not_present"):
            runner.validate_rating(value, self.row)

    def test_wrong_evidence_id_rejected(self):
        value = good_rating(self.row); value["evidence_id"] = "wrong"
        with self.assertRaisesRegex(ValueError, "identity_or_version"):
            runner.validate_rating(value, self.row)

    def test_wrong_taxonomy_version_rejected(self):
        value = good_rating(self.row); value["attribute_taxonomy_version"] = "v1"
        with self.assertRaisesRegex(ValueError, "identity_or_version"):
            runner.validate_rating(value, self.row)

    def test_wage_gap_permission_rejected(self):
        value = good_rating(self.row); value["no_wage_gap_claim"] = False
        with self.assertRaisesRegex(ValueError, "boundary_booleans"):
            runner.validate_rating(value, self.row)

    def test_final_causal_permission_rejected(self):
        value = good_rating(self.row); value["no_final_causal_claim"] = False
        with self.assertRaisesRegex(ValueError, "boundary_booleans"):
            runner.validate_rating(value, self.row)

    def test_final_causal_language_rejected(self):
        value = good_rating(self.row); value["attribute_ratings"]["automatic_raise_mechanism"]["claim_boundary"] = "This caused the wage disparity."
        with self.assertRaisesRegex(ValueError, "forbidden_final_claim"):
            runner.validate_rating(value, self.row)

    def test_regression_claim_language_rejected(self):
        value = good_rating(self.row); value["attribute_ratings"]["automatic_raise_mechanism"]["claim_boundary"] = "Regression shows a causal effect."
        with self.assertRaisesRegex(ValueError, "forbidden_final_claim"):
            runner.validate_rating(value, self.row)

    def test_flatten_round_trip(self):
        parsed = good_rating(self.row)
        result = runner.LiveResult("req", "success", "", 1.0, 2, 3, 5, "", "")
        flat = runner.flatten_rating(parsed, self.row, result, 1)
        self.assertEqual(runner.unflatten_rating(flat), parsed)


class StageAndPersistenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows, cls.audit = runner.verify_inputs()

    def test_dry_manifest_has_643_rows_and_no_payloads(self):
        selected, _ = runner.select_preflight(self.rows)
        rows = runner.dry_manifest(self.rows, selected)
        self.assertEqual(len(rows), 643)
        self.assertTrue(all(row["raw_prompt_saved"] == "false" and row["raw_response_saved"] == "false" for row in rows))

    def test_dry_manifest_does_not_contain_evidence_text(self):
        selected, _ = runner.select_preflight(self.rows)
        first = runner.dry_manifest(self.rows, selected)[0]
        self.assertNotIn("evidence_span_or_summary_pointer", first)

    def test_preflight_has_difficult_row(self):
        selected, coverage = runner.select_preflight(self.rows)
        self.assertTrue(coverage["difficult_weak"]["present_in_manifest"])
        self.assertGreaterEqual(len(selected), 1)

    def test_no_strike_case_is_not_fabricated(self):
        _, coverage = runner.select_preflight(self.rows)
        strike = coverage["strike_no_strike"]
        self.assertEqual(bool(strike["selected_evidence_id"]), strike["present_in_manifest"])

    def test_output_guard_rejects_tmp(self):
        with self.assertRaisesRegex(RuntimeError, "docs/analysis"):
            runner.output_guard(runner.ROOT / "tmp/not_allowed", resume=False)

    def test_existing_output_requires_resume(self):
        with tempfile.TemporaryDirectory(dir=runner.ROOT / "docs/analysis") as name:
            with self.assertRaises(FileExistsError):
                runner.output_guard(Path(name), resume=False)

    def test_contract_files_have_no_raw_prompt_or_response(self):
        with tempfile.TemporaryDirectory(dir=runner.ROOT / "docs/analysis") as name:
            path = Path(name); runner.write_contract_files(path)
            names = {item.name for item in path.iterdir()}
            self.assertFalse(any("raw_prompt" in name or "raw_response" in name for name in names))

    def test_request_metadata_excludes_response_text(self):
        result = runner.LiveResult("req", "success", "SECRET_RESPONSE", 1.0, 1, 2, 3, "", "")
        meta = runner.request_metadata(self.rows[0], "preflight", 1, result, True, 100, "model")
        self.assertNotIn("response_text", meta)
        self.assertEqual(meta["raw_response_saved"], "false")

    def test_fake_model_call_produces_valid_parsed_only_output(self):
        row = self.rows[0]
        payload = json.dumps(good_rating(row))
        def fake(items, **kwargs):
            return [runner.LiveResult("req", "success", payload, 0.1, 10, 20, 30, "", "") for _ in items]
        valid, quarantines, metadata = runner.run_rating_calls([row], stage="preflight", key="not_logged", model="test", timeout=1, parallel=1, max_attempts=1, caller=fake)
        self.assertEqual(len(valid), 1)
        self.assertEqual(quarantines, [])
        self.assertNotIn("response_text", metadata[0])

    def test_fake_invalid_output_is_quarantined(self):
        row = self.rows[0]
        def fake(items, **kwargs):
            return [runner.LiveResult("req", "success", "{}", 0.1, 10, 2, 12, "", "") for _ in items]
        valid, quarantines, metadata = runner.run_rating_calls([row], stage="preflight", key="not_logged", model="test", timeout=1, parallel=1, max_attempts=2, caller=fake)
        self.assertEqual(valid, [])
        self.assertEqual(len(quarantines), 1)
        self.assertEqual(len(metadata), 2)

    def test_checkpoint_unknown_id_rejected(self):
        with tempfile.TemporaryDirectory(dir=runner.ROOT / "docs/analysis") as name:
            path = Path(name) / "checkpoint.csv"
            row = {field: "" for field in runner.RATING_OUTPUT_FIELDS}; row["evidence_id"] = "unknown"
            runner.write_csv(path, runner.RATING_OUTPUT_FIELDS, [row])
            with self.assertRaisesRegex(RuntimeError, "unknown or duplicate"):
                runner.load_checkpoint(path, {self.rows[0]["evidence_id"]: self.rows[0]})

    def test_reconciliation_underflow_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "reconcile"):
            runner.validate_final_outputs([], [], self.rows)

    def test_reconciliation_overlap_rejected(self):
        parsed = good_rating(self.rows[0]); result = runner.LiveResult("r", "success", "", 1, 0, 0, 0, "", "")
        flat = runner.flatten_rating(parsed, self.rows[0], result, 1)
        q = {field: "" for field in runner.QUARANTINE_FIELDS}; q["evidence_id"] = self.rows[0]["evidence_id"]
        with self.assertRaisesRegex(RuntimeError, "reconcile"):
            runner.validate_final_outputs([flat], [q], self.rows)

    def test_completed_requires_all_outputs(self):
        with tempfile.TemporaryDirectory(dir=runner.ROOT / "docs/analysis") as name:
            self.assertFalse(runner.completed(Path(name)))

    def test_future_prompt_keeps_phase_boundaries(self):
        text = runner.prompt_template_markdown()
        for phrase in ("Do not calculate statistics", "Do not state final causal claims", "Raw prompts and raw responses must not be persisted"):
            self.assertIn(phrase, text)

    def test_global_readiness_never_true_in_contract(self):
        self.assertFalse(runner.taxonomy_payload()["global_analysis_readiness"])


class CompletedOutputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out = runner.DEFAULT_OUTPUT_DIR
        cls.decision = runner.read_json(cls.out / "gabriel_claim_rating_643_decision.json")

    def test_completed_outputs_reconcile(self):
        self.assertEqual(self.decision["valid_rating_rows"] + self.decision["quarantine_rows"], 643)

    def test_completed_decision_with_quarantine(self):
        self.assertEqual(self.decision["decision"], "gabriel_claim_rating_643_completed_with_quarantine")

    def test_summary_review_not_allowed_with_quarantine(self):
        self.assertFalse(self.decision["summary_review_allowed"])

    def test_repair_prompt_selected(self):
        self.assertTrue((self.out / "next_gabriel_claim_rating_repair_prompt.md").is_file())
        self.assertFalse((self.out / "next_gabriel_claim_rating_summary_review_prompt.md").is_file())

    def test_repair_prompt_is_quarantine_bounded(self):
        text = (self.out / "next_gabriel_claim_rating_repair_prompt.md").read_text(encoding="utf-8")
        self.assertIn("Repair only the 35 explicitly quarantined IDs", text)
        self.assertIn("Do not compute cross-row", text)
        self.assertIn("Do not make final causal claims", text)

    def test_rating_output_has_no_raw_payload_columns(self):
        with (self.out / "gabriel_claim_oriented_attribute_ratings_643.csv").open(newline="", encoding="utf-8") as handle:
            fields = csv.DictReader(handle).fieldnames or []
        self.assertFalse({"raw_prompt", "raw_response", "prompt", "response"}.intersection(fields))

    def test_dashboard_status_reconciles(self):
        completed, decision = dashboard.gabriel_claim_rating_643_status()
        self.assertTrue(completed)
        self.assertEqual(decision["valid_rating_rows"], 608)
        self.assertFalse(decision["global_analysis_readiness"])

    def test_upstream_descendant_dashboard_validator_accepts_rating_phase(self):
        calibration = runner.read_json(runner.ROOT / "docs/dashboard/data/text_table_calibration_status_summary.json")
        readiness = runner.read_json(runner.ROOT / "docs/dashboard/data/analysis_readiness.json")
        registry_review.validate_dashboard_state(calibration, readiness)

    def test_all_invariants_pass(self):
        payload = runner.read_json(self.out / "gabriel_claim_rating_643_invariant_checks.json")
        self.assertTrue(payload["all_invariants_passed"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
