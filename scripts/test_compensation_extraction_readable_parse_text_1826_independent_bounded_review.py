#!/usr/bin/env python3
"""Offline tests for the 1,826-case independent bounded review."""

from __future__ import annotations

import csv
import json
import tempfile
import unittest
from collections import Counter
from pathlib import Path

import run_compensation_extraction_readable_parse_text_1826_independent_bounded_review as review


class IndependentBoundedReview1826Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temp = tempfile.TemporaryDirectory()
        cls.output = Path(cls.temp.name) / "independent_review"
        cls.before = {
            name: review.prior.qa500.sha_file(review.SOURCE_DIR / name)
            for name in review.REQUIRED_INPUTS
        }
        prior_summary = json.loads(
            (review.SOURCE_DIR / review.SUMMARY).read_text(encoding="utf-8")
        )
        cls.upstream_before = {
            name: review.prior.qa500.sha_file(review.prior.SOURCE_DIR / name)
            for name in prior_summary["input_sha256"]
        }
        cls.result = review.review(review.SOURCE_DIR, cls.output, write=True)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temp.cleanup()

    def test_exact_scope_and_item_accounting(self) -> None:
        counts = Counter(row["review_scope_type"] for row in self.result["ledger"])
        self.assertEqual(len(self.result["ledger"]), 27)
        self.assertEqual(counts, Counter({
            "duplicate_provenance_row": 14,
            "newly_canonicalized_duplicate": 5,
            "working_out_of_classification_reroute": 3,
            "unresolved_conflict_group": 2,
            "wasco_record_boundary_repair": 1,
            "shadow_ledger_count_and_hash_consistency": 1,
            "dashboard_and_decision_consistency": 1,
        }))

    def test_two_unresolved_groups_are_preserved(self) -> None:
        rows = [
            row for row in self.result["ledger"]
            if row["review_scope_type"] == "unresolved_conflict_group"
        ]
        self.assertEqual(len(rows), 2)
        self.assertTrue(all(row["review_status"] == "pass_explicitly_unresolved" for row in rows))
        self.assertTrue(all(row["ambiguity_preserved"] == "true" for row in rows))
        self.assertTrue(all(row["independent_outcome"] == "remain_explicitly_unresolved" for row in rows))

    def test_working_out_reroute_provenance_is_preserved(self) -> None:
        rows = [
            row for row in self.result["ledger"]
            if row["review_scope_type"] == "working_out_of_classification_reroute"
        ]
        self.assertEqual(len(rows), 3)
        self.assertTrue(all(row["linked_observation_ids"].startswith("nobsqa1826_") for row in rows))
        self.assertTrue(all(row["bounded_pointer_valid"] == "true" for row in rows))

    def test_wasco_repair_is_shadow_only_and_reconciled(self) -> None:
        rows = [
            row for row in self.result["ledger"]
            if row["review_scope_type"] == "wasco_record_boundary_repair"
        ]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["source_group_or_record_id"], review.WASCO_ID)
        self.assertEqual(rows[0]["count_check"], "4744-1+3=4746")
        source_rows = review.prior.qa500.read_csv(review.prior.SOURCE_DIR / review.prior.NONBASE)
        self.assertEqual(sum(row.get("non_base_wage_observation_id") == review.WASCO_TAIL_ID for row in source_rows), 1)

    def test_duplicate_provenance_counts_and_unique_ids(self) -> None:
        summary = self.result["summary"]
        self.assertEqual(summary["newly_canonicalized_duplicate_observations_verified"], 5)
        self.assertEqual(summary["duplicate_provenance_rows_verified"], 14)
        self.assertEqual(summary["duplicate_observation_id_count"], 0)

    def test_counts_integrity_and_rate(self) -> None:
        summary = self.result["summary"]
        self.assertEqual(summary["corrected_quantitative_active_observation_count"], 1907)
        self.assertEqual(summary["corrected_qualitative_active_observation_count"], 1954)
        self.assertEqual(summary["corrected_mixed_active_case_count"], 371)
        self.assertEqual(summary["corrected_non_base_wage_active_observation_count"], 4733)
        self.assertEqual(summary["corrected_reference_exclusion_active_count"], 345)
        self.assertEqual(summary["invalid_observation_page_count"], 0)
        self.assertEqual(summary["base_non_base_wage_contamination_count"], 0)
        self.assertAlmostEqual(summary["unresolved_quantitative_conflict_rate"], 2 / 1907, places=8)

    def test_input_and_shadow_hashes_are_unchanged(self) -> None:
        after = {
            name: review.prior.qa500.sha_file(review.SOURCE_DIR / name)
            for name in review.REQUIRED_INPUTS
        }
        upstream_after = {
            name: review.prior.qa500.sha_file(review.prior.SOURCE_DIR / name)
            for name in self.upstream_before
        }
        self.assertEqual(self.before, after)
        self.assertEqual(self.upstream_before, upstream_after)
        self.assertNotEqual(self.output.resolve(), review.SOURCE_DIR.resolve())

    def test_decision_allows_prompt_not_merge_or_analysis(self) -> None:
        decision = self.result["decision"]
        self.assertEqual(
            decision["decision"],
            "independent_review_pass_final_provisional_merge_prompt_allowed",
        )
        self.assertTrue(decision["final_provisional_merge_prompt_allowed"])
        self.assertFalse(decision["final_provisional_merge_allowed"])
        self.assertFalse(decision["final_analysis_ready"])
        self.assertFalse(decision["ingestion_allowed"])
        self.assertFalse(decision["codify_allowed"])

    def test_no_network_model_extraction_or_selection_path(self) -> None:
        source = Path(review.__file__).read_text(encoding="utf-8").lower()
        for forbidden in (
            "requests.", "httpx.", "urllib.request", "call_gabriel(",
            "run_live_extraction(", "freeze_selection(", "ocrmypdf",
        ):
            self.assertNotIn(forbidden, source)
        self.assertFalse(self.result["summary"]["gabriel_api_used"])
        self.assertFalse(self.result["summary"]["new_extraction_run"])
        self.assertFalse(self.result["summary"]["new_document_selection"])

    def test_written_ledger_has_expected_rows(self) -> None:
        with (self.output / review.OUTPUT_NAMES["ledger"]).open(
            newline="", encoding="utf-8"
        ) as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 27)
        self.assertTrue(all(row["review_status"].startswith("pass") for row in rows))


if __name__ == "__main__":
    unittest.main(verbosity=2)
