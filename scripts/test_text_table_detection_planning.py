#!/usr/bin/env python3
"""Synthetic offline tests for text/table planning, running, and auditing."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import socket
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from reportlab.pdfgen import canvas


SCRIPTS = Path(__file__).resolve().parent
ROOT = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))

import audit_text_table_detection_lanes as auditor  # noqa: E402
import prepare_text_table_detection_pilot as planner  # noqa: E402
import text_table_detection_sources as runner  # noqa: E402


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


def make_pdf(path: Path, lines: list[str]) -> None:
    pdf = canvas.Canvas(str(path))
    y = 760
    for line in lines:
        pdf.drawString(50, y, line)
        y -= 18
    pdf.save()


def readiness_row(index: int, *, action: str = "parse_text_layer_later"):
    text_status = "absent" if action == "ocr_later" else (
        "partial" if index % 7 == 0 else "present"
    )
    return {
        "pdf_readiness_id": f"pr_{index:04d}",
        "source_review_id": f"sr_{index:04d}",
        "candidate_queue_row_id": f"cq_{index:04d}",
        "triage_id": f"tr_{index:04d}",
        "verification_id": f"vr_{index:04d}",
        "source_review_pilot_id": (
            "SOURCE-REVIEW-PILOT1-150-2026-07-24"
            if index % 3 == 0
            else "SOURCE-REVIEW-BATCH2-500-2026-07-24"
            if index % 3 == 1
            else "SOURCE-REVIEW-BATCH3-3X500-2026-07-24"
        ),
        "state": f"S{index % 20:02d}",
        "municipality": f"Municipality {index}",
        "government_name": f"Government {index}",
        "unit_type": ("police", "fire", "non_safety")[index % 3],
        "candidate_source_type": (
            "cba",
            "wage_schedule_or_compensation_plan",
            "memorandum_or_settlement",
            "ordinance_or_policy",
        )[index % 4],
        "priority_for_content_review": "p1" if index % 2 else "p2",
        "source_officialness_rating": (
            "official_municipal",
            "official_state_repository",
            "official_union",
            "uncertain",
            "unknown",
        )[index % 5],
        "source_relevance_rating": "possible",
        "document_type_rating": "cba_candidate",
        "extraction_readiness_rating": "medium",
        "content_artifact_path": f"tmp/synthetic_{index}.pdf",
        "content_hash": hashlib.sha256(str(index).encode()).hexdigest(),
        "content_byte_size": str(1000 + index),
        "content_type_observed": "application/pdf",
        "pdf_page_count": str((index % 130) + 1),
        "text_layer_status": text_status,
        "readiness_status": "readiness_checked",
        "recommended_next_action": action,
    }


def input_row(pdf: Path, *, content_hash: str | None = None):
    values = {
        "text_table_detection_id": "ttd_test",
        "pdf_readiness_id": "pr_test",
        "source_review_id": "sr_test",
        "candidate_queue_row_id": "cq_test",
        "triage_id": "tr_test",
        "verification_id": "vr_test",
        "source_review_pilot_id": (
            "SOURCE-REVIEW-PILOT1-150-2026-07-24"
        ),
        "state": "MA",
        "municipality": "Testville",
        "government_name": "CITY OF TESTVILLE",
        "unit_type": "police",
        "candidate_source_type": "cba",
        "priority_for_content_review": "p1",
        "source_officialness_rating": "official_municipal",
        "source_relevance_rating": "possible",
        "document_type_rating": "cba_candidate",
        "extraction_readiness_rating": "medium",
        "content_artifact_path": pdf.as_posix(),
        "content_hash": content_hash or (sha256(pdf) if pdf.exists() else "0" * 64),
        "content_byte_size": str(pdf.stat().st_size if pdf.exists() else 1),
        "content_type_observed": "application/pdf",
        "pdf_page_count": "1",
        "text_layer_status": "present",
        "text_table_detection_pilot_id": "TEST-PILOT",
        "text_table_detection_lane_id": "lane_1",
        "pilot_selection_rank": "1",
        "page_count_bin": "1_to_10",
        "artifact_byte_size_bin": "small_le_512_kib",
        "sample_selection_reason": "synthetic parse-text candidate",
    }
    return {field: values.get(field, "") for field in planner.INPUT_FIELDS}


class TextTableDetectionTests(unittest.TestCase):
    def planner_fixture(self, root: Path) -> argparse.Namespace:
        readiness = root / "readiness.csv"
        source = root / "source.csv"
        triage = root / "triage.csv"
        rows = [readiness_row(index) for index in range(180)]
        rows += [
            readiness_row(1000 + index, action="ocr_later")
            for index in range(20)
        ]
        fields = sorted(
            planner.REQUIRED_READINESS_FIELDS
            | {"artifact_byte_size_bin"}
        )
        write_csv(readiness, rows, fields)
        write_csv(
            source,
            [{"source_review_id": row["source_review_id"]} for row in rows],
            ["source_review_id"],
        )
        write_csv(
            triage,
            [{"triage_id": row["triage_id"]} for row in rows],
            ["triage_id"],
        )
        return argparse.Namespace(
            pdf_readiness_ledger_csv=str(readiness),
            source_review_ledger_csv=str(source),
            triage_ledger_csv=str(triage),
            output_dir=str(root / "plan"),
            pilot_id="TEST-TEXT-TABLE-150",
            sample_size=150,
            num_lanes=3,
            state_diversity=True,
            include_partial_text_layer=True,
            exclude_ocr_later=True,
            plan_only=True,
        )

    def planned_rows(self, output: Path) -> list[dict[str, str]]:
        rows: list[dict[str, str]] = []
        for lane in range(1, 4):
            rows.extend(
                read_csv(
                    output
                    / f"lane_{lane}_text_table_detection_input.csv"
                )
            )
        return rows

    def test_planner_selects_only_parse_text_rows(self):
        with tempfile.TemporaryDirectory() as raw:
            args = self.planner_fixture(Path(raw))
            planner.create_plan(args)
            rows = self.planned_rows(Path(args.output_dir))
            self.assertEqual(len(rows), 150)
            self.assertTrue(
                all(
                    row["text_layer_status"] in {"present", "partial"}
                    for row in rows
                )
            )

    def test_planner_excludes_ocr_later(self):
        with tempfile.TemporaryDirectory() as raw:
            args = self.planner_fixture(Path(raw))
            planner.create_plan(args)
            selected = {
                row["source_review_id"]
                for row in self.planned_rows(Path(args.output_dir))
            }
            ocr_ids = {f"sr_{1000 + index:04d}" for index in range(20)}
            self.assertFalse(selected & ocr_ids)

    def test_planner_creates_150_rows(self):
        with tempfile.TemporaryDirectory() as raw:
            args = self.planner_fixture(Path(raw))
            manifest = planner.create_plan(args)
            self.assertEqual(manifest["selected_rows"], 150)
            self.assertEqual(len(self.planned_rows(Path(args.output_dir))), 150)

    def test_planner_balances_three_lanes(self):
        with tempfile.TemporaryDirectory() as raw:
            args = self.planner_fixture(Path(raw))
            manifest = planner.create_plan(args)
            self.assertEqual(manifest["lane_rows"], [50, 50, 50])

    def test_dry_run_opens_no_pdfs(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            input_path = root / "input.csv"
            row = input_row(root / "does_not_exist.pdf")
            write_csv(input_path, [row], planner.INPUT_FIELDS)
            args = argparse.Namespace(
                input_csv=str(input_path),
                output_dir=str(root / "dry"),
                max_rows=None,
                max_pages_to_scan=10,
                max_text_chars_per_page=1500,
                timeout_per_file=30.0,
                no_save_text=True,
                dry_run=True,
            )

            def forbidden_inspector(*_args, **_kwargs):
                raise AssertionError("dry-run invoked PDF inspector")

            summary = runner.run(args, inspector=forbidden_inspector)
            self.assertEqual(summary["local_artifacts_opened"], 0)
            self.assertEqual(summary["pdfs_opened_for_detection"], 0)

    def test_hash_mismatch_is_terminal(self):
        with tempfile.TemporaryDirectory() as raw:
            pdf = Path(raw) / "fixture.pdf"
            make_pdf(pdf, ["Agreement text"])
            row = input_row(pdf, content_hash="f" * 64)
            result, _ = runner.inspect_artifact(
                row,
                max_pages_to_scan=10,
                max_text_chars_per_page=1500,
                timeout_per_file=30,
            )
            self.assertEqual(result["detection_status"], "hash_mismatch")

    def test_missing_artifact_is_terminal(self):
        with tempfile.TemporaryDirectory() as raw:
            row = input_row(Path(raw) / "missing.pdf")
            result, _ = runner.inspect_artifact(
                row,
                max_pages_to_scan=10,
                max_text_chars_per_page=1500,
                timeout_per_file=30,
            )
            self.assertEqual(result["detection_status"], "artifact_missing")

    def test_wage_schedule_fixture_produces_signal_without_values(self):
        with tempfile.TemporaryDirectory() as raw:
            pdf = Path(raw) / "wage.pdf"
            make_pdf(
                pdf,
                [
                    "Collective Bargaining Agreement",
                    "Effective July 1, 2020 through June 30, 2023",
                    "Salary Schedule Step Grade Annual Compensation",
                    "Patrol Officer    Step 1    $50,000",
                    "Sergeant          Step 2    $55,000",
                    "Lieutenant        Step 3    $60,000",
                ],
            )
            result, _ = runner.inspect_artifact(
                input_row(pdf),
                max_pages_to_scan=10,
                max_text_chars_per_page=1500,
                timeout_per_file=30,
            )
            self.assertEqual(result["detection_status"], "detection_checked")
            self.assertIn(result["wage_table_signal"], {"likely", "possible"})
            serialized = json.dumps(result)
            self.assertNotIn("$50,000", serialized)
            self.assertLessEqual(
                len(result["candidate_contract_period_text"]), 300
            )

    def test_no_wage_fixture_is_unlikely(self):
        with tempfile.TemporaryDirectory() as raw:
            pdf = Path(raw) / "plain.pdf"
            make_pdf(
                pdf,
                [
                    "Department handbook",
                    "Employees should keep shared rooms orderly.",
                    "Questions should be directed to the front office.",
                ],
            )
            result, _ = runner.inspect_artifact(
                input_row(pdf),
                max_pages_to_scan=10,
                max_text_chars_per_page=1500,
                timeout_per_file=30,
            )
            self.assertEqual(result["wage_table_signal"], "unlikely")

    def test_parser_error_is_terminal(self):
        with tempfile.TemporaryDirectory() as raw:
            pdf = Path(raw) / "fixture.pdf"
            make_pdf(pdf, ["Agreement text"])

            def bad_reader(*_args, **_kwargs):
                raise RuntimeError("synthetic parser failure")

            result, _ = runner.inspect_artifact(
                input_row(pdf),
                max_pages_to_scan=10,
                max_text_chars_per_page=1500,
                timeout_per_file=30,
                reader_factory=bad_reader,
            )
            self.assertEqual(result["detection_status"], "parser_error")

    def run_fixture(self, root: Path) -> tuple[dict[str, object], Path]:
        pdf = root / "fixture.pdf"
        make_pdf(pdf, ["Salary Schedule", "Step 1    Grade A    100"])
        input_path = root / "input.csv"
        write_csv(input_path, [input_row(pdf)], planner.INPUT_FIELDS)
        output = root / "local"
        args = argparse.Namespace(
            input_csv=str(input_path),
            output_dir=str(output),
            max_rows=None,
            max_pages_to_scan=10,
            max_text_chars_per_page=1500,
            timeout_per_file=30.0,
            no_save_text=True,
            dry_run=False,
        )
        return runner.run(args), output

    def test_runner_writes_no_full_text_artifacts(self):
        with tempfile.TemporaryDirectory() as raw:
            _summary, output = self.run_fixture(Path(raw))
            names = {path.name for path in output.rglob("*") if path.is_file()}
            self.assertFalse(
                any(name.endswith((".txt", ".text")) for name in names)
            )
            self.assertFalse(
                any("full_text" in name or "extracted_text" in name for name in names)
            )

    def test_runner_makes_no_network_calls(self):
        with tempfile.TemporaryDirectory() as raw:
            with mock.patch.object(
                socket.socket,
                "connect",
                side_effect=AssertionError("network call attempted"),
            ):
                summary, _output = self.run_fixture(Path(raw))
            self.assertEqual(summary["network_calls"], 0)

    def test_auditor_classifies_completed_lane(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            pdf = root / "fixture.pdf"
            make_pdf(pdf, ["Salary Schedule", "Step 1    Grade A    100"])
            input_path = root / "lane.csv"
            write_csv(input_path, [input_row(pdf)], planner.INPUT_FIELDS)
            local_output = root / "local"
            args = argparse.Namespace(
                input_csv=str(input_path),
                output_dir=str(local_output),
                max_rows=None,
                max_pages_to_scan=10,
                max_text_chars_per_page=1500,
                timeout_per_file=30.0,
                no_save_text=True,
                dry_run=False,
            )
            runner.run(args)
            manifest = {
                "pilot_id": "TEST-PILOT",
                "selected_rows": 1,
                "lanes": [
                    {
                        "lane_id": "lane_1",
                        "expected_rows": 1,
                        "input_csv": str(input_path),
                        "input_sha256": sha256(input_path),
                        "dry_run_output_dir": str(root / "dry"),
                        "future_local_output_dir": str(local_output),
                    }
                ],
            }
            manifest_path = root / "manifest.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            result = auditor.audit(manifest_path, root / "audit")
            self.assertEqual(
                result["lane_classification_counts"],
                {"completed_merge_eligible": 1},
            )

    def test_protected_files_are_not_modified(self):
        protected = [
            ROOT / "data" / "contracts.csv",
            ROOT / "data" / "city_coverage.csv",
        ]
        before = {path: sha256(path) for path in protected}
        with tempfile.TemporaryDirectory() as raw:
            args = self.planner_fixture(Path(raw))
            planner.create_plan(args)
        after = {path: sha256(path) for path in protected}
        self.assertEqual(before, after)


def main() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        TextTableDetectionTests
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
