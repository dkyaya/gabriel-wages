#!/usr/bin/env python3
"""Regression tests for bounded source review/download over 429 verified leads."""

from __future__ import annotations

import asyncio
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

import httpx


ROOT = Path(__file__).resolve().parent.parent
RUNNER = ROOT / "scripts/run_targeted_source_review_download_429.py"
SPEC = importlib.util.spec_from_file_location("source_review_download_429", RUNNER)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mod
SPEC.loader.exec_module(mod)
DASHBOARD_RUNNER = ROOT / "scripts/build_dashboard_data.py"
DASHBOARD_SPEC = importlib.util.spec_from_file_location("source_review_download_429_dashboard", DASHBOARD_RUNNER)
assert DASHBOARD_SPEC and DASHBOARD_SPEC.loader
dashboard = importlib.util.module_from_spec(DASHBOARD_SPEC)
sys.modules[DASHBOARD_SPEC.name] = dashboard
DASHBOARD_SPEC.loader.exec_module(dashboard)


class SourceReviewDownload429Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.queue, cls.hashes = mod.verify_inputs()

    def test_task_lineage_and_scope(self) -> None:
        self.assertEqual(mod.INPUT_COMMIT, "03c728630dfaaafd027ed222bc7120769eec1a58")
        self.assertEqual(len(self.queue), 429)
        self.assertEqual(mod.id_set_hash(self.queue), mod.EXPECTED_ID_SET_HASH)

    def test_immutable_inputs_match(self) -> None:
        self.assertEqual(self.hashes, mod.EXPECTED_HASHES)

    def test_only_verified_tier_a_b_enter(self) -> None:
        self.assertTrue(all(row["verification_status"] == "verified_source_lead" for row in self.queue))
        self.assertEqual({tier: sum(row["priority_tier"] == tier for row in self.queue) for tier in mod.EXPECTED_TIERS}, mod.EXPECTED_TIERS)
        self.assertEqual({lane: sum(row["lane_id"] == lane for row in self.queue) for lane in mod.EXPECTED_LANES}, mod.EXPECTED_LANES)

    def test_nonverified_results_are_excluded(self) -> None:
        all_rows = mod.read_csv(mod.INPUT_DIR / "targeted_source_verification_tier_a_b_results.csv")
        queue_ids = {row["candidate_id"] for row in self.queue}
        excluded = {row["candidate_id"] for row in all_rows if row["verification_status"] != "verified_source_lead"}
        self.assertFalse(queue_ids & excluded)
        self.assertEqual(len(excluded), 342)

    def test_downstream_statuses_closed_at_input(self) -> None:
        for row in self.queue:
            self.assertEqual(row["download_status"], "not_downloaded")
            self.assertEqual(row["extraction_status"], "not_extracted")
            self.assertEqual(row["rating_status"], "not_rated")
            self.assertEqual(row["causal_status"], "not_causal_evidence")

    def test_bounded_transport_contract(self) -> None:
        self.assertEqual(mod.MAX_CONCURRENCY, 8)
        self.assertEqual(mod.MAX_RETRIES, 1)
        self.assertLessEqual(mod.MAX_FILE_BYTES, 25 * 1024 * 1024)
        self.assertLessEqual(mod.TIMEOUT_SECONDS, 30)

    def test_retained_directory_is_task_local(self) -> None:
        self.assertEqual(mod.RETAINED_DIR.parent, mod.OUTPUT_DIR)
        self.assertTrue(str(mod.RETAINED_DIR).startswith(str(mod.ROOT / "docs/analysis")))

    def test_source_has_no_pdf_parser_or_ocr_or_model(self) -> None:
        source = RUNNER.read_text(encoding="utf-8").casefold()
        for forbidden in ("pypdf", "pdfplumber", "pymupdf", "fitz.open", "tesseract", "ocrmypdf", "openai", "gabriel.codify"):
            self.assertNotIn(forbidden, source)
        self.assertIn('client.stream("get", url)', source)
        self.assertIn("response.aiter_bytes", source)

    def _locked(self) -> dict[str, str]:
        return mod.lock_row(self.queue[0])

    async def _download_with(self, handler, row=None):
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler), follow_redirects=True) as client:
            return await mod.download_one(client, row or self._locked())

    def test_pdf_download_streams_and_hashes_without_parsing(self) -> None:
        old_root, old_retained = mod.ROOT, mod.RETAINED_DIR
        with tempfile.TemporaryDirectory() as temp:
            mod.ROOT = Path(temp)
            mod.RETAINED_DIR = mod.ROOT / "retained"
            mod.RETAINED_DIR.mkdir()
            payload = b"%PDF-1.7\nsynthetic bytes only\n%%EOF\n"
            result = asyncio.run(self._download_with(lambda request: httpx.Response(200, headers={"content-type": "application/pdf"}, content=payload, request=request)))
            self.assertEqual(result["status"], "retained_downloaded_source")
            self.assertEqual(result["extension"], ".pdf")
            self.assertEqual(result["size"], len(payload))
            self.assertTrue(Path(result["path"]).name.endswith(".pdf"))
        mod.ROOT, mod.RETAINED_DIR = old_root, old_retained

    def test_404_is_unavailable(self) -> None:
        result = asyncio.run(self._download_with(lambda request: httpx.Response(404, request=request)))
        self.assertEqual(result["status"], "unavailable_on_get")

    def test_403_is_needs_review(self) -> None:
        result = asyncio.run(self._download_with(lambda request: httpx.Response(403, request=request)))
        self.assertEqual(result["status"], "weak_or_needs_review")

    def test_500_retries_once_then_blocks(self) -> None:
        calls = []
        def handler(request):
            calls.append(request.method)
            return httpx.Response(500, request=request)
        result = asyncio.run(self._download_with(handler))
        self.assertEqual(result["status"], "blocked_by_transport")
        self.assertEqual(calls, ["GET", "GET"])

    def test_unsupported_content_type_is_quarantined(self) -> None:
        old = mod.RETAINED_DIR
        with tempfile.TemporaryDirectory() as temp:
            mod.RETAINED_DIR = Path(temp)
            result = asyncio.run(self._download_with(lambda request: httpx.Response(200, headers={"content-type": "image/png"}, content=b"PNG", request=request)))
            self.assertEqual(result["status"], "wrong_content_type")
            self.assertEqual(list(Path(temp).iterdir()), [])
        mod.RETAINED_DIR = old

    def test_html_with_embedded_key_literal_is_not_retained(self) -> None:
        old = mod.RETAINED_DIR
        with tempfile.TemporaryDirectory() as temp:
            mod.RETAINED_DIR = Path(temp)
            payload = b"<html><script>widget.initialize({ api_key: 'public-widget-key' });</script></html>"
            result = asyncio.run(self._download_with(lambda request: httpx.Response(200, headers={"content-type": "text/html"}, content=payload, request=request)))
            self.assertEqual(result["status"], "weak_or_needs_review")
            self.assertEqual(list(Path(temp).iterdir()), [])
        mod.RETAINED_DIR = old

    def test_content_length_oversize_is_quarantined(self) -> None:
        result = asyncio.run(self._download_with(lambda request: httpx.Response(200, headers={"content-type": "application/pdf", "content-length": str(mod.MAX_FILE_BYTES + 1)}, request=request)))
        self.assertEqual(result["status"], "oversized_for_this_pass")

    def test_result_row_keeps_all_downstream_boundaries_closed(self) -> None:
        row = self._locked()
        raw = {"status": "retained_downloaded_source", "reason": "fixture", "http_status": 200,
               "content_type": "application/pdf", "extension": ".pdf", "size": 10,
               "sha256": "a" * 64, "path": "docs/analysis/task/fixture.pdf", "attempts": 1, "elapsed": 0.1}
        result = mod.result_row(row, raw, "2026-07-26T00:00:00Z")
        self.assertEqual(result["extraction_status"], "not_extracted")
        self.assertEqual(result["rating_status"], "not_rated")
        self.assertEqual(result["ingestion_status"], "not_ingested")
        self.assertEqual(result["codification_status"], "not_codified")
        self.assertEqual(result["causal_status"], "not_causal_evidence")
        self.assertEqual(result["global_analysis_readiness"], "false")

    def test_controlled_status_inventory(self) -> None:
        self.assertEqual(len(mod.CONTROLLED_STATUSES), 8)
        self.assertIn("duplicate_file_hash", mod.CONTROLLED_STATUSES)
        self.assertIn("oversized_for_this_pass", mod.CONTROLLED_STATUSES)

    def test_duplicate_hash_quarantine_removes_redundant_copy(self) -> None:
        old_root, old_retained = mod.ROOT, mod.RETAINED_DIR
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); retained = root / "retained"; retained.mkdir()
            mod.ROOT, mod.RETAINED_DIR = root, retained
            first = retained / "a.pdf"; second = retained / "b.pdf"
            first.write_bytes(b"same"); second.write_bytes(b"same")
            base = {"source_review_download_status": "retained_downloaded_source", "file_sha256": mod.sha256(first),
                    "priority_tier": "tier_a", "duplicate_file_group_id": "", "notes": "", "candidate_id": "A"}
            rows = [{**base, "local_retained_path": "retained/a.pdf"},
                    {**base, "priority_tier": "tier_b", "candidate_id": "B", "local_retained_path": "retained/b.pdf"}]
            groups = mod.quarantine_duplicate_hashes(rows)
            self.assertEqual(len(groups), 1)
            self.assertEqual(rows[1]["source_review_download_status"], "duplicate_file_hash")
            self.assertTrue(first.exists()); self.assertFalse(second.exists())
        mod.ROOT, mod.RETAINED_DIR = old_root, old_retained

    def test_partial_outputs_fail_closed(self) -> None:
        old_out, old_retained = mod.OUTPUT_DIR, mod.RETAINED_DIR
        with tempfile.TemporaryDirectory() as temp:
            mod.OUTPUT_DIR = Path(temp)
            mod.RETAINED_DIR = mod.OUTPUT_DIR / "retained_sources"
            mod.RETAINED_DIR.mkdir()
            (mod.OUTPUT_DIR / mod.REQUIRED_FINAL_OUTPUTS[0]).touch()
            with self.assertRaises(RuntimeError):
                mod.validate_complete()
        mod.OUTPUT_DIR, mod.RETAINED_DIR = old_out, old_retained

    def test_prepared_lock_when_present(self) -> None:
        path = mod.OUTPUT_DIR / "targeted_source_review_download_429_lock.json"
        if not path.exists():
            self.skipTest("dry preparation has not run")
        lock = mod.read_json(path)
        locked = mod.read_csv(mod.OUTPUT_DIR / "targeted_source_review_download_429_locked_queue.csv")
        self.assertEqual(len(locked), 429)
        self.assertEqual(lock["candidate_id_set_sha256"], mod.EXPECTED_ID_SET_HASH)
        self.assertEqual(mod.id_set_hash(locked), mod.EXPECTED_ID_SET_HASH)

    def test_completed_outputs_when_present(self) -> None:
        decision_path = mod.OUTPUT_DIR / "targeted_source_review_download_429_decision.json"
        if not decision_path.exists():
            self.skipTest("live download has not completed")
        mod.validate_complete()
        decision = mod.read_json(decision_path)
        self.assertEqual(decision["locked_download_queue_count"], 429)
        self.assertFalse(decision["global_analysis_readiness"])

    def test_future_prompt_when_present_preserves_boundaries(self) -> None:
        prompts = list(mod.OUTPUT_DIR.glob("next_targeted_*_prompt.md"))
        if not prompts:
            self.skipTest("live download has not completed")
        text = prompts[0].read_text(encoding="utf-8").casefold()
        for phrase in ("separately authorized", "not extracted", "not rated", "not ingested", "not causal evidence", "global analysis readiness true"):
            self.assertIn(phrase, text)

    def test_dashboard_source_review_download_gate(self) -> None:
        completed, decision = dashboard.targeted_source_review_download_429_status()
        self.assertTrue(completed)
        self.assertEqual(decision["locked_download_queue_count"], 429)
        self.assertEqual(decision["retained_downloaded_source_count"], 387)
        self.assertFalse(decision["global_analysis_readiness"])

    def test_dashboard_generated_status_remains_closed(self) -> None:
        readiness = mod.read_json(ROOT / "docs/dashboard/data/analysis_readiness.json")
        calibration = mod.read_json(ROOT / "docs/dashboard/data/text_table_calibration_status_summary.json")
        self.assertEqual(readiness["overall_status"], "quantitative_to_qualitative_mechanism_linkage_513_completed_claim_review_ready_global_analysis_closed")
        self.assertEqual(calibration["calibration_phase"], "quantitative_to_qualitative_mechanism_linkage_513_completed_claim_review_ready")
        self.assertTrue(calibration["targeted_source_review_download_completed"])
        self.assertEqual(calibration["targeted_source_review_download_retained_count"], 387)
        self.assertTrue(calibration["targeted_pdf_text_layer_readiness_ready_next"])


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(SourceReviewDownload429Tests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    passed = result.testsRun - len(result.failures) - len(result.errors)
    print(f"source-review/download checks: {passed}/{result.testsRun} passed")
    raise SystemExit(0 if result.wasSuccessful() else 1)
