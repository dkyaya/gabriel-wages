#!/usr/bin/env python3
"""Focused offline tests for deterministic compensation schema repair."""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts/repair_compensation_evidence_final_provisional_schemas.py"
SPEC = importlib.util.spec_from_file_location("schema_repair", MODULE_PATH)
assert SPEC and SPEC.loader
repair = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = repair
SPEC.loader.exec_module(repair)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class SchemaRepairTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.package_before = {lane: digest(path) for lane, path in repair.LANES.items()}
        cls.durable_before = {name: digest(path) for name, path in repair.DURABLE_BRIDGE_INPUTS.items()}
        cls.temp = tempfile.TemporaryDirectory(
            dir=ROOT / "docs/analysis/compensation_extraction"
        )
        cls.output = Path(cls.temp.name) / "new_schema_repair"
        cls.dry = repair.no_write_preflight(cls.output)
        cls.dry_output_existed_after_preflight = cls.output.exists()
        cls.result = repair.run(cls.output)
        cls.package_after = {lane: digest(path) for lane, path in repair.LANES.items()}
        cls.durable_after = {name: digest(path) for name, path in repair.DURABLE_BRIDGE_INPUTS.items()}

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temp.cleanup()

    def test_no_write_dry_run_and_new_boundary(self) -> None:
        self.assertEqual(self.dry["writes_performed"], 0)
        self.assertFalse(self.dry_output_existed_after_preflight)
        self.assertEqual(self.dry["package_hashes_passed"], 5)

    def test_package_and_durable_ledgers_unchanged(self) -> None:
        self.assertEqual(self.package_before, self.package_after)
        self.assertEqual(self.durable_before, self.durable_after)
        self.assertEqual(self.package_after, repair.EXPECTED_PACKAGE_SHA256)

    def test_nonbase_duplicate_lineage_is_lossless(self) -> None:
        audit = self.result["nonbase_duplicate_lineage_repair"]
        self.assertEqual(audit["source_quantitative_populated_each"], [134, 134])
        self.assertEqual(audit["source_mixed_populated_each"], [85, 85])
        self.assertEqual(audit["source_quantitative_disagreements"], 0)
        self.assertEqual(audit["source_mixed_disagreements"], 0)
        with (self.output / repair.OUTPUT_FILENAMES["nonbase_shadow"]).open() as handle:
            header = next(csv.reader(handle))
        self.assertEqual(len(header), len(set(header)))

    def test_raw_hash_bridge_is_one_to_one(self) -> None:
        audit = self.result["identity_provenance_bridge"]
        self.assertEqual(audit["document_identity_count"], 1826)
        self.assertEqual(audit["unique_raw_retained_content_hash_count"], 1826)
        self.assertEqual(audit["identity_quarantine_count"], 0)
        self.assertEqual(audit["durable_inputs_mutated"], False)
        self.assertEqual(audit["ocr_needed_or_ocr_later_count"], 0)
        self.assertEqual(audit["parse_text_present_or_partial_count"], 1826)

    def test_matching_and_occupation_are_not_fabricated(self) -> None:
        audit = self.result["identity_provenance_bridge"]
        self.assertEqual(audit["occupation_class_exact_count"], 1219)
        self.assertEqual(audit["occupation_class_incomplete_non_safety_count"], 607)
        self.assertEqual(audit["negotiation_cycle_id_count"], 0)
        self.assertEqual(audit["matched_set_id_count"], 0)

    def test_current_active_is_exact_copy_and_qa_is_derived(self) -> None:
        rows = read_rows(self.output / repair.OUTPUT_FILENAMES["quant_shadow"])
        self.assertTrue(all(row["current_active"] == row["active_in_readable_conflict_qa_lane"] for row in rows))
        self.assertTrue(all(row["current_qa_status"] and row["current_qa_status_source"] for row in rows))

    def test_raw_quantitative_values_preserved_and_ambiguous_not_scalarized(self) -> None:
        original = read_rows(repair.LANES["quantitative"])
        repaired = read_rows(self.output / repair.OUTPUT_FILENAMES["quant_shadow"])
        raw_fields = ["rate_value", "salary_value", "hourly_rate", "annual_salary", "percentage_increase"]
        self.assertEqual(
            [[row[field] for field in raw_fields] for row in original],
            [[row[field] for field in raw_fields] for row in repaired],
        )
        for row in repaired:
            if "raw_value_formula_pair_multiplier_hours_or_unparsed" in row["analysis_quarantine_reasons"]:
                self.assertEqual(row["normalized_scalar_value"], "")

    def test_two_conflicts_and_five_members_quarantined(self) -> None:
        rows = read_rows(self.output / repair.OUTPUT_FILENAMES["quant_shadow"])
        members = [row for row in rows if row["unresolved_conflict_resolution_id"]]
        self.assertEqual(len(members), 5)
        self.assertEqual(len({row["unresolved_conflict_resolution_id"] for row in members}), 2)
        self.assertTrue(all(row["analysis_candidate_eligible"] == "false" for row in members))

    def test_active_mixed_and_historical_memberships(self) -> None:
        audit = self.result["mixed"]
        self.assertEqual(audit["active_join_validation"]["active_mixed_rows"], 371)
        self.assertEqual(audit["active_qualitative_historical_inactive_rows"], 50)
        self.assertEqual(audit["active_qualitative_historical_inactive_unique_keys"], 16)
        self.assertEqual(audit["active_qualitative_historical_missing_rows"], 20)
        self.assertEqual(audit["active_qualitative_historical_missing_unique_keys"], 5)

    def test_nonbase_and_reference_remain_separate(self) -> None:
        self.assertEqual(self.result["non_base_wage"]["base_wage_outcome_eligible_count"], 0)
        self.assertEqual(self.result["reference_and_exclusion"]["analysis_outcome_eligible_count"], 0)
        nonbase = read_rows(self.output / repair.OUTPUT_FILENAMES["nonbase_candidate"])
        reference = read_rows(self.output / repair.OUTPUT_FILENAMES["reference_control"])
        self.assertTrue(all(row["base_wage_outcome_eligible"] == "false" for row in nonbase))
        self.assertTrue(all(row["control_only"] == "true" for row in reference))

    def test_qualitative_is_navigation_only(self) -> None:
        self.assertFalse(self.result["qualitative"]["coded_analysis_candidate_created"])
        self.assertFalse((self.output / "qualitative_mechanism_analysis_view_candidate.csv").exists())
        navigation = read_rows(self.output / repair.OUTPUT_FILENAMES["qual_navigation"])
        self.assertEqual(len(navigation), 1954)
        self.assertTrue(all(row["qualitative_coded_measurement_eligible"] == "false" for row in navigation))

    def test_analysis_readiness_stays_false(self) -> None:
        self.assertEqual(
            self.result["decision"], "schema_repairs_partial_additional_bounded_evidence_needed"
        )
        self.assertFalse(self.result["analysis_readiness"])
        self.assertFalse(self.result["analysis_facing_promotion_allowed"])
        self.assertFalse(self.result["repeat_analysis_readiness_review_allowed"])

    def test_no_forbidden_output_locations_or_actions(self) -> None:
        self.assertEqual(self.result["forbidden_actions_performed"], [])
        self.assertFalse(self.result["ocr_later_documents_included"])
        self.assertFalse((ROOT / "data/compensation_analysis.csv").exists())
        self.assertFalse((self.output / "qualitative_mechanism_analysis_view_candidate.csv").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
