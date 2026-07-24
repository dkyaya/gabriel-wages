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


def main() -> int:
    protected = {
        path: digest(path)
        for path in [QUEUE, MUNICIPALITY_COVERAGE, STATE_COVERAGE, COUNTY_COVERAGE]
    }
    tests = [
        test_identity_and_duplicate_groups,
        test_scope_controls,
        test_large_profiles,
        test_dry_runner_opens_no_urls_and_audits,
        test_mocked_live_path_and_duplicate_reuse,
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
