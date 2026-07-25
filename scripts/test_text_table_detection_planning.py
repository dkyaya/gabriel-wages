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
import merge_text_table_detection_lanes as merger  # noqa: E402
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
            all_parse_text=False,
            num_lanes=3,
            balance_lanes=True,
            state_diversity=True,
            include_partial_text_layer=True,
            exclude_ocr_later=True,
            freeze_heuristic_version=(
                planner.FROZEN_HEURISTIC_VERSION
            ),
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

    def test_full_planner_selects_all_parse_text_rows_in_four_lanes(self):
        with tempfile.TemporaryDirectory() as raw:
            args = self.planner_fixture(Path(raw))
            args.pilot_id = "TEST-TEXT-TABLE-FULL"
            args.all_parse_text = True
            args.num_lanes = 4
            manifest = planner.create_plan(args)
            rows: list[dict[str, str]] = []
            for lane in range(1, 5):
                rows.extend(
                    read_csv(
                        Path(args.output_dir)
                        / f"lane_{lane}_text_table_detection_input.csv"
                    )
                )
            self.assertEqual(manifest["selected_rows"], 180)
            self.assertEqual(manifest["lane_rows"], [45, 45, 45, 45])
            self.assertEqual(len(rows), 180)
            self.assertEqual(
                len({row["pdf_readiness_id"] for row in rows}), 180
            )
            self.assertTrue(
                all(
                    row["sample_selection_reason"]
                    == (
                        "complete durable parse_text_layer_later universe "
                        "under frozen heuristic"
                    )
                    for row in rows
                )
            )
            self.assertEqual(
                manifest["frozen_heuristic_version"],
                runner.TABLE_METHOD,
            )

    def test_planner_rejects_unfrozen_heuristic_version(self):
        with tempfile.TemporaryDirectory() as raw:
            args = self.planner_fixture(Path(raw))
            args.freeze_heuristic_version = "changed_heuristic"
            with self.assertRaisesRegex(
                ValueError, "unsupported heuristic version"
            ):
                planner.create_plan(args)

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


