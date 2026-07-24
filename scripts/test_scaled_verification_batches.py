#!/usr/bin/env python3
"""Offline and mock-transport tests for scaled candidate-source verification."""

from __future__ import annotations

import argparse
import asyncio
import csv
import hashlib
import json
import tempfile
from pathlib import Path

import httpx

import audit_verification_lanes as auditor
import merge_verification_lanes as merger
import prepare_scaled_verification_batches as planner
import verify_candidate_sources as verifier


ROOT = Path(__file__).resolve().parent.parent
QUEUE = ROOT / "docs" / "analysis" / "national_scout_candidate_queue_2026-07-20.csv"
MUNICIPALITY_COVERAGE = (
    ROOT
    / "docs"
    / "analysis"
    / "national_scout_coverage_municipality_2026-07-20.csv"
)
STATE_COVERAGE = ROOT / "docs" / "analysis" / "national_scout_coverage_state.csv"
COUNTY_COVERAGE = ROOT / "docs" / "analysis" / "national_scout_coverage_county.csv"
ROUND1_ROUTING_LEDGER = (
    ROOT
    / "docs"
    / "analysis"
    / "verification_ledgers"
    / "VERIFICATION-SCALE-ROUND1-3X750-2026-07-23"
    / "verified_source_routing_ledger.csv"
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def synthetic_queue(
    entries: list[tuple[str, str, str]] | None = None,
) -> list[dict[str, str]]:
    base = {
        "municipality_id": "m1",
        "state": "MA",
        "municipality": "Example",
        "document_title": "Collective Agreement",
        "document_type_scouted": "cba",
        "unit_type_scouted": "police",
        "source_owner_type": "city",
        "confidence": "high",
        "triage_score": "90",
        "source_wave": "TEST",
        "scout_stage_status": "unverified_scout_candidate",
    }
    entries = entries or [
        ("Q1", "https://example.invalid/document.pdf", "high_priority_later_verify"),
        (
            "Q2",
            "https://EXAMPLE.invalid/document.pdf#page=2",
            "medium_priority_later_verify",
        ),
        ("Q3", "https://example.invalid/context", "context_only_hold"),
        ("Q4", "https://example.invalid/duplicate", "likely_duplicate_hold"),
    ]
    rows = []
    for queue_id, url, bucket in entries:
        row = dict(base)
        row.update({"queue_id": queue_id, "source_url": url, "triage_bucket": bucket})
        rows.append(row)
    return rows


def synthetic_universe() -> dict[str, dict[str, str]]:
    return {
        "m1": {
            "municipality_id": "m1",
            "census_gov_id": "123456",
            "state": "MA",
            "municipality": "Example",
            "government_name": "CITY OF EXAMPLE",
            "population": "100000",
        }
    }


def planner_args(
    output: Path,
    *,
    profile: str,
    priority_scope: str = "scheduled",
    include_held: bool = False,
    include_duplicates: bool = False,
) -> argparse.Namespace:
    return argparse.Namespace(
        candidate_queue_csv=str(QUEUE),
        output_dir=str(output),
        round_id=f"SYNTHETIC-{profile}",
        profile=profile,
        batch_size=None,
        num_lanes=None,
        concurrency_per_lane=8,
        verification_timeout=20.0,
        max_bytes=10_485_760,
        include_held=include_held,
        include_duplicates=include_duplicates,
        dedupe_fetch_plan=True,
        exclude_verified_ledger_csv="",
        fill_with_held_after_scheduled=False,
        balance_lanes=False,
        priority_scope=priority_scope,
        state_scope="",
        plan_only=True,
    )


def verifier_args(input_path: Path, output_dir: Path, *, dry_run: bool) -> argparse.Namespace:
    return argparse.Namespace(
        input_csv=str(input_path),
        output_dir=str(output_dir),
        dry_run=dry_run,
        max_rows=None,
        timeout=20.0,
        connect_timeout=8.0,
        read_timeout=15.0,
        max_redirects=5,
        max_bytes=10_485_760,
        concurrency=8,
        user_agent="GabrielWagesVerifierTest/1.0",
        resume_from_output_dir=None,
        skip_completed_verification_ids=False,
        candidate_artifact_dir=str(output_dir / "candidate_artifacts"),
        write_content_samples=False,
        respect_robots_note=True,
    )


def test_identity_and_duplicate_groups() -> None:
    rows = synthetic_queue()
    enriched = planner.enrich_candidates(rows, synthetic_universe(), {"MA": 2.5})
    assert len(enriched) == len(rows)
    assert {row["candidate_queue_row_id"] for row in enriched} == {
        row["queue_id"] for row in rows
    }
    assert len({row["verification_id"] for row in enriched}) == len(rows)
    assert enriched[0]["duplicate_source_group_id"] == enriched[1][
        "duplicate_source_group_id"
    ]
    assert enriched[0]["duplicate_group_size"] == 2
    assert enriched[1]["duplicate_group_role"] == "linked_duplicate"


def test_scope_controls() -> None:
    enriched = planner.enrich_candidates(
        synthetic_queue(), synthetic_universe(), {"MA": 2.5}
    )
    scheduled = [
        row
        for row in enriched
        if planner.eligible_for_scope(
            row,
            priority_scope="scheduled",
            include_held=False,
            include_duplicates=False,
            state_scope=None,
        )
    ]
    assert {row["candidate_queue_row_id"] for row in scheduled} == {"Q1", "Q2"}
    all_without_duplicates = [
        row
        for row in enriched
        if planner.eligible_for_scope(
            row,
            priority_scope="all",
            include_held=True,
            include_duplicates=False,
            state_scope=None,
        )
    ]
    assert {row["candidate_queue_row_id"] for row in all_without_duplicates} == {
        "Q1",
        "Q2",
        "Q3",
    }
    all_with_duplicates = [
        row
        for row in enriched
        if planner.eligible_for_scope(
            row,
            priority_scope="all",
            include_held=True,
            include_duplicates=True,
            state_scope=None,
        )
    ]
    assert len(all_with_duplicates) == 4


def test_large_profiles() -> None:
    with tempfile.TemporaryDirectory(prefix="verification_plan_test_") as temporary:
        root = Path(temporary)
        plan_750 = planner.prepare(
            planner_args(root / "round750", profile="aggressive_750")
        )
        assert [len(lane) for lane in plan_750["lanes"]] == [750, 750, 750]
        ids_750 = [
            str(row["verification_id"]) for lane in plan_750["lanes"] for row in lane
        ]
        assert len(ids_750) == len(set(ids_750)) == 2250
        manifest_750 = json.loads(
            (root / "round750" / "verification_round_manifest.json").read_text()
        )
        assert manifest_750["profile"] == "aggressive_750"
        assert manifest_750["planned_candidate_rows"] == 2250
        assert manifest_750["concurrency_per_lane"] == 8

        plan_1000 = planner.prepare(
            planner_args(root / "round1000", profile="max_1000")
        )
        assert [len(lane) for lane in plan_1000["lanes"]] == [1000, 1000, 1000]
        ids_1000 = [
            str(row["verification_id"])
            for lane in plan_1000["lanes"]
            for row in lane
        ]
        assert len(ids_1000) == len(set(ids_1000)) == 3000


def test_option_b_remainder_excludes_round1_and_balances() -> None:
    with tempfile.TemporaryDirectory(prefix="verification_remainder_test_") as temporary:
        root = Path(temporary)
        args = planner_args(
            root / "remainder",
            profile="max_1000",
            priority_scope="remainder_all",
        )
        args.exclude_verified_ledger_csv = str(ROUND1_ROUTING_LEDGER)
        args.fill_with_held_after_scheduled = True
        args.balance_lanes = True
        result = planner.prepare(args)
        lanes = result["lanes"]
        assert [len(lane) for lane in lanes] == [826, 825, 825]
        selected = [row for lane in lanes for row in lane]
        assert len(selected) == 2476
        assert sum(
            row["candidate_status_before_verification"] == "scheduled"
            for row in selected
        ) == 1350
        assert sum(
            row["candidate_status_before_verification"] != "scheduled"
            for row in selected
        ) == 1126
        with ROUND1_ROUTING_LEDGER.open(newline="", encoding="utf-8") as handle:
            prior = list(csv.DictReader(handle))
        prior_queue_ids = {row["candidate_queue_row_id"] for row in prior}
        prior_verification_ids = {row["verification_id"] for row in prior}
        assert not (
            {str(row["candidate_queue_row_id"]) for row in selected}
            & prior_queue_ids
        )
        assert not (
            {str(row["verification_id"]) for row in selected}
            & prior_verification_ids
        )
        manifest = json.loads(
            (root / "remainder" / "verification_round_manifest.json").read_text()
        )
        assert manifest["planned_candidate_rows"] == 2476
        assert manifest["under_capacity_rows"] == 524
        assert manifest["remaining_url_bearing_rows_unselected"] == 0
        assert manifest["excluded_candidate_queue_row_ids"] == 2250
        assert manifest["excluded_verification_ids"] == 2250


def write_input(
    path: Path, entries: list[tuple[str, str, str]] | None = None
) -> list[dict[str, str]]:
    enriched = planner.enrich_candidates(
        synthetic_queue(entries), synthetic_universe(), {"MA": 2.5}
    )
    planner.write_csv(path, enriched, planner.IDENTITY_FIELDS)
    return [{key: str(value) for key, value in row.items()} for row in enriched]


def test_dry_runner_opens_no_urls_and_audits() -> None:
    with tempfile.TemporaryDirectory(prefix="verification_dry_test_") as temporary:
        root = Path(temporary)
        input_path = root / "lane_1_input.csv"
        expected = write_input(input_path)
        dry_dir = root / "lane_1_dry"
        summary = verifier.run_dry(verifier_args(input_path, dry_dir, dry_run=True))
        assert summary["planned_rows"] == 4
        assert summary["urls_opened"] == 0
        assert summary["network_calls"] == 0
        with (dry_dir / "verification_ledger.csv").open(
            newline="", encoding="utf-8"
        ) as handle:
            ledger_rows = list(csv.DictReader(handle))
        assert [row["verification_id"] for row in ledger_rows] == [
            row["verification_id"] for row in expected
        ]
        assert all(
            row["verification_status"] == "dry_run_planned" for row in ledger_rows
        )

        manifest_path = root / "manifest.json"
        manifest = {
            "round_id": "DRY-TEST",
            "lanes": [
                {
                    "lane_id": "lane_1",
                    "input_csv": str(input_path),
                    "input_sha256": digest(input_path),
                    "expected_rows": 4,
                    "dry_run_output_dir": str(dry_dir),
                    "live_output_dir": str(root / "lane_1_live"),
                }
            ],
        }
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        result = auditor.audit(manifest_path, root / "audit")
        assert result["lane_classification_counts"] == {"dry_run_passed": 1}
        assert result["merge_recommendation"] == "do_not_merge_until_resume_or_review"
        assert result["urls_opened"] == 0
        assert result["network_calls"] == 0


def test_mocked_live_path_and_duplicate_reuse() -> None:
    entries = [
        ("QH", "https://mock.invalid/html", "high_priority_later_verify"),
        ("QD", "https://MOCK.invalid/html#same", "high_priority_later_verify"),
        ("QP", "https://mock.invalid/document.pdf", "high_priority_later_verify"),
        ("QT", "https://mock.invalid/timeout", "high_priority_later_verify"),
        ("QR", "https://mock.invalid/redirect", "high_priority_later_verify"),
        ("QL", "https://mock.invalid/large", "high_priority_later_verify"),
    ]
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        if request.url.path == "/html":
            return httpx.Response(
                200,
                headers={"content-type": "text/html; charset=utf-8"},
                content=b"<html><title>Mock</title></html>",
            )
        if request.url.path == "/document.pdf":
            return httpx.Response(
                200,
                headers={"content-type": "application/pdf"},
                content=b"%PDF-1.7 mock",
            )
        if request.url.path == "/timeout":
            raise httpx.ReadTimeout("synthetic timeout", request=request)
        if request.url.path == "/redirect":
            return httpx.Response(302, headers={"location": "/redirected"})
        if request.url.path == "/redirected":
            return httpx.Response(
                200,
                headers={"content-type": "text/html"},
                content=b"<html>redirect target</html>",
            )
        if request.url.path == "/large":
            return httpx.Response(
                200,
                headers={
                    "content-type": "application/octet-stream",
                    "content-length": "99999999",
                },
            )
        raise AssertionError(f"Unexpected mock request: {request.url}")

    with tempfile.TemporaryDirectory(prefix="verification_live_mock_") as temporary:
        root = Path(temporary)
        input_path = root / "lane_1_input.csv"
        expected = write_input(input_path, entries)
        live_dir = root / "lane_1_live"
        args = verifier_args(input_path, live_dir, dry_run=False)
        summary = asyncio.run(
            verifier.run_live(args, transport=httpx.MockTransport(handler))
        )
        assert summary["status"] == "completed"
        assert summary["planned_rows"] == len(expected)
        assert summary["network_calls"] == 5
        assert calls.count("/html") == 1
        with (live_dir / "verification_ledger.csv").open(
            newline="", encoding="utf-8"
        ) as handle:
            rows = list(csv.DictReader(handle))
        statuses = {row["candidate_queue_row_id"]: row for row in rows}
        assert statuses["QH"]["verification_status"] == "reachable_html"
        assert statuses["QD"]["verification_status"] == "duplicate_of_verified_source"
        assert statuses["QD"]["duplicate_fetch_reused_from_verification_id"]
        assert statuses["QP"]["verification_status"] == "reachable_pdf_or_document"
        assert statuses["QT"]["verification_status"] == "timeout"
        assert statuses["QR"]["verification_status"] == "reachable_html"
        assert statuses["QR"]["redirect_detected"] == "yes"
        assert statuses["QL"]["verification_status"] == "too_large"
        assert len(rows) == len(expected)

        manifest_path = root / "manifest.json"
        manifest_path.write_text(
            json.dumps(
                {
                    "round_id": "LIVE-MOCK-TEST",
                    "lanes": [
                        {
                            "lane_id": "lane_1",
                            "input_csv": str(input_path),
                            "input_sha256": digest(input_path),
                            "expected_rows": len(expected),
                            "dry_run_output_dir": str(root / "lane_1_dry"),
                            "live_output_dir": str(live_dir),
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        audit = auditor.audit(manifest_path, root / "audit")
        assert audit["lane_classification_counts"] == {
            "completed_merge_eligible": 1
        }
        assert audit["merge_recommendation"] == "merge_all_verification_lanes"
        assert audit["verification_status_counts"]["reachable_html"] == 2
        assert audit["duplicate_reuse_rows"] == 1


def write_synthetic_merge_lane(
    root: Path,
    lane_id: str,
    *,
    pending_last_row: bool = False,
    entries: list[tuple[str, str, str]] | None = None,
) -> tuple[dict[str, object], dict[str, object]]:
    input_path = root / f"{lane_id}_input.csv"
    input_rows = write_input(input_path, entries)
    live_dir = root / f"{lane_id}_live"
    live_dir.mkdir()
    ledger_rows: list[dict[str, str]] = []
    for index, input_row in enumerate(input_rows):
        row = {field: "" for field in verifier.LEDGER_FIELDS}
        for field in planner.IDENTITY_FIELDS:
            if field in row:
                row[field] = input_row.get(field, "")
        row.update(
            {
                "verification_status": "reachable_html",
                "verification_status_detail": "synthetic terminal result",
                "url_reachable": "yes",
                "http_status_code": "200",
                "final_url": input_row["candidate_url"],
                "redirect_detected": "no",
                "redirect_chain_length": "0",
                "content_type": "text/html",
                "content_length_header": "100",
                "bytes_read": "100",
                "fetch_elapsed_seconds": "0.01",
                "source_officialness_prelim": "unknown",
                "employer_match_prelim": "needs_content_review",
                "source_document_type_prelim": "html_needs_content_review",
                "wage_data_signal_prelim": "unknown",
                "mechanism_language_signal_prelim": "unknown",
                "verified_at": "2026-07-24T00:00:00Z",
            }
        )
        if pending_last_row and index == len(input_rows) - 1:
            row["verification_status"] = "pending"
        ledger_rows.append(row)
    planner.write_csv(
        live_dir / "verification_ledger.csv", ledger_rows, verifier.LEDGER_FIELDS
    )
    (live_dir / "verification_summary.json").write_text(
        json.dumps(
            {
                "status": "completed",
                "urls_opened": len(ledger_rows),
                "network_calls": len(ledger_rows),
            }
        ),
        encoding="utf-8",
    )
    lane = {
        "lane_id": lane_id,
        "lane_number": int(lane_id.rsplit("_", 1)[-1]),
        "input_csv": str(input_path),
        "input_sha256": digest(input_path),
        "expected_rows": len(input_rows),
        "dry_run_output_dir": str(root / f"{lane_id}_dry"),
        "live_output_dir": str(live_dir),
    }
    lane_audit = {
        "lane_id": lane_id,
        "classification": "completed_merge_eligible",
        "ledger_rows": len(ledger_rows),
        "terminal_rows": len(ledger_rows),
    }
    return lane, lane_audit


def synthetic_merge_audit(
    round_id: str,
    lanes: list[dict[str, object]],
    lane_audits: list[dict[str, object]],
) -> dict[str, object]:
    rows = sum(int(lane["expected_rows"]) for lane in lanes)
    return {
        "round_id": round_id,
        "lanes": lane_audits,
        "planned_candidate_rows": rows,
        "ledger_rows": rows,
        "terminal_rows": rows,
        "cross_lane_duplicate_verification_ids": 0,
        "accounting_mutations": 0,
        "urls_opened": rows,
        "network_calls": rows,
        "duplicate_reuse_rows": 0,
        "merge_recommendation": "merge_all_verification_lanes",
    }


def test_serial_merge_preserves_rows_and_fields() -> None:
    with tempfile.TemporaryDirectory(prefix="verification_merge_test_") as temporary:
        root = Path(temporary)
        lane, lane_audit = write_synthetic_merge_lane(root, "lane_1")
        round_id = "SYNTHETIC-MERGE-ROUND"
        manifest_path = root / "manifest.json"
        audit_path = root / "audit.json"
        manifest_path.write_text(
            json.dumps({"round_id": round_id, "lanes": [lane]}),
            encoding="utf-8",
        )
        audit_path.write_text(
            json.dumps(synthetic_merge_audit(round_id, [lane], [lane_audit])),
            encoding="utf-8",
        )
        output_dir = root / "merged"
        summary = merger.merge(
            manifest_path=manifest_path,
            audit_summary_path=audit_path,
            output_dir=output_dir,
            round_id=round_id,
            merge_id="SYNTHETIC-MERGE-ID",
            merged_at="2026-07-24T00:00:00Z",
            write_latest=False,
        )
        _, merged_rows = merger.read_csv(
            output_dir / "verified_source_routing_ledger.csv"
        )
        assert summary["ledger_rows"] == len(merged_rows) == 4
        assert summary["terminal_rows"] == 4
        assert summary["verification_status_counts"] == {"reachable_html": 4}
        assert summary["reachable_or_reused_total"] == 4
        assert all(
            row["verification_stage"]
            == "url_reachability_metadata_verified"
            for row in merged_rows
        )
        assert [row["duplicate_source_group_id"] for row in merged_rows]
        assert all(row["verification_lane_id"] == "lane_1" for row in merged_rows)


def test_serial_merge_rejects_duplicate_pending_and_ineligible() -> None:
    with tempfile.TemporaryDirectory(prefix="verification_merge_gate_test_") as temporary:
        root = Path(temporary)
        lane_1, audit_1 = write_synthetic_merge_lane(root, "lane_1")
        lane_2, audit_2 = write_synthetic_merge_lane(root, "lane_2")
        round_id = "SYNTHETIC-MERGE-GATES"
        manifest_path = root / "duplicate_manifest.json"
        audit_path = root / "duplicate_audit.json"
        manifest_path.write_text(
            json.dumps({"round_id": round_id, "lanes": [lane_1, lane_2]}),
            encoding="utf-8",
        )
        audit_path.write_text(
            json.dumps(
                synthetic_merge_audit(
                    round_id, [lane_1, lane_2], [audit_1, audit_2]
                )
            ),
            encoding="utf-8",
        )
        try:
            merger.merge(
                manifest_path=manifest_path,
                audit_summary_path=audit_path,
                output_dir=root / "duplicate_output",
                round_id=round_id,
                merge_id="DUPLICATE-MERGE",
                write_latest=False,
            )
        except merger.MergeValidationError as exc:
            assert "duplicate verification IDs" in str(exc)
        else:
            raise AssertionError("Duplicate verification IDs did not fail merge")

        pending_lane, pending_audit = write_synthetic_merge_lane(
            root, "lane_3", pending_last_row=True
        )
        pending_manifest = root / "pending_manifest.json"
        pending_audit_path = root / "pending_audit.json"
        pending_manifest.write_text(
            json.dumps({"round_id": round_id, "lanes": [pending_lane]}),
            encoding="utf-8",
        )
        pending_audit_path.write_text(
            json.dumps(
                synthetic_merge_audit(
                    round_id, [pending_lane], [pending_audit]
                )
            ),
            encoding="utf-8",
        )
        try:
            merger.merge(
                manifest_path=pending_manifest,
                audit_summary_path=pending_audit_path,
                output_dir=root / "pending_output",
                round_id=round_id,
                merge_id="PENDING-MERGE",
                write_latest=False,
            )
        except merger.MergeValidationError as exc:
            assert "non-terminal" in str(exc)
        else:
            raise AssertionError("Non-terminal row did not fail merge")

        ineligible = synthetic_merge_audit(round_id, [lane_1], [audit_1])
        ineligible["merge_recommendation"] = "do_not_merge_until_resume_or_review"
        ineligible_path = root / "ineligible_audit.json"
        ineligible_path.write_text(json.dumps(ineligible), encoding="utf-8")
        single_manifest = root / "single_manifest.json"
        single_manifest.write_text(
            json.dumps({"round_id": round_id, "lanes": [lane_1]}),
            encoding="utf-8",
        )
        try:
            merger.merge(
                manifest_path=single_manifest,
                audit_summary_path=ineligible_path,
                output_dir=root / "ineligible_output",
                round_id=round_id,
                merge_id="INELIGIBLE-MERGE",
                write_latest=False,
            )
        except merger.MergeValidationError as exc:
            assert "does not recommend" in str(exc)
        else:
            raise AssertionError("Ineligible audit did not fail merge")


def test_serial_merge_builds_cumulative_latest_without_losing_prior_round() -> None:
    with tempfile.TemporaryDirectory(prefix="verification_cumulative_test_") as temporary:
        root = Path(temporary)
        ledger_root = root / "verification_ledgers"
        ledger_root.mkdir()

        lane_1, audit_1 = write_synthetic_merge_lane(root, "lane_1")
        manifest_1 = root / "manifest_1.json"
        audit_path_1 = root / "audit_1.json"
        round_1 = "SYNTHETIC-ROUND-1"
        manifest_1.write_text(
            json.dumps({"round_id": round_1, "lanes": [lane_1]}),
            encoding="utf-8",
        )
        audit_path_1.write_text(
            json.dumps(synthetic_merge_audit(round_1, [lane_1], [audit_1])),
            encoding="utf-8",
        )
        merger.merge(
            manifest_path=manifest_1,
            audit_summary_path=audit_path_1,
            output_dir=ledger_root / round_1,
            round_id=round_1,
            merge_id="SYNTHETIC-MERGE-1",
            merged_at="2026-07-24T00:00:00Z",
            write_latest=True,
        )

        second_entries = [
            ("R1", "https://second.invalid/one", "high_priority_later_verify"),
            ("R2", "https://second.invalid/two", "high_priority_later_verify"),
            ("R3", "https://second.invalid/three", "medium_priority_later_verify"),
            ("R4", "https://second.invalid/four", "low_priority_later_verify"),
        ]
        lane_2, audit_2 = write_synthetic_merge_lane(
            root, "lane_2", entries=second_entries
        )
        manifest_2 = root / "manifest_2.json"
        audit_path_2 = root / "audit_2.json"
        round_2 = "SYNTHETIC-ROUND-2"
        manifest_2.write_text(
            json.dumps({"round_id": round_2, "lanes": [lane_2]}),
            encoding="utf-8",
        )
        audit_path_2.write_text(
            json.dumps(synthetic_merge_audit(round_2, [lane_2], [audit_2])),
            encoding="utf-8",
        )
        round_2_summary = merger.merge(
            manifest_path=manifest_2,
            audit_summary_path=audit_path_2,
            output_dir=ledger_root / round_2,
            round_id=round_2,
            merge_id="SYNTHETIC-MERGE-2",
            merged_at="2026-07-24T00:01:00Z",
            write_latest=True,
        )

        _, round_2_rows = merger.read_csv(
            ledger_root / round_2 / merger.ROUND_LEDGER_NAME
        )
        _, cumulative_rows = merger.read_csv(
            ledger_root / merger.CUMULATIVE_LEDGER_NAME
        )
        _, latest_rows = merger.read_csv(ledger_root / merger.LATEST_LEDGER_NAME)
        cumulative_summary = merger.load_json(
            ledger_root / merger.CUMULATIVE_SUMMARY_NAME
        )
        latest_summary = merger.load_json(ledger_root / merger.LATEST_SUMMARY_NAME)
        assert len(round_2_rows) == round_2_summary["ledger_rows"] == 4
        assert len(cumulative_rows) == len(latest_rows) == 8
        assert len({row["verification_id"] for row in cumulative_rows}) == 8
        assert len({row["candidate_queue_row_id"] for row in cumulative_rows}) == 8
        assert cumulative_summary == latest_summary
        assert cumulative_summary["summary_scope"] == "cumulative_project_wide"
        assert cumulative_summary["verification_round_ids"] == [round_1, round_2]
        assert cumulative_summary["round_rows"] == {round_1: 4, round_2: 4}
        assert cumulative_summary["reachable_or_reused_total"] == 8
        assert cumulative_summary["rows_added_by_latest_merge"] == 4


def main() -> int:
    protected = {
        path: digest(path)
        for path in [QUEUE, MUNICIPALITY_COVERAGE, STATE_COVERAGE, COUNTY_COVERAGE]
    }
    tests = [
        test_identity_and_duplicate_groups,
        test_scope_controls,
        test_large_profiles,
        test_option_b_remainder_excludes_round1_and_balances,
        test_dry_runner_opens_no_urls_and_audits,
        test_mocked_live_path_and_duplicate_reuse,
        test_serial_merge_preserves_rows_and_fields,
        test_serial_merge_rejects_duplicate_pending_and_ineligible,
        test_serial_merge_builds_cumulative_latest_without_losing_prior_round,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    for path, before in protected.items():
        assert digest(path) == before, f"Protected accounting file changed: {path}"
    print("PASS no_candidate_queue_or_coverage_files_modified")
    print(
        f"All {len(tests) + 1} scaled-verification tests passed; "
        "all live-path HTTP behavior used MockTransport; external network calls=0."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
