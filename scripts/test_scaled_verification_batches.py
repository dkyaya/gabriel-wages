#!/usr/bin/env python3
"""Offline tests for the scaled candidate-source verification framework."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import tempfile
from pathlib import Path

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


def synthetic_queue() -> list[dict[str, str]]:
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
    rows = []
    for queue_id, url, bucket in [
        ("Q1", "https://example.invalid/document.pdf", "high_priority_later_verify"),
        ("Q2", "https://EXAMPLE.invalid/document.pdf#page=2", "medium_priority_later_verify"),
        ("Q3", "https://example.invalid/context", "context_only_hold"),
        ("Q4", "https://example.invalid/duplicate", "likely_duplicate_hold"),
    ]:
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


def test_canonical_round_3x250() -> None:
    with tempfile.TemporaryDirectory(prefix="verification_plan_test_") as temporary:
        output = Path(temporary) / "round"
        args = argparse.Namespace(
            candidate_queue_csv=str(QUEUE),
            output_dir=str(output),
            round_id="SYNTHETIC-CANONICAL-3X250",
            batch_size=250,
            num_lanes=3,
            include_held=False,
            include_duplicates=False,
            priority_scope="scheduled",
            state_scope="",
            plan_only=True,
        )
        result = planner.prepare(args)
        assert sum(len(lane) for lane in result["lanes"]) == 750
        assert [len(lane) for lane in result["lanes"]] == [250, 250, 250]
        ids = [
            str(row["verification_id"])
            for lane in result["lanes"]
            for row in lane
        ]
        assert len(ids) == len(set(ids)) == 750
        manifest = json.loads(
            (output / "verification_round_manifest.json").read_text(encoding="utf-8")
        )
        assert manifest["planned_candidate_rows"] == 750
        assert manifest["urls_opened"] == 0
        assert manifest["network_calls"] == 0


def write_input(path: Path) -> list[dict[str, str]]:
    enriched = planner.enrich_candidates(
        synthetic_queue()[:2], synthetic_universe(), {"MA": 2.5}
    )
    planner.write_csv(path, enriched, planner.IDENTITY_FIELDS)
    return [{key: str(value) for key, value in row.items()} for row in enriched]


def test_dry_runner_and_auditor() -> None:
    with tempfile.TemporaryDirectory(prefix="verification_dry_test_") as temporary:
        root = Path(temporary)
        input_path = root / "lane_1_input.csv"
        expected = write_input(input_path)
        dry_dir = root / "lane_1_dry"
        summary = verifier.run_dry(
            argparse.Namespace(
                input_csv=str(input_path),
                output_dir=str(dry_dir),
                max_rows=None,
                timeout=30.0,
                concurrency=3,
                respect_robots_note=True,
            )
        )
        assert summary["planned_rows"] == 2
        assert summary["urls_opened"] == 0
        assert summary["network_calls"] == 0
        ledger = verifier.read_input(input_path, None)
        assert [row["verification_id"] for row in ledger] == [
            row["verification_id"] for row in expected
        ]
        with (dry_dir / "verification_ledger.csv").open(
            newline="", encoding="utf-8"
        ) as handle:
            ledger_rows = list(csv.DictReader(handle))
        assert len(ledger_rows) == 2
        assert all(
            row["verification_status"] == "planned_not_verified"
            for row in ledger_rows
        )

        manifest_path = root / "manifest.json"
        manifest = {
            "round_id": "DRY-TEST",
            "lanes": [
                {
                    "lane_id": "lane_1",
                    "input_csv": str(input_path),
                    "input_sha256": digest(input_path),
                    "expected_rows": 2,
                    "dry_run_output_dir": str(dry_dir),
                    "live_output_dir": str(root / "lane_1_live"),
                }
            ],
        }
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        result = auditor.audit(manifest_path, root / "audit")
        assert result["lane_classification_counts"] == {"dry_run_passed": 1}
        assert (
            result["merge_recommendation"]
            == "dry_run_complete_do_not_merge_live_ledger"
        )
        assert result["urls_opened"] == 0
        assert result["network_calls"] == 0


def main() -> int:
    protected = {
        path: digest(path)
        for path in [QUEUE, MUNICIPALITY_COVERAGE, STATE_COVERAGE, COUNTY_COVERAGE]
    }
    tests = [
        test_identity_and_duplicate_groups,
        test_scope_controls,
        test_canonical_round_3x250,
        test_dry_runner_and_auditor,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    for path, before in protected.items():
        assert digest(path) == before, f"Protected accounting file changed: {path}"
    print("PASS no_candidate_queue_or_coverage_files_modified")
    print(f"All {len(tests) + 1} scaled-verification tests passed; network calls=0.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
