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
import merge_pdf_readiness_lanes as merger
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


class PdfReadinessMergeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.protected_before = {
            path: file_hash(path) for path in PROTECTED if path.exists()
        }

    def tearDown(self) -> None:
        for path, digest in self.protected_before.items():
            self.assertEqual(file_hash(path), digest)
        self.temp.cleanup()

    def source_row(self, index: int) -> dict[str, str]:
        return {
            "source_review_id": f"source-{index}",
            "candidate_queue_row_id": f"candidate-{index}",
            "triage_id": f"triage-{index}",
            "verification_id": f"verification-{index}",
            "source_review_pilot_id": (
                "SOURCE-REVIEW-PILOT1"
                if index < 2
                else "SOURCE-REVIEW-BATCH2"
            ),
            "state": ["OH", "MA", "CA", "IL"][index],
            "municipality": f"Municipality {index}",
            "government_name": f"Government {index}",
            "unit_type_scouted": ["police", "fire", "non_safety", "police"][
                index
            ],
            "candidate_source_type": "cba",
            "priority_for_content_review": "p1" if index < 3 else "p2",
            "source_officialness_rating": "official_municipal",
            "source_relevance_rating": "possible",
            "document_type_rating": "cba_candidate",
            "extraction_readiness_rating": "medium",
            "content_artifact_path": f"/retained/lane_{index}/artifact.pdf",
            "content_hash": f"{index + 1:064x}",
            "content_byte_size": str(1000 + index),
            "content_type_observed": "application/pdf",
            "source_review_status": "reviewed_metadata_and_artifact_saved",
        }

    def readiness_row(
        self, source: dict[str, str], round_id: str, lane_id: str
    ) -> dict[str, str]:
        text_status = (
            "present"
            if source["source_review_id"] in {"source-0", "source-2"}
            else "partial"
            if source["source_review_id"] == "source-1"
            else "absent"
        )
        parseability = {
            "present": "high",
            "partial": "medium",
            "absent": "low",
        }[text_status]
        return {
            "pdf_readiness_id": f"readiness-{source['source_review_id']}",
            "source_review_id": source["source_review_id"],
            "candidate_queue_row_id": source["candidate_queue_row_id"],
            "triage_id": source["triage_id"],
            "verification_id": source["verification_id"],
            "source_review_pilot_id": source["source_review_pilot_id"],
            "state": source["state"],
            "municipality": source["municipality"],
            "government_name": source["government_name"],
            "unit_type": source["unit_type_scouted"],
            "candidate_source_type": source["candidate_source_type"],
            "priority_for_content_review": source[
                "priority_for_content_review"
            ],
            "source_officialness_rating": source[
                "source_officialness_rating"
            ],
            "source_relevance_rating": source["source_relevance_rating"],
            "document_type_rating": source["document_type_rating"],
            "extraction_readiness_rating": source[
                "extraction_readiness_rating"
            ],
            "content_artifact_path": source["content_artifact_path"],
            "content_hash": source["content_hash"],
            "content_byte_size": source["content_byte_size"],
            "content_type_observed": source["content_type_observed"],
            "pdf_readiness_pilot_id": round_id,
            "pdf_readiness_lane_id": lane_id,
            "pilot_selection_rank": "1",
            "artifact_byte_size_bin": "small_le_512_kib",
            "sample_selection_reason": "test",
            "readiness_status": "readiness_checked",
            "readiness_status_detail": "bounded technical check complete",
            "artifact_exists": "yes",
            "artifact_hash_verified": "yes",
            "pdf_signature_valid": "yes",
            "parser_library": "pypdf",
            "parser_version": "test",
            "parser_elapsed_seconds": "0.1",
            "pdf_page_count": str(10 + int(source["source_review_id"][-1])),
            "text_layer_status": text_status,
            "sampled_pages_checked": "3",
            "sampled_pages_with_text": (
                "3" if text_status == "present" else "1"
                if text_status == "partial"
                else "0"
            ),
            "text_chars_sampled_total": (
                "100" if text_status != "absent" else "0"
            ),
            "text_extraction_error_type": "",
            "text_extraction_error_sanitized": "",
            "technical_parseability_rating": parseability,
            "recommended_next_action": (
                "ocr_later"
                if text_status == "absent"
                else "parse_text_layer_later"
            ),
            "ocr_needed_signal": "yes" if text_status == "absent" else "no",
            "reviewer": "test",
            "reviewed_at": "2026-07-24T00:00:00Z",
        }

    def build_fixture(
        self,
        base: Path,
        *,
        row_mutator: object | None = None,
        source_mutator: object | None = None,
        audit_mutator: object | None = None,
    ) -> tuple[argparse.Namespace, list[dict[str, str]]]:
        base.mkdir(parents=True)
        source_rows = [self.source_row(index) for index in range(4)]
        if callable(source_mutator):
            source_mutator(source_rows)
        source_path = base / "source_review.csv"
        write_csv(source_path, source_rows)
        manifests: list[str] = []
        audits: list[str] = []
        readiness_rows: list[dict[str, str]] = []
        for round_index, indexes in enumerate(((0, 1), (2, 3)), start=1):
            round_id = f"PDF-ROUND-{round_index}"
            lane_id = "lane_1"
            lane_dir = base / f"round_{round_index}_local"
            lane_dir.mkdir()
            rows = [
                self.readiness_row(
                    self.source_row(index), round_id, lane_id
                )
                for index in indexes
            ]
            readiness_rows.extend(rows)
            ledger = lane_dir / "pdf_readiness_ledger.csv"
            write_csv(ledger, rows)
            manifest_path = base / f"round_{round_index}_manifest.json"
            manifest = {
                "pilot_id": round_id,
                "selected_rows": 2,
                "lanes": [
                    {
                        "lane_id": lane_id,
                        "expected_rows": 2,
                        "future_local_output_dir": lane_dir.as_posix(),
                    }
                ],
            }
            manifest_path.write_text(
                json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
            )
            audit_path = base / f"round_{round_index}_audit.json"
            audit = {
                "pilot_id": round_id,
                "manifest": manifest_path.as_posix(),
                "planned_rows": 2,
                "ledger_rows": 2,
                "terminal_rows": 2,
                "lane_classification_counts": {
                    "completed_merge_eligible": 1
                },
                "lanes": [
                    {
                        "lane_id": lane_id,
                        "classification": "completed_merge_eligible",
                        "mode": "local",
                        "no_forbidden_activity": True,
                        "terminal_rows": 2,
                    }
                ],
                "cross_lane_duplicate_pdf_readiness_ids": 0,
                "cross_lane_duplicate_source_review_ids": 0,
                "cross_lane_duplicate_candidate_queue_ids": 0,
                "hash_failures": 0,
                "missing_artifacts": 0,
                "parser_errors": 0,
                "urls_opened": 0,
                "network_calls": 0,
                "downloads": 0,
                "ocr_runs": 0,
                "full_text_artifacts_written": 0,
                "wage_values_extracted": 0,
                "ingestion_actions": 0,
                "codify_actions": 0,
                "durable_readiness_merges": 0,
                "merge_recommendation": "merge_all_pdf_readiness_lanes",
            }
            if callable(audit_mutator):
                audit_mutator(audit, round_index)
            audit_path.write_text(
                json.dumps(audit, indent=2) + "\n", encoding="utf-8"
            )
            manifests.append(manifest_path.as_posix())
            audits.append(audit_path.as_posix())
        if callable(row_mutator):
            row_mutator(base, readiness_rows)
            for round_index in (1, 2):
                indexes = (0, 1) if round_index == 1 else (2, 3)
                write_csv(
                    base
                    / f"round_{round_index}_local"
                    / "pdf_readiness_ledger.csv",
                    [readiness_rows[index] for index in indexes],
                )
        return (
            argparse.Namespace(
                manifest=manifests,
                audit_summary=audits,
                source_review_ledger_csv=source_path.as_posix(),
                output_dir=(base / "durable").as_posix(),
                merge_id="PDF-MERGE-TEST",
            ),
            readiness_rows,
        )

    def test_merge_preserves_all_round_rows_and_readiness_fields(self) -> None:
        args, input_rows = self.build_fixture(self.base / "preserve")
        with mock.patch.object(
            socket,
            "create_connection",
            side_effect=AssertionError("network attempted"),
        ):
            summary = merger.merge(args)
        output = Path(args.output_dir)
        _, merged = merger.read_csv(
            output / "pdf_readiness_ledger_cumulative.csv"
        )
        self.assertEqual(len(merged), 4)
        self.assertEqual(summary["pdf_readiness_rows_merged"], 4)
        self.assertEqual(summary["retained_pdf_artifacts_available"], 4)
        self.assertEqual(
            summary["text_layer_status_counts"],
            {"absent": 1, "partial": 1, "present": 2},
        )
        by_id = {row["pdf_readiness_id"]: row for row in merged}
        for source in input_rows:
            result = by_id[source["pdf_readiness_id"]]
            for field in (
                "content_artifact_path",
                "content_hash",
                "content_byte_size",
                "content_type_observed",
                "pdf_page_count",
                "text_layer_status",
                "technical_parseability_rating",
                "recommended_next_action",
            ):
                self.assertEqual(result[field], source[field])
            self.assertEqual(
                result["pdf_readiness_stage"],
                "technical_readiness_checked_not_extracted",
            )
        self.assertEqual(
            (
                output / "pdf_readiness_ledger_cumulative.csv"
            ).read_bytes(),
            (output / "pdf_readiness_ledger_latest.csv").read_bytes(),
        )
        self.assertEqual(
            (
                output / "pdf_readiness_summary_cumulative.json"
            ).read_bytes(),
            (output / "pdf_readiness_summary_latest.json").read_bytes(),
        )
        for field in merger.FORBIDDEN_COUNTER_FIELDS:
            self.assertEqual(summary[field], 0)
        self.assertEqual(summary["durable_readiness_merges"], 1)

    def test_duplicate_identities_fail(self) -> None:
        for field in (
            "pdf_readiness_id",
            "source_review_id",
            "candidate_queue_row_id",
        ):
            with self.subTest(field=field):
                def mutate(
                    _base: Path,
                    rows: list[dict[str, str]],
                    target: str = field,
                ) -> None:
                    rows[2][target] = rows[0][target]

                args, _ = self.build_fixture(
                    self.base / f"duplicate_{field}",
                    row_mutator=mutate,
                )
                with self.assertRaisesRegex(ValueError, "duplicate identity"):
                    merger.merge(args)

    def test_missing_terminal_row_fails(self) -> None:
        def mutate(_base: Path, rows: list[dict[str, str]]) -> None:
            rows[0]["readiness_status"] = "planned_not_checked"

        args, _ = self.build_fixture(
            self.base / "nonterminal", row_mutator=mutate
        )
        with self.assertRaisesRegex(ValueError, "nonterminal readiness"):
            merger.merge(args)

    def test_non_merge_eligible_audit_fails(self) -> None:
        def mutate(audit: dict[str, object], round_index: int) -> None:
            if round_index == 2:
                audit["merge_recommendation"] = (
                    "do_not_merge_until_resume_or_review"
                )

        args, _ = self.build_fixture(
            self.base / "bad_audit", audit_mutator=mutate
        )
        with self.assertRaisesRegex(ValueError, "not merge eligible"):
            merger.merge(args)

    def test_retained_source_review_identity_mismatch_fails(self) -> None:
        def mutate(rows: list[dict[str, str]]) -> None:
            rows.pop()

        args, _ = self.build_fixture(
            self.base / "authority_identity", source_mutator=mutate
        )
        with self.assertRaisesRegex(ValueError, "identity mismatch"):
            merger.merge(args)

    def test_authority_artifact_field_mismatches_fail(self) -> None:
        for field in (
            "content_artifact_path",
            "content_hash",
            "content_byte_size",
            "content_type_observed",
        ):
            with self.subTest(field=field):
                def mutate(
                    _base: Path,
                    rows: list[dict[str, str]],
                    target: str = field,
                ) -> None:
                    rows[0][target] = "mismatch"

                args, _ = self.build_fixture(
                    self.base / f"authority_{field}",
                    row_mutator=mutate,
                )
                with self.assertRaisesRegex(
                    ValueError, "authority field mismatch"
                ):
                    merger.merge(args)

    def test_forbidden_activity_audit_fails(self) -> None:
        def mutate(audit: dict[str, object], round_index: int) -> None:
            if round_index == 1:
                audit["downloads"] = 1

        args, _ = self.build_fixture(
            self.base / "forbidden", audit_mutator=mutate
        )
        with self.assertRaisesRegex(ValueError, "forbidden audit counter"):
            merger.merge(args)

    def test_existing_durable_target_fails_closed(self) -> None:
        args, _ = self.build_fixture(self.base / "existing")
        Path(args.output_dir).mkdir()
        with self.assertRaises(FileExistsError):
            merger.merge(args)


if __name__ == "__main__":
    unittest.main(verbosity=2)
