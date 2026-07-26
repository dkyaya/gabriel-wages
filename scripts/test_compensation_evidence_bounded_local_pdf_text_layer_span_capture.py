#!/usr/bin/env python3
"""Offline regression and stress tests for bounded PDF text-layer span capture."""

from __future__ import annotations

import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import run_compensation_evidence_bounded_local_pdf_text_layer_span_capture as mod


class FakePage:
    def __init__(self, text: str):
        self.text = text

    def extract_text(self) -> str:
        return self.text


class FakeReader:
    pages_by_path: dict[str, list[str]] = {}

    def __init__(self, path: str):
        self.pages = [FakePage(text) for text in self.pages_by_path[path]]


def base_row(obs_id: str = "q1", mechanism: str = "CPI_or_COLA_indexing") -> dict[str, str]:
    row = {field: "" for field in mod.SPAN_FIELDS}
    row.update({
        "qualitative_observation_id": obs_id,
        "extraction_case_id": "case1",
        "document_identity_id": "doc1",
        "source_review_id": "sr1",
        "text_table_detection_id": "ttd1",
        "raw_retained_content_hash": "a" * 64,
        "artifact_pointer_bridge": "tmp/fake.pdf",
        "page_number": "1",
        "bounded_evidence_pointer": "case1#page=1",
        "mechanism_type": mechanism,
    })
    return row


class SpanMatchingTests(unittest.TestCase):
    def test_exact_structured_value(self):
        row = base_row()
        row["indexing_formula"] = "The annual adjustment equals the Consumer Price Index."
        page = "Header\nThe annual adjustment equals the Consumer Price Index.\nFooter"
        result = mod.select_span(row, page)
        self.assertEqual(result["span_capture_status"], "exact_verified")
        mod.verify_span(page, result)

    def test_whitespace_normalized_exact_value_round_trips(self):
        row = base_row()
        row["indexing_formula"] = "Consumer Price Index adjustment"
        page = "The Consumer  Price   Index adjustment applies."
        result = mod.select_span(row, page)
        self.assertEqual(result["span_capture_status"], "exact_verified")
        self.assertEqual(page[int(result["span_start"]):int(result["span_end"])], result["literal_verbatim_evidence_span"])

    def test_empty_text_page(self):
        self.assertEqual(mod.select_span(base_row(), " \n\t")["span_capture_status"], "no_text_layer")

    def test_multiple_identical_occurrences_is_ambiguous(self):
        row = base_row()
        row["indexing_formula"] = "Consumer Price Index"
        result = mod.select_span(row, "Consumer Price Index\nConsumer Price Index")
        self.assertEqual(result["span_capture_status"], "span_ambiguous_multiple_candidates")
        self.assertEqual(result["span_qa_pass"], "false")

    def test_label_with_no_matching_span(self):
        result = mod.select_span(base_row(), "Unrelated grievance language only.")
        self.assertEqual(result["span_capture_status"], "span_unavailable_or_unverified")

    def test_literal_anchor_is_exact_substring(self):
        page = "Annual COLA shall equal two percent. Other words."
        result = mod.select_span(base_row(), page)
        self.assertIn(result["literal_verbatim_evidence_span"], page)
        mod.verify_span(page, result)

    def test_other_label_has_no_dump_bucket_pattern(self):
        row = base_row(mechanism="other")
        result = mod.select_span(row, "This page says pay and salary many times.")
        self.assertEqual(result["span_capture_status"], "span_unavailable_or_unverified")

    def test_span_offset_corruption_fails(self):
        page = "Annual COLA shall equal two percent."
        result = mod.select_span(base_row(), page)
        result["span_start"] = "1"
        with self.assertRaises(RuntimeError):
            mod.verify_span(page, result)

    def test_span_hash_corruption_fails(self):
        page = "Annual COLA shall equal two percent."
        result = mod.select_span(base_row(), page)
        result["span_sha256"] = "0" * 64
        with self.assertRaises(RuntimeError):
            mod.verify_span(page, result)

    def test_full_page_text_leakage_fails(self):
        page = "Consumer Price Index"
        result = mod.span_result("exact_verified", "fixture", 0, len(page), page, 1)
        with self.assertRaises(RuntimeError):
            mod.verify_span(page, result)

    def test_span_length_bound(self):
        page = "COLA " + "x" * (mod.MAX_SPAN_CHARS + 5)
        result = mod.span_result("exact_verified", "fixture", 0, len(page), page, 1)
        with self.assertRaises(RuntimeError):
            mod.verify_span(page, result)

    def test_multiline_span_storage_fails(self):
        page = "Consumer Price \nIndex adjustment applies."
        text = "Consumer Price \nIndex"
        result = mod.span_result("exact_verified", "fixture", 0, len(text), text, 1)
        with self.assertRaisesRegex(RuntimeError, "single physical"):
            mod.verify_span(page, result)


