#!/usr/bin/env python3
"""Offline regression tests for the 1,826-case targeted conflict QA pass."""

from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

import run_compensation_extraction_readable_parse_text_1826_targeted_conflict_qa as qa


class ReadableParseText1826TargetedConflictQATests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temp = tempfile.TemporaryDirectory()
        cls.output = Path(cls.temp.name) / "qa"
        cls.before = {
            name: qa.qa500.sha_file(qa.SOURCE_DIR / name)
            for name in (
                qa.REVIEW, qa.DECISION, qa.SUMMARY, qa.QUANT, qa.QUAL,
                qa.MIXED, qa.NONBASE, qa.REFERENCE,
            )
        }
        cls.result = qa.resolve(qa.SOURCE_DIR, cls.output, write=True)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temp.cleanup()

    def test_exact_37_group_scope(self) -> None:
        self.assertEqual(len(self.result["resolutions"]), 37)
        self.assertEqual(self.result["summary"]["review_group_count"], 37)
        self.assertEqual(
            sum(self.result["summary"]["targeted_resolution_counts"].values()), 37
        )

    def test_resolution_accounting_and_rate(self) -> None:
        summary = self.result["summary"]
        self.assertEqual(summary["targeted_resolved_group_count"], 35)
        self.assertEqual(summary["targeted_unresolved_group_count"], 2)
        self.assertEqual(
            summary["targeted_resolution_counts"],
            {
                "distinct_classification_or_rank": 13,
                "distinct_effective_period": 10,
                "distinct_schedule_cell": 11,
                "insufficient_evidence_needs_review": 2,
                "non_base_wage_misroute": 1,
            },
        )
        self.assertAlmostEqual(
            summary["unresolved_quantitative_conflict_rate"], 2 / 1907, places=8
        )
        self.assertLessEqual(summary["unresolved_quantitative_conflict_rate"], .02)

    def test_working_out_of_classification_is_rerouted_with_provenance(self) -> None:
        rows = [
            row for row in self.result["resolutions"]
            if row["resolution_classification"] == "non_base_wage_misroute"
        ]
        self.assertEqual(len(rows), 1)
        self.assertEqual(len(rows[0]["routed_quantitative_observation_ids"].split("|")), 3)
        created = [
            row for row in self.result["rows"]["nonbase"]
            if row.get("cumulative_cohort")
            == "readable_parse_text_1826_targeted_conflict_qa"
        ]
        self.assertEqual(len(created), 3)
        self.assertTrue(all(row["source_quantitative_observation_id"] for row in created))
        self.assertTrue(all(row["source_mixed_join_key"] == row["source_mixed_join_key"] for row in created))
        self.assertTrue(all(row["non_base_wage_type"] == "stipend" for row in created))
        active_quant = {
            row["quantitative_observation_id"]: row
            for row in self.result["rows"]["quant"]
        }
        self.assertTrue(
            all(
                active_quant[source_id]["active_in_readable_conflict_qa_lane"]
                == "false"
                for source_id in rows[0]["routed_quantitative_observation_ids"].split("|")
            )
        )

    def test_corrected_counts_and_integrity_invariants(self) -> None:
        summary = self.result["summary"]
        self.assertEqual(summary["corrected_quantitative_active_observation_count"], 1907)
        self.assertEqual(summary["corrected_qualitative_active_observation_count"], 1954)
        self.assertEqual(summary["corrected_mixed_active_case_count"], 371)
        self.assertEqual(summary["corrected_non_base_wage_active_observation_count"], 4733)
        self.assertEqual(summary["corrected_reference_exclusion_active_count"], 345)
        self.assertEqual(summary["source_csv_record_boundary_repairs"], 1)
        self.assertEqual(summary["source_non_base_wage_physical_csv_row_count"], 4744)
        self.assertEqual(summary["duplicate_observation_id_count"], 0)
        self.assertEqual(summary["invalid_observation_page_count"], 0)
        self.assertEqual(summary["base_non_base_wage_contamination_count"], 0)
        self.assertEqual(summary["newly_canonicalized_duplicate_observations_preserved"], 5)
        self.assertTrue(summary["matched_representation_intact"])

    def test_shadow_outputs_do_not_overwrite_inputs(self) -> None:
        after = {name: qa.qa500.sha_file(qa.SOURCE_DIR / name) for name in self.before}
        self.assertEqual(self.before, after)
        for key in ("quant", "qual", "mixed", "nonbase", "reference"):
            self.assertTrue((self.output / qa.OUTPUT_NAMES[key]).is_file())
        self.assertNotEqual(self.output.resolve(), qa.SOURCE_DIR.resolve())

    def test_no_model_network_selection_or_extraction_path(self) -> None:
        source = Path(qa.__file__).read_text(encoding="utf-8").lower()
        for forbidden in (
            "requests.", "httpx.", "urllib.request", "call_gabriel(",
            "freeze_selection(", "run_live_extraction(", "ocrmypdf",
        ):
            self.assertNotIn(forbidden, source)
        summary = self.result["summary"]
        self.assertFalse(summary["gabriel_api_used"])
        self.assertFalse(summary["new_extraction_run"])
        self.assertFalse(summary["new_document_selection"])

    def test_dashboard_gate_stays_provisional_and_analysis_false(self) -> None:
        decision = self.result["decision"]
        self.assertTrue(decision["qa_pass"])
        self.assertFalse(decision["final_provisional_merge_allowed"])
        self.assertFalse(decision["final_analysis_ready"])
        self.assertFalse(decision["ingestion_allowed"])
        self.assertFalse(decision["codify_allowed"])

    def test_all_readable_covered_and_ocr_untouched(self) -> None:
        summary = self.result["summary"]
        self.assertEqual(summary["cumulative_case_count"], 1826)
        self.assertEqual(summary["cumulative_unique_content_hash_count"], 1826)
        self.assertTrue(summary["all_unique_readable_parse_text_documents_covered"])
        self.assertTrue(summary["ocr_later_documents_untouched"])

    def test_resolution_csv_has_37_rows(self) -> None:
        with (self.output / qa.OUTPUT_NAMES["resolutions"]).open(
            newline="", encoding="utf-8"
        ) as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 37)
        self.assertTrue(all(row["reason_codes"] for row in rows))


if __name__ == "__main__":
    unittest.main(verbosity=2)
