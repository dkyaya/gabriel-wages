#!/usr/bin/env python3
"""Regression checks for the bounded GitHub Pages deployment repair."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import build_dashboard_data as dashboard


ROOT = Path(__file__).resolve().parent.parent


def manifest_row(path: str, *, size: int = 4, digest: str = "a" * 64) -> dict[str, str]:
    return {
        "source_review_download_id": "source-001",
        "retained_file_path": path,
        "retained_file_size_bytes": str(size),
        "retained_file_sha256": digest,
    }


class DashboardPagesDeploymentRepairTests(unittest.TestCase):
    def test_clean_checkout_accepts_valid_durable_manifest_without_ignored_binary(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository_root = Path(directory)
            retained_root = repository_root / "analysis" / "retained_sources"
            audit = dashboard.validate_git_ignored_retained_manifest(
                [manifest_row("analysis/retained_sources/source-001.pdf")],
                retained_root=retained_root,
                repository_root=repository_root,
            )
        self.assertTrue(audit["manifest_metadata_valid"])
        self.assertFalse(audit["local_files_checked"])
        self.assertTrue(audit["local_files_valid_when_present"])

    def test_local_checkout_still_checks_present_retained_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository_root = Path(directory)
            retained_root = repository_root / "analysis" / "retained_sources"
            retained_root.mkdir(parents=True)
            source = retained_root / "source-001.pdf"
            source.write_bytes(b"test")
            audit = dashboard.validate_git_ignored_retained_manifest(
                [manifest_row("analysis/retained_sources/source-001.pdf")],
                retained_root=retained_root,
                repository_root=repository_root,
            )
            bad_size = dashboard.validate_git_ignored_retained_manifest(
                [manifest_row("analysis/retained_sources/source-001.pdf", size=5)],
                retained_root=retained_root,
                repository_root=repository_root,
            )
        self.assertTrue(audit["local_files_checked"])
        self.assertTrue(audit["local_files_valid_when_present"])
        self.assertFalse(bad_size["local_files_valid_when_present"])

    def test_manifest_rejects_outside_path_and_invalid_hash(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository_root = Path(directory)
            retained_root = repository_root / "analysis" / "retained_sources"
            audit = dashboard.validate_git_ignored_retained_manifest(
                [manifest_row("analysis/outside.pdf", digest="not-a-sha256")],
                retained_root=retained_root,
                repository_root=repository_root,
            )
        self.assertFalse(audit["manifest_metadata_valid"])

    def test_current_dashboard_contract(self) -> None:
        phase = json.loads((ROOT / "docs/dashboard/data/project_phase_summary.json").read_text())
        expected = {
            "actual_scout_covered_municipalities": 16887,
            "broad_state_4x2500_source_review_queue_count": 3950,
            "broad_state_4x2500_source_review_retained_count": 3672,
            "broad_state_4x2500_source_review_retained_pdf_count": 3248,
            "broad_state_4x2500_source_review_retained_html_count": 350,
            "broad_state_4x2500_source_review_retained_other_count": 74,
            "broad_state_4x2500_pdf_text_readiness_text_extraction_ready_count": 2940,
            "broad_state_4x2500_pdf_text_readiness_parse_pdf_ready_count": 2577,
            "broad_state_4x2500_pdf_text_readiness_html_ready_count": 291,
            "broad_state_4x2500_pdf_text_readiness_other_ready_count": 72,
            "broad_state_4x2500_pdf_text_readiness_ocr_later_count": 601,
        }
        for field, value in expected.items():
            self.assertEqual(phase[field], value)
        self.assertEqual(phase["dashboard_map_filter"], "scout_coverage_rate_only")
        self.assertFalse(phase["global_analysis_readiness"])
        self.assertEqual(phase["wage_gap_analysis_readiness"], "blocked_pending_normalization")
        self.assertEqual(phase["causal_analysis_readiness"], "blocked_pending_matched_structure")
        extraction_summary_path = (
            ROOT / "docs/analysis/compensation_extraction/"
            "BROAD-STATE-4X2500-TEXT-EXTRACTION-2026-07-30/text_extraction_summary.json"
        )
        if extraction_summary_path.exists():
            extraction = json.loads(extraction_summary_path.read_text())
            self.assertTrue(phase["broad_state_4x2500_text_extraction_available"])
            self.assertEqual(phase["broad_state_4x2500_text_extraction_queue_count"], 2940)
            self.assertEqual(
                phase["broad_state_4x2500_text_extraction_ok_count"],
                extraction["extraction_status_counts"]["extracted_ok"],
            )
            self.assertEqual(
                phase["broad_state_4x2500_text_extraction_span_ready_count"],
                extraction["span_extraction_ready_count"],
            )
            span_summary_path = (
                ROOT / "docs/analysis/compensation_extraction/"
                "BROAD-STATE-4X2500-SPAN-EXTRACTION-2026-07-30/span_extraction_summary.json"
            )
            if span_summary_path.exists():
                span = json.loads(span_summary_path.read_text())
                self.assertTrue(phase["broad_state_4x2500_span_extraction_available"])
                self.assertEqual(phase["broad_state_4x2500_span_extraction_queue_count"], 2795)
                self.assertEqual(phase["broad_state_4x2500_span_candidate_count"], span["total_span_candidate_count"])
                self.assertEqual(phase["broad_state_4x2500_span_rating_ready_count"], span["span_rating_ready_count"])
                rating_summary_path = (
                    ROOT / "docs/analysis/compensation_extraction/"
                    "BROAD-STATE-4X2500-SPAN-RATING-AND-DASHBOARD-CLEANUP-2026-07-30/"
                    "span_rating_summary.json"
                )
                if rating_summary_path.exists():
                    rating = json.loads(rating_summary_path.read_text())
                    self.assertTrue(phase["broad_state_4x2500_span_rating_available"])
                    self.assertEqual(phase["broad_state_4x2500_span_rating_queue_count"], 18612)
                    self.assertEqual(phase["rating_valid_count"], rating["valid_rating_count"])
                    self.assertEqual(phase["rating_quarantine_count"], rating["quarantine_rating_count"])
                    self.assertEqual(
                        phase["next_task"],
                        "BROAD-STATE-4X2500-RATING-INGEST-CODIFY-2026-07-30",
                    )
                else:
                    self.assertIn("BROAD-STATE-4X2500-SPAN-RATING-2026-07-30", phase["next_task"])
            else:
                self.assertIn("BROAD-STATE-4X2500-SPAN-EXTRACTION-2026-07-30", phase["next_task"])
        else:
            self.assertIn("BROAD-STATE-4X2500-TEXT-EXTRACTION-2026-07-30", phase["next_task"])

    def test_pages_workflow_uses_actions_artifact_and_correct_base(self) -> None:
        workflow = (ROOT / ".github/workflows/deploy-dashboard.yml").read_text()
        vite = (ROOT / "docs/dashboard/vite.config.js").read_text()
        self.assertIn("actions/upload-pages-artifact@v4", workflow)
        self.assertIn("actions/deploy-pages@v4", workflow)
        self.assertIn("path: docs/dashboard/dist", workflow)
        self.assertIn("DASHBOARD_BASE_PATH: /gabriel-wages/", workflow)
        self.assertIn('"/gabriel-wages/"', vite)


if __name__ == "__main__":
    unittest.main(verbosity=2)
