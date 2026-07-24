#!/usr/bin/env python3
"""Offline tests for source-review pilot planning, dry runs, and audits."""

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


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import audit_source_review_lanes as auditor  # noqa: E402
import prepare_source_review_pilot as planner  # noqa: E402
import source_review_sources as runner  # noqa: E402


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0]) if rows else ["queue_id"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class SourceReviewPlanningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.protected = [
            ROOT / "data" / "contracts.csv",
            ROOT / "data" / "city_coverage.csv",
            ROOT
            / "docs"
            / "analysis"
            / "national_scout_candidate_queue_2026-07-20.csv",
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
        ]
        cls.before = {path: file_hash(path) for path in cls.protected}

    @classmethod
    def tearDownClass(cls) -> None:
        after = {path: file_hash(path) for path in cls.protected}
        if after != cls.before:
            raise AssertionError("A protected upstream file changed during tests")

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.triage = self.base / "triage.csv"
        self.queue = self.base / "queue.csv"
        self.plan_dir = self.base / "plan"
        states = ["CA", "IL", "MA", "OH", "WA"]
        rows: list[dict[str, str]] = []
        for index in range(220):
            state = states[index % len(states)]
            queue_id = f"queue-{index:04d}"
            rows.append(
                self.row(
                    queue_id,
                    state=state,
                    municipality_id=f"{state}-m-{index % 90:03d}",
                )
            )
        rows.extend(
            [
                self.row(
                    "queue-duplicate",
                    duplicate_group_size="2",
                    duplicate_source_group_id="dup-1",
                ),
                self.row(
                    "queue-oversized",
                    verification_status="too_large",
                    triage_status="oversized_needs_separate_pass",
                ),
                self.row(
                    "queue-blocked",
                    verification_status="blocked_or_forbidden",
                ),
                self.row(
                    "queue-defer",
                    priority_for_content_review="defer",
                ),
                self.row(
                    "queue-exclude",
                    priority_for_content_review="exclude",
                ),
                self.row(
                    "queue-lower",
                    candidate_status_before_verification="context_hold",
                ),
            ]
        )
        write_csv(self.triage, rows)
        write_csv(self.queue, [{"queue_id": row["candidate_queue_row_id"]} for row in rows])

    def tearDown(self) -> None:
        self.temp.cleanup()

    @staticmethod
    def row(
        queue_id: str,
        *,
        state: str = "CA",
        municipality_id: str = "CA-m-001",
        duplicate_group_size: str = "1",
        duplicate_source_group_id: str = "",
        verification_status: str = "reachable_pdf_or_document",
        triage_status: str = "high_priority_content_review",
        priority_for_content_review: str = "p1",
        candidate_status_before_verification: str = "scheduled",
    ) -> dict[str, str]:
        return {
            "triage_id": f"triage-{queue_id}",
            "candidate_queue_row_id": queue_id,
            "verification_id": f"verify-{queue_id}",
            "municipality_id": municipality_id,
            "census_gov_id": f"census-{municipality_id}",
            "state": state,
            "municipality": f"Municipality {municipality_id}",
            "government_name": f"Government {municipality_id}",
            "candidate_url": f"https://example.invalid/{queue_id}.pdf",
            "final_url": f"https://example.invalid/{queue_id}.pdf",
            "source_locator": f"https://example.invalid/{queue_id}.pdf",
            "candidate_title": f"Candidate {queue_id}",
            "candidate_source_type": "cba",
            "candidate_status_before_verification": candidate_status_before_verification,
            "verification_status": verification_status,
            "content_type": "application/pdf",
            "triage_status": triage_status,
            "priority_for_content_review": priority_for_content_review,
            "recommended_next_action": "content_review_download_allowed_later",
            "candidate_priority": "high",
            "verification_round_id": "VERIFY-ROUND",
            "content_triage_round_id": "TRIAGE-ROUND",
            "source_owner_type": "city",
            "unit_type_scouted": "police",
            "population": "100000",
            "matched_set_potential": "yes",
            "official_domain_signal": "likely_official",
            "duplicate_source_group_id": duplicate_source_group_id,
            "duplicate_group_size": duplicate_group_size,
            "duplicate_group_role_for_triage": "unique_url",
        }

    def plan_args(self, output_dir: Path | None = None) -> argparse.Namespace:
        return argparse.Namespace(
            triage_ledger_csv=self.triage.as_posix(),
            candidate_queue_csv=self.queue.as_posix(),
            output_dir=(output_dir or self.plan_dir).as_posix(),
            pilot_id="SYNTHETIC-PILOT-150",
            pilot_size=150,
            num_lanes=2,
            priority_scope="p1_download_allowed",
            state_diversity=True,
            source_type_scope="cba_first",
            exclude_duplicates=True,
            exclude_oversized=True,
            exclude_blocked=True,
            plan_only=True,
        )

    def test_planner_filters_sizes_balances_and_diversifies(self) -> None:
        manifest = planner.create_plan(self.plan_args())
        self.assertEqual(manifest["p1_download_allowed_rows"], 224)
        self.assertEqual(manifest["eligible_pool_rows_after_exclusions"], 220)
        self.assertEqual(manifest["selected_rows"], 150)
        self.assertEqual(
            [lane["expected_rows"] for lane in manifest["lanes"]], [75, 75]
        )
        self.assertEqual(set(manifest["selected_state_distribution"]), {"CA", "IL", "MA", "OH", "WA"})
        selected = []
        for lane in manifest["lanes"]:
            selected.extend(planner.read_csv(Path(lane["input_csv"])))
        selected_ids = {row["candidate_queue_row_id"] for row in selected}
        self.assertFalse(
            {
                "queue-duplicate",
                "queue-oversized",
                "queue-blocked",
                "queue-defer",
                "queue-exclude",
                "queue-lower",
            }
            & selected_ids
        )
        self.assertTrue(
            all(row["priority_for_content_review"] == "p1" for row in selected)
        )
        self.assertTrue(
            all(
                row["recommended_next_action"]
                == "content_review_download_allowed_later"
                for row in selected
            )
        )

    def test_source_review_ids_are_deterministic(self) -> None:
        first = planner.create_plan(self.plan_args(self.base / "plan-a"))
        second = planner.create_plan(self.plan_args(self.base / "plan-b"))
        for first_lane, second_lane in zip(first["lanes"], second["lanes"]):
            first_rows = planner.read_csv(Path(first_lane["input_csv"]))
            second_rows = planner.read_csv(Path(second_lane["input_csv"]))
            self.assertEqual(
                [row["source_review_id"] for row in first_rows],
                [row["source_review_id"] for row in second_rows],
            )

    def test_dry_run_opens_no_network_and_writes_schema(self) -> None:
        manifest = planner.create_plan(self.plan_args())
        lane = manifest["lanes"][0]
        output_dir = self.base / "lane-1-dry"
        args = argparse.Namespace(
            input_csv=lane["input_csv"],
            output_dir=output_dir.as_posix(),
            dry_run=True,
            review_mode="source_rating_planned",
            max_rows=None,
            download_mode="none",
            no_download=True,
            write_content_samples=False,
        )
        with mock.patch.object(
            socket, "create_connection", side_effect=AssertionError("network")
        ):
            summary = runner.run_dry(args)
        self.assertEqual(summary["ledger_rows"], 75)
        self.assertEqual(summary["urls_opened"], 0)
        self.assertEqual(summary["documents_downloaded"], 0)
        ledger = runner.read_csv(output_dir / "source_review_ledger.csv")
        self.assertTrue(
            all(row["source_review_status"] == "planned_not_reviewed" for row in ledger)
        )
        self.assertTrue(all(not row["content_artifact_path"] for row in ledger))

    def test_non_dry_mode_is_rejected(self) -> None:
        manifest = planner.create_plan(self.plan_args())
        lane = manifest["lanes"][0]
        args = argparse.Namespace(
            input_csv=lane["input_csv"],
            output_dir=(self.base / "rejected").as_posix(),
            dry_run=False,
            review_mode="source_rating_planned",
            max_rows=None,
            download_mode="none",
            no_download=True,
            write_content_samples=False,
        )
        with self.assertRaisesRegex(ValueError, "not implemented"):
            runner.run_dry(args)

    def test_auditor_classifies_two_dry_lanes(self) -> None:
        manifest = planner.create_plan(self.plan_args())
        manifest_path = self.plan_dir / "source_review_pilot_manifest.json"
        for index, lane in enumerate(manifest["lanes"], start=1):
            dry_dir = self.base / f"lane-{index}-dry"
            lane["dry_run_output_dir"] = dry_dir.as_posix()
            lane["future_live_output_dir"] = (self.base / f"lane-{index}-live").as_posix()
            runner.run_dry(
                argparse.Namespace(
                    input_csv=lane["input_csv"],
                    output_dir=dry_dir.as_posix(),
                    dry_run=True,
                    review_mode="source_rating_planned",
                    max_rows=None,
                    download_mode="none",
                    no_download=True,
                    write_content_samples=False,
                )
            )
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        result = auditor.audit(manifest_path, self.base / "audit")
        self.assertEqual(result["classification_counts"], {"dry_run_passed": 2})
        self.assertEqual(result["ledger_rows"], 150)
        self.assertEqual(result["terminal_rows"], 150)
        self.assertEqual(
            result["merge_recommendation"], "dry_run_complete_no_live_source_review"
        )
        self.assertEqual(result["cross_lane_duplicate_source_review_ids"], 0)
        self.assertEqual(result["cross_lane_duplicate_candidate_queue_ids"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
