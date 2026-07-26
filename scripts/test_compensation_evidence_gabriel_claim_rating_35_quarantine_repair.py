#!/usr/bin/env python3
"""Adversarial tests for the bounded 35-row GABRIEL quarantine repair."""

from __future__ import annotations

import copy
import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import run_compensation_evidence_gabriel_claim_rating_35_quarantine_repair as runner
import run_compensation_evidence_gabriel_claim_rating_643 as base
import build_dashboard_data as dashboard


def good_rating(row: dict[str, str], *, weak: bool = False) -> dict:
    ratings = {}
    for attribute in base.ATTRIBUTE_IDS:
        ratings[attribute] = {
            "attribute_present": False,
            "direction_of_pressure": "not_applicable",
            "evidence_strength": "not_supported",
            "claim_relevance": "not_claim_ready",
            "reason_code": f"no_{attribute}"[:80],
            "supporting_quote": "",
            "claim_boundary": "The supplied span does not support this attribute.",
        }
    span = row["evidence_span_or_summary_pointer"]
    quote = span[: min(80, len(span))]
    primary = "weak_or_no_claim_support" if weak else "automatic_raise_mechanism"
    ratings[primary] = {
        "attribute_present": True,
        "direction_of_pressure": "not_applicable" if weak else "neutral_or_unclear",
        "evidence_strength": "weak" if weak else "moderate",
        "claim_relevance": "not_claim_ready" if weak else "documentary_mechanism_claim",
        "reason_code": "insufficient_exact_span_support" if weak else "exact_span_support",
        "supporting_quote": quote,
        "claim_boundary": "This supports only a bounded documentary reading, not a wage effect or causal conclusion.",
    }
    return {
        "evidence_id": row["evidence_id"],
        "attribute_taxonomy_version": "v1.1",
        "attribute_ratings": ratings,
        "primary_attribute": primary,
        "overall_evidence_quality": "low" if weak else "medium",
        "scout_priority_signal": "medium",
        "no_wage_gap_claim": True,
        "no_final_causal_claim": True,
    }


class InputScopeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest, cls.valid, cls.quarantine, cls.audit = runner.verify_inputs()
        cls.manifest_map = {row["evidence_id"]: row for row in cls.manifest}
        cls.repair_rows = [cls.manifest_map[row["evidence_id"]] for row in cls.quarantine]

    def test_manifest_count(self):
        self.assertEqual(len(self.manifest), 643)

    def test_original_valid_count(self):
        self.assertEqual(len(self.valid), 608)

    def test_quarantine_count(self):
        self.assertEqual(len(self.quarantine), 35)

    def test_valid_file_hash(self):
        self.assertEqual(runner.sha256(runner.VALID_PATH), runner.EXPECTED_VALID_FILE_SHA256)

    def test_quarantine_file_hash(self):
        self.assertEqual(runner.sha256(runner.QUARANTINE_PATH), runner.EXPECTED_QUARANTINE_FILE_SHA256)

    def test_manifest_hash(self):
        self.assertEqual(runner.sha256(runner.MANIFEST_PATH), runner.EXPECTED_MANIFEST_SHA256)

    def test_quarantine_id_hash(self):
        self.assertEqual(runner.id_set_sha256(row["evidence_id"] for row in self.quarantine), runner.EXPECTED_QUARANTINE_ID_HASH)

    def test_valid_id_hash(self):
        self.assertEqual(runner.id_set_sha256(row["evidence_id"] for row in self.valid), runner.EXPECTED_ORIGINAL_VALID_ID_HASH)

    def test_valid_and_quarantine_disjoint(self):
        self.assertFalse({row["evidence_id"] for row in self.valid} & {row["evidence_id"] for row in self.quarantine})

    def test_valid_and_quarantine_cover_manifest(self):
        observed = {row["evidence_id"] for row in self.valid} | {row["evidence_id"] for row in self.quarantine}
        self.assertEqual(observed, set(self.manifest_map))

    def test_original_valid_rows_revalidate(self):
        for row in self.valid:
            base.validate_rating(base.unflatten_rating(row), self.manifest_map[row["evidence_id"]])

    def test_original_valid_canonical_hash_recorded(self):
        observed = runner.canonical_rows_sha256(self.valid, base.RATING_OUTPUT_FIELDS)
        self.assertEqual(observed, self.audit["original_valid_rows_canonical_sha256"])

    def test_original_valid_mutation_changes_hash(self):
        mutated = copy.deepcopy(self.valid)
        mutated[0]["primary_attribute"] = "weak_or_no_claim_support"
        self.assertNotEqual(
            runner.canonical_rows_sha256(mutated, base.RATING_OUTPUT_FIELDS),
            self.audit["original_valid_rows_canonical_sha256"],
        )

    def test_four_expected_failure_classes(self):
        counts = {}
        for row in self.quarantine:
            counts[row["error_code"]] = counts.get(row["error_code"], 0) + 1
        self.assertEqual(counts, {
            "weak_attribute_controls_invalid": 15,
            "supporting_quote_not_exact_substring": 18,
            "positive_attribute_has_negative_controls": 1,
            "forbidden_final_claim_language": 1,
        })

    def test_quarantine_summary_fallback_is_read_only(self):
        self.assertIn(
            self.audit["input_resolutions"]["quarantine_summary.json"],
            {"primary_input_directory", "verified_prior_lite_relay_fallback_no_upstream_mutation"},
        )


class DryRunAndDiagnosticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out = runner.DEFAULT_OUTPUT_DIR
        cls.summary = base.read_json(cls.out / "gabriel_claim_rating_35_quarantine_repair_summary.json")
        cls.manifest = base.read_csv(cls.out / "gabriel_claim_rating_35_quarantine_repair_manifest.csv")
        cls.diagnostics = base.read_csv(cls.out / "gabriel_claim_rating_35_quarantine_diagnostics.csv")

    def test_dry_run_scope_35(self):
        self.assertEqual(self.summary["repair_input_rows"], 35)

    def test_dry_run_api_not_called(self):
        self.assertFalse(self.summary.get("dry_run_gabriel_api_called", self.summary.get("gabriel_api_called")))

    def test_deterministic_repairs_zero(self):
        self.assertEqual(self.summary["deterministically_repairable_rows"], 0)

    def test_bounded_retry_rows_35(self):
        self.assertEqual(self.summary["bounded_model_retry_required_rows"], 35)

    def test_manifest_rows_35(self):
        self.assertEqual(len(self.manifest), 35)

    def test_diagnostic_rows_35(self):
        self.assertEqual(len(self.diagnostics), 35)

    def test_manifest_id_hash(self):
        self.assertEqual(runner.id_set_sha256(row["evidence_id"] for row in self.manifest), runner.EXPECTED_QUARANTINE_ID_HASH)

    def test_manifest_contains_no_span_text(self):
        self.assertNotIn("evidence_span", self.manifest[0])

    def test_diagnostics_contain_no_span_text(self):
        self.assertNotIn("evidence_span_or_summary_pointer", self.diagnostics[0])

    def test_no_safe_deterministic_edit_claimed(self):
        self.assertTrue(all(row["safe_deterministic_edit_available"] == "false" for row in self.diagnostics))

    def test_no_invalid_payload_claimed(self):
        self.assertTrue(all(row["invalid_rating_payload_persisted"] == "false" for row in self.diagnostics))

    def test_exact_span_available_for_all(self):
        self.assertTrue(all(row["evidence_span_available"] == "true" for row in self.diagnostics))

    def test_no_outside_scope_evidence(self):
        self.assertTrue(all(row["outside_scope_evidence_used"] == "false" for row in self.diagnostics))

    def test_no_raw_payload_persistence(self):
        self.assertTrue(all(row["raw_prompt_saved"] == "false" and row["raw_response_saved"] == "false" for row in self.manifest))

    def test_global_readiness_false(self):
        self.assertFalse(self.summary["global_analysis_readiness"])


class PromptAndPreflightTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        manifest, _, quarantine, _ = runner.verify_inputs()
        row_map = {row["evidence_id"]: row for row in manifest}
        cls.quarantine = quarantine
        cls.repair_rows = [row_map[row["evidence_id"]] for row in quarantine]
        cls.errors = {row["evidence_id"]: row["error_code"] for row in quarantine}

    def test_preflight_selects_four(self):
        selected, _ = runner.select_preflight(self.repair_rows, self.quarantine)
        self.assertEqual(len(selected), 4)

    def test_preflight_covers_all_failure_classes(self):
        _, coverage = runner.select_preflight(self.repair_rows, self.quarantine)
        self.assertEqual(set(coverage), set(self.errors.values()))

    def test_prompt_has_all_14_attribute_names(self):
        row = self.repair_rows[0]
        prompt = runner.build_repair_prompt(row, self.errors[row["evidence_id"]])
        self.assertTrue(all(attribute in prompt for attribute in base.ATTRIBUTE_IDS))

    def test_prompt_requires_exact_substring(self):
        row = self.repair_rows[0]
        prompt = runner.build_repair_prompt(row, self.errors[row["evidence_id"]])
        self.assertIn("one contiguous exact substring", prompt)

    def test_prompt_requires_negative_controls(self):
        row = self.repair_rows[0]
        prompt = runner.build_repair_prompt(row, self.errors[row["evidence_id"]])
        self.assertIn("attribute_present=false", prompt)
        self.assertIn("evidence_strength=not_supported", prompt)

    def test_prompt_preserves_weak_semantics(self):
        row = self.repair_rows[0]
        prompt = runner.build_repair_prompt(row, self.errors[row["evidence_id"]])
        self.assertIn("weak_or_no_claim_support is present, no other attribute may be present", prompt)

    def test_prompt_forbids_final_claim(self):
        row = self.repair_rows[0]
        prompt = runner.build_repair_prompt(row, self.errors[row["evidence_id"]])
        self.assertIn("final causal conclusion", prompt)

    def test_prompt_does_not_request_outside_evidence(self):
        row = self.repair_rows[0]
        prompt = runner.build_repair_prompt(row, self.errors[row["evidence_id"]])
        self.assertIn("bounded to the supplied exact span", prompt)

    def test_fake_valid_call_passes(self):
        row = self.repair_rows[0]
        parsed = good_rating(row, weak=True)

        def caller(items, **_kwargs):
            return [base.LiveResult("fake", "success", json.dumps(parsed), 0.1, 1, 1, 2, "", "")]

        valid, remaining, metadata = runner.run_calls(
            [row], self.errors, stage="test", key="redacted", model="test-model",
            timeout=1, parallel=1, max_attempts=1, caller=caller,
        )
        self.assertEqual(len(valid), 1)
        self.assertFalse(remaining)
        self.assertEqual(metadata[0]["schema_valid"], "true")

    def test_fake_paraphrased_quote_quarantined(self):
        row = self.repair_rows[0]
        parsed = good_rating(row)
        parsed["attribute_ratings"]["automatic_raise_mechanism"]["supporting_quote"] = "not an exact quote"

        def caller(items, **_kwargs):
            return [base.LiveResult("fake", "success", json.dumps(parsed), 0.1, 1, 1, 2, "", "")]

        valid, remaining, _ = runner.run_calls(
            [row], self.errors, stage="test", key="redacted", model="test-model",
            timeout=1, parallel=1, max_attempts=1, caller=caller,
        )
        self.assertFalse(valid)
        self.assertEqual(remaining[0]["error_code"], "supporting_quote_not_exact_substring")

    def test_fake_weak_control_error_quarantined(self):
        row = self.repair_rows[0]
        parsed = good_rating(row, weak=True)
        parsed["attribute_ratings"]["weak_or_no_claim_support"]["claim_relevance"] = "documentary_mechanism_claim"

        def caller(items, **_kwargs):
            return [base.LiveResult("fake", "success", json.dumps(parsed), 0.1, 1, 1, 2, "", "")]

        valid, remaining, _ = runner.run_calls(
            [row], self.errors, stage="test", key="redacted", model="test-model",
            timeout=1, parallel=1, max_attempts=1, caller=caller,
        )
        self.assertFalse(valid)
        self.assertEqual(remaining[0]["error_code"], "weak_attribute_controls_invalid")

    def test_fake_final_claim_quarantined(self):
        row = self.repair_rows[0]
        parsed = good_rating(row)
        parsed["attribute_ratings"]["automatic_raise_mechanism"]["claim_boundary"] = "This caused the wage increase."

        def caller(items, **_kwargs):
            return [base.LiveResult("fake", "success", json.dumps(parsed), 0.1, 1, 1, 2, "", "")]

        valid, remaining, _ = runner.run_calls(
            [row], self.errors, stage="test", key="redacted", model="test-model",
            timeout=1, parallel=1, max_attempts=1, caller=caller,
        )
        self.assertFalse(valid)
        self.assertEqual(remaining[0]["error_code"], "forbidden_final_claim_language")

    def test_request_metadata_has_no_payload(self):
        self.assertNotIn("prompt", base.REQUEST_FIELDS)
        self.assertNotIn("response", base.REQUEST_FIELDS)