class PageGuardTests(unittest.TestCase):
    def setUp(self):
        self.path = Path("/tmp/fake.pdf")
        self.request = mod.ApprovedPage(self.path, "a" * 64, 1)
        FakeReader.pages_by_path = {str(self.path): ["Annual COLA applies.", "Do not read this page."]}

    def test_approved_page_access(self):
        guard = mod.PageAccessGuard({self.request}, FakeReader)
        text, count = guard.extract(self.request)
        self.assertEqual(text, "Annual COLA applies.")
        self.assertEqual(count, 2)

    def test_non_target_page_access_fails_closed(self):
        guard = mod.PageAccessGuard({self.request}, FakeReader)
        with self.assertRaisesRegex(RuntimeError, "Non-target"):
            guard.extract(mod.ApprovedPage(self.path, "a" * 64, 2))

    def test_page_pointer_outside_range_fails(self):
        request = mod.ApprovedPage(self.path, "a" * 64, 3)
        guard = mod.PageAccessGuard({request}, FakeReader)
        with self.assertRaises(IndexError):
            guard.extract(request)


class CheckpointTests(unittest.TestCase):
    def test_schema_version_mismatch_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "checkpoint.jsonl"
            path.write_text(json.dumps({"schema_version": "old", "input_signature": "sig", "qualitative_observation_id": "q1"}) + "\n")
            with self.assertRaisesRegex(RuntimeError, "signature mismatch"):
                mod.load_checkpoint(path, "sig")

    def test_duplicate_checkpoint_id_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "checkpoint.jsonl"
            item = {"schema_version": mod.SCHEMA_VERSION, "input_signature": "sig", "qualitative_observation_id": "q1"}
            path.write_text(json.dumps(item) + "\n" + json.dumps(item) + "\n")
            with self.assertRaisesRegex(RuntimeError, "Duplicate checkpoint"):
                mod.load_checkpoint(path, "sig")

    def test_full_page_text_checkpoint_leakage_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "checkpoint.jsonl"
            item = {"schema_version": mod.SCHEMA_VERSION, "input_signature": "sig", "qualitative_observation_id": "q1", "page_text": "forbidden"}
            path.write_text(json.dumps(item) + "\n")
            with self.assertRaisesRegex(RuntimeError, "leakage"):
                mod.load_checkpoint(path, "sig")

    def test_append_rejects_page_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(RuntimeError, "leakage"):
                mod.append_checkpoint(Path(tmp) / "checkpoint.jsonl", {"page_text": "forbidden"})

    def test_idempotent_checkpoint_load(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "checkpoint.jsonl"
            item = {"schema_version": mod.SCHEMA_VERSION, "input_signature": "sig", "qualitative_observation_id": "q1"}
            mod.append_checkpoint(path, item)
            self.assertEqual(mod.load_checkpoint(path, "sig"), mod.load_checkpoint(path, "sig"))


class PreflightFailureTests(unittest.TestCase):
    def test_missing_retained_pdf_path_fails(self):
        with self.assertRaises(FileNotFoundError):
            mod.verify_retained_pdf(Path("/tmp/definitely_missing_gabriel_span_fixture.pdf"), "0" * 64)

    def test_wrong_retained_pdf_hash_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "fixture.pdf"
            path.write_bytes(b"not the expected bytes")
            with self.assertRaisesRegex(RuntimeError, "SHA-256 mismatch"):
                mod.verify_retained_pdf(path, "0" * 64)

    def test_ocr_later_status_fails(self):
        with self.assertRaisesRegex(RuntimeError, "OCR-later"):
            mod.assert_text_layer_allowed({"ocr_needed_signal": "yes", "recommended_next_action": "ocr_later"})

    def test_duplicate_qualitative_observation_ids_fail(self):
        with self.assertRaisesRegex(RuntimeError, "Duplicate"):
            mod.assert_unique_observation_ids([{"qualitative_observation_id": "q1"}, {"qualitative_observation_id": "q1"}], 2)

    def test_blank_qualitative_observation_id_fails(self):
        with self.assertRaisesRegex(RuntimeError, "blank"):
            mod.assert_unique_observation_ids([{"qualitative_observation_id": ""}], 1)


class CaptureResumeTests(unittest.TestCase):
    def test_partial_checkpoint_resume_reuses_row_and_reads_only_missing_page(self):
        with tempfile.TemporaryDirectory(dir=mod.ROOT / "tmp") as tmp:
            tmp_path = Path(tmp)
            p1, p2 = tmp_path / "a.pdf", tmp_path / "b.pdf"
            p1.write_bytes(b"fake1")
            p2.write_bytes(b"fake2")
            h1, h2 = hashlib.sha256(b"fake1").hexdigest(), hashlib.sha256(b"fake2").hexdigest()
            r1, r2 = base_row("q1"), base_row("q2")
            for row, path, digest in ((r1, p1, h1), (r2, p2, h2)):
                row["artifact_pointer_bridge"] = str(path.relative_to(mod.ROOT)) if mod.ROOT in path.parents else str(path)
                row["raw_retained_content_hash"] = digest
                row["indexing_formula"] = "Consumer Price Index"
            r1["artifact_pointer_bridge"] = str(p1.relative_to(mod.ROOT))
            r2["artifact_pointer_bridge"] = str(p2.relative_to(mod.ROOT))
            approved = {mod.ApprovedPage(p1, h1, 1), mod.ApprovedPage(p2, h2, 1)}
            preflight = {"rows": [r1, r2], "approved": approved, "input_hashes": {"navigation": "n"}}
            signature = mod.checkpoint_signature([r1, r2], preflight["input_hashes"])
            checkpoint = tmp_path / "checkpoint.jsonl"
            first = {
                "schema_version": mod.SCHEMA_VERSION, "input_signature": signature,
                "qualitative_observation_id": "q1", "extraction_case_id": "case1",
                "document_identity_id": "doc1", "source_review_id": "sr1",
                "text_table_detection_id": "ttd1", "retained_content_hash": h1,
                "pdf_sha256": h1, "page_number": "1", "bounded_evidence_pointer": "case1#page=1",
                "mechanism_type": "CPI_or_COLA_indexing", "artifact_pointer": str(p1.relative_to(mod.ROOT)),
                "page_access_status": "text_layer_present", "pdf_page_count": "1", "text_layer_char_count": "27",
                "page_access_error_type_sanitized": "", **mod.span_result("exact_verified", "fixture", 0, 20, "Consumer Price Index", 1),
                "qa_status": "exact_literal_span_verified",
            }
            mod.append_checkpoint(checkpoint, first)
            FakeReader.pages_by_path = {str(p2): ["Consumer Price Index adjustment."]}
            ledger, page_audit, checkpoint_audit = mod.capture(preflight, checkpoint, True, FakeReader)
            self.assertEqual(len(ledger), 2)
            self.assertEqual(len(page_audit), 2)
            self.assertEqual(checkpoint_audit["checkpoint_reused_row_count"], 1)
            self.assertEqual(checkpoint_audit["unique_pages_accessed_this_run"], 1)


class IntegrationInvariantTests(unittest.TestCase):
    def test_actual_repo_preflight_counts_and_hashes(self):
        with tempfile.TemporaryDirectory(dir=mod.ROOT / "docs/analysis") as tmp:
            output = Path(tmp) / "new-output"
            result = mod.load_preflight(output)
            self.assertEqual(result["qualitative_row_count"], 1954)
            self.assertEqual(result["unique_pdf_count"], 788)
            self.assertEqual(result["unique_approved_page_count"], 1223)
            self.assertEqual(result["ocr_later_approved_count"], 0)
            self.assertEqual(result["package_sha256_checks_passed"], 5)

    def test_complete_output_resume_reuses_without_page_access(self):
        output = mod.DEFAULT_OUTPUT
        result = mod.load_preflight(output, allow_existing=True)
        reused = mod.reuse_complete_output(output, result)
        self.assertTrue(reused["idempotent_complete_output_reused"])
        self.assertEqual(reused["pdf_pages_reaccessed_on_reuse"], 0)

    def test_carried_forward_counts(self):
        expected = {"quant_candidate": 862, "quant_exception": 1045, "nonbase": 4733, "reference": 345, "conflicts": 2}
        for name, count in expected.items():
            _, rows = mod.read_rows(mod.INPUTS[name])
            self.assertEqual(len(rows), count)

    def test_prior_navigation_ids_unique(self):
        _, rows = mod.read_rows(mod.INPUTS["navigation"])
        ids = [row["qualitative_observation_id"] for row in rows]
        self.assertEqual(len(ids), mod.EXPECTED_ROWS)
        self.assertEqual(len(set(ids)), mod.EXPECTED_ROWS)

    def test_navigation_shadow_preserves_historical_qa_and_separates_span_qa(self):
        _, prior = mod.read_rows(mod.INPUTS["navigation"])
        header, repaired = mod.read_rows(mod.DEFAULT_OUTPUT / mod.OUTPUTS["verified_navigation"])
        self.assertIn("span_qa_status", header)
        self.assertEqual([row["qa_status"] for row in repaired], [row["qa_status"] for row in prior])
        self.assertTrue(all(row["span_qa_status"] for row in repaired))

    def test_analysis_readiness_predecessor_false(self):
        decision = json.loads(mod.INPUTS["decision"].read_text())
        self.assertFalse(decision["analysis_readiness"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
