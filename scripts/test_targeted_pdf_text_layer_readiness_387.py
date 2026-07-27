#!/usr/bin/env python3
"""Regression tests for the bounded 387-file PDF/HTML readiness review."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parent.parent
RUNNER = ROOT / "scripts/run_targeted_pdf_text_layer_readiness_387.py"
SPEC = importlib.util.spec_from_file_location("targeted_pdf_text_layer_readiness_387", RUNNER)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mod
SPEC.loader.exec_module(mod)
DASHBOARD_RUNNER = ROOT / "scripts/build_dashboard_data.py"
DASHBOARD_SPEC = importlib.util.spec_from_file_location("targeted_pdf_text_layer_readiness_387_dashboard", DASHBOARD_RUNNER)
assert DASHBOARD_SPEC and DASHBOARD_SPEC.loader
dashboard = importlib.util.module_from_spec(DASHBOARD_SPEC)
sys.modules[DASHBOARD_SPEC.name] = dashboard
DASHBOARD_SPEC.loader.exec_module(dashboard)


class TargetedPDFTextLayerReadiness387Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.queue, cls.excluded, cls.hashes = mod.verify_inputs(verify_file_bytes=True)

    def test_exact_scope_and_lineage(self) -> None:
        self.assertEqual(mod.INPUT_COMMIT, "d39fdd79595905178314d5455cd0bd7602329592")
        self.assertEqual(len(self.queue), 387)
        self.assertEqual(mod.id_set_hash(self.queue), mod.EXPECTED_ID_SET_HASH)

    def test_immutable_inputs_match(self) -> None:
        self.assertEqual(self.hashes, mod.EXPECTED_HASHES)

    def test_content_types_and_lanes_reconcile(self) -> None:
        self.assertEqual({key: sum(row["content_type_hint"] == key for row in self.queue) for key in mod.EXPECTED_TYPES}, mod.EXPECTED_TYPES)
        self.assertEqual({key: sum(row["lane_id"] == key for row in self.queue) for key in mod.EXPECTED_LANES}, mod.EXPECTED_LANES)

    def test_prior_exclusions_do_not_enter(self) -> None:
        self.assertEqual(len(self.excluded), 42)
        self.assertFalse({row["candidate_id"] for row in self.queue} & {row["candidate_id"] for row in self.excluded})

    def test_only_retained_sources_enter(self) -> None:
        for row in self.queue:
            self.assertEqual(row["source_review_download_status"], "retained_downloaded_source")
            self.assertEqual(row["download_status"], "downloaded_retained")

    def test_all_input_paths_are_task_local_and_hash_valid(self) -> None:
        retained_dir = (mod.INPUT_DIR / "retained_sources").resolve()
        for row in self.queue:
            path = mod.ROOT / row["local_retained_path"]
            self.assertTrue(path.resolve().is_relative_to(retained_dir))
            self.assertEqual(path.stat().st_size, int(row["file_size_bytes"]))

    def test_downstream_boundaries_are_closed_at_input(self) -> None:
        for row in self.queue:
            self.assertEqual(row["extraction_status"], "not_extracted")
            self.assertEqual(row["rating_status"], "not_rated")
            self.assertEqual(row["ingestion_status"], "not_ingested")
            self.assertEqual(row["codification_status"], "not_codified")
            self.assertEqual(row["causal_status"], "not_causal_evidence")
            self.assertEqual(row["global_analysis_readiness"], "false")

    def test_runner_has_no_network_ocr_render_or_model_dependencies(self) -> None:
        source = RUNNER.read_text(encoding="utf-8").casefold()
        for forbidden in ("import httpx", "import requests", "urllib.request", "tesseract", "ocrmypdf", "pdftoppm", "pdf2image", "openai", "gabriel.codify"):
            self.assertNotIn(forbidden, source)
        self.assertIn("max_pdf_probe_pages = 3", source)
        self.assertIn('"pdftotext", "-f", "1", "-l"', source)

    def test_pdfinfo_parser(self) -> None:
        parsed = mod.parse_pdfinfo(b"Pages: 41\nEncrypted: no\nPDF version: 1.7\n")
        self.assertEqual(parsed, {"page_count": 41, "encrypted": False, "pdf_version": "1.7"})

    def _pdf_row(self, root: Path, size: int = 32) -> dict[str, str]:
        path = root / "fixture.pdf"
        path.write_bytes(b"%PDF-1.7\n" + b"x" * max(0, size - 9))
        row = {field: "" for field in mod.LOCK_FIELDS}
        row.update({
            "retained_source_id": "R", "candidate_id": "C", "lane_id": "lane_1",
            "content_type_hint": "application/pdf", "file_extension": ".pdf",
            "file_size_bytes": str(path.stat().st_size), "local_retained_path": "fixture.pdf",
            "source_review_download_status": "retained_downloaded_source",
            "download_status": "downloaded_retained", "extraction_status": "not_extracted",
            "rating_status": "not_rated", "ingestion_status": "not_ingested",
            "codification_status": "not_codified", "causal_status": "not_causal_evidence",
            "global_analysis_readiness": "false",
        })
        return row

    def test_pdf_text_layer_signal_classifies_parse_later(self) -> None:
        old_root = mod.ROOT
        with tempfile.TemporaryDirectory() as temp:
            mod.ROOT = Path(temp)
            row = self._pdf_row(mod.ROOT)
            responses = [
                subprocess.CompletedProcess([], 0, b"Pages: 10\nEncrypted: no\nPDF version: 1.7\n", b""),
                subprocess.CompletedProcess([], 0, b"machine readable words " * 8, b""),
            ]
            with patch.object(mod, "run_local_command", side_effect=responses):
                result = mod.inspect_pdf(row)
            self.assertEqual(result["readiness_status"], "parse_text_layer_later")
            self.assertEqual(result["pdf_has_text_layer_hint"], "true")
            self.assertEqual(result["bounded_text_probe_pages"], "3")
        mod.ROOT = old_root

    def test_pdf_without_text_signal_defers_to_ocr_later(self) -> None:
        old_root = mod.ROOT
        with tempfile.TemporaryDirectory() as temp:
            mod.ROOT = Path(temp)
            row = self._pdf_row(mod.ROOT)
            responses = [
                subprocess.CompletedProcess([], 0, b"Pages: 2\nEncrypted: no\n", b""),
                subprocess.CompletedProcess([], 0, b" \n\f", b""),
            ]
            with patch.object(mod, "run_local_command", side_effect=responses):
                result = mod.inspect_pdf(row)
            self.assertEqual(result["readiness_status"], "ocr_later_or_defer")
            self.assertEqual(result["pdf_has_text_layer_hint"], "false")
        mod.ROOT = old_root

    def test_encrypted_pdf_needs_review_without_text_probe(self) -> None:
        old_root = mod.ROOT
        with tempfile.TemporaryDirectory() as temp:
            mod.ROOT = Path(temp)
            row = self._pdf_row(mod.ROOT)
            with patch.object(mod, "run_local_command", return_value=subprocess.CompletedProcess([], 0, b"Pages: 8\nEncrypted: yes\n", b"")) as command:
                result = mod.inspect_pdf(row)
            self.assertEqual(result["readiness_status"], "needs_review")
            self.assertEqual(command.call_count, 1)
        mod.ROOT = old_root

    def test_oversized_pdf_skips_text_probe(self) -> None:
        old_root = mod.ROOT
        with tempfile.TemporaryDirectory() as temp:
            mod.ROOT = Path(temp)
            row = self._pdf_row(mod.ROOT)
            row["file_size_bytes"] = str(mod.MAX_TEXT_PASS_BYTES + 1)
            with patch.object(mod, "run_local_command", return_value=subprocess.CompletedProcess([], 0, b"Pages: 8\nEncrypted: no\n", b"")) as command:
                result = mod.inspect_pdf(row)
            self.assertEqual(result["readiness_status"], "oversized_for_text_pass")
            self.assertEqual(command.call_count, 1)
        mod.ROOT = old_root

    def test_corrupt_pdf_is_explicit(self) -> None:
        old_root = mod.ROOT
        with tempfile.TemporaryDirectory() as temp:
            mod.ROOT = Path(temp)
            row = self._pdf_row(mod.ROOT)
            with patch.object(mod, "run_local_command", return_value=subprocess.CompletedProcess([], 1, b"", b"not a pdf")):
                result = mod.inspect_pdf(row)
            self.assertEqual(result["readiness_status"], "corrupt_or_unreadable")
        mod.ROOT = old_root

    def _html_row(self, root: Path, payload: bytes) -> dict[str, str]:
        path = root / "fixture.html"
        path.write_bytes(payload)
        row = {field: "" for field in mod.LOCK_FIELDS}
        row.update({
            "retained_source_id": "H", "candidate_id": "HC", "lane_id": "lane_2",
            "content_type_hint": "text/html", "file_extension": ".html",
            "file_size_bytes": str(path.stat().st_size), "local_retained_path": "fixture.html",
            "source_review_download_status": "retained_downloaded_source",
            "download_status": "downloaded_retained", "extraction_status": "not_extracted",
            "rating_status": "not_rated", "ingestion_status": "not_ingested",
            "codification_status": "not_codified", "causal_status": "not_causal_evidence",
            "global_analysis_readiness": "false",
        })
        return row

    def test_html_visible_text_classifies_html_later(self) -> None:
        old_root = mod.ROOT
        with tempfile.TemporaryDirectory() as temp:
            mod.ROOT = Path(temp)
            payload = ("<html><body><p>" + "municipal collective bargaining agreement " * 12 + "</p></body></html>").encode()
            result = mod.inspect_html(self._html_row(mod.ROOT, payload))
            self.assertEqual(result["readiness_status"], "html_text_later")
            self.assertEqual(result["html_text_readiness_hint"], "text_ready")
        mod.ROOT = old_root

    def test_html_redirect_shell_needs_review(self) -> None:
        old_root = mod.ROOT
        with tempfile.TemporaryDirectory() as temp:
            mod.ROOT = Path(temp)
            payload = b'<html><head><meta http-equiv="refresh" content="0;url=x"></head><body>Moved</body></html>'
            result = mod.inspect_html(self._html_row(mod.ROOT, payload))
            self.assertEqual(result["readiness_status"], "needs_review")
            self.assertEqual(result["html_text_readiness_hint"], "redirect_or_shell")
        mod.ROOT = old_root

    def test_empty_html_is_corrupt(self) -> None:
        old_root = mod.ROOT
        with tempfile.TemporaryDirectory() as temp:
            mod.ROOT = Path(temp)
            result = mod.inspect_html(self._html_row(mod.ROOT, b"tiny"))
            self.assertEqual(result["readiness_status"], "corrupt_or_unreadable")
        mod.ROOT = old_root

    def test_result_boundaries_remain_closed(self) -> None:
        row = self.queue[0]
        result = mod.inspection_result(row, "needs_review", "fixture")
        self.assertEqual(result["extraction_status"], "not_extracted")
        self.assertEqual(result["rating_status"], "not_rated")
        self.assertEqual(result["ingestion_status"], "not_ingested")
        self.assertEqual(result["codification_status"], "not_codified")
        self.assertEqual(result["causal_status"], "not_causal_evidence")
        self.assertEqual(result["global_analysis_readiness"], "false")

    def test_controlled_statuses_are_exact(self) -> None:
        self.assertEqual(len(mod.CONTROLLED_STATUSES), 7)
        self.assertIn("parse_text_layer_later", mod.CONTROLLED_STATUSES)
        self.assertIn("html_text_later", mod.CONTROLLED_STATUSES)
        self.assertIn("ocr_later_or_defer", mod.CONTROLLED_STATUSES)

    def test_prepared_lock_when_present(self) -> None:
        path = mod.OUTPUT_DIR / "targeted_pdf_text_layer_readiness_387_lock.json"
        if not path.exists():
            self.skipTest("readiness preparation has not run")
        lock = mod.read_json(path)
        locked = mod.read_csv(mod.OUTPUT_DIR / "targeted_pdf_text_layer_readiness_387_locked_queue.csv")
        self.assertEqual(len(locked), 387)
        self.assertEqual(lock["retained_source_id_set_sha256"], mod.EXPECTED_ID_SET_HASH)
        self.assertEqual(lock["retained_file_integrity_pass_count"], 387)

    def test_completed_outputs_when_present(self) -> None:
        decision_path = mod.OUTPUT_DIR / "targeted_pdf_text_layer_readiness_387_decision.json"
        if not decision_path.exists():
            self.skipTest("readiness inspection has not completed")
        mod.validate_complete()
        decision = json.loads(decision_path.read_text(encoding="utf-8"))
        self.assertEqual(decision["retained_readiness_queue_count"], 387)
        self.assertFalse(decision["global_analysis_readiness"])

    def test_future_prompt_when_present_preserves_boundaries(self) -> None:
        path = mod.OUTPUT_DIR / "next_targeted_text_layer_extraction_prompt.md"
        if not path.exists():
            self.skipTest("readiness inspection has not completed")
        text = path.read_text(encoding="utf-8").casefold()
        for phrase in ("separately authorized", "ocr-later/defer", "extraction is not rating", "not causal evidence", "global analysis readiness true"):
            self.assertIn(phrase, text)

    def test_dashboard_readiness_gate(self) -> None:
        completed, decision = dashboard.targeted_pdf_text_layer_readiness_387_status()
        self.assertTrue(completed)
        self.assertEqual(decision["retained_readiness_queue_count"], 387)
        self.assertEqual(decision["readiness_status_counts"]["parse_text_layer_later"], 289)
        self.assertEqual(decision["readiness_status_counts"]["html_text_later"], 32)
        self.assertFalse(decision["global_analysis_readiness"])

    def test_dashboard_generated_status_remains_globally_closed(self) -> None:
        readiness = mod.read_json(ROOT / "docs/dashboard/data/analysis_readiness.json")
        calibration = mod.read_json(ROOT / "docs/dashboard/data/text_table_calibration_status_summary.json")
        self.assertEqual(readiness["overall_status"], "targeted_pdf_text_layer_readiness_387_completed_text_extraction_ready_global_analysis_closed")
        self.assertEqual(calibration["calibration_phase"], "targeted_pdf_text_layer_readiness_387_completed_text_extraction_ready")
        self.assertTrue(calibration["targeted_pdf_text_layer_readiness_completed"])
        self.assertTrue(calibration["targeted_bounded_text_layer_extraction_ready_next"])
        self.assertFalse(calibration["targeted_pdf_text_layer_repair_needed"])

    def test_partial_outputs_fail_closed(self) -> None:
        old_output = mod.OUTPUT_DIR
        with tempfile.TemporaryDirectory() as temp:
            mod.OUTPUT_DIR = Path(temp)
            (mod.OUTPUT_DIR / mod.REQUIRED_FINAL_OUTPUTS[0]).touch()
            with self.assertRaises(RuntimeError):
                mod.validate_complete()
        mod.OUTPUT_DIR = old_output


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TargetedPDFTextLayerReadiness387Tests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    passed = result.testsRun - len(result.failures) - len(result.errors)
    print(f"targeted PDF/text-layer readiness checks: {passed}/{result.testsRun} passed")
    raise SystemExit(0 if result.wasSuccessful() else 1)
