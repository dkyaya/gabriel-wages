#!/usr/bin/env python3
"""Bounded invariant tests for the 3,950-row source-review/download wave."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import unittest
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs/analysis/compensation_extraction/BROAD-STATE-4X2500-SOURCE-REVIEW-DOWNLOAD-2026-07-30"
ARTIFACT_ROOT = ROOT / "artifacts/local_retained_sources/broad_state_4x2500_source_review_download_2026-07-30"


def read_json(name: str):
    return json.loads((OUTPUT / name).read_text(encoding="utf-8"))


def read_csv(name: str):
    with (OUTPUT / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class SourceReviewDownloadTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.summary = read_json("source_review_download_summary.json")
        cls.merged = read_csv("merged_source_review_results.csv")
        cls.retained = read_csv("retained_source_manifest.csv")

    def test_queue_lane_priority_and_terminal_reconciliation(self):
        self.assertEqual(len(self.merged), 3950)
        self.assertEqual(len({row["source_review_download_id"] for row in self.merged}), 3950)
        self.assertEqual(Counter(row["source_review_lane_id"] for row in self.merged), Counter({
            "source_review_lane_001": 988,
            "source_review_lane_002": 988,
            "source_review_lane_003": 987,
            "source_review_lane_004": 987,
        }))
        self.assertEqual(Counter(row["priority_bucket"] for row in self.merged), Counter({
            "high_priority_verification_ready": 2920,
            "medium_priority_verification_ready": 918,
            "low_priority_verification_ready": 112,
        }))
        self.assertEqual(sum(self.summary["terminal_status_counts"].values()), 3950)

    def test_retained_storage_hash_size_and_ignore(self):
        self.assertEqual(len(self.retained), self.summary["retained_source_count"])
        for row in self.retained:
            path = ROOT / row["retained_local_artifact_path"]
            self.assertTrue(path.is_file(), path)
            self.assertTrue(path.is_relative_to(ARTIFACT_ROOT))
            self.assertEqual(path.stat().st_size, int(row["retained_file_size_bytes"]))
            self.assertEqual(file_sha256(path), row["retained_file_sha256"])
        ignored = subprocess.run(
            ["git", "check-ignore", str(ARTIFACT_ROOT.relative_to(ROOT))],
            cwd=ROOT, check=False, capture_output=True, text=True,
        )
        self.assertEqual(ignored.returncode, 0)
        tracked = subprocess.run(
            ["git", "ls-files", str(ARTIFACT_ROOT.relative_to(ROOT))],
            cwd=ROOT, check=True, capture_output=True, text=True,
        ).stdout.strip()
        self.assertFalse(tracked)

    def test_forbidden_actions_and_global_gate(self):
        audit = read_json("forbidden_action_audit.json")
        self.assertTrue(audit["passed"])
        for key in ("text_extractions", "ocr_runs", "rating_runs", "ingestion_runs", "codification_runs", "wage_gap_calculations", "regressions", "final_causal_claims"):
            self.assertEqual(audit[key], 0)
        self.assertFalse(self.summary["global_analysis_readiness"])
        self.assertEqual(self.summary["dashboard_map_filter"], "total_scout_coverage_only")
        self.assertEqual(self.summary["dashboard_scout_covered_municipalities"], 16887)

    def test_dashboard_current_stage(self):
        phase = json.loads((ROOT / "docs/dashboard/data/project_phase_summary.json").read_text(encoding="utf-8"))
        self.assertTrue(phase["broad_state_4x2500_source_review_download_available"])
        self.assertEqual(phase["broad_state_4x2500_source_review_queue_count"], 3950)
        self.assertEqual(phase["broad_state_4x2500_source_review_retained_count"], len(self.retained))
        self.assertFalse(phase["global_analysis_readiness"])
        self.assertEqual(phase["global_wage_gap_analysis_readiness"], "blocked_pending_normalization")
        self.assertEqual(phase["global_causal_analysis_readiness"], "blocked_pending_matched_structure")


if __name__ == "__main__":
    unittest.main()
