#!/usr/bin/env python3
"""Focused gates for gap-directed Tier C verification and memo visibility."""

from __future__ import annotations

import importlib.util
import inspect
import json
import unittest
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = ROOT / "scripts/run_targeted_tier_c_verification_from_bounded_memo_gaps.py"
spec = importlib.util.spec_from_file_location("tier_c_runner", RUNNER_PATH)
runner = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(runner)


class TierCVerificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pool, cls.hashes = runner.validate_inputs()
        cls.queue, cls.scores = runner.select_queue(cls.pool)

    def test_immutable_inputs_are_pinned(self):
        self.assertEqual(len(self.hashes), len(runner.CANDIDATE_HASHES) + len(runner.MEMO_HASHES) + 1)

    def test_exact_tier_c_pool_and_targeted_queue(self):
        self.assertEqual(len(self.pool), 2703)
        self.assertEqual(len(self.queue), 1000)
        self.assertEqual(len({row["candidate_id"] for row in self.queue}), 1000)
        self.assertTrue(all(row["priority_tier"] == "tier_c" for row in self.queue))

    def test_fixed_gap_quotas(self):
        self.assertEqual(Counter(row["target_mechanism_family"] for row in self.queue), Counter(runner.QUOTAS))

    def test_no_weak_padding(self):
        self.assertGreaterEqual(min(int(row["gap_priority_score"]) for row in self.queue), runner.MIN_GAP_SCORE)
        self.assertTrue(all(row["quality_label"] in {"verification_ready_medium", "verification_ready_low"} for row in self.queue))

    def test_a_b_d_repair_deprioritized_and_prior_excluded_absent(self):
        prior = runner.read_csv(runner.AB_DIR / "targeted_source_verification_tier_a_b_results.csv")
        excluded = {row["candidate_id"] for row in prior if row["verification_status"] != "verified_source_lead"}
        ids = {row["candidate_id"] for row in self.queue}
        self.assertFalse(ids & excluded)
        self.assertTrue(all(row["review_disposition"] == "verification_queue" for row in self.queue))

    def test_regions_are_static_or_unknown(self):
        allowed = {"Northeast", "Midwest", "South", "West", "District of Columbia / Federal district", "Unknown"}
        self.assertTrue(all(row["derived_region"] in allowed for row in self.queue))
        self.assertEqual(runner.region("MA"), "Northeast")
        self.assertEqual(runner.region("OH"), "Midwest")
        self.assertEqual(runner.region("TX"), "South")
        self.assertEqual(runner.region("CA"), "West")
        self.assertEqual(runner.region(""), "Unknown")

    def test_gap_priority_is_memo_directed(self):
        mechanisms = {row["target_mechanism_family"] for row in self.queue}
        self.assertEqual(mechanisms, set(runner.QUOTAS))
        self.assertGreaterEqual(sum(row["derived_region"] in {"South", "Northeast"} for row in self.queue), 700)
        self.assertGreaterEqual(sum("same_city_counterpart_value" in row["gap_priority_reason"] for row in self.queue), 700)

    def test_runner_uses_existing_head_only_transport(self):
        source = RUNNER_PATH.read_text(encoding="utf-8")
        self.assertIn("head_probe", source)
        self.assertNotIn('client.get(', source)
        self.assertNotIn('client.stream("GET"', source)
        self.assertNotIn("response.read(", source)
        self.assertNotIn("pdfplumber", source)
        self.assertNotIn("pytesseract", source)

    def test_result_schema_keeps_downstream_boundaries_closed(self):
        self.assertIn("download_status", runner.RESULT_FIELDS)
        self.assertIn("extraction_status", runner.RESULT_FIELDS)
        self.assertIn("rating_status", runner.RESULT_FIELDS)
        self.assertIn("causal_status", runner.RESULT_FIELDS)

    def test_partial_outputs_cannot_masquerade_as_complete(self):
        source = inspect.getsource(runner.validate_complete)
        self.assertIn("REQUIRED_OUTPUTS", source)
        self.assertIn("EXPECTED_QUEUE", source)

    def test_completed_outputs_when_present(self):
        if not runner.OUTPUT_DIR.exists():
            self.skipTest("outputs not materialized")
        runner.validate_complete()
        results = runner.read_csv(runner.OUTPUT_DIR / "targeted_tier_c_verification_results.csv")
        self.assertEqual(len(results), 1000)
        self.assertTrue(all(row["priority_tier"] == "tier_c" for row in results))
        self.assertTrue(all(row["download_status"] == "not_downloaded" for row in results))
        self.assertTrue(all(row["extraction_status"] == "not_extracted" for row in results))
        self.assertTrue(all(row["rating_status"] == "not_rated" for row in results))
        self.assertTrue(all(row["causal_status"] == "not_causal_evidence" for row in results))

    def test_exclusions_reconcile_when_present(self):
        if not (runner.OUTPUT_DIR / "targeted_tier_c_verification_results_summary.json").exists():
            self.skipTest("results not materialized")
        summary = runner.read_json(runner.OUTPUT_DIR / "targeted_tier_c_verification_results_summary.json")
        self.assertEqual(sum(summary["verification_status_counts"].values()), 1000)

    def test_dashboard_memo_visibility_when_present(self):
        visibility = runner.OUTPUT_DIR / "dashboard_visibility_check_for_bounded_memo_verified_keys.json"
        if not visibility.exists():
            self.skipTest("dashboard visibility output not materialized")
        checks = runner.read_json(visibility)
        self.assertTrue(checks["local_dashboard_data_rebuilt"])
        self.assertTrue(checks["local_production_build_exists"])
        self.assertTrue(checks["memo_decision_present"])
        self.assertTrue(checks["memo_exact_same_source_pairs_268"])
        self.assertTrue(checks["memo_linked_quantitative_rows_208"])
        self.assertTrue(checks["memo_linked_qualitative_records_90"])
        self.assertTrue(checks["memo_path_present"])
        self.assertTrue(checks["memo_dashboard_metadata_path_present"])
        self.assertTrue(checks["memo_geography_path_present"])
        self.assertTrue(checks["global_analysis_readiness_false"])

    def test_future_prompt_preserves_source_review_boundaries_when_present(self):
        path = runner.OUTPUT_DIR / "next_task.md"
        if not path.exists():
            self.skipTest("future prompt not materialized")
        text = path.read_text(encoding="utf-8").casefold()
        for phrase in ("verified_source_lead", "do not", "pdf pages", "ocr", "extract", "rate", "wage gaps", "regressions", "causal", "global analysis readiness"):
            self.assertIn(phrase, text)

    def test_dashboard_global_readiness_stays_false(self):
        path = ROOT / "docs/dashboard/data/analysis_readiness.json"
        if not path.exists():
            self.skipTest("dashboard data unavailable")
        payload = path.read_text(encoding="utf-8").casefold()
        self.assertNotIn('"global_analysis_readiness": true', payload)


if __name__ == "__main__":
    unittest.main(verbosity=2)
