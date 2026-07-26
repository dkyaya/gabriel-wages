#!/usr/bin/env python3
"""Focused offline tests for final-package schema readiness review."""

from __future__ import annotations

import hashlib
import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts/review_compensation_evidence_final_provisional_schema_readiness.py"
SPEC = importlib.util.spec_from_file_location("schema_review", MODULE_PATH)
assert SPEC and SPEC.loader
review = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = review
SPEC.loader.exec_module(review)


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class SchemaReadinessReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.before = {lane: file_hash(path) for lane, path in review.LANES.items()}
        cls.result = review.audit()
        cls.after = {lane: file_hash(path) for lane, path in review.LANES.items()}

    def test_all_five_hashes_and_counts_pass(self) -> None:
        self.assertTrue(self.result["all_five_hash_checks_pass"])
        self.assertTrue(self.result["input_output_hash_sets_match"])
        self.assertTrue(all(value["pass"] for value in self.result["counts"].values()))

    def test_review_is_read_only(self) -> None:
        self.assertEqual(self.before, self.after)
        self.assertFalse(self.result["package_ledgers_modified"])
        self.assertFalse(self.result["analysis_dataset_created"])

    def test_schemas_stay_separate(self) -> None:
        self.assertTrue(self.result["schemas_remain_separate"])
        self.assertEqual(set(self.result["schema_fields"]), set(review.LANES))

    def test_non_base_duplicate_provenance_headers_are_detected(self) -> None:
        duplicated = self.result["duplicate_headers"]["non_base_wage"]
        self.assertEqual(duplicated["source_quantitative_observation_id"], 2)
        self.assertEqual(duplicated["source_mixed_join_key"], 2)
        values = self.result["non_base_duplicate_header_value_audit"]
        self.assertEqual(
            values["source_quantitative_observation_id"],
            {
                "first_nonblank_rows": 134,
                "second_nonblank_rows": 134,
                "value_disagreement_rows": 0,
            },
        )
        self.assertEqual(
            values["source_mixed_join_key"],
            {
                "first_nonblank_rows": 85,
                "second_nonblank_rows": 85,
                "value_disagreement_rows": 0,
            },
        )

    def test_required_analysis_identity_gaps_are_detected(self) -> None:
        for missing in self.result["missing_analysis_fields"].values():
            self.assertIn("retained_content_hash", missing)
            self.assertIn("matched_set_id", missing)
            self.assertIn("negotiation_cycle_id", missing)
            self.assertIn("occupation_class", missing)
        self.assertFalse(
            self.result["case_identity_audit"]["case_index_has_raw_retained_content_hash"]
        )

    def test_active_mixed_join_members_are_valid(self) -> None:
        self.assertEqual(self.result["mixed_join_audit"]["active_mixed_rows"], 371)
        self.assertEqual(self.result["mixed_join_audit"]["issue_counts"], {})
        self.assertEqual(
            self.result["mixed_join_audit"]["active_qualitative_references_to_inactive_mixed"],
            50,
        )
        self.assertEqual(
            self.result["mixed_join_audit"]["active_qualitative_references_to_missing_mixed"],
            20,
        )
        self.assertEqual(
            self.result["mixed_join_audit"]["active_qualitative_unique_missing_mixed_keys"],
            5,
        )
        self.assertEqual(
            self.result["mixed_join_audit"]["recorded_historical_missing_mixed_key_count"],
            5,
        )

    def test_duplicate_provenance_is_preserved(self) -> None:
        duplicate = self.result["duplicate_provenance_audit"]
        self.assertEqual(sum(duplicate["duplicate_observation_id_counts"].values()), 0)
        self.assertEqual(duplicate["duplicate_provenance_rows"], 14)
        self.assertEqual(duplicate["newly_canonicalized_duplicate_count"], 5)

    def test_two_conflicts_remain_explicit_and_active(self) -> None:
        unresolved = self.result["unresolved_conflict_audit"]
        self.assertEqual(unresolved["group_count"], 2)
        self.assertTrue(unresolved["all_observations_remain_active"])
        self.assertEqual(
            unresolved["recommended_treatment"],
            "quarantine_from_analysis_views_without_mutating_provisional_rows",
        )

    def test_non_base_remains_companion_data(self) -> None:
        self.assertEqual(
            self.result["non_base_recommended_treatment"],
            "retain_as_separate_companion_dataset_not_base_wage_input",
        )

    def test_readiness_holds_and_analysis_remains_false(self) -> None:
        self.assertEqual(
            self.result["schema_readiness_decision"],
            "schema_readiness_hold_schema_repairs_required",
        )
        self.assertFalse(self.result["final_analysis_ready"])
        self.assertEqual(self.result["future_prompt"], "next_schema_repair_prompt.md")
        self.assertEqual(
            {blocker["blocker_id"] for blocker in self.result["blockers"]},
            {f"B{number:02d}" for number in range(1, 12)},
        )

    def test_ocr_and_forbidden_stages_remain_closed(self) -> None:
        self.assertFalse(self.result["ocr_later_documents_included"])
        self.assertFalse(self.result["ingestion_or_codification_performed"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
