"""No-network checks for the direct-SDK state-source-scout backend."""

from __future__ import annotations

import csv
import json
import sys
import tempfile
from pathlib import Path

import gabriel_state_source_scout as scout


class FakeUsageDetails:
    reasoning_tokens = 7


class FakeUsage:
    input_tokens = 123
    output_tokens = 45
    total_tokens = 168
    output_tokens_details = FakeUsageDetails()


class FakeResponse:
    id = "resp_synthetic_fixture"
    status = "completed"
    usage = FakeUsage()

    def __init__(self, output_text: str):
        self.output_text = output_text

    def model_dump(self, mode: str = "json") -> dict:
        assert mode == "json"
        return {
            "output": [
                {
                    "type": "web_search_call",
                    "action": {
                        "sources": [
                            {
                                "url": "https://example.gov/agreement.pdf",
                                "title": "Example agreement",
                            }
                        ]
                    },
                }
            ]
        }


def _candidate_json() -> str:
    return json.dumps(
        {
            "municipality": "Example Borough",
            "state": "PA",
            "candidates": [
                {
                    "unit_type": "non_safety",
                    "document_title": "Example Borough Civilian Agreement",
                    "union_name": "Example Local 1",
                    "employer": "Example Borough",
                    "contract_years": "2020-2023",
                    "source_url": "https://example.gov/agreement.pdf",
                    "source_owner_type": "city",
                    "document_type": "cba",
                    "candidate_stage": "qualifying_candidate",
                    "document_completeness": "full_document",
                    "visible_year_evidence": "Cover states 2020-2023.",
                    "overlap_with_anchor_cycle": "overlap",
                    "duplicate_risk": "none_known",
                    "blocked_or_unreadable_flag": "no",
                    "cycle_match_notes": "Overlaps the supplied anchor.",
                    "comparator_role": "ordinary_non_safety_comparator",
                    "wrong_employer_risk": "low",
                    "context_only_flag": "no",
                    "needs_verification_reason": "Verify URL and operative term.",
                    "why_relevant": "Potential ordinary municipal comparator.",
                    "confidence": "medium",
                }
            ],
        }
    )


def _check_request_shapes() -> None:
    live = scout.build_direct_sdk_response_kwargs(
        "prompt", "gpt-5.4-nano", "low", web_search=True
    )
    assert live["model"] == "gpt-5.4-nano"
    assert live["reasoning"] == {"effort": "low"}
    assert live["tools"] == [{"type": "web_search", "search_context_size": "low"}]
    assert live["include"] == ["web_search_call.action.sources"]

    smoke = scout.build_direct_sdk_response_kwargs(
        "Reply with OK.",
        "gpt-5.4-nano",
        "low",
        web_search=False,
        reasoning_effort=None,
    )
    assert "tools" not in smoke
    assert "include" not in smoke
    assert "reasoning" not in smoke


def _check_mocked_response_uses_existing_candidate_pipeline() -> None:
    identifier = "direct-sdk-fixture"
    row = scout.direct_sdk_response_to_row(
        FakeResponse(_candidate_json()), identifier, "fixture prompt", 1.25
    )
    assert row["Identifier"] == identifier
    assert row["Successful"] is True
    assert row["Response IDs"] == "resp_synthetic_fixture"
    assert row["Input Tokens"] == 123
    assert row["Reasoning Tokens"] == 7
    assert row["Output Tokens"] == 45
    assert row["Total Tokens"] == 168
    assert "https://example.gov/agreement.pdf" in row["Web Search Sources"]

    candidates, failure = scout.parse_response_to_candidates(
        "fixture-run",
        {
            "state": "PA",
            "municipality": "Example Borough",
            "municipality_id": "example-pa-001",
        },
        identifier,
        row["Response"],
        "tmp/raw_outputs.csv#identifier=direct-sdk-fixture",
        gabriel_row=row,
    )
    assert failure is None
    assert len(candidates) == 1
    assert candidates[0]["unit_type"] == "non_safety"
    assert candidates[0]["verification_status"] == "unverified"
    assert candidates[0]["promotion_status"] == "raw_model_output"


def _check_secret_redaction_and_log() -> None:
    secret = "synthetic-secret-value-for-test"
    unsafe = (
        "Authorization: Bearer synthetic-secret-value-for-test "
        "Ocp-Apim-Subscription-Key=synthetic-secret-value-for-test"
    )
    safe = scout.redact_direct_sdk_text(unsafe, [secret])
    assert secret not in safe
    assert "[REDACTED]" in safe

    with tempfile.TemporaryDirectory() as tmp:
        path = scout.write_direct_sdk_sanitized_log(
            Path(tmp),
            [
                {
                    "Identifier": "fixture",
                    "Successful": False,
                    "Response": "",
                    "Response IDs": "",
                    "Input Tokens": "",
                    "Reasoning Tokens": "",
                    "Output Tokens": "",
                    "Error Log": unsafe,
                }
            ],
            model="gpt-5.4-nano",
            web_search=False,
            timeout=30,
            max_retries=0,
            secret_values=[secret],
        )
        rendered = path.read_text(encoding="utf-8")
    assert secret not in rendered
    assert "Ocp-Apim-Subscription-Key" in rendered


