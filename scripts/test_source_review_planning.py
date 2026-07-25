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

import httpx


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import audit_source_review_lanes as auditor  # noqa: E402
import merge_source_review_lanes as merger  # noqa: E402
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


class FakeHttpClient:
    """Thread-safe enough immutable fake for bounded runner tests."""

    def __init__(
        self,
        result: runner.HttpFetchResult | None = None,
        error: Exception | None = None,
    ) -> None:
        self.result = result
        self.error = error
        self.calls = 0
        self.call_urls: list[str] = []

    def fetch(self, url: str, **kwargs: object) -> runner.HttpFetchResult:
        self.calls += 1
        self.call_urls.append(url)
        if self.error is not None:
            raise self.error
        if self.result is None:
            raise AssertionError("Fake HTTP client has no configured result")
        return self.result


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
        candidate_source_type: str = "cba",
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
            "candidate_source_type": candidate_source_type,
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
            exclude_source_review_ledger_csv=[],
            balance_lanes=True,
            plan_only=True,
        )

    def live_args(
        self,
        input_csv: str,
        output_dir: Path,
        *,
        max_rows: int | None = 1,
        max_bytes: int = 1024 * 1024,
    ) -> argparse.Namespace:
        return argparse.Namespace(
            input_csv=input_csv,
            output_dir=output_dir.as_posix(),
            dry_run=False,
            review_mode="source_rating_live",
            max_rows=max_rows,
            download_mode="bounded",
            no_download=False,
            write_content_samples=False,
            timeout=30.0,
            connect_timeout=8.0,
            read_timeout=20.0,
            max_redirects=5,
            max_bytes=max_bytes,
            concurrency=2,
            candidate_artifact_dir=None,
            user_agent=runner.DEFAULT_USER_AGENT,
            trust_env_proxy=False,
            resume_from_output_dir=None,
            skip_completed_source_review_ids=False,
            allow_live_content_access=True,
        )

    def run_one_fake(
        self,
        fake: FakeHttpClient,
        *,
        label: str,
        max_bytes: int = 1024 * 1024,
    ) -> tuple[dict[str, object], dict[str, str], Path]:
        manifest = planner.create_plan(self.plan_args())
        lane = manifest["lanes"][0]
        output_dir = self.base / label
        args = self.live_args(
            str(lane["input_csv"]), output_dir, max_bytes=max_bytes
        )
        with mock.patch.object(
            socket, "create_connection", side_effect=AssertionError("network")
        ):
            summary = runner.run_live(args, client=fake)
        ledger = runner.read_csv(output_dir / "source_review_ledger.csv")
        self.assertEqual(len(ledger), 1)
        return summary, ledger[0], output_dir

    def prepare_merge_fixture(
        self,
    ) -> tuple[Path, Path, Path, dict[str, object]]:
        args = self.plan_args(self.base / "merge-plan")
        args.pilot_id = "SYNTHETIC-SOURCE-REVIEW-PILOT"
        args.pilot_size = 100
        args.num_lanes = 2
        manifest = planner.create_plan(args)
        manifest_path = (
            Path(args.output_dir) / "source_review_pilot_manifest.json"
        )
        fake = FakeHttpClient(
            runner.HttpFetchResult(
                200,
                "https://example.invalid/final.pdf",
                {"Content-Type": "application/pdf"},
                b"%PDF-1.4\nmerge fixture\n%%EOF\n",
                0.01,
            )
        )
        for index, lane in enumerate(manifest["lanes"], start=1):
            live_dir = self.base / f"merge-lane-{index}-live"
            lane["future_live_output_dir"] = live_dir.as_posix()
            lane["dry_run_output_dir"] = (
                self.base / f"merge-lane-{index}-dry-absent"
            ).as_posix()
            with mock.patch.object(
                socket,
                "create_connection",
                side_effect=AssertionError("network"),
            ):
                runner.run_live(
                    self.live_args(
                        str(lane["input_csv"]),
                        live_dir,
                        max_rows=None,
                    ),
                    client=fake,
                )
        manifest_path.write_text(
            json.dumps(manifest, indent=2) + "\n",
            encoding="utf-8",
        )
        audit_dir = self.base / "merge-audit"
        audit_result = auditor.audit(manifest_path, audit_dir)
        audit_path = audit_dir / "source_review_lane_audit_summary.json"
        output_dir = self.base / "durable" / manifest["pilot_id"]
        return manifest_path, audit_path, output_dir, audit_result

    def prepare_prior_durable_fixture(
        self,
        *,
        manifest_path: Path,
        output_dir: Path,
        collide_with_current: bool = False,
    ) -> tuple[Path, Path]:
        manifest = json.loads(manifest_path.read_text())
        lane_ledger = (
            Path(manifest["lanes"][0]["future_live_output_dir"])
            / "source_review_ledger.csv"
        )
        _, current_rows = merger.read_csv(lane_ledger)
        prior_rows: list[dict[str, str]] = []
        for index, source in enumerate(current_rows[:10]):
            row = dict(source)
            row["source_review_id"] = f"prior-{row['source_review_id']}"
            if not collide_with_current or index:
                row["candidate_queue_row_id"] = (
                    f"prior-{row['candidate_queue_row_id']}"
                )
            row["source_review_pilot_id"] = "SYNTHETIC-PRIOR-PILOT"
            row["source_review_merge_id"] = "SYNTHETIC-PRIOR-MERGE"
            row["source_review_merged_at"] = "2026-07-23T00:00:00Z"
            row["source_review_stage"] = merger.MERGED_STAGE
            prior_rows.append(row)
        prior_dir = output_dir.parent / "SYNTHETIC-PRIOR-PILOT"
        prior_ledger = prior_dir / "source_review_ledger.csv"
        prior_summary = prior_dir / "source_review_summary.json"
        write_csv(prior_ledger, prior_rows)
        prior_summary.write_text(
            json.dumps(
                {
                    "status": "source_review_batch_merged",
                    "ledger_rows": len(prior_rows),
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        latest_ledger = output_dir.parent / merger.LATEST_LEDGER_NAME
        latest_summary = output_dir.parent / merger.LATEST_SUMMARY_NAME
        latest_ledger.write_bytes(prior_ledger.read_bytes())
        latest_summary.write_bytes(prior_summary.read_bytes())
        return prior_ledger, prior_summary

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

    def test_planner_excludes_prior_ledger_and_balances_500_rows(self) -> None:
        states = [f"S{index:02d}" for index in range(10)]
        rows = [
            self.row(
                f"batch2-{index:04d}",
                state=states[index % len(states)],
                municipality_id=f"{states[index % len(states)]}-m-{index:04d}",
            )
            for index in range(550)
        ]
        triage = self.base / "batch2-triage.csv"
        queue = self.base / "batch2-queue.csv"
        prior = self.base / "pilot1-ledger.csv"
        write_csv(triage, rows)
        write_csv(
            queue,
            [{"queue_id": row["candidate_queue_row_id"]} for row in rows],
        )
        prior_rows = [
            {
                "source_review_id": f"pilot1-review-{index:04d}",
                "candidate_queue_row_id": rows[index][
                    "candidate_queue_row_id"
                ],
            }
            for index in range(50)
        ]
        write_csv(prior, prior_rows)
        args = self.plan_args(self.base / "batch2-plan")
        args.triage_ledger_csv = triage.as_posix()
        args.candidate_queue_csv = queue.as_posix()
        args.pilot_id = "SOURCE-REVIEW-BATCH2-500-TEST"
        args.pilot_size = 500
        args.exclude_source_review_ledger_csv = [prior.as_posix()]
        manifest = planner.create_plan(args)
        self.assertEqual(
            manifest["eligible_pool_rows_before_prior_review_exclusion"],
            550,
        )
        self.assertEqual(manifest["excluded_prior_candidate_queue_ids"], 50)
        self.assertEqual(manifest["eligible_pool_rows_after_exclusions"], 500)
        self.assertEqual(manifest["selected_rows"], 500)
        self.assertEqual(
            [lane["expected_rows"] for lane in manifest["lanes"]],
            [250, 250],
        )
        selected = [
            row
            for lane in manifest["lanes"]
            for row in planner.read_csv(Path(lane["input_csv"]))
        ]
        prior_candidate_ids = {
            row["candidate_queue_row_id"] for row in prior_rows
        }
        prior_review_ids = {row["source_review_id"] for row in prior_rows}
        self.assertFalse(
            {row["candidate_queue_row_id"] for row in selected}
            & prior_candidate_ids
        )
        self.assertFalse(
            {row["source_review_id"] for row in selected}
            & prior_review_ids
        )

    def test_planner_selects_1500_in_p1_then_p2_then_p3_order(self) -> None:
        priorities = [
            ("p1", "high_priority_content_review", 1150),
            ("p2", "medium_priority_content_review", 500),
            ("p3", "low_priority_content_review", 100),
        ]
        rows: list[dict[str, str]] = []
        index = 0
        for priority, triage_status, total in priorities:
            for priority_index in range(total):
                source_type = (
                    "cba"
                    if priority != "p2" or priority_index < 250
                    else "wage_schedule_or_compensation_plan"
                )
                rows.append(
                    self.row(
                        f"batch3-{index:04d}",
                        state=f"S{index % 20:02d}",
                        municipality_id=f"m-{index:04d}",
                        priority_for_content_review=priority,
                        triage_status=triage_status,
                        candidate_source_type=source_type,
                    )
                )
                index += 1
        triage = self.base / "batch3-triage.csv"
        queue = self.base / "batch3-queue.csv"
        prior = self.base / "batch3-prior.csv"
        write_csv(triage, rows)
        write_csv(
            queue,
            [{"queue_id": row["candidate_queue_row_id"]} for row in rows],
        )
        prior_rows = [
            {
                "source_review_id": f"prior-review-{index:04d}",
                "candidate_queue_row_id": rows[index][
                    "candidate_queue_row_id"
                ],
            }
            for index in range(100)
        ]
        write_csv(prior, prior_rows)
        args = self.plan_args(self.base / "batch3-plan")
        args.triage_ledger_csv = triage.as_posix()
        args.candidate_queue_csv = queue.as_posix()
        args.pilot_id = "SOURCE-REVIEW-BATCH3-3X500-TEST"
        args.pilot_size = 1500
        args.num_lanes = 3
        args.rows_per_lane = 500
        args.priority_scope = "p1_then_p2_download_allowed"
        args.exclude_source_review_ledger_csv = [prior.as_posix()]
        manifest = planner.create_plan(args)
        self.assertEqual(manifest["selected_rows"], 1500)
        self.assertFalse(manifest["selection_under_capacity"])
        self.assertEqual(
            manifest["selected_priority_distribution"],
            {"p1": 1050, "p2": 450},
        )
        self.assertEqual(
            [lane["expected_rows"] for lane in manifest["lanes"]],
            [500, 500, 500],
        )
        selected = sorted(
            [
                row
                for lane in manifest["lanes"]
                for row in planner.read_csv(Path(lane["input_csv"]))
            ],
            key=lambda row: int(row["pilot_selection_rank"]),
        )
        self.assertTrue(
            all(
                row["priority_for_content_review"] == "p1"
                for row in selected[:1050]
            )
        )
        self.assertTrue(
            all(
                row["priority_for_content_review"] == "p2"
                for row in selected[1050:]
            )
        )
        p2_rows = selected[1050:]
        self.assertTrue(
            all(
                row["candidate_source_type"] == "cba"
                for row in p2_rows[:250]
            )
        )
        self.assertFalse(
            {row["candidate_queue_row_id"] for row in selected}
            & {
                row["candidate_queue_row_id"]
                for row in prior_rows
            }
        )

    def test_priority_ordered_planner_selects_all_when_under_capacity(
        self,
    ) -> None:
        rows = [
            self.row(
                f"under-{index:04d}",
                priority_for_content_review=(
                    "p1" if index < 200 else "p2"
                ),
                triage_status=(
                    "high_priority_content_review"
                    if index < 200
                    else "medium_priority_content_review"
                ),
            )
            for index in range(450)
        ]
        triage = self.base / "under-triage.csv"
        queue = self.base / "under-queue.csv"
        write_csv(triage, rows)
        write_csv(
            queue,
            [{"queue_id": row["candidate_queue_row_id"]} for row in rows],
        )
        args = self.plan_args(self.base / "under-plan")
        args.triage_ledger_csv = triage.as_posix()
        args.candidate_queue_csv = queue.as_posix()
        args.pilot_size = 1500
        args.num_lanes = 3
        args.rows_per_lane = 500
        args.priority_scope = "p1_then_p2_download_allowed"
        manifest = planner.create_plan(args)
        self.assertEqual(manifest["selected_rows"], 450)
        self.assertTrue(manifest["selection_under_capacity"])
        self.assertEqual(
            [lane["expected_rows"] for lane in manifest["lanes"]],
            [150, 150, 150],
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
        with self.assertRaisesRegex(ValueError, "requires --dry-run"):
            runner.run_dry(args)

    def test_live_mode_requires_explicit_authorization_and_download(self) -> None:
        manifest = planner.create_plan(self.plan_args())
        lane = manifest["lanes"][0]
        args = self.live_args(str(lane["input_csv"]), self.base / "live-gate")
        args.allow_live_content_access = False
        with self.assertRaisesRegex(ValueError, "allow-live-content-access"):
            runner.run_live(args, client=FakeHttpClient())
        self.assertFalse((self.base / "live-gate").exists())
        args.allow_live_content_access = True
        args.no_download = True
        with self.assertRaisesRegex(ValueError, "download-mode bounded"):
            runner.run_live(args, client=FakeHttpClient())
        self.assertFalse((self.base / "live-gate").exists())

    def test_live_uses_raw_locator_and_only_records_sanitized_url(self) -> None:
        manifest = planner.create_plan(self.plan_args())
        source = planner.read_csv(Path(manifest["lanes"][0]["input_csv"]))[0]
        raw_locator = (
            "https://example.invalid/document.pdf?"
            "access_token=fixture-secret&document=123"
        )
        source["source_locator"] = raw_locator
        source["final_url"] = raw_locator
        source["candidate_url"] = raw_locator
        input_csv = self.base / "raw-locator-input.csv"
        write_csv(input_csv, [source])
        fake = FakeHttpClient(
            runner.HttpFetchResult(
                200,
                raw_locator,
                {"Content-Type": "application/pdf"},
                b"%PDF-1.4\nfixture\n",
                0.01,
            )
        )
        output_dir = self.base / "raw-locator-live"
        args = self.live_args(input_csv.as_posix(), output_dir)
        runner.run_live(args, client=fake)
        row = runner.read_csv(output_dir / "source_review_ledger.csv")[0]
        self.assertEqual(fake.call_urls, [raw_locator])
        self.assertNotIn("fixture-secret", row["final_access_url_sanitized"])
        self.assertIn("%5BREDACTED%5D", row["final_access_url_sanitized"])

    def test_proxy_environment_is_explicit_and_disabled_by_default(self) -> None:
        with mock.patch.object(
            sys,
            "argv",
            [
                "source_review_sources.py",
                "--input-csv",
                "input.csv",
                "--output-dir",
                "output",
            ],
        ):
            self.assertFalse(runner.parse_args().trust_env_proxy)
        with mock.patch.object(
            sys,
            "argv",
            [
                "source_review_sources.py",
                "--input-csv",
                "input.csv",
                "--output-dir",
                "output",
                "--trust-env-proxy",
            ],
        ):
            self.assertTrue(runner.parse_args().trust_env_proxy)
        self.assertFalse(runner.HttpxBoundedHttpClient().trust_env_proxy)

    def test_connection_error_preserves_only_sanitized_exception_type(self) -> None:
        fake = FakeHttpClient(
            error=runner.FetchConnectionError(
                "sensitive fixture detail",
                cause_type="../../Connect Secret Type",
            )
        )
        _, row, _ = self.run_one_fake(fake, label="connection-diagnostic")
        self.assertEqual(row["source_review_status"], "download_connection_error")
        self.assertEqual(
            row["transport_exception_type"], "Connect_Secret_Type"
        )
        self.assertEqual(
            row["error_message_sanitized"],
            "bounded source connection failed",
        )
        self.assertNotIn("sensitive", json.dumps(row))

    def test_verifier_compatible_httpx_mock_transport_succeeds(self) -> None:
        requests: list[str] = []
        body = b"%PDF-1.4\nhttpx mock fixture\n%%EOF\n"

        def handler(request: httpx.Request) -> httpx.Response:
            requests.append(str(request.url))
            return httpx.Response(
                200,
                headers={"Content-Type": "application/pdf"},
                content=body,
                request=request,
            )

        client = runner.HttpxBoundedHttpClient(
            trust_env_proxy=False,
            transport=httpx.MockTransport(handler),
        )
        summary, row, output_dir = self.run_one_fake(
            client,  # type: ignore[arg-type]
            label="httpx-compatible-live",
        )
        self.assertEqual(len(requests), 1)
        self.assertEqual(
            row["source_review_status"],
            "reviewed_metadata_and_artifact_saved",
        )
        self.assertEqual(row["content_hash"], hashlib.sha256(body).hexdigest())
        self.assertEqual(summary["http_client"], "httpx_verifier_compatible")
        self.assertFalse(summary["trust_env_proxy"])
        self.assertTrue(Path(row["content_artifact_path"]).is_file())
        self.assertTrue(
            Path(row["content_artifact_path"])
            .resolve()
            .is_relative_to(output_dir.resolve())
        )

    def test_mocked_reachable_pdf_saves_lane_local_artifact_and_hash(self) -> None:
        body = b"%PDF-1.4\nmock bounded PDF fixture\n%%EOF\n"
        fake = FakeHttpClient(
            runner.HttpFetchResult(
                status_code=200,
                final_url="https://example.invalid/final.pdf",
                headers={"Content-Type": "application/pdf"},
                body=body,
                elapsed_seconds=0.01,
                content_length_header=len(body),
            )
        )
        summary, row, output_dir = self.run_one_fake(fake, label="pdf-live")
        artifact = Path(row["content_artifact_path"])
        self.assertTrue(artifact.is_file())
        self.assertTrue(artifact.resolve().is_relative_to(output_dir.resolve()))
        self.assertEqual(artifact.read_bytes(), body)
        self.assertEqual(row["content_hash"], hashlib.sha256(body).hexdigest())
        self.assertEqual(
            row["source_review_status"],
            "reviewed_metadata_and_artifact_saved",
        )
        self.assertEqual(row["content_type_observed"], "application/pdf")
        self.assertEqual(row["pdf_page_count"], "unknown")
        self.assertEqual(row["text_layer_status"], "unknown")
        self.assertEqual(row["documents_parsed"], "0")
        self.assertEqual(row["ocr_runs"], "0")
        self.assertEqual(summary["terminal_rows"], 1)
        self.assertEqual(fake.calls, 1)

    def test_mocked_reachable_html_records_type_without_extraction(self) -> None:
        body = b"<!doctype html><html><title>Fixture</title></html>"
        fake = FakeHttpClient(
            runner.HttpFetchResult(
                status_code=200,
                final_url="https://example.invalid/final",
                headers={"Content-Type": "text/html; charset=utf-8"},
                body=body,
                elapsed_seconds=0.01,
            )
        )
        _, row, output_dir = self.run_one_fake(fake, label="html-live")
        self.assertEqual(row["content_type_observed"], "text/html")
        self.assertEqual(row["documents_parsed"], "0")
        self.assertEqual(row["wage_table_signal"], "unknown")
        self.assertFalse(row["content_sample_path"])
        self.assertTrue(Path(row["content_artifact_path"]).is_file())
        self.assertTrue(
            Path(row["content_artifact_path"])
            .resolve()
            .is_relative_to(output_dir.resolve())
        )

    def test_mocked_too_large_writes_no_full_artifact(self) -> None:
        fake = FakeHttpClient(
            runner.HttpFetchResult(
                status_code=200,
                final_url="https://example.invalid/large.pdf",
                headers={
                    "Content-Type": "application/pdf",
                    "Content-Length": "999",
                },
                body=b"",
                elapsed_seconds=0.01,
                too_large=True,
                content_length_header=999,
            )
        )
        _, row, output_dir = self.run_one_fake(
            fake, label="large-live", max_bytes=10
        )
        self.assertEqual(row["source_review_status"], "download_too_large")
        self.assertFalse(row["content_artifact_path"])
        self.assertFalse((output_dir / "candidate_artifacts" / "content").exists())

    def test_mocked_terminal_failure_statuses(self) -> None:
        cases = [
            (
                "timeout",
                FakeHttpClient(error=runner.FetchTimeout("fixture")),
                "download_timeout",
            ),
            (
                "ssl",
                FakeHttpClient(error=runner.FetchSslError("fixture")),
                "download_ssl_error",
            ),
            (
                "not-found",
                FakeHttpClient(
                    runner.HttpFetchResult(
                        404,
                        "https://example.invalid/missing",
                        {},
                        b"",
                        0.01,
                    )
                ),
                "download_not_found",
            ),
            (
                "forbidden",
                FakeHttpClient(
                    runner.HttpFetchResult(
                        403,
                        "https://example.invalid/forbidden",
                        {},
                        b"",
                        0.01,
                    )
                ),
                "download_forbidden",
            ),
        ]
        for label, fake, expected in cases:
            with self.subTest(label=label):
                _, row, _ = self.run_one_fake(fake, label=f"failure-{label}")
                self.assertEqual(row["source_review_status"], expected)
                self.assertFalse(row["content_artifact_path"])

    def test_output_reuse_fails_closed_without_resume(self) -> None:
        body = b"%PDF-1.4\nfixture\n"
        fake = FakeHttpClient(
            runner.HttpFetchResult(
                200,
                "https://example.invalid/a.pdf",
                {"Content-Type": "application/pdf"},
                body,
                0.01,
            )
        )
        manifest = planner.create_plan(self.plan_args())
        lane = manifest["lanes"][0]
        output_dir = self.base / "reuse-live"
        args = self.live_args(str(lane["input_csv"]), output_dir)
        runner.run_live(args, client=fake)
        with self.assertRaisesRegex(FileExistsError, "Refusing to overwrite"):
            runner.run_live(args, client=fake)

    def test_artifact_names_cannot_traverse_and_stay_lane_local(self) -> None:
        manifest = planner.create_plan(self.plan_args())
        source = planner.read_csv(Path(manifest["lanes"][0]["input_csv"]))[0]
        source["source_review_id"] = "../../escape"
        input_csv = self.base / "traversal-input.csv"
        runner.write_csv(input_csv, [source], runner.LEDGER_FIELDS)
        output_dir = self.base / "traversal-live"
        args = self.live_args(input_csv.as_posix(), output_dir)
        fake = FakeHttpClient(
            runner.HttpFetchResult(
                200,
                "https://example.invalid/a.pdf",
                {"Content-Type": "application/pdf"},
                b"%PDF-1.4\nfixture\n",
                0.01,
            )
        )
        runner.run_live(args, client=fake)
        row = runner.read_csv(output_dir / "source_review_ledger.csv")[0]
        for field in ("content_artifact_path", "response_metadata_path"):
            path = Path(row[field])
            self.assertTrue(path.resolve().is_relative_to(output_dir.resolve()))
        self.assertFalse((self.base / "escape").exists())
        args = self.live_args(input_csv.as_posix(), self.base / "outside-live")
        args.candidate_artifact_dir = (self.base / "outside-artifacts").as_posix()
        with self.assertRaisesRegex(ValueError, "lane-local"):
            runner.run_live(args, client=fake)
        self.assertFalse((self.base / "outside-artifacts").exists())

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

    def test_auditor_classifies_mocked_live_lanes(self) -> None:
        manifest = planner.create_plan(self.plan_args())
        manifest_path = self.plan_dir / "source_review_pilot_manifest.json"
        fake = FakeHttpClient(
            runner.HttpFetchResult(
                200,
                "https://example.invalid/final.pdf",
                {"Content-Type": "application/pdf"},
                b"%PDF-1.4\nmock lane fixture\n",
                0.01,
            )
        )
        for index, lane in enumerate(manifest["lanes"], start=1):
            live_dir = self.base / f"lane-{index}-mock-live"
            lane["future_live_output_dir"] = live_dir.as_posix()
            lane["dry_run_output_dir"] = (
                self.base / f"lane-{index}-absent-dry"
            ).as_posix()
            args = self.live_args(
                str(lane["input_csv"]), live_dir, max_rows=None
            )
            with mock.patch.object(
                socket,
                "create_connection",
                side_effect=AssertionError("network"),
            ):
                runner.run_live(args, client=fake)
        manifest_path.write_text(
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
        )
        result = auditor.audit(manifest_path, self.base / "mock-live-audit")
        self.assertEqual(
            result["classification_counts"],
            {"completed_merge_eligible": 2},
        )
        self.assertEqual(result["ledger_rows"], 150)
        self.assertEqual(result["terminal_rows"], 150)
        self.assertEqual(
            result["merge_recommendation"], "merge_all_source_review_lanes"
        )
        self.assertEqual(result["content_artifact_files"], 150)
        self.assertEqual(result["metadata_artifact_files"], 150)
        self.assertTrue(result["artifact_integrity_passed"])
        self.assertEqual(result["documents_parsed"], 0)
        self.assertEqual(result["ocr_runs"], 0)

    def test_merge_preserves_rows_artifacts_hashes_and_ratings(self) -> None:
        manifest_path, audit_path, output_dir, _ = (
            self.prepare_merge_fixture()
        )
        original_dir = self.base / "original-failed-attempt"
        original_dir.mkdir()
        (original_dir / "source_review_ledger.csv").write_text(
            "source_review_id,source_review_status\n"
            "poison-original,download_connection_error\n",
            encoding="utf-8",
        )
        with mock.patch.object(
            socket,
            "create_connection",
            side_effect=AssertionError("network"),
        ):
            summary = merger.merge(
                manifest_path=manifest_path,
                audit_path=audit_path,
                output_dir=output_dir,
                pilot_id="SYNTHETIC-SOURCE-REVIEW-PILOT",
                merge_id="SYNTHETIC-HTTPX-MERGE",
                merged_at="2026-07-24T00:00:00Z",
            )
        fields, rows = merger.read_csv(
            output_dir / "source_review_ledger.csv"
        )
        self.assertEqual(len(rows), 100)
        self.assertNotIn(
            "poison-original",
            {row["source_review_id"] for row in rows},
        )
        self.assertEqual(
            {row["source_review_stage"] for row in rows},
            {merger.MERGED_STAGE},
        )
        self.assertEqual(
            {row["source_review_merge_id"] for row in rows},
            {"SYNTHETIC-HTTPX-MERGE"},
        )
        self.assertEqual(summary["content_artifact_count"], 100)
        self.assertEqual(summary["rows_with_content_hash"], 100)
        self.assertEqual(
            summary["source_relevance_rating_counts"],
            {"possible": 100},
        )
        self.assertEqual(
            summary["extraction_readiness_rating_counts"],
            {"medium": 100},
        )
        for row in rows:
            artifact = Path(row["content_artifact_path"])
            self.assertTrue(artifact.is_file())
            self.assertEqual(
                hashlib.sha256(artifact.read_bytes()).hexdigest(),
                row["content_hash"],
            )
        self.assertIn("source_review_merge_id", fields)
        latest = output_dir.parent / "source_review_ledger_latest.csv"
        self.assertEqual(
            latest.read_bytes(),
            (output_dir / "source_review_ledger.csv").read_bytes(),
        )
        cumulative = output_dir.parent / "source_review_ledger_cumulative.csv"
        self.assertEqual(cumulative.read_bytes(), latest.read_bytes())
        self.assertEqual(summary["merge_urls_opened"], 0)
        self.assertEqual(summary["merge_documents_downloaded"], 0)
        self.assertEqual(
            summary["original_failed_attempt_status"],
            "preserved_unmerged_superseded_transport",
        )

    def test_merge_builds_cumulative_latest_from_explicit_prior(self) -> None:
        manifest_path, audit_path, output_dir, _ = (
            self.prepare_merge_fixture()
        )
        prior_ledger, prior_summary = self.prepare_prior_durable_fixture(
            manifest_path=manifest_path,
            output_dir=output_dir,
        )
        summary = merger.merge(
            manifest_path=manifest_path,
            audit_path=audit_path,
            output_dir=output_dir,
            pilot_id="SYNTHETIC-SOURCE-REVIEW-PILOT",
            merge_id="SYNTHETIC-HTTPX-MERGE",
            prior_ledger_path=prior_ledger,
            prior_summary_path=prior_summary,
            merged_at="2026-07-24T00:00:00Z",
        )
        _, round_rows = merger.read_csv(
            output_dir / merger.ROUND_LEDGER_NAME
        )
        cumulative_path = (
            output_dir.parent / merger.CUMULATIVE_LEDGER_NAME
        )
        _, cumulative_rows = merger.read_csv(cumulative_path)
        latest_path = output_dir.parent / merger.LATEST_LEDGER_NAME
        cumulative_summary = json.loads(
            (
                output_dir.parent / merger.CUMULATIVE_SUMMARY_NAME
            ).read_text()
        )
        self.assertEqual(len(round_rows), 100)
        self.assertEqual(summary["ledger_rows"], 100)
        self.assertEqual(len(cumulative_rows), 110)
        self.assertEqual(
            len({row["source_review_id"] for row in cumulative_rows}),
            110,
        )
        self.assertEqual(
            len(
                {
                    row["candidate_queue_row_id"]
                    for row in cumulative_rows
                }
            ),
            110,
        )
        self.assertEqual(latest_path.read_bytes(), cumulative_path.read_bytes())
        self.assertEqual(cumulative_summary["ledger_rows"], 110)
        self.assertEqual(cumulative_summary["content_artifact_count"], 110)
        self.assertEqual(
            cumulative_summary["merged_batch_rows"],
            {
                "SYNTHETIC-PRIOR-PILOT": 10,
                "SYNTHETIC-SOURCE-REVIEW-PILOT": 100,
            },
        )

    def test_merge_rejects_identity_overlap_with_prior(self) -> None:
        manifest_path, audit_path, output_dir, _ = (
            self.prepare_merge_fixture()
        )
        prior_ledger, prior_summary = self.prepare_prior_durable_fixture(
            manifest_path=manifest_path,
            output_dir=output_dir,
            collide_with_current=True,
        )
        latest_before = (
            output_dir.parent / merger.LATEST_LEDGER_NAME
        ).read_bytes()
        with self.assertRaisesRegex(
            merger.SourceReviewMergeError, "candidate queue"
        ):
            merger.merge(
                manifest_path=manifest_path,
                audit_path=audit_path,
                output_dir=output_dir,
                pilot_id="SYNTHETIC-SOURCE-REVIEW-PILOT",
                merge_id="SYNTHETIC-HTTPX-MERGE",
                prior_ledger_path=prior_ledger,
                prior_summary_path=prior_summary,
            )
        self.assertEqual(
            (output_dir.parent / merger.LATEST_LEDGER_NAME).read_bytes(),
            latest_before,
        )
        self.assertFalse(output_dir.exists())

    def test_merge_rejects_duplicate_source_review_ids(self) -> None:
        with self.assertRaisesRegex(
            merger.SourceReviewMergeError, "source_review"
        ):
            merger.validate_unique_identities(
                [
                    {
                        "source_review_id": "duplicate",
                        "candidate_queue_row_id": "queue-1",
                    },
                    {
                        "source_review_id": "duplicate",
                        "candidate_queue_row_id": "queue-2",
                    },
                ]
            )

    def test_merge_rejects_duplicate_candidate_queue_ids(self) -> None:
        with self.assertRaisesRegex(
            merger.SourceReviewMergeError, "candidate queue"
        ):
            merger.validate_unique_identities(
                [
                    {
                        "source_review_id": "review-1",
                        "candidate_queue_row_id": "duplicate",
                    },
                    {
                        "source_review_id": "review-2",
                        "candidate_queue_row_id": "duplicate",
                    },
                ]
            )

    def test_merge_rejects_missing_terminal_row(self) -> None:
        manifest_path, audit_path, output_dir, _ = (
            self.prepare_merge_fixture()
        )
        manifest = json.loads(manifest_path.read_text())
        ledger_path = (
            Path(manifest["lanes"][0]["future_live_output_dir"])
            / "source_review_ledger.csv"
        )
        _, rows = merger.read_csv(ledger_path)
        rows[0]["source_review_status"] = "planned_not_reviewed"
        write_csv(ledger_path, rows)
        with self.assertRaisesRegex(
            merger.SourceReviewMergeError, "Nonterminal"
        ):
            merger.merge(
                manifest_path=manifest_path,
                audit_path=audit_path,
                output_dir=output_dir,
                pilot_id="SYNTHETIC-SOURCE-REVIEW-PILOT",
                merge_id="SYNTHETIC-HTTPX-MERGE",
            )

    def test_merge_rejects_noneligible_audit(self) -> None:
        manifest_path, audit_path, output_dir, _ = (
            self.prepare_merge_fixture()
        )
        audit = json.loads(audit_path.read_text())
        audit["merge_recommendation"] = (
            "do_not_merge_until_resume_or_review"
        )
        audit_path.write_text(
            json.dumps(audit, indent=2) + "\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(
            merger.SourceReviewMergeError, "does not recommend"
        ):
            merger.merge(
                manifest_path=manifest_path,
                audit_path=audit_path,
                output_dir=output_dir,
                pilot_id="SYNTHETIC-SOURCE-REVIEW-PILOT",
                merge_id="SYNTHETIC-HTTPX-MERGE",
            )

    def test_merge_refuses_to_overwrite_durable_outputs(self) -> None:
        manifest_path, audit_path, output_dir, _ = (
            self.prepare_merge_fixture()
        )
        output_dir.mkdir(parents=True)
        (output_dir / "source_review_ledger.csv").write_text(
            "already exists\n", encoding="utf-8"
        )
        with self.assertRaisesRegex(FileExistsError, "Refusing to overwrite"):
            merger.merge(
                manifest_path=manifest_path,
                audit_path=audit_path,
                output_dir=output_dir,
                pilot_id="SYNTHETIC-SOURCE-REVIEW-PILOT",
                merge_id="SYNTHETIC-HTTPX-MERGE",
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
