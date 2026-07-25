#!/usr/bin/env python3
"""Synthetic offline tests for calibration-subset preparation."""

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


SCRIPTS = Path(__file__).resolve().parent
ROOT = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))

import prepare_text_table_calibration_subset as planner  # noqa: E402


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


def detection_row(index: int) -> dict[str, str]:
    signal = "likely" if index < 100 else "possible" if index < 188 else "unlikely"
    if index in {100, 101} or index >= 195:
        extraction_priority = "p3"
        next_action = "manual_review"
    elif signal == "likely":
        extraction_priority = "p1"
        next_action = "wage_table_extraction_pilot"
    elif signal == "possible":
        extraction_priority = "p2"
        next_action = "larger_text_detection_pass"
    else:
        extraction_priority = "p2"
        next_action = "contract_period_extraction_pilot"
    source_types = (
        "cba",
        "wage_schedule_or_compensation_plan",
        "memorandum_or_settlement",
        "ordinance_or_policy",
        "arbitration_award",
        "factfinding",
    )
    page_bins = (
        "1_to_10",
        "11_to_25",
        "26_to_50",
        "51_to_100",
        "over_100",
    )
    page_bin = page_bins[index % len(page_bins)]
    pages = ("1", "2", "3")[: (index % 3) + 1]
    values = {
        "text_table_detection_id": f"ttd_{index:04d}",
        "pdf_readiness_id": f"pr_{index:04d}",
        "source_review_id": f"sr_{index:04d}",
        "candidate_queue_row_id": f"cq_{index:04d}",
        "state": f"S{index % 25:02d}",
        "municipality": f"Municipality {index}",
        "government_name": f"Government {index}",
        "unit_type": ("police", "fire", "non_safety")[index % 3],
        "candidate_source_type": source_types[index % len(source_types)],
        "priority_for_content_review": "p1" if index % 4 else "p2",
        "source_officialness_rating": (
            "official_municipal",
            "official_state_repository",
            "official_union",
            "uncertain",
            "unknown",
        )[index % 5],
        "source_relevance_rating": "possible",
        "document_type_rating": "cba_candidate",
        "pdf_page_count": str((index % 120) + 1),
        "content_artifact_path": f"tmp/never_open_{index}.pdf",
        "wage_table_signal": signal,
        "wage_table_signal_confidence": {
            "likely": "high",
            "possible": "medium",
            "unlikely": "low",
        }[signal],
        "contract_period_signal": "likely",
        "contract_period_confidence": "high",
        "table_like_structure_signal": (
            "unlikely" if signal == "unlikely" else "likely"
        ),
        "candidate_wage_pages": ",".join(pages),
        "candidate_wage_page_count": str(len(pages)),
        "candidate_contract_period_text": "Effective 2020 through 2023",
        "detection_notes": "synthetic bounded detection note",
        "source_review_pilot_id": (
            "SOURCE-REVIEW-PILOT1-150-2026-07-24"
            if index % 3 == 0
            else "SOURCE-REVIEW-BATCH2-500-2026-07-24"
            if index % 3 == 1
            else "SOURCE-REVIEW-BATCH3-3X500-2026-07-24"
        ),
        "page_count_bin": page_bin,
        "text_layer_status": (
            "partial"
            if index == 102 or index % 11 == 0
            else "present"
        ),
        "extraction_pilot_priority": extraction_priority,
        "recommended_next_action": next_action,
        "table_detection_method": "bounded_keyword_numeric_structure_v1",
        "detection_status": "detection_checked",
    }
    return values