def _check_repeated_connection_error_stop_signature() -> None:
    failed = {
        "Response": "",
        "Response IDs": "",
        "Output Tokens": "",
        "Error Log": '["APIConnectionError: Connection error."]',
    }
    assert scout.is_direct_sdk_connection_failure_without_response(failed) is True
    assert scout.is_direct_sdk_connection_failure_without_response(
        {**failed, "Response IDs": "resp_fixture"}
    ) is False
    stopped = scout._direct_sdk_stopped_row("fixture", "prompt")
    assert stopped["Successful"] is False
    assert "stopped_before_request" in stopped["Error Log"]


def _check_estimated_cost_and_missing_pricing() -> None:
    usage = {
        "token_usage_available": True,
        "input_tokens": 1_000_000,
        "reasoning_tokens": 100_000,
        "output_tokens": 500_000,
        "total_tokens": 1_500_000,
    }
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        config_path = tmp_path / "pricing.json"
        config_path.write_text(
            json.dumps(
                {
                    "models": {
                        "fixture-model": {
                            "model_name": "fixture-model",
                            "input_price_per_1m_tokens": 1.0,
                            "output_price_per_1m_tokens": 2.0,
                            "reasoning_price_per_1m_tokens": None,
                            "reasoning_billing_mode": "included_in_output_tokens",
                            "source_note": "Synthetic test pricing; not billed cost.",
                            "effective_date": "2026-07-20",
                            "estimate_only": True,
                            "estimated_cost_scope": "token_only",
                        }
                    }
                }
            ),
            encoding="utf-8",
        )
        estimated = scout.apply_direct_sdk_estimated_cost(
            usage, config_path, "fixture-model"
        )
        assert estimated["estimated_cost_available"] is True
        assert estimated["token_usage_available"] is True
        assert estimated["estimate_only"] is True
        assert estimated["pricing_missing_or_unconfirmed"] is True
        assert estimated["estimated_input_cost"] == 1.0
        assert estimated["estimated_output_cost"] == 1.0
        assert estimated["estimated_reasoning_cost"] == 0.0
        assert estimated["estimated_total_cost"] == 2.0
        assert estimated["reasoning_billing_mode"] == "included_in_output_tokens"
        assert "not billed cost" in estimated["pricing_source_note"]

        missing = scout.apply_direct_sdk_estimated_cost(
            usage, tmp_path / "missing.json", "fixture-model"
        )
        assert missing["estimated_cost_available"] is False
        assert missing["token_usage_available"] is True
        assert missing["pricing_missing_or_unconfirmed"] is True
        assert missing["estimated_total_cost"] is None
        assert missing["estimate_only"] is True


def _check_dry_run_remains_backend_independent() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        municipalities_path = tmp_path / "municipalities.csv"
        with municipalities_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f, fieldnames=["municipality_id", "municipality", "state"]
            )
            writer.writeheader()
            writer.writerow(
                {
                    "municipality_id": "dry-run-pa-001",
                    "municipality": "Example Borough",
                    "state": "PA",
                }
            )
        output_dir = tmp_path / "dry-run-output"
        original_argv = sys.argv
        try:
            sys.argv = [
                "gabriel_state_source_scout.py",
                "--dry-run",
                "--live-backend",
                "direct-sdk",
                "--state",
                "PA",
                "--municipalities-csv",
                str(municipalities_path),
                "--output-dir",
                str(output_dir),
                "--prompt-mode",
                "minimal",
            ]
            assert scout.main() == 0
        finally:
            sys.argv = original_argv

        metadata = json.loads((output_dir / "run_metadata.json").read_text(encoding="utf-8"))
        assert metadata["mode"] == "dry_run"
        assert metadata["live_attempted"] is False
        assert "live_backend" not in metadata
        assert sorted(path.name for path in output_dir.iterdir()) == [
            "prompt_preview.md",
            "run_metadata.json",
        ]


def _check_isolated_worker_cost_log() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        worker_log = Path(tmp) / "worker_run" / "batch_cost_log.csv"
        first = {"run_id": "worker-fixture-01", "state": "CA"}
        second = {"run_id": "worker-fixture-02", "state": "NJ"}
        assert scout.append_cost_log(first, worker_log) == worker_log
        assert scout.append_cost_log(second, worker_log) == worker_log
        with worker_log.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        assert [row["run_id"] for row in rows] == [
            "worker-fixture-01",
            "worker-fixture-02",
        ]
        assert list(rows[0]) == scout.COST_SUMMARY_FIELDS


def main() -> int:
    _check_request_shapes()
    _check_mocked_response_uses_existing_candidate_pipeline()
    _check_secret_redaction_and_log()
    _check_repeated_connection_error_stop_signature()
    _check_estimated_cost_and_missing_pricing()
    _check_dry_run_remains_backend_independent()
    _check_isolated_worker_cost_log()
    print("PASS: direct SDK request shape preserves scout web-search settings")
    print("PASS: no-search smoke request omits tools and web search")
    print("PASS: mocked direct response enters the existing unverified candidate pipeline")
    print("PASS: credential values are redacted from direct-backend logs")
    print("PASS: repeated connection errors trigger the no-further-request stop signature")
    print("PASS: estimated token cost is labeled and missing pricing preserves usage")
    print("PASS: dry-run artifacts and metadata remain backend-independent")
    print("PASS: parallel workers can route cost logging to a batch-specific file")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
