#!/usr/bin/env python3
"""Focused, no-network tests for the remaining-municipality live runner."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import run_broad_state_remaining_5lane_live_scout as live  # noqa: E402


class RemainingLiveScoutTests(unittest.TestCase):
    def test_locked_queue_reconciles(self) -> None:
        result = live.validate_locks()
        self.assertTrue(result["passed"])
        self.assertEqual(result["master_target_count"], 18_702)
        self.assertEqual(sum(result["lane_counts"].values()), 18_702)

    def test_query_packet_is_mapped_without_mutating_locked_row(self) -> None:
        row = live.read_csv(live.lane_queue_path(1))[0]
        original = dict(row)
        adapted = live.adapt_target(row)
        self.assertEqual(row, original)
        self.assertEqual(adapted["scout_target_id"], row["target_id"])
        self.assertEqual(adapted["search_hint_1"], row["primary_query"])
        self.assertEqual(adapted["search_hint_2"], row["secondary_query"])
        self.assertIn(row["source_family_query_family"], adapted["selection_reason"])

    def test_terminal_status_mapping(self) -> None:
        self.assertEqual(live.terminal_status({"parse_status": "parseable", "candidate_count": 2}), "parseable_with_candidates")
        self.assertEqual(live.terminal_status({"parse_status": "parseable", "candidate_count": 0}), "parseable_no_candidates")
        self.assertEqual(live.terminal_status({"parse_status": "failed", "failure_type": "timeout"}), "search_error")
        self.assertEqual(live.terminal_status({"parse_status": "failed", "failure_type": "invalid_json"}), "failed_unparseable")

    def test_preflight_requires_safe_transport_and_parseable_probe(self) -> None:
        safe = {
            "gate_status": "passed",
            "transport_diagnostic": {
                "diagnosis_category": "A",
                "metadata_only": True,
                "secret_exposure_detected": False,
                "raw_prompts_persisted": False,
                "raw_responses_persisted": False,
                "queue_coverage_dashboard_corpus_changed": False,
            },
            "one_row_probe": {"passed": True, "parseable_rows": 1},
        }
        with tempfile.TemporaryDirectory(dir=ROOT / "tmp") as temporary:
            path = Path(temporary)
            (path / "preflight_plan.json").write_text(json.dumps(safe), encoding="utf-8")
            self.assertEqual(live.validate_preflight(path)["gate_status"], "passed")
            safe["one_row_probe"] = {"passed": False, "parseable_rows": 0}
            (path / "preflight_plan.json").write_text(json.dumps(safe), encoding="utf-8")
            with self.assertRaises(RuntimeError):
                live.validate_preflight(path)

    def test_checkpoint_rejects_corrupt_or_foreign_outcome(self) -> None:
        queue = live.read_csv(live.lane_queue_path(1))[:1]
        lane_hash = "test-lane-hash"
        with tempfile.TemporaryDirectory(dir=ROOT / "tmp") as temporary:
            outcome = Path(temporary) / "outcome.json"
            outcome.write_text('{"terminal_status":"parseable_no_candidates"}\n', encoding="utf-8")
            entry = {
                "target_id": queue[0]["target_id"],
                "outcome_path": str(outcome.relative_to(ROOT)),
                "outcome_sha256": live.sha256_file(outcome),
            }
            checkpoint = {"lane_queue_sha256": lane_hash, "accepted": [entry]}
            self.assertEqual(live.accepted_entries(checkpoint, 1, queue, lane_hash), [entry])
            checkpoint["accepted"][0]["target_id"] = "foreign-target"
            with self.assertRaises(RuntimeError):
                live.accepted_entries(checkpoint, 1, queue, lane_hash)


if __name__ == "__main__":
    unittest.main()