class CalibrationPlanningTests(unittest.TestCase):
    def fixture(self, root: Path) -> argparse.Namespace:
        detection = root / "detection.csv"
        pdf = root / "readiness.csv"
        source = root / "source.csv"
        rows = [detection_row(index) for index in range(200)]
        detection_fields = sorted(planner.REQUIRED_DETECTION_FIELDS)
        write_csv(detection, rows, detection_fields)
        pdf_fields = [
            "pdf_readiness_id",
            "source_review_id",
            "candidate_queue_row_id",
            "content_artifact_path",
            "pdf_page_count",
            "text_layer_status",
        ]
        write_csv(
            pdf,
            [
                {field: row[field] for field in pdf_fields}
                for row in rows
            ],
            pdf_fields,
        )
        source_fields = [
            "source_review_id",
            "candidate_queue_row_id",
            "content_artifact_path",
        ]
        write_csv(
            source,
            [
                {field: row[field] for field in source_fields}
                for row in rows
            ],
            source_fields,
        )
        return argparse.Namespace(
            text_table_ledger_csv=str(detection),
            pdf_readiness_ledger_csv=str(pdf),
            source_review_ledger_csv=str(source),
            output_dir=str(root / "packet"),
            calibration_id="TEST-CALIBRATION-150",
            sample_size=150,
            stratify=True,
            include_unlikely=True,
            plan_only=True,
        )

    def run_fixture(
        self, root: Path
    ) -> tuple[dict[str, object], argparse.Namespace, list[dict[str, str]]]:
        args = self.fixture(root)
        summary = planner.create_plan(args)
        rows = read_csv(
            Path(args.output_dir) / "calibration_review_input.csv"
        )
        return summary, args, rows

    def test_requested_sample_and_signal_allocation(self):
        with tempfile.TemporaryDirectory() as raw:
            summary, _args, rows = self.run_fixture(Path(raw))
            self.assertEqual(len(rows), 150)
            self.assertEqual(summary["calibration_subset_rows"], 150)
            self.assertEqual(
                summary["wage_table_signal_counts"],
                {"likely": 80, "possible": 58, "unlikely": 12},
            )

    def test_includes_all_unlikely_likely_and_possible(self):
        with tempfile.TemporaryDirectory() as raw:
            _summary, _args, rows = self.run_fixture(Path(raw))
            unlikely = {
                row["text_table_detection_id"]
                for row in rows
                if row["wage_table_signal"] == "unlikely"
            }
            self.assertEqual(
                unlikely, {f"ttd_{index:04d}" for index in range(188, 200)}
            )
            signals = {row["wage_table_signal"] for row in rows}
            self.assertEqual(signals, {"likely", "possible", "unlikely"})

    def test_preserves_required_identity_fields(self):
        with tempfile.TemporaryDirectory() as raw:
            _summary, _args, rows = self.run_fixture(Path(raw))
            for field in (
                "calibration_id",
                "text_table_detection_id",
                "pdf_readiness_id",
                "source_review_id",
                "candidate_queue_row_id",
            ):
                values = [row[field] for row in rows]
                self.assertTrue(all(values))
                self.assertEqual(len(values), len(set(values)))

    def test_initializes_manual_fields_without_review(self):
        with tempfile.TemporaryDirectory() as raw:
            _summary, _args, rows = self.run_fixture(Path(raw))
            self.assertTrue(
                all(row["calibration_status"] == "not_reviewed" for row in rows)
            )
            unknown_fields = {
                "page_hint_precision_label",
                "wage_table_present_label",
                "wage_table_page_match_label",
                "contract_period_present_label",
                "contract_period_hint_match_label",
                "table_layout_type",
                "extraction_complexity_label",
                "false_positive_family",
                "recommended_extraction_action",
                "reviewer_confidence",
            }
            self.assertTrue(
                all(
                    row[field] == "unknown"
                    for row in rows
                    for field in unknown_fields
                )
            )
            self.assertTrue(all(not row["reviewer"] for row in rows))
            self.assertTrue(all(not row["reviewed_at"] for row in rows))

    def test_writes_no_full_text_or_final_wage_fields(self):
        with tempfile.TemporaryDirectory() as raw:
            _summary, args, _rows = self.run_fixture(Path(raw))
            header = next(
                csv.reader(
                    (
                        Path(args.output_dir)
                        / "calibration_review_input.csv"
                    ).open(encoding="utf-8")
                )
            )
            lowered = " ".join(header).lower()
            self.assertNotIn("full_text", lowered)
            self.assertNotIn("complete_page_text", lowered)
            self.assertNotIn("final_wage_value", lowered)
            names = {
                path.name
                for path in Path(args.output_dir).rglob("*")
                if path.is_file()
            }
            self.assertFalse(any(name.endswith(".pdf") for name in names))
            self.assertFalse(any(name.endswith(".txt") for name in names))

    def test_planner_opens_no_pdfs(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            args = self.fixture(root)
            original_open = Path.open

            def guarded_open(path, *open_args, **open_kwargs):
                if path.suffix.lower() == ".pdf":
                    raise AssertionError("planner opened a PDF")
                return original_open(path, *open_args, **open_kwargs)

            with mock.patch.object(Path, "open", new=guarded_open):
                summary = planner.create_plan(args)
            self.assertEqual(summary["pdfs_opened"], 0)

    def test_planner_makes_no_network_calls(self):
        with tempfile.TemporaryDirectory() as raw:
            args = self.fixture(Path(raw))
            with mock.patch.object(
                socket.socket,
                "connect",
                side_effect=AssertionError("network call attempted"),
            ):
                summary = planner.create_plan(args)
            self.assertEqual(summary["network_calls"], 0)
            self.assertEqual(summary["urls_opened"], 0)

    def test_protected_and_authority_files_are_not_modified(self):
        protected = [
            ROOT / "data/contracts.csv",
            ROOT / "data/city_coverage.csv",
            ROOT
            / "docs/analysis/text_table_detection_ledgers/"
            "text_table_detection_ledger_cumulative.csv",
            ROOT
            / "docs/analysis/pdf_readiness_ledgers/"
            "pdf_readiness_ledger_cumulative.csv",
            ROOT
            / "docs/analysis/source_review_ledgers/"
            "source_review_ledger_cumulative.csv",
        ]
        before = {path: sha256(path) for path in protected}
        with tempfile.TemporaryDirectory() as raw:
            self.run_fixture(Path(raw))
        after = {path: sha256(path) for path in protected}
        self.assertEqual(before, after)

    def test_selection_is_deterministic(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            args_one = self.fixture(root / "one")
            planner.create_plan(args_one)
            args_two = self.fixture(root / "two")
            planner.create_plan(args_two)
            rows_one = read_csv(
                Path(args_one.output_dir) / "calibration_review_input.csv"
            )
            rows_two = read_csv(
                Path(args_two.output_dir) / "calibration_review_input.csv"
            )
            self.assertEqual(
                [row["text_table_detection_id"] for row in rows_one],
                [row["text_table_detection_id"] for row in rows_two],
            )


def main() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        CalibrationPlanningTests
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
