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


if __name__ == "__main__":
    unittest.main(verbosity=2)
