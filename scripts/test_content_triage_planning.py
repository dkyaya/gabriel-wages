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
import merge_content_triage_lanes as merger  # noqa: E402
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
    specifications.extend(
        ("duplicate_same_url_pending", "likely_duplicate_hold", "cba", "application/pdf")
        for _ in range(10)
    )
    specifications.extend(
        ("reachable_http", "medium_priority_later_verify", "ordinance_or_policy", "text/plain")
        for _ in range(10)
    )
    for status in (
        "too_large",
        "blocked_or_forbidden",
        "not_found",
        "error",
        "ssl_error",
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
            "medium_priority_later_verify": "scheduled",
            "low_priority_later_verify": "scheduled",
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
        "exclude_triage_ledger_csv": [],
        "include_nonreachable": False,
        "include_too_large": False,
        "metadata_only_all_statuses": False,
        "balance_lanes": False,
        "plan_only": True,
    }
    values.update(overrides)
    return argparse.Namespace(**values)


def make_merge_fixture(
    root: Path,
) -> tuple[list[Path], list[Path], Path, Path]:
    routing, queue = synthetic_inputs(root)
    plan = planner.prepare(
        args_for(
            routing,
            queue,
            root / "source_plan",
            batch_size=6,
            num_lanes=1,
        )
    )
    selected = [dict(row) for row in plan["selected"]]
    selected[-1]["candidate_status_before_verification"] = "context_hold"
    selected[-1]["triage_bucket"] = "context_only_hold"
    selected[-1]["candidate_priority"] = "low"
    selected[-1]["candidate_source_type"] = "context_only"
    selected[-1]["verification_status"] = "reachable_html"
    selected[-1]["content_type"] = "text/html"

    _, routing_rows = merger.read_csv(routing)
    selected_queue_ids = {
        row["candidate_queue_row_id"] for row in selected
    }
    routing_subset = [
        row
        for row in routing_rows
        if row["candidate_queue_row_id"] in selected_queue_ids
    ]
    routing_subset_path = root / "routing_subset.csv"
    write_csv(routing_subset_path, routing_subset)

    manifest_paths: list[Path] = []
    audit_paths: list[Path] = []
    for round_number, rows in enumerate((selected[:3], selected[3:]), start=1):
        round_id = f"SYNTH-METADATA-ROUND-{round_number}"
        round_dir = root / f"round_{round_number}"
        input_path = round_dir / "lane_1_content_triage_input.csv"
        write_csv(input_path, rows)
        metadata_dir = root / f"round_{round_number}_metadata"
        runner.run(
            argparse.Namespace(
                input_csv=input_path.as_posix(),
                output_dir=metadata_dir.as_posix(),
                dry_run=False,
                max_rows=None,
                review_mode="metadata_only",
                write_content_samples=False,
                no_write_content_samples=True,
            )
        )
        manifest = {
            "schema_version": "1.0.0",
            "round_id": round_id,
            "selected_rows": len(rows),
            "lanes": [
                {
                    "lane_id": "lane_1",
                    "input_csv": input_path.as_posix(),
                    "input_sha256": sha(input_path),
                    "expected_rows": len(rows),
                    "dry_run_output_dir": (
                        root / f"round_{round_number}_dry"
                    ).as_posix(),
                    "future_live_output_dir": (
                        root / f"round_{round_number}_live"
                    ).as_posix(),
                    "metadata_only_output_dir": metadata_dir.as_posix(),
                }
            ],
        }
        manifest_path = round_dir / "content_triage_round_manifest.json"
        manifest_path.write_text(
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
        )
        audit_dir = root / f"round_{round_number}_audit"
        auditor.audit(manifest_path, audit_dir)
        manifest_paths.append(manifest_path)
        audit_paths.append(
            audit_dir / "content_triage_lane_audit_summary.json"
        )
    return manifest_paths, audit_paths, routing_subset_path, root / "merged"


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
                manifest["blocked_not_found_error_transport_rows_deferred"], 60
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

    def test_all_routed_remainder_excludes_prior_and_balances_four_lanes(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            routing, queue = synthetic_inputs(root)
            routing_rows = list(
                csv.DictReader(routing.open(newline="", encoding="utf-8"))
            )
            excluded = [
                {
                    "triage_id": f"PRIOR-{index:03d}",
                    "candidate_queue_row_id": row["candidate_queue_row_id"],
                    "triage_status": "high_priority_content_review",
                }
                for index, row in enumerate(routing_rows[:10], start=1)
            ]
            excluded_path = root / "prior_triage.csv"
            write_csv(excluded_path, excluded)
            result = planner.prepare(
                args_for(
                    routing,
                    queue,
                    root / "remainder",
                    priority_scope="all_routed_remainder",
                    num_lanes=4,
                    batch_size=1000,
                    exclude_triage_ledger_csv=[excluded_path.as_posix()],
                    include_nonreachable=True,
                    include_too_large=True,
                    include_lower_disposition=True,
                    include_duplicates=True,
                    metadata_only_all_statuses=True,
                    balance_lanes=True,
                )
            )
            expected = len(routing_rows) - len(excluded)
            self.assertEqual(result["manifest"]["selected_rows"], expected)
            self.assertEqual(
                result["manifest"]["excluded_prior_triage_rows"], len(excluded)
            )
            self.assertEqual(
                result["manifest"]["selected_plus_excluded_rows"],
                len(routing_rows),
            )
            self.assertEqual(
                result["manifest"]["unselected_routed_rows_after_plan"], 0
            )
            lane_sizes = [len(lane) for lane in result["lanes"]]
            self.assertLessEqual(max(lane_sizes) - min(lane_sizes), 1)
            self.assertEqual(sum(lane_sizes), expected)
            selected_ids = {
                row["candidate_queue_row_id"] for row in result["selected"]
            }
            self.assertFalse(
                selected_ids.intersection(
                    row["candidate_queue_row_id"] for row in excluded
                )
            )
            self.assertEqual(
                set(result["manifest"]["selected_verification_status_distribution"]),
                planner.ELIGIBLE_ROUTING_STATUSES
                | planner.DEFERRED_ROUTING_STATUSES,
            )

    def test_metadata_only_all_statuses_are_terminal_and_conservative(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            routing, queue = synthetic_inputs(root)
            routing_rows = list(
                csv.DictReader(routing.open(newline="", encoding="utf-8"))
            )
            excluded_path = root / "prior_triage.csv"
            write_csv(
                excluded_path,
                [
                    {
                        "triage_id": "PRIOR-ONE",
                        "candidate_queue_row_id": routing_rows[0][
                            "candidate_queue_row_id"
                        ],
                        "triage_status": "high_priority_content_review",
                    }
                ],
            )
            result = planner.prepare(
                args_for(
                    routing,
                    queue,
                    root / "remainder",
                    priority_scope="all_routed_remainder",
                    num_lanes=4,
                    batch_size=1000,
                    exclude_triage_ledger_csv=[excluded_path.as_posix()],
                    include_nonreachable=True,
                    include_too_large=True,
                    include_lower_disposition=True,
                    include_duplicates=True,
                    metadata_only_all_statuses=True,
                    balance_lanes=True,
                )
            )
            sample_by_status: dict[str, dict[str, object]] = {}
            for row in result["selected"]:
                sample_by_status.setdefault(str(row["verification_status"]), row)
            sample_path = root / "all_status_sample.csv"
            planner.write_csv(sample_path, list(sample_by_status.values()))
            summary = runner.run(
                argparse.Namespace(
                    input_csv=sample_path.as_posix(),
                    output_dir=(root / "metadata").as_posix(),
                    dry_run=False,
                    max_rows=None,
                    review_mode="metadata_only",
                    write_content_samples=False,
                    no_write_content_samples=True,
                )
            )
            self.assertEqual(summary["urls_opened"], 0)
            self.assertEqual(summary["documents_downloaded"], 0)
            output = {
                row["verification_status"]: row
                for row in csv.DictReader(
                    (root / "metadata" / "triage_ledger.csv").open(
                        newline="", encoding="utf-8"
                    )
                )
            }
            self.assertEqual(
                output["too_large"]["triage_status"],
                "oversized_needs_separate_pass",
            )
            self.assertEqual(
                output["too_large"]["recommended_next_action"],
                "oversized_strategy_later",
            )
            for status in ("duplicate_of_verified_source", "duplicate_same_url_pending"):
                self.assertEqual(
                    output[status]["triage_status"],
                    "duplicate_defer_to_canonical",
                )
                self.assertEqual(
                    output[status]["recommended_next_action"],
                    "duplicate_group_review",
                )
            for status in ("blocked_or_forbidden", "not_found"):
                self.assertEqual(
                    output[status]["triage_status"],
                    "blocked_or_unreachable_defer",
                )
            for status in ("error", "ssl_error", "timeout", "connection_error"):
                self.assertEqual(
                    output[status]["triage_status"], "needs_manual_review"
                )
            lower_rows = [
                row
                for row in output.values()
                if row["candidate_status_before_verification"] != "scheduled"
            ]
            self.assertTrue(lower_rows)
            self.assertTrue(
                all(row["priority_for_content_review"] != "p1" for row in lower_rows)
            )

    def test_four_lane_metadata_audit_recommends_merge_all(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            routing, queue = synthetic_inputs(root)
            routing_rows = list(
                csv.DictReader(routing.open(newline="", encoding="utf-8"))
            )
            excluded_path = root / "prior_triage.csv"
            write_csv(
                excluded_path,
                [
                    {
                        "triage_id": "PRIOR-ONE",
                        "candidate_queue_row_id": routing_rows[0][
                            "candidate_queue_row_id"
                        ],
                        "triage_status": "high_priority_content_review",
                    }
                ],
            )
            result = planner.prepare(
                args_for(
                    routing,
                    queue,
                    root / "remainder",
                    priority_scope="all_routed_remainder",
                    num_lanes=4,
                    batch_size=1000,
                    exclude_triage_ledger_csv=[excluded_path.as_posix()],
                    include_nonreachable=True,
                    include_too_large=True,
                    include_lower_disposition=True,
                    include_duplicates=True,
                    metadata_only_all_statuses=True,
                    balance_lanes=True,
                )
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
            manifest_path = (
                root / "remainder" / "content_triage_round_manifest.json"
            )
            manifest_path.write_text(
                json.dumps(result["manifest"], indent=2) + "\n",
                encoding="utf-8",
            )
            payload = auditor.audit(manifest_path, root / "audit")
            self.assertEqual(
                payload["classification_counts"],
                {"completed_merge_eligible": 4},
            )
            self.assertEqual(
                payload["merge_recommendation"],
                "merge_all_content_triage_lanes",
            )
            self.assertEqual(payload["terminal_rows"], len(routing_rows) - 1)
            self.assertEqual(payload["urls_opened"], 0)
            self.assertIn("too_large", payload["routing_status_to_triage_status"])

    def test_cumulative_merge_preserves_multiple_rounds_and_is_offline(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifests, audits, routing, output = make_merge_fixture(root)
            with patch.object(
                socket,
                "create_connection",
                side_effect=AssertionError("network call attempted"),
            ):
                summary = merger.merge(
                    manifest_paths=manifests,
                    audit_paths=audits,
                    routing_ledger_path=routing,
                    output_dir=output,
                    merge_id="SYNTH-CUMULATIVE-MERGE",
                    merged_at="2026-07-24T20:00:00Z",
                )
            self.assertEqual(summary["ledger_rows"], 6)
            self.assertEqual(summary["terminal_rows"], 6)
            self.assertEqual(summary["unique_triage_ids"], 6)
            self.assertEqual(summary["unique_candidate_queue_row_ids"], 6)
            self.assertTrue(summary["routing_identity_equality"])
            self.assertEqual(
                summary["triage_status_counts"],
                {
                    "high_priority_content_review": 5,
                    "low_priority_content_review": 1,
                },
            )
            self.assertEqual(
                summary["recommended_next_action_counts"],
                {
                    "content_review_download_allowed_later": 5,
                    "metadata_review_only": 1,
                },
            )
            self.assertEqual(
                summary["extraction_readiness_prelim_counts"],
                {"low": 1, "medium": 5},
            )
            self.assertEqual(
                summary["source_relevance_prelim_counts"],
                {"likely_relevant": 5, "possibly_relevant": 1},
            )
            self.assertEqual(
                summary["priority_for_content_review_counts"],
                {"p1": 5, "p3": 1},
            )
            self.assertTrue(
                all(summary[field] == 0 for field in merger.ACCESS_FIELDS)
            )
            _, rows = merger.read_csv(output / merger.LEDGER_NAME)
            lower = [
                row
                for row in rows
                if row["candidate_status_before_verification"] == "context_hold"
            ]
            self.assertEqual(len(lower), 1)
            self.assertEqual(lower[0]["priority_for_content_review"], "p3")
            self.assertEqual(
                lower[0]["content_triage_stage"],
                "metadata_only_triaged_not_content_reviewed",
            )
            self.assertTrue(
                all(row["content_triage_merge_id"] == "SYNTH-CUMULATIVE-MERGE" for row in rows)
            )
            self.assertEqual(
                sha(output / merger.LEDGER_NAME),
                sha(output / merger.LATEST_LEDGER_NAME),
            )
            with self.assertRaises(FileExistsError):
                merger.merge(
                    manifest_paths=manifests,
                    audit_paths=audits,
                    routing_ledger_path=routing,
                    output_dir=output,
                    merge_id="SYNTH-SECOND-MERGE",
                )

    def test_cumulative_merge_rejects_duplicate_triage_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifests, audits, routing, output = make_merge_fixture(root)
            _, first_rows = merger.read_csv(
                root / "round_1_metadata" / "triage_ledger.csv"
            )
            duplicate_id = first_rows[0]["triage_id"]
            second_manifest = json.loads(
                manifests[1].read_text(encoding="utf-8")
            )
            second_input = Path(second_manifest["lanes"][0]["input_csv"])
            _, input_rows = merger.read_csv(second_input)
            input_rows[0]["triage_id"] = duplicate_id
            write_csv(second_input, input_rows)
            second_manifest["lanes"][0]["input_sha256"] = sha(second_input)
            manifests[1].write_text(
                json.dumps(second_manifest, indent=2) + "\n",
                encoding="utf-8",
            )
            second_ledger = root / "round_2_metadata" / "triage_ledger.csv"
            _, ledger_rows = merger.read_csv(second_ledger)
            ledger_rows[0]["triage_id"] = duplicate_id
            write_csv(second_ledger, ledger_rows)
            auditor.audit(manifests[1], audits[1].parent)
            with self.assertRaisesRegex(ValueError, "Duplicate triage IDs"):
                merger.merge(
                    manifest_paths=manifests,
                    audit_paths=audits,
                    routing_ledger_path=routing,
                    output_dir=output,
                    merge_id="SYNTH-DUPLICATE-TRIAGE",
                )

    def test_cumulative_merge_rejects_duplicate_candidate_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifests, audits, routing, output = make_merge_fixture(root)
            _, first_rows = merger.read_csv(
                root / "round_1_metadata" / "triage_ledger.csv"
            )
            duplicate_id = first_rows[0]["candidate_queue_row_id"]
            second_manifest = json.loads(
                manifests[1].read_text(encoding="utf-8")
            )
            second_input = Path(second_manifest["lanes"][0]["input_csv"])
            _, input_rows = merger.read_csv(second_input)
            input_rows[0]["candidate_queue_row_id"] = duplicate_id
            write_csv(second_input, input_rows)
            second_manifest["lanes"][0]["input_sha256"] = sha(second_input)
            manifests[1].write_text(
                json.dumps(second_manifest, indent=2) + "\n",
                encoding="utf-8",
            )
            second_ledger = root / "round_2_metadata" / "triage_ledger.csv"
            _, ledger_rows = merger.read_csv(second_ledger)
            ledger_rows[0]["candidate_queue_row_id"] = duplicate_id
            write_csv(second_ledger, ledger_rows)
            auditor.audit(manifests[1], audits[1].parent)
            with self.assertRaisesRegex(
                ValueError, "Duplicate candidate queue IDs"
            ):
                merger.merge(
                    manifest_paths=manifests,
                    audit_paths=audits,
                    routing_ledger_path=routing,
                    output_dir=output,
                    merge_id="SYNTH-DUPLICATE-CANDIDATE",
                )

    def test_cumulative_merge_rejects_missing_terminal_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifests, audits, routing, output = make_merge_fixture(root)
            ledger_path = root / "round_2_metadata" / "triage_ledger.csv"
            _, rows = merger.read_csv(ledger_path)
            rows[0]["triage_status"] = ""
            write_csv(ledger_path, rows)
            with self.assertRaisesRegex(ValueError, "Nonterminal"):
                merger.merge(
                    manifest_paths=manifests,
                    audit_paths=audits,
                    routing_ledger_path=routing,
                    output_dir=output,
                    merge_id="SYNTH-NONTERMINAL",
                )

    def test_cumulative_merge_rejects_noneligible_audit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifests, audits, routing, output = make_merge_fixture(root)
            audit = json.loads(audits[1].read_text(encoding="utf-8"))
            audit["merge_recommendation"] = "do_not_merge_until_resume_or_review"
            audits[1].write_text(
                json.dumps(audit, indent=2) + "\n", encoding="utf-8"
            )
            with self.assertRaisesRegex(ValueError, "not merge-eligible"):
                merger.merge(
                    manifest_paths=manifests,
                    audit_paths=audits,
                    routing_ledger_path=routing,
                    output_dir=output,
                    merge_id="SYNTH-UNSAFE-AUDIT",
                )

    def test_cumulative_merge_rejects_routing_identity_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifests, audits, routing, output = make_merge_fixture(root)
            _, routing_rows = merger.read_csv(routing)
            write_csv(routing, routing_rows[:-1])
            with self.assertRaisesRegex(ValueError, "identity mismatch"):
                merger.merge(
                    manifest_paths=manifests,
                    audit_paths=audits,
                    routing_ledger_path=routing,
                    output_dir=output,
                    merge_id="SYNTH-ROUTING-MISMATCH",
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
