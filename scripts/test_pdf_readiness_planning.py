#!/usr/bin/env python3
"""Offline/mock tests for PDF-readiness planning, parsing, and auditing."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import socket
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from pypdf import PdfWriter
from reportlab.pdfgen import canvas

import audit_pdf_readiness_lanes as auditor
import pdf_readiness_sources as runner
import prepare_pdf_readiness_pilot as planner


ROOT = Path(__file__).resolve().parent.parent
PROTECTED = [
    ROOT / "data" / "contracts.csv",
    ROOT / "data" / "city_coverage.csv",
    ROOT
    / "docs"
    / "analysis"
    / "verification_ledgers"
    / "verified_source_routing_ledger_cumulative.csv",
    ROOT
    / "docs"
    / "analysis"
    / "content_triage_ledgers"
    / "content_triage_metadata_ledger_cumulative.csv",
    ROOT
    / "docs"
    / "analysis"
    / "source_review_ledgers"
    / "source_review_ledger_cumulative.csv",
]


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    fields = list(rows[0])
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def make_text_pdf(path: Path, text: str = "Technical readiness text") -> None:
    pdf = canvas.Canvas(path.as_posix())
    pdf.drawString(72, 720, text)
    pdf.showPage()
    pdf.save()


def make_blank_pdf(path: Path) -> None:
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    with path.open("wb") as handle:
        writer.write(handle)


class PdfReadinessPlanningTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.text_pdf = self.base / "text.pdf"
        self.blank_pdf = self.base / "blank.pdf"
        make_text_pdf(self.text_pdf)
        make_blank_pdf(self.blank_pdf)
        self.source_ledger = self.base / "source_review.csv"
        self.source_rows = self.build_source_rows(180)
        write_csv(self.source_ledger, self.source_rows)
        self.protected_before = {
            path: file_hash(path) for path in PROTECTED if path.exists()
        }

    def tearDown(self) -> None:
        for path, digest in self.protected_before.items():
            self.assertEqual(file_hash(path), digest)
        self.temp.cleanup()

    def build_source_rows(self, count: int) -> list[dict[str, str]]:
        states = ["OH", "MA", "CA", "IL", "TX", "WA"]
        officialness = [
            "official_municipal",
            "official_state_repository",
            "official_union",
            "uncertain",
            "unknown",
        ]
        units = ["police", "fire", "non_safety"]
        batches = [
            "SOURCE-REVIEW-PILOT1-150-2026-07-24",
            "SOURCE-REVIEW-BATCH2-500-2026-07-24",
            "SOURCE-REVIEW-BATCH3-3X500-2026-07-24",
        ]
        rows: list[dict[str, str]] = []
        for index in range(count):
            artifact = self.text_pdf if index % 2 == 0 else self.blank_pdf
            rows.append(
                {
                    "source_review_id": f"sr-{index:04d}",
                    "candidate_queue_row_id": f"cq-{index:04d}",
                    "triage_id": f"tri-{index:04d}",
                    "verification_id": f"ver-{index:04d}",
                    "source_review_pilot_id": batches[index % len(batches)],
                    "source_review_merged_at": "2026-07-24T00:00:00Z",
                    "state": states[index % len(states)],
                    "municipality": f"Municipality {index}",
                    "government_name": f"Government {index}",
                    "unit_type_scouted": units[index % len(units)],
                    "candidate_source_type": (
                        "cba"
                        if index % 4
                        else "wage_schedule_or_compensation_plan"
                    ),
                    "priority_for_content_review": (
                        "p1" if index % 4 else "p2"
                    ),
                    "source_officialness_rating": officialness[
                        index % len(officialness)
                    ],
                    "source_relevance_rating": "possible",
                    "document_type_rating": (
                        "cba_candidate" if index % 5 else "unknown"
                    ),
                    "extraction_readiness_rating": "medium",
                    "content_artifact_path": artifact.as_posix(),
                    "content_hash": file_hash(artifact),
                    "content_byte_size": str(artifact.stat().st_size),
                    "content_type_observed": "application/pdf",
                    "source_review_status": (
                        "reviewed_metadata_and_artifact_saved"
                    ),
                }
            )
        return rows

    def plan_args(
        self,
        output: Path,
        *,
        sample_size: int = 150,
        num_lanes: int = 3,
        all_remaining: bool = False,
        exclusion_paths: list[Path] | None = None,
    ) -> argparse.Namespace:
        return argparse.Namespace(
            source_review_ledger_csv=self.source_ledger.as_posix(),
            output_dir=output.as_posix(),
            pilot_id="PDF-READINESS-TEST",
            sample_size=sample_size,
            all_remaining=all_remaining,
            num_lanes=num_lanes,
            balance_lanes=True,
            exclude_readiness_ledger_csv=[
                path.as_posix() for path in (exclusion_paths or [])
            ],
            state_diversity=True,
            include_prior_batches=True,
            plan_only=True,
        )

    def run_args(
        self, input_csv: Path, output: Path, *, dry_run: bool
    ) -> argparse.Namespace:
        return argparse.Namespace(
            input_csv=input_csv.as_posix(),
            output_dir=output.as_posix(),
            max_rows=None,
            max_pages_to_sample=3,
            max_text_chars_per_page=500,
            timeout_per_file=20.0,
            no_save_text=True,
            dry_run=dry_run,
        )

    def test_planner_selects_only_retained_pdf_rows(self) -> None:
        bad = dict(self.source_rows[0])
        bad["source_review_id"] = "bad"
        bad["candidate_queue_row_id"] = "bad"
        bad["content_artifact_path"] = ""
        bad["content_hash"] = ""
        bad["source_review_status"] = "download_timeout"
        write_csv(self.source_ledger, self.source_rows + [bad])
        manifest = planner.create_plan(
            self.plan_args(self.base / "plan", sample_size=20)
        )
        self.assertEqual(manifest["selected_rows"], 20)
        for lane in manifest["lanes"]:
            _, rows = runner.read_csv(Path(lane["input_csv"]))
            self.assertTrue(all(row["content_artifact_path"] for row in rows))
            self.assertTrue(all(row["content_hash"] for row in rows))

    def test_planner_creates_150_balanced_across_three_lanes(self) -> None:
        manifest = planner.create_plan(self.plan_args(self.base / "plan"))
        self.assertEqual(manifest["selected_rows"], 150)
        self.assertEqual(manifest["lane_rows"], [50, 50, 50])
        all_rows: list[dict[str, str]] = []
        for lane in manifest["lanes"]:
            _, rows = runner.read_csv(Path(lane["input_csv"]))
            all_rows.extend(rows)
        self.assertEqual(len({row["pdf_readiness_id"] for row in all_rows}), 150)
        self.assertEqual(len({row["source_review_id"] for row in all_rows}), 150)
        self.assertEqual(
            set(row["source_review_pilot_id"] for row in all_rows),
            {
                "SOURCE-REVIEW-PILOT1-150-2026-07-24",
                "SOURCE-REVIEW-BATCH2-500-2026-07-24",
                "SOURCE-REVIEW-BATCH3-3X500-2026-07-24",
            },
        )

    def test_all_remaining_excludes_prior_readiness_and_balances_four_lanes(
        self,
    ) -> None:
        exclusion_paths: list[Path] = []
        excluded_review_ids: set[str] = set()
        for lane_index, source_subset in enumerate(
            (self.source_rows[:4], self.source_rows[4:7]), start=1
        ):
            rows = []
            for source in source_subset:
                excluded_review_ids.add(source["source_review_id"])
                rows.append(
                    {
                        "pdf_readiness_id": (
                            f"prior-{source['source_review_id']}"
                        ),
                        "source_review_id": source["source_review_id"],
                        "candidate_queue_row_id": source[
                            "candidate_queue_row_id"
                        ],
                        "readiness_status": "readiness_checked",
                    }
                )
            path = self.base / f"prior_lane_{lane_index}.csv"
            write_csv(path, rows)
            exclusion_paths.append(path)
        manifest = planner.create_plan(
            self.plan_args(
                self.base / "all_remaining_plan",
                num_lanes=4,
                all_remaining=True,
                exclusion_paths=exclusion_paths,
            )
        )
        self.assertEqual(manifest["eligible_retained_pdf_rows"], 180)
        self.assertEqual(manifest["excluded_readiness_rows"], 7)
        self.assertEqual(manifest["eligible_remaining_pdf_rows"], 173)
        self.assertEqual(manifest["selected_rows"], 173)
        self.assertEqual(manifest["lane_rows"], [44, 43, 43, 43])
        selected: list[dict[str, str]] = []
        for lane in manifest["lanes"]:
            _, lane_rows = runner.read_csv(Path(lane["input_csv"]))
            selected.extend(lane_rows)
        selected_review_ids = {
            row["source_review_id"] for row in selected
        }
        self.assertFalse(selected_review_ids & excluded_review_ids)
        self.assertEqual(
            selected_review_ids | excluded_review_ids,
            {row["source_review_id"] for row in self.source_rows},
        )
        self.assertEqual(
            len({row["candidate_queue_row_id"] for row in selected}),
            173,
        )

    def test_all_remaining_cli_accepts_repeatable_exclusions(self) -> None:
        args = planner.build_parser().parse_args(
            [
                "--source-review-ledger-csv",
                "source.csv",
                "--output-dir",
                "output",
                "--pilot-id",
                "PDF-READINESS-REMAINDER",
                "--all-remaining",
                "--num-lanes",
                "4",
                "--balance-lanes",
                "--include-prior-batches",
                "--exclude-readiness-ledger-csv",
                "lane_1.csv",
                "--exclude-readiness-ledger-csv",
                "lane_2.csv",
                "--plan-only",
            ]
        )
        self.assertTrue(args.all_remaining)
        self.assertTrue(args.balance_lanes)
        self.assertEqual(
            args.exclude_readiness_ledger_csv,
            ["lane_1.csv", "lane_2.csv"],
        )

    def one_input(self, artifact: Path) -> dict[str, str]:
        source = dict(self.source_rows[0])
        source["content_artifact_path"] = artifact.as_posix()
        source["content_hash"] = file_hash(artifact)
        source["content_byte_size"] = str(artifact.stat().st_size)
        row = {field: source.get(field, "") for field in planner.IDENTITY_FIELDS}
        row.update(
            {
                "pdf_readiness_id": "pr-test",
                "unit_type": source["unit_type_scouted"],
                "pdf_readiness_pilot_id": "PDF-READINESS-TEST",
                "pdf_readiness_lane_id": "lane_1",
                "pilot_selection_rank": "1",
                "artifact_byte_size_bin": "small_le_512_kib",
                "sample_selection_reason": "test",
            }
        )
        return row

    def test_hash_mismatch_is_terminal_not_ready(self) -> None:
        row = self.one_input(self.text_pdf)
        row["content_hash"] = "0" * 64
        result, _ = runner.inspect_artifact(
            row,
            max_pages_to_sample=3,
            max_text_chars_per_page=500,
            timeout_per_file=20,
        )
        self.assertEqual(result["readiness_status"], "hash_mismatch")
        self.assertEqual(result["technical_parseability_rating"], "not_ready")

    def test_missing_artifact_is_terminal_not_ready(self) -> None:
        row = self.one_input(self.text_pdf)
        row["content_artifact_path"] = (self.base / "missing.pdf").as_posix()
        result, _ = runner.inspect_artifact(
            row,
            max_pages_to_sample=3,
            max_text_chars_per_page=500,
            timeout_per_file=20,
        )
        self.assertEqual(result["readiness_status"], "artifact_missing")
        self.assertEqual(result["technical_parseability_rating"], "not_ready")

    def test_parser_error_is_terminal_parser_error(self) -> None:
        broken = self.base / "broken.pdf"
        broken.write_bytes(b"%PDF-broken")
        row = self.one_input(broken)
        result, _ = runner.inspect_artifact(
            row,
            max_pages_to_sample=3,
            max_text_chars_per_page=500,
            timeout_per_file=20,
        )
        self.assertEqual(result["readiness_status"], "parser_error")
        self.assertEqual(result["text_layer_status"], "parser_error")

    def test_text_pdf_is_present_without_saved_text(self) -> None:
        row = self.one_input(self.text_pdf)
        result, _ = runner.inspect_artifact(
            row,
            max_pages_to_sample=3,
            max_text_chars_per_page=500,
            timeout_per_file=20,
        )
        self.assertEqual(result["readiness_status"], "readiness_checked")
        self.assertEqual(result["text_layer_status"], "present")
        self.assertEqual(result["technical_parseability_rating"], "high")
        self.assertNotIn("Technical readiness text", str(result))

    def test_blank_pdf_is_absent(self) -> None:
        row = self.one_input(self.blank_pdf)
        result, _ = runner.inspect_artifact(
            row,
            max_pages_to_sample=3,
            max_text_chars_per_page=500,
            timeout_per_file=20,
        )
        self.assertEqual(result["text_layer_status"], "absent")
        self.assertEqual(result["recommended_next_action"], "ocr_later")

    def test_dry_run_opens_no_pdf(self) -> None:
        row = self.one_input(self.text_pdf)
        input_path = self.base / "dry_input.csv"
        planner.write_csv(input_path, [row])
        output = self.base / "dry"
        with mock.patch.object(
            runner,
            "inspect_artifact",
            side_effect=AssertionError("PDF opened"),
        ):
            summary = runner.run(self.run_args(input_path, output, dry_run=True))
        self.assertEqual(summary["terminal_rows"], 1)
        self.assertEqual(summary["local_artifacts_opened"], 0)

    def test_no_save_text_cli_flag_remains_enabled(self) -> None:
        args = runner.build_parser().parse_args(
            [
                "--input-csv",
                "input.csv",
                "--output-dir",
                "output",
                "--no-save-text",
            ]
        )
        self.assertTrue(args.no_save_text)

    def test_local_runner_makes_no_network_calls(self) -> None:
        row = self.one_input(self.text_pdf)
        input_path = self.base / "local_input.csv"
        planner.write_csv(input_path, [row])
        with mock.patch.object(
            socket,
            "create_connection",
            side_effect=AssertionError("network attempted"),
        ):
            summary = runner.run(
                self.run_args(input_path, self.base / "local", dry_run=False)
            )
        self.assertEqual(summary["network_calls"], 0)
        self.assertEqual(summary["urls_opened"], 0)
        self.assertEqual(summary["full_text_artifacts_written"], 0)

    def test_auditor_classifies_completed_lanes(self) -> None:
        plan_dir = self.base / "audit_plan"
        manifest = planner.create_plan(
            self.plan_args(plan_dir, sample_size=6, num_lanes=3)
        )
        for index, lane in enumerate(manifest["lanes"], start=1):
            local_dir = self.base / f"audit_local_{index}"
            lane["future_local_output_dir"] = local_dir.as_posix()
            lane["dry_run_output_dir"] = (
                self.base / f"audit_dry_absent_{index}"
            ).as_posix()
            with mock.patch.object(
                socket,
                "create_connection",
                side_effect=AssertionError("network attempted"),
            ):
                runner.run(
                    self.run_args(
                        Path(lane["input_csv"]),
                        local_dir,
                        dry_run=False,
                    )
                )
        manifest_path = plan_dir / "pdf_readiness_pilot_manifest.json"
        manifest_path.write_text(
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
        )
        result = auditor.audit(manifest_path, self.base / "audit_result")
        self.assertEqual(
            result["lane_classification_counts"],
            {"completed_merge_eligible": 3},
        )
        self.assertEqual(
            result["merge_recommendation"],
            "merge_all_pdf_readiness_lanes",
        )
        self.assertEqual(result["terminal_rows"], 6)


if __name__ == "__main__":
    unittest.main(verbosity=2)
