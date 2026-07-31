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
        self.assertIn(
            phase["wage_gap_analysis_readiness"],
            {
                "blocked_pending_normalization",
                "bounded_local_documentary_candidates_require_final_manual_validation",
                "bounded_local_documentary_validation_complete_final_estimation_blocked",
                "bounded_local_documentary_examples_only_final_estimation_blocked",
                "bounded_growth_continuity_only_final_estimation_blocked",
            },
        )
        self.assertEqual(phase["validated_bounded_wage_differential_candidate_count"], 1)
        self.assertEqual(phase["conditional_bounded_wage_differential_candidate_count"], 3)
        self.assertEqual(phase["rejected_bounded_wage_differential_candidate_count"], 0)
        self.assertIn(
            phase["causal_analysis_readiness"],
            {"blocked_pending_matched_structure", "blocked_pending_stronger_causal_design"},
        )
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
                    ingest_summary_path = (
                        ROOT / "docs/analysis/compensation_extraction/"
                        "BROAD-STATE-4X2500-RATING-INGEST-CODIFY-PI-EVIDENCE-2026-07-30/"
                        "rating_ingest_codify_summary.json"
                    )
                    if ingest_summary_path.exists():
                        ingest = json.loads(ingest_summary_path.read_text())
                        self.assertTrue(phase["broad_state_4x2500_rating_ingest_codify_available"])
                        self.assertEqual(phase["rating_valid_count"], 18554)
                        self.assertEqual(phase["rating_quarantine_count"], 58)
                        self.assertEqual(phase["codified_record_count"], 18554)
                        self.assertEqual(
                            phase["careful_claim_candidate_count"],
                            ingest["careful_claim_candidate_count"],
                        )
                        normalization_summary_path = (
                            ROOT / "docs/analysis/compensation_extraction/"
                            "BROAD-STATE-4X2500-NORMALIZATION-MATCHED-STRUCTURE-PARAPHRASE-REPAIR-2026-07-30/"
                            "normalization_matching_paraphrase_repair_summary.json"
                        )
                        if normalization_summary_path.exists():
                            normalization = json.loads(normalization_summary_path.read_text())
                            self.assertTrue(phase["broad_state_4x2500_normalization_matching_available"])
                            self.assertEqual(phase["normalized_quantitative_record_count"], 11548)
                            self.assertEqual(
                                phase["matched_safety_non_safety_cycle_candidate_count"],
                                normalization["matched_safety_non_safety_cycle_candidate_count"],
                            )
                            rescue_summary_path = (
                                ROOT / "docs/analysis/compensation_extraction/"
                                "BROAD-STATE-4X2500-NORMALIZATION-RESCUE-GAP-GROWTH-CLAIMS-2026-07-30/"
                                "normalization_rescue_gap_growth_summary.json"
                            )
                            if rescue_summary_path.exists():
                                rescue = json.loads(rescue_summary_path.read_text())
                                self.assertTrue(phase["broad_state_4x2500_normalization_rescue_available"])
                                bounded_validation_path = (
                                    ROOT / "docs/analysis/compensation_extraction/"
                                    "BROAD-STATE-4X2500-BOUNDED-WAGE-DIFFERENTIAL-VALIDATION-2026-07-30/"
                                    "bounded_wage_differential_validation_summary.json"
                                )
                                if bounded_validation_path.exists():
                                    self.assertTrue(phase["broad_state_4x2500_bounded_wage_validation_available"])
                                    pi_report_path = (
                                        ROOT / "docs/analysis/compensation_extraction/"
                                        "BROAD-STATE-4X2500-PI-REPORT-DRAFT-2026-07-30/"
                                        "pi_report_draft_manifest.json"
                                    )
                                    if pi_report_path.exists():
                                        self.assertTrue(phase["broad_state_4x2500_pi_report_draft_available"])
                                        self.assertEqual(phase["pi_report_careful_claim_count"], 18)
                                        pi_report_v2_path = (
                                            ROOT / "docs/analysis/compensation_extraction/"
                                            "BROAD-STATE-4X2500-PI-REPORT-COMPARISON-MECHANISM-REPAIR-2026-07-30/"
                                            "comparison_mechanism_repair_manifest.json"
                                        )
                                        if pi_report_v2_path.exists():
                                            self.assertTrue(phase["broad_state_4x2500_pi_report_v2_available"])
                                            self.assertEqual(phase["pi_report_v2_claim_count"], 16)
                                            self.assertTrue(phase["pi_report_v2_all_nine_critiques_answered"])
                                            pi_report_final_path = (
                                                ROOT / "docs/analysis/compensation_extraction/"
                                                "BROAD-STATE-4X2500-PI-REPORT-FINALIZE-2026-07-30/"
                                                "pi_report_final_send_ready_manifest.json"
                                            )
                                            if pi_report_final_path.exists():
                                                self.assertTrue(phase["broad_state_4x2500_pi_report_final_available"])
                                                growth_continuity_path = (
                                                    ROOT / "docs/analysis/compensation_extraction/"
                                                    "BROAD-STATE-4X2500-MECHANISM-ATTRIBUTED-WAGE-GROWTH-"
                                                    "CONTINUITY-2026-07-31/wage_growth_continuity_manifest.json"
                                                )
                                                if growth_continuity_path.exists():
                                                    growth_review_path = (
                                                        ROOT / "docs/analysis/compensation_extraction/"
                                                        "BROAD-STATE-WAGE-GROWTH-CONTINUITY-REVIEW-2026-07-31/"
                                                        "wage_growth_continuity_review_manifest.json"
                                                    )
                                                    if growth_review_path.exists():
                                                        remaining_infrastructure_path = (
                                                            ROOT / "docs/analysis/compensation_extraction/"
                                                            "BROAD-STATE-REMAINING-MUNICIPALITIES-5LANE-"
                                                            "SCOUT-INFRASTRUCTURE-2026-07-31/"
                                                            "remaining_municipality_scout_infrastructure_manifest.json"
                                                        )
                                                        if remaining_infrastructure_path.exists():
                                                            remaining_live_path = (
                                                                ROOT / "docs/analysis/compensation_extraction/"
                                                                "BROAD-STATE-REMAINING-MUNICIPALITIES-5LANE-"
                                                                "LIVE-SCOUT-2026-07-31/"
                                                                "remaining_municipalities_live_scout_manifest.json"
                                                            )
                                                            if remaining_live_path.exists():
                                                                self.assertEqual(
                                                                    phase["current_phase"],
                                                                    "remaining-municipality 5-lane live scout blocked at backend preflight",
                                                                )
                                                                self.assertEqual(
                                                                    phase["next_task"],
                                                                    "BROAD-STATE-REMAINING-MUNICIPALITIES-5LANE-"
                                                                    "LIVE-SCOUT-RETRY-2026-08-01",
                                                                )
                                                                self.assertTrue(
                                                                    phase["remaining_municipality_5lane_live_scout_preflight_failed"]
                                                                )
                                                                self.assertEqual(phase["accepted_terminal_outcomes"], 0)
                                                            else:
                                                                self.assertEqual(
                                                                    phase["current_phase"],
                                                                    "Remaining-municipality 5-lane scout infrastructure ready",
                                                                )
                                                                self.assertEqual(
                                                                    phase["next_task"],
                                                                    "BROAD-STATE-REMAINING-MUNICIPALITIES-5LANE-"
                                                                    "LIVE-SCOUT-2026-07-31",
                                                                )
                                                            self.assertEqual(
                                                                phase["planned_remaining_scout_lane_sizes"],
                                                                [3741, 3741, 3740, 3740, 3740],
                                                            )
                                                        else:
                                                            self.assertEqual(
                                                                phase["current_phase"],
                                                                "Wage-growth continuity review complete",
                                                            )
                                                            self.assertEqual(
                                                                phase["next_task"],
                                                                "BROAD-STATE-REMAINING-MUNICIPALITIES-5LANE-"
                                                                "SCOUT-INFRASTRUCTURE-2026-07-31",
                                                            )
                                                        self.assertEqual(
                                                            phase["remaining_unscouted_eligible_municipality_count"],
                                                            18702,
                                                        )
                                                    else:
                                                        self.assertEqual(
                                                            phase["current_phase"],
                                                            "Mechanism-attributed wage-growth continuity complete",
                                                        )
                                                        self.assertEqual(
                                                            phase["next_task"],
                                                            "BROAD-STATE-WAGE-GROWTH-CONTINUITY-REVIEW-2026-07-31",
                                                        )
                                                else:
                                                    self.assertEqual(phase["current_phase"], "PI report final complete")
                                                    self.assertEqual(
                                                        phase["next_task"],
                                                        "BROAD-STATE-4X2500-PI-REPORT-SEND-PACKAGE-2026-07-30",
                                                    )
                                                self.assertEqual(phase["pi_report_final_claim_count"], 16)
                                                self.assertTrue(phase["pi_report_final_number_crosscheck_passed"])
                                                self.assertTrue(phase["pi_report_final_forbidden_claim_audit_passed"])
                                                published_pdf = (
                                                    ROOT
                                                    / "docs/dashboard/public/reports/"
                                                    "pi_report_final_2026-07-30/"
                                                    "pi_report_final_2026-07-30.pdf"
                                                )
                                                if published_pdf.exists():
                                                    self.assertTrue(
                                                        phase[
                                                            "broad_state_4x2500_pi_report_pdf_published"
                                                        ]
                                                    )
                                                    self.assertEqual(
                                                        phase["current_report_path"],
                                                        "reports/pi_report_final_2026-07-30/"
                                                        "pi_report_final_2026-07-30.pdf",
                                                    )
                                            else:
                                                self.assertEqual(
                                                    phase["current_phase"],
                                                    "PI report v2 comparison/mechanism repair complete",
                                                )
                                                self.assertEqual(
                                                    phase["next_task"],
                                                    "BROAD-STATE-4X2500-PI-REPORT-FINALIZE-2026-07-30",
                                                )
                                        else:
                                            self.assertEqual(phase["current_phase"], "PI report draft complete")
                                            self.assertEqual(
                                                phase["next_task"],
                                                "BROAD-STATE-4X2500-PI-REPORT-REVIEW-FINALIZE-2026-07-30",
                                            )
                                    else:
                                        self.assertEqual(phase["current_phase"], "Bounded wage-differential validation complete")
                                else:
                                    self.assertEqual(
                                        phase["current_phase"],
                                        "Normalization rescue and bounded claims complete",
                                    )
                                self.assertEqual(
                                    phase["current_bounded_wage_differential_candidate_count"],
                                    rescue["current_bounded_wage_differential_candidate_count"],
                                )
                                self.assertFalse(phase["global_analysis_readiness"])
                            else:
                                self.assertEqual(phase["current_phase"], "Normalization and matched structure complete")
                            if not phase.get("broad_state_4x2500_pi_report_draft_available"):
                                self.assertEqual(
                                    phase["next_task"],
                                    "BROAD-STATE-4X2500-PI-REPORT-DRAFT-2026-07-30",
                                )
                        else:
                            self.assertEqual(
                                phase["current_phase"],
                                "Rating ingestion/codification complete",
                            )
                            self.assertEqual(
                                phase["next_task"],
                                "BROAD-STATE-4X2500-NORMALIZATION-MATCHED-STRUCTURE-2026-07-30",
                            )
                    else:
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