class GuardrailTests(unittest.TestCase):
    def test_output_guard_rejects_tmp(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(RuntimeError):
                runner.output_guard(Path(directory) / "out", resume=False)

    def test_existing_output_requires_resume(self):
        with self.assertRaises(FileExistsError):
            runner.output_guard(runner.DEFAULT_OUTPUT_DIR, resume=False)

    def test_partial_output_not_complete(self):
        with tempfile.TemporaryDirectory(dir=runner.ANALYSIS_ROOT) as directory:
            self.assertFalse(runner.completed(Path(directory)))

    def test_taxonomy_stays_v1_1(self):
        self.assertEqual(base.TAXONOMY_VERSION, "v1.1")

    def test_exactly_14_attributes(self):
        self.assertEqual(len(base.ATTRIBUTE_IDS), 14)

    def test_strike_attribute_preserved(self):
        self.assertIn("strike_or_no_strike_constraint", base.ATTRIBUTE_IDS)

    def test_no_new_attribute_added(self):
        self.assertEqual(base.ATTRIBUTE_IDS[-1], "weak_or_no_claim_support")

    def test_repair_script_does_not_write_upstream(self):
        source = Path(runner.__file__).read_text(encoding="utf-8")
        self.assertNotIn("VALID_PATH.write", source)
        self.assertNotIn("QUARANTINE_PATH.write", source)
        self.assertNotIn("MANIFEST_PATH.write", source)

    def test_future_prompt_or_pending_output(self):
        if runner.completed(runner.DEFAULT_OUTPUT_DIR):
            decision = base.read_json(runner.DEFAULT_OUTPUT_DIR / "gabriel_claim_rating_35_quarantine_repair_decision.json")
            self.assertTrue(decision["summary_review_allowed"])
            self.assertTrue((runner.DEFAULT_OUTPUT_DIR / "next_gabriel_claim_rating_summary_review_prompt.md").is_file())


class CompletedOutputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not runner.completed(runner.DEFAULT_OUTPUT_DIR):
            raise unittest.SkipTest("live repair outputs not completed yet")
        cls.out = runner.DEFAULT_OUTPUT_DIR
        cls.decision = base.read_json(cls.out / "gabriel_claim_rating_35_quarantine_repair_decision.json")
        cls.ratings = base.read_csv(cls.out / "gabriel_claim_oriented_attribute_ratings_643_repaired.csv")
        cls.remaining = base.read_csv(cls.out / "gabriel_claim_oriented_attribute_rating_remaining_quarantine.csv")
        cls.invariants = base.read_json(cls.out / "gabriel_claim_rating_35_quarantine_repair_invariant_checks.json")

    def test_total_reconciles(self):
        self.assertEqual(len(self.ratings) + len(self.remaining), 643)

    def test_original_valid_unchanged(self):
        self.assertEqual(self.decision["original_valid_rows_unchanged"], 608)

    def test_scope_is_35(self):
        self.assertEqual(self.decision["repair_input_rows"], 35)

    def test_all_invariants_pass(self):
        self.assertTrue(self.invariants["all_invariants_passed"])

    def test_global_readiness_false(self):
        self.assertFalse(self.decision["global_analysis_readiness"])

    def test_no_cross_row_statistics(self):
        self.assertFalse(self.decision["cross_row_statistics_computed"])

    def test_no_raw_payloads(self):
        names = {path.name.lower() for path in self.out.iterdir()}
        self.assertFalse(any("raw_prompt" in name or "raw_response" in name for name in names))

    def test_summary_review_requires_full_validity(self):
        if self.decision["decision"] == "gabriel_claim_rating_643_repaired_summary_review_allowed":
            self.assertEqual(len(self.ratings), 643)
            self.assertFalse(self.remaining)

    def test_remaining_quarantine_allows_exclusion_scoped_review(self):
        if self.remaining:
            self.assertEqual(self.decision["decision"], "gabriel_claim_rating_643_repaired_with_remaining_quarantine")
            self.assertTrue(self.decision["summary_review_allowed"])
            self.assertIn("explicit_quarantine_exclusions", self.decision["summary_review_scope"])

    def test_dashboard_repair_status_reconciles(self):
        completed, decision = dashboard.gabriel_claim_rating_35_repair_status()
        self.assertTrue(completed)
        self.assertEqual(decision["total_valid_rows"], len(self.ratings))
        self.assertEqual(decision["remaining_quarantine_rows"], len(self.remaining))

    def test_future_prompt_preserves_phase_boundaries(self):
        text = (self.out / "next_gabriel_claim_rating_summary_review_prompt.md").read_text(encoding="utf-8")
        required = (
            "Do not call GABRIEL/API or any model",
            "Do not calculate wage gaps",
            "run regressions",
            "final causal claims",
            "Keep global analysis readiness false",
            "GABRIEL rating is not causal proof",
        )
        self.assertTrue(all(phrase.casefold() in text.casefold() for phrase in required))

    def test_request_metadata_has_no_payload_columns(self):
        rows = base.read_csv(self.out / "gabriel_claim_rating_35_repair_request_metadata.csv")
        self.assertTrue(rows)
        self.assertFalse({"prompt", "response", "raw_prompt", "raw_response"}.intersection(rows[0]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
