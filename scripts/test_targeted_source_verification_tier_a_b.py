#!/usr/bin/env python3
"""Regression tests for the Tier A+B HEAD-only verifier."""

from __future__ import annotations

import asyncio
import csv
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

import httpx


ROOT = Path(__file__).resolve().parent.parent
RUNNER = ROOT / "scripts/run_targeted_source_verification_tier_a_b.py"
SPEC = importlib.util.spec_from_file_location("tier_ab_verifier", RUNNER)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mod
SPEC.loader.exec_module(mod)
DASHBOARD_RUNNER = ROOT / "scripts/build_dashboard_data.py"
DASHBOARD_SPEC = importlib.util.spec_from_file_location("tier_ab_verification_dashboard", DASHBOARD_RUNNER)
assert DASHBOARD_SPEC and DASHBOARD_SPEC.loader
dashboard = importlib.util.module_from_spec(DASHBOARD_SPEC)
sys.modules[DASHBOARD_SPEC.name] = dashboard
DASHBOARD_SPEC.loader.exec_module(dashboard)


class TierABVerificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.queue, cls.hashes = mod.verify_inputs()

    def test_task_lineage(self) -> None:
        self.assertEqual(mod.INPUT_COMMIT, "bc6ef99ab321c05fd0976bd4c08c81da6b8f8321")
        self.assertEqual(mod.EXPECTED_COUNT, 771)

    def test_immutable_input_hashes(self) -> None:
        self.assertEqual(self.hashes, mod.EXPECTED_HASHES)

    def test_exact_tier_a_b_scope(self) -> None:
        self.assertEqual(len(self.queue), 771)
        counts = {tier: sum(row["verification_priority_tier"] == tier for row in self.queue) for tier in mod.EXPECTED_TIERS}
        self.assertEqual(counts, mod.EXPECTED_TIERS)

    def test_tier_c_d_repair_deprioritized_excluded(self) -> None:
        self.assertTrue(all(row["verification_priority_tier"] in {"tier_a", "tier_b"} for row in self.queue))
        self.assertTrue(all(row["candidate_quality_label"] in {"verification_ready_high", "verification_ready_medium"} for row in self.queue))

    def test_id_set_hash_locked(self) -> None:
        self.assertEqual(mod.id_set_hash(self.queue), mod.EXPECTED_ID_SET_HASH)

    def test_candidate_only_lineage(self) -> None:
        for row in self.queue:
            self.assertEqual(row["retrieval_status"], "candidate_only")
            self.assertEqual(row["verification_status"], "not_verified")
            self.assertEqual(row["extraction_status"], "not_extracted")
            self.assertEqual(row["rating_status"], "not_rated")
            self.assertEqual(row["causal_status"], "not_causal_evidence")

    def test_prepared_lock_matches_queue(self) -> None:
        lock = mod.read_json(mod.OUTPUT_DIR / "targeted_source_verification_tier_a_b_lock.json")
        locked = mod.read_csv(mod.OUTPUT_DIR / "targeted_source_verification_tier_a_b_locked_queue.csv")
        self.assertEqual(len(locked), 771)
        self.assertEqual(lock["tier_counts"], mod.EXPECTED_TIERS)
        self.assertEqual(mod.sha256(mod.OUTPUT_DIR / "targeted_source_verification_tier_a_b_locked_queue.csv"), lock["queue_sha256"])
        self.assertEqual(mod.id_set_hash(locked), lock["candidate_id_set_sha256"])

    def test_dry_run_no_call_contract(self) -> None:
        summary = mod.read_json(mod.OUTPUT_DIR / "targeted_source_verification_tier_a_b_dry_run_summary.json")
        self.assertTrue(summary["no_call_dry_run"])
        self.assertEqual(summary["dry_run_rows"], 771)
        self.assertEqual(summary["live_requests"], 0)
        self.assertEqual(summary["downloads"], 0)
        self.assertEqual(summary["pdf_page_accesses"], 0)

    def test_source_enforces_head_only(self) -> None:
        source = RUNNER.read_text(encoding="utf-8")
        self.assertIn('client.stream("HEAD", url)', source)
        self.assertNotIn('client.stream("GET"', source)
        self.assertNotIn("client.get(", source)
        self.assertNotIn("response.aread(", source)
        self.assertNotIn("response.content", source)
        self.assertNotIn("response.text", source)

    def test_bounded_transport_contract(self) -> None:
        self.assertEqual(mod.MAX_CONCURRENCY, 12)
        self.assertEqual(mod.MAX_RETRIES, 1)
        self.assertEqual(mod.MAX_REDIRECTS, 5)
        self.assertLessEqual(mod.TIMEOUT_SECONDS, 10)

    def _client(self, handler):
        return httpx.AsyncClient(transport=httpx.MockTransport(handler), follow_redirects=True)

    def test_head_probe_reachable(self) -> None:
        row = mod.lock_row(self.queue[0])
        async def run():
            async with self._client(lambda request: httpx.Response(200, headers={"content-type": "application/pdf"}, request=request)) as client:
                return await mod.head_probe(client, row)
        result = asyncio.run(run())
        self.assertEqual(result["kind"], "verified_source_lead")
        self.assertEqual(result["status_code"], 200)

    def test_head_probe_404_unavailable(self) -> None:
        row = mod.lock_row(self.queue[0])
        async def run():
            async with self._client(lambda request: httpx.Response(404, request=request)) as client:
                return await mod.head_probe(client, row)
        self.assertEqual(asyncio.run(run())["kind"], "unavailable")

    def test_head_probe_405_needs_review_no_get_fallback(self) -> None:
        row = mod.lock_row(self.queue[0])
        methods = []
        def handler(request):
            methods.append(request.method)
            return httpx.Response(405, request=request)
        async def run():
            async with self._client(handler) as client:
                return await mod.head_probe(client, row)
        self.assertEqual(asyncio.run(run())["kind"], "weak_or_needs_review")
        self.assertEqual(methods, ["HEAD"])

    def test_head_probe_500_retries_once(self) -> None:
        row = mod.lock_row(self.queue[0])
        calls = []
        def handler(request):
            calls.append(request.method)
            return httpx.Response(500, request=request)
        async def run():
            async with self._client(handler) as client:
                return await mod.head_probe(client, row)
        result = asyncio.run(run())
        self.assertEqual(result["kind"], "blocked_by_transport")
        self.assertEqual(calls, ["HEAD", "HEAD"])

    def test_invalid_locator_is_verification_error(self) -> None:
        row = mod.lock_row(self.queue[0]); row["source_url_or_locator"] = "not a web locator"
        async def run():
            async with self._client(lambda request: httpx.Response(200, request=request)) as client:
                return await mod.head_probe(client, row)
        self.assertEqual(asyncio.run(run())["kind"], "verification_error")

    def test_explicit_period_conflict(self) -> None:
        row = mod.lock_row(self.queue[0])
        row["source_title"] = "Agreement 2001-2003"
        row["source_url_or_locator"] = "https://example.org/agreement-2001-2003.pdf"
        row["contract_or_document_period"] = "2018-2020"
        kind, _, _ = mod.identity_assessment(row, row["source_url_or_locator"], "application/pdf")
        self.assertEqual(kind, "wrong_period")

    def test_explicit_wrong_unit(self) -> None:
        row = mod.lock_row(self.queue[0])
        row.update({"unit_type": "non_safety_comparator", "source_title": "Police Department Agreement", "occupation_group": "Police officers", "bargaining_unit_name": "Police Patrolmen"})
        kind, _, _ = mod.identity_assessment(row, row["source_url_or_locator"], "application/pdf")
        self.assertEqual(kind, "wrong_unit")

    def test_explicit_discourse_only(self) -> None:
        row = mod.lock_row(self.queue[0]); row["source_title"] = "Newspaper article about bargaining"
        kind, _, _ = mod.identity_assessment(row, row["source_url_or_locator"], "text/html")
        self.assertEqual(kind, "discourse_only")

    def test_result_row_preserves_downstream_closure(self) -> None:
        row = mod.lock_row(self.queue[0])
        probe = {"kind": "verified_source_lead", "reason": "fixture", "status_code": 200, "content_type": "application/pdf", "final_locator": row["source_url_or_locator"], "elapsed": 0.1, "attempts": 1, "identity_score": 10}
        result = mod.result_row(row, probe, "2026-07-26T00:00:00Z")
        self.assertEqual(result["download_status"], "not_downloaded")
        self.assertEqual(result["extraction_status"], "not_extracted")
        self.assertEqual(result["rating_status"], "not_rated")
        self.assertEqual(result["causal_status"], "not_causal_evidence")
        self.assertNotIn(row["source_url_or_locator"], result["notes"])

    def test_controlled_status_inventory(self) -> None:
        self.assertEqual(len(mod.CONTROLLED_STATUSES), 10)
        self.assertIn("verified_source_lead", mod.CONTROLLED_STATUSES)
        self.assertIn("blocked_by_transport", mod.CONTROLLED_STATUSES)

    def test_partial_outputs_fail_closed(self) -> None:
        old = mod.OUTPUT_DIR
        with tempfile.TemporaryDirectory() as temp:
            mod.OUTPUT_DIR = Path(temp)
            (mod.OUTPUT_DIR / mod.REQUIRED_FINAL_OUTPUTS[0]).touch()
            with self.assertRaises(RuntimeError):
                mod.validate_complete()
        mod.OUTPUT_DIR = old

    def test_completed_outputs_when_present(self) -> None:
        decision = mod.OUTPUT_DIR / "targeted_source_verification_tier_a_b_decision.json"
        if not decision.exists():
            self.skipTest("live verification not completed yet")
        mod.validate_complete()
        data = mod.read_json(decision)
        self.assertEqual(data["verification_queue_count"], 771)
        self.assertEqual(data["get_requests"], 0)
        self.assertEqual(data["documents_downloaded"], 0)
        self.assertFalse(data["global_analysis_readiness"])

    def test_future_prompt_when_present_preserves_boundary(self) -> None:
        prompts = list(mod.OUTPUT_DIR.glob("next_targeted_*_prompt.md"))
        if not prompts:
            self.skipTest("live verification not completed yet")
        text = prompts[0].read_text(encoding="utf-8")
        for phrase in ("separately authorized", "must not extract", "not downloaded", "not rated", "not causal evidence", "global analysis readiness true"):
            self.assertIn(phrase, text)

    def test_dashboard_tier_a_b_verification_gate(self) -> None:
        completed, decision = dashboard.targeted_source_verification_tier_a_b_status()
        self.assertTrue(completed)
        self.assertEqual(decision["verification_queue_count"], 771)
        self.assertEqual(decision["verified_source_lead_count"], 429)
        self.assertFalse(decision["global_analysis_readiness"])

    def test_dashboard_generated_status_remains_closed(self) -> None:
        readiness = mod.read_json(ROOT / "docs/dashboard/data/analysis_readiness.json")
        calibration = mod.read_json(ROOT / "docs/dashboard/data/text_table_calibration_status_summary.json")
        self.assertEqual(
            readiness["overall_status"],
            "targeted_source_verification_tier_a_b_completed_source_review_ready_global_analysis_closed",
        )
        self.assertEqual(
            calibration["calibration_phase"],
            "targeted_source_verification_tier_a_b_completed_source_review_ready",
        )
        self.assertTrue(calibration["targeted_source_verification_completed"])
        self.assertEqual(calibration["targeted_source_verified_source_lead_count"], 429)
        self.assertTrue(calibration["targeted_source_review_download_ready_next"])


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TierABVerificationTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    passed = result.testsRun - len(result.failures) - len(result.errors)
    print(f"Tier A+B verification checks: {passed}/{result.testsRun} passed")
    raise SystemExit(0 if result.wasSuccessful() else 1)
