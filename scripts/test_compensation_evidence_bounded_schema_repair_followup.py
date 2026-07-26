#!/usr/bin/env python3
"""Focused offline tests for the bounded compensation schema-repair follow-up."""

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
MODULE_PATH = ROOT / "scripts/run_compensation_evidence_bounded_schema_repair_followup.py"
SPEC = importlib.util.spec_from_file_location("bounded_schema_followup", MODULE_PATH)
assert SPEC and SPEC.loader
followup = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = followup
SPEC.loader.exec_module(followup)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class BoundedSchemaFollowupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.prior_before = {name: digest(path) for name, path in followup.PRIOR_INPUTS.items()}
        cls.durable_before = {name: digest(path) for name, path in followup.DURABLE_INPUTS.items()}
        cls.temp = tempfile.TemporaryDirectory(dir=ROOT / "docs/analysis/compensation_extraction")
        cls.output = Path(cls.temp.name) / "bounded_followup"
        cls.preflight = followup.no_write_preflight(cls.output)
        cls.output_existed_after_preflight = cls.output.exists()
        cls.result = followup.run(cls.output)
        cls.prior_after = {name: digest(path) for name, path in followup.PRIOR_INPUTS.items()}
        cls.durable_after = {name: digest(path) for name, path in followup.DURABLE_INPUTS.items()}

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temp.cleanup()

    def test_no_write_preflight_and_hashes(self) -> None:
        self.assertFalse(self.output_existed_after_preflight)
        self.assertEqual(self.preflight["writes_performed"], 0)
        self.assertEqual(self.preflight["package_sha256_checks_passed"], 5)
        self.assertEqual(self.preflight["document_identity_count"], 1826)

    def test_prior_and_durable_inputs_unchanged(self) -> None:
        self.assertEqual(self.prior_before, self.prior_after)
        self.assertEqual(self.durable_before, self.durable_after)
        self.assertEqual(
            {name: self.prior_after[name] for name in followup.EXPECTED_PRIOR_SHA256},
            followup.EXPECTED_PRIOR_SHA256,
        )

    def test_cycle_and_matches_are_supported_or_quarantined(self) -> None:
        cycle = rows(self.output / followup.OUTPUTS["cycle_bridge"])
        self.assertEqual(len(cycle), 1826)
        allowed = {
            "established_single_exact_pair",
            "quarantined_conflicting_or_multiple_exact_pairs",
            "quarantined_no_exact_full_date_pair",
        }
        self.assertTrue(all(row["cycle_bridge_status"] in allowed for row in cycle))
        for row in cycle:
            if row["negotiation_cycle_id"]:
                self.assertTrue(row["contract_period_start"] and row["contract_period_end"])
                self.assertEqual(row["cycle_bridge_status"], "established_single_exact_pair")
            if row["matched_set_id"]:
                self.assertTrue(row["negotiation_cycle_id"])
        self.assertGreater(self.result["cycle_matching"]["exact_cycle_established_count"], 0)
        self.assertGreater(self.result["cycle_matching"]["matched_set_id_document_count"], 0)

    def test_non_safety_subclasses_are_controlled_or_quarantined(self) -> None:
        occupation = rows(self.output / followup.OUTPUTS["occupation_bridge"])
        controlled = set(followup.OCCUPATION_RULES) | {"police", "fire"}
        self.assertTrue(
            all(not row["controlled_occupation_class"] or row["controlled_occupation_class"] in controlled for row in occupation)
        )
        for row in occupation:
            if row["unit_type"] == "non_safety" and not row["controlled_occupation_class"]:
                self.assertTrue(row["occupation_class_bridge_status"].startswith("quarantined_"))
        self.assertGreater(self.result["occupation"]["non_safety_subclass_established_count"], 0)
        self.assertGreater(self.result["occupation"]["non_safety_quarantined_count"], 0)

    def test_retrieval_provenance_uses_explicit_durable_support(self) -> None:
        retrieval = rows(self.output / followup.OUTPUTS["retrieval_bridge"])
        self.assertEqual(len(retrieval), 1826)
        for row in retrieval:
            if row["retrieval_date"]:
                self.assertEqual(row["retrieval_method"], "public_download")
                self.assertTrue(row["source_cite"] and row["artifact_pointer"])
                self.assertTrue(row["retrieval_bridge_status"].startswith("established_"))
        self.assertEqual(self.result["retrieval_provenance"]["urls_opened_by_followup"], 0)

    def test_quantitative_raw_and_prior_normalization_fields_preserved(self) -> None:
        prior = rows(followup.PRIOR_INPUTS["quantitative"])
        repaired = rows(self.output / followup.OUTPUTS["quant_shadow"])
        preserved = [
            "rate_value",
            "salary_value",
            "hourly_rate",
            "annual_salary",
            "percentage_increase",
            "normalized_scalar_value",
            "normalized_range_minimum",
            "normalized_range_maximum",
            "analysis_quarantine_reasons",
            "analysis_candidate_eligible",
        ]
        self.assertEqual(
            [[row[field] for field in preserved] for row in prior],
            [[row[field] for field in preserved] for row in repaired],
        )
        conflict = [
            row
            for row in repaired
            if "explicit_unresolved_conflict_member" in row["followup_analysis_quarantine_reasons"]
        ]
        self.assertEqual(len(conflict), 5)
        self.assertTrue(all(row["followup_analysis_candidate_eligible"] == "false" for row in conflict))

    def test_qualitative_is_navigation_only_without_spans(self) -> None:
        audit = json.loads((self.output / followup.OUTPUTS["qual_span_audit"]).read_text())
        self.assertEqual(audit["dedicated_literal_verbatim_span_count"], 0)
        self.assertFalse(audit["coded_analysis_candidate_created"])
        self.assertFalse((self.output / "qualitative_mechanism_analysis_view_candidate_followup.csv").exists())
        self.assertEqual(len(rows(self.output / followup.OUTPUTS["qual_navigation"])), 1954)

    def test_nonbase_and_reference_remain_separate(self) -> None:
        nonbase = rows(self.output / followup.OUTPUTS["nonbase_candidate"])
        reference = rows(self.output / followup.OUTPUTS["reference_control"])
        self.assertEqual(len(nonbase), 4733)
        self.assertEqual(len(reference), 345)
        self.assertTrue(all(row["base_wage_outcome_eligible"] == "false" for row in nonbase))
        self.assertTrue(all(row["control_only"] == "true" for row in reference))

    def test_forbidden_actions_absent_and_readiness_false(self) -> None:
        self.assertEqual(self.result["forbidden_actions_performed"], [])
        self.assertFalse(self.result["ocr_later_documents_included"])
        self.assertFalse(self.result["analysis_readiness"])
        self.assertFalse(self.result["analysis_facing_promotion_allowed"])
        self.assertFalse(self.result["repeat_analysis_readiness_review_allowed"])
        self.assertEqual(
            self.result["decision"],
            "bounded_schema_followup_partial_additional_bounded_repair_needed",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
