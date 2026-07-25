#!/usr/bin/env python3
"""Offline synthetic tests for the independent adjudication packet helper."""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path

from pypdf import PdfWriter


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = (
    REPO_ROOT / "scripts" / "prepare_independent_text_table_adjudication_packet.py"
)
SCHEMA_PATH = (
    REPO_ROOT
    / "docs"
    / "analysis"
    / "text_table_independent_adjudication_schema_2026-07-24.md"
)

spec = importlib.util.spec_from_file_location("adjudication_packet", SCRIPT_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("Could not load adjudication packet helper")
packet = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = packet
spec.loader.exec_module(packet)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


class IndependentAdjudicationPacketTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.pdf_paths: list[Path] = []
        for index in range(3):
            path = self.root / f"artifact_{index}.pdf"
            writer = PdfWriter()
            for _ in range(8 + index):
                writer.add_blank_page(width=612, height=792)
            with path.open("wb") as handle:
                writer.write(handle)
            self.pdf_paths.append(path)

        self.input_path = self.root / "calibration_input.csv"
        self.review2_path = self.root / "review2.csv"
        self.output_dir = self.root / "packet"
        source_fields = [
            "calibration_id",
            "source_review_id",
            "pdf_readiness_id",
            "candidate_queue_row_id",
            "state",
            "municipality",
            "government_name",
            "unit_type",
            "candidate_source_type",
            "pdf_page_count",
            "candidate_wage_pages",
            "content_artifact_path",
            "wage_table_signal",
            "candidate_contract_period_text",
            "recommended_next_action",
        ]
        source_rows = []
        for index, pdf_path in enumerate(self.pdf_paths):
            source_rows.append(
                {
                    "calibration_id": f"cal_{index}",
                    "source_review_id": f"sr_{index}",
                    "pdf_readiness_id": f"pr_{index}",
                    "candidate_queue_row_id": f"queue_{index}",
                    "state": "ZZ",
                    "municipality": f"Town {index}",
                    "government_name": f"City of Town {index}",
                    "unit_type": "police" if index == 0 else "non_safety",
                    "candidate_source_type": "cba",
                    "pdf_page_count": str(8 + index),
                    "candidate_wage_pages": "2,5,8" if index != 2 else "",
                    "content_artifact_path": str(pdf_path),
                    "wage_table_signal": "likely",
                    "candidate_contract_period_text": "synthetic forbidden snippet",
                    "recommended_next_action": "synthetic prior action",
                }
            )
        write_csv(self.input_path, source_fields, source_rows)
        write_csv(
            self.review2_path,
            [
                "calibration_id",
                "wage_schedule_table_confirmed_label",
                "candidate_page_relationship_label",
                "extraction_gate_label",
            ],
            [
                {
                    "calibration_id": f"cal_{index}",
                    "wage_schedule_table_confirmed_label": "yes",
                    "candidate_page_relationship_label": "exact_table_page",
                    "extraction_gate_label": "pass_high_confidence",
                }
                for index in range(3)
            ],
        )
        self.input_before = digest(self.input_path)
        self.review2_before = digest(self.review2_path)
        result = packet.main(
            [
                "--calibration-input-csv",
                str(self.input_path),
                "--review2-csv",
                str(self.review2_path),
                "--output-dir",
                str(self.output_dir),
                "--adjudication-prep-id",
                "SYNTHETIC-ADJUDICATION",
                "--candidate-page-window",
                "1",
                "--navigation-page-budget",
                "2",
                "--max-rendered-pages-per-case",
                "3",
                "--max-cases",
                "2",
                "--no-save-full-text",
                "--plan-only",
            ]
        )
        self.assertEqual(result, 0)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_human_csv_is_blinded_and_preserves_identities(self) -> None:
        header, rows = read_csv(
            self.output_dir / "independent_adjudication_blinded_review_input.csv"
        )
        self.assertEqual(header, packet.REQUIRED_IDENTITY_FIELDS + packet.HUMAN_REVIEW_FIELDS)
        self.assertFalse(packet.FORBIDDEN_HUMAN_FIELDS & set(header))
        self.assertEqual([row["calibration_id"] for row in rows], ["cal_0", "cal_1"])
        self.assertEqual([row["source_review_id"] for row in rows], ["sr_0", "sr_1"])
        self.assertEqual([row["pdf_readiness_id"] for row in rows], ["pr_0", "pr_1"])
        self.assertEqual(
            [row["candidate_queue_row_id"] for row in rows],
            ["queue_0", "queue_1"],
        )
        serialized = json.dumps(rows)
        self.assertNotIn("pass_high_confidence", serialized)
        self.assertNotIn("synthetic forbidden snippet", serialized)
        self.assertNotIn("synthetic prior action", serialized)

    def test_human_fields_are_initialized(self) -> None:
        _, rows = read_csv(
            self.output_dir / "independent_adjudication_blinded_review_input.csv"
        )
        for row in rows:
            self.assertEqual(row["human_reviewer"], "")
            self.assertEqual(row["human_reviewed_at"], "")
            self.assertEqual(row["human_review_status"], "not_reviewed")
            self.assertEqual(row["human_notes"], "")
            for field in packet.HUMAN_REVIEW_FIELDS:
                if field not in {
                    "human_reviewer",
                    "human_reviewed_at",
                    "human_review_status",
                    "human_notes",
                }:
                    self.assertEqual(row[field], "unknown")

    def test_max_cases_and_render_budget_are_respected(self) -> None:
        _, human_rows = read_csv(
            self.output_dir / "independent_adjudication_blinded_review_input.csv"
        )
        _, render_rows = read_csv(
            self.output_dir / "independent_adjudication_render_manifest.csv"
        )
        self.assertEqual(len(human_rows), 2)
        per_case = Counter(row["adjudication_case_id"] for row in render_rows)
        self.assertTrue(per_case)
        self.assertLessEqual(max(per_case.values()), 3)
        for human_row in human_rows:
            navigation = [
                value
                for value in human_row["blinded_navigation_pages"].split(",")
                if value
            ]
            self.assertLessEqual(len(navigation), 2)
        self.assertTrue(
            all(row["render_status"] == "planned_not_rendered" for row in render_rows)
        )

    def test_inputs_and_review_outputs_are_not_mutated(self) -> None:
        self.assertEqual(digest(self.input_path), self.input_before)
        self.assertEqual(digest(self.review2_path), self.review2_before)

    def test_no_full_text_or_complete_table_artifacts_are_written(self) -> None:
        relative_files = {
            path.relative_to(self.output_dir).as_posix()
            for path in self.output_dir.rglob("*")
            if path.is_file()
        }
        self.assertFalse(any(path.endswith(".txt") for path in relative_files))
        self.assertFalse(any("full_text" in path for path in relative_files))
        self.assertFalse(any("table_cells" in path for path in relative_files))
        manifest = json.loads(
            (self.output_dir / "independent_adjudication_manifest.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertFalse(manifest["full_text_saved"])
        self.assertFalse(manifest["full_tables_saved"])
        self.assertFalse(manifest["structured_wage_values_saved"])

    def test_helper_has_no_network_or_url_opening_imports(self) -> None:
        source = SCRIPT_PATH.read_text(encoding="utf-8")
        forbidden_imports = [
            "import requests",
            "import httpx",
            "import urllib",
            "import socket",
            "import webbrowser",
            "urlopen(",
        ]
        for forbidden in forbidden_imports:
            self.assertNotIn(forbidden, source)
        manifest = json.loads(
            (self.output_dir / "independent_adjudication_manifest.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(manifest["urls_opened"], 0)
        self.assertEqual(manifest["network_calls"], 0)
        self.assertEqual(manifest["ocr_runs"], 0)

    def test_every_allowed_value_is_documented(self) -> None:
        schema = SCHEMA_PATH.read_text(encoding="utf-8")
        instructions = (
            self.output_dir / "independent_adjudication_instructions.md"
        ).read_text(encoding="utf-8")
        for field, values in packet.ALLOWED_VALUES.items():
            self.assertIn(field, schema)
            self.assertIn(field, instructions)
            for value in values:
                self.assertIn(f"`{value}`", schema)
                self.assertIn(f"`{value}`", instructions)


if __name__ == "__main__":
    unittest.main(verbosity=2)
