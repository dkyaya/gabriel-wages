#!/usr/bin/env python3
"""Bounded regression tests for the 4x2500 non-OCR text extractor."""

import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("run_broad_state_4x2500_text_extraction.py")
SPEC = importlib.util.spec_from_file_location("extractor", SCRIPT)
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MOD)


class ExtractionTests(unittest.TestCase):
    def test_html_removes_navigation_and_scripts(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "page.html"
            path.write_text("<nav>MENU</nav><script>SECRET</script><article><h1>Pay plan</h1><p>Salary schedule language.</p></article>")
            text, method, links = MOD.extract_html(path)
            self.assertIn("Pay plan", text)
            self.assertIn("Salary schedule", text)
            self.assertNotIn("MENU", text)
            self.assertNotIn("SECRET", text)
            self.assertEqual(method, "stdlib_htmlparser_visible_text_cleanup")
            self.assertEqual(links, 0)

    def test_quality_labels_are_controlled(self):
        pdf = {"primary_readiness_status": "parse_text_pdf_ready", "page_count": "10"}
        html = {"primary_readiness_status": "html_text_ready", "page_count": ""}
        self.assertEqual(MOD.quality_status(pdf, "short")[0], "extracted_empty")
        self.assertEqual(MOD.quality_status(pdf, "word " * 50)[0], "extracted_low_density")
        self.assertEqual(MOD.quality_status(html, "word " * 60, 40)[0], "html_noisy_or_boilerplate")
        self.assertTrue(set(MOD.STATUSES).issuperset({MOD.quality_status(pdf, "word " * 1000)[0]}))

    def test_fixed_width_separators_are_not_repeated_garbage(self):
        pdf = {"primary_readiness_status": "parse_text_pdf_ready", "page_count": "1"}
        table_text = ("salary schedule\n" + "_" * 120 + "\n" + "-" * 120 + "\n") * 3
        self.assertEqual(MOD.quality_status(pdf, table_text)[0], "extracted_ok")
        self.assertEqual(
            MOD.quality_status(pdf, "A" * 100 + " wage schedule " * 20)[0],
            "extracted_suspected_bad_text",
        )

    def test_lane_assignment_is_exact_and_unique(self):
        rows = []
        for status, count in MOD.APPROVED.items():
            for index in range(count):
                rows.append({"readiness_id": f"{status}-{index}", "primary_readiness_status": status,
                             "priority_bucket": "high", "source_family_hint": "test", "state": "MA"})
        lanes = MOD.assign_lanes(rows)
        self.assertEqual([len(lanes[name]) for name in MOD.LANES], [735] * 4)
        ids = [row["readiness_id"] for lane in lanes.values() for row in lane]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(ids), 2940)


if __name__ == "__main__":
    unittest.main()
