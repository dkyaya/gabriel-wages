#!/usr/bin/env python3
"""Regression tests for the bounded 321-source text-layer extraction stage."""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = ROOT / "scripts/run_targeted_text_layer_extraction_321.py"
SPEC = importlib.util.spec_from_file_location("targeted_text_layer_extraction_321", RUNNER_PATH)
assert SPEC and SPEC.loader
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)
DASHBOARD_SPEC = importlib.util.spec_from_file_location("build_dashboard_data", ROOT / "scripts/build_dashboard_data.py")
assert DASHBOARD_SPEC and DASHBOARD_SPEC.loader
dashboard = importlib.util.module_from_spec(DASHBOARD_SPEC)
DASHBOARD_SPEC.loader.exec_module(dashboard)


def csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


class TargetedTextLayerExtraction321Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.queue, cls.preserved, cls.hashes = runner.verify_inputs(verify_file_bytes=False)
        cls.pdf = [row for row in cls.queue if row["readiness_status"] == "parse_text_layer_later"]
        cls.html = [row for row in cls.queue if row["readiness_status"] == "html_text_later"]

    def test_exact_locked_scope(self) -> None:
        self.assertEqual(len(self.queue), 321)
        self.assertEqual(len({row["retained_source_id"] for row in self.queue}), 321)
        self.assertEqual(runner.id_set_hash(self.queue), runner.EXPECTED_ID_SET_HASH)

    def test_pdf_html_split(self) -> None:
        self.assertEqual((len(self.pdf), len(self.html)), (289, 32))
        self.assertTrue(all(row["content_type_hint"] == "application/pdf" for row in self.pdf))
        self.assertTrue(all(row["content_type_hint"] == "text/html" for row in self.html))

    def test_lane_and_mechanism_scope(self) -> None:
        from collections import Counter

        self.assertEqual(dict(Counter(row["lane_id"] for row in self.queue)), runner.EXPECTED_LANES)
        self.assertEqual(
            dict(Counter(row["target_mechanism_family"] for row in self.queue)),
            runner.EXPECTED_MECHANISMS,
        )

    def test_only_tier_a_b_retained_integrity_pass_rows(self) -> None:
        for row in self.queue:
            self.assertIn(row["priority_tier"], {"tier_a", "tier_b"})
            self.assertEqual(row["source_review_download_status"], "retained_downloaded_source")
            self.assertEqual(row["file_integrity_status"], "integrity_pass")

    def test_downstream_input_statuses_closed(self) -> None:
        for row in self.queue:
            self.assertEqual(row["extraction_status"], "not_extracted")
            self.assertEqual(row["rating_status"], "not_rated")
            self.assertEqual(row["ingestion_status"], "not_ingested")
            self.assertEqual(row["codification_status"], "not_codified")
            self.assertEqual(row["causal_status"], "not_causal_evidence")
            self.assertEqual(row["global_analysis_readiness"], "false")

    def test_exclusions_preserved_and_disjoint(self) -> None:
        self.assertEqual(len(self.preserved), 108)
        self.assertEqual(sum(row["exclusion_layer"] == "readiness_review" for row in self.preserved), 66)
        self.assertEqual(sum(row["exclusion_layer"] == "source_review_download" for row in self.preserved), 42)
        ready_ids = {row["retained_source_id"] for row in self.queue}
        readiness_excluded_ids = {
            row["retained_source_id"] for row in self.preserved if row["exclusion_layer"] == "readiness_review"
        }
        self.assertFalse(ready_ids & readiness_excluded_ids)

    def test_all_immutable_input_hashes_are_pinned(self) -> None:
        self.assertEqual(self.hashes, runner.EXPECTED_HASHES)

    def test_all_retained_paths_stay_under_retained_directory(self) -> None:
        for row in self.queue:
            path = (ROOT / row["local_retained_path"]).resolve()
            self.assertTrue(path.is_file())
            self.assertTrue(path.is_relative_to(runner.RETAINED_DIR.resolve()))

    def test_runner_has_no_network_or_forbidden_extractors(self) -> None:
        source = RUNNER_PATH.read_text(encoding="utf-8")
        forbidden = ("requests.", "urllib.request", "httpx.", "pytesseract", "ocrmypdf", "pdf2image", "gabriel.codify")
        for token in forbidden:
            self.assertNotIn(token, source)

    def test_pdf_command_is_local_non_ocr_and_non_rendering(self) -> None:
        completed = subprocess.CompletedProcess([], 0, stdout=b"A contract clause with enough local text. " * 10, stderr=b"")
        with mock.patch.object(runner, "write_artifact", return_value=("task/text.txt", "a" * 64, 100)), mock.patch.object(
            runner.subprocess, "run", return_value=completed
        ) as call:
            result = runner.extract_pdf(self.pdf[0])
        command = call.call_args.args[0]
        self.assertEqual(command[:4], ["pdftotext", "-enc", "UTF-8", "-nopgbrk"])
        self.assertNotIn("ocr", " ".join(command).casefold())
        self.assertEqual(result["ocr_used"], "false")
        self.assertEqual(result["pdf_rendering_used"], "false")

    def test_pdf_success_preserves_closed_statuses(self) -> None:
        completed = subprocess.CompletedProcess([], 0, stdout=b"Collective bargaining agreement text. " * 200, stderr=b"")
        with mock.patch.object(runner, "write_artifact", return_value=("task/text.txt", "a" * 64, 100)), mock.patch.object(
            runner.subprocess, "run", return_value=completed
        ):
            row = dict(self.pdf[0])
            row["page_count"] = "1"
            result = runner.extract_pdf(row)
            self.assertEqual(result["extraction_status"], "extracted_ok")
        self.assertEqual(result["rating_status"], "not_rated")
        self.assertEqual(result["ingestion_status"], "not_ingested")
        self.assertEqual(result["codification_status"], "not_codified")
        self.assertEqual(result["causal_status"], "not_causal_evidence")
        self.assertEqual(result["global_analysis_readiness"], "false")

    def test_pdf_empty_too_short(self) -> None:
        completed = subprocess.CompletedProcess([], 0, stdout=b"tiny", stderr=b"")
        with mock.patch.object(runner, "write_artifact", return_value=("task/text.txt", "a" * 64, 10)), mock.patch.object(
            runner.subprocess, "run", return_value=completed
        ):
            result = runner.extract_pdf(self.pdf[0])
        self.assertEqual(result["extraction_status"], "empty_or_too_short")

    def test_pdf_low_density(self) -> None:
        completed = subprocess.CompletedProcess([], 0, stdout=(b"word " * 30), stderr=b"")
        with mock.patch.object(runner, "write_artifact", return_value=("task/text.txt", "a" * 64, 150)), mock.patch.object(
            runner.subprocess, "run", return_value=completed
        ):
            row = dict(self.pdf[0])
            row["page_count"] = "100"
            result = runner.extract_pdf(row)
        self.assertEqual(result["extraction_status"], "low_text_density")

    def test_pdf_nonzero_and_timeout_are_errors(self) -> None:
        with mock.patch.object(
            runner.subprocess, "run", return_value=subprocess.CompletedProcess([], 1, stdout=b"", stderr=b"bad")
        ):
            self.assertEqual(runner.extract_pdf(self.pdf[0])["extraction_status"], "extraction_error")
        with mock.patch.object(runner.subprocess, "run", side_effect=subprocess.TimeoutExpired("pdftotext", 1)):
            self.assertEqual(runner.extract_pdf(self.pdf[0])["extraction_status"], "extraction_error")

    def test_visible_html_excludes_script_style_and_svg(self) -> None:
        parser = runner.VisibleHTMLExtractor()
        parser.feed("<html><style>secret-style</style><script>secret-script</script><svg>secret-svg</svg><p>Visible agreement text</p></html>")
        text = parser.text()
        self.assertIn("Visible agreement text", text)
        self.assertNotIn("secret-", text)

    def test_html_success_is_local_and_bounded(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.html"
            source.write_text("<html><body><p>Municipal agreement language. " + "term " * 100 + "</p></body></html>", encoding="utf-8")
            text_dir = Path(directory) / "out"
            text_dir.mkdir()
            row = dict(self.html[0])
            row["local_retained_path"] = str(source)
            with mock.patch.object(runner, "ROOT", Path("/")), mock.patch.object(runner, "HTML_TEXT_DIR", text_dir):
                result = runner.extract_html(row)
            self.assertEqual(result["extraction_status"], "extracted_ok")
            self.assertEqual(result["extraction_method"], "local_html_visible_text_parser")
            self.assertEqual(result["model_api_used"], "false")

    def test_html_redirect_shell_is_quarantined(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.html"
            source.write_text('<meta http-equiv="refresh" content="1"><p>' + "shell " * 100 + "</p>", encoding="utf-8")
            text_dir = Path(directory) / "out"
            text_dir.mkdir()
            row = dict(self.html[0])
            row["local_retained_path"] = str(source)
            with mock.patch.object(runner, "ROOT", Path("/")), mock.patch.object(runner, "HTML_TEXT_DIR", text_dir):
                result = runner.extract_html(row)
            self.assertEqual(result["extraction_status"], "html_noisy_or_shell")

    def test_secret_pattern_blocks_artifact_retention(self) -> None:
        secret_text = b"-----BEGIN PRIVATE KEY-----\n" + b"x" * 500
        completed = subprocess.CompletedProcess([], 0, stdout=secret_text, stderr=b"")
        with tempfile.TemporaryDirectory() as directory, mock.patch.object(runner, "PDF_TEXT_DIR", Path(directory)), mock.patch.object(
            runner.subprocess, "run", return_value=completed
        ):
            row = dict(self.pdf[0])
            row["page_count"] = "1"
            result = runner.extract_pdf(row)
            self.assertEqual(list(Path(directory).glob("*.txt")), [])
        self.assertEqual(result["extraction_status"], "extraction_error")
        self.assertEqual(result["extracted_text_path"], "")

    def test_nonready_status_rejected(self) -> None:
        row = dict(self.pdf[0])
        row["readiness_status"] = "ocr_later_or_defer"
        result = runner.extract_one(row)
        self.assertEqual(result["extraction_status"], "extraction_error")
        self.assertEqual(result["extraction_reason"], "nonready_status_rejected")

    def test_controlled_status_vocabulary(self) -> None:
        self.assertEqual(
            runner.CONTROLLED_STATUSES,
            {"extracted_ok", "empty_or_too_short", "low_text_density", "suspected_bad_text_layer", "html_noisy_or_shell", "extraction_error"},
        )

    def test_artifact_identifier_is_deterministic(self) -> None:
        source_id = self.queue[0]["retained_source_id"]
        self.assertEqual(runner.extracted_text_id(source_id), runner.extracted_text_id(source_id))
        self.assertTrue(runner.extracted_text_id(source_id).startswith("TXT321-"))

    def test_prepared_or_completed_outputs_fail_closed(self) -> None:
        if not runner.OUTPUT_DIR.exists():
            return
        lock = json.loads((runner.OUTPUT_DIR / "targeted_text_layer_extraction_321_lock.json").read_text())
        locked = csv_rows(runner.OUTPUT_DIR / "targeted_text_layer_extraction_321_locked_queue.csv")
        self.assertEqual(lock["locked_queue_count"], 321)
        self.assertEqual(len(locked), 321)
        self.assertEqual(lock["retained_source_id_set_sha256"], runner.EXPECTED_ID_SET_HASH)
        if (runner.OUTPUT_DIR / "targeted_text_layer_extraction_321_decision.json").is_file():
            runner.validate_complete()

    def test_completed_outputs_have_no_forbidden_downstream_promotion(self) -> None:
        path = runner.OUTPUT_DIR / "targeted_text_layer_extraction_321_results.csv"
        if not path.is_file():
            return
        rows = csv_rows(path)
        self.assertEqual(len(rows), 321)
        for row in rows:
            self.assertEqual(row["ocr_used"], "false")
            self.assertEqual(row["pdf_rendering_used"], "false")
            self.assertEqual(row["model_api_used"], "false")
            self.assertEqual(row["rating_status"], "not_rated")
            self.assertEqual(row["global_analysis_readiness"], "false")

    def test_future_prompt_preserves_evidence_rating_boundary(self) -> None:
        path = runner.OUTPUT_DIR / "next_targeted_evidence_extraction_prompt.md"
        if not path.is_file():
            return
        text = path.read_text(encoding="utf-8")
        self.assertIn("exact verbatim spans", text)
        self.assertIn("Do not", text)
        self.assertIn("global analysis readiness true", text)

    def test_dashboard_extraction_gate(self) -> None:
        completed, decision = dashboard.targeted_text_layer_extraction_321_status()
        self.assertTrue(completed)
        self.assertEqual(decision["extraction_queue_count"], 321)
        self.assertEqual(decision["pdf_extraction_count"], 289)
        self.assertEqual(decision["html_extraction_count"], 32)
        self.assertEqual(decision["extraction_status_counts"], {"extracted_ok": 321})
        self.assertFalse(decision["global_analysis_readiness"])

    def test_dashboard_generated_status_remains_globally_closed(self) -> None:
        readiness_path = ROOT / "docs/dashboard/data/analysis_readiness.json"
        calibration_path = ROOT / "docs/dashboard/data/text_table_calibration_status_summary.json"
        if not (readiness_path.is_file() and calibration_path.is_file()):
            return
        readiness = json.loads(readiness_path.read_text(encoding="utf-8"))
        calibration = json.loads(calibration_path.read_text(encoding="utf-8"))
        if calibration.get("targeted_text_layer_extraction_completed"):
            if calibration.get("targeted_evidence_span_rating_summary_completed"):
                self.assertEqual(
                    readiness["overall_status"],
                    "quantitative_to_qualitative_mechanism_linkage_513_completed_claim_review_ready_global_analysis_closed",
                )
                self.assertEqual(
                    calibration["calibration_phase"],
                    "quantitative_to_qualitative_mechanism_linkage_513_completed_claim_review_ready",
                )
            elif calibration.get("targeted_evidence_span_rating_completed"):
                self.assertEqual(
                    readiness["overall_status"],
                    "targeted_evidence_span_rating_201_completed_with_quarantine_summary_review_ready_global_analysis_closed",
                )
                self.assertEqual(
                    calibration["calibration_phase"],
                    "targeted_evidence_span_rating_201_completed_with_quarantine",
                )
            elif calibration.get("targeted_evidence_span_extraction_completed"):
                self.assertEqual(
                    readiness["overall_status"],
                    "targeted_evidence_span_extraction_321_completed_rating_ready_global_analysis_closed",
                )
                self.assertEqual(
                    calibration["calibration_phase"],
                    "targeted_evidence_span_extraction_321_completed_rating_ready",
                )
            else:
                self.assertEqual(
                    readiness["overall_status"],
                    "targeted_text_layer_extraction_321_completed_evidence_extraction_ready_global_analysis_closed",
                )
                self.assertEqual(
                    calibration["calibration_phase"],
                    "targeted_text_layer_extraction_321_completed_evidence_extraction_ready",
                )
            self.assertTrue(calibration["targeted_evidence_extraction_review_ready_next"])
            self.assertFalse(calibration["targeted_text_layer_extraction_repair_needed"])
            self.assertNotIn('"global_analysis_readiness": true', json.dumps(readiness, sort_keys=True).casefold())


if __name__ == "__main__":
    unittest.main(verbosity=2)
