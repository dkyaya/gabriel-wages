#!/usr/bin/env python3
"""Regression tests for the broad-state 4x2500 readiness package."""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import unittest
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/run_broad_state_4x2500_pdf_text_readiness.py"
SPEC = importlib.util.spec_from_file_location("b4x2500_readiness", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


class ReadinessPackageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.output = MODULE.OUTPUT_DIR

    def test_controlled_status_contract_and_probe_bounds(self) -> None:
        self.assertEqual(
            MODULE.READY_STATUSES,
            {"parse_text_pdf_ready", "html_text_ready", "other_document_text_ready"},
        )
        self.assertEqual(len(MODULE.CONTROLLED_STATUSES), 11)
        self.assertEqual(MODULE.MAX_PDF_PROBE_PAGES, 3)
        self.assertEqual(MODULE.MAX_HTML_PROBE_BYTES, 256 * 1024)
        self.assertEqual(MODULE.MAX_TEXT_PASS_BYTES, 20 * 1024 * 1024)
        self.assertEqual(MODULE.MAX_TEXT_PASS_PAGES, 500)

    def test_locked_queue_and_lane_hashes(self) -> None:
        locked = rows(self.output / "readiness_locked_queue.csv")
        manifest = json.loads((self.output / "pdf_text_readiness_manifest.json").read_text())
        self.assertEqual(len(locked), 3672)
        self.assertEqual(len({row["source_review_download_id"] for row in locked}), 3672)
        self.assertEqual(Counter(row["source_type"] for row in locked), MODULE.EXPECTED_TYPES)
        self.assertEqual(Counter(row["lane_id"] for row in locked), MODULE.LANE_COUNTS)
        for lane in MODULE.LANES:
            path = self.output / f"{lane}_queue.csv"
            self.assertEqual(len(rows(path)), 918)
            self.assertEqual(digest(path), manifest["lane_manifests"][lane]["csv_sha256"])

    def test_completed_package_reconciles_when_present(self) -> None:
        summary_path = self.output / "pdf_text_readiness_summary.json"
        if not summary_path.exists():
            self.skipTest("lanes not yet merged")
        summary = json.loads(summary_path.read_text())
        merged = rows(self.output / "merged_pdf_text_readiness_results.csv")
        ready = rows(self.output / "text_extraction_ready_queue.csv")
        self.assertEqual(len(merged), 3672)
        self.assertEqual(sum(summary["primary_readiness_status_counts"].values()), 3672)
        self.assertEqual(len(ready), summary["text_extraction_ready_count"])
        self.assertTrue(all(row["primary_readiness_status"] in MODULE.READY_STATUSES for row in ready))
        self.assertTrue(all(row["full_text_persisted_flag"] == "false" for row in merged))
        self.assertTrue(all(row["ocr_run_flag"] == "false" for row in merged))

    def test_no_source_payload_written_to_output(self) -> None:
        forbidden = {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".rtf", ".html", ".htm", ".zip"}
        offenders = [path for path in self.output.rglob("*") if path.is_file() and path.suffix.casefold() in forbidden]
        self.assertEqual(offenders, [])

    def test_dashboard_contract_when_built(self) -> None:
        summary_path = self.output / "pdf_text_readiness_summary.json"
        if not summary_path.exists():
            self.skipTest("readiness summary not yet merged")
        phase = json.loads((ROOT / "docs/dashboard/data/project_phase_summary.json").read_text())
        pdf_status = json.loads((ROOT / "docs/dashboard/data/pdf_readiness_status_summary.json").read_text())
        reports = json.loads((ROOT / "docs/dashboard/data/reports_index.json").read_text())
        self.assertTrue(phase["broad_state_4x2500_pdf_text_readiness_available"])
        self.assertEqual(phase["broad_state_4x2500_pdf_text_readiness_text_extraction_ready_count"], 2940)
        self.assertEqual(phase["current_scout_covered"], 16887)
        self.assertEqual(phase["actual_scout_covered_municipalities"], 35574)
        self.assertEqual(phase["dashboard_map_filter"], "scout_coverage_rate_only")
        self.assertFalse(phase["global_analysis_readiness"])
        self.assertIn(phase["wage_gap_analysis_readiness"], {"blocked_pending_normalization", "bounded_growth_continuity_only_final_estimation_blocked"})
        self.assertIn(phase["causal_analysis_readiness"], {"blocked_pending_matched_structure", "blocked_pending_stronger_causal_design"})
        self.assertEqual(pdf_status["pdf_readiness_phase"], "broad_state_4x2500_3672_completed")
        current = [report for report in reports["reports"] if report["current"]]
        self.assertEqual(len(current), 1)
        self.assertEqual(current[0]["id"], "broad-state-4x2500-pi-report-final-2026-07-30")


if __name__ == "__main__":
    unittest.main(verbosity=2)
