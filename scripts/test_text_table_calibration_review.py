#!/usr/bin/env python3
"""Synthetic offline tests for bounded calibration review."""

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


SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

import review_text_table_calibration_subset as reviewer  # noqa: E402
from prepare_text_table_calibration_subset import OUTPUT_FIELDS  # noqa: E402


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_csv(
    path: Path, rows: list[dict[str, str]], fields: list[str]
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=fields, lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def make_pdf(path: Path, pages: list[list[str]]) -> None:
    pdf = canvas.Canvas(str(path))
    for page_lines in pages:
        y = 760
        for line in page_lines:
            pdf.drawString(50, y, line)
            y -= 18
        pdf.showPage()
    pdf.save()


def input_row(
    index: int,
    artifact: Path,
    page_count: int,
    candidate_pages: str = "3",
) -> dict[str, str]:
    row = {field: "" for field in OUTPUT_FIELDS}
    row.update(
        {
            "calibration_id": f"cal_{index}",
            "text_table_detection_id": f"ttd_{index}",
            "pdf_readiness_id": f"pdf_{index}",
            "source_review_id": f"sr_{index}",
            "candidate_queue_row_id": f"cq_{index}",
            "state": "MA",
            "municipality": f"Testville {index}",
            "government_name": f"Testville {index}",
            "unit_type": ("police", "fire", "non_safety")[index % 3],
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
            "detection_notes": "synthetic detection metadata",
            "calibration_round_id": "TEST-CALIBRATION",
            "calibration_selection_rank": str(index + 1),
            "calibration_selection_reason": "synthetic",
            "source_review_pilot_id": "SOURCE-REVIEW-TEST",
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


def authority_row(
    row: dict[str, str], *, content_hash: str, content_size: int
) -> dict[str, str]:
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
        "content_hash": content_hash,
        "content_byte_size": str(content_size),
        "content_type_observed": "application/pdf",
    }


class CalibrationReviewTests(unittest.TestCase):
    def fixture(
        self,
        root: Path,
        *,
        missing: bool = False,
        hash_mismatch: bool = False,
        page_count: int = 6,
        candidate_pages: str = "3",
    ) -> argparse.Namespace:
        artifact = root / "fixture.pdf"
        if not missing:
            pages = [
                ["Collective bargaining agreement 2021 through 2024"],
                ["General terms and conditions"],
                [
                    "Salary Schedule Effective 2022",
                    "Rank  Step 1  Step 2  Step 3",
                    "Officer  50000  52000  54000",
                    "Sergeant  60000  62000  64000",
                ],
                ["Continuation of unrelated agreement provisions"],
                ["Health insurance premium contribution table"],
                ["Appendix and signatures"],
            ][:page_count]
            make_pdf(artifact, pages)
        row = input_row(0, artifact, page_count, candidate_pages)
        input_path = root / "input.csv"
        authority_path = root / "authority.csv"
        write_csv(input_path, [row], OUTPUT_FIELDS)
        actual_hash = sha256(artifact) if artifact.exists() else "missing"
        actual_size = artifact.stat().st_size if artifact.exists() else 1
        authority = authority_row(
            row,
            content_hash=("0" * 64 if hash_mismatch else actual_hash),
            content_size=actual_size,
        )
        write_csv(
            authority_path,
            [authority],
            list(authority),
        )
        return argparse.Namespace(
            input_csv=str(input_path),
            output_dir=str(root / "output"),
            review_id="TEST-REVIEW",
            text_table_ledger_csv=str(authority_path),
            max_rows=None,
            candidate_page_window=1,
            max_pages_per_document=5,
            max_snippet_chars=300,
            no_save_full_text=True,
            dry_run=False,
        )

    def test_dry_run_opens_no_pdfs(self):
        with tempfile.TemporaryDirectory() as raw:
            args = self.fixture(Path(raw))
            args.dry_run = True
            with mock.patch.object(
                reviewer, "PdfReader", side_effect=AssertionError("opened PDF")
            ):
                summary = reviewer.run(args)
            self.assertEqual(summary["pdfs_opened"], 0)
            self.assertEqual(summary["reviewed_rows"], 0)

    def test_review_preserves_rows_and_identities(self):
        with tempfile.TemporaryDirectory() as raw:
            args = self.fixture(Path(raw))
            original = read_csv(Path(args.input_csv))[0]
            summary = reviewer.run(args)
            result = read_csv(Path(args.output_dir) / "calibration_reviewed.csv")[0]
            self.assertEqual(summary["rows"], 1)
            for field in (
                "calibration_id",
                "text_table_detection_id",
                "pdf_readiness_id",
                "source_review_id",
                "candidate_queue_row_id",
            ):
                self.assertEqual(result[field], original[field])

    def test_missing_artifact_is_terminal_second_review(self):
        with tempfile.TemporaryDirectory() as raw:
            args = self.fixture(Path(raw), missing=True)
            reviewer.run(args)
            result = read_csv(Path(args.output_dir) / "calibration_reviewed.csv")[0]
            self.assertEqual(result["calibration_status"], "needs_second_review")
            self.assertEqual(result["pdf_opened_review"], "0")

    def test_hash_mismatch_is_flagged_without_pdf_open(self):
        with tempfile.TemporaryDirectory() as raw:
            args = self.fixture(Path(raw), hash_mismatch=True)
            reviewer.run(args)
            result = read_csv(Path(args.output_dir) / "calibration_reviewed.csv")[0]
            self.assertEqual(result["artifact_hash_verified_review"], "0")
            self.assertEqual(result["calibration_status"], "needs_second_review")
            self.assertEqual(result["pdf_opened_review"], "0")

    def test_candidate_window_and_page_cap_are_respected(self):
        with tempfile.TemporaryDirectory() as raw:
            args = self.fixture(Path(raw))
            args.max_pages_per_document = 3
            reviewer.run(args)
            result = read_csv(Path(args.output_dir) / "calibration_reviewed.csv")[0]
            inspected = {
                int(value) for value in result["pages_inspected"].split(",")
            }
            self.assertLessEqual(len(inspected), 3)
            self.assertTrue(inspected.issubset({1, 2, 3, 4}))
            self.assertIn(3, inspected)

    def test_labels_are_controlled_and_notes_bounded(self):
        with tempfile.TemporaryDirectory() as raw:
            args = self.fixture(Path(raw))
            reviewer.run(args)
            result = read_csv(Path(args.output_dir) / "calibration_reviewed.csv")[0]
            for field, values in reviewer.ALLOWED.items():
                self.assertIn(result[field], values)
            for field in (
                "reviewer_notes",
                "extraction_schema_notes",
                "review_status_detail",
            ):
                self.assertLessEqual(len(result[field]), 300)

    def test_wage_schedule_fixture_is_useful(self):
        with tempfile.TemporaryDirectory() as raw:
            args = self.fixture(Path(raw))
            reviewer.run(args)
            result = read_csv(Path(args.output_dir) / "calibration_reviewed.csv")[0]
            self.assertIn(
                result["wage_table_present_label"], {"yes", "maybe"}
            )
            self.assertIn(
                result["page_hint_precision_label"],
                {"correct", "partially_correct"},
            )

    def test_writes_no_full_text_artifacts(self):
        with tempfile.TemporaryDirectory() as raw:
            args = self.fixture(Path(raw))
            reviewer.run(args)
            output = Path(args.output_dir)
            names = {path.name.lower() for path in output.rglob("*") if path.is_file()}
            self.assertFalse(any("full_text" in name for name in names))
            self.assertFalse(any(name.endswith(".txt") for name in names))
            self.assertFalse(any(name.endswith(".pdf") for name in names))

    def test_original_and_authority_files_are_not_mutated(self):
        with tempfile.TemporaryDirectory() as raw:
            args = self.fixture(Path(raw))
            before_input = sha256(Path(args.input_csv))
            before_authority = sha256(Path(args.text_table_ledger_csv))
            reviewer.run(args)
            self.assertEqual(before_input, sha256(Path(args.input_csv)))
            self.assertEqual(
                before_authority, sha256(Path(args.text_table_ledger_csv))
            )

    def test_runner_makes_no_network_calls(self):
        with tempfile.TemporaryDirectory() as raw:
            args = self.fixture(Path(raw))
            with mock.patch.object(
                socket.socket,
                "connect",
                side_effect=AssertionError("network call"),
            ):
                reviewer.run(args)


if __name__ == "__main__":
    unittest.main(verbosity=2)
