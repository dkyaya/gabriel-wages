#!/usr/bin/env python3
"""Focused offline tests for bounded qualitative span/residual metadata repair."""

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
MODULE_PATH = ROOT / "scripts/run_compensation_evidence_bounded_qualitative_span_residual_metadata_repair.py"
SPEC = importlib.util.spec_from_file_location("bounded_span_residual_repair", MODULE_PATH)
assert SPEC and SPEC.loader
repair = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = repair
SPEC.loader.exec_module(repair)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


class BoundedSpanResidualMetadataRepairTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.current_before = {name: digest(path) for name, path in repair.CURRENT_INPUTS.items()}
        cls.durable_before = {name: digest(path) for name, path in repair.DURABLE_INPUTS.items()}
        cls.packet_before = {name: digest(path) for name, path in repair.PACKET_INPUTS.items()}
        cls.temp = tempfile.TemporaryDirectory(
            dir=ROOT / "docs/analysis/compensation_extraction"
        )
        cls.output = Path(cls.temp.name) / "bounded_span_residual_repair"
        cls.preflight = repair.no_write_preflight(cls.output)
        cls.output_after_preflight = cls.output.exists()
        cls.result = repair.run(cls.output)
        cls.current_after = {name: digest(path) for name, path in repair.CURRENT_INPUTS.items()}
        cls.durable_after = {name: digest(path) for name, path in repair.DURABLE_INPUTS.items()}
        cls.packet_after = {name: digest(path) for name, path in repair.PACKET_INPUTS.items()}

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temp.cleanup()

    def test_no_write_preflight_and_immutable_hashes(self) -> None:
        self.assertFalse(self.output_after_preflight)
        self.assertEqual(self.preflight["writes_performed"], 0)
        self.assertEqual(self.preflight["package_sha256_checks_passed"], 5)
        self.assertEqual(self.preflight["residual_cycle_identity_count"], 571)
        self.assertEqual(self.preflight["residual_non_safety_identity_count"], 535)
        self.assertEqual(self.current_before, self.current_after)
        self.assertEqual(self.durable_before, self.durable_after)
        self.assertEqual(self.packet_before, self.packet_after)

    def test_qualitative_span_capture_fails_closed_without_text_payload(self) -> None:
        audit = json.loads((self.output / repair.OUTPUTS["span_audit"]).read_text())
        ledger = rows(self.output / repair.OUTPUTS["span_ledger"])
        self.assertEqual(len(ledger), 1954)
        self.assertEqual(audit["exact_bounded_page_pointer_match_count"], 1954)
        self.assertEqual(audit["retained_bounded_text_payload_count"], 0)
        self.assertEqual(audit["literal_span_exact_substring_qa_pass_count"], 0)
        self.assertFalse(audit["coded_qualitative_analysis_view_created"])
        self.assertTrue(
            all(
                row["span_capture_status"] == "span_unavailable_or_unverified"
                and row["span_qa_pass"] == "false"
                and not row["literal_verbatim_evidence_span"]
                for row in ledger
            )
        )
        self.assertFalse((self.output / "qualitative_mechanism_analysis_view_candidate.csv").exists())

    def test_cycle_repairs_are_exact_and_prior_rows_are_preserved(self) -> None:
        prior = {row["document_identity_id"]: row for row in rows(repair.CURRENT_INPUTS["cycle_bridge"])}
        revised = rows(self.output / repair.OUTPUTS["cycle_bridge"])
        candidate = {
            row["queue_id"]: row for row in rows(repair.DURABLE_INPUTS["candidate_queue"])
        }
        self.assertEqual(len(revised), 1826)
        self.assertGreater(self.result["cycle_matching"]["new_exact_cycle_count"], 0)
        for row in revised:
            old = prior[row["document_identity_id"]]
            if old["negotiation_cycle_id"]:
                self.assertEqual(row["contract_period_start"], old["contract_period_start"])
                self.assertEqual(row["contract_period_end"], old["contract_period_end"])
                self.assertEqual(row["negotiation_cycle_id"], old["negotiation_cycle_id"])
            elif row["negotiation_cycle_id"]:
                self.assertRegex(row["contract_period_start"], r"^\d{4}-\d{2}-\d{2}$")
                self.assertRegex(row["contract_period_end"], r"^\d{4}-\d{2}-\d{2}$")
                self.assertTrue(row["residual_cycle_exact_evidence_sha256"])
                self.assertNotIn("document_title", row["residual_cycle_support_fields"])
                if "candidate_queue.cycle_match_notes" in row["residual_cycle_support_fields"]:
                    self.assertIn(
                        row["residual_cycle_exact_evidence"],
                        candidate[row["candidate_queue_row_id"]]["cycle_match_notes"],
                    )

    def test_non_safety_classes_are_controlled_or_quarantined(self) -> None:
        prior = {row["document_identity_id"]: row for row in rows(repair.CURRENT_INPUTS["occupation_bridge"])}
        revised = rows(self.output / repair.OUTPUTS["occupation_bridge"])
        allowed = {
            "police", "fire", "teacher", "sanitation", "clerical_admin", "public_works",
            "transit", "parks_rec", "library", "nurse_health", "other",
        }
        self.assertGreater(self.result["occupation"]["new_non_safety_subclass_count"], 0)
        for row in revised:
            old = prior[row["document_identity_id"]]
            self.assertIn(row["controlled_occupation_class"], allowed | {""})
            if old["controlled_occupation_class"]:
                self.assertEqual(row["controlled_occupation_class"], old["controlled_occupation_class"])
            if row["unit_type"] == "non_safety" and not row["controlled_occupation_class"]:
                self.assertTrue(row["residual_occupation_bridge_status"].startswith("quarantined_"))

    def test_quantitative_nonbase_reference_and_conflicts_are_byte_preserved(self) -> None:
        pairs = {
            "quant_candidate": "quant_candidate",
            "quant_exceptions": "quant_exceptions",
            "nonbase_candidate": "nonbase_candidate",
            "reference_control": "reference_control",
            "conflict_quarantine": "conflict_quarantine",
        }
        for output_name, input_name in pairs.items():
            self.assertEqual(
                digest(self.output / repair.OUTPUTS[output_name]),
                digest(repair.CURRENT_INPUTS[input_name]),
            )
        self.assertEqual(len(rows(self.output / repair.OUTPUTS["quant_candidate"])), 862)
        self.assertEqual(len(rows(self.output / repair.OUTPUTS["quant_exceptions"])), 1045)
        self.assertEqual(len(rows(self.output / repair.OUTPUTS["nonbase_candidate"])), 4733)
        self.assertEqual(len(rows(self.output / repair.OUTPUTS["reference_control"])), 345)
        conflicts = rows(self.output / repair.OUTPUTS["conflict_quarantine"])
        self.assertEqual(len(conflicts), 2)
        self.assertEqual(sum(int(row["observation_count"]) for row in conflicts), 5)

    def test_navigation_only_and_analysis_readiness_false(self) -> None:
        nav = rows(self.output / repair.OUTPUTS["qual_navigation"])
        self.assertEqual(len(nav), 1954)
        self.assertTrue(all(row["qualitative_coded_measurement_eligible"] == "false" for row in nav))
        self.assertFalse(self.result["analysis_readiness"])
        self.assertFalse(self.result["analysis_facing_promotion_allowed"])
        self.assertFalse(self.result["repeat_analysis_readiness_review_allowed"])
        self.assertEqual(
            self.result["decision"],
            "bounded_span_metadata_repair_blocked_missing_bounded_text_or_span_support",
        )

    def test_forbidden_actions_absent(self) -> None:
        self.assertEqual(self.result["forbidden_actions_performed"], [])
        self.assertFalse(self.result["ocr_later_documents_included"])
        audit = self.result["qualitative_span_capture"]
        self.assertEqual(audit["pdfs_opened"], 0)
        self.assertEqual(audit["ocr_runs"], 0)
        self.assertEqual(audit["model_calls"], 0)
        self.assertEqual(audit["extraction_runs"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
