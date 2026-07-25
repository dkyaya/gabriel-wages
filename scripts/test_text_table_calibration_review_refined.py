#!/usr/bin/env python3
"""Synthetic offline tests for refined visual/table calibration gating."""

from __future__ import annotations

import argparse
import csv
import hashlib
import socket
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

import review_text_table_calibration_subset as reviewer  # noqa: E402
from prepare_text_table_calibration_subset import OUTPUT_FIELDS  # noqa: E402


IMMUTABLE_FILES = (
    ROOT
    / "docs/analysis/text_table_calibration"
    / "TEXT-TABLE-CALIBRATION-SUBSET1-150-2026-07-24"
    / "calibration_review_input.csv",
    ROOT
    / "docs/analysis/text_table_calibration"
    / "TEXT-TABLE-CALIBRATION-SUBSET1-REVIEW1-2026-07-24"
    / "calibration_reviewed.csv",
    ROOT
    / "docs/analysis/text_table_calibration"
    / "TEXT-TABLE-CALIBRATION-SUBSET1-REVIEW1-2026-07-24"
    / "calibration_review_summary.json",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_csv(
    path: Path,
    rows: list[dict[str, str]],
    fields: list[str],
) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fields,
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def read_row(path: Path) -> dict[str, str]:
    with path.open(newline="", encoding="utf-8") as handle:
        return next(csv.DictReader(handle))


def make_pdf(path: Path, pages: list[list[str]]) -> None:
    pdf = canvas.Canvas(str(path))
    pdf.setFont("Courier", 10)
    for lines in pages:
        y = 760
        for line in lines:
            pdf.drawString(45, y, line)
            y -= 17
        pdf.showPage()
    pdf.save()


def input_row(
    artifact: Path,
    page_count: int,
    candidate_pages: str,
) -> dict[str, str]:
    row = {field: "" for field in OUTPUT_FIELDS}
    row.update(
        {
            "calibration_id": "cal_refined",
            "text_table_detection_id": "ttd_refined",
            "pdf_readiness_id": "pdf_refined",
            "source_review_id": "sr_refined",
            "candidate_queue_row_id": "cq_refined",
            "state": "MA",
            "municipality": "Synthetic",
            "government_name": "Synthetic",
            "unit_type": "police",
            "candidate_source_type": "cba",
            "priority_for_content_review": "p1",
            "source_officialness_rating": "official_municipal",
            "source_relevance_rating": "possible",
            "document_type_rating": "cba_candidate",
            "pdf_page_count": str(page_count),
            "content_artifact_path": str(artifact),
            "wage_table_signal": "likely",
            "contract_period_signal": "likely",
            "table_like_structure_signal": "likely",
            "candidate_wage_pages": candidate_pages,
            "candidate_wage_page_count": (
                str(len(candidate_pages.split(",")))
                if candidate_pages
                else "0"
            ),
            "detection_notes": "synthetic",
            "calibration_round_id": "SYNTHETIC",
            "calibration_selection_rank": "1",
            "calibration_selection_reason": "synthetic",
            "source_review_pilot_id": "SOURCE-REVIEW-SYNTHETIC",
            "page_count_bin": "1_to_10",
            "text_layer_status": "present",
            "wage_table_signal_confidence": "high",
            "contract_period_confidence": "high",
            "candidate_contract_period_text": (
                "Agreement effective 2021 through 2024"
            ),
            "extraction_pilot_priority": "p1",
            "recommended_next_action": "wage_table_extraction_pilot",
            "table_detection_method": (
                "bounded_keyword_numeric_structure_v1"
            ),
            "calibration_status": "not_reviewed",
            "page_hint_precision_label": "unknown",
            "wage_table_present_label": "unknown",
            "wage_table_page_match_label": "unknown",
            "contract_period_present_label": "unknown",
            "contract_period_hint_match_label": "unknown",
            "table_layout_type": "unknown",
            "extraction_complexity_label": "unknown",
            "false_positive_family": "unknown",
            "recommended_extraction_action": "unknown",
            "reviewer_confidence": "unknown",
        }
    )
    return row


def authority_row(row: dict[str, str], artifact: Path) -> dict[str, str]:
    return {
        "text_table_detection_id": row["text_table_detection_id"],
        "pdf_readiness_id": row["pdf_readiness_id"],
        "source_review_id": row["source_review_id"],
        "candidate_queue_row_id": row["candidate_queue_row_id"],
        "content_artifact_path": row["content_artifact_path"],
        "pdf_page_count": row["pdf_page_count"],
        "text_layer_status": row["text_layer_status"],
        "wage_table_signal": row["wage_table_signal"],
        "candidate_wage_pages": row["candidate_wage_pages"],
        "candidate_wage_page_count": row["candidate_wage_page_count"],
        "content_hash": sha256(artifact),
        "content_byte_size": str(artifact.stat().st_size),
        "content_type_observed": "application/pdf",
    }


class RefinedReviewTests(unittest.TestCase):
    def fixture(
        self,
        root: Path,
        pages: list[list[str]],
        *,
        candidate_pages: str = "1",
        render_pages: bool = True,
        render_budget: int = 3,
        navigation_budget: int = 4,
    ) -> argparse.Namespace:
        artifact = root / "fixture.pdf"
        make_pdf(artifact, pages)
        row = input_row(artifact, len(pages), candidate_pages)
        input_path = root / "input.csv"
        authority_path = root / "authority.csv"
        write_csv(input_path, [row], OUTPUT_FIELDS)
        authority = authority_row(row, artifact)
        write_csv(authority_path, [authority], list(authority))
        return argparse.Namespace(
            input_csv=str(input_path),
            output_dir=str(root / "output"),
            review_id="SYNTHETIC-REFINED-REVIEW",
            text_table_ledger_csv=str(authority_path),
            max_rows=None,
            candidate_page_window=1,
            max_pages_per_document=6,
            max_snippet_chars=300,
            no_save_full_text=True,
            dry_run=False,
            review_mode=reviewer.REFINED_REVIEW_MODE,
            render_pages=render_pages,
            max_rendered_pages_per_document=render_budget,
            navigation_page_budget=navigation_budget,
            require_visual_table_confirmation=True,
        )

    def run_case(
        self,
        args: argparse.Namespace,
        *,
        rendered: bool = True,
    ) -> tuple[dict[str, object], dict[str, str]]:
        with mock.patch.object(
            reviewer,
            "render_pdf_page",
            return_value=rendered,
        ):
            summary = reviewer.run(args)
        row = read_row(Path(args.output_dir) / "calibration_reviewed.csv")
        return summary, row

    def test_wage_prose_is_not_a_table(self):
        with tempfile.TemporaryDirectory() as raw:
            args = self.fixture(
                Path(raw),
                [[
                    "ARTICLE 12 WAGES",
                    (
                        "Employees receive a salary increase of 3 percent "
                        "effective in 2024."
                    ),
                    (
                        "The annual adjustment is described in this "
                        "paragraph and is not a schedule."
                    ),
                ]],
            )
            _, row = self.run_case(args)
            self.assertEqual(row["wage_language_present_label"], "yes")
            self.assertEqual(row["visual_table_structure_label"], "prose_only")
            self.assertIn(
                row["extraction_gate_label"],
                {"second_review_required", "fail_exclude"},
            )

    def test_benefits_table_is_not_a_wage_schedule(self):
        with tempfile.TemporaryDirectory() as raw:
            args = self.fixture(
                Path(raw),
                [[
                    "Health Insurance Premium Contribution Table",
                    "Plan A  Employee 100  Employer 200",
                    "Plan B  Employee 150  Employer 250",
                ]],
            )
            _, row = self.run_case(args)
            self.assertEqual(
                row["visual_table_structure_label"],
                "benefits_table",
            )
            self.assertEqual(
                row["wage_schedule_table_confirmed_label"],
                "no",
            )
            self.assertEqual(row["extraction_gate_label"], "fail_exclude")

    def test_classification_without_pay_is_not_a_wage_schedule(self):
        with tempfile.TemporaryDirectory() as raw:
            args = self.fixture(
                Path(raw),
                [[
                    "Classification Roster",
                    "Class Code  Position Title  Status",
                    "101  Police Officer  Active",
                    "102  Police Sergeant  Active",
                ]],
            )
            _, row = self.run_case(args)
            self.assertEqual(
                row["visual_table_structure_label"],
                "classification_only",
            )
            self.assertEqual(
                row["wage_schedule_table_confirmed_label"],
                "no",
            )

    def test_contents_reference_points_to_later_table(self):
        with tempfile.TemporaryDirectory() as raw:
            args = self.fixture(
                Path(raw),
                [
                    [
                        "TABLE OF CONTENTS",
                        "Article 12 Wages  3",
                        "Appendix A Salary Table  5",
                    ],
                    ["General agreement language"],
                    ["Wage article prose only"],
                    ["Appendix introduction"],
                    [
                        "Appendix A Salary Schedule",
                        "Rank  Step 1  Step 2  Step 3",
                        "Officer  50000  52000  54000",
                        "Sergeant  60000  62000  64000",
                    ],
                ],
                candidate_pages="1",
            )
            _, row = self.run_case(args)
            self.assertEqual(
                row["candidate_page_relationship_label"],
                "points_to_later_table",
            )
            self.assertIn("5", row["navigation_references_found"])
            self.assertIn("5", row["navigation_pages_inspected"])
            self.assertEqual(
                row["table_navigation_signal"],
                "appendix_reference",
            )

    def test_confirmed_wage_table_can_pass_high_confidence(self):
        with tempfile.TemporaryDirectory() as raw:
            args = self.fixture(
                Path(raw),
                [[
                    "Salary Schedule",
                    "Rank  Step 1  Step 2  Step 3",
                    "Officer  50000  52000  54000",
                    "Sergeant  60000  62000  64000",
                ]],
            )
            _, row = self.run_case(args)
            self.assertEqual(
                row["visual_table_structure_label"],
                "confirmed_table",
            )
            self.assertEqual(
                row["wage_schedule_table_confirmed_label"],
                "yes",
            )
            self.assertEqual(
                row["extraction_gate_label"],
                "pass_high_confidence",
            )
            self.assertEqual(
                row["visual_confirmation_method"],
                "text_structure_plus_rendered_check",
            )

    def test_refined_mode_preserves_identities_and_immutable_reviews(self):
        with tempfile.TemporaryDirectory() as raw:
            args = self.fixture(
                Path(raw),
                [["Wage article prose with a 3 percent adjustment."]],
            )
            before = {
                str(path): sha256(path)
                for path in IMMUTABLE_FILES
            }
            original = read_row(Path(args.input_csv))
            _, row = self.run_case(args)
            for field in (
                "calibration_id",
                "text_table_detection_id",
                "pdf_readiness_id",
                "source_review_id",
                "candidate_queue_row_id",
            ):
                self.assertEqual(row[field], original[field])
            self.assertEqual(
                before,
                {str(path): sha256(path) for path in IMMUTABLE_FILES},
            )

    def test_render_budget_is_respected(self):
        with tempfile.TemporaryDirectory() as raw:
            args = self.fixture(
                Path(raw),
                [
                    [
                        "Salary Schedule",
                        "Rank  Step 1  Step 2",
                        "Officer  50000  52000",
                        "Sergeant  60000  62000",
                    ]
                    for _ in range(5)
                ],
                candidate_pages="1,2,3,4,5",
                render_budget=2,
            )
            with mock.patch.object(
                reviewer,
                "render_pdf_page",
                return_value=True,
            ) as render:
                reviewer.run(args)
            self.assertLessEqual(render.call_count, 2)

    def test_snippet_cap_and_allowed_values(self):
        with tempfile.TemporaryDirectory() as raw:
            args = self.fixture(
                Path(raw),
                [["Wages and salary language without a table."]],
            )
            args.max_snippet_chars = 80
            _, row = self.run_case(args)
            for field, allowed in reviewer.ALLOWED.items():
                self.assertIn(row[field], allowed)
            for field in (
                "reviewer_notes",
                "extraction_schema_notes",
                "review_status_detail",
                "extraction_gate_reason",
            ):
                self.assertLessEqual(len(row[field]), 80)

    def test_no_network_ocr_or_full_text_outputs(self):
        with tempfile.TemporaryDirectory() as raw:
            args = self.fixture(
                Path(raw),
                [[
                    "Salary Schedule",
                    "Rank  Step 1  Step 2",
                    "Officer  50000  52000",
                    "Sergeant  60000  62000",
                ]],
            )
            with mock.patch.object(
                socket.socket,
                "connect",
                side_effect=AssertionError("network call"),
            ), mock.patch.object(
                reviewer,
                "render_pdf_page",
                return_value=True,
            ):
                summary = reviewer.run(args)
            output = Path(args.output_dir)
            names = {
                path.name.lower()
                for path in output.rglob("*")
                if path.is_file()
            }
            self.assertFalse(any(name.endswith(".pdf") for name in names))
            self.assertFalse(any(name.endswith(".png") for name in names))
            self.assertFalse(any(name.endswith(".txt") for name in names))
            self.assertFalse(any("full_text" in name for name in names))
            self.assertEqual(summary["network_calls"], 0)
            self.assertEqual(summary["ocr_runs"], 0)
            self.assertEqual(summary["final_wage_values_extracted"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
