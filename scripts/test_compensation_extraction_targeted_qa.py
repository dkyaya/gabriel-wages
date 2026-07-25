#!/usr/bin/env python3
"""Offline tests for deterministic 500-document targeted QA."""

from __future__ import annotations

import csv
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts/run_compensation_extraction_targeted_qa.py"
spec = importlib.util.spec_from_file_location("targeted_qa", RUNNER)
if spec is None or spec.loader is None:
    raise RuntimeError("Could not load targeted QA runner")
qa = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = qa
spec.loader.exec_module(qa)


def quant(**updates: str) -> dict[str, str]:
    row = {
        "compensation_type": "annual_salary",
        "occupation_unit_classification_rank": "",
        "rate_value": "",
        "salary_value": "50000",
        "hourly_rate": "",
        "annual_salary": "50000",
        "pay_band": "",
        "step": "",
        "grade": "",
        "percentage_increase": "",
        "effective_date": "2026-01-01",
        "currency_or_unit": "USD annual",
        "reason_code": "SCHEDULE_A",
    }
    row.update(updates)
    return row


class TargetedQATests(unittest.TestCase):
    def test_nonbase_terms_are_routed_not_promoted(self) -> None:
        row = quant(
            compensation_type="other",
            annual_salary="",
            salary_value="",
            rate_value="1.5 times regular rate",
            reason_code="OVERTIME_RATE",
        )
        classification, detected, _ = qa.possible_nonbase_resolution(row)
        self.assertEqual(classification, "route_to_non_base_wage")
        self.assertEqual(detected, "overtime")

    def test_distinct_period_and_schedule_cell_resolution(self) -> None:
        rows = [
            quant(
                compensation_type="percentage_increase",
                annual_salary="",
                salary_value="",
                percentage_increase="2%",
                effective_date="",
                reason_code="WAGE_2025",
            ),
            quant(
                compensation_type="percentage_increase",
                annual_salary="",
                salary_value="",
                percentage_increase="3%",
                effective_date="",
                reason_code="WAGE_2026",
            ),
        ]
        self.assertEqual(qa.conflict_resolution(rows)[0], "distinct_effective_period")
        for row in rows:
            row["reason_code"] = "BASE" + row["percentage_increase"].replace("%", "")
        self.assertEqual(qa.conflict_resolution(rows)[0], "distinct_schedule_cell")

    def test_under_specified_conflict_fails_closed(self) -> None:
        rows = [quant(annual_salary="50000"), quant(annual_salary="51000")]
        self.assertEqual(
            qa.conflict_resolution(rows)[0],
            "insufficient_evidence_needs_review",
        )

    def test_rerouted_record_preserves_source_id_and_pointer(self) -> None:
        row = {
            **quant(
                compensation_type="other",
                annual_salary="",
                salary_value="",
                rate_value="$500 stipend",
                reason_code="CERT_STIPEND",
            ),
            "quantitative_observation_id": "qobs_test",
            "extraction_case_id": "case_test",
            "document_identity_id": "doc_test",
            "text_table_detection_id": "ttd_test",
            "source_review_id": "sr_test",
            "candidate_queue_row_id": "cq_test",
            "state": "ZZ",
            "municipality": "Testville",
            "government_name": "City of Testville",
            "unit_type": "police",
            "candidate_source_type": "cba",
            "contract_period_start": "2025",
            "contract_period_end": "2027",
            "page_number": "2",
            "bounded_evidence_pointer": "local.pdf#page=2",
            "confidence": "high",
            "qa_status": "needs_review",
        }
        created = qa.make_nonbase_from_quant(row, "stipend", "qares_test")
        self.assertEqual(created["source_quantitative_observation_id"], "qobs_test")
        self.assertEqual(created["bounded_evidence_pointer"], "local.pdf#page=2")
        self.assertEqual(created["active_in_corrected_lane"], "true")

    def test_no_network_or_gabriel_code_path(self) -> None:
        source = RUNNER.read_text(encoding="utf-8")
        for forbidden in (
            "requests.",
            "httpx.",
            "urllib.request",
            "openai",
            "gabriel.call",
        ):
            self.assertNotIn(forbidden, source.lower())

    def test_dry_run_writes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "out"
            fake = {
                "summary": {"review_rows_processed": 187},
                "decision": {"scale_1000_recommendation": "recommend_1000_document_extraction"},
            }
            with mock.patch.object(qa, "resolve", return_value=fake) as resolver:
                with mock.patch.object(
                    sys,
                    "argv",
                    ["runner", "--source-dir", temp, "--output-dir", str(output), "--dry-run"],
                ):
                    self.assertEqual(qa.main(), 0)
            self.assertFalse(output.exists())
            self.assertFalse(resolver.call_args.kwargs["write_outputs"])

    def test_resolution_vocabularies_are_closed(self) -> None:
        self.assertEqual(len(qa.CONFLICT_CLASSES), 7)
        self.assertEqual(len(qa.NONBASE_REVIEW_CLASSES), 5)
        self.assertIn("true_conflict_unresolved", qa.CONFLICT_CLASSES)
        self.assertIn("route_to_non_base_wage", qa.NONBASE_REVIEW_CLASSES)

    def test_frozen_queue_resolves_end_to_end_without_input_mutation(self) -> None:
        required = [
            qa.REVIEW,
            qa.PACKET,
            qa.SELECTION,
            qa.DECISION,
            qa.QUANT,
            qa.QUAL,
            qa.MIXED,
            qa.NONBASE,
            qa.REFERENCE,
        ]
        before = {name: qa.sha_file(qa.SOURCE_DIR / name) for name in required}
        with tempfile.TemporaryDirectory() as temp:
            result = qa.resolve(qa.SOURCE_DIR, Path(temp), write_outputs=True)
            self.assertEqual(len(result["resolutions"]), 187)
            self.assertTrue(result["decision"]["integrity_qa_pass"])
            self.assertTrue(result["decision"]["scale_qa_pass"])
            self.assertLessEqual(
                result["decision"]["unresolved_quantitative_conflict_rate"],
                0.02,
            )
            self.assertEqual(
                result["decision"]["unresolved_base_non_base_contamination_count"],
                0,
            )
            with (
                Path(temp) / "compensation_extraction_500_targeted_qa_resolutions.csv"
            ).open(newline="", encoding="utf-8") as handle:
                resolutions = list(csv.DictReader(handle))
            self.assertEqual(
                sum(row["review_type"] == "possible_non_base_wage_in_quantitative_lane" for row in resolutions),
                102,
            )
            self.assertTrue(
                all(
                    row["resolution_classification"] == "route_to_non_base_wage"
                    for row in resolutions
                    if row["review_type"] == "possible_non_base_wage_in_quantitative_lane"
                )
            )
        after = {name: qa.sha_file(qa.SOURCE_DIR / name) for name in required}
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main(verbosity=2)
