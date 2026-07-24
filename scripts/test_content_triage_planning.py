#!/usr/bin/env python3
"""Offline tests for content-triage planning, metadata triage, and lane audit."""

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
from unittest.mock import patch


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import audit_content_triage_lanes as auditor  # noqa: E402
import content_triage_sources as runner  # noqa: E402
import prepare_content_triage_batches as planner  # noqa: E402


PROTECTED = [
    ROOT / "data" / "contracts.csv",
    ROOT / "data" / "city_coverage.csv",
    ROOT / "docs" / "analysis" / "national_scout_candidate_queue_2026-07-20.csv",
    ROOT
    / "docs"
    / "analysis"
    / "verification_ledgers"
    / "verified_source_routing_ledger_cumulative.csv",
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0])
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def synthetic_inputs(base: Path) -> tuple[Path, Path]:
    queue_rows: list[dict[str, str]] = []
    routing_rows: list[dict[str, str]] = []
    specifications: list[tuple[str, str, str, str]] = []
    specifications.extend(
        ("reachable_pdf_or_document", "high_priority_later_verify", "cba", "application/pdf")
        for _ in range(1050)
    )
    specifications.extend(
        ("reachable_html", "high_priority_later_verify", "index_page", "text/html")
        for _ in range(20)
    )
    specifications.extend(
        ("reachable_pdf_or_document", "context_only_hold", "context_only", "application/pdf")
        for _ in range(50)
    )
    specifications.extend(
        ("duplicate_of_verified_source", "likely_duplicate_hold", "cba", "application/pdf")
        for _ in range(20)
    )
    for status in (
        "too_large",
        "blocked_or_forbidden",
        "not_found",
        "error",
        "timeout",
        "connection_error",
    ):
        specifications.extend(
            (status, "high_priority_later_verify", "cba", "application/pdf")
            for _ in range(10)
        )
    for index, (status, bucket, source_type, content_type) in enumerate(
        specifications, start=1
    ):
        queue_id = f"Q-{index:05d}"
        state = ["OH", "CA", "IL", "WA"][index % 4]
        municipality_id = f"M-{index // 3:05d}"
        group_id = (
            "URL-DUPLICATE-ONE"
            if index in {1, 2, 3}
            else f"URL-{index:05d}"
        )
        disposition = {
            "high_priority_later_verify": "scheduled",
            "context_only_hold": "context_hold",
            "likely_duplicate_hold": "duplicate_hold",
        }[bucket]
        queue_rows.append(
            {
                "queue_id": queue_id,
                "municipality_id": municipality_id,
                "state": state,
                "municipality": f"City {index}",
                "source_url": f"https://example.gov/{index}.pdf",
                "document_title": f"Collective agreement {index}",
                "document_type_scouted": source_type,
                "source_owner_type": "city",
                "unit_type_scouted": (
                    "police" if index % 3 == 0 else "non_safety"
                ),
                "triage_bucket": bucket,
            }
        )
        routing_rows.append(
            {
                "verification_id": f"VER-{index:05d}",
                "candidate_queue_row_id": queue_id,
                "verification_round_id": "SYNTH-ROUTING",
                "municipality_id": municipality_id,
                "census_gov_id": str(100000 + index),
                "state": state,
                "municipality": f"City {index}",
                "government_name": f"CITY {index}",
                "candidate_url": f"https://example.gov/{index}.pdf",
                "final_url": f"https://example.gov/{index}.pdf",
                "candidate_title": f"Collective agreement {index}",
                "candidate_source_type": source_type,
                "candidate_status_before_verification": disposition,
                "verification_status": status,
                "content_type": content_type,
                "duplicate_source_group_id": group_id,
                "verification_lane_id": "lane_1",
                "verification_stage": "url_reachability_metadata_verified",
            }
        )
    queue_path = base / "queue.csv"
    routing_path = base / "routing.csv"
    write_csv(queue_path, queue_rows)
    write_csv(routing_path, routing_rows)
    return routing_path, queue_path


def args_for(
    routing: Path,
    queue: Path,
    output: Path,
    **overrides: object,
) -> argparse.Namespace:
    values: dict[str, object] = {
        "routing_ledger_csv": routing.as_posix(),
        "candidate_queue_csv": queue.as_posix(),
        "output_dir": output.as_posix(),
        "round_id": "SYNTH-CONTENT-TRIAGE",
        "batch_size": 1000,
        "num_lanes": 2,
        "priority_scope": "scheduled_high_priority_reachable",
        "include_html": True,
        "include_duplicates": False,
        "include_lower_disposition": False,
        "exclude_too_large": True,
        "plan_only": True,
    }
    values.update(overrides)
    return argparse.Namespace(**values)


