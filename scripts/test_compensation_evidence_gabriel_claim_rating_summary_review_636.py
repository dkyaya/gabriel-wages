#!/usr/bin/env python3
"""Adversarial tests for the bounded 636-row GABRIEL rating summary review."""

from __future__ import annotations

import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import build_dashboard_data as dashboard
import run_compensation_evidence_gabriel_claim_rating_summary_review_636 as runner
import run_compensation_evidence_gabriel_claim_rating_643 as rating


class InputIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.valid, cls.excluded, cls.manifest, cls.audit = runner.verify_inputs()
        cls.valid_ids = {row["evidence_id"] for row in cls.valid}
        cls.excluded_ids = {row["evidence_id"] for row in cls.excluded}

    def test_valid_count_exact(self): self.assertEqual(len(self.valid), 636)
    def test_excluded_count_exact(self): self.assertEqual(len(self.excluded), 7)
    def test_total_reconciles(self): self.assertEqual(len(self.valid) + len(self.excluded), 643)
    def test_manifest_count(self): self.assertEqual(len(self.manifest), 643)
    def test_valid_ids_unique(self): self.assertEqual(len(self.valid_ids), 636)
    def test_excluded_ids_unique(self): self.assertEqual(len(self.excluded_ids), 7)
    def test_sets_disjoint(self): self.assertFalse(self.valid_ids & self.excluded_ids)
    def test_sets_cover_authorized(self): self.assertEqual(self.valid_ids | self.excluded_ids, {row["evidence_id"] for row in self.manifest})
    def test_valid_file_hash(self): self.assertEqual(runner.sha256(runner.VALID_PATH), runner.EXPECTED_VALID_SHA256)
    def test_excluded_file_hash(self): self.assertEqual(runner.sha256(runner.QUARANTINE_PATH), runner.EXPECTED_QUARANTINE_SHA256)
    def test_manifest_hash(self): self.assertEqual(runner.sha256(runner.MANIFEST_PATH), runner.EXPECTED_MANIFEST_SHA256)
    def test_quarantine_summary_fallback_hash(self):
        paths, _ = runner.resolve_inputs()
        self.assertEqual(runner.sha256(paths["remaining_quarantine_summary.json"]), runner.EXPECTED_QUARANTINE_SUMMARY_SHA256)
    def test_fallback_is_read_only_resolution(self):
        _, resolutions = runner.resolve_inputs()
        self.assertIn(resolutions["remaining_quarantine_summary.json"], {"primary_input_directory", "verified_prior_lite_relay_fallback_no_upstream_mutation"})
    def test_predecessor_authorizes_summary(self):
        decision = rating.read_json(runner.INPUT_DIR / "gabriel_claim_rating_35_quarantine_repair_decision.json")
        self.assertTrue(decision["summary_review_allowed"])
    def test_valid_rows_revalidate(self):
        manifest = {row["evidence_id"]: row for row in self.manifest}
        for row in self.valid:
            rating.validate_rating(rating.unflatten_rating(row), manifest[row["evidence_id"]])
    def test_all_valid_rows_v1_1(self): self.assertTrue(all(row["attribute_taxonomy_version"] == "v1.1" for row in self.valid))
    def test_no_raw_payload_flags_in_exclusions(self):
        self.assertTrue(all(row["raw_prompt_saved"] == "false" and row["raw_response_saved"] == "false" for row in self.excluded))
    def test_remaining_error_counts(self):
        counts = {}
        for row in self.excluded: counts[row["error_code"]] = counts.get(row["error_code"], 0) + 1
        self.assertEqual(counts, {"supporting_quote_not_exact_substring": 4, "no_supported_attribute_without_weak_marker": 2, "response_identity_or_version_invalid": 1})


class SummaryContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.valid, cls.excluded, cls.manifest, _ = runner.verify_inputs()
        cls.summary = runner.aggregate(cls.valid)
        cls.out = runner.DEFAULT_OUTPUT_DIR

    def test_fourteen_attributes(self): self.assertEqual(len(self.summary["presence"]), 14)
    def test_attribute_order_matches_v1_1(self): self.assertEqual([row["attribute_id"] for row in self.summary["presence"]], list(rating.ATTRIBUTE_IDS))
    def test_positive_cells_reconcile(self): self.assertEqual(self.summary["positive_attribute_cells"], 722)
    def test_presence_rows_reconcile(self):
        self.assertTrue(all(int(row["present_count"]) + int(row["absent_count"]) == 636 for row in self.summary["presence"]))
    def test_implementation_count(self): self.assertEqual(self.summary["crosswalk"]["implementation_or_retroactivity_advantage"]["present_count"], 171)
    def test_automatic_raise_count(self): self.assertEqual(self.summary["crosswalk"]["automatic_raise_mechanism"]["present_count"], 109)
    def test_base_wage_count(self): self.assertEqual(self.summary["crosswalk"]["base_wage_direct_value"]["present_count"], 100)
    def test_non_base_count(self): self.assertEqual(self.summary["crosswalk"]["non_base_compensation_signal"]["present_count"], 76)
    def test_safety_advantage_zero(self): self.assertEqual(self.summary["crosswalk"]["safety_advantage_signal"]["present_count"], 0)
    def test_non_safety_constraint_zero(self): self.assertEqual(self.summary["crosswalk"]["non_safety_constraint_signal"]["present_count"], 0)
    def test_direction_present_counts_total_722(self): self.assertEqual(sum(int(row["count_present_attribute_cells"]) for row in self.summary["direction"]), 722)
    def test_strength_present_counts_total_722(self): self.assertEqual(sum(int(row["count_present_attribute_cells"]) for row in self.summary["strength"]), 722)
    def test_relevance_present_counts_total_722(self): self.assertEqual(sum(int(row["count_present_attribute_cells"]) for row in self.summary["relevance"]), 722)
    def test_scout_priority_rows_total_636(self): self.assertEqual(sum(int(row["row_count"]) for row in self.summary["scout"]), 636)
    def test_claim_registry_has_thirteen_substantive_attributes(self): self.assertEqual(len(runner.claim_registry(self.summary)), 13)
    def test_zero_support_claims_require_more_data(self):
        rows = {row["attribute_id"]: row for row in runner.claim_registry(self.summary)}
        self.assertEqual(rows["safety_advantage_signal"]["review_status"], "more_data_required")
    def test_claim_boundaries_forbid_effect_inference(self):
        self.assertTrue(all("no actual wage effect" in row["claim_boundary"] for row in runner.claim_registry(self.summary)))
    def test_valid_manifest_contains_no_span_or_quote(self):
        rows = rating.read_csv(self.out / "gabriel_claim_rating_summary_review_valid_636_manifest.csv")
        self.assertNotIn("supporting_quote", rows[0]); self.assertNotIn("evidence_span", rows[0])
    def test_excluded_rows_never_marked_valid(self):
        rows = rating.read_csv(self.out / "gabriel_claim_rating_summary_review_excluded_7_manifest.csv")
        self.assertTrue(all(row["included_in_valid_summary"] == "false" for row in rows))


class GuardrailAndNarrativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.out = runner.DEFAULT_OUTPUT_DIR

    def test_decision_exact(self):
        self.assertEqual(rating.read_json(self.out / "gabriel_claim_rating_summary_review_636_decision.json")["decision"], runner.DECISION)
    def test_global_readiness_false(self): self.assertFalse(rating.read_json(self.out / "gabriel_claim_rating_summary_review_636_decision.json")["global_analysis_readiness"])
    def test_model_calls_false(self): self.assertFalse(rating.read_json(self.out / "gabriel_claim_rating_summary_review_636_decision.json")["gabriel_api_or_model_called"])
    def test_quantitative_lane_not_analyzed(self): self.assertEqual(rating.read_json(self.out / "gabriel_claim_rating_summary_review_636_decision.json")["quantitative_direct_text_rows_preserved_for_later_triage"], 862)
    def test_invariants_pass(self): self.assertTrue(rating.read_json(self.out / "gabriel_claim_rating_summary_review_636_invariant_checks.json")["all_invariants_passed"])
    def test_stress_count(self): self.assertEqual(rating.read_json(self.out / "gabriel_claim_rating_summary_review_636_regression_test_inventory.json")["failure_mode_count"], 41)
    def test_required_outputs_complete(self): self.assertTrue(runner.completed(self.out))
    def test_partial_output_fails_closed(self):
        with tempfile.TemporaryDirectory(dir=runner.ANALYSIS_ROOT) as tmp:
            path = Path(tmp); (path / "partial.txt").write_text("partial")
            with self.assertRaisesRegex(RuntimeError, "partial outputs"):
                runner.output_guard(path, True)
    def test_non_analysis_output_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(RuntimeError, "under docs/analysis"):
                runner.output_guard(Path(tmp), False)
    def test_resume_completed_writes_zero_contract(self):
        before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in self.out.iterdir() if p.is_file()}
        self.assertTrue(runner.completed(self.out))
        after = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in self.out.iterdir() if p.is_file()}
        self.assertEqual(before, after)
    def test_assert_bounded_rejects_final_claim(self):
        with self.assertRaisesRegex(RuntimeError, "forbidden"):
            runner.assert_bounded_text("In the 636 valid-rated rows, mechanism X causes the wage gap.")
    def test_assert_bounded_rejects_unbounded_claim(self):
        with self.assertRaisesRegex(RuntimeError, "not explicitly bounded"):
            runner.assert_bounded_text("Mechanism X appears frequently.")
    def test_assert_bounded_accepts_safe_claim(self):
        runner.assert_bounded_text("Within the 636 valid-rated rows, mechanism X has textual support.")
    def test_future_prompt_has_all_phase_boundaries(self):
        text = (self.out / "next_provisional_claim_review_prompt.md").read_text()
        for phrase in ("Do not call GABRIEL/API or any model", "Do not calculate wage gaps", "run regressions", "estimate treatment effects", "final causal claims", "Keep global analysis readiness false", "seven quarantine rows"):
            self.assertIn(phrase, text)
    def test_no_raw_prompt_response_files(self):
        names = [p.name.casefold() for p in self.out.iterdir()]
        self.assertFalse(any("raw_prompt" in name or "raw_response" in name for name in names))
    def test_runner_has_no_model_call_symbols(self):
        source = Path(runner.__file__).read_text()
        for token in ("direct_sdk_batch(", "load_subscription_key(", "requests.post(", "openai.responses"):
            self.assertNotIn(token, source)
    def test_narratives_are_corpus_bounded(self):
        for name in ("provisional_mechanism_findings_from_valid_ratings.md", "stronger_mechanism_signals_current_corpus.md", "weaker_or_inconclusive_mechanism_signals_current_corpus.md", "provisional_claims_supported_by_636_valid_ratings.md"):
            self.assertIn("636 valid-rated", (self.out / name).read_text())
    def test_claims_not_allowed_cover_final_classes(self):
        text = (self.out / "claims_not_allowed_after_summary_review.md").read_text().casefold()
        for phrase in ("wage-gap", "regression", "treatment-effect", "causal"):
            self.assertIn(phrase, text)


class DashboardTests(unittest.TestCase):
    def test_dashboard_status_gate(self):
        complete, decision = dashboard.gabriel_claim_rating_summary_review_636_status()
        self.assertTrue(complete); self.assertEqual(decision["valid_summary_rows"], 636)
    def test_dashboard_global_readiness_false(self):
        _, decision = dashboard.gabriel_claim_rating_summary_review_636_status()
        self.assertFalse(decision["global_analysis_readiness"])
    def test_dashboard_allows_only_provisional_review(self):
        _, decision = dashboard.gabriel_claim_rating_summary_review_636_status()
        self.assertTrue(decision["provisional_claim_review_allowed"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