class TextTableDetectionMergeTests(unittest.TestCase):
    def detection_row(
        self,
        index: int,
        *,
        pilot_id: str = "TEST-TEXT-TABLE-FULL",
        lane_id: str = "lane_1",
    ) -> dict[str, str]:
        base = readiness_row(index)
        values = {
            **base,
            "text_table_detection_id": f"ttd_{index:04d}",
            "text_table_detection_pilot_id": pilot_id,
            "text_table_detection_lane_id": lane_id,
            "pilot_selection_rank": str(index + 1),
            "page_count_bin": "1_to_10",
            "artifact_byte_size_bin": "small_le_512_kib",
            "sample_selection_reason": (
                "complete durable parse_text_layer_later universe "
                "under frozen heuristic"
            ),
            "detection_status": "detection_checked",
            "detection_status_detail": "synthetic bounded detection",
            "parser_library": "pypdf",
            "parser_version": "6.13.2",
            "parser_elapsed_seconds": "0.01",
            "pages_scanned": "1",
            "pages_with_text": "1",
            "total_text_chars_scanned": "100",
            "wage_table_signal": "likely" if index % 2 else "possible",
            "wage_table_signal_confidence": (
                "high" if index % 2 else "medium"
            ),
            "candidate_wage_pages": "1",
            "candidate_wage_page_count": "1",
            "contract_period_signal": "likely",
            "contract_period_confidence": "high",
            "candidate_contract_period_text": "Effective 2020 through 2023",
            "pay_schedule_signal": "detected",
            "salary_schedule_signal": "detected",
            "hourly_rate_signal": "not_detected",
            "step_grade_signal": "detected",
            "rank_position_signal": "detected",
            "effective_date_signal": "detected",
            "bargaining_unit_signal": "detected",
            "public_safety_signal": "detected",
            "non_safety_signal": "not_detected",
            "table_like_structure_signal": "likely",
            "table_detection_method": runner.TABLE_METHOD,
            "extraction_pilot_priority": "p1",
            "recommended_next_action": "wage_table_extraction_pilot",
            "detection_notes": "synthetic bounded signals only",
            "reviewer": "synthetic_test",
            "reviewed_at": "2026-07-25T00:00:00Z",
        }
        return {field: values.get(field, "") for field in runner.LEDGER_FIELDS}

    def merge_fixture(self, root: Path) -> argparse.Namespace:
        pilot_id = "TEST-TEXT-TABLE-FULL"
        rows = [
            self.detection_row(index, pilot_id=pilot_id, lane_id="lane_1")
            for index in range(2)
        ]
        rows += [
            self.detection_row(index, pilot_id=pilot_id, lane_id="lane_2")
            for index in range(2, 4)
        ]
        lanes = []
        for lane_number in (1, 2):
            lane_id = f"lane_{lane_number}"
            output = root / lane_id / "local"
            lane_rows = [
                row
                for row in rows
                if row["text_table_detection_lane_id"] == lane_id
            ]
            write_csv(
                output / "text_table_detection_ledger.csv",
                lane_rows,
                runner.LEDGER_FIELDS,
            )
            lanes.append(
                {
                    "lane_id": lane_id,
                    "expected_rows": len(lane_rows),
                    "future_local_output_dir": str(output),
                    "frozen_heuristic_version": runner.TABLE_METHOD,
                }
            )
        manifest = {
            "pilot_id": pilot_id,
            "selected_rows": len(rows),
            "frozen_heuristic_version": runner.TABLE_METHOD,
            "lanes": lanes,
        }
        manifest_path = root / "manifest.json"
        manifest_path.write_text(
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
        )
        audit = {
            "pilot_id": pilot_id,
            "manifest": manifest_path.as_posix(),
            "planned_rows": len(rows),
            "ledger_rows": len(rows),
            "terminal_rows": len(rows),
            "lane_classification_counts": {
                "completed_merge_eligible": len(lanes)
            },
            "lanes": [
                {
                    "lane_id": lane["lane_id"],
                    "classification": "completed_merge_eligible",
                    "mode": "local",
                    "no_forbidden_activity": True,
                    "terminal_rows": lane["expected_rows"],
                }
                for lane in lanes
            ],
            "detection_status_counts": {"detection_checked": len(rows)},
            "frozen_heuristic_version": runner.TABLE_METHOD,
            "merge_recommendation": (
                "merge_all_text_table_detection_lanes"
            ),
            **{field: 0 for field in merger.AUDIT_ZERO_FIELDS},
            **{field: 0 for field in merger.FORBIDDEN_AUDIT_FIELDS},
        }
        audit_path = root / "audit.json"
        audit_path.write_text(
            json.dumps(audit, indent=2) + "\n", encoding="utf-8"
        )
        authority_rows = []
        for row in rows:
            authority = {
                field: row.get(field, "")
                for field in [
                    "pdf_readiness_id",
                    *merger.AUTHORITY_MATCH_FIELDS,
                ]
            }
            authority.update(
                {
                    "recommended_next_action": "parse_text_layer_later",
                    "text_layer_status": row["text_layer_status"],
                }
            )
            authority_rows.append(authority)
        authority_fields = list(
            dict.fromkeys(
                [
                    "pdf_readiness_id",
                    *merger.AUTHORITY_MATCH_FIELDS,
                    "recommended_next_action",
                ]
            )
        )
        readiness_path = root / "readiness.csv"
        write_csv(readiness_path, authority_rows, authority_fields)
        return argparse.Namespace(
            manifest=str(manifest_path),
            audit_summary=str(audit_path),
            pdf_readiness_ledger_csv=str(readiness_path),
            output_dir=str(root / "durable"),
            merge_id="TEST-TEXT-TABLE-MERGE",
        )

    def lane_ledger(
        self, args: argparse.Namespace, lane_id: str = "lane_1"
    ) -> Path:
        manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
        lane = next(
            item for item in manifest["lanes"] if item["lane_id"] == lane_id
        )
        return (
            Path(lane["future_local_output_dir"])
            / "text_table_detection_ledger.csv"
        )

    def mutate_lane(
        self,
        args: argparse.Namespace,
        mutator,
        lane_id: str = "lane_1",
    ) -> None:
        path = self.lane_ledger(args, lane_id)
        rows = read_csv(path)
        mutator(rows)
        write_csv(path, rows, runner.LEDGER_FIELDS)

    def test_merge_preserves_all_rows_and_detection_fields(self):
        with tempfile.TemporaryDirectory() as raw:
            args = self.merge_fixture(Path(raw))
            summary = merger.merge(args)
            rows = read_csv(
                Path(args.output_dir)
                / merger.OUTPUT_NAMES["ledger"]
            )
            self.assertEqual(summary["full_parse_text_rows_merged"], 4)
            self.assertEqual(len(rows), 4)
            self.assertEqual(
                {row["table_detection_method"] for row in rows},
                {runner.TABLE_METHOD},
            )
            self.assertEqual(
                {row["candidate_wage_pages"] for row in rows}, {"1"}
            )
            self.assertTrue(
                all(
                    row["text_table_detection_stage"] == merger.STAGE
                    for row in rows
                )
            )
            self.assertTrue(
                summary["exact_parse_text_authority_equality"][
                    "pdf_readiness_id_set_equal"
                ]
            )
            self.assertEqual(summary["urls_opened"], 0)
            self.assertEqual(summary["network_calls"], 0)
            self.assertEqual(summary["final_wage_values_extracted"], 0)

    def test_duplicate_identity_fields_fail(self):
        for field in merger.IDENTITY_FIELDS:
            with self.subTest(field=field):
                with tempfile.TemporaryDirectory() as raw:
                    args = self.merge_fixture(Path(raw))

                    def duplicate(rows):
                        rows[1][field] = rows[0][field]

                    self.mutate_lane(args, duplicate)
                    with self.assertRaisesRegex(
                        ValueError, f"duplicate identity: {field}"
                    ):
                        merger.merge(args)

    def test_nonterminal_row_fails(self):
        with tempfile.TemporaryDirectory() as raw:
            args = self.merge_fixture(Path(raw))
            self.mutate_lane(
                args,
                lambda rows: rows[0].__setitem__(
                    "detection_status", runner.DRY_STATUS
                ),
            )
            with self.assertRaisesRegex(ValueError, "nonterminal"):
                merger.merge(args)

    def test_non_merge_eligible_audit_fails(self):
        with tempfile.TemporaryDirectory() as raw:
            args = self.merge_fixture(Path(raw))
            path = Path(args.audit_summary)
            audit = json.loads(path.read_text(encoding="utf-8"))
            audit["merge_recommendation"] = "do_not_merge"
            path.write_text(json.dumps(audit), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "not merge eligible"):
                merger.merge(args)

    def test_authority_identity_mismatch_fails(self):
        with tempfile.TemporaryDirectory() as raw:
            args = self.merge_fixture(Path(raw))
            path = Path(args.pdf_readiness_ledger_csv)
            fields, rows = merger.read_csv(path)
            rows[0]["pdf_readiness_id"] = "different_authority_id"
            write_csv(path, rows, fields)
            with self.assertRaisesRegex(ValueError, "identity mismatch"):
                merger.merge(args)

    def test_authority_artifact_mismatch_fails(self):
        with tempfile.TemporaryDirectory() as raw:
            args = self.merge_fixture(Path(raw))
            path = Path(args.pdf_readiness_ledger_csv)
            fields, rows = merger.read_csv(path)
            rows[0]["content_hash"] = "f" * 64
            write_csv(path, rows, fields)
            with self.assertRaisesRegex(
                ValueError, "authority field mismatch"
            ):
                merger.merge(args)

    def test_existing_output_fails_closed(self):
        with tempfile.TemporaryDirectory() as raw:
            args = self.merge_fixture(Path(raw))
            Path(args.output_dir).mkdir()
            with self.assertRaises(FileExistsError):
                merger.merge(args)

    def test_merge_makes_no_network_calls_or_protected_mutations(self):
        protected = [
            ROOT / "data" / "contracts.csv",
            ROOT / "data" / "city_coverage.csv",
        ]
        before = {path: sha256(path) for path in protected}
        with tempfile.TemporaryDirectory() as raw:
            args = self.merge_fixture(Path(raw))
            with mock.patch.object(
                socket.socket,
                "connect",
                side_effect=AssertionError("network call attempted"),
            ):
                summary = merger.merge(args)
            self.assertEqual(summary["network_calls"], 0)
            self.assertEqual(summary["durable_text_table_merges"], 1)
        after = {path: sha256(path) for path in protected}
        self.assertEqual(before, after)


def main() -> int:
    suite = unittest.TestSuite(
        [
            unittest.defaultTestLoader.loadTestsFromTestCase(
                TextTableDetectionTests
            ),
            unittest.defaultTestLoader.loadTestsFromTestCase(
                TextTableDetectionMergeTests
            ),
        ]
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