class ContentTriagePlanningTests(unittest.TestCase):
    def setUp(self) -> None:
        self.before = {path: sha(path) for path in PROTECTED}

    def tearDown(self) -> None:
        self.assertEqual(self.before, {path: sha(path) for path in PROTECTED})

    def test_planner_selects_reachable_high_scheduled_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            routing, queue = synthetic_inputs(root)
            result = planner.prepare(args_for(routing, queue, root / "plan"))
            manifest = result["manifest"]
            self.assertEqual(manifest["selected_rows"], 1000)
            self.assertEqual([len(lane) for lane in result["lanes"]], [500, 500])
            self.assertEqual(manifest["too_large_rows_deferred"], 10)
            self.assertEqual(
                manifest["blocked_not_found_error_transport_rows_deferred"], 50
            )
            self.assertEqual(manifest["lower_disposition_rows_selected"], 0)
            self.assertTrue(
                all(
                    row["verification_status"]
                    in planner.ELIGIBLE_ROUTING_STATUSES
                    for row in result["selected"]
                )
            )
            self.assertTrue(
                all(
                    row["candidate_status_before_verification"] == "scheduled"
                    for row in result["selected"]
                )
            )

    def test_duplicate_groups_preserved_and_linked_rows_excluded_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            routing, queue = synthetic_inputs(root)
            result = planner.prepare(args_for(routing, queue, root / "plan"))
            duplicate_rows = [
                row
                for row in result["selected"]
                if row["duplicate_source_group_id"] == "URL-DUPLICATE-ONE"
            ]
            self.assertEqual(len(duplicate_rows), 1)
            self.assertEqual(
                duplicate_rows[0]["duplicate_group_role_for_triage"],
                "canonical_representative",
            )
            self.assertGreater(
                result["manifest"]["linked_duplicate_rows_in_routing_eligible_pool"],
                0,
            )

    def test_include_duplicates_and_lower_dispositions_is_explicit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            routing, queue = synthetic_inputs(root)
            result = planner.prepare(
                args_for(
                    routing,
                    queue,
                    root / "plan",
                    batch_size=1200,
                    priority_scope="all_reachable",
                    include_duplicates=True,
                    include_lower_disposition=True,
                )
            )
            self.assertTrue(
                any(
                    row["duplicate_group_role_for_triage"] == "linked_duplicate"
                    for row in result["selected"]
                )
            )
            self.assertTrue(
                any(
                    row["candidate_status_before_verification"] == "context_hold"
                    for row in result["selected"]
                )
            )

    def test_dry_run_writes_terminal_schema_without_network_or_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            routing, queue = synthetic_inputs(root)
            result = planner.prepare(args_for(routing, queue, root / "plan"))
            lane_path = Path(result["manifest"]["lanes"][0]["input_csv"])
            dry_args = argparse.Namespace(
                input_csv=lane_path.as_posix(),
                output_dir=(root / "dry").as_posix(),
                dry_run=True,
                max_rows=None,
                review_mode="metadata_only",
                write_content_samples=False,
                no_write_content_samples=True,
            )
            with patch.object(
                socket,
                "create_connection",
                side_effect=AssertionError("network call attempted"),
            ):
                summary = runner.dry_run(dry_args)
            self.assertEqual(summary["planned_rows"], 500)
            self.assertEqual(summary["terminal_planned_rows"], 500)
            self.assertEqual(summary["urls_opened"], 0)
            self.assertEqual(summary["network_calls"], 0)
            self.assertEqual(summary["content_artifacts_written"], 0)
            ledger = list(
                csv.DictReader(
                    (root / "dry" / "triage_ledger.csv").open(
                        newline="", encoding="utf-8"
                    )
                )
            )
            self.assertEqual(len(ledger), 500)
            self.assertTrue(all(row["triage_status"] == "triage_planned" for row in ledger))

    def test_auditor_classifies_two_dry_lanes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            routing, queue = synthetic_inputs(root)
            result = planner.prepare(args_for(routing, queue, root / "plan"))
            for index, lane in enumerate(result["manifest"]["lanes"], start=1):
                lane["dry_run_output_dir"] = (root / f"lane_{index}_dry").as_posix()
                runner.dry_run(
                    argparse.Namespace(
                        input_csv=lane["input_csv"],
                        output_dir=lane["dry_run_output_dir"],
                        dry_run=True,
                        max_rows=None,
                        review_mode="metadata_only",
                        write_content_samples=False,
                        no_write_content_samples=True,
                    )
                )
            (root / "plan" / "content_triage_round_manifest.json").write_text(
                json.dumps(result["manifest"], indent=2) + "\n",
                encoding="utf-8",
            )
            payload = auditor.audit(
                root / "plan" / "content_triage_round_manifest.json",
                root / "audit",
            )
            self.assertEqual(
                payload["classification_counts"], {"dry_run_passed": 2}
            )
            self.assertEqual(payload["ledger_rows"], 1000)
            self.assertEqual(payload["terminal_rows"], 1000)
            self.assertEqual(
                payload["merge_recommendation"],
                "dry_run_complete_do_not_merge_live_triage",
            )
            self.assertEqual(payload["urls_opened"], 0)

    def test_live_mode_is_guarded_not_implemented(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            routing, queue = synthetic_inputs(root)
            result = planner.prepare(
                args_for(routing, queue, root / "plan", batch_size=10)
            )
            with self.assertRaisesRegex(ValueError, "not implemented"):
                runner.run(
                    argparse.Namespace(
                        input_csv=result["manifest"]["lanes"][0]["input_csv"],
                        output_dir=(root / "live").as_posix(),
                        dry_run=False,
                        max_rows=None,
                        review_mode="content_review",
                        write_content_samples=False,
                        no_write_content_samples=True,
                    )
                )

    def test_metadata_only_classifies_cba_pdf_without_network(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            routing, queue = synthetic_inputs(root)
            result = planner.prepare(
                args_for(routing, queue, root / "plan", batch_size=10)
            )
            metadata_args = argparse.Namespace(
                input_csv=result["manifest"]["lanes"][0]["input_csv"],
                output_dir=(root / "metadata").as_posix(),
                dry_run=False,
                max_rows=None,
                review_mode="metadata_only",
                write_content_samples=False,
                no_write_content_samples=True,
            )
            with patch.object(
                socket,
                "create_connection",
                side_effect=AssertionError("network call attempted"),
            ):
                summary = runner.run(metadata_args)
            self.assertEqual(summary["status"], "metadata_only_completed")
            self.assertEqual(summary["urls_opened"], 0)
            self.assertEqual(summary["network_calls"], 0)
            self.assertEqual(summary["documents_downloaded"], 0)
            self.assertEqual(summary["documents_parsed"], 0)
            rows = list(
                csv.DictReader(
                    (root / "metadata" / "triage_ledger.csv").open(
                        newline="", encoding="utf-8"
                    )
                )
            )
            self.assertTrue(rows)
            self.assertTrue(
                all(
                    row["triage_status"] == "high_priority_content_review"
                    for row in rows
                )
            )
            self.assertTrue(
                all(row["extraction_readiness_prelim"] == "medium" for row in rows)
            )
            self.assertTrue(
                all(row["source_relevance_prelim"] == "likely_relevant" for row in rows)
            )
            self.assertTrue(
                all(
                    row["recommended_next_action"]
                    == "content_review_download_allowed_later"
                    for row in rows
                )
            )
            self.assertTrue(all(row["reviewer"] == "script_metadata_only" for row in rows))

    def test_missing_classification_metadata_needs_manual_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            routing, queue = synthetic_inputs(root)
            result = planner.prepare(
                args_for(routing, queue, root / "plan", batch_size=2)
            )
            lane_path = Path(result["manifest"]["lanes"][0]["input_csv"])
            rows = list(csv.DictReader(lane_path.open(newline="", encoding="utf-8")))
            rows[0]["candidate_source_type"] = ""
            write_csv(lane_path, rows)
            summary = runner.run(
                argparse.Namespace(
                    input_csv=lane_path.as_posix(),
                    output_dir=(root / "metadata").as_posix(),
                    dry_run=False,
                    max_rows=None,
                    review_mode="metadata_only",
                    write_content_samples=False,
                    no_write_content_samples=True,
                )
            )
            self.assertEqual(summary["triage_status_counts"], {"needs_manual_review": 1})
            output = list(
                csv.DictReader(
                    (root / "metadata" / "triage_ledger.csv").open(
                        newline="", encoding="utf-8"
                    )
                )
            )[0]
            self.assertEqual(output["recommended_next_action"], "manual_review")
            self.assertIn("candidate_source_type", output["manual_review_reason"])

    def test_auditor_classifies_two_metadata_only_lanes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            routing, queue = synthetic_inputs(root)
            result = planner.prepare(
                args_for(routing, queue, root / "plan", batch_size=20)
            )
            for index, lane in enumerate(result["manifest"]["lanes"], start=1):
                metadata_dir = root / f"lane_{index}_metadata"
                lane["metadata_only_output_dir"] = metadata_dir.as_posix()
                runner.run(
                    argparse.Namespace(
                        input_csv=lane["input_csv"],
                        output_dir=metadata_dir.as_posix(),
                        dry_run=False,
                        max_rows=None,
                        review_mode="metadata_only",
                        write_content_samples=False,
                        no_write_content_samples=True,
                    )
                )
            manifest_path = root / "plan" / "content_triage_round_manifest.json"
            manifest_path.write_text(
                json.dumps(result["manifest"], indent=2) + "\n",
                encoding="utf-8",
            )
            payload = auditor.audit(manifest_path, root / "audit")
            self.assertEqual(
                payload["classification_counts"], {"completed_merge_eligible": 2}
            )
            self.assertEqual(payload["ledger_rows"], 20)
            self.assertEqual(payload["terminal_rows"], 20)
            self.assertEqual(
                payload["merge_recommendation"],
                "merge_all_content_triage_lanes",
            )
            self.assertEqual(payload["urls_opened"], 0)
            self.assertEqual(payload["documents_downloaded"], 0)
            self.assertEqual(payload["content_artifacts_written"], 0)
            self.assertEqual(
                payload["recommended_next_action_counts"],
                {"content_review_download_allowed_later": 20},
            )


def main() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        ContentTriagePlanningTests
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print(
        f"Content-triage planning checks: {result.testsRun}; "
        "network calls: 0; protected-file mutations: 0."
    )
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
