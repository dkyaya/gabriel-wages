#!/usr/bin/env python3
"""Bounded regression tests for the remaining-municipality extractor adapter."""

import importlib.util
import sys
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location(
    "remaining_text_extraction", SCRIPTS / "run_remaining_municipality_text_extraction.py"
)
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MOD)


class RemainingTextExtractionTests(unittest.TestCase):
    def test_lane_assignment_exact_disjoint_and_balanced(self):
        rows = []
        for status, count in MOD.APPROVED.items():
            for index in range(count):
                rows.append({
                    "readiness_id": f"{status}-{index}",
                    "primary_readiness_status": status,
                    "priority_bucket": "high_priority_verification_ready",
                    "source_family_hint": "test",
                    "state": "PA",
                })
        lanes = MOD.assign_lanes(rows)
        self.assertEqual([len(lanes[lane]) for lane in MOD.LANES], [512, 512, 512, 511, 511])
        identifiers = [row["readiness_id"] for lane in lanes.values() for row in lane]
        self.assertEqual(len(identifiers), 2558)
        self.assertEqual(len(set(identifiers)), 2558)

    def test_quality_statuses_follow_current_contract(self):
        pdf = {"primary_readiness_status": "parse_text_pdf_ready", "page_count": "10"}
        html = {"primary_readiness_status": "html_text_ready", "page_count": ""}
        self.assertEqual(MOD.quality_status(pdf, "short")[0], "extracted_empty_or_too_low_text")
        self.assertEqual(MOD.quality_status(pdf, "word " * 50)[0], "extracted_low_text_but_usable")
        self.assertEqual(MOD.quality_status(html, "word " * 60, 40)[0], "extracted_low_text_but_usable")
        self.assertEqual(MOD.quality_status(pdf, "wage schedule " * 1000)[0], "extracted_ok")

    def test_page_accounting_contract(self):
        self.assertEqual(sum(MOD.LANES.values()), MOD.EXPECTED)
        self.assertEqual(sum(MOD.APPROVED.values()), MOD.EXPECTED)
        self.assertEqual(MOD.READY_STATUSES, {"extracted_ok"})
        self.assertIn("extracted_low_text_but_usable", MOD.SUCCESS_STATUSES)


if __name__ == "__main__":
    unittest.main()
